import csv, re, collections
rows = list(csv.reader(open('D:/ERX-001/frappe-bench/apps/frappe_china/frappe_china/translations/zh.csv', encoding='utf-8', newline='')))
c = collections.Counter()
ex = collections.defaultdict(list)
for r in rows:
    if re.search(r'(?i)naming series', r[0]):
        t = '编号模板' if '编号模板' in r[1] else '命名规则' if '命名规则' in r[1] else '编号规则' if '编号规则' in r[1] else 'other'
        c[t] += 1; ex[t].append((r[0][:70], r[1][:50]))
print(c)
for t, v in ex.items():
    print(t); [print('   ', x) for x in v[:6]]
