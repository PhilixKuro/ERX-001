# -*- coding: utf-8 -*-
import sys, os, csv, io
sys.path.insert(0, r'D:/ERX-001/frappe-bench/env/lib/python3.14/site-packages')
from babel.messages.mofile import read_mo

ZH = r'D:/ERX-001/Reference/zelin-tech-erpnext_china/erpnext_china/translations/zh.csv'
MO = r'D:/ERX-001/frappe-bench/sites/assets/locale/zh/LC_MESSAGES'

rows = list(csv.reader(io.StringIO(open(ZH, encoding='utf-8').read())))
print('csv.reader rows:', len(rows))
# find the odd rows
for i, r in enumerate(rows):
    if len(r) < 2 or not r[0].strip():
        print(f'  ODD row #{i+1}: len={len(r)} repr={r!r}')

# keying WITHOUT the nonempty-key filter
k_all = {}
for r in rows:
    if len(r) >= 2:
        k_all.setdefault(r[0], r[1])
print('unique keys INCLUDING empty-string key:', len(k_all))
k_ne = {k: v for k, v in k_all.items() if k.strip()}
print('unique keys EXCLUDING empty/blank key :', len(k_ne))

mo = {}
for app in ('frappe', 'erpnext'):
    with open(os.path.join(MO, app + '.mo'), 'rb') as f:
        cat = read_mo(f)
    for m in cat:
        if not m.id: continue
        mid = m.id if isinstance(m.id, str) else m.id[0]
        s = m.string if isinstance(m.string, str) else (m.string[0] if m.string else '')
        if s: mo.setdefault(mid, s)

for label, src in (('INCLUDING empty key', k_all), ('EXCLUDING empty key', k_ne)):
    inter = set(src) & set(mo)
    diff = sum(1 for k in inter if mo[k].strip() != src[k].strip())
    print(f'[{label}] total={len(src)} overlap={len(inter)} differing={diff} gap={len(set(src)-set(mo))}')

# strict (no .strip()) comparison
inter = set(k_ne) & set(mo)
diff_strict = sum(1 for k in inter if mo[k] != k_ne[k])
print('strict (no strip) differing:', diff_strict)
