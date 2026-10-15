#!/usr/bin/env python3
"""Currency Exchange Rate Table for non-USD invoices (per drive_new/Currency Exchange Flow.txt).

Rule order per invoice:
  1. AMENDMENT / SOF  - a rate stated in a contract, SOF or amendment that covers the invoice's contract.
  2. INVOICE          - a rate printed on the invoice itself (document-date rate).
  3. LEGACY           - per-invoice conversion_rate from legacy/api-snapshot.json (invoice-date FX, same as fx_rates()).
  NONE                - no rate available (external FX API is blocked here, so these are flagged, not guessed).

rate_to_usd = USD per 1 unit of the invoice currency (same convention as the engine's fx_to_usd).

Writes:
  work/engine_out/fx_table.csv
  work/engine_out/fx_notes.md

Run:  python3 -I work/engine/fx_table.py
Stdlib only. Does not modify discrepancy.py, rate_card.py or findings.py.
"""
import collections
import csv
import datetime
import glob
import json
import os
import re
import statistics

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.normpath(os.path.join(HERE, '..', '..'))      # /home/user/ez
W = os.path.join(BASE, 'work')
OUT = os.path.join(W, 'engine_out')
FX_CODES = ('INR', 'GBP', 'EUR', 'JPY', 'CHF', 'HUF', 'BRL')

RATE_RE = re.compile(r'(?:fx rate|exchange rate|conversion rate|rate of exchange)\W{0,6}(?:of\s+)?(\d+(?:\.\d+)?)', re.I)
PRINT_RE = re.compile(r'(?:exchange rate|rate of exchange|conversion rate|fx rate)\W{0,20}(\d+\.\d{2,6})', re.I)
BOILERPLATE = re.compile(r'applied to the original', re.I)
ID_RE = re.compile(r'\b[A-Z]\d{5}-\d{2}\b|\b\d{6}\b')


def rel(p):
    return os.path.relpath(p, BASE)


def read_jsonl(path):
    for n, line in enumerate(open(path, encoding='utf-8', errors='replace'), 1):
        line = line.strip()
        if not line:
            continue
        try:
            yield n, json.loads(line)
        except ValueError:
            continue


# ---------------------------------------------------------------- invoices
def load_invoices():
    """invoice_no -> dict(date, currency, doc_kind, source_path, contract_refs, template). All currencies."""
    inv = {}
    for f in ('invoice_lines.csv', 'invoice_lines_other.csv'):
        for l in csv.DictReader(open(os.path.join(W, f), encoding='utf-8')):
            e = inv.setdefault(l['invoice_no'], dict(date=l['invoice_date'], currency=l['currency'], doc_kind=l['doc_kind'],
                                                     source_path=l['source_path'], contract_refs=set(), template=l['template']))
            if l['contract_ref']:
                e['contract_refs'].add(l['contract_ref'])
    return inv


def billing_paths():
    """source path -> (hash, doc_number)."""
    out = {}
    for r in csv.DictReader(open(os.path.join(BASE, 'analysis', 'billing_index.csv'), encoding='utf-8')):
        out[r['path']] = (r['hash'], r['doc_number'])
    return out


# ---------------------------------------------------------------- stated rates (SOF / amendment / contract)
def stated_rates():
    """-> list of dict(currency, rate (local per USD), ids, source_ref)."""
    found = []
    files = sorted(glob.glob(os.path.join(W, 'amend28_*.jsonl')) + glob.glob(os.path.join(W, 'sof_*.jsonl')) +
                   glob.glob(os.path.join(BASE, 'analysis', 'contracts_*.jsonl')))
    for path in files:
        for n, r in read_jsonl(path):
            blob = ' | '.join(str(v) for v in r.values() if isinstance(v, (str, int, float)))
            if isinstance(r.get('pricing_sample'), list):
                blob += ' | ' + ' | '.join(r['pricing_sample'])
            m = RATE_RE.search(blob)
            if not m:
                continue
            cur = None
            for pat in (r'invoice currency\W+([A-Z]{3})', r'to ([A-Z]{3}) invoice'):
                c = re.search(pat, blob)
                if c:
                    cur = c.group(1)
                    break
            if not cur and r.get('currency') in FX_CODES:
                cur = r['currency']
            if cur not in FX_CODES:
                continue
            ids = {r.get(k) for k in ('contract_id', 'amendment_id') if r.get(k)}
            ids |= set(ID_RE.findall(str(r.get('text', '')) + ' ' + ' '.join(r.get('pricing_sample') or [])))
            tag = 'AMENDMENT' if r.get('amendment_id') or 'amend' in os.path.basename(path) else 'SOF'
            ref = f"{r.get('amendment_id') or r.get('contract_id') or '?'} p{r.get('page', '?')} {rel(path)}:{n}"
            found.append(dict(currency=cur, rate=float(m.group(1)), ids=ids, source=tag, source_ref=ref,
                              text=blob[:200]))
    return found


