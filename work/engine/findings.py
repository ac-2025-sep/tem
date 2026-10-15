"""Merge the SOF ledger and the Amendment-28 rate-card check into one verdict per service-month, tiered by confidence.

Tiers reflect two audits (work/engine_out/audit_notes.md, audit2_notes.md):
  A_RECOVERABLE   rate-card HIGH overbilling from Mar-2024 (audit 2: 8/10 confirmed), not offset by credits
  B_RAISE         plausible billing errors needing Verizon/EZ confirmation (lower measured precision)
                  claim_status splits the claim (tierB_review.csv, row-by-row review): VERIFIED = executed SOF, no credit,
                  no pass-through/fee explanation; NEEDS_DOC = a named document decides it; blank = no claim.
                  Review-only categories (claim 0): FEE_REVIEW (pending order change, cancellation, change fee, TSP),
                  ESCALATOR_REVIEW (contract footnote increase), NRC_PASSTHROUGH_MISMATCH (CPE/landed NRC above the SOF
                  location-level Landed Costs), REMOVAL_REVIEW. CITED_REVISION_NOT_PROVIDED / NRC_NO_PRICE stay in E.
  C_COMMERCIAL    early-termination liabilities: negotiation items, not billing errors
  D_UNDERBILLED   in Verizon's favour; no claim, but explains variance
  E_UNVERIFIABLE  spend we cannot price yet (missing contracts / no rate)
Run from TEM: python3 -I work/engine/findings.py
"""
import csv, os, collections

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'engine_out')
AMEND28_FIRST_FULL_MONTH = '2024-03'   # Feb-2024 was credited (audit 2); repricing claim starts Mar-2024

B_RAISE = {'NRC_OVERBILLED', 'OVERBILLED', 'OVERBILLED_FALLBACK', 'BILLED_AFTER_REMOVAL', 'ESCALATOR_REVIEW', 'REMOVAL_REVIEW',
           'FEE_REVIEW', 'NRC_PASSTHROUGH_MISMATCH'}
NO_CLAIM = {'FEE_REVIEW', 'ESCALATOR_REVIEW', 'NRC_PASSTHROUGH_MISMATCH', 'REMOVAL_REVIEW'}   # questions, never dollars
D_UNDER = {'UNDERBILLED', 'UNDERBILLED_FALLBACK', 'PRICE_BASIS_UNCERTAIN'}
OK = {'OK', 'NRC_OK', 'NRC_INSTALMENTS_REMAINING', 'NRC_PASSTHROUGH', 'USAGE_BASED', 'REFUNDED', 'INCOMPLETE_MONTH'}


