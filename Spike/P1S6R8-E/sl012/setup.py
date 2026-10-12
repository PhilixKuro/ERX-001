import csv, re, json
rows = list(csv.reader(open('D:/ERX-001/frappe-bench/apps/frappe_china/frappe_china/translations/zh.csv', encoding='utf-8', newline='')))
pop = json.load(open('population.json', encoding='utf-8'))
batch = {k for a, rs in pop.items() for k, _, _ in rs}
for r in rows:
    if re.fullmatch(r'[A-Za-z &]+ Setup', r[0]): print(r[0], '|', r[1], '| batch' if r[0] in batch else '| demo/other')
