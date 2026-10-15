"""Rate-card pricing check for the unpriced pool (master agreement 208686, Amendment 28 = L51187-02).

Pool = ledger rows categorised MASTER_RATE_CARD / NO_CONTRACT_REF / CONTRACT_NOT_PROVIDED / SERVICE_NOT_IN_CONTRACT (+DRIFT).
Writes work/engine_out/rate_card.csv and rate_card_checks.csv.  Run: python3 -I work/engine/rate_card.py

Findings that drive the rules (each verified on invoices, see report):
- Amendment 28 pp.42-43 PIP Port rates are fixed NET charges ("fixed charges are not eligible for any discounts", p.11);
  invoices from service month 2024-02 bill exactly these with no discount line.  Earlier months are priced under the
  pre-amendment pricebook (list 1/0.64 x net, PIP discounts 34%/45%) -> not checkable against Amendment 28.
- pp.44-48 (Non-Optimized, "net rate for illustrative purposes only") are inconsistent with invoices -> LOW confidence fallback.
- Amendment 28 holds no Managed WAN / SD-WAN / Internet Dedicated tables; for those the only price source is the SOF price
  book (contract_prices.csv), used as a tier consensus (MED confidence when >=2 SOF rows agree, LOW for a single row).
"""
import csv, json, os, re, sys, collections, importlib.util

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
W = os.path.join(HERE, '..')
OUT = os.path.join(W, 'engine_out')
_sp = importlib.util.spec_from_file_location('discrepancy', os.path.join(HERE, 'discrepancy.py'))
D = importlib.util.module_from_spec(_sp); _sp.loader.exec_module(D)   # reuse num/load_lines/months_of, no edits to it

EFFECTIVE = '2024-02'            # first service month billed at Amendment 28 rates (verified on invoices)
TOL_ABS, TOL_PCT, TOL_DISC = 1.00, 0.01, 0.5
POOL = re.compile(r'(MASTER_RATE_CARD|NO_CONTRACT_REF|CONTRACT_NOT_PROVIDED|SERVICE_NOT_IN_CONTRACT)')
DISC_TERMS = {'PIP GLOBAL': 50.0, 'PIP USA': 55.0, 'PIP GLOBAL CE': 50.0, 'PIP USA CE': 55.0}   # Amendment 28 p.11
ALIAS = {'united states of america': 'united states', 'usa': 'united states', 'united kingdom': 'uk',
         'korea (south)': 'korea, republic of', 'korea, republic of': 'korea, republic of', 'russia': 'russian federation',
         'czechia': 'czech republic', 'hong kong sar': 'hong kong'}


def cn(c):
    c = re.sub(r'\s+', ' ', (c or '').strip().lower())
    return ALIAS.get(c, c)


def speed(s):
    m = re.search(r'([\d.]+)\s*(Mbps|Gbps|Kbps)', s or '', re.I)
    if not m:
        return None
    v = float(m[1]) * {'mbps': 1, 'gbps': 1000, 'kbps': 0.001}[m[2].lower()]
    return f'{v:g}'


