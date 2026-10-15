"""Discrepancy engine v1: Verizon charges vs contracted price, on a service x month ledger.

Rules (each verified on real invoices, see work/engine/RULES.md):
- Contract MRC == gross recurring charge for that service for a full month. Discounts/credits/tax are separate lines.
- Recurring charges are compared per service-month, not per invoice: US accounts bill in advance while add-ons
  bill in arrears, some accounts bill bi-monthly, and 'CE' catch-up lines back-bill earlier months.
  Every REC/CE line is spread over the days it covers; each service-month total is compared to MRC x coverage.
- NRCs are billed in instalments, so they are compared cumulatively per service.
- The contract named on the invoice line wins; otherwise the latest *signed* revision that prices that service ID,
  never one older than the cited revision (CITED_REVISION_NOT_PROVIDED when the cited revision is missing or lacks the service).
- CPE landed-cost / pass-through NRCs are summed per (contract, location) and compared with the SOF's service-less
  location-level 'Landed Costs' row: NRC_PASSTHROUGH (<= SOF) or NRC_PASSTHROUGH_MISMATCH (> SOF, review only).
- Non-SOF fees (pending order change, cancellation, change fee, TSP) are never priced as install NRC/MRC: FEE_REVIEW,
  a question for Verizon with no claim. They are kept out of the service-month ledger so they cannot inflate OVERBILLED.
- NRC_NO_PRICE: the only SOF rows for the service are REMOVED zeros, so 0 is not a price.
- ESCALATOR_REVIEW also when the overbilling equals k lines x the SOF footnote escalator ('increase every N year(s) of X percent').
Run from the TEM folder: python3 -I work/engine/discrepancy.py
"""
import csv, json, glob, os, re, calendar, collections
from datetime import date, timedelta

W = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
OUT = os.path.join(W, 'engine_out')
TOL_ABS, TOL_PCT = 1.00, 0.01   # ponytail: flat tolerance; make per-currency if EZ disagrees
MASTER_CONTRACT = '208686'      # Verizon Business Service Agreement ID, cited on rate-card-priced services


def num(v):
    """'1,234.56' / '86,91' (decimal comma) / "2'948.04" / 'N/A' -> float|None"""
    if v in (None, '', 'N/A', 'Included'):
        return None
    t = str(v).strip().replace("'", '').replace(' ', '')
    if re.fullmatch(r'-?\d{1,3}(\.\d{3})*,\d{1,2}', t):   # European: 1.234,56 or 86,91
        t = t.replace('.', '').replace(',', '.')
    try:
        return float(t.replace(',', ''))
    except ValueError:
        return None


def d(s):
    try:
        return date.fromisoformat(s[:10])
    except (TypeError, ValueError):
        return None


def ref_key(ref):  # J35912-04 -> ('J35912', 4) so later revisions win
    m = re.match(r'([A-Z]\d{5})-(\d{2})', ref or '')
    return (m[1], int(m[2])) if m else (ref or '', 0)


def months_of(start, end):
    """Yield (YYYY-MM, days covered, days in month) for a period."""
    s, e = d(start), d(end)
    if not s or not e or e < s:
        return
    cur = s
    while cur <= e:
        dim = calendar.monthrange(cur.year, cur.month)[1]
        last = date(cur.year, cur.month, dim)
        yield f'{cur:%Y-%m}', (min(e, last) - cur).days + 1, dim
        cur = last + timedelta(days=1)


def prorate(start, end):
    return round(sum(c / m for _, c, m in months_of(start, end)), 4) or 1.0


