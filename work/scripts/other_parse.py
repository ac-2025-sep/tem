"""Deterministic line-item parsers for the less common Verizon/NTT templates (EZ TEM rebuild).
Run: python3 -I work/scripts/other_parse.py   (from the TEM dir)
Writes work/invoice_lines_other.csv and work/invoice_reconcile_other.csv.
Templates: VZ_US_STMT_NODE/SMB, VZ_IN_GST_TAXINV, VZ_XTRA_INV_UKJP, NTT_CLOUD_COMM, Verizon Hungary (not in billing_index)."""
import csv, json, os, re, subprocess
from datetime import date

ROOT = "/media/abhay/Workspace/Egon Zehnder/TEM"
CACHE = "/tmp/claude-1000/-media-abhay-Workspace-Egon-Zehnder-TEM/89559593-5640-49fd-89d5-ba41c22b9f71/scratchpad/other_txt"
COLS = "source_path template doc_kind invoice_no invoice_date account_number customer_id currency location_id service_id contract_ref circuit_id related_service_id service_name charge_type period_start period_end description amount discount net_amount original_invoice_ref page".split()
MON = {m: i + 1 for i, m in enumerate("jan feb mar apr may jun jul aug sep oct nov dec".split())}


def text(h, path):
    f = f"{CACHE}/{h}.txt"
    if not os.path.exists(f):
        os.makedirs(CACHE, exist_ok=True)
        subprocess.run(["pdftotext", "-layout", f"{ROOT}/{path}", f], stderr=subprocess.DEVNULL)
    return open(f, errors="ignore").read()


def us(s):  # '$1,428.48CR' -> -1428.48
    v = float(re.sub(r"[^\d.]", "", s))
    return -v if s.upper().endswith("CR") or s.startswith("-") else v


def eu(s):  # '- 1.562,48' -> -1562.48
    v = float(re.sub(r"[^\d,]", "", s).replace(",", "."))
    return -v if "-" in s else v


def en(s):  # '-1,234.50'
    return float(s.replace(",", ""))


def iso_mdy(s):
    m, d, y = s.split("/")
    return f"{y}-{m}-{d}"


def iso_txt(s):  # 01-Feb-25 | 01Aug25 | 03-Feb-2025 | 04 Aug 2025
    a, b, c = re.match(r"(\d{1,2})[ -]?([A-Za-z]{3})[a-z]*[ -]?(\d{2,4})", s).groups()
    c = int(c) + (2000 if len(c) == 2 else 0)
    return date(c, MON[b.lower()], int(a)).isoformat()


class Doc:
    def __init__(self, r, **kw):
        self.r, self.rows = r, []
        self.base = dict(source_path=r["path"], template=r["template"], doc_kind="invoice", invoice_no=r["doc_number"],
                         invoice_date=r["doc_date"], account_number=r["account_number"], customer_id=r["customer_id"],
                         currency=r["currency"], original_invoice_ref="")
        self.base.update(kw)

    def add(self, ctype, amount, desc="", discount=0.0, **kw):
        row = {c: "" for c in COLS}
        row.update(self.base)
        row.update(kw)
        row.update(charge_type=ctype, description=re.sub(r"\s+", " ", desc).strip(), amount=f"{amount:.2f}",
                   discount=f"{discount:.2f}", net_amount=f"{amount + discount:.2f}")
        self.rows.append(row)

    def total(self):
        return round(sum(float(x["net_amount"]) for x in self.rows), 2)


# ---------------------------------------------------------------- US statements (NODE / SMB)
MONEY = re.compile(r"\$[\d,]+\.\d+(?:CR)?")
DR = re.compile(r"(\d\d/\d\d/\d{4})\s+(?:to\s+)?(\d\d/\d\d/\d{4})")


