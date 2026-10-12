import csv, json, re, importlib.util
R = 'D:/ERX-001/'
s = importlib.util.spec_from_file_location('bl', R + 'Spike/P1S6R4-baseline.py'); bl = importlib.util.module_from_spec(s); s.loader.exec_module(bl)
refs = {}
for app in bl.APPS[:-1]:
    for e in bl.parse_po(bl.app_path(app) / 'locale/main.pot'):
        refs.setdefault(e['id'], []).extend(e['refs'])
rows = list(csv.reader(open(R + 'frappe-bench/apps/frappe_china/frappe_china/translations/zh.csv', encoding='utf-8', newline='')))
cur = {r[0] + (':' + r[2] if len(r) == 3 and r[2] else ''): r[1] for r in rows}
bs = json.load(open(R + 'Spike/P1S6R7/sample_backscan.json', encoding='utf-8'))
out = {'backscan_in_csv': [], 'specific_in_csv': []}
for x in bs['backscan']:
    out['backscan_in_csv'].append({'key': x['key'], 'expected': x['new'], 'csv': cur.get(x['key']), 'ok': cur.get(x['key']) == x['new']})
for k, v in bs['specific'].items():
    out['specific_in_csv'].append({'key': k, 'expected': v, 'csv': cur.get(k), 'ok': cur.get(k) == v})
STOCKF = re.compile(r'repost_item_valuation|stock_reposting_settings|stock_ledger|stock_controller|stock/|serial_batch_bundle|item_valuation')
resid = []
for r in rows:
    if '重过账' in r[1] or '重新过账' in r[1]:
        rf = refs.get(r[0], [])
        resid.append({'key': r[0], 'zh': r[1], 'refs': rf[:4], 'stock_ref': any(STOCKF.search(x) for x in rf)})
out['csv_rows_with_重过账'] = resid
out['summary'] = {'backscan_ok': sum(x['ok'] for x in out['backscan_in_csv']), 'backscan_total': len(out['backscan_in_csv']),
                  'specific_ok': sum(x['ok'] for x in out['specific_in_csv']), 'csv_重过账_rows': len(resid),
                  'stock_ref_rows': sum(x['stock_ref'] for x in resid)}
json.dump(out, open('backscan_check.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(out['summary'])
with open('backscan_resid.txt', 'w', encoding='utf-8') as f:
    for x in resid: f.write(f"{'STOCK ' if x['stock_ref'] else '      '}{x['key'][:90]!r} | {x['zh'][:60]} | {x['refs']}\n")