# ---------------- price book ----------------
def load_prices():
    rows = []
    for p in csv.DictReader(open(os.path.join(W, 'contract_prices.csv'))):
        rows.append(dict(ref=p['contract_ref'], loc=p['location_id'], svc=p['service_id'], act=p['activity_type'],
                         mrc=num(p['mrc']), nrc=num(p['nrc']), cur=p['currency'], src=p['source_path'],
                         desc=p['item_description'] + ' ' + p['service_name']))
    for f in glob.glob(os.path.join(W, '*.jsonl')):
        for line in open(f):
            r = json.loads(line)
            if r.get('row_type') != 'price':
                continue
            rows.append(dict(ref=r.get('amendment_id'), loc=r.get('location_id'), svc=r.get('service_id'),
                             act=r.get('activity_type'), mrc=num(r.get('mrc')), nrc=num(r.get('nrc')),
                             cur=r.get('currency'), src=r.get('source_path') or os.path.basename(f),
                             desc=f"{r.get('service_name') or ''} {r.get('text') or ''}"))
    book, seen, loc_pass, esc = {}, {}, collections.defaultdict(float), dict(ESCALATOR_SEED)
    for r in rows:
        m = ESCALATOR.search(r['desc'] or '')
        if m and r['ref']:
            esc[r['ref']] = (int(m[1]), float(m[2]) / 100)
        if not r['svc']:
            # service-less rows are location-level Landed Costs / Shipping: the cap for CPE NRCs at that site
            sig = (r['ref'], r['loc'], r['desc'], r['nrc'])
            if r['nrc'] and r['loc'] and PASSTHROUGH.search(r['desc'] or '') and seen.setdefault(sig, r['src']) == r['src']:
                loc_pass[(r['ref'], r['loc'], r['cur'])] += r['nrc']
            continue
        sig = (r['ref'], str(r['svc']), r['act'], r['mrc'], r['nrc'])
        if seen.setdefault(sig, r['src']) != r['src']:
            continue   # identical row from another copy of the same contract (filed under two names)
        b = book.setdefault((r['ref'], str(r['svc'])),
                            dict(mrc=0.0, nrc=0.0, disc=0.0, comp=collections.Counter(), removed=False, usage=False, cur=r['cur'], src=r['src'], loc=r['loc']))
        b['usage'] |= 'usage' in (r['desc'] or '').lower()
        act = (r['act'] or '').upper()
        if act == 'REMOVED':
            b['removed'] = True
        elif act == 'DISCOUNT' or (r['mrc'] or 0) < 0:
            b['disc'] += r['mrc'] or 0          # contract discount row, e.g. 'Internet Dedicated Services (60%)' = -786
        else:
            b['mrc'] += r['mrc'] or 0
            if r['mrc']:
                b['comp'][r['mrc']] += 1            # component lines, for escalator tests that hit only some lines
            b['nrc'] += r['nrc'] or 0
    by_svc = collections.defaultdict(list)
    for (ref, svc), b in book.items():
        by_svc[svc].append((ref, b))
    for svc in by_svc:
        by_svc[svc].sort(key=lambda t: ref_key(t[0]))
    return book, by_svc, {r['ref'] for r in rows if r['ref']}, loc_pass, esc


def is_signed(src):
    """ponytail: signature is only visible in the file name; unsigned copies (DocuSign/AdobeSign drafts) sit in 'Missing Document'."""
    return bool(re.search(r'sign', os.path.basename(src or ''), re.I)) or '/Verizon/' in (src or '') or 'OneDrive' in (src or '')


def resolve(ref, svc, book, by_svc, docs):
    """-> (priced_by, price entry or None, reason when unpriced)"""
    if ref and (ref, svc) in book:
        return ref, book[(ref, svc)], ''
    if by_svc.get(svc):
        # an older revision of the *cited* contract is stale. When the cited doc is on file but lacks this service, family order is
        # meaningless (services move between SOFs; blocking all 244 such OK rows would lose coverage), so main() judges: a fallback
        # that matches the bill is fine, one that doesn't is CITED_REVISION_NOT_PROVIDED. Cited doc absent: block outright.
        cands = [t for t in by_svc[svc] if not ref or ref == MASTER_CONTRACT or ref_key(t[0])[0] != ref_key(ref)[0] or ref_key(t[0]) >= ref_key(ref)]
        if not cands or (ref and ref != MASTER_CONTRACT and ref not in docs and ref_key(ref) > ref_key(by_svc[svc][-1][0])):
            return '', None, 'CITED_REVISION_NOT_PROVIDED'   # invoice cites a newer revision we don't have; older price would mislead
        # ponytail: no effective dates per revision yet; fall back to the latest *non-removing* revision and mark it
        live = [t for t in cands if not (t[1]['removed'] and t[1]['mrc'] == 0)] or cands
        live = [t for t in live if is_signed(t[1]['src'])] or live   # never an unsigned copy when a signed one exists
        return (*live[-1], 'FALLBACK_REVISION')
    if ref == MASTER_CONTRACT:
        return '', None, 'MASTER_RATE_CARD'          # priced off master-agreement rate cards, not a per-service SOF
    if ref and ref not in docs:
        return '', None, 'CONTRACT_NOT_PROVIDED'
    return '', None, 'SERVICE_NOT_IN_CONTRACT' if ref else 'NO_CONTRACT_REF'


