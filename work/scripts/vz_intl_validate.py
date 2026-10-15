"""Validate invoice_lines.csv: header-total reconcile -> work/invoice_reconcile.csv ; CSV line match -> work/csv_match_detail.csv
Run: python3 -I work/scripts/vz_intl_validate.py"""
import csv, re, sys, collections
sys.path[:0] = ["/media/abhay/Workspace/Egon Zehnder/TEM/analysis/scripts", "/media/abhay/Workspace/Egon Zehnder/TEM/work/scripts"]
import vz_load
from vz_intl_lines import ROOT, text, SCOPE
W = f"{ROOT}/work"
lines = list(csv.DictReader(open(f"{W}/invoice_lines.csv")))
idx = [r for r in csv.DictReader(open(f"{ROOT}/analysis/billing_index.csv")) if r["template"] in SCOPE]
by = collections.defaultdict(list)
for l in lines: by[l["source_path"]].append(l)


def lastnum(label, t):
    m = re.search(label + r"[^\n\d$-]*([^\n]*)", t)
    if not m: return None
    ns = re.findall(r"-?\s?\$?-?[\d'.,]*\d", m.group(1))
    if not ns: return None
    s = ns[-1]; neg = "-" in s
    s = re.sub(r"[^\d.,]", "", s.replace("'", ""))
    if re.search(r",\d{2}$", s) and "." in s and s.rfind(".") < s.rfind(","): s = s.replace(".", "").replace(",", ".")
    elif re.search(r",\d{2}$", s) and "." not in s: s = s.replace(",", ".")
    else: s = s.replace(",", "")
    v = float(s); return -v if neg else v


out = []
for r in idx:
    t = text(r["hash"], r["path"]); p1 = t.split("\f")[0]
    ls = by.get(r["path"], [])
    hdr = lastnum(r"(?:Total Current Charges|Totale addebiti correnti)", p1)  # own parse: index total_amount mis-reads comma-decimal bills
    hnet = lastnum(r"(?:Net Charges|Addebiti netti)", p1)
    htax = lastnum(r"(?:Taxes/VAT|Imposte/IVA|Taxes and Surcharges)", p1)
    sign = -1 if r["doc_kind"] == "credit_note" else 1
    stot = round(sum(float(l["line_total"]) for l in ls), 2)
    snet = round(sum(float(l["net_amount"]) for l in ls), 2)
    stax = round(sum(float(l["tax"]) for l in ls), 2)
    diff = None if hdr is None else round(stot - sign * hdr, 2)
    tol = 0.05 + (0.5 * len(ls) if r["currency"] in ("INR", "JPY", "KRW") else 0) + (0.01 * len(ls))
    tol = 0.05 + 0.011 * len(ls)  # per-line cent rounding
    if r["account_number"].startswith(("IN", "JP")) and r["currency"] != "USD": tol += 0.5 * len(ls)
    status = "NOHDR" if hdr is None else ("OK" if abs(diff) <= tol else ("ZERO_LINES" if not ls else "DIFF"))
    out.append(dict(source_path=r["path"], template=r["template"], doc_kind=r["doc_kind"], invoice_no=r["doc_number"], currency=r["currency"],
                    n_lines=len(ls), header_total=hdr, header_net=hnet, header_tax=htax, sum_line_total=stot, sum_net=snet, sum_tax=stax,
                    diff_total=diff, tol=round(tol, 2), diff_net=None if hnet is None else round(snet - sign * hnet, 2),
                    diff_tax=None if htax is None else round(stax - sign * htax, 2), status=status))
with open(f"{W}/invoice_reconcile.csv", "w", newline="") as f:
    w = csv.DictWriter(f, list(out[0])); w.writeheader(); w.writerows(out)
c = collections.Counter((o["template"], o["status"]) for o in out)
for k in sorted(c): print(k, c[k])
print("reconcile OK", sum(o["status"] == "OK" for o in out), "/", len(out))

# ---- CSV comparison
def mny(s): return float(s)
csvrows = {}
for k, (h, rows) in vz_load.load().items():
    if "(1)" in k: continue
    for r in rows:
        if len(r) != 29: continue
        csvrows.setdefault(r[3], {})
        csvrows[r[3]].setdefault(k, []).append(r)
# dedupe quarterly overlap: keep first period key per invoice
crow = {}
for inv, d in csvrows.items():
    k = sorted(d, key=lambda x: (len(x), x))[0] if False else None
    best = min(d, key=lambda x: x.startswith("2025-04-01THRU2025-06-30"))  # prefer monthly file over quarterly
    crow[inv] = d[best]
def ctype(r):
    p = r[11]
    rec, nrc, usg = mny(r[23]), mny(r[24]), mny(r[22])
    if p.startswith("One Time Credit"): return "CREDIT"
    if usg: return "USAGE"
    if nrc and not rec: return "NRC"
    return "REC"