def apply_stated(inv_no, info, stated):
    """Return (rate_to_usd, source, ref) if a stated rate covers this invoice, else None."""
    hits = [s for s in stated if s['currency'] == info['currency'] and (info['contract_refs'] & s['ids'])]
    if not hits:
        return None
    if len({round(h['rate'], 6) for h in hits}) > 1:
        # conflicting stated rates for the same currency and contract: do not guess, leave to lower rules
        return None
    h = hits[0]
    # stated rate is local-per-USD for INR-style quotes ("Fx Rate 83.235"); convert to USD per unit
    return 1.0 / h['rate'], h['source'], h['source_ref']


# ---------------------------------------------------------------- invoice-printed rates
def printed_rate(text, currency):
    """Rate printed on the invoice, as USD per unit of currency, or None. Boilerplate lines are ignored."""
    for line in text.splitlines():
        if BOILERPLATE.search(line):
            continue
        m = PRINT_RE.search(line)
        if not m:
            continue
        v = float(m.group(1))
        if currency == 'INR' and 50 < v < 120:
            return 1.0 / v
        if currency == 'GBP':
            if 0.5 < v < 1.0:
                return 1.0 / v
            if 1.0 < v < 2.0:
                return v
    return None


def printed_rates(inv, bpaths):
    out = {}
    for no, info in inv.items():
        if info['currency'] == 'USD':
            continue
        bp = bpaths.get(info['source_path'])
        if not bp:
            continue
        f = os.path.join(W, '.txtcache', bp[0] + '.txt')
        if not os.path.exists(f):
            continue
        rate = printed_rate(open(f, encoding='utf-8', errors='replace').read(), info['currency'])
        if rate:
            out[no] = (rate, rel(f))
    return out


# ---------------------------------------------------------------- legacy per-invoice rates
def legacy_rates():
    snap = json.load(open(os.path.join(BASE, 'legacy', 'api-snapshot.json'), encoding='utf-8'))
    out = {}
    for i in snap['invoices_verizon']['body']['data']:
        if i.get('conversion_rate') and i.get('invoice_id'):
            out[i['invoice_id']] = float(i['conversion_rate'])
    return out


# ---------------------------------------------------------------- ECB historical reference rates (step 3 API source)
ECB_PATH = os.path.join(W, 'fx', 'eurofxref-hist.csv')


def load_ecb():
    """date -> {currency: units per 1 EUR}; USD column is USD per 1 EUR. Missing or N/A values are dropped."""
    if not os.path.exists(ECB_PATH):
        return {}
    out = {}
    for r in csv.DictReader(open(ECB_PATH, encoding='utf-8')):
        vals = {}
        for c in FX_CODES + ('USD',):
            v = (r.get(c) or '').strip()
            if v and v != 'N/A':
                vals[c] = float(v)
        out[r['Date']] = vals
    return out


def ecb_usd_per_unit(ecb, cur, date):
    """USD per 1 unit of cur on date, or on the latest prior ECB business day (weekends/holidays)."""
    if cur == 'EUR' or cur not in FX_CODES:
        return None
    day = datetime.date.fromisoformat(date)
    for back in range(0, 15):
        d = (day - datetime.timedelta(days=back)).isoformat()
        vals = ecb.get(d)
        if vals and cur in vals and 'USD' in vals:
            return vals['USD'] / vals[cur], d
    return None


