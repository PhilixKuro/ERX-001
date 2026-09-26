# -*- coding: utf-8 -*-
import sys, os, csv, io
sys.path.insert(0, r'D:/ERX-001/frappe-bench/env/lib/python3.14/site-packages')
try:
    from babel.messages.pofile import read_po
    print('babel read_po imported OK')
except Exception as e:
    print('babel import FAILED:', type(e).__name__, e); sys.exit(1)

BENCH = r'D:/ERX-001/frappe-bench/apps'
ZH = r'D:/ERX-001/Reference/zelin-tech-erpnext_china/erpnext_china/translations/zh.csv'

official = {}
for app in ('frappe', 'erpnext'):
    p = os.path.join(BENCH, app, app, 'locale', 'zh.po')
    with open(p, 'rb') as f:
        cat = read_po(f)
    d = {}
    for m in cat:
        if not m.id:
            continue
        mid = m.id if isinstance(m.id, str) else m.id[0]
        d[mid] = m.string if isinstance(m.string, str) else (m.string[0] if m.string else '')
    official[app] = d
    print(f'{app}/locale/zh.po unique msgid: {len(d)}, nonempty msgstr: {sum(1 for v in d.values() if v)}')

allof = set(official['frappe']) | set(official['erpnext'])
print('official zh universe:', len(allof))

rows = list(csv.reader(io.StringIO(open(ZH, encoding='utf-8').read())))
zelin = {}
for r in rows:
    if len(r) >= 2 and r[0].strip():
        zelin.setdefault(r[0], r[1])
zk = set(zelin)
print('zelin unique keys:', len(zk))
inter = zk & allof
print('OVERLAP (zelin key has an official zh entry):', len(inter))
print('zelin-only (official has NO such msgid):', len(zk - allof))
same = diff = 0
for k in inter:
    off = official['frappe'].get(k) or official['erpnext'].get(k) or ''
    if off.strip() == zelin[k].strip():
        same += 1
    else:
        diff += 1
print('  identical rendering:', same)
print('  DIFFERENT rendering:', diff)
print()
print('vocabulary-material candidates (zelin-only + differing) =',
      len(zk - allof), '+', diff, '=', len(zk - allof) + diff)
