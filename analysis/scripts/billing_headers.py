"""Deterministic header extractor for the 881 EZ billing PDFs.
Run: python3 -I analysis/scripts/billing_headers.py  (from the TEM dir). Writes analysis/billing_index.csv
Text cache: pdftotext -layout output in CACHE (rebuilt if missing)."""
import csv, json, os, re, subprocess, sys
from datetime import date

ROOT = "/media/abhay/Workspace/Egon Zehnder/TEM"
CACHE = "/tmp/claude-1000/txt"
MON = {m: i + 1 for i, m in enumerate("jan feb mar apr may jun jul aug sep oct nov dec".split())}
MON.update(dict(gen=1, mag=5, giu=6, lug=7, ago=8, set=9, ott=10, dic=12))
NUM = r"-?\s?[\d'.,]*\d"


def text(h, path):
    f = f"{CACHE}/{h}.txt"
    if not os.path.exists(f):
        os.makedirs(CACHE, exist_ok=True)
        subprocess.run(["pdftotext", "-layout", f"{ROOT}/{path}", f], stderr=subprocess.DEVNULL)
    return open(f, errors="ignore").read()


def num(s, it=False):
    """'38'956.69' '5.461,95' '$12,573.40' '- 1'080.00' '240,397.20CR' -> float (CR/leading - => negative)"""
    if s is None:
        return None
    neg = "-" in s or s.strip().upper().endswith("CR")
    s = re.sub(r"[^\d.,]", "", s.replace("'", ""))
    if not s:
        return None
    if it or re.search(r",\d{2}$", s) and "." in s and s.rfind(".") < s.rfind(","):
        s = s.replace(".", "").replace(",", ".")
    else:
        s = s.replace(",", "")
    try:
        v = float(s)
    except ValueError:
        return None
    return -v if neg else v


def pdate(s, fmt):
    """fmt: dmy_txt ('02 giu 2025', '03-Feb-2025'), dmy_num ('01/12/2024','05-06-2026'), mdy ('04/10/2023')"""
    if not s:
        return None
    try:
        if fmt == "txt":
            d, m, y = re.match(r"(\d{1,2})[ -]([A-Za-z]{3})[a-z]*[ -](\d{4})", s.strip()).groups()
            return date(int(y), MON[m.lower()], int(d)).isoformat()
        a, b, y = re.match(r"(\d{1,2})[/-](\d{1,2})[/-](\d{4})", s.strip()).groups()
        d, m = (int(b), int(a)) if fmt == "mdy" else (int(a), int(b))
        return date(int(y), m, d).isoformat()
    except Exception:
        return None


def g(rx, t, flags=0):
    m = re.search(rx, t, flags)
    return m.group(1).strip() if m else None


def last_num(label, t):
    m = re.search(label + r"[^\n\d$-]*([^\n]*)", t)
    if not m:
        return None
    nums = re.findall(r"-?\s?\$?[\d'.,]*\d(?:CR)?", m.group(1))
    return num(nums[-1]) if nums else None


def classify(p1, full):
    if "Document Extraction and Discrepancy" in p1: return "NOT_BILLING_NTT_GUIDE"
    if "COLLABORATION" in p1 and "Invoice No." in p1: return "NTT_CLOUD_COMM"
    if "Statement Summary" in p1 and "Bill Payer ID" in p1:
        return "VZ_US_STMT_NODE" if "Node No" in p1 else "VZ_US_STMT_SMB"
    if "Original for Recipient" in p1 and "Tax Invoice" in p1: return "VZ_IN_GST_TAXINV"
    if "Xtraconnect Reference" in p1: return "VZ_XTRA_INV_UKJP"
    if "Numero fattura" in p1: return "VZ_INTL_IT"
    if "Credit Note Number" in p1: return "VZ_INTL_CN"
    if re.search(r"Remittance Statement|Invoice Summary", full[:20000]) and "Customer ID" in full[:3000] and "Page 1" not in p1[:400]:
        return "VZ_CA_EC" if "Verizon Canada" in p1 else "VZ_US_EC"
    if re.search(r"Page 1 of \d+", p1) and "Customer ID" in p1: return "VZ_INTL_PAGEOF"
    if "Customer ID" in p1 and "Invoice Number" in p1: return "VZ_INTL_EN"
    return "UNKNOWN"