# ---------------------------------------------------------------- build table
def build():
    inv = load_invoices()
    bpaths = billing_paths()
    stated = stated_rates()
    printed = printed_rates(inv, bpaths)
    legacy = legacy_rates()
    ecb = load_ecb()

    table = {}
    for no, info in sorted(inv.items(), key=lambda kv: (kv[1]['date'], kv[0])):
        if info['currency'] == 'USD':
            continue
        ecb_hit = ecb_usd_per_unit(ecb, info['currency'], info['date'])
        common = dict(date=info['date'], currency=info['currency'], invoice_no=no, doc_kind=info['doc_kind'],
                      legacy=legacy.get(no), printed=printed.get(no, (None,))[0],
                      ecb=ecb_hit[0] if ecb_hit else None)
        s = apply_stated(no, info, stated)
        if s:
            table[no] = dict(common, rate=s[0], source=s[1], ref=s[2])
            continue
        if no in printed:
            table[no] = dict(common, rate=printed[no][0], source='INVOICE', ref=f"{no} {printed[no][1]}")
            continue
        if ecb_hit:
            rate, used = ecb_hit
            usd, cur_u = ecb[used]['USD'], ecb[used][info['currency']]
            ref = (f"{no} ECB eurofxref-hist {used} ({info['currency']}->USD = USD {usd}/{info['currency']} {cur_u})"
                   + ('' if used == info['date'] else f"; invoice date {info['date']} not an ECB day"))
            table[no] = dict(common, rate=rate, source='API_ECB', ref=ref)
            continue
        if no in legacy:
            table[no] = dict(common, rate=legacy[no], source='LEGACY',
                             ref=f"{no} legacy/api-snapshot.json conversion_rate (no ECB rate)")
            continue
        table[no] = dict(common, rate=None, source='NONE', ref=f"{no} no stated, printed, ECB or legacy rate")
    return inv, table, stated, printed, legacy


def write_table(table):
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, 'fx_table.csv')
    with open(path, 'w', newline='', encoding='utf-8') as fh:
        w = csv.writer(fh)
        w.writerow(['date', 'currency', 'rate_to_usd', 'source', 'source_ref', 'invoice_no'])
        for e in sorted(table.values(), key=lambda e: (e['date'], e['currency'], e['invoice_no'])):
            w.writerow([e['date'], e['currency'],
                        '' if e['rate'] is None else f"{e['rate']:.10f}", e['source'], e['ref'], e['invoice_no']])
    return path


# ---------------------------------------------------------------- comparisons and findings impact
def pct(a, b):
    return (a - b) / b * 100.0


def compare(table):
    printed_vs = [(e['printed'], e['legacy'], e['invoice_no']) for e in table.values() if e['printed'] and e['legacy']]
    amend_vs = [(e['rate'], e['legacy'], e['invoice_no'], e['ref'])
                for e in table.values() if e['source'] in ('AMENDMENT', 'SOF') and e['legacy']]
    ecb_vs = [(e['ecb'], e['legacy'], e['invoice_no']) for e in table.values() if e['ecb'] and e['legacy']]
    return printed_vs, amend_vs, ecb_vs


def findings_impact(table, inv):
    fl = list(csv.DictReader(open(os.path.join(OUT, 'findings.csv'), encoding='utf-8')))
    nonusd = [r for r in fl if r['currency'] != 'USD']
    anchor_ok = anchor_bad = 0
    changed = []
    unresolved_rows = 0
    no_fx_rows = []
    billed_delta = 0.0
    billed_rows = 0
    for r in nonusd:
        ids = [x for x in r['invoices'].split() if x in table]
        if not ids:
            unresolved_rows += 1
            continue
        # engine keys a ledger row to its first contributing invoice in (invoice_date, invoice_no) order
        anchor = min(ids, key=lambda x: (table[x]['date'], x))
        e = table[anchor]
        old_fx = float(r['fx_to_usd']) if r['fx_to_usd'] else None
        if e['legacy'] is not None and old_fx is not None and abs(e['legacy'] - old_fx) < 1e-9:
            anchor_ok += 1
        else:
            anchor_bad += 1
        if e['rate'] is None or old_fx is None:
            if e['rate'] is None:
                no_fx_rows.append(r)
            continue
        if e['source'] == 'LEGACY':
            continue
        if r['billed']:
            billed_delta += float(r['billed']) * (e['rate'] - old_fx)
            billed_rows += 1
        if not r['discrepancy'] or not r['discrepancy_usd']:
            continue
        disc = float(r['discrepancy'])
        old_usd = float(r['discrepancy_usd'])
        new_usd = round(disc * e['rate'], 2)
        if abs(new_usd - old_usd) > 0.005:
            changed.append(dict(kind=r['kind'], service_id=r['service_id'], month=r['month'], currency=r['currency'],
                                anchor=anchor, source=e['source'], old_fx=old_fx, new_fx=e['rate'],
                                discrepancy=disc, old_usd=old_usd, new_usd=new_usd, delta=new_usd - old_usd))
    total_old = sum(float(r['discrepancy_usd']) for r in fl if r['discrepancy_usd'] and r['discrepancy'])
    return dict(rows=len(fl), nonusd_rows=len(nonusd), anchor_match=anchor_ok, anchor_mismatch=anchor_bad,
                unresolved=unresolved_rows, changed=changed, total_old=total_old, no_fx_rows=no_fx_rows,
                billed_delta=billed_delta, billed_rows=billed_rows)


