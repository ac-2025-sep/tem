import sys; sys.path.insert(0,"/media/abhay/Workspace/Egon Zehnder/TEM/analysis/scripts")
from vz_load import *
from collections import Counter
h,r=load()["2025-04-01THRU2025-06-30"]; _=0
d=load(); allr=[]
for k in ["2024-11-01THRU2024-11-30","2024-12-01THRU2024-12-31","2025-01-01THRU2025-01-31","2025-02-01THRU2025-02-28","2025-03-01THRU2025-03-31","2025-04-01THRU2025-06-30"]:
    h,r=d[k]; allr+=[dict(zip(h,x)) for x in r]
f=lambda x,c:float(x[c])
bad=[x for x in allr if abs(f(x,"Recurring Charges")+f(x,"Non - Recurring Charges")+f(x,"Discount Amount")+f(x,"Taxes and surcharges")-f(x,"Total Charges"))>0.011]
print(len(bad),Counter(x["Product Description"].startswith("One Time Credit") for x in bad))
print([ (x["Product Description"][:50],x["Recurring Charges"],x["Non - Recurring Charges"],x["Discount Amount"],x["Taxes and surcharges"],x["Total Charges"]) for x in bad if not x["Product Description"].startswith("One Time Credit")][:5])
print("credit rows: all rec/nrc/disc zero?",all(f(x,"Recurring Charges")==f(x,"Non - Recurring Charges")==f(x,"Discount Amount")==0 for x in allr if x["Product Description"].startswith("One Time Credit")))
print("non-ascii/KANJI rows",sum("KANJI" in x["Location Address"] for x in allr))
