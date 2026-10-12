import csv, re, json
P = 'D:/ERX-001/frappe-bench/apps/frappe_china/frappe_china/translations/zh.csv'
raw = open(P, 'rb').read()
rows = list(csv.reader(open(P, encoding='utf-8', newline='')))
k = lambda r: (r[0].casefold(), r[2] if len(r) == 3 else '')
bad = [(i + 1, a[0][:40], b[0][:40]) for i, (a, b) in enumerate(zip(rows, rows[1:])) if k(a) > k(b)]
print('rows', len(rows), 'unsorted adjacent pairs', len(bad), bad[:5])
print('CRLF in file:', b'\r\n' in raw, ' BOM:', raw[:3] == b'\xef\xbb\xbf', ' ends with LF:', raw.endswith(b'\n'))
print('sorted(rows)==rows:', sorted(rows, key=k) == rows)
PH = re.compile(r"\{\{?\s*[^{}]+\s*\}?|\{\d+\}|%\([^)]*\)s|%s")
odd = [(r[0][:70], m) for r in rows for m in PH.findall(r[0]) if m.startswith('{') and not m.endswith('}')]
print('csv sources with unclosed-brace placeholder capture:', len(odd), odd[:5])
merged = json.load(open('erx_merged.json', encoding='utf-8'))
ns = "Naming series '{0}' for DocType '{1}' does not contain standard '.' or '{{' separator. Using fallback extraction."
print('merged value of Naming series key on erx:', repr(merged.get(ns)))
