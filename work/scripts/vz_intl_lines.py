"""Deterministic line-item parser: Verizon INTL_EN/CN/IT/PAGEOF + CA_EC/US_EC invoices.
Run: python3 -I work/scripts/vz_intl_lines.py   (from TEM dir; needs pdftotext; text cached in work/.txtcache)
Writes work/invoice_lines.csv. Reconcile/CSV compare: work/scripts/vz_intl_validate.py"""
import csv, os, re, subprocess, sys
from datetime import date
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))   # TEM root
CACHE = f"{ROOT}/work/.txtcache"
SCOPE = {"VZ_INTL_EN", "VZ_INTL_CN", "VZ_INTL_IT", "VZ_INTL_PAGEOF", "VZ_CA_EC", "VZ_US_EC"}
MON = {m: i + 1 for i, m in enumerate("jan feb mar apr may jun jul aug sep oct nov dec".split())}
MON.update(gen=1, mag=5, giu=6, lug=7, ago=8, set=9, ott=10, dic=12)
COLS = "source_path template doc_kind invoice_no invoice_date account_number customer_id currency location_id service_id contract_ref circuit_id related_service_id service_name charge_type period_start period_end description amount discount net_amount original_invoice_ref page tax line_total raw_type".split()


def text(h, path):
    f = f"{CACHE}/{h}.txt"
    if not os.path.exists(f):
        os.makedirs(CACHE, exist_ok=True)
        subprocess.run(["pdftotext", "-layout", f"{ROOT}/{path}", f], stderr=subprocess.DEVNULL)
    return open(f, errors="ignore").read()


def num(s, it=False):
    s = s.strip()
    neg = "-" in s
    s = re.sub(r"[^\d.,]", "", s.replace("'", ""))
    if it or re.search(r",\d{1,2}$", s): s = s.replace(".", "").replace(",", ".")
    else: s = s.replace(",", "")
    return -float(s) if neg else float(s)


NUMRX = re.compile(r"(?<![\w.,/-])(-\s?)?(?:-)?\$?(\d[\d',.]*\d|\d)(?![\w])")
PER_A = r"\d{2}[A-Za-z]{3}\d{2}(?:-\d{2}[A-Za-z]{3}\d{2})?"
PER_P = r"\d{2}-\d{2}-\d{4}-?"
ROW = re.compile(r"^(?P<d>.*?)\s*(?:\b(?P<t1>REC|NRC|ADJ|USG|USA|OTH|CE)\b\s+)?(?P<p>%s|%s)(?:\s+\b(?P<t2>REC|NRC|ADJ|USG|USA|OTH|CE)\b)?(?P<r>.*)$" % (PER_A, PER_P))
QTY = re.compile(r"\b\d[\d,.]*\s+(?:Unit\(s\)|Minutes?|MB|GB|Mbps|Calls?|Each|Month\(s\)|Day\(s\)|Hour\(s\)|Hours?|Units?)(?!\w)", re.I)
HDRLBL = ("Amount", "Promotions", "Taxes", "Surcharges", "GST/HST", "PST/QST", "Total")
SKIP = re.compile(r"^\s*(Total |Customer ID|Account Number|Invoice Date|Invoice Number|Document Date|Credit Note Number|Page \d|Pagina|ID cliente|Numero|Data fattura|Location /|ID - Name|Solution /|\s*$)")


def pdate(s):
    if s is None: return ""
    m = re.match(r"(\d{2})([A-Za-z]{3})(\d{2})$", s)
    if m: return date(2000 + int(m[3]), MON[m[2].lower()], int(m[1])).isoformat()
    m = re.match(r"(\d{2})-(\d{2})-(\d{4})$", s)
    if m: return date(int(m[3]), int(m[2]), int(m[1])).isoformat()
    return ""


def header_cols(line):
    """right-edge x of each money column label in a detail header line"""
    out = []
    for m in re.finditer(r"Amount|Promotions|Taxes\s*/\s*VAT|Taxes\s*&|Surcharges|GST/HST|PST/QST|Total\s*\(\w+\)|Importo|Totale", line):
        lbl = m.group(0)
        k = "amt" if lbl in ("Amount", "Importo") else "disc" if lbl == "Promotions" else "tot" if lbl.startswith("Tot") else "tax"
        if lbl.startswith("Taxes") and "&" in lbl:  # "Taxes &" label sits on 1st line, "Surcharges" on 2nd - skip dup
            continue
        out.append((k, m.end()))
    return out


