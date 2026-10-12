import csv, json, re
from pathlib import Path
APP = Path('D:/ERX-001/frappe-bench/apps/frappe_china/frappe_china')
rows = list(csv.reader(open(APP / 'translations/zh.csv', encoding='utf-8', newline='')))
cur = {r[0]: r[1] for r in rows}
rs = list(csv.reader(open('D:/ERX-001/Spike/P1S6R7/prune_restore.csv', encoding='utf-8', newline='')))
print('restore rows', len(rs), 'present exact', sum(cur.get(r[0]) == r[1] for r in rs), [r[0] for r in rs if cur.get(r[0]) != r[1]])
# html templates and other files with _( not scanned by _app_source_strings (only py/js)
pat = re.compile(r"""(?<![A-Za-z_])_{1,2}\(\s*(["'])((?:\.|(?!\1).)*)\1""")
merged = json.load(open('erx_merged.json', encoding='utf-8'))
han = re.compile('[\u4e00-\u9fff]')
miss = []
for p in APP.rglob('*'):
    if p.suffix not in ('.html', '.vue', '.ts', '.jinja', '.md', '.txt') or 'tests' in p.parts or 'node_modules' in p.parts: continue
    t = p.read_text(encoding='utf-8', errors='replace')
    for m in pat.finditer(t):
        k = m.group(2)
        if not han.search(merged.get(k) or ''): miss.append((p.relative_to(APP).as_posix(), k, merged.get(k)))
print('non-py/js _() calls without Chinese:', len(miss)); [print('  ', x) for x in miss[:20]]
# json non-DocType files with label/title (workspace, workspace_sidebar, number_card, etc.)
jmiss = []
for p in APP.rglob('*.json'):
    if 'tests' in p.parts: continue
    try: d = json.loads(p.read_text(encoding='utf-8'))
    except Exception: continue
    def walk(o):
        if isinstance(o, dict):
            for kk, v in o.items():
                if kk in ('label', 'title', 'link_to_label', 'description') and isinstance(v, str) and v and not han.search(v):
                    yield v
                else:
                    yield from walk(v)
        elif isinstance(o, list):
            for x in o: yield from walk(x)
    for v in walk(d):
        if not han.search(merged.get(v) or ''): jmiss.append((p.relative_to(APP).as_posix(), v[:60]))
print('json label/title/description without Chinese in merged:', len(jmiss)); [print('  ', x) for x in sorted(set(jmiss))[:30]]
