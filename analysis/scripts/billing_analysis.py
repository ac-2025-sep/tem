import csv,re,collections,json
R='/media/abhay/Workspace/Egon Zehnder/TEM/'
rows=list(csv.DictReader(open(R+'analysis/billing_index.csv')))
# credit-note linkage
idx=collections.defaultdict(list)
for r in rows:
    if r['doc_kind']!='credit_note' and r['doc_number']: idx[r['doc_number']].append(r)
cn=[r for r in rows if r['doc_kind']=='credit_note']
res=[]
for r in cn:
    t=open(f"/tmp/claude-1000/txt/{r['hash']}.txt").read()
    orig=sorted(set(re.findall(r'Original Invoice:\s*(\S+)',t)))
    found=[o for o in orig if o in idx]
    # same account match?
    acc=[o for o in found if any(x['account_number']==r['account_number'] for x in idx[o])]
    res.append((r,orig,found,acc))
print('credit notes',len(cn),'with Original Invoice ref',sum(1 for x in res if x[1]),'all refs found in index',sum(1 for x in res if x[1] and len(x[2])==len(x[1])),'some found',sum(1 for x in res if x[2]),'no ref',sum(1 for x in res if not x[1]))
print('ref count dist',collections.Counter(len(x[1]) for x in res))
print('total distinct refs',len({o for x in res for o in x[1]}),'found',len({o for x in res for o in x[2]}))
miss=collections.Counter(o for x in res for o in x[1] if o not in idx)
print('missing sample',list(miss)[:15])
print('no-ref',[x[0]['path'][-60:] for x in res if not x[1]][:5])
# dup invoices
c=collections.Counter((r['doc_number']) for r in rows if r['doc_number'] and r['doc_kind']!='credit_note')
print('dup invoice numbers (diff hash)',[k for k,v in c.items() if v>1][:10])
# coverage
inv=[r for r in rows if r['doc_kind'] in('invoice','debit_note') and r['doc_date'] and r['template']!='NOT_BILLING_NTT_GUIDE']
months=sorted({r['doc_date'][:7] for r in inv})
print(months[0],months[-1])
acc=collections.defaultdict(set)
for r in inv: acc[(r['template'].split('_')[0]+' '+(r['account_number'] or r['customer_id'] or '?'))].add(r['doc_date'][:7])
allm=[]
y,m=map(int,months[0].split('-'))
while (y,m)<=tuple(map(int,months[-1].split('-'))):
    allm.append(f'{y}-{m:02d}'); m+=1
    if m>12:y+=1;m=1
json.dump(dict(allm=allm,acc={k:sorted(v) for k,v in acc.items()}),open('/tmp/claude-1000/cov.json','w'))