# ---------------- rate card ----------------
def build_card():
    rows = []
    for l in open(os.path.join(W, 'amend28_p1_57.jsonl')):
        r = json.loads(l)
        if r['row_type'] == 'rate' and r.get('discount_pct') and r.get('service_name') in DISC_TERMS:
            rows.append(dict(product=r['service_name'], tier_or_speed='discount off Standard Service Charge', country='ALL',
                             list_rate='', discount_pct=r['discount_pct'], net_rate='', currency='', source_page=r['page'],
                             rate_type='DISCOUNT_TERM', note='Optimized PIP discount; applies to non-fixed charges only'))
        elif r['row_type'] == 'rate' and r.get('service_name') == 'PIP Port' and r['page'] in (42, 43):
            rows.append(dict(product='PIP Port', tier_or_speed=speed(r['text']) + ' Mbps', country=r['country'], list_rate='',
                             discount_pct='', net_rate=r['mrc'], currency=r['currency'], source_page=r['page'],
                             rate_type='NET_FIXED', note='Ethernet; printed rate is net (fixed charge, no further discount)'))
        elif r['row_type'] == 'rate' and r.get('service_name') == 'PIP Port - Dynamic Network Manager':
            rows.append(dict(product='PIP Port', tier_or_speed='100 Mbps', country=r['country'], list_rate='', discount_pct='',
                             net_rate=r['mrc'], currency=r['currency'], source_page=r['page'], rate_type='NET_FIXED_DYNAMIC',
                             note='Dynamic Network Manager variant (alt to static 561.00)'))
        elif r['row_type'] == 'rate' and 44 <= r['page'] <= 48 and r.get('mrc') and 'net rate' in (r.get('text') or ''):
            m = re.search(r'net rate \$([\d,.]+)', r['text']); net = D.num(m[1]) if m else None
            if net and speed(r['text']) and 'Gold' not in r['text']:
                rows.append(dict(product='PIP Port', tier_or_speed=speed(r['text']) + ' Mbps', country=r['country'], list_rate=r['mrc'],
                                 discount_pct=round(100 * (1 - net / r['mrc']), 2), net_rate=net, currency=r['currency'],
                                 source_page=r['page'], rate_type='NONOPT_ILLUSTRATIVE',
                                 note=f"{r['service_name'][:40]}: 'net rate for illustrative purposes only'; list is ~10x p.42-43 net; not what invoices bill"))
        elif r['row_type'] == 'rate' and 'Class of Service' in (r.get('service_name') or '') + (r.get('text') or ''):
            rows.append(dict(product='PIP Class of Service (EF Realtime CAR)', tier_or_speed='0 Kbps-90 Mbps', country=r['country'],
                             list_rate='', discount_pct='', net_rate=0.0, currency='USD', source_page=r['page'], rate_type='NET_FIXED',
                             note='table not itemised, all rows 0.00'))
        elif r['row_type'] == 'rate' and 'Gold CAR' in (r.get('service_name') or ''):
            rows.append(dict(product='Gold CAR', tier_or_speed='all', country='ALL', list_rate='', discount_pct='', net_rate=0.0,
                             currency='USD', source_page=r['page'], rate_type='NET_FIXED', note='table not itemised, all rows 0.00'))
    rows += sof_consensus()
    return rows


def sof_key(desc):
    """Normalise an item description (SOF or invoice) to (product, tier, country) or None."""
    d = re.sub(r'^.*?(?=(Network Engineering|Software Defined Secure Branch|Internet Port|PIP Port|Router Management|Network Analysis))', '', desc.strip(), flags=re.S)
    d = re.split(r'\s*\|?\s*Discount\s*:', d)[0].strip()
    p = [x.strip() for x in d.split(' - ')]
    if p[0] == 'Software Defined Secure Branch' and len(p) >= 4:
        feat = re.search(r'^(.*?\d+\s?(?:mbps|gbps))', ' - '.join(p[4:]).lower())   # feature+bandwidth; SOF tails are truncated
        return p[0], ' - '.join(p[1:4]) + (' | ' + re.sub(r'\s+', ' ', feat[1]) if feat else ''), ''
    if p[0] == 'Internet Port' and len(p) >= 4:
        return p[0], f'{speed(p[2])} Mbps', cn(p[3])
    if p[0] == 'Network Engineering' and len(p) == 2:
        return p[0], p[1], ''
    return None