def fx_rates():
    # ponytail: borrows legacy per-invoice conversion_rate (invoice-date FX); replace with own FX table per Currency Exchange Flow
    snap = json.load(open(os.path.join(W, '..', 'legacy', 'api-snapshot.json')))
    return {i['invoice_id']: i['conversion_rate'] for i in snap['invoices_verizon']['body']['data'] if i.get('conversion_rate')}


def load_lines():
    lines, first_src = [], {}
    for f in ('invoice_lines.csv', 'invoice_lines_other.csv'):
        for l in csv.DictReader(open(os.path.join(W, f))):
            if first_src.setdefault(l['invoice_no'], l['source_path']) != l['source_path']:
                continue   # same invoice delivered as two PDFs (e.g. India AC_/vz_ signed copies)
            lines.append(l)
    return lines


PASSTHROUGH = re.compile(r'landed cost|import vat|shipping|delivery charge', re.I)
# fees with no SOF row by nature (order changes, cancellations, priority restoration): a question for Verizon, not an install/MRC check
FEE = re.compile(r'pending order change|cancellation (fee|-)|change fee|telecommunications service priority', re.I)
ESCALATOR = re.compile(r'increase every (\d+) year\(?s?\)? of (\d+(?:\.\d+)?) percent', re.I)
# footnote text of the SOF PDFs is not in this checkout; N25702-01 footnote 1 taken from audit2 (3.0%/yr)
ESCALATOR_SEED = {'N25702-01': (1, 0.03)}


def month_weights(l):
    spans = list(months_of(l['period_start'], l['period_end'])) or [((l['invoice_date'] or '')[:7], 1, 1)]
    tot = sum(c / m for _, c, m in spans)
    return [(m, (c / dim) / tot) for m, c, dim in spans]


def is_escalation(billed, expected):
    return expected > 0 and any(abs(billed / expected - (1 + p) ** n) < 0.002 for p in (0.03, 0.05) for n in range(1, 6))


def is_line_escalation(diff, hit, esc):
    """diff == k identical SOF component lines x ((1+p)^y - 1): the footnote escalator hits only some lines (6 x 800 x 3% = 144)."""
    if not esc or diff <= 0:
        return False
    n, p = esc
    return any(abs(diff - k * m * ((1 + p) ** y - 1)) < 0.011 for m, cnt in hit['comp'].items() for k in range(1, cnt + 1) for y in range(1, 6))


def stale_fallback(cited, reason, priced_by):
    return reason == 'FALLBACK_REVISION' and bool(cited) and cited != MASTER_CONTRACT and ref_key(cited) > ref_key(priced_by)


def is_etl(l):
    s, e = d(l['period_start']), d(l['period_end'])
    return 'early termination' in (l['description'] or '').lower() or bool(s and e and (e - s).days > 60)


def add_months(m, k):
    y, mo = divmod(int(m[:4]) * 12 + int(m[5:7]) - 1 + k, 12)
    return f'{y}-{mo + 1:02d}'


def month_diff(a, b):   # b - a in months
    return (int(b[:4]) * 12 + int(b[5:7])) - (int(a[:4]) * 12 + int(a[5:7]))


def lag_of(lags, svc):
    """Usual gap between service month and the invoice carrying its main recurring charge (0 = advance, 1 = arrears)."""
    return lags[svc].most_common(1)[0][0] if lags.get(svc) else 0


def judge(billed, expected):
    diff = billed - expected
    if abs(diff) <= max(TOL_ABS, abs(expected) * TOL_PCT):
        return 'OK'
    return 'OVERBILLED' if diff > 0 else 'UNDERBILLED'