def us_pages(t):
    L = t.replace("\f", "\n").split("\n")
    starts = [i for i, l in enumerate(L) if re.search(r"Invoice Number\s{2,}\d+\s*$", l)]
    pg = []
    for k, s in enumerate(starts):
        j = s - 1
        while j >= 0 and not L[j].strip():
            j -= 1
        pg.append([s, L[j].strip(), j])
    out = []
    for k, (s, title, tj) in enumerate(pg):
        end = pg[k + 1][2] if k + 1 < len(pg) else len(L)
        body = L[s:end]
        hdr = "\n".join(body[:8])
        n = re.search(r"Page Number\s+(\d+)", hdr)
        a = re.search(r"Account Number\s+(\S+)", hdr)
        out.append((title, int(n.group(1)) if n else k + 1, a.group(1) if a else "", body))
    return out


def us_parse(r, d):
    t = text(r["hash"], r["path"])
    corp = re.search(r"Corporation ID\s+(\d+)", t)
    d.base["customer_id"] = corp.group(1) if corp else r["customer_id"]
    bp = re.search(r"Bill Payer(?: ID:?)?\s+(\S+)", t)
    d.base["account_number"] = bp.group(1) if bp else r["account_number"]
    d.base["invoice_date"] = r["doc_date"]
    st = {}
    for title, pn, acct, body in us_pages(t):
        kind = {"Data Services - Dedicated Access Circuit Detail by Account": "Dedicated Access",
                "Data Services - Private IP Detail by Account": "Private IP",
                "Data Services - Managed Network Services Detail": "Managed Network Services",
                "Additional Charges Detail": "ADDL", "Additional Charges Summary": "LATE",
                "Voice Services - Inbound Usage/Features by Toll Free Number": "TOLL"}.get(title)
        if not kind:
            continue
        if st.get("kind") != kind:
            st.clear(); st.update(kind=kind, svc=None, loc=acct, circ=None, per=(None, None), pend=[], active=False)
        started, sect, tf, tfacct = False, "", None, acct
        svc, loc, circ, per, pend, active = st["svc"], st["loc"], st["circ"], st["per"], st["pend"], st["active"]
        if kind in ("Dedicated Access", "Private IP"):
            loc = acct
        for ln in body:
            s = ln.strip()
            if not started:
                started = s.startswith("Description")
                continue
            if not s or s.startswith("___"):
                continue
            mo = MONEY.findall(ln)
            first = ln.find("$") if mo else len(ln)
            common = dict(page=pn)
            if kind in ("Dedicated Access", "Private IP", "Managed Network Services"):
                m = re.match(r"Circuit ID:\s*(\S+)", s)
                m2 = re.match(r"^(\S+)/(G\d+)$", s)
                if m and kind != "Managed Network Services":
                    if m.group(1) != svc:
                        per, pend = (None, None), []
                    svc = circ = m.group(1); loc = acct; active = True
                    continue
                if m2 and kind == "Managed Network Services":
                    if m2.group(1) != svc:
                        per, pend = (None, None), []
                    svc, loc, circ = m2.group(1), m2.group(2), ""; active = True
                    continue
                if s.startswith("Total"):
                    if re.match(r"Total (Circuit ID|\S+/G\d+)", s):
                        active = False
                    continue
                if not active:
                    continue
                kw = dict(common, location_id=loc if kind != "Private IP" or True else acct, service_id=svc, circuit_id=circ,
                          service_name=kind, period_start=per[0] or "", period_end=per[1] or "")
                m = DR.search(s) if s.startswith("Service Period") else None
                if s.startswith("Service Period"):
                    if m:
                        per = (iso_mdy(m.group(1)), iso_mdy(m.group(2)))
                    pend = []
                    continue
                if s.startswith("Subtotal"):
                    pend = []
                    continue
                if s.startswith("Estimated Discounts"):
                    v = us(mo[-1]) if mo else 0
                    if v:
                        d.add("DISCOUNT", v, "Estimated discounts and promotions", **kw)
                    continue
                if s.startswith("Estimated Taxes"):
                    v = us(mo[-1]) if mo else 0
                    if v:
                        d.add("TAX", v, "Estimated taxes and surcharges", **kw)
                    continue
                if len(mo) >= 3 and per[0]:
                    parts = re.split(r"\s{2,}", ln[:first].strip())
                    desc = " ".join(pend + [parts[0]])
                    ex = " ".join(parts[1:])
                    desc = desc + ((f" qty={ex}" if ex.isdigit() else f" [{ex}]") if ex else "")
                    rec, nrc = us(mo[0]), us(mo[1])
                    if nrc:
                        d.add("NRC", nrc, desc, **kw)
                    if rec or not nrc:
                        d.add("REC", rec, desc, **kw)
                    pend = []
                elif per[0] and not mo:
                    pend.append(s)
            elif kind == "ADDL":
                if s.startswith("Total Additional"):
                    continue
                if s.startswith("Total"):
                    continue
                kw = dict(common, location_id=acct, service_name=sect)
                if s.startswith("Estimated Discounts"):
                    v = us(mo[-1]) if mo else 0
                    if v:
                        d.add("DISCOUNT", v, "Estimated discounts and promotions", **kw)
                    continue
                if s.startswith("Estimated Taxes"):
                    v = us(mo[-1]) if mo else 0
                    if v:
                        d.add("TAX", v, "Estimated taxes and surcharges", **kw)
                    continue
                if s.startswith("*"):
                    continue
                if len(mo) >= 3:
                    m = DR.search(ln)
                    ps, pe = (iso_mdy(m.group(1)), iso_mdy(m.group(2))) if m else ("", "")
                    desc = re.split(r"\s{2,}", ln[:first].strip())[0]
                    desc = DR.sub("", desc).strip() or ln[:first].strip().split("  ")[0]
                    rec, nrc = us(mo[0]), us(mo[1])
                    cnt = re.search(r"(\d+)\s+$", ln[:first])
                    q = f" qty={cnt.group(1)}" if cnt else ""
                    kw.update(period_start=ps, period_end=pe)
                    if nrc:
                        d.add("NRC", nrc, desc + q, **kw)
                    if rec or not nrc:
                        d.add("REC", rec, desc + q, **kw)
                elif not mo:
                    sect = s
            elif kind == "LATE":
                if not mo and not s.startswith(("Total", "Estimated", "*")):
                    sect = s
                elif "Late Payment" in sect and not s.startswith("Total") and len(mo) >= 3:
                    d.add("OTHER", us(mo[1]) + us(mo[0]), "Late Payment Fee", page=pn, location_id=d.base["account_number"],
                          service_name="Late Payment Fee")
            elif kind == "TOLL":
                if s.startswith(("Total", "*")):
                    continue
                if re.fullmatch(r"\d{3}-\d{3}-\d{4}", s):
                    tf = s
                elif re.fullmatch(r"[A-Z]\d{5,}", s):
                    tfacct = s
                elif len(mo) >= 5:
                    parts = re.split(r"\s{2,}", ln[:first].strip())
                    desc = f"{parts[0]} calls={parts[1] if len(parts) > 1 else ''} minutes={parts[2] if len(parts) > 2 else ''}"
                    kw = dict(common, location_id=tfacct, service_id=tf or "", service_name="Toll Free Inbound")
                    ch, sur, dis, tax = us(mo[0]), us(mo[1]), us(mo[2]), us(mo[3])
                    d.add("USAGE", ch, desc, **kw)
                    if sur:
                        d.add("OTHER", sur, desc + " surcharges", **kw)
                    if dis:
                        d.add("DISCOUNT", dis, desc, **kw)
                    if tax:
                        d.add("TAX", tax, desc, **kw)
        st.update(svc=svc, loc=loc, circ=circ, per=per, pend=pend, active=active)
    us_summary_fallback(d, t)