def sof_consensus():
    g = collections.defaultdict(list)
    for r in csv.DictReader(open(os.path.join(W, 'contract_prices.csv'))):
        k = sof_key(r['item_description']); m = D.num(r['mrc'])
        if k and m and m > 0 and (r['activity_type'] or '').upper() != 'REMOVED':
            g[(k, r['currency'])].append(m)
    out = []
    for (k, cur), v in sorted(g.items()):
        mode, n = collections.Counter(v).most_common(1)[0]
        if n != len(v):   # require unanimous SOF rows
            continue
        out.append(dict(product=k[0], tier_or_speed=k[1], country=k[2].title() if k[2] else '', list_rate=mode, discount_pct='', net_rate='',
                        currency=cur, source_page='contract_prices.csv', rate_type='SOF_CONSENSUS_N%d' % len(v),
                        note='SOF MRC; discount not in SOF (billed discount is checked for consistency only)'))
    return out


# ---------------- parsing ----------------
def parse(desc):
    """invoice description -> dict(product, tier, country, label) or None"""
    d = desc.strip()
    m = re.search(r'Discount\s*:\s*(.*?)\s*\((\d+(?:\.\d+)?)%\)', d)
    label, lpct = (m[1].strip(), float(m[2])) if m else ('', None)
    base = re.split(r'\s*\|?\s*Discount\s*:', d)[0].strip()
    p = [x.strip() for x in base.split(' - ')]
    if p[0] == 'PIP Port' and len(p) == 3:
        return dict(product='PIP Port', tier=f'{speed(p[1])} Mbps', country=cn(p[2]), label=label, lpct=lpct)
    if p[0] == 'Class of Service' and len(p) >= 3:
        return dict(product='Class of Service', tier=' - '.join(p[1:]), country='', label=label, lpct=lpct)
    k = sof_key(base)
    if k:
        return dict(product=k[0], tier=k[1], country=k[2], label=label, lpct=lpct)
    if p[0] in ('Router Management', 'Network Analysis'):
        return dict(product=p[0], tier=' - '.join(p[1:]), country='', label=label, lpct=lpct)
    return None


def sof_find(sof, prod, tier, ctry, cur):
    hit = sof.get((prod, tier, ctry, cur))
    if not hit and ' | adv sd wan + adv ng fw' in tier:   # standard feature set: SOF text is often truncated before it
        hit = sof.get((prod, tier.split(' | ')[0], ctry, cur))
    return hit


