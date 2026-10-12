import re, json, csv
from pathlib import Path
APP = Path('D:/ERX-001/frappe-bench/apps/frappe_china/frappe_china')
merged = json.load(open('erx_merged.json', encoding='utf-8'))
rows = list(csv.reader(open(APP / 'translations/zh.csv', encoding='utf-8', newline='')))
csvk = {r[0] for r in rows}
han = re.compile('[\u4e00-\u9fff]')
keys = {}
ws = (APP / 'website_translation.py').read_text(encoding='utf-8')
m = re.search(r'SOURCES = \((.*?)\n\)', ws, re.S)
for k in re.findall(r'"([^"]*)"', m.group(1)):
    keys.setdefault(k, set()).add('website_translation.SOURCES')
js = (APP / 'public/js/independent_app_labels.js').read_text(encoding='utf-8')
for s in re.findall(r"new Set\(\[(.*?)\]\)", js):
    for k in re.findall(r"'([^']*)'", s):
        keys.setdefault(k, set()).add('independent_app_labels.js Set')
for k in ['{0}/{1} steps completed', '{0}/{1} steps', '{0}% completed', 'days']:
    keys.setdefault(k, set()).add('independent_app_labels.js key')
dp = (APP / 'public/js/desk_patches.js').read_text(encoding='utf-8')
for k in re.findall(r"""translate\(\s*["']([^"']+)["']""", dp):
    keys.setdefault(k, set()).add('desk_patches.js translate')
inst = (APP / 'install.py').read_text(encoding='utf-8')
pm = re.search(r'PROBE_SOURCE[^=]*=\s*["\'](.+?)["\']', inst)
if pm:
    keys.setdefault(pm.group(1), set()).add('install.PROBE_SOURCE')
for p in (APP / 'templates/independent_apps').glob('*.html'):
    t = p.read_text(encoding='utf-8')
    for k in re.findall(r"china_labels\[['\"]([^'\"]+)['\"]\]", t):
        keys.setdefault(k, set()).add(p.name)
res = []
for k, where in sorted(keys.items()):
    v = merged.get(k)
    res.append({'key': k, 'where': sorted(where), 'merged': v, 'has_han': bool(han.search(v or '')), 'in_csv': k in csvk})
json.dump(res, open('literal_keys.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
with open('literal_keys.txt', 'w', encoding='utf-8') as f:
    for r in res:
        f.write(f"{'OK ' if r['has_han'] else 'NO '}{'csv' if r['in_csv'] else 'off'} {r['key']!r} -> {r['merged']} {r['where']}\n")