# ---------------- engine ----------------
def main():
    book, by_svc, docs, loc_pass, esc = load_prices()
    fx = fx_rates()
    lines = load_lines()

    ledger = collections.OrderedDict()   # (svc, currency, month) -> entry
    nrc = collections.OrderedDict()      # svc -> entry
    etl, seen_months, passthrough = [], set(), []
    fees = collections.OrderedDict()     # (svc, currency, month or '') -> non-SOF fee entry
    credits = collections.defaultdict(float)             # (svc, currency, month) -> credits/adjustments, incl. credit notes
    discounts = collections.defaultdict(float)           # (svc, currency, month) -> separate DISCOUNT lines
    lags = collections.defaultdict(collections.Counter)   # svc -> {invoice month - service month: count}         # early-termination liabilities; (account, invoice month) present in corpus
    unpriced_other = 0
    for l in sorted(lines, key=lambda l: (l['invoice_date'] or '', l['invoice_no'])):
        ct, svc = l['charge_type'], l['service_id']
        if ct in ('CREDIT', 'ADJ') and svc:
            for month, w in month_weights(l):
                credits[(svc, l['currency'], month)] += (num(l['amount']) or 0) * w
            continue
        if ct == 'DISCOUNT' and svc:   # US statement / Hungary: discount billed as its own line, net it into the service-month
            for month, w in month_weights(l):
                discounts[(svc, l['currency'], month)] += (num(l['amount']) or 0) * w
            continue
        if ct not in ('REC', 'NRC') or not svc:
            unpriced_other += 1
            continue
        amt = num(l['amount']) or 0
        net = amt + (num(l['discount']) or 0)
        rate = 1.0 if l['currency'] == 'USD' else fx.get(l['invoice_no'])
        priced_by, hit, reason = resolve(l['contract_ref'], svc, book, by_svc, docs)
        base = dict(service_id=svc, service_name=l['service_name'], location_id=l['location_id'], account=l['account_number'],
                    currency=l['currency'], cited_contract=l['contract_ref'], priced_by=priced_by, reason=reason, hit=hit)
        desc = l['description'] or ''
        if ct == 'NRC' and PASSTHROUGH.search(desc):
            passthrough.append(dict(base, invoice_no=l['invoice_no'], billed=amt, fx=rate, loc_check=False))   # 'Landed Costs - Purchase' splits into duty/VAT/shipping components that exceed the SOF row legitimately
            continue
        if ct == 'NRC' and desc.startswith('CPE -') and hit and hit['nrc'] == 0 and not hit['usage']:
            # INTL_EN prints CPE install NRCs as 'CPE - (svc/ref)'; the SOF prices them only in the location-level Landed Costs row
            passthrough.append(dict(base, invoice_no=l['invoice_no'], billed=amt, fx=rate, loc_check=True))
            continue
        if ct == 'NRC' and is_etl(l):
            etl.append(dict(base, invoice_no=l['invoice_no'], period_start=l['period_start'], period_end=l['period_end'],
                            billed=amt, fx=rate, description=l['description']))
            continue
        if FEE.search(desc):   # REC (TSP) or NRC: keep out of the ledger/NRC cumulation, report as a question
            for month, w in (month_weights(l) if ct == 'REC' else [('', 1.0)]):
                fe = fees.setdefault((svc, l['currency'], month), dict(base, month=month, billed=0.0, invoices=set(), descs=set(), fx=rate, ct=ct))
                fe['billed'] += amt * w; fe['invoices'].add(l['invoice_no']); fe['descs'].add(re.sub(r'\s*\(?\d[\d/-]*\)?$', '', desc)[:50])
            continue
        if ct == 'NRC':
            e = nrc.setdefault(svc, dict(base, billed=0.0, billed_usd=0.0, invoices=[], fx=rate))
            e['billed'] += amt; e['billed_usd'] += amt * (rate or 0); e['invoices'].append(l['invoice_no'])
            continue
        spans = list(months_of(l['period_start'], l['period_end'])) or [((l['invoice_date'] or '')[:7], 1, 1)]
        total_frac = sum(c / m for _, c, m in spans)
        for month, covered, dim in spans:
            w = (covered / dim) / total_frac   # a 2-month line puts half in each month, regardless of month length
            e = ledger.setdefault((svc, l['currency'], month),
                                  dict(base, month=month, billed=0.0, net=0.0, cover=0.0, invoices=set(), raw=set(), fx=rate))
            e['billed'] += amt * w
            e['net'] += net * w
            if l.get('raw_type') != 'CE' or e['cover'] == 0:
                e['cover'] = max(e['cover'], covered / dim)   # components of one service share the period: don't add them up
            e['invoices'].add(l['invoice_no']); e['raw'].add(l.get('raw_type') or 'REC')
            if hit and (not e['hit'] or e['reason'] == 'FALLBACK_REVISION'):
                e.update(priced_by=priced_by, hit=hit, reason=reason)
            seen_months.add((l['account_number'], (l['invoice_date'] or '')[:7]))
            if l.get('raw_type', 'REC') == 'REC' and covered == dim:
                lags[svc][month_diff(month, (l['invoice_date'] or month)[:7])] += 1

    orphan_disc = 0.0
    for k, v in discounts.items():
        if k in ledger:
            ledger[k]['net'] += v
        else:
            orphan_disc += v
    if orphan_disc:
        print(f'DISCOUNT lines with no matching service-month: {orphan_disc:,.2f}')
    rows = []
    for (svc, cur, month), e in ledger.items():
        billed_cmp = round(e['billed'], 2)
        hit, billed, net = e['hit'], round(e['billed'], 2), round(e['net'], 2)
        expected = None
        if not hit:
            cat = e['reason']
        elif hit['usage']:
            cat = 'USAGE_BASED'                       # contract item is metered; flat MRC comparison doesn't apply
        elif hit['cur'] and hit['cur'] != cur:
            cat = 'CURRENCY_MISMATCH'                 # ponytail: needs SOF/amendment FX rate per Currency Exchange Flow
        elif hit['removed'] and hit['mrc'] == 0:
            if e['reason'] == 'FALLBACK_REVISION':
                cat = 'REMOVAL_REVIEW'                # removal known only from another revision; no effective date
            else:
                cat, expected = ('BILLED_AFTER_REMOVAL', 0.0) if abs(billed) > TOL_ABS else ('OK', 0.0)
        else:
            cover = e['cover'] or 1.0
            list_exp, net_exp = round(hit['mrc'] * cover, 2), round((hit['mrc'] + hit['disc']) * cover, 2)
            # compare like with like: contract net vs billed net when the SOF carries a discount, else list vs gross;
            # a match on the other basis is still OK (discount applied from the master agreement instead of the SOF)
            if hit['disc']:
                expected, got = net_exp, net
            else:
                expected, got = list_exp, billed
            cat = judge(got, expected)
            if cat != 'OK' and stale_fallback(e['cited_contract'], e['reason'], e['priced_by']):
                cat = 'CITED_REVISION_NOT_PROVIDED'   # price comes from a revision older than the cited one, which lacks this service
            if cat != 'OK' and (judge(billed, list_exp) == 'OK' or judge(net, list_exp) == 'OK'):
                cat = 'OK'
            billed_cmp = got
            credit = round(credits.get((svc, cur, month), 0.0), 2)
            if cat == 'OVERBILLED' and credit and judge(got + credit, expected) != 'OVERBILLED':
                cat = 'REFUNDED'                      # a credit line / credit note for this service-month already fixed it
            elif cat == 'OVERBILLED' and (is_escalation(got, expected) or is_line_escalation(got - expected, hit, esc.get(e['priced_by']))):
                cat = 'ESCALATOR_REVIEW'              # matches a 3-5%/yr contractual increase; check the SOF footnote
            if cat not in ('OK', 'CITED_REVISION_NOT_PROVIDED'):
                if e['cited_contract'] == MASTER_CONTRACT and not hit['disc']:
                    cat = 'PRICE_BASIS_UNCERTAIN'     # invoice prices off master agreement; SOF list price may not apply
                elif cat == 'UNDERBILLED' and (e['account'], add_months(month, lag_of(lags, svc))) not in seen_months:
                    cat = 'INCOMPLETE_MONTH'          # the invoice that would carry this month is missing from the corpus
                elif e['reason'] == 'FALLBACK_REVISION':
                    cat += '_FALLBACK'                # priced by a revision the invoice didn't cite: lower confidence
        rows.append(dict(kind='REC', service_id=svc, month=month, currency=cur, location_id=e['location_id'],
                         service_name=e['service_name'], account=e['account'], cited_contract=e['cited_contract'],
                         priced_by=e['priced_by'], billed=billed, billed_net=net, credits=round(credits.get((svc, cur, month), 0.0), 2), expected=expected,
                         discrepancy=round((billed_cmp if expected not in (None, 0.0) or cat == 'OK' else billed) - expected, 2)
                         if expected is not None and cat not in ('OK',) else (0.0 if cat == 'OK' else None),
                         category=cat, invoices=' '.join(sorted(e['invoices'])), line_types='/'.join(sorted(e['raw'])),
                         fx_to_usd=e['fx']))
    for svc, e in nrc.items():
        hit, billed = e['hit'], round(e['billed'], 2)
        expected = round(hit['nrc'], 2) if hit and not hit['usage'] else None
        if not hit:
            cat = e['reason']
        elif hit['removed'] and hit['nrc'] == 0 and hit['mrc'] == 0:
            cat, expected = 'NRC_NO_PRICE', None     # only REMOVED zero rows: 0 is a removal marker, not an install price
        elif expected is None:
            cat = 'USAGE_BASED'
        elif billed - expected <= loc_pass.get((e['cited_contract'], e['location_id'], e['currency']), 0.0) + max(TOL_ABS, expected * TOL_PCT) \
                and billed > expected + max(TOL_ABS, expected * TOL_PCT):
            cat = 'NRC_OK'   # excess is within the SOF location-level Landed Costs / Shipping row (e.g. 91.27 + 40.47 + 0.39 = 132.13)
        elif billed - expected > max(TOL_ABS, expected * TOL_PCT):
            cat = 'CITED_REVISION_NOT_PROVIDED' if stale_fallback(e['cited_contract'], e['reason'], e['priced_by']) else 'NRC_OVERBILLED'
        else:
            cat = 'NRC_OK' if abs(billed - expected) <= max(TOL_ABS, expected * TOL_PCT) else 'NRC_INSTALMENTS_REMAINING'
        rows.append(dict(kind='NRC', service_id=svc, month='', currency=e['currency'], location_id=e['location_id'],
                         service_name=e['service_name'], account=e['account'], cited_contract=e['cited_contract'],
                         priced_by=e['priced_by'], billed=billed, billed_net=billed, credits='', expected=expected,
                         discrepancy=round(billed - expected, 2) if expected is not None and cat == 'NRC_OVERBILLED' else None,
                         category=cat, invoices=' '.join(e['invoices']), line_types='NRC', fx_to_usd=e['fx']))
    for t in etl:   # 2. early-termination liability: commercial (waiver) item, not a pricing error
        hit = t['hit']
        months_left = prorate(t['period_start'], t['period_end'])
        est = round(0.75 * hit['mrc'] * months_left, 2) if hit and hit['mrc'] else None   # ponytail: 75% rule observed, confirm in contract
        rows.append(dict(kind='ETL', service_id=t['service_id'], month=t['period_start'][:7], currency=t['currency'],
                         location_id=t['location_id'], service_name=t['service_name'], account=t['account'],
                         cited_contract=t['cited_contract'], priced_by=t['priced_by'], billed=round(t['billed'], 2),
                         billed_net=round(t['billed'], 2), credits='', expected=est, discrepancy=None, category='EARLY_TERMINATION',
                         invoices=t['invoice_no'], line_types='NRC', fx_to_usd=t['fx']))

    cpe_loc = collections.defaultdict(float)   # (contract, location, currency) -> CPE/landed NRC billed across all invoices (pairs split by month)
    for t in passthrough:
        if t['loc_check']:
            cpe_loc[(t['cited_contract'], t['location_id'], t['currency'])] += t['billed']
    for t in passthrough:   # F3: landed costs / import VAT / shipping: compare at location level with the SOF, not per service
        k = (t['cited_contract'], t['location_id'], t['currency'])
        cap = loc_pass.get(k)
        cat = 'NRC_PASSTHROUGH_MISMATCH' if t['loc_check'] and cap and cpe_loc[k] > cap + 0.02 else 'NRC_PASSTHROUGH'
        rows.append(dict(kind='NRC', service_id=t['service_id'], month='', currency=t['currency'], location_id=t['location_id'],
                         service_name=t['service_name'], account=t['account'], cited_contract=t['cited_contract'],
                         priced_by=t['priced_by'], billed=round(t['billed'], 2), billed_net=round(t['billed'], 2), credits='',
                         expected=round(cap, 2) if t['loc_check'] and cap else None, discrepancy=None, category=cat,
                         invoices=t['invoice_no'], line_types='NRC', fx_to_usd=t['fx']))
    for (svc, cur, month), t in fees.items():   # non-SOF fees: always a question, never a claim (discrepancy stays blank)
        rows.append(dict(kind='FEE', service_id=svc, month=month, currency=cur, location_id=t['location_id'],
                         service_name=t['service_name'] + ' | ' + '; '.join(sorted(t['descs'])), account=t['account'],
                         cited_contract=t['cited_contract'], priced_by=t['priced_by'], billed=round(t['billed'], 2),
                         billed_net=round(t['billed'], 2), credits='', expected=None, discrepancy=None, category='FEE_REVIEW',
                         invoices=' '.join(sorted(t['invoices'])), line_types=t['ct'], fx_to_usd=t['fx']))
    price_drift(rows)
    for r in rows:
        rate = r['fx_to_usd']
        r['billed_usd'] = round(r['billed'] * rate, 2) if rate else None
        r['billed_net_usd'] = round(r['billed_net'] * rate, 2) if rate else None
        r['discrepancy_usd'] = round(r['discrepancy'] * rate, 2) if rate and r['discrepancy'] is not None else None

    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, 'service_month_ledger.csv'), 'w', newline='') as fh:
        w = csv.DictWriter(fh, list(rows[0])); w.writeheader(); w.writerows(rows)
    summarize(rows, unpriced_other)
    return rows