def assign(nums, cols, tot_hint=None):
    """nums: [(value,endx)]; return amt,disc,tax,total"""
    vals = [v for v, _ in nums]
    if not vals: return 0.0, 0.0, 0.0, 0.0
    T = vals[-1]
    amt = vals[0]
    d = t = 0.0
    mids = nums[1:-1] if len(nums) > 1 else []
    tax_cols = [x for k, x in cols if k == "tax"]
    for v, x in mids:
        # nearest column by right edge
        best = min(cols, key=lambda c: abs(c[1] - x))[0] if cols else None
        if best == "disc": d += v
        elif best == "tax": t += v
        else:
            if v < 0: d += v
            else: t += v
    if len(nums) == 1: amt = T
    return amt, d, t, T


def parse_doc(rec, t):
    tpl = rec["template"]
    it = tpl == "VZ_INTL_IT"
    pages = t.split("\f")
    if it:  # drop English translation duplicate pages
        for i, p in enumerate(pages):
            if "Translation" in p[:2500]:
                pages = pages[:i]; break
    kind = rec["doc_kind"]
    out = []
    loc = svc = con = circ = rel = sname = None
    orig = ""
    cols = []
    cur = None  # current row dict awaiting continuation
    in_detail = False
    ctx_page = 0

    def flush():
        nonlocal cur
        if cur:
            cur["description"] = re.sub(r"\s+", " ", cur["description"]).strip()
            out.append(cur)
        cur = None

    for pno, pg in enumerate(pages, 1):
        lines = pg.split("\n")
        for hi, hl in enumerate(lines[:14]):
            if re.search(r"(Invoice Number|Credit Note Number|Numero fattura):", hl):
                lines = [x for x in lines[hi + 1:] if not re.match(r"^\s*(Toronto ON .*|[A-Z]{3}|(NV )?Verizon[^\d]*)$", x)] if False else lines[hi + 1:]
                k = 0
                while k < len(lines) and k < 4 and re.match(r"^\s*(Toronto ON .*|[A-Z]{3}|(NV )?Verizon[^\d]*|)$", lines[k]): k += 1
                lines = lines[k:]
                break
        vend_seen = False
        for ln in lines:
            s = ln.strip()
            if not s: continue
            if re.search(r"Promotions", ln) and re.search(r"Total\s*\(", ln):
                c = header_cols(ln)
                if c: cols = c
                continue
            if SKIP.match(ln) and not s.startswith("Total "):
                if re.match(r"\s*(Description|Charge)\b", ln): pass
                else: continue
            m = re.match(r"^\s*ID:\s*(\d{5,9}C|CW-\w+|[A-Z0-9-]+)(?:\s+-|\s*$)", ln)
            if m:
                flush(); loc = m[1]; in_detail = True; svc = con = circ = rel = sname = None; continue
            if not in_detail: continue
            if re.search(r"Promotions", ln) and re.search(r"Total\s*\(", ln):
                c = header_cols(ln)
                if c: cols = c
                continue
            if re.match(r"^\s*(Charge\s|Description\s|Type\s|Solution)", ln) and not ROW.match(ln):
                if re.search(r"Quantity|Charge|Description", s) and len(s) < 100: continue
            if re.match(r"^\s*Total\b", ln):
                flush()
                if re.match(r"^\s*Total \d{7,}\b", ln) is None and re.match(r"^\s*Total (\d{5,9}C|[A-Z]{1,3}\d{5,})", ln): pass
                continue
            if re.match(r"^\s*Vendor|^\s*Verizon\s+\w", ln) and not vend_seen and pno > 0 and ln.startswith((" ", "V")) and re.match(r"^\s*(Verizon|NV Verizon)[A-Za-z .,]*$", ln):
                vend_seen = True; continue
            if re.match(r"^\s*[A-Z]{3}\s*$", ln): continue
            # service block header (layout B)
            m = re.match(r"^\s*(?P<n>.*?)\s*-?\s*Service ID:\s*(?P<s>.+?)(?:\s+Contract/SOF Number:\s*(?P<c>\S+))?\s*(?:\(continued\))?\s*$", ln)
            if m:
                flush(); svc, con = m["s"], m["c"] or ""; sname = m["n"].strip(" -") or sname; circ = rel = None; continue
            m = re.match(r"^\s*(?P<n>[A-Z][^()]*?)\s+Contract/SOF Number:\s*(?P<c>\S+)", ln)
            if m and "Service ID" not in ln:
                flush(); svc, con, sname, circ, rel = None, m["c"], m["n"].strip(), None, None; continue
            m = re.match(r"^\s*Circuit ID:\s*(\S+)", ln)
            if m: flush(); circ = m[1]; continue
            m = re.match(r"^\s*Related Service:\s*(.*)", ln)
            if m: flush(); rel = ";".join(re.findall(r"\d{7,}", m[1])); continue
            m = re.match(r"^\s*Original Invoice:\s*(\S+)\s+(\S+)", ln)
            if m:
                orig = m[1]
                if cur: cur["original_invoice_ref"] = orig
                continue
            if re.match(r"^\s*(HSN/SAC|Discount\s*:|\(continued\))", ln) or s.endswith("(continued)"):
                if cur and s.startswith("Discount"): cur["description"] += " | " + s
                continue
            mm = ROW.match(ln)
            if mm and (mm["t1"] or mm["t2"] or re.search(r"\d", mm["r"] or "")):
                flush()
                d = mm["d"].strip()
                # layout A: "Product - (sid/contract)"
                ma = re.search(r"\((\d{5,}|[A-Z0-9-]+)/([^)]+)\)", d)
                mb = None if ma else re.search(r" - \(([A-Za-z][^()/]*)\)", d)
                if mb:
                    svc, con, sname, circ, rel = mb[1].strip(), "", d[:mb.start()].strip(" -"), None, None
                if ma:
                    svc, con = ma[1], ma[2]
                    sname = d[:ma.start()].strip(" -")
                    circ = rel = None
                    d = d
                r = mm["r"] or ""
                r = QTY.sub(" ", r)
                nums = [(num(x.group(0), it), x.end()) for x in NUMRX.finditer(r)]
                # absolute end positions for column mapping
                off = ln.find(r) if r else 0
                base = len(ln) - len(r)
                nums = [(num(x.group(0), it), base + x.end()) for x in NUMRX.finditer(r)]
                amt, disc, tax, tot = assign(nums, cols)
                typ = mm["t1"] or mm["t2"] or ""
                pp = mm["p"]
                if re.match(PER_A, pp):
                    ps, pe = pdate(pp[:7]), pdate(pp[8:15]) if len(pp) > 8 else pdate(pp[:7])
                else:
                    ps, pe = pdate(pp.rstrip("-")), ""
                cur = dict(location_id=loc, service_id=svc, contract_ref=con, circuit_id=circ, related_service_id=rel,
                           service_name=sname, ptype=typ, period_start=ps, period_end=pe, description=d, amount=amt,
                           discount=disc, tax=tax, line_total=tot, original_invoice_ref=orig if typ == "ADJ" else "",
                           page=pno, nn=len(nums))
                continue
            # PAGEOF period end on its own line
            if cur and re.match(r"^\s*\d{2}-\d{2}-\d{4}\s*$", ln) and not cur["period_end"]:
                cur["period_end"] = pdate(s); continue
            if cur and ln.startswith(" "):
                mc = re.match(r"^\s*\((\d{5,})/([^)]+)\)\s*$", ln)
                if mc and (not cur["service_id"] or cur["description"].endswith(" -")):  # service ref wrapped onto its own line;
                    cur["service_id"], cur["contract_ref"] = mc[1], mc[2]; svc, con = mc[1], mc[2]   # "Product -" + wrapped ref must not
                    cur["service_name"] = sname = cur["description"].strip(" -"); circ = rel = None   # keep the previous service's id
                else:
                    cur["description"] += " " + s
    flush()
    return out