def ptype(l): return l["charge_type"]
agg = collections.Counter(); det = []; svcfail = []
seen = set()
for r in idx:
    inv = r["doc_number"]
    if inv not in crow or inv in seen: continue
    seen.add(inv)
    ls = by.get(r["path"], [])
    cs = crow[inv]
    tol = 1.0 if cs[0][28] == "INR" else 0.011
    key_c = collections.defaultdict(list)
    for x in cs:
        sid = x[8] if x[8] not in ("-", "") else ""
        key_c[sid].append(x)
    pool = {k: [(abs(mny(x[27])), ctype(x), x) for x in v] for k, v in key_c.items()}
    n = ms = mt = 0
    for l in ls:
        n += 1
        sid = l["service_id"] or ""
        tot = abs(float(l["line_total"]))
        cand = pool.get(sid, [])
        hit = None
        for i, (ct, cty, x) in enumerate(cand):
            if abs(ct - tot) <= tol: hit = i; break
        status = "nomatch"
        if hit is not None:
            ct, cty, x = cand.pop(hit); ms += 1; status = "match"
            if cty == ptype(l) or (cty == "REC" and ptype(l) in ("ADJ", "OTHER")) or (cty == "CREDIT" and ptype(l) in ("ADJ", "CREDIT")): mt += 1
            else: status = "match_type_diff"
        det.append(dict(invoice_no=inv, template=r["template"], service_id=sid, charge_type=l["charge_type"], line_total=l["line_total"], desc=l["description"][:60], status=status))
    # group level: (service_id, charge type) sums, PDF vs CSV (PDF rows aggregate several CSV product rows)
    gp = collections.defaultdict(lambda: [0.0, 0]); gc = collections.defaultdict(float)
    for l in ls:
        k = (l["service_id"] or "", "CREDIT" if l["charge_type"] in ("ADJ", "CREDIT") else "NRC" if l["charge_type"] == "NRC" else "REC")
        gp[k][0] += float(l["line_total"]); gp[k][1] += 1
    for x in cs:
        ty = ctype(x); k = (x[8] if x[8] not in ("-", "") else "", "CREDIT" if ty == "CREDIT" else "NRC" if ty == "NRC" else "REC")
        gc[k] += mny(x[27])
    # type-agnostic fallback: sum per service
    sp = collections.defaultdict(float); sc = collections.defaultdict(float)
    for k, (v, c_) in gp.items(): sp[k[0]] += v
    for k, v in gc.items(): sc[k[0]] += v
    for k, (v, c_) in gp.items():
        if abs(sc.get(k[0], 1e9) - sp[k[0]]) <= tol * max(c_, 1) * 4 + 0.011 * 4: agg["grp_lines"] += c_
    for k, v in sp.items():
        if not abs(sc.get(k, 1e9) - v) <= tol * 4 + 0.05: svcfail.append((inv, r["template"], k or "(none)", round(v, 2), round(sc[k], 2) if k in sc else None))
    for k, v in sc.items():
        if k not in sp: svcfail.append((inv, r["template"], k or "(none)", None, round(v, 2)))
    agg["svc_groups"] += len(sp); agg["svc_groups_ok"] += sum(abs(sc.get(k, 1e9) - v) <= tol * 4 + 0.05 for k, v in sp.items())
    agg["csv_svc_groups"] += len(sc); agg["csv_svc_groups_in_pdf"] += sum(k in sp for k in sc)
    nleft = sum(len(v) for v in pool.values())
    agg["inv"] += 1; agg["lines"] += n; agg["svc_amt"] += ms; agg["svc_amt_type"] += mt; agg["csv_rows"] += len(cs); agg["csv_unmatched"] += nleft
    agg[r["template"] + "_lines"] += n; agg[r["template"] + "_match"] += ms; agg[r["template"] + "_csv"] += len(cs); agg[r["template"] + "_csvleft"] += nleft
with open(f"{W}/csv_match_detail.csv", "w", newline="") as f:
    w = csv.DictWriter(f, list(det[0])); w.writeheader(); w.writerows(det)
for k, v in sorted(agg.items()): print(k, v)
print("service-level (invoice,service_id) sum agreement: lines %.1f%%, groups %.1f%%, csv service groups present in pdf %.1f%%" % (100*agg["grp_lines"]/agg["lines"], 100*agg["svc_groups_ok"]/agg["svc_groups"], 100*agg["csv_svc_groups_in_pdf"]/agg["csv_svc_groups"]))
print("line match (invoice,service_id,amount): %.1f%%; with charge type: %.1f%%; CSV rows covered: %.1f%%" % (
    100 * agg["svc_amt"] / agg["lines"], 100 * agg["svc_amt_type"] / agg["lines"], 100 * (agg["csv_rows"] - agg["csv_unmatched"]) / agg["csv_rows"]))

with open(f"{W}/csv_service_mismatch.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["invoice_no", "template", "service_id", "pdf_sum", "csv_sum"]); w.writerows(svcfail)
print(len(svcfail), "service-level mismatches")