def us_summary_fallback(d, t):
    """Where detail pages are missing/partial for a circuit/service, use consolidated 'Data Services Summary' rows."""
    summ, cat, key = {}, "", None
    for title, pn, acct, body in us_pages(t):
        if title != "Data Services Summary":
            continue
        for ln in body:
            s = ln.strip()
            mo = MONEY.findall(ln)
            ind = len(ln) - len(ln.lstrip())
            if not mo and s and not s.startswith(("Total", "___", "Description", "Corporation", "Estimated", "Usage", "Charges", "WIESEN", "ZURICH", "EGON ZEHNDER")):
                m = re.match(r"Circuit ID:\s*(\S+)$", s)
                if m:
                    key = m.group(1)
                elif ind == 4 and re.fullmatch(r"[\w.-]+", s):
                    key = s
                elif ind == 2:
                    cat = s
            if s.startswith("Service Period") and len(mo) == 6 and key:
                m = DR.search(s)
                summ.setdefault(key, []).append((pn, cat, iso_mdy(m.group(1)), iso_mdy(m.group(2)), [us(x) for x in mo]))
    for key, rows in summ.items():
        dsum = round(sum(float(x["net_amount"]) for x in d.rows if x["service_id"] == key), 2)
        ssum = round(sum(r[4][5] for r in rows), 2)
        if abs(dsum - ssum) <= 0.02:
            continue
        old = [x for x in d.rows if x["service_id"] == key]
        loc = next((x["location_id"] for x in old), "")
        d.rows[:] = [x for x in d.rows if x["service_id"] != key]
        for pn, cat, a, b, v in rows:
            kw = dict(page=pn, service_id=key, circuit_id=key if key.startswith(("W", "BCBH")) else "", location_id=loc,
                      service_name=cat, period_start=a, period_end=b)
            for ct, val in (("USAGE", v[0]), ("REC", v[1]), ("NRC", v[2]), ("DISCOUNT", v[3]), ("TAX", v[4])):
                if val:
                    d.add(ct, val, "summary-level line (no detail page)", **kw)