def main():
    idx = [r for r in csv.DictReader(open(f"{ROOT}/analysis/billing_index.csv")) if r["template"] in SCOPE]
    rows = []
    for rec in idx:
        t = text(rec["hash"], rec["path"])
        for o in parse_doc(rec, t):
            sign = -1 if rec["doc_kind"] == "credit_note" else 1
            ty = o["ptype"]
            desc = o["description"]
            ct = {"REC": "REC", "NRC": "NRC", "USG": "USAGE", "USA": "USAGE", "ADJ": "ADJ", "OTH": "OTHER", "CE": "REC"}.get(ty, "OTHER")
            if ct == "ADJ" and re.search(r"credit", desc, re.I): ct = "CREDIT"
            a, d, tx, tt = (o[k] * sign for k in ("amount", "discount", "tax", "line_total"))
            rows.append(dict(source_path=rec["path"], template=rec["template"], doc_kind=rec["doc_kind"], invoice_no=rec["doc_number"],
                             invoice_date=rec["doc_date"], account_number=rec["account_number"], customer_id=rec["customer_id"],
                             currency=rec["currency"], location_id=o["location_id"], service_id=o["service_id"], contract_ref=o["contract_ref"],
                             circuit_id=o["circuit_id"], related_service_id=o["related_service_id"], service_name=o["service_name"],
                             charge_type=ct, period_start=o["period_start"], period_end=o["period_end"], description=desc,
                             amount=round(a, 2), discount=round(d, 2), net_amount=round(a + d, 2),
                             original_invoice_ref=o["original_invoice_ref"], page=o["page"], tax=round(tx, 2), line_total=round(tt, 2), raw_type=ty))
    os.makedirs(f"{ROOT}/work", exist_ok=True)
    with open(f"{ROOT}/work/invoice_lines.csv", "w", newline="") as f:
        w = csv.DictWriter(f, COLS); w.writeheader(); w.writerows(rows)
    print(len(idx), "docs", len(rows), "lines")


if __name__ == "__main__":
    main()
