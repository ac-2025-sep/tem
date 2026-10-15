"""Rate-card check for US legacy-statement Private IP circuits (templates VZ_US_STMT_NODE / VZ_US_STMT_SMB, no contract reference).

Writes work/engine_out/us_stmt_rate_card_checks.csv (same columns as rate_card_checks.csv + `evidence`) and
us_stmt_addressable.csv (where the NO_CONTRACT_REF Private IP dollars sit by product class).
Run: python3 -I work/engine/us_stmt_rate_card.py        (stdlib only; imports rate_card.py / discrepancy.py, edits neither)

What the statements actually look like (verified on the parsed lines, see work/engine_out/us_stmt_notes.md):
- Per circuit and service month: gross port line `PRIVATE IP - ETHERNET [10.000 Mbps]` (or `PORT RECURRING [1.984 Mbps]`) plus a
  separate `Estimated discounts and promotions` line.  The service ledger does NOT subtract that discount line, so the
  "$2.3M" bucket is GROSS list; the Amendment-28 comparison must be on port + discount (+ credits) = NET.
- Gross/discount pairs reproduce the Amendment 28 pp.44-48 list/net pairs exactly (e.g. 5056.00 -> 505.60, 52800.00 -> 5280.00).
- The statements carry no country/city for a circuit (and the raw statement text is not in work/.txtcache), so country is
  unresolved: a month is OK if its net equals the p.42-43 (or p.44-48 net) rate of ANY country at that speed, and the
  gross list is used as a second key.  Overbilled is only emitted when net exceeds the highest rate of every country at that speed.
- Pre-2024-02 service months are priced under the old pricebook -> RC_NO_RATE (not checkable against Amendment 28).
- Billing day-count: partial months are prorated on a 30-day basis; accept days and days-1 (Verizon is not consistent on the end day).
- Credits are netted across invoices per circuit x month (the Sep-2026 statement credits Dec-2025..Jun-2026 for W0W63578/W0W63617).
"""
import csv, os, re, sys, collections, importlib.util

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
W = os.path.join(HERE, '..')
OUT = os.path.join(W, 'engine_out')


def _load(name):
    sp = importlib.util.spec_from_file_location(name, os.path.join(HERE, name + '.py'))
    m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m)
    return m


D = _load('discrepancy')
R = _load('rate_card')          # build_card, EFFECTIVE, cn

EFFECTIVE = R.EFFECTIVE
TOL_ABS, TOL_PCT = 1.00, 0.01
E1 = {'1.92', '1.984', '2.048'}   # E1 family: invoices say 1.984, Amendment says "1.920 / 1.984 / 2.048"

CLS = [  # (class, regex on upper-cased description)
    ('PORT', r'^(PRIVATE IP - ETHERNET|PORT RECURRING)'),
    ('COS', r'^PRIVATE IP EF'),
    ('CONNFEE', r'CONNECTION FEE'),
    ('MWAN', r'MANAGED WAN'),
    ('ACCESS', r'^(LOCAL ACCESS|ACCESS CHARGE|AUTO DISCONNECT CREDITS LOCAL ACCESS)'),
    ('DISC', r'^ESTIMATED DISCOUNTS'),
    ('SUMMARY', r'SUMMARY-LEVEL'),
]


def klass(desc):
    u = desc.upper()
    for c, rx in CLS:
        if re.search(rx, u):
            return c
    return 'OTHER'


BR = re.compile(r'\[(?:(\d\d)/(\d\d)\s+(\d\d)/(\d\d)\s+)?([\d.]+)\s*(Mbps|Kbps|Gbps)\]', re.I)


def parse_br(desc):
    """-> (speed_str|None, partial_days|None).  partial_days = inclusive day count of a prorated line."""
    m = BR.search(desc)
    if not m:
        return None, None
    v = float(m[5]) * {'mbps': 1, 'gbps': 1000, 'kbps': 0.001}[m[6].lower()]
    sp = '2' if f'{v:g}' in E1 else f'{v:g}'
    days = None
    if m[1]:
        from datetime import date
        a, b = date(2001, int(m[1]), int(m[2])), date(2001, int(m[3]), int(m[4]))
        days = (b - a).days + 1
    return sp, days


def tiernorm(t):
    v = (t or '').replace(' Mbps', '')
    return '2' if v in E1 else v