def locs(t, tpl):
    if tpl.startswith("VZ_US_STMT"):
        ids = re.findall(r"^\s*Circuit ID:\s*(\S+)", t, re.M)
    elif tpl in ("VZ_IN_GST_TAXINV", "VZ_XTRA_INV_UKJP"):
        ids = re.findall(r"\b([A-Z]\d[A-Z]\d{5})\b", t)
    elif tpl.startswith("NTT"):
        ids = []
    else:
        ids = re.findall(r"^\s*ID:\s*(\d{5,9}C|CW-[A-Z]\d+|[A-Z0-9-]+)\s+-", t, re.M)
    u = list(dict.fromkeys(ids))
    return f"{len(u)}|{';'.join(u[:3])}"


def period(t, tpl):
    ds = []
    if tpl.startswith("VZ_US_STMT"):
        for a, b in re.findall(r"Service Period (\d\d/\d\d/\d{4}) to (\d\d/\d\d/\d{4})", t):
            ds += [pdate(a, "mdy"), pdate(b, "mdy")]
    elif tpl in ("VZ_IN_GST_TAXINV", "VZ_XTRA_INV_UKJP"):
        for a, b in re.findall(r"(\d\d-[A-Za-z]{3}-\d\d)\s+(\d\d-[A-Za-z]{3}-\d\d)", t):
            for x in (a, b):
                d, m, y = x.split("-"); ds.append(date(2000 + int(y), MON[m.lower()], int(d)).isoformat())
    elif tpl.startswith("NTT"):
        m = re.search(r"Billing Period\s+(\S+)\s*-\s*(\S+)", t)
        if m: ds = [pdate(m.group(1), "mdy"), pdate(m.group(2), "mdy")]
    elif tpl == "VZ_INTL_PAGEOF":  # DD-MM-YYYY- \n DD-MM-YYYY
        ds = [pdate(a, "dmy") for x in re.findall(r"\b(?:REC|NRC|USG)\s+(\d\d-\d\d-\d{4})-|^\s{20,}(\d\d-\d\d-\d{4})\s*$", t, re.M) for a in x if a]
    else:  # 01Dec24-31Dec24 or single 25Feb24
        for d, m, y in re.findall(r"\b(\d\d)([A-Za-z]{3})(\d\d)\b", t):
            if m.lower() in MON:
                ds.append(date(2000 + int(y), MON[m.lower()], int(d)).isoformat())
    ds = sorted(x for x in ds if x)
    return f"{ds[0]}/{ds[-1]}" if ds else None