def write_notes(inv, table, stated, printed, legacy, printed_vs, amend_vs, ecb_vs, impact):
    L = []
    add = L.append
    add('# FX notes: Currency Exchange Rate Table (non-USD invoices)')
    add('')
    add('Generated by `work/engine/fx_table.py` (stdlib only). Table: `work/engine_out/fx_table.csv`.')
    add('Convention: `rate_to_usd` = USD per 1 unit of the invoice currency (same as the engine `fx_to_usd`).')
    add('Priority per `drive_new/Currency Exchange Flow.txt`: (1) AMENDMENT/SOF stated rate, (2) INVOICE printed rate, (3) API_ECB rate on the invoice date (latest prior ECB business day if the date is not an ECB publication day), then LEGACY (legacy per-invoice conversion_rate) only if ECB has no rate, then NONE.')
    add('ECB source: `work/fx/eurofxref-hist.csv` (ECB euro reference rates, quoted per 1 EUR; X->USD = USD column / X column).')
    add('Legacy and printed rates are kept in the comparison sections below.')
    add('')
    add('## Stated rates found (contracts, SOF, amendments)')
    if not stated:
        add('None.')
    for s in stated:
        add(f"- {s['currency']} {s['rate']} (local per USD) on {sorted(s['ids'])}: {s['source_ref']}")
        add(f"  - text: `{s['text'][:160]}`")
    add('- Not used: BRL 5.0546 in `analysis/contracts_3.jsonl` (USD-to-BRL, contract 208686). No BRL invoices exist in the lines data.')
    add('- No stated GBP rate was found in any contract, SOF or amendment file.')
    add('- The INR rate table is dated "established 01 Jan 2024". The spec applies a stated amendment rate without a date window, so it is applied to all INR invoices under contract L51187-02 / 208686. Invoices dated before 2024 would be the first to question this.')
    add('')
    add('## Invoice-printed rates')
    add(f"- Non-USD invoices with a printed rate found in the cached text: {len(printed)}.")
    add('- The only FX-related text on invoices is boilerplate ("converted using the exchange rate applied to the original") and no invoice prints a local-to-USD rate or a USD equivalent total.')
    add('')
    add('## Coverage: non-USD invoices by currency and source')
    cnt = collections.Counter((e['currency'], e['source']) for e in table.values())
    cur_tot = collections.Counter(e['currency'] for e in table.values())
    srcs = ['AMENDMENT', 'SOF', 'INVOICE', 'API_ECB', 'LEGACY', 'NONE']
    add('| currency | total docs | ' + ' | '.join(srcs) + ' |')
    add('|---|---|' + '---|' * len(srcs))
    for c in sorted(cur_tot):
        add(f"| {c} | {cur_tot[c]} | " + ' | '.join(str(cnt.get((c, s), 0)) for s in srcs) + ' |')
    add(f"| all | {len(table)} | " + ' | '.join(str(sum(v for (c, s), v in cnt.items() if s == x)) for x in srcs) + ' |')
    kinds = collections.Counter(e['doc_kind'] for e in table.values())
    add('')
    add(f"Documents: {dict(kinds)} (credit notes included as non-USD documents).")
    add('')
    none = sorted([e for e in table.values() if e['source'] == 'NONE'], key=lambda e: (e['date'], e['invoice_no']))
    add(f"## No rate from any source ({len(none)})")
    for e in none:
        add(f"- {e['date']} {e['currency']} {e['invoice_no']}")
    if not none:
        add('None. Every non-USD invoice has a rate.')
    add('')
    add('## Comparison: invoice-printed vs legacy')
    if not printed_vs:
        add('- Count: 0. No invoice prints a rate, so no printed-vs-legacy comparison is possible.')
    else:
        d = [abs(pct(p, lg)) for p, lg, _ in printed_vs]
        add(f"- Count: {len(d)}; max abs % difference: {max(d):.4f}%")
    add('')
    add('## Comparison: ECB (API_ECB, invoice date) vs legacy')
    if not ecb_vs:
        add('- Count: 0.')
    else:
        dd = sorted(((abs(pct(e, lg)), no, e, lg) for e, lg, no in ecb_vs), reverse=True)
        add(f"- Count: {len(dd)}; max abs % difference: {dd[0][0]:.4f}% (invoice {dd[0][1]}: ECB {dd[0][2]:.10f} vs legacy {dd[0][3]:.10f}); median: {statistics.median(x for x, *_ in dd):.4f}%")
    add('')
    add('## Comparison: stated amendment rate vs legacy (the only stated-vs-legacy comparison available)')
    if not amend_vs:
        add('- Count: 0.')
    else:
        # table rate is already USD per unit (apply_stated inverts the stated local-per-USD quote)
        dd = [(abs(pct(r, lg)), no) for r, lg, no, _ in amend_vs]
        mx = max(dd)
        add(f"- Count: {len(dd)}; max abs % difference: {mx[0]:.4f}% (invoice {mx[1]}); median: {statistics.median(x for x, _ in dd):.4f}%")
        add(f"- Amendment rate 1/83.235 = {1/83.235:.10f} USD per INR, next to legacy values {min(l for _, l, _, _ in amend_vs):.10f} to {max(l for _, l, _, _ in amend_vs):.10f}.")
    add('')
    add('## USD impact on findings.csv discrepancy_usd if the table rates replaced legacy')
    add(f"- findings.csv rows: {impact['rows']}; non-USD rows: {impact['nonusd_rows']}.")
    add(f"- Engine anchor check (legacy rate of first contributing invoice = row fx_to_usd): match {impact['anchor_match']}, mismatch {impact['anchor_mismatch']}, rows with no matching invoice: {impact['unresolved']}.")
    ch = impact['changed']
    add(f"- Rows whose discrepancy_usd changes: {len(ch)}.")
    add(f"- Context, billed_usd (not discrepancy): {impact['billed_rows']} rows anchored to a non-legacy rate would change by {impact['billed_delta']:,.2f} USD in total.")
    add(f"- Findings rows with no FX rate at all (fx_to_usd blank, billed_usd and discrepancy_usd unavailable): {len(impact['no_fx_rows'])}; discrepancy values on them: {sorted({r['discrepancy'] for r in impact['no_fx_rows']})}.")
    if ch:
        net = sum(c['delta'] for c in ch)
        mx = max(ch, key=lambda c: abs(c['delta']))
        add(f"- Net change in discrepancy_usd: {net:,.2f} USD (total discrepancy_usd across all findings rows: {impact['total_old']:,.2f} USD before, {impact['total_old'] + net:,.2f} after).")
        add(f"- Largest single-row change: {mx['delta']:,.2f} USD ({mx['kind']} {mx['service_id']} {mx['month']}, anchor invoice {mx['anchor']}, legacy {mx['old_fx']:.6f} to table {mx['new_fx']:.10f}).")
        add(f"- Fx change per row: {min(c['new_fx']/c['old_fx']-1 for c in ch)*100:.4f}% to {max(c['new_fx']/c['old_fx']-1 for c in ch)*100:.4f}%.")
        add('- Rows whose anchor invoice is LEGACY-sourced are unchanged by construction. Changes come from ECB-anchored GBP and INR rows, and the rate differences are small (see the ECB comparison above).')
    else:
        add('- No change in discrepancy_usd.')
    add('')
    add('## Caveats')
    add('- findings.csv rows are not re-run. This is a what-if on discrepancy_usd only. claim_usd and final categories are not recomputed.')
    add('- Table dates are invoice (document) dates, as the spec requires. ECB rates come from the local copy in work/fx/, not a live API call.')
    add('- A rate applied from a stated amendment is not date-limited (see the 01 Jan 2024 note above).')
    path = os.path.join(OUT, 'fx_notes.md')
    open(path, 'w', encoding='utf-8').write('\n'.join(L) + '\n')
    return path


def main():
    inv, table, stated, printed, legacy = build()
    tpath = write_table(table)
    printed_vs, amend_vs, ecb_vs = compare(table)
    impact = findings_impact(table, inv)
    npath = write_notes(inv, table, stated, printed, legacy, printed_vs, amend_vs, ecb_vs, impact)
    cnt = collections.Counter(e['source'] for e in table.values())
    print('wrote', tpath, 'rows', len(table), dict(cnt))
    print('wrote', npath)
    print('discrepancy_usd rows changed', len(impact['changed']),
          'net', round(sum(c['delta'] for c in impact['changed']), 2))


if __name__ == '__main__':
    main()