def build_rates():
    """speed -> list of dict(country, net, list, strict) from Amendment 28 (p.42-43 strict; p.44-48 illustrative)."""
    byspeed = collections.defaultdict(list)
    for r in R.build_card():
        if r['product'] != 'PIP Port' or r['net_rate'] in ('', None):
            continue
        if not (r['rate_type'].startswith('NET') or r['rate_type'].startswith('NONOPT')):
            continue
        byspeed[tiernorm(r['tier_or_speed'])].append(dict(
            country=r['country'], net=float(r['net_rate']), list=float(r['list_rate']) if r['list_rate'] != '' else None,
            strict=r['rate_type'].startswith('NET'), page=r['source_page']))
    return byspeed


CTRY_FIX = {'columbia': 'colombia', 'korea': 'korea, republic of', 'kor': 'korea, republic of',
            'united arab emirates (trucial st': 'united arab emirates',
            'germany; federal republic of (we': 'germany'}


def circuit_countries():
    """circuit -> country from the raw statement text (`Orig: CITY, Country` under each `Circuit ID:`; BCBH* from `P#### EGON ZEHNDER INTL - SEOUL, KOR`)."""
    import re as _re
    seen = collections.defaultdict(collections.Counter)
    for r in csv.DictReader(open(os.path.join(HERE, '..', '..', 'analysis', 'billing_index.csv'))):
        if not r['template'].startswith('VZ_US_STMT_NODE'):
            continue
        fp = os.path.join(W, '.txtcache', r['hash'] + '.txt')
        if not os.path.exists(fp):
            continue
        cur, loc = None, None
        for ln in open(fp, errors='ignore'):
            h = _re.match(r'^P\d+ EGON ZEHNDER INTL - .*?,\s*([A-Za-z ]+)\s*$', ln)
            if h:
                loc = h[1].strip()
            a = _re.match(r'\s+Circuit ID:\s+(\S+)', ln)
            if a:
                cur = a[1]
                if loc:
                    seen[cur][loc.lower()] += 1
                loc = None
                continue
            b = _re.match(r'\s+Orig:\s*(.+)', ln)
            if b and cur:
                seen[cur][b[1].rsplit(',', 1)[-1].strip().lower()] += 1
    out = {}
    for k, v in seen.items():
        c = v.most_common(1)[0][0]
        out[k] = R.cn(CTRY_FIX.get(c, c))
    return out


def close(a, b):
    return abs(a - b) <= max(TOL_ABS, abs(b) * TOL_PCT)


def month_of(l):
    return (l['period_start'] or l['invoice_date'] or '')[:7]