# ---------------------------------------------------------------- Xtraconnect (India GST, UK/JP)
def xtra_parse(r, d):
    t = text(r["hash"], r["path"])
    pages = t.split("\f")
    acct = re.search(r"(?:Account|Customer) Number\s+(\S+)", t).group(1)
    d.base["account_number"] = acct
    d.base["customer_id"] = acct
    m = re.search(r"Invoice Date\s+(\S+)", t)
    ds = m.group(1)
    d.base["invoice_date"] = iso_txt(ds) if re.match(r"\d+-[A-Za-z]", ds) else "-".join(reversed(ds.split("/")))
    d.base["currency"] = re.search(r"Billing Currency\s+(\w+)", t).group(1)
    cur = d.base["currency"]
    for k, lab in (("DISCOUNT", "Total Discounts"), ("TAX", "Total (?:Tax|VAT)")):
        mm = re.search(rf"^\s*(?:.*\s)?{lab}\s+(?:[\d,]+\s+)?(-?[\d,]+\.\d\d)\s*$", t, re.M)
        if mm and en(mm.group(1)):
            d.add(k, en(mm.group(1)), "Total tax" if k == "TAX" else "Total discounts", page=1, service_name="Tax")
    ctype, loc, grp, hdr = "REC", "", "", None
    ids = {}

    def flush():
        nonlocal hdr
        if hdr and not hdr["n"]:
            d.add(hdr["ctype"], hdr["amt"], hdr["desc"], **hdr["kw"])
        hdr = None
    for pn, pg in enumerate(pages, 1):
        L = pg.split("\n")
        in_usage_grp = False
        for ln in L:
            s = ln.strip()
            if s in ("Recurring Charges", "Non-Recurring Charges", "Usage Charges"):
                flush(); ctype = {"R": "REC", "N": "NRC", "U": "USAGE"}[s[0]]
                continue
            m = re.match(r"(.+?)\s+Charges$", s)
            if m and "," in m.group(1) and len(s) < 60:
                flush(); loc = m.group(1)
                continue
            if s.startswith("➲"):
                flush(); grp = s[1:].strip()
                m = re.match(r"(.+?)\s{2,}([\d,]+\.\d\d)$", s[1:].strip())
                if m:  # usage group header with amount (UK)
                    grp = m.group(1)
                continue
            m = re.match(r"-\s+(.+?)\s{2,}(-?[\d,]+\.\d\d)\s*$", s)
            if m:
                flush()
                wid = re.search(r"\bW[0-9A-Z]{1}[A-Z0-9]\d{5}\b", m.group(1))
                w = wid.group(0) if wid else ""
                hdr = dict(n=0, amt=en(m.group(2)), desc=m.group(1), ctype=ctype,
                           kw=dict(page=pn, location_id=loc, service_id=w, circuit_id=w, service_name=grp))
                continue
            m = re.match(r"●\s+Location:\s*(.+)", s)
            if m:
                loc = m.group(1).strip()
                if hdr:
                    hdr["kw"]["location_id"] = loc
                continue
            m = re.match(r"●\s+(.+?)\s+(\d\d-[A-Za-z]{3}-\d\d)\s+(\d\d-[A-Za-z]{3}-\d\d)\s+(-?[\d,]+\.\d\d)$", s)
            if m and hdr:
                hdr["n"] += 1
                desc = re.sub(r"\btaxable\b", "", m.group(1)).strip()
                w2 = re.search(r"\bW[0-9A-Z]{1}[A-Z0-9]\d{5}\b", desc)
                kw = dict(hdr["kw"], period_start=iso_txt(m.group(2)), period_end=iso_txt(m.group(3)),
                          related_service_id=w2.group(0) if w2 and w2.group(0) != hdr["kw"]["service_id"] else "")
                d.add(hdr["ctype"], en(m.group(4)), f"{hdr['desc']} | {desc}" if False else desc, **kw)
                continue
            m = re.match(r"●\s+(.+?)\s{2,}([\d,]+)\s+([\d,]+\.\d\d)\s+([\d,]+\.\d\d)$", s)  # UK usage bullet (summarised below)
            if m:
                continue
            if s.startswith("Summary by Usage Group"):
                in_usage_grp = True
                continue
            if in_usage_grp:
                if s.startswith("Total"):
                    in_usage_grp = False
                    continue
                m = re.match(r"(.+?)\s{2,}([\d,]+)\s+([\d,]+\.\d\d)\s+(-?[\d,]+\.\d\d)$", s)
                if m:
                    d.add("USAGE", en(m.group(4)), f"{m.group(1)} calls={m.group(2)} minutes={m.group(3)}", page=pn,
                          service_name="Direct Voice - Direct Access")
        flush()


