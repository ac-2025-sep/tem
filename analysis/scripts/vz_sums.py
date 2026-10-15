import sys; sys.path.insert(0,"/media/abhay/Workspace/Egon Zehnder/TEM/analysis/scripts")
from vz_load import *
d=load(); want=sys.argv[1:]
for k,(h,r) in d.items():
    if k.endswith("(1)") or k.startswith("2025-04"):continue
    for i in want:
        rows=[dict(zip(h,x)) for x in r if x[3]==i]
        if rows:
            s=lambda c:round(sum(float(x[c]) for x in rows),2)
            print(i,k,len(rows),{c:s(c) for c in ["Recurring Charges","Non - Recurring Charges","Discount Amount","Taxes and surcharges","Total Charges"]},"locs",len({x["Location ID"] for x in rows}))
