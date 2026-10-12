import csv, re, importlib.util
R = 'D:/ERX-001/'
s = importlib.util.spec_from_file_location('bl', R + 'Spike/P1S6R4-baseline.py'); bl = importlib.util.module_from_spec(s); s.loader.exec_module(bl)
refs = {}
for app in bl.APPS[:-1]:
    for e in bl.parse_po(bl.app_path(app) / 'locale/main.pot'):
        refs.setdefault(e['id'], []).extend(e['refs'])
rows = list(csv.reader(open(R + 'frappe-bench/apps/frappe_china/frappe_china/translations/zh.csv', encoding='utf-8', newline='')))
ST = re.compile(r'repost_item_valuation|stock_reposting_settings')
with open('backscan2.txt', 'w', encoding='utf-8') as f:
    for r in rows:
        rf = refs.get(r[0], [])
        if re.search(r'(?i)repost', r[0]) and (any(ST.search(x) for x in rf) or not any('repost_accounting' in x or 'accounts_settings' in x for x in rf)):
            f.write(f"{r[0][:90]!r} | {r[1][:70]} | {rf[:3]}\n")