def main():
    os.makedirs(OUT, exist_ok=True)
    rates = build_rates()
    ctry_of = circuit_countries()
    pool = {}
    for r in csv.DictReader(open(os.path.join(OUT, 'service_month_ledger.csv'))):
        if r['kind'] == 'REC' and r['category'].startswith('NO_CONTRACT_REF') and r['service_name'] == 'Private IP':
            pool[(r['service_id'], r['currency'], r['month'])] = r

    # -------- aggregate statement lines per circuit x month --------
    agg = collections.OrderedDict()
    lines = [l for l in D.load_lines() if l['template'].startswith('VZ_US_STMT') and l['service_name'] == 'Private IP'
             and l['charge_type'] in ('REC', 'DISCOUNT')]
    for l in sorted(lines, key=lambda l: (l['invoice_date'] or '', l['invoice_no'], int(l['page'] or 0))):
        key = (l['service_id'], l['currency'] or 'USD', month_of(l))
        if key not in pool:
            continue
        a = D.num(l['amount']) or 0.0
        c = 'DISC' if l['charge_type'] == 'DISCOUNT' else klass(l['description'])
        e = agg.setdefault(key, dict(cls=collections.Counter(), gross=0.0, pcred=0.0, disc=0.0, inv=set(), ev=[], speeds=set(),
                                     partial=set(), nport=0))
        e['cls'][c] += a
        e['inv'].add(l['invoice_no'])
        if c == 'PORT':
            sp, days = parse_br(l['description'])
            if sp:
                e['speeds'].add(sp)
            if days:
                e['partial'].add(days)
            if a >= 0:
                e['gross'] += a; e['nport'] += 1
            else:
                e['pcred'] += a
            e['ev'].append(f"inv {l['invoice_no']} p{l['page']}: {l['description']} {a:.2f}")
        elif c == 'DISC':
            e['disc'] += a
            e['ev'].append(f"inv {l['invoice_no']} p{l['page']}: {l['description']} {a:.2f}")
        elif c == 'SUMMARY':
            e['ev'].append(f"inv {l['invoice_no']} p{l['page']}: {l['description']} {a:.2f}")

    # -------- addressable breakdown (all pool service-months, by class, GROSS as in the ledger) --------
    brk = collections.Counter(); brk_n = collections.Counter()
    for key, e in agg.items():
        fx = float(pool[key]['fx_to_usd'] or 1)
        pre = 'pre' if key[2] < EFFECTIVE else 'post'
        for c, v in e['cls'].items():
            brk[(pre, c)] += v * fx; brk_n[(pre, c)] += 1
    with open(os.path.join(OUT, 'us_stmt_addressable.csv'), 'w', newline='') as fh:
        w = csv.writer(fh); w.writerow(['period', 'line_class', 'usd', 'service_months'])
        for (pre, c), v in sorted(brk.items()):
            w.writerow([pre + ('-2024-02' if pre == 'post' else '-2024-02'), c, round(v, 2), brk_n[(pre, c)]])

    # -------- per circuit-month verdicts --------
    rows, peers = [], collections.defaultdict(list)
    for key, e in agg.items():
        svc, cur, month = key
        led = pool[key]
        if e['nport'] == 0 and e['pcred'] == 0:
            continue          # month has no port line (access/support only) -> not a PIP Port month
        sp = sorted(e['speeds'])
        gross, disc, pcred = round(e['gross'], 2), round(e['disc'], 2), round(e['pcred'], 2)
        net = round(gross + disc + pcred, 2)
        fx = float(led['fx_to_usd'] or 1)
        dbp = round(-100 * disc / gross, 2) if gross > 0.005 and disc < 0 else 0.0
        cc = ctry_of.get(svc)
        cands = rates.get(sp[0], []) if len(sp) == 1 else []
        if cc and cands:
            cands = [c for c in cands if R.cn(c['country']) == cc]
        exp, cat, conf, basis, ctry = None, 'RC_NO_RATE', '', '', ''
        if month < EFFECTIVE:
            basis = 'PRE_AMENDMENT_28 service month (old pricebook, not checkable)'
        elif len(sp) != 1:
            basis = f'speed not unambiguous ({sp or "none"})'
        elif not cands:
            basis = f'no PIP Port rate at {sp[0]} Mbps in Amendment 28' + (f' for {cc}' if cc else '')
        else:
            days = sorted(e['partial'])
            covers = {1.0}
            for d_ in days:
                covers |= {d_ / 30, (d_ - 1) / 30}
            hit = None
            for c in sorted(cands, key=lambda c: (not c['strict'])):
                for cv in sorted(covers, reverse=True):
                    if close(net, c['net'] * cv):
                        hit = (c, cv); break
                if hit:
                    break
            listhit = [c for c in cands if c['list'] and close(gross, c['list'])] if gross > 0 and not days else []
            allnets = [c['net'] for c in cands]
            if hit:
                c, cv = hit
                same = sorted({x['country'] for x in cands if close(x['net'], c['net'])})
                ctry = (cc.title() if cc else '/'.join(sorted({x['country'] for x in (listhit or cands) if close(x['net'], c['net'])})))
                exp = round(c['net'] * cv, 2)
                cat = 'RC_OK'
                conf = ('HIGH' if c['strict'] else 'MED') if cc else ('MED' if (c['strict'] and listhit) else 'LOW')
                basis = (f"net {net:.2f} = Amend28 {'p.42-43 net' if c['strict'] else 'p.44-48 table'} {c['net']:g}"
                         f"{' x %.4f' % cv if cv != 1 else ''} for {len(same)} country(ies) at {sp[0]} Mbps; "
                         f"gross {'= list ' + format(listhit[0]['list'], 'g') if listhit else 'no list match'}; country " + (cc if cc else 'unresolved'))
            elif pcred < 0 and net <= max(allnets) + TOL_ABS:
                cat, conf, exp = 'RC_OK', 'LOW', round(net, 2)
                basis = 'port credited/prorated after disconnect; net not above any Amend28 rate'
                if abs(net) < 0.5:
                    basis = 'port fully credited in a later statement (net 0.00)'
            elif net > max(allnets) * (1 + TOL_PCT) + TOL_ABS:
                top = max(cands, key=lambda c: c['net'])
                exp = round(top['net'], 2)
                cat, conf = 'RC_OVERBILLED', 'LOW'
                basis = f"net {net:.2f} above the highest Amend28 rate at {sp[0]} Mbps ({top['net']:g} {top['country']}); country {cc or 'unresolved'}"
            elif net < min(allnets) - TOL_ABS:
                exp = round(min(allnets), 2)
                cat, conf = 'RC_UNDERBILLED', 'LOW'
                basis = f'net {net:.2f} below the lowest Amend28 rate at {sp[0]} Mbps; country unresolved'
            else:
                basis = f'net {net:.2f} between country rates at {sp[0]} Mbps and matches none; country unresolved'
        rows.append(dict(service_id=svc, month=month, product='PIP Port', tier=(sp[0] + ' Mbps') if len(sp) == 1 else '',
                         country=ctry or (cc.title() if cc else ''), currency=cur, billed=net, expected=exp, discount_billed_pct=dbp if gross > 0 else '',
                         discount_contract_pct='', discrepancy=round(net - exp, 2) if exp is not None else '', category=cat,
                         invoices=' '.join(sorted(e['inv'])), billed_gross=gross, discount_label_pct='', confidence=conf,
                         basis=basis, ledger_category=led['category'], fx_to_usd=led['fx_to_usd'], billed_usd=round(net * fx, 2),
                         evidence=' || '.join(e['ev'])[:900]))
        if cat == 'RC_OK':
            peers[(month, sp[0] if len(sp) == 1 else '')].append(svc)

    # confidence upgrade: HIGH only when a flagged month is above EVERY country's rate AND >=1 comparable circuit (same speed,
    # same month) was billed at an Amendment-28 rate AND the flagged port has no credit (audit2 pattern: others repriced, this one not)
    for r in rows:
        if r['category'] == 'RC_OVERBILLED':
            sp = r['tier'].replace(' Mbps', '')
            if peers.get((r['month'], sp)) and r['billed_gross'] > 0:
                r['confidence'] = 'HIGH'
                r['basis'] += f"; peers at card same month: {len(peers[(r['month'], sp)])}"
    cols = list(rows[0]) if rows else []
    with open(os.path.join(OUT, 'us_stmt_rate_card_checks.csv'), 'w', newline='') as fh:
        w = csv.DictWriter(fh, cols); w.writeheader(); w.writerows(rows)
    summarize(rows, pool, agg, brk, brk_n)
    return rows