def extract(rec):
    t = text(rec["hash"], rec["path"])
    p1 = t.split("\f")[0]
    tpl = classify(p1, t)
    if tpl == "UNKNOWN" and "Statement Summary" in t[:6000]:  # US statements: cover page text is not in page-1 chunk
        p1 = t[:6000]; tpl = "VZ_US_STMT_NODE" if "Node No" in p1 else "VZ_US_STMT_SMB"
    o = dict(template=tpl, doc_kind="invoice", vendor="Verizon", customer_id=None, account_number=None,
             doc_number=None, doc_date=None, currency=None, total_amount=None)
    if tpl == "NOT_BILLING_NTT_GUIDE":
        o["vendor"] = "NTT"; return o, t
    if tpl == "NTT_CLOUD_COMM":
        o["vendor"] = "NTT Cloud Communications US"
        o["customer_id"] = g(r"#CP#1\s*\n\s*(\w+)", p1)
        o["doc_number"] = g(r"\b(INUS\d+)", p1)
        o["doc_date"] = pdate(g(r"\n\s*(\d\d/\d\d/\d{4})\s*\n\s*INUS", p1) or g(r"Invoice Date[^\n]*?(\d\d/\d\d/\d{4})", p1), "mdy")
        o["currency"] = "USD"
        # layout text has no reliable positions; use raw mode for the total
        raw = subprocess.run(["pdftotext", "-raw", f"{ROOT}/{rec['path']}", "-"], capture_output=True, text=True).stdout
        o["doc_number"] = o["doc_number"] or g(r"(INUS\d+)", raw)
        o["customer_id"] = g(r"#CP#1\s*\n(\w+)", raw)
        o["doc_date"] = pdate(g(r"\n(\d\d/\d\d/\d{4})\nINUS", raw), "mdy")
        o["total_amount"] = num(g(r"Total Amount \$\s*([\d,.]+)", raw))
        o["_period_src"] = raw
        return o, raw
    if tpl.startswith("VZ_US_STMT"):
        o["customer_id"] = g(r"Corporate ID:\s*(\S+)", p1)
        o["account_number"] = g(r"Bill Payer ID:\s*(\S+)", p1)
        o["doc_number"] = g(r"Invoice Number:\s*(\S+)", p1)
        o["doc_date"] = pdate(g(r"Invoice Date:\s*(\S+)", p1), "mdy")
        o["currency"] = "USD"
        o["total_amount"] = num(g(r"Total Current Charges\s+(\$[\d,.]+)", p1))
        o["vendor"] = "Verizon Business US (MCI)"
        return o, t
    if tpl in ("VZ_IN_GST_TAXINV", "VZ_XTRA_INV_UKJP"):
        o["customer_id"] = None
        o["account_number"] = g(r"(?:Account|Customer) Number\s+(\S+)", p1)
        o["doc_number"] = g(r"Invoice Number\s+(\S+)", p1)
        d = g(r"Invoice Date\s+(\S+)", p1)
        o["doc_date"] = pdate(d, "txt" if re.search(r"[A-Za-z]", d or "") else "dmy")
        o["currency"] = g(r"Billing Currency\s+([A-Z]{3})", p1)
        o["total_amount"] = last_num(r"Total Invoice Amount", p1)
        ent = g(r"(Verizon [A-Z][A-Za-z ]+?(?:Ltd|Limited|Private Limited|Pvt Ltd|GmbH|Inc))", t)
        o["vendor"] = ent or "Verizon"
        return o, t
    # Customer-ID family
    it = tpl == "VZ_INTL_IT"
    L = dict(cust=r"(?:Customer ID|ID cliente):\s*(\S+)", acc=r"(?:Account Number|Numero di conto):\s*(\S+)",
             dn=r"(?:Invoice Number|Credit Note Number|Numero fattura):\s*(\S+)",
             dd=r"(?:Invoice Date|Document Date|Data fattura):\s*([^\n]+?)\s*(?:\n|$)")
    o["customer_id"] = g(L["cust"], t)
    o["account_number"] = g(L["acc"], t) or g(r"Account Number:\s*(\S+)", t)
    o["doc_number"] = g(L["dn"], t)
    d = g(L["dd"], t)
    if d:
        o["doc_date"] = pdate(d, "txt" if re.search(r"[A-Za-z]", d) else "dmy")
    if tpl in ("VZ_CA_EC", "VZ_US_EC"):
        o["vendor"] = "Verizon Canada Ltd" if tpl == "VZ_CA_EC" else "Verizon US (MCI) Enterprise"
        o["currency"] = g(r"Total \(([A-Z]{3})\)", p1)
        o["total_amount"] = last_num(r"Total Current Charges", p1)
        return o, t
    m = re.search(r"\n\s*((?:NV )?Verizon [^\n]*?)(?:\s{2,}[^\n]*)?\n\s*([A-Z]{3})\s*\n", p1)
    if m: o["vendor"] = f"{m.group(1)} ({m.group(2)})"
    o["currency"] = g(r"(?:Billing Currency|Valuta fattura)\s*\(([A-Z]{3})\)", p1)
    if re.search(r"^\s*Credit Note\s*$", p1, re.M): o["doc_kind"] = "credit_note"
    elif re.search(r"^\s*Debit Note\s*$", p1, re.M): o["doc_kind"] = "debit_note"
    o["total_amount"] = last_num(r"(?:Total Current Charges|Totale addebiti correnti)", p1)
    return o, t


def main():
    recs = json.load(open(f"{ROOT}/analysis/batches/billing_docs.json"))
    rows = []
    for r in recs:
        o, t = extract(r)
        rows.append(dict(hash=r["hash"], path=r["path"], template=o["template"], doc_kind=o["doc_kind"], vendor=o["vendor"],
                         customer_id=o["customer_id"], account_number=o["account_number"], doc_number=o["doc_number"],
                         doc_date=o["doc_date"], billing_period=period(t, o["template"]), currency=o["currency"],
                         total_amount=o["total_amount"], pages=r["pages"], location_ids_found=locs(t, o["template"]),
                         dup_paths_count=len(r["all_paths"])))
    cols = list(rows[0])
    with open(f"{ROOT}/analysis/billing_index.csv", "w", newline="") as f:
        w = csv.DictWriter(f, cols); w.writeheader(); w.writerows(rows)
    print(len(rows), "rows")


if __name__ == "__main__":
    main()