def price_drift(rows):
    """Contract-free check for unpriced services: monthly rate changes between fully covered months."""
    last = {}
    for r in sorted((r for r in rows if r['kind'] == 'REC'), key=lambda r: (r['service_id'], r['currency'], r['month'])):
        r['drift_vs_prev_month'] = ''
        k = (r['service_id'], r['currency'])
        if r['line_types'] != 'REC':
            continue
        prev = last.get(k)
        if prev is not None and abs(r['billed'] - prev) > max(TOL_ABS, abs(prev) * TOL_PCT):
            r['drift_vs_prev_month'] = round(r['billed'] - prev, 2)
            if r['expected'] is None and r['category'] != 'USAGE_BASED':
                r['category'] += '+DRIFT'
        last[k] = r['billed']
    for r in rows:
        r.setdefault('drift_vs_prev_month', '')


def summarize(rows, unpriced_other):
    s = collections.defaultdict(lambda: [0, 0.0, 0.0])
    for r in rows:
        x = s[r['category']]; x[0] += 1; x[1] += r['billed_usd'] or 0; x[2] += r['discrepancy_usd'] or 0
    print(f"{'category (USD)':30}{'rows':>8}{'billed':>14}{'discrepancy':>14}")
    for c, (n, b, dsc) in sorted(s.items(), key=lambda kv: -kv[1][1]):
        print(f'{c:30}{n:8}{b:14,.0f}{dsc:14,.0f}')
    print('lines not price-checkable (discount/credit/tax/usage/no service id):', unpriced_other,
          '| rows without FX:', sum(1 for r in rows if r['billed_usd'] is None))


