import csv, io, os
base = r'D:\ERX-001\Reference\zelin-tech-erpnext_china\erpnext_china'
print('===== zelin locale/zh.po full content =====')
print(io.open(os.path.join(base,'locale','zh.po'), encoding='utf-8').read())
print('===== zelin zh.csv 3-column (context) rows =====')
for r in csv.reader(io.open(os.path.join(base,'translations','zh.csv'), encoding='utf-8', newline='')):
    if len(r) == 3 and r[2]:
        print('  src=%-34s tgt=%-16s ctx=%s' % (r[0], r[1], r[2]))