def f(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def tier(ledger_cat, rc, credits=0.0):
    if rc and rc['category'] == 'RC_OVERBILLED':
        if rc['confidence'] == 'HIGH' and rc['month'] >= AMEND28_FIRST_FULL_MONTH:
            return 'A_RECOVERABLE', 'RC_OVERBILLED'
        if rc['confidence'] == 'HIGH' and credits < 0:
            return 'OK', 'RC_REFUNDED'                # Feb-2024: "One Time Credit - PIP Port" already netted it (audit 2)
        return 'B_RAISE', 'RC_OVERBILLED_' + (rc['confidence'] or 'LOW')
    if rc and rc['category'] == 'RC_OK' and rc['confidence'] in ('HIGH', 'MED'):
        return 'OK', 'RC_OK'
    base = ledger_cat.replace('+DRIFT', '')
    if base == 'EARLY_TERMINATION':
        return 'C_COMMERCIAL', ledger_cat
    if base in B_RAISE:
        return 'B_RAISE', ledger_cat
    if base in D_UNDER:
        return 'D_UNDERBILLED', ledger_cat
    if base in OK:
        return 'OK', ledger_cat
    return 'E_UNVERIFIABLE', ledger_cat


def main():
    led = list(csv.DictReader(open(os.path.join(OUT, 'service_month_ledger.csv'))))
    review = {(x['service_id'], x['month']): x['verdict'] for x in csv.DictReader(open(os.path.join(OUT, 'tierB_review.csv')))}
    rc = {(x['service_id'], x['month']): x for x in csv.DictReader(open(os.path.join(OUT, 'rate_card_checks.csv')))}
    us = os.path.join(OUT, 'us_stmt_rate_card_checks.csv')   # US statements: circuit -> country/speed from raw text
    if os.path.exists(us):
        for x in csv.DictReader(open(us)):
            k = (x['service_id'], x['month'])
            if x['category'] != 'RC_NO_RATE' and (k not in rc or rc[k]['category'] == 'RC_NO_RATE'):
                rc[k] = x
    out = []
    for r in led:
        hit = rc.get((r['service_id'], r['month'])) if r['kind'] == 'REC' else None
        t, cat = tier(r['category'], hit, f(r.get('credits')))
        disc_usd = f(r['discrepancy_usd'])
        expected = r['expected']
        if hit and cat.startswith('RC_'):
            fx = f(r['fx_to_usd']) or 1.0
            disc_usd = round(f(hit['discrepancy']) * fx, 2)
            expected = hit['expected']
            if cat.startswith('RC_OVERBILLED') and f(r.get('credits')) < 0:
                disc_usd = max(0.0, round(disc_usd + f(r['credits']) * fx, 2))   # net any credit for that service-month
        claim = disc_usd if t in ('A_RECOVERABLE', 'B_RAISE') and disc_usd > 0 and cat not in NO_CLAIM else 0.0
        v = review.get((r['service_id'], r['month'] if r['kind'] == 'REC' else ''))
        status = ('VERIFIED' if v == 'TP' else 'NEEDS_DOC' if v == 'NEEDS_DOC' else '') if t == 'B_RAISE' and claim > 0 else ''
        out.append(dict(r, tier=t, final_category=cat, final_expected=expected, claim_usd=claim, claim_status=status,
                        evidence=(hit or {}).get('basis', '') or f"priced by {r['priced_by'] or '-'}; invoices {r['invoices']}"))
    with open(os.path.join(OUT, 'findings.csv'), 'w', newline='') as fh:
        w = csv.DictWriter(fh, list(out[0])); w.writeheader(); w.writerows(out)

    s = collections.defaultdict(lambda: [0, 0.0, 0.0, 0.0])
    for r in out:
        x = s[(r['tier'], r['final_category'])]; x[0] += 1; x[1] += f(r['billed_usd']); x[2] += f(r['billed_net_usd']); x[3] += r['claim_usd']
    print(f"{'tier':16}{'category':34}{'rows':>7}{'billed $':>13}{'net $':>13}{'claim $':>11}")
    for (t, c), (n, b, nb, cl) in sorted(s.items(), key=lambda kv: (kv[0][0], -kv[1][1])):
        print(f'{t:16}{c:34}{n:7}{b:13,.0f}{nb:13,.0f}{cl:11,.0f}')
    tot = collections.defaultdict(lambda: [0.0, 0.0])
    for r in out:
        tot[r['tier']][0] += f(r['billed_usd']); tot[r['tier']][1] += f(r['billed_net_usd'])
    cs = collections.defaultdict(lambda: [0, 0.0])
    for r in out:
        if r['tier'] == 'B_RAISE' and r['claim_usd'] > 0:
            cs[r['claim_status'] or '(blank: not in review)'][0] += 1; cs[r['claim_status'] or '(blank: not in review)'][1] += r['claim_usd']
    print('tier B claim by claim_status:', {k: (n, round(c, 2)) for k, (n, c) in sorted(cs.items())}, 'total', round(sum(c for _, c in cs.values()), 2))
    print({k: (round(g), round(nb)) for k, (g, nb) in sorted(tot.items())}, '(gross, net)')


if __name__ == '__main__':
    assert tier('OK', dict(category='RC_OVERBILLED', confidence='HIGH', month='2024-02'))[0] == 'B_RAISE'
    assert tier('OK', dict(category='RC_OVERBILLED', confidence='HIGH', month='2024-05'))[0] == 'A_RECOVERABLE'
    assert tier('MASTER_RATE_CARD+DRIFT', None)[0] == 'E_UNVERIFIABLE'
    assert tier('EARLY_TERMINATION', None)[0] == 'C_COMMERCIAL'
    main()