# ---------------------------------------------------------------- NTT
def ntt_parse(r, d):
    t = text(r["hash"], r["path"])
    p1 = t.split("SUMMARY PAGE")[0]
    mm = re.search(r"Billing Period\s+(\d\d/\d\d/\d{4})\s*-\s*(\d\d/\d\d/\d{4})", p1)
    bp = (iso_mdy(mm.group(1)), iso_mdy(mm.group(2))) if mm else ("", "")
    d.base["invoice_date"] = r["doc_date"]
    d.base["account_number"] = r["customer_id"]
    prod, last, sect = "", None, ""
    L = p1.split("\n")
    start = next(i for i, l in enumerate(L) if l.strip().startswith("DESCRIPTION"))
    item = re.compile(r"^(.*?)\s+(-?[\d,]+\.\d\d)\s+(\d\d/\d\d/\d{4})(?:\s*-\s*(\d\d/\d\d/\d{4}))?\s+(-?[\d,]+\.\d\d)$")
    for ln in L[start + 1:]:
        s = re.sub(r"\s+", " ", ln.strip())
        if not s or s.startswith(("Balance", "(*)", "Mean of", "CHECK", "WIRE")):
            if s.startswith("Balance"):
                break
            continue
        m = item.match(s)
        if m:
            desc, dis, a, b, amt = m.groups()
            qm = re.match(r"(\d+) x (.+?) \(UnitPrice: ([\d.]+) \$\)$", desc)
            if qm:
                desc = f"{qm.group(2)} qty={qm.group(1)} unit={qm.group(3)}"
            else:
                um = re.search(r"(\d+)\*([\d.]+)\$", desc)
                if um:
                    desc = re.sub(r"\s*\d+\*[\d.]+\$", "", desc) + f" qty={um.group(1)} unit={um.group(2)}"
            ct = "USAGE" if sect == "Usage" else "NRC" if sect.startswith("Other") else "REC"
            d.add(ct, en(amt), desc, discount=-en(dis) if en(dis) else 0.0, service_name=prod, page=1,
                  period_start=iso_mdy(a), period_end=iso_mdy(b or a))
            last = len(d.rows) - 1
            continue
        m = re.match(r"^(Federal Tax|State Tax|County Tax|Local Tax|Telecom Surcharges & Fees|Federal Universal Services Fund Contribution)\s+(-?[\d,]+\.\d\d)$", s)
        if m:
            if en(m.group(2)):
                d.add("TAX", en(m.group(2)), m.group(1), service_name=prod, page=1, period_start=bp[0], period_end=bp[1])
            continue
        m = re.match(r"^(.+?)\s+(-?[\d,]+\.\d\d)$", s)
        if m and not re.search(r"\d\*", s):
            if m.group(1) in ("Recurring Fee", "Usage") or m.group(1).startswith("Other"):
                sect = m.group(1)
            else:
                prod = m.group(1)
            continue
        # continuation line of previous item (e.g. 'Dynamic Emergency ... 1*5320.9$')
        if last is not None:
            row = d.rows[last]
            um = re.search(r"(\d+)\*([\d.]+)\$", s)
            row["description"] += " " + re.sub(r"\s*\d+\*[\d.]+\$", "", s).strip()
            if um and "qty=" not in row["description"]:
                row["description"] = row["description"].strip() + f" qty={um.group(1)} unit={um.group(2)}"
    for x in d.rows:
        x["description"] = x["description"].strip()


