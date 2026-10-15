"""Deterministic Verizon SOF/amendment price extractor. Run: python3 -I extract_vz_prices.py"""
import csv, json, re, subprocess, sys
from pathlib import Path

ROOT = Path("/media/abhay/Workspace/Egon Zehnder/TEM")
WORK = ROOT / "work"
AMT = r"(?:-?\(?\d[\d,'.]*\)?|N/A|Included\d*)"
ROW = re.compile(r"^(?P<left>.*?)\s*\b(?P<act>[A-Z]{4,})\b\s+(?:(?P<qty>\d+|N/A)(?:\s+[A-Za-z]+\(s\))?\s+)?(?P<mrc>%s)\s+(?P<nrc>%s)\s*$" % (AMT, AMT))
ACTS = {"ADDED", "REMOVED", "CHANGED", "EXISTING", "NEW", "CHANGE", "UNCHANGED", "MOVED", "RENEWED", "DELETED", "CANCELLED", "CANCELED"}
ROW1 = re.compile(r"^(?P<left>.*?)\s*\b(?P<act>[A-Z]{4,})\b(?P<mid>.*?)(?P<mrc>%s)\s*$" % AMT)  # single-amount row; column decides MRC vs NRC
PLAIN = re.compile(r"^\s*(?P<left>[A-Za-z].*?)\s{2,}(?P<mrc>%s)\s+(?P<nrc>%s)\s*$" % (AMT, AMT))  # delivery-charge rows
SVC = re.compile(r"^\s*(?:(?P<name>.+?),\s*)?Service ID:\s*(?P<id>\d+|See Appendix)\s*$")
LOC = re.compile(r"^\s*Location ID:\s*(?P<id>[A-Z0-9]+)\b\s*-?\s*(?P<city>.*)$")
ITEM_START = re.compile(r"^[A-Z][A-Za-z/&,() ]{1,40} - \S")
NOISE = re.compile(r"(Amendment ID:|CCR Package ID|Contract ID:|Reference ID:|CCR Ref ID|Routing Code|Quote ID|^\s*- Page \d+|CONFIDENTIAL|Envelope ID|^\s*(Activity|Type|Quantity|MRC|NRC|\(USD\)|\(\w{3}\))(\s+(Type|Quantity|MRC|NRC|\(\w{3}\)))*\s*$|Service Detail for Location|\(See Appendix|Service Order terminations|applicable commitment|Previous Order Section|Appendix|Service Summary|Services Sold and Provided)", re.I)
END = re.compile(r"(Subtotal|\bTotal\b.*excluding|Delivery Charges Subtotal)", re.I)


CD = False  # per-document flag: comma is the decimal mark


def num(s):
    if s is None: return None
    s = s.strip()
    if s.upper() == "N/A" or s.lower().startswith("included"): return None
    neg = s.startswith("-") or s.startswith("(")
    s = s.replace("'", "").strip("()-")
    if CD or ("," in s and "." in s and s.rfind(",") > s.rfind(".")):
        s = s.replace(".", "").replace(",", ".")
    else:
        s = s.replace(",", "")
    s = re.sub(r"[^\d.]", "", s)
    if not s: return None
    v = float(s)
    return -v if neg else v


def clean_name(n):
    n = re.sub(r"[\s+^*]+$", "", n or "").strip()
    n = re.sub(r"\s*\+?\s+for \w+$", "", n)
    return n.replace("Equipment Related", "Equipment and Related")


def doc_kind(t):
    # earliest title phrase wins
    pats = [("cancellation", r"Cancellation Notification"), ("add_change", r"Add/Change Form"),
            ("sof", r"Service Order Form|Amendment and Service Order"), ("amendment", r"\n\s*(?:\w+-\w+ )?Amendment\s*\n|Amendment\s*\n\s*to the")]
    hits = [(m.start(), k) for k, pt in pats if (m := re.search(pt, t[:4000]))]
    return min(hits)[1] if hits else "other"