def _selfcheck():
    assert prorate('2024-10-01', '2024-11-30') == 2.0
    assert prorate('2024-02-01', '2024-02-29') == 1.0
    assert abs(prorate('2024-03-16', '2024-03-31') - 16 / 31) < 1e-3
    assert prorate('2024-03-01', '2024-09-30') == 7.0
    assert ref_key('J35912-04') > ref_key('J35912-00')
    assert num('86,91') == 86.91 and num('1,234.56') == 1234.56 and num('1.234,56') == 1234.56 and num("2'948.04") == 2948.04 and num('18,791') == 18791
    assert add_months('2025-12', 1) == '2026-01' and add_months('2025-01', -1) == '2024-12' and month_diff('2025-11', '2026-01') == 2
    assert is_etl(dict(period_start='2026-01-02', period_end='2027-08-01', description='Access'))
    assert not is_etl(dict(period_start='2026-01-01', period_end='2026-01-31', description='Install'))
    assert is_escalation(9149.96, 9149.96 / 1.03) and not is_escalation(110, 100)
    assert [round(w, 3) for _, w in month_weights(dict(period_start='2025-09-01', period_end='2025-10-31', invoice_date=''))] == [0.5, 0.5]
    assert ESCALATOR.search('subject to an increase every 1 year(s) of 3.0 percent')[2] == '3.0'
    assert is_line_escalation(144.0, dict(comp=collections.Counter({800.0: 6})), (1, 0.03)) and not is_line_escalation(100, dict(comp=collections.Counter({800.0: 6})), (1, 0.03))
    assert FEE.search('Pending Order Change') and FEE.search('Telecommunications Service Priority - Restoration - 1') and not FEE.search('Access - NRC')
    assert judge(100.5, 100) == 'OK' and judge(110, 100) == 'OVERBILLED' and judge(80, 100) == 'UNDERBILLED'


if __name__ == '__main__':
    _selfcheck()
    main()