# ---------------------------------------------------------------- Verizon Hungary
def hu_parse(r, d):
    t = text(r["hash"], r["path"])
    i = [m.start() for m in re.finditer(r"^\s+Page 1\s*$", t, re.M)][-1]
    t = t[i:]
    hdr = lambda lab: re.search(lab + r":\s+(.+?)\s*$", t, re.M).group(1)
    d.base.update(customer_id=hdr("Customer ID"), account_number=hdr("Account Number"), invoice_no=hdr("Invoice Number"),
                  invoice_date=iso_txt(hdr("Invoice Date")), currency="USD")
    d.base["template"] = "VZ_HU_INV"
    tot = re.search(r"Total Current Charges\s+[\d.,]+\s+(-?\s?[\d.]+,\d\d)", t)
    d.header_total = eu(tot.group(1))
    loc = svc = ctr = rel = name = ""
    cur = None
    pn = 1
    num = r"-?\s?\d{1,3}(?:\.\d{3})*,\d\d"
    row = re.compile(rf"^\s*(.*?)\s+(\d\d[A-Za-z]{{3}}\d\d)(?:-(\d\d[A-Za-z]{{3}}\d\d))?\s+(REC|NRC|USAGE|[A-Z]{{3,5}})\b\s*(?:(\d+ Unit\(s\))\s*)?((?:{num}\s*)*)$")

    def flush():
        nonlocal cur
        if cur:
            kw = cur["kw"]
            d.add(cur["ct"], cur["amt"], cur["desc"], **kw)
            if cur["dis"]:
                d.add("DISCOUNT", cur["dis"], cur["desc"], **kw)
        cur = None
    for ln in t.split("\n"):
        pm = re.match(r"^\s+Page (\d+)\s*$", ln)
        if pm:
            pn = int(pm.group(1)); continue
        s = ln.strip()
        m = re.match(r"ID:\s*(\S+) - ", s)
        if m:
            flush(); loc = m.group(1); continue
        m = re.match(r"(.+?) - Service ID:\s*(\d+)\s+Contract/SOF Number:\s*(\S+)", s)
        if m:
            flush(); name, svc, cn = m.groups(); ctr = rel = ""; kwc = cn; cref = cn; continue
        m = re.match(r"Circuit ID:\s*(\S+)", s)
        if m:
            ctr = m.group(1); continue
        m = re.match(r"Related Service:\s*(.+)", s)
        if m:
            rel = ";".join(re.findall(r"\d{6,}", m.group(1))); continue
        if s.startswith("Total "):
            flush(); continue
        m = row.match(ln)
        if m and svc:
            flush()
            desc, a, b, ct, unit, nums = m.groups()
            v = [eu(x) for x in re.findall(num, nums)]
            amt, dis = (v[0], v[1]) if len(v) == 3 else (v[0], 0.0) if v else (0.0, 0.0)
            kw = dict(page=pn, location_id=loc, service_id=svc, contract_ref=cref, circuit_id=ctr, related_service_id=rel,
                      service_name=name, period_start=iso_txt(a), period_end=iso_txt(b or a))
            if unit:
                desc += " qty=" + unit.split()[0]
            cur = dict(ct=ct, amt=amt, dis=dis, desc=desc, kw=kw)
        elif cur and s and not re.match(r"(Description|Location|Charge|Page|Solution|Name)", s):
            cur["desc"] += " " + s
    flush()


