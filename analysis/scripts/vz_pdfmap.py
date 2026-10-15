import sys,re,os,json; sys.path.insert(0,"/media/abhay/Workspace/Egon Zehnder/TEM/analysis/scripts")
from vz_load import *
from collections import Counter,defaultdict
S="/tmp/claude-1000/-media-abhay-Workspace-Egon-Zehnder-TEM/89559593-5640-49fd-89d5-ba41c22b9f71/scratchpad/"
paths=[l.strip() for l in open(S+"pdfs.txt")]
paths=[p for p in paths if "SOF" not in p and "Amendments" not in p and "Credit Notes" not in p]
d=load(); csvinv={}
for k,(h,r) in d.items():
    for x in r:
        csvinv.setdefault(x[3],set()).add(k)
csvset=set(csvinv)
byname={}
for p in paths: byname.setdefault(os.path.basename(p),p)
pat=Counter(); pdf={}
for n in byname:
    s=n[:-4]; parts=s.split("_")
    pat[re.sub(r"[0-9]","9",re.sub(r"[A-Z]+(?=[0-9])","A",s))[:45]]+=1
    hit=[t for t in parts if t in csvset]
    dt=re.findall(r"\d{4}-\d{2}-\d{2}",s)
    pdf[n]=(parts,hit,dt[0] if dt else None)
print(len(byname),"unique pdf names; with CSV invoice no. in name:",sum(1 for v in pdf.values() if v[1]))
print(pat.most_common(25))
# months: PDFs by date in name, only those matching csv
m=Counter(v[2][:7] for v in pdf.values() if v[2]); print("PDF by date month",sorted(m.items()))
mi=Counter(v[2][:7] for v in pdf.values() if v[2] and v[1]); print("matched",sorted(mi.items()))
# invoices in CSV not found in PDFs
found={h for v in pdf.values() for h in v[1]}
print("csv invoices",len(csvset),"found in pdf names",len(csvset&found),"missing",sorted(csvset-found))
json.dump({n:[v[0],v[1],v[2],byname[n]] for n,v in pdf.items()},open(S+"pdfmap.json","w"))
# a sample of 2-part-different patterns
for n in list(byname)[:0]: pass
print([n for n in byname if not n.startswith("vz_") ][:30])
