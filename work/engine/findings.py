"""Merge the SOF ledger and the Amendment-28 rate-card check into one verdict per service-month, tiered by confidence.

Tiers reflect two audits (work/engine_out/audit_notes.md, audit2_notes.md):
  A_RECOVERABLE   rate-card HIGH overbilling from Mar-2024 (audit 2: 8/10 confirmed), not offset by credits
  B_RAISE         plausible billing errors needing Verizon/EZ confirmation (lower measured precision)
  C_COMMERCIAL    early-termination liabilities: negotiation items, not billing errors
  D_UNDERBILLED   in Verizon's favour; no claim, but explains variance
  E_UNVERIFIABLE  spend we cannot price yet (missing contracts / no rate)
Run from TEM: python3 -I work/engine/findings.py
"""
import csv, os, collections

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'engine_out')
AMEND28_FIRST_FULL_MONTH = '2024-03'   # Feb-2024 was credited (audit 2); repricing claim starts Mar-2024

B_RAISE = {'NRC_OVERBILLED', 'OVERBILLED', 'OVERBILLED_FALLBACK', 'BILLED_AFTER_REMOVAL', 'ESCALATOR_REVIEW', 'REMOVAL_REVIEW'}
D_UNDER = {'UNDERBILLED', 'UNDERBILLED_FALLBACK', 'PRICE_BASIS_UNCERTAIN'}
OK = {'OK', 'NRC_OK', 'NRC_INSTALMENTS_REMAINING', 'NRC_PASSTHROUGH', 'USAGE_BASED', 'REFUNDED', 'INCOMPLETE_MONTH'}


def f(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def tier(ledger_cat, rc):
    if rc and rc['category'] == 'RC_OVERBILLED':
        if rc['confidence'] == 'HIGH' and rc['month'] >= AMEND28_FIRST_FULL_MONTH:
            return 'A_RECOVERABLE', 'RC_OVERBILLED'
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
    rc = {(x['service_id'], x['month']): x for x in csv.DictReader(open(os.path.join(OUT, 'rate_card_checks.csv')))}
    out = []
    for r in led:
        hit = rc.get((r['service_id'], r['month'])) if r['kind'] == 'REC' else None
        t, cat = tier(r['category'], hit)
        disc_usd = f(r['discrepancy_usd'])
        expected = r['expected']
        if hit and cat.startswith('RC_'):
            fx = f(r['fx_to_usd']) or 1.0
            disc_usd = round(f(hit['discrepancy']) * fx, 2)
            expected = hit['expected']
            if cat.startswith('RC_OVERBILLED') and f(r.get('credits')) < 0:
                disc_usd = max(0.0, round(disc_usd + f(r['credits']) * fx, 2))   # net any credit for that service-month
        out.append(dict(r, tier=t, final_category=cat, final_expected=expected,
                        claim_usd=disc_usd if t in ('A_RECOVERABLE', 'B_RAISE') and disc_usd > 0 else 0.0,
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
    print({k: (round(g), round(nb)) for k, (g, nb) in sorted(tot.items())}, '(gross, net)')


if __name__ == '__main__':
    assert tier('OK', dict(category='RC_OVERBILLED', confidence='HIGH', month='2024-02'))[0] == 'B_RAISE'
    assert tier('OK', dict(category='RC_OVERBILLED', confidence='HIGH', month='2024-05'))[0] == 'A_RECOVERABLE'
    assert tier('MASTER_RATE_CARD+DRIFT', None)[0] == 'E_UNVERIFIABLE'
    assert tier('EARLY_TERMINATION', None)[0] == 'C_COMMERCIAL'
    main()
