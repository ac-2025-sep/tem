import sys; sys.path.insert(0,"/media/abhay/Workspace/Egon Zehnder/TEM/analysis/scripts")
from vz_load import *
from collections import Counter,defaultdict
d=load()
D={k:[dict(zip(h,x)) for x in r] for k,(h,r) in d.items()}
for k,r in sorted(D.items()): print(k,len(r),Counter(len(x) for x in d[k][1]),Counter(x["Currency"] for x in r))
m1,m2=D["2025-05-01THRU2025-05-31"],D["2025-05-01THRU2025-05-31 (1)"]
t=lambda r:tuple(r.values())
print("May identical rows multiset:",Counter(map(t,m1))==Counter(map(t,m2)))
a,b=Counter(map(t,m1)),Counter(map(t,m2)); print("only in A",sum((a-b).values()),"only B",sum((b-a).values()))
print("May order same:",[t(x) for x in m1]==[t(x) for x in m2])
# invoice sets
inv=lambda r:set(x["Invoice Number"] for x in r)
months=[k for k in D if "THRU" in k and not k.startswith("2025-04") and "(1)" not in k]
q=D["2025-04-01THRU2025-06-30"]
print("quarter bill dates",Counter(x["Bill Date"][:7] for x in q))
for k in sorted(months):
    mo=k[:7]; qs=[x for x in q if x["Bill Date"][:7]==mo]
    mr=D[k]
    print(k,"monthly rows",len(mr),"inv",len(inv(mr)),"| quarter rows same bill month",len(qs),"inv",len(inv(qs)),"inv overlap",len(inv(mr)&inv(qs)),
      "multiset equal",Counter(map(t,mr))==Counter(map(t,qs)))
    # compare per-invoice sums
    s=lambda r:{i:round(sum(float(x["Total Charges"]) for x in r if x["Invoice Number"]==i),2) for i in inv(r)}
    sm,sq=s(mr),s(qs); print("  invoices only monthly",sorted(set(sm)-set(sq))[:8],"only quarter",sorted(set(sq)-set(sm))[:8],"sum mismatches",[(i,sm[i],sq[i]) for i in set(sm)&set(sq) if sm[i]!=sq[i]][:5])
# months of bill date across all, union invoices
allr=[x for k,r in D.items() if k not in("2025-04-01THRU2025-06-30","2025-05-01THRU2025-05-31 (1)") for x in r]
print("Union invoices by bill month:",sorted(Counter(i for i in {(x["Invoice Number"],x["Bill Date"][:7]) for x in allr}.__iter__() and [b for a,b in {(x["Invoice Number"],x["Bill Date"][:7]) for x in allr}]).items()))
print("invoice numbers w/ >1 bill date:",[i for i,c in Counter(a for a,b in {(x["Invoice Number"],x["Bill Date"]) for x in allr}).items() if c>1])
# cols: invoice -> acct/corp/currency
print("invoice->acct many:",sum(1 for i,c in Counter(a for a,b in {(x["Invoice Number"],x["Billing Account Number"]) for x in allr}).items() if c>1))
print("corp->accts",{c:sorted({x["Billing Account Number"] for x in allr if x["Customer Group ID/Corp ID"]==c}) for c in {x["Customer Group ID/Corp ID"] for x in allr}})
# acct->currency, invoice prefixes
ac=defaultdict(set)
for x in allr: ac[x["Billing Account Number"]].add(x["Currency"])
print({a:sorted(c) for a,c in ac.items()})
print("inv prefix",Counter(x["Invoice Number"][:3] for x in {(x["Invoice Number"]):x for x in allr}.values()))
# totals check
bad=0;neg=0
for x in allr:
    f=lambda c:float(x[c]); s=f("Usage Charges")+f("Recurring Charges")+f("Non - Recurring Charges")+f("Discount Amount")+f("Taxes and surcharges")
    if abs(s-f("Total Charges"))>0.011: bad+=1; 
print("rows total != sum components:",bad,"of",len(allr))
print("neg totals",sum(float(x["Total Charges"])<0 for x in allr),"disc rows",sum(float(x["Discount Amount"])!=0 for x in allr),"tax rows",sum(float(x["Taxes and surcharges"])!=0 for x in allr),"usage nonzero",sum(float(x["Usage Charges"])!=0 for x in allr),"NRC rows",sum(float(x["Non - Recurring Charges"])!=0 for x in allr))
# granularity: dup keys
key=lambda x:(x["Invoice Number"],x["Location ID"],x["Charge Description (Service)"],x["Service ID"],x["Circuit ID"],x["Service Period"],x["Product Description"])
c=Counter(map(key,allr)); print("dup rows on full key",sum(v-1 for v in c.values() if v>1))
print("Service ID '-':",sum(x["Service ID"]=="-" for x in allr),"circuit blank",sum(x["Circuit ID"]=="" for x in allr))
print("loc ids",len({x["Location ID"] for x in allr}),"loc w/ >1 addr",sum(1 for l in {x["Location ID"] for x in allr} if len({x["Location Address"] for x in allr if x["Location ID"]==l})>1))
print("ChargeDesc prefixes",Counter(x["Charge Description (Service)"][:6] for x in allr))
print("Charge desc per invoice sample",Counter(x["Charge Description (Service)"] for x in allr if x["Invoice Number"]=="Z1215061").most_common(3))