def parse_legacy(path, t):
    """Pre-2018 'Order Item' layout (e.g. B65461-00): one service block with numbered order items."""
    m = re.search(r"Service ID\s+(\d+).*?Service Commitment\s+(\d+)\s*Months", t, re.S)
    loc = re.search(r"Location ID:\s*([A-Z0-9]+)", t)
    act = re.search(r"Activity Type\s+([A-Z]+)", t)
    out = []
    for r in re.finditer(r"^\s+(\d+)\s{2,}(.*?)\s{2,}(%s)\s+(%s)\s*\n(.*?)\n" % (AMT, AMT), t, re.M):
        if "Location ID" in r[2]: continue
        out.append(dict(source_path=path, location_id=loc[1] if loc else "", location_city="", service_id=m[1] if m else "", service_name="",
                        item_description=(r[2] + " " + r[5]).strip(), activity_type=act[1] if act else "", quantity=None,
                        mrc=num(r[3]), nrc=num(r[4]), page=1, commitment_months=int(m[2]) if m else None))
    return out[:1]


def parse(path, text):
    pages = text.split("\f")
    lines = [(pi + 1, l.rstrip()) for pi, p in enumerate(pages) for l in p.split("\n")]
    items, commit_by_sid = [], {}
    loc = city = svcname = sid = commit = None
    hdr_unit = False
    hdr = None        # (mrc_end_col, nrc_end_col) of last MRC/NRC header line
    seg = []          # pending description lines (since last row)
    last = None       # last item (for trailing description)
    in_delivery = False
    app_heading = None
    last_text = ""

    def flush():
        nonlocal seg, last
        if seg and last is not None:
            last["item_description"] = (last["item_description"] + " " + " ".join(seg)).strip()
        seg = []

    for pg, l in lines:
        if not l.strip(): continue
        m = LOC.match(l)
        if m:
            flush(); loc, city = m["id"], re.sub(r"^-\s*", "", m["city"]).strip(); in_delivery = False; sid = None; continue
        if re.match(r"^\s*\d+\.\s+Service Delivered to", l):
            flush(); sid = None; in_delivery = False; continue
        m = re.match(r"^\s*\d+\.\s+(\S.*?)\s*$", l)
        if m and not ROW.match(l) and len(m[1]) < 70:
            app_heading = clean_name(m[1])
        m = SVC.match(l)
        if m:
            flush(); in_delivery = False
            sid = m["id"]
            nm = clean_name(m["name"]) if m["name"] else None
            if not nm or nm == "See Appendix": nm = clean_name(last_text) if sid == "See Appendix" else app_heading
            svcname = nm; commit = None
            if sid != "See Appendix": last = None
            continue
        m = re.match(r"^\s*Service Commitment:\s*(.*)$", l)
        if m:
            mm = re.search(r"(\d+)\s*Month", m[1], re.I)
            commit = int(mm[1]) if mm else None
            if commit and sid and sid.isdigit(): commit_by_sid[sid] = commit
            continue
        if re.match(r"^\s*Activity Type:", l): continue
        if re.match(r"^\s*Delivery Charges\s*$", l):
            flush(); in_delivery = True; sid = None; svcname = "Delivery Charges"; last = None; continue
        if END.search(l):
            flush(); last = None; seg = []
            if re.search(r"Subtotal", l, re.I) is None: pass
            continue
        hm = re.search(r"\bMRC\b.*\bNRC\b", l)
        if hm and not ROW.match(l): hdr = (re.search(r"\bMRC\b", l).end(), re.search(r"\bNRC\b", l).end()); hdr_unit = "Unit" in l; continue
        r = ROW.match(l)
        if r and hdr and hdr_unit and r["qty"] is None and r["mrc"] == "N/A" and abs(r.end("nrc") - hdr[0]) < abs(r.end("nrc") - hdr[1]):
            r = {"left": r["left"], "act": r["act"], "qty": "N/A", "mrc": r["nrc"], "nrc": "N/A"}  # N/A was the quantity
        if not r:
            r1 = ROW1.match(l)
            if r1 and r1["act"] in ACTS and hdr and not re.search(r"\d\s+(N/A|%s)\s*$" % AMT, r1["mid"] + "x") and "Per Hour" not in l:
                e = r1.end("mrc"); isn = abs(e - hdr[1]) < abs(e - hdr[0])
                r = {"left": r1["left"], "act": r1["act"], "qty": None, "mrc": "N/A" if isn else r1["mrc"], "nrc": r1["mrc"] if isn else "N/A"}
            elif r1 and r1["act"] in ACTS and "Per Hour" in l:
                r = {"left": r1["left"], "act": r1["act"], "qty": None, "mrc": "N/A", "nrc": "N/A"}
        if r and r["act"] in ACTS and (sid or in_delivery or True) and loc:
            left = r["left"].strip()
            if left: seg.append(left)
            # split seg: lines before the last item-start belong to previous item
            idx = max([i for i, s in enumerate(seg) if ITEM_START.match(s)] or [0]) if last is not None else 0
            if last is not None and idx > 0:
                last["item_description"] = (last["item_description"] + " " + " ".join(seg[:idx])).strip()
                seg = seg[idx:]
            it = dict(source_path=path, location_id=loc, location_city=city, service_id=sid if sid and sid.isdigit() else "",
                      service_name=svcname or "", item_description=" ".join(seg).strip(), activity_type=r["act"],
                      quantity=num(r["qty"]) if r["qty"] else None, mrc=num(r["mrc"]), nrc=num(r["nrc"]), page=pg)
            items.append(it); last = it; seg = []
            continue
        if not in_delivery and loc and sid and re.match(r"^\s*(Discount|Credit)", l):
            p = PLAIN.match(l)
            if p:
                it = dict(source_path=path, location_id=loc, location_city=city, service_id=sid if sid.isdigit() else "",
                          service_name=svcname or "", item_description=p["left"].strip(), activity_type="DISCOUNT", quantity=None,
                          mrc=num(p["mrc"]), nrc=num(p["nrc"]), page=pg)
                items.append(it); last = it; seg = []; continue
        if in_delivery:
            p = PLAIN.match(l)
            if p and loc:
                it = dict(source_path=path, location_id=loc, location_city=city, service_id="", service_name="Delivery Charges",
                          item_description=p["left"].strip(), activity_type="", quantity=None, mrc=num(p["mrc"]), nrc=num(p["nrc"]), page=pg)
                items.append(it); last = it; seg = []
            continue
        if NOISE.search(l): continue
        if sid is not None or last is not None:
            seg.append(l.strip())
        last_text = l.strip()
    flush()
    for it in items:
        it["commitment_months"] = commit_by_sid.get(it["service_id"])
    return items