# ---------------------------------------------------------------- main
def main():
    idx = list(csv.DictReader(open(f"{ROOT}/analysis/billing_index.csv")))
    docs = [r for r in idx if r["template"] in ("VZ_US_STMT_NODE", "VZ_US_STMT_SMB", "VZ_IN_GST_TAXINV", "VZ_XTRA_INV_UKJP", "NTT_CLOUD_COMM")]
    hu = []
    for f in ("contracts_2.jsonl", "contracts_3.jsonl"):
        for l in open(f"{ROOT}/analysis/{f}"):
            j = json.loads(l)
            if j.get("doc_type") == "other" and "ungar" in (j.get("summary") or "") + (j.get("vendor_entity") or ""):
                hu.append(dict(hash=j["hash"], path=j["path"], template="VZ_HU_INV", doc_kind="invoice", doc_number="",
                               doc_date="", account_number="", customer_id="", currency="USD", total_amount=""))
    out, rec, seen = [], [], {}
    for r in docs + hu:
        d = Doc(r)
        tpl = r["template"]
        d.header_total = float(r["total_amount"]) if r["total_amount"] else None
        {"VZ_US_STMT_NODE": us_parse, "VZ_US_STMT_SMB": us_parse, "VZ_IN_GST_TAXINV": xtra_parse,
         "VZ_XTRA_INV_UKJP": xtra_parse, "NTT_CLOUD_COMM": ntt_parse, "VZ_HU_INV": hu_parse}[tpl](r, d)
        no = d.base["invoice_no"]
        dup = seen.get((tpl, no), "")
        if not dup:
            seen[(tpl, no)] = r["path"]
        else:
            pass
        if d.header_total is not None and d.header_total < 0:
            for x in d.rows:
                x["doc_kind"] = "credit_note"
        if not dup:
            out += d.rows
        s = d.total()
        diff = round(s - d.header_total, 2) if d.header_total is not None else ""
        rec.append(dict(source_path=r["path"], template=d.base["template"], invoice_no=no, currency=d.base["currency"],
                        header_total=d.header_total, lines_sum=s, diff=diff, n_lines=len(d.rows),
                        status="OK" if diff != "" and abs(diff) < 0.025 else "FAIL", dup_of=dup, lines_emitted=0 if dup else len(d.rows)))
    os.makedirs(f"{ROOT}/work", exist_ok=True)
    with open(f"{ROOT}/work/invoice_lines_other.csv", "w", newline="") as f:
        w = csv.DictWriter(f, COLS); w.writeheader(); w.writerows(out)
    with open(f"{ROOT}/work/invoice_reconcile_other.csv", "w", newline="") as f:
        w = csv.DictWriter(f, list(rec[0])); w.writeheader(); w.writerows(rec)
    print(len(out), "lines;", sum(x["status"] == "OK" for x in rec), "/", len(rec), "reconciled")


if __name__ == "__main__":
    main()
