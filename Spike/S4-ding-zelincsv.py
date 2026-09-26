import csv, os, io
base = r'D:\ERX-001\Reference\zelin-tech-erpnext_china\erpnext_china'
csvp = os.path.join(base,'translations','zh.csv')
pop  = os.path.join(base,'locale','zh.po')
news = ['Vihicle Maker','Phone Number','Completed By','Minutes','Tax Rate','Weightage',
        'Gross Margin','Manufacturing','Bank Account Name','Bank Account Type',
        'Bank Account Subtype','SELECT','Perm Level','Customer Part Number',
        'Delivery Warehouse','Role Profile','Closing Balance as per Bank Statement']
rows = list(csv.reader(io.open(csvp, encoding='utf-8', newline='')))
print('zh.csv total rows:', len(rows))
lens = {}
for r in rows: lens[len(r)] = lens.get(len(r),0)+1
print('row-length histogram:', lens)
d2 = {}
for r in rows:
    if len(r)>=2: d2.setdefault(r[0], []).append((r[1], r[2] if len(r)>=3 else None))
print()
print('--- are the 25 new labels present in zelin zh.csv? ---')
hit=miss=0
for n in news:
    v = d2.get(n)
    if v: hit+=1; print('  HIT  %-40s -> %s' % (n, v))
    else: miss+=1; print('  MISS %-40s' % n)
print('  hit=%d miss=%d' % (hit,miss))
print()
po = io.open(pop, encoding='utf-8').read() if os.path.exists(pop) else ''
print('zh.po exists:', os.path.exists(pop), 'bytes:', len(po))
print('--- new labels present as msgid in zh.po? ---')
for n in news:
    print('  %-40s %s' % (n, 'YES' if ('msgid "%s"' % n) in po else 'no'))