def summary_totals(text):
    """Sum the 'Total excluding ...' line that closes each Order Summary by Location block."""
    mrc = nrc = 0.0; n = 0; cur = None
    for blk in re.split(r"Order Summary by Location", text)[1:]:
        L = blk.split("Service Order Details")[0].split("\n")
        for i, l in enumerate(L):
            if re.search(r"Total.*excluding", l):
                m = re.search(r"\b([A-Z]{3})\s+(%s)\s+(%s)\s*$" % (AMT, AMT), l + "\n" + (L[i + 1] if i + 1 < len(L) else ""), re.M) \
                    or re.search(r"\b([A-Z]{3})\s+(%s)\s+(%s)\s*$" % (AMT, AMT), (L[i + 1] if i + 1 < len(L) else ""))
                if m:
                    mrc += num(m[2]) or 0; nrc += num(m[3]) or 0; n += 1; cur = cur or m[1]; break
    return (mrc, nrc, cur) if n else (None, None, None)


def main():
    docs = json.load(open(ROOT / "analysis/batches/vz_contracts_text.json"))
    rows, drows = [], []
    for d in docs:
        p = d["path"]
        t = subprocess.run(["pdftotext", "-layout", str(ROOT / p), "-"], capture_output=True, text=True).stdout
        ref = re.search(r"(?:Amendment ID|CCR Package ID):\s*([A-Z]\d{5}-\d\d)", t)
        cid = re.search(r"Contract ID:\s*(\S+)", t)
        ref, cid = (ref[1] if ref else Path(p).stem), (cid[1] if cid else "")
        kind = doc_kind(t)
        global CD
        CD = len(re.findall(r",\d{2}\s*$", t, re.M)) >= 3 and len(re.findall(r"\d\.\d{2}\s*$", t, re.M)) < 3
        smrc, snrc, cur = summary_totals(t)
        items = parse(p, t) if smrc is not None or kind in ("sof", "amendment") else []
        if cur is None:
            cm = re.search(r"Total \((\w{3})\) excluding", t) or re.search(r"MRC\s+NRC\s*\n\s*(?:No\.?\s+Order Item\s+)?\((\w{3})\)", t) or re.search(r"Total excluding[^\n]*?\b(USD|EUR|GBP|BRL|CNY|INR|CHF)\b", t)
            cur = cm[1] if cm else ""
        if not items and re.search(r"Service Ordered:", t):
            items = parse_legacy(p, t)
            for it in items: it["service_name"] = "Secure Cloud Interconnect" if "Secure Cloud Interconnect" in t else ""
            if items: smrc, snrc = sum(i["mrc"] or 0 for i in items), sum(i["nrc"] or 0 for i in items)  # legacy 'Total excluding' mirrors item
        for it in items:
            it.update(contract_ref=ref, contract_id=cid, doc_kind=kind, currency=cur)
        rows += items
        sm = round(sum(i["mrc"] or 0 for i in items), 2); sn = round(sum(i["nrc"] or 0 for i in items), 2)
        if kind == "cancellation": status, note = "no_pricing", "cancellation notice"
        elif not items and len(t.strip()) < 150 * d["pages"]: status, note = "failed", "no usable text layer (scanned/image PDF); needs OCR"
        elif not items and re.search(r"Customer Specific Pricing|Standard Charges", t): status, note = "no_pricing", "terms/rate-card amendment, no order price table"
        elif not items and smrc is None: status, note = "no_pricing", "no order price table (terms-only amendment/add-change form)"
        elif not items: status, note = "failed", "summary present but no item rows parsed"
        elif smrc is None: status, note = "parsed_no_summary", "no Order Summary totals to reconcile"
        else: status, note = "ok", ""
        rec = ""
        if smrc is not None and items:
            rec = abs(sm - smrc) <= 0.01 and abs(sn - snrc) <= 0.01
            if not rec: note = f"diff mrc {sm - smrc:+.2f} nrc {sn - snrc:+.2f}"
        drows.append(dict(source_path=p, contract_ref=ref, contract_id=cid, doc_kind=kind,
                          n_locations=len({i["location_id"] for i in items}), n_services=len({(i["location_id"], i["service_id"], i["service_name"]) for i in items}),
                          summary_mrc_total=smrc if smrc is None else round(smrc, 2), summary_nrc_total=snrc if snrc is None else round(snrc, 2),
                          sum_item_mrc=sm, sum_item_nrc=sn, reconciles=rec, parse_status=status, notes=note))
    cols = "source_path contract_ref contract_id doc_kind location_id location_city service_id service_name item_description activity_type quantity mrc nrc currency commitment_months page".split()
    with open(WORK / "contract_prices.csv", "w", newline="") as f:
        w = csv.DictWriter(f, cols); w.writeheader(); w.writerows(rows)
    dcols = list(drows[0])
    with open(WORK / "contract_docs.csv", "w", newline="") as f:
        w = csv.DictWriter(f, dcols); w.writeheader(); w.writerows(drows)
    print(len(docs), "docs", len(rows), "rows")


if __name__ == "__main__":
    main()
