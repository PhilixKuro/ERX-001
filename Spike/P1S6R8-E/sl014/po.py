import os,re,csv,sys
apps=r'D:\ERX-001\frappe-bench\apps'
keys=["Item To Manufacture","Operation","Customer Name","Territory","Lead Owner","Deal Owner","Industry","Source","Purchase Receipt","Journal Entry","Empty","Select","of","Add","Click to sort by {0}","{0} Filter Applied","Filter Applied","Filters Applied","Expected Deal Value","Organization","Website","First Name","Salutation","Next Step","Probability"]
found={k:[] for k in keys}
for app in ['frappe','erpnext','crm','hrms','insights','raven']:
    for root,ds,fs in os.walk(os.path.join(apps,app,app,'locale')):
        for f in fs:
            if f=='zh.po':
                txt=open(os.path.join(root,f),encoding='utf-8').read()
                for m in re.finditer(r'(?:msgctxt "(.*?)"\n)?msgid "(.*?)"\nmsgstr "(.*?)"',txt):
                    if m.group(2) in found and m.group(3): found[m.group(2)].append((app,m.group(1),m.group(3)))
c=os.path.join(apps,'frappe_china','frappe_china','translations','zh.csv')
for row in csv.reader(open(c,encoding='utf-8')):
    if row and row[0] in found: found[row[0]].append(('csv',row[2] if len(row)>2 else '',row[1]))
for k,v in found.items(): print(k,'=>',v[:6])
