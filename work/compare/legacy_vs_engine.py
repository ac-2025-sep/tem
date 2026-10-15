"""Head-to-head: legacy Presence360 vs our engine, on the same Verizon invoices.

Inputs: legacy/api-snapshot.json (invoice headers), work/legacy_capture/legacy_lines.csv (legacy line verdicts),
work/invoice_lines*.csv (our parse), work/engine_out/findings.csv (our verdicts, one row per service-month).
Writes work/compare/out/*.csv and prints a JSON summary.  Run from TEM root: python3 -I work/compare/legacy_vs_engine.py
"""
import csv, json, os, re, collections
from datetime import datetime

W = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
OUT = os.path.join(W, 'compare', 'out')
TOL = 1.00


def f(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def norm(i):
    return (i or '').strip().lstrip('0').upper()


def month_of(period):
    m = re.match(r'(\d\d[A-Za-z]{3}\d\d)', period or '')
    return datetime.strptime(m[1], '%d%b%y').strftime('%Y-%m') if m else None


def main():
    os.makedirs(OUT, exist_ok=True)
    S = {}
    snap = json.load(open(os.path.join(W, '..', 'legacy', 'api-snapshot.json')))
    body = snap['invoices_verizon']['body']
    leg_inv = {norm(i['invoice_id']): i for i in body['data'] if i.get('invoice_id')}
    S['legacy_header'] = dict(invoices=len(body['data']), total_discrepancy=body['total_discrepancy'], total_adj=body['total_adj'],
                              total_usd=round(sum(f(i['total_usd']) for i in body['data'])),
                              disc_gt_invoice=sum(1 for i in body['data'] if f(i['total_discrepancy']) > f(i['total_usd']) + 1),
                              zero_line_invoices=sum(1 for i in body['data'] if not i.get('line_item_count')))

    # ---- 1. invoice coverage
    ours = {}
    for fn in ('invoice_lines.csv', 'invoice_lines_other.csv'):
        for x in csv.DictReader(open(os.path.join(W, fn))):
            if x['doc_kind'] == 'invoice':
                ours.setdefault(norm(x['invoice_no']), x['template'])
    both, lo, oo = set(leg_inv) & set(ours), set(leg_inv) - set(ours), set(ours) - set(leg_inv)
    S['coverage'] = dict(ours=len(ours), legacy=len(leg_inv), both=len(both), legacy_only=len(lo), ours_only=len(oo),
                         ours_only_by_template=dict(collections.Counter(ours[k] for k in oo)),
                         legacy_only_zero_lines=sum(1 for k in lo if not leg_inv[k].get('line_item_count')),
                         legacy_only_usd=round(sum(f(leg_inv[k]['total_usd']) for k in lo)))

    # ---- 2. legacy line verdicts -> service-month
    L = list(csv.DictReader(open(os.path.join(W, 'legacy_capture', 'legacy_lines.csv'))))
    usd = lambda x, k: f(x[k]) * (f(x['conversion_rate']) or 1.0)
    S['legacy_lines'] = dict(lines=len(L), billed_usd=round(sum(usd(x, 'amount') for x in L)),
                             by_status={k: dict(lines=v, disc_usd=round(sum(usd(x, 'discrepancy') for x in L if x['sof_status'] == k)))
                                        for k, v in collections.Counter(x['sof_status'] for x in L).items()},
                             net_disc_usd=round(sum(usd(x, 'discrepancy') for x in L)),
                             abs_disc_usd=round(sum(abs(usd(x, 'discrepancy')) for x in L)))
    lsm = collections.defaultdict(lambda: dict(billed=0.0, disc=0.0, lines=0, missing=0, matched=0, flagged=0, src=set()))
    for x in L:
        if x['charge_type'] not in ('REC', 'CE'):
            continue
        m = month_of(x['charge_period'])
        if not m:
            continue
        e = lsm[(x['service_id'], m)]
        e['billed'] += usd(x, 'amount'); e['disc'] += usd(x, 'discrepancy'); e['lines'] += 1
        if x['sof_status'] == 'Missing':
            e['missing'] += 1
        else:
            e['matched'] += 1; e['src'].add(x['matched_source'])
            if abs(f(x['discrepancy'])) > TOL:
                e['flagged'] += 1

    def legacy_verdict(e):
        if e['matched'] == 0:
            return 'L_UNMATCHED'            # whole amount counted as discrepancy
        if e['flagged'] == 0:
            return 'L_OK'
        return 'L_OVER' if e['disc'] > TOL else 'L_UNDER' if e['disc'] < -TOL else 'L_FLAG_NETS_ZERO'

    # ---- 3. join to our findings (REC rows)
    F = {(x['service_id'], x['month']): x for x in csv.DictReader(open(os.path.join(W, 'engine_out', 'findings.csv'))) if x['kind'] == 'REC'}

    def engine_verdict(r):
        t = r['tier']
        if t == 'A_RECOVERABLE':
            return 'E_A_CLAIM'
        if t == 'B_RAISE':
            return 'E_B_CLAIM' if f(r['claim_usd']) > 0 else 'E_B_REVIEW'
        if t == 'C_COMMERCIAL':
            return 'E_C_COMMERCIAL'
        if t == 'D_UNDERBILLED':
            return 'E_D_UNDER'
        if t == 'OK':
            return 'E_OK'
        return 'E_UNVERIFIABLE'

    rows, cm, cm_usd = [], collections.Counter(), collections.defaultdict(float)
    for k, e in lsm.items():
        r = F.get(k)
        lv, ev = legacy_verdict(e), (engine_verdict(r) if r else 'E_NOT_IN_LEDGER')
        cm[(lv, ev)] += 1; cm_usd[(lv, ev)] += e['billed']
        rows.append(dict(service_id=k[0], month=k[1], legacy_verdict=lv, legacy_disc_usd=round(e['disc'], 2),
                         legacy_billed_usd=round(e['billed'], 2), legacy_source='/'.join(sorted(e['src'])),
                         engine_verdict=ev, engine_category=(r or {}).get('final_category', ''),
                         engine_expected=(r or {}).get('final_expected', ''), engine_claim_usd=(r or {}).get('claim_usd', ''),
                         engine_billed_net_usd=(r or {}).get('billed_net_usd', '')))
    with open(os.path.join(OUT, 'service_month_join.csv'), 'w', newline='') as fh:
        w = csv.DictWriter(fh, list(rows[0])); w.writeheader(); w.writerows(rows)
    S['confusion'] = {f'{a}|{b}': dict(n=n, billed_usd=round(cm_usd[(a, b)])) for (a, b), n in sorted(cm.items())}

    # ---- 4. recall: what did legacy say about each of our claims?
    claims = [r for r in F.values() if r['tier'] in ('A_RECOVERABLE', 'B_RAISE') and f(r['claim_usd']) > 0]
    rec = collections.Counter(); rec_usd = collections.defaultdict(float); amt_err = []
    for r in claims:
        e = lsm.get((r['service_id'], r['month']))
        lv = legacy_verdict(e) if e else 'L_NOT_CAPTURED'
        rec[lv] += 1; rec_usd[lv] += f(r['claim_usd'])
        if lv == 'L_OVER':
            amt_err.append(e['disc'] - f(r['claim_usd']))
    S['recall_on_our_claims'] = dict(rows=len(claims), claim_usd=round(sum(f(r['claim_usd']) for r in claims), 2),
                                     by_legacy_verdict={k: dict(n=v, claim_usd=round(rec_usd[k], 2)) for k, v in rec.items()},
                                     legacy_over_amount_vs_ours_median=sorted(amt_err)[len(amt_err) // 2] if amt_err else None)

    # ---- 5. precision of legacy's own matched flags (service-month level)
    flagged = [r for r in rows if r['legacy_verdict'] in ('L_OVER', 'L_UNDER', 'L_FLAG_NETS_ZERO')]
    pc = collections.Counter(r['engine_verdict'] for r in flagged)
    S['legacy_flag_precision'] = dict(flagged_service_months=len(flagged), engine_says=dict(pc),
                                      over_flags=sum(r['legacy_verdict'] == 'L_OVER' for r in flagged),
                                      over_flags_confirmed=sum(r['legacy_verdict'] == 'L_OVER' and r['engine_verdict'] in ('E_A_CLAIM', 'E_B_CLAIM') for r in flagged))

    # ---- 6. our tiers, net USD (all kinds)
    tiers = collections.defaultdict(lambda: [0, 0.0, 0.0])
    for r in csv.DictReader(open(os.path.join(W, 'engine_out', 'findings.csv'))):
        t = tiers[r['tier']]; t[0] += 1; t[1] += f(r['billed_net_usd']); t[2] += f(r['claim_usd'])
    S['engine_tiers'] = {k: dict(rows=v[0], net_usd=round(v[1]), claim_usd=round(v[2], 2)) for k, v in sorted(tiers.items())}
    json.dump(S, open(os.path.join(OUT, 'summary.json'), 'w'), indent=1, default=str)
    print(json.dumps(S, indent=1, default=str))


if __name__ == '__main__':
    main()
