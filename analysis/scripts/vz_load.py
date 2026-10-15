import glob,os
B="/media/abhay/Workspace/Egon Zehnder/TEM/"
def parse(p):
    # Verizon CSV has unescaped inner quotes in some descriptions -> split on '","' instead of csv module
    L=open(p,encoding='utf-8').read().splitlines()
    rows=[[c.strip() for c in l[1:-1].split('","')] for l in L if l.strip()]
    return rows[0],rows[1:]
def load():
    out={}
    for p in glob.glob(B+"extracted/Data Dump/Verizon Dump/Verizon Invoices/*/*.CSV"):
        k=os.path.basename(p)[len("ConsolidatedInvoiceReportFROM"):-4]+(" (1)" if "(1)" in p else "")
        out[k]=parse(p)
    return out
