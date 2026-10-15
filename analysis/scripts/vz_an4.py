import sys,json; sys.path.insert(0,"/media/abhay/Workspace/Egon Zehnder/TEM/analysis/scripts")
from vz_load import *
from collections import Counter,defaultdict
S="/tmp/claude-1000/-media-abhay-Workspace-Egon-Zehnder-TEM/89559593-5640-49fd-89d5-ba41c22b9f71/scratchpad/"
pm=json.load(open(S+"pdfmap.json")); d=load()
inv={}
for k,(h,r) in d.items():
    if k.endswith("(1)"):continue
    for x in r:
        x=dict(zip(h,x));i=x["Invoice Number"]
        e=inv.setdefault(i,dict(bd=x["Bill Date"],acct=x["Billing Account Number"],corp=x["Customer Group ID/Corp ID"],cur=x["Currency"],tot=0,n=0,files=set()))
        e["tot"]+=float(x["Total Charges"]);e["n"]+=1;e["files"].add(k)
for e in inv.values(): e["tot"]=round(e["tot"],2)
json.dump({k:{**v,"files":sorted(v["files"])} for k,v in inv.items()},open(S+"csvinv.json","w"))
# date diff and account/corp match
dd=Counter();ok=0
for n,(parts,hit,dt,p) in pm.items():
    if hit:
        i=hit[0];e=inv[i]; dd[(dt==e["bd"])]+=1
        ok+= (e["acct"] in parts and e["corp"] in parts)
print("date eq bill date",dd,"acct+corp in name",ok)
print("nonmatching dates sample",[(n,inv[v[1][0]]["bd"]) for n,v in pm.items() if v[1] and v[2]!=inv[v[1][0]]["bd"]][:6])
q=[i for i,e in inv.items() if e["bd"].startswith("2025-04")]; print("April CSV invoices",len(q),[ (i,i in {h for v in pm.values() for h in v[1]}) for i in q][:80:10], "pdfs found for April",sum(1 for i in q if any(i in v[1] for v in pm.values())))
# per-month: csv invoices vs pdf with date in month vs pdf matched
cm=Counter(e["bd"][:7] for e in inv.values())
print("csv inv per bill month",sorted(cm.items()))
# pdfs in same months NOT in CSV: by prefix/acct
cs=set(inv)
extra=[(n,v[2]) for n,v in pm.items() if v[2] and "2024-11"<=v[2][:7]<="2025-06" and not v[1]]
print("pdfs dated Nov24-Jun25 w/o csv invoice:",len(extra),extra[:12])
