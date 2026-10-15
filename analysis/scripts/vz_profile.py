import sys; sys.path.insert(0,"/media/abhay/Workspace/Egon Zehnder/TEM/analysis/scripts")
from vz_load import *
from collections import Counter,defaultdict
d=load(); H=None
for k,(h,r) in sorted(d.items()):
    if H is None:H=h
    print(k,len(r),"hdr_same",h==H, "widths",Counter(len(x) for x in r))
h,_=d[sorted(d)[0]]
allr=[]
for k,(h,r) in sorted(d.items()):
    for x in r: allr.append((k,dict(zip(h,x))))
for c in h:
    vals=Counter(x[c] for _,x in allr)
    print("##",c,"distinct",len(vals),vals.most_common(4))
# per file
for k,(h,r) in sorted(d.items()):
    rr=[dict(zip(h,x)) for x in r]
    inv=Counter(x["Invoice Number"] for x in rr)
    print(k,"invoices",len(inv),"accts",sorted(set(x["Billing Account Number"] for x in rr)),"cur",Counter(x["Currency"] for x in rr),"billdates",sorted(set(x["Bill Date"] for x in rr)))