# ---------------- engine ----------------
def main():
    card = build_card()
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, 'rate_card.csv'), 'w', newline='') as fh:
        cols = ['product', 'tier_or_speed', 'country', 'list_rate', 'discount_pct', 'net_rate', 'currency', 'source_page', 'rate_type', 'note']
        w = csv.DictWriter(fh, cols); w.writeheader(); w.writerows(card)

    pip = collections.defaultdict(list)       # (country, tier) -> [(net, type)]
    sof = {}                                   # (product, tier, country, currency) -> (list, type)
    for r in card:
        if r['product'] == 'PIP Port' and r['rate_type'].startswith(('NET', 'NONOPT')) and r['net_rate'] != '':
            pip[(cn(r['country']), r['tier_or_speed'])].append((r['net_rate'], r['rate_type']))
        elif r['rate_type'].startswith('SOF'):
            sof[(r['product'], r['tier_or_speed'], cn(r['country']), r['currency'])] = (r['list_rate'], r['rate_type'])

    pool = {}
    for r in csv.DictReader(open(os.path.join(OUT, 'service_month_ledger.csv'))):
        if r['kind'] == 'REC' and POOL.match(r['category']):
            pool[(r['service_id'], r['currency'], r['month'])] = r
    svcs = {k[0] for k in pool}

    agg = collections.OrderedDict()
    for l in sorted(D.load_lines(), key=lambda l: (l['invoice_date'] or '', l['invoice_no'])):
        if l['charge_type'] not in ('REC', 'DISCOUNT') or l['service_id'] not in svcs:
            continue
        pr = parse(l['description'])
        disc = l['charge_type'] == 'DISCOUNT'      # separate DISCOUNT line (e.g. HU invoices): folds into net of same key
        if disc and not pr:
            continue
        amt, net = D.num(l['amount']) or 0, D.num(l['net_amount'])
        net = amt + (D.num(l['discount']) or 0) if net is None else net
        spans = list(D.months_of(l['period_start'], l['period_end'])) or [((l['invoice_date'] or '')[:7], 1, 1)]
        tot = sum(c for _, c, _ in spans)
        for month, cov, dim in spans:
            if (l['service_id'], l['currency'], month) not in pool:
                continue
            key = (l['service_id'], l['currency'], month, pr['product'] if pr else 'UNPARSED:' + (l['service_name'] or ''),
                   pr['tier'] if pr else '', pr['country'] if pr else '')
            e = agg.setdefault(key, dict(pr=pr, gross=0.0, net=0.0, cover=0.0, inv=set(), ce=False, label=set()))
            e['gross'] += 0 if disc else amt * cov / tot; e['net'] += net * cov / tot
            if not disc and (l.get('raw_type') != 'CE' or e['cover'] == 0):
                e['cover'] = min(1.0, e['cover'] + cov / dim)
            e['ce'] |= l.get('raw_type') == 'CE'; e['inv'].add(l['invoice_no'])
            if pr and pr['lpct'] is not None:
                e['label'].add((pr['label'], pr['lpct']))

    rows = []
    for (svc, cur, month, prod, tier, ctry), e in agg.items():
        led = pool[(svc, cur, month)]
        gross, netb, cover, pr = round(e['gross'], 2), round(e['net'], 2), e['cover'] or 1.0, e['pr']
        dbp = round(100 * (gross - netb) / gross, 2) if gross > 0.005 else 0.0
        lab = sorted(e['label'], key=lambda t: t[1])
        label_pct = lab[0][1] if lab else None
        contract = DISC_TERMS.get(lab[0][0].upper()) if lab else None
        exp, cat, conf, basis = None, 'RC_NO_RATE', '', ''
        if pr is None or cur is None:
            basis = 'UNPARSED description'
        elif month < EFFECTIVE and (prod in ('PIP Port', 'Class of Service')):
            basis = 'PRE_AMENDMENT_28 service month (old pricebook, not checkable)'
        elif prod == 'PIP Port' and cur == 'USD' and pip.get((ctry, tier)):
            cands = pip[(ctry, tier)]
            high = [c for c in cands if c[1].startswith('NET')]
            use = high or cands
            conf = 'HIGH' if high else 'LOW'
            per = min(use, key=lambda c: abs(netb - c[0] * cover))      # static vs Dynamic variant: nearest
            exp, basis = round(per[0] * cover, 2), f'card net {per[0]} ({per[1]})'
            if abs(netb - exp) <= max(TOL_ABS, abs(exp) * TOL_PCT):
                cat = 'RC_OK'
            else:
                cat = 'RC_OVERBILLED' if netb > exp else 'RC_UNDERBILLED'
        elif contract is not None and gross > 0 and prod in ('PIP Port', 'Class of Service'):
            # no card rate: gross list unverified, only the discount % is checked against the 50%/55% term
            exp, conf = round(gross * (1 - contract / 100), 2), 'MED'
            basis = f'billed gross x (1-{contract:g}%) [list unverified]'
            if dbp < contract - TOL_DISC:
                cat = 'RC_DISCOUNT_SHORT'
            elif abs(netb - exp) <= max(TOL_ABS, abs(exp) * TOL_PCT):
                cat = 'RC_OK'
            else:
                cat = 'RC_UNDERBILLED'     # discount deeper than contract
        elif sof_find(sof, prod, tier, ctry, cur):
            lst, typ = sof_find(sof, prod, tier, ctry, cur)
            pct = label_pct if label_pct is not None else round(dbp)
            exp = round(lst * (1 - pct / 100) * cover, 2)
            if abs(netb - round(lst * cover, 2)) <= max(TOL_ABS, lst * cover * TOL_PCT):
                exp = round(lst * cover, 2)      # SOF figure may already be net of the discount (e.g. Co-Mgmt 387 = 645 x 60%)
            conf = 'LOW' if typ == 'SOF_CONSENSUS_N1' else 'MED'
            basis = f'SOF list {lst:g} x (1-{pct:g}% billed label) ({typ})'
            if abs(netb - exp) <= max(TOL_ABS, abs(exp) * TOL_PCT):
                cat = 'RC_OK'
            else:
                cat = 'RC_OVERBILLED' if netb > exp else 'RC_UNDERBILLED'
        else:
            basis = 'no rate in Amendment 28 / SOF price book'
        rows.append(dict(service_id=svc, month=month, product=prod, tier=tier, country=ctry.title() if ctry else '', currency=cur,
                         billed=netb, expected=exp, discount_billed_pct=dbp if gross > 0 else '',
                         discount_contract_pct=contract if contract is not None else '',
                         discrepancy=round(netb - exp, 2) if exp is not None else '', category=cat,
                         invoices=' '.join(sorted(e['inv'])), billed_gross=gross, discount_label_pct=label_pct if label_pct is not None else '',
                         confidence=conf, basis=basis + (' | CE catch-up line present' if e['ce'] else ''),
                         ledger_category=led['category'], fx_to_usd=led['fx_to_usd'],
                         billed_usd=round(netb * float(led['fx_to_usd']), 2) if led['fx_to_usd'] else ''))
    cols = list(rows[0])
    with open(os.path.join(OUT, 'rate_card_checks.csv'), 'w', newline='') as fh:
        w = csv.DictWriter(fh, cols); w.writeheader(); w.writerows(rows)
    summarize(rows, pool, agg)
    return rows