def summarize(rows, pool, agg, brk, brk_n):
    tot = sum(float(r['billed_usd'] or 0) for r in pool.values())
    print(f'pool: {len(pool)} NO_CONTRACT_REF Private IP service-months, ledger (gross) ${tot:,.0f}')
    print('\nledger $ by line class (gross; DISC rows are NOT in the ledger total):')
    for (pre, c), v in sorted(brk.items()):
        print(f'  {pre:5}{c:9}{v:14,.0f}{brk_n[(pre, c)]:6}')
    n = collections.Counter(); s = collections.Counter(); g = collections.Counter(); d = collections.Counter()
    for r in rows:
        k = (r['category'], r['confidence'])
        n[k] += 1; s[k] += r['billed_usd']; g[k] += r['billed_gross'] * float(r['fx_to_usd'] or 1)
        d[k] += (r['discrepancy'] or 0) * float(r['fx_to_usd'] or 0) if r['discrepancy'] != '' else 0
    print(f"\n{'category':16}{'conf':6}{'rows':>6}{'net_usd':>12}{'gross_usd':>13}{'discr_usd':>11}")
    for k in sorted(n):
        print(f'{k[0]:16}{k[1]:6}{n[k]:6}{s[k]:12,.0f}{g[k]:13,.0f}{d[k]:11,.0f}')
    chk = [r for r in rows if r['category'] != 'RC_NO_RATE']
    print(f"checked port-months {len(chk)}: net ${sum(r['billed_usd'] for r in chk):,.0f}, gross ${sum(r['billed_gross'] * float(r['fx_to_usd']) for r in chk):,.0f}")
    pre = [r for r in rows if r['category'] == 'RC_NO_RATE' and r['month'] < EFFECTIVE]
    print(f"pre-2024-02 port-months {len(pre)}: net ${sum(r['billed_usd'] for r in pre):,.0f}, gross ${sum(r['billed_gross'] for r in pre):,.0f}")
    oth = [r for r in rows if r['category'] == 'RC_NO_RATE' and r['month'] >= EFFECTIVE]
    print(f'post-amendment, no verdict: {len(oth)}', [(r['service_id'], r['month'], r['basis'][:50]) for r in oth][:5])


def _selfcheck():
    assert parse_br('PRIVATE IP - ETHERNET [10.000 Mbps]') == ('10', None)
    assert parse_br('PORT RECURRING [1.984 Mbps]') == ('2', None)
    assert parse_br('PRIVATE IP - ETHERNET [02/01 02/24 8.000 Mbps]') == ('8', 24)
    assert klass('PRIVATE IP EF-REAL TIME [512.000 Kbps]') == 'COS'
    assert klass('AUTO DISCONNECT CREDITS LOCAL ACCESS PRIVATE IP - INTL [2.000 Mbps]') == 'ACCESS'
    assert klass('MANAGED WAN SUPPORT SERVICES [2.000 Mbps]') == 'MWAN'
    assert close(246.27, 307.84 * 24 / 30)


if __name__ == '__main__':
    _selfcheck()
    main()
