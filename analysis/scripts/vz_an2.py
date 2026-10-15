import sys; sys.path.insert(0,"/media/abhay/Workspace/Egon Zehnder/TEM/analysis/scripts")
from vz_load import *
from collections import Counter,defaultdict
d=load(); allr=[]
for k in ["2024-11-01THRU2024-11-30","2024-12-01THRU2024-12-31","2025-01-01THRU2025-01-31","2025-02-01THRU2025-02-28","2025-03-01THRU2025-03-31","2025-04-01THRU2025-06-30"]:
    h,r=d[k]; allr+=[dict(zip(h,x),_f=k) for x in r]
f=lambda x,c:float(x[c])
bad=[x for x in allr if abs(f(x,"Usage Charges")+f(x,"Recurring Charges")+f(x,"Non - Recurring Charges")+f(x,"Discount Amount")+f(x,"Taxes and surcharges")-f(x,"Total Charges"))>0.011]
print(len(allr),len(bad))
# alt: total = rec+nrc+tax (discount informational?)
alt=[x for x in bad if abs(f(x,"Recurring Charges")+f(x,"Non - Recurring Charges")+f(x,"Taxes and surcharges")-f(x,"Total Charges"))>0.011]
print("still bad with discount excluded",len(alt))
for x in bad[:4]: print({c:x[c] for c in ["Invoice Number","Product Description","Recurring Charges","Non - Recurring Charges","Discount Amount","Taxes and surcharges","Total Charges"]})
for x in alt[:6]: print("ALT",{c:x[c] for c in ["Invoice Number","Product Description","Recurring Charges","Non - Recurring Charges","Discount Amount","Taxes and surcharges","Total Charges"]})
# discount rows examples
print([ {c:x[c] for c in ["Invoice Number","Product Description","Recurring Charges","Discount Amount","Total Charges"]} for x in allr if f(x,"Discount Amount")!=0][:3])
print("disc rows w/ rec=0",sum(1 for x in allr if f(x,"Discount Amount")!=0 and f(x,"Recurring Charges")==0))
# credits
print("P11 rows",Counter(x["Product Description"][:40] for x in allr if x["Charge Description (Service)"].startswith("P11")).most_common(8))
print("negative total non-P11 samples",[ (x["Product Description"][:60],x["Total Charges"]) for x in allr if f(x,"Total Charges")<0 and not x["Charge Description (Service)"].startswith("P11")][:4])
print("Product keywords",Counter(x["Product Description"].split(" - ")[0] for x in allr).most_common(15))
# loc address multi
for l in {x["Location ID"] for x in allr}:
    a={x["Location Address"] for x in allr if x["Location ID"]==l}
    if len(a)>1: print(l,a)
print("loc sample",Counter((x["Location ID"],x["Location Address"][:40]) for x in allr).most_common(12))
print("Loc id '1000000..'",Counter(x["Location ID"] for x in allr if x["Location ID"].startswith("1000000")))
# service id sample with circuit
print([ (x["Service ID"],x["Circuit ID"],x["Product Description"][:50],x["Location ID"]) for x in allr if x["Circuit ID"]][:5])
print("svc id only digits",Counter(("digits" if x["Service ID"].isdigit() else x["Service ID"][:2]) for x in allr))
# service-period variants
print("period forms",Counter(len(x["Service Period"]) for x in allr))
# Effective date
print("eff 0000",sum(x["Effective Date"]=="0000-00-00" for x in allr))
# Invoice totals per file for linkage
inv=defaultdict(float);cur={};acct={};dt={};rows=Counter();corp={}
for x in allr:
    i=x["Invoice Number"];inv[i]+=f(x,"Total Charges");cur[i]=x["Currency"];acct[i]=x["Billing Account Number"];dt[i]=x["Bill Date"];rows[i]+=1;corp[i]=x["Customer Group ID/Corp ID"]
import json;json.dump({i:[round(inv[i],2),cur[i],acct[i],dt[i],rows[i],corp[i]] for i in inv},open("/tmp/claude-1000/-media-abhay-Workspace-Egon-Zehnder-TEM/89559593-5640-49fd-89d5-ba41c22b9f71/scratchpad/inv.json","w"))
print(len(inv))