def summarize(rows, pool, agg):
    n = collections.Counter(); s = collections.Counter(); d = collections.Counter()
    for r in rows:
        n[r['category']] += 1; s[r['category']] += r['billed_usd'] or 0
        d[r['category']] += (r['discrepancy'] or 0) * float(r['fx_to_usd'] or 0) if r['discrepancy'] != '' else 0
    print(f"{'category':20}{'rows':>7}{'billed_usd':>14}{'discr_usd':>12}")
    for c in sorted(n):
        print(f'{c:20}{n[c]:7}{s[c]:14,.0f}{d[c]:12,.0f}')
    priced = {(r['service_id'], r['currency'], r['month']) for r in rows if r['category'] != 'RC_NO_RATE'}
    tot = sum(float(r['billed_usd'] or 0) for r in pool.values())
    pu = sum(float(pool[k]['billed_usd'] or 0) for k in priced)
    lu = sum(r['billed_usd'] or 0 for r in rows if r['category'] != 'RC_NO_RATE')
    print(f'pool rows {len(pool)} (${tot:,.0f}); service-months with >=1 priced product {len(priced)} (${pu:,.0f} full-row, ${lu:,.0f} priced-line)')
    c = collections.Counter(r['confidence'] for r in rows if r['category'] != 'RC_NO_RATE'); print('confidence', dict(c))


def _selfcheck():
    assert speed('Ethernet 100 Mbps') == '100' and speed('1 Gbps') == '1000'
    assert parse('PIP Port - 10 Mbps - Turkey | Discount : PIP Global (34%)') == dict(product='PIP Port', tier='10 Mbps', country='turkey', label='PIP Global', lpct=34.0)
    assert parse('Network Engineering - Medium')['tier'] == 'Medium'
    assert parse('Internet Port - Tiered - 1 Gbps - United States of America | Discount : Internet Dedicated Services (60%)')['tier'] == '1000 Mbps'
    assert parse('Software Defined Secure Branch - Full - Medium - Versa - Adv SD WAN 500Mbps | Discount : Global SD WAN (40%)')['tier'].startswith('Full - Medium - Versa | adv sd wan')
    assert parse('Local Access - Gold') is None


if __name__ == '__main__':
    _selfcheck()
    main()
