# -*- coding: utf-8 -*-
import sys, os, csv, io, json, collections
sys.path.insert(0, r'D:/ERX-001/frappe-bench/env/lib/python3.14/site-packages')
from babel.messages.mofile import read_mo

MO = r'D:/ERX-001/frappe-bench/sites/assets/locale/zh/LC_MESSAGES'
ZH = r'D:/ERX-001/Reference/zelin-tech-erpnext_china/erpnext_china/translations/zh.csv'

mo = {}
for app in ('frappe', 'erpnext'):
    p = os.path.join(MO, app + '.mo')
    with open(p, 'rb') as f:
        cat = read_mo(f)
    d = {}
    for m in cat:
        if not m.id: continue
        mid = m.id if isinstance(m.id, str) else m.id[0]
        s = m.string if isinstance(m.string, str) else (m.string[0] if m.string else '')
        if s: d[mid] = s
    print(f'{app}.mo translated entries: {len(d)}')
    mo[app] = d
allmo = set(mo['frappe']) | set(mo['erpnext'])
print('runtime zh .mo universe (translated only):', len(allmo))

rows = list(csv.reader(io.StringIO(open(ZH, encoding='utf-8').read())))
zelin = {}
for r in rows:
    if len(r) >= 2 and r[0].strip():
        zelin.setdefault(r[0], r[1])
zk = set(zelin)
inter = zk & allmo
same = diff = 0
for k in inter:
    off = mo['frappe'].get(k) or mo['erpnext'].get(k) or ''
    if off.strip() == zelin[k].strip(): same += 1
    else: diff += 1
print()
print('zelin unique:', len(zk))
print('overlap with runtime .mo:', len(inter), ' | identical:', same, ' | DIFFERENT:', diff)
print('zelin strings with NO runtime zh translation at all:', len(zk - allmo))
print('=> genuinely additive (fills a gap):', len(zk - allmo))
print('=> conflicting (official已有但译法不同):', diff)

print()
print('=== property_setter.json duplicate names ===')
P = r'D:/ERX-001/Reference/zelin-tech-erpnext_china/erpnext_china/fixtures/property_setter.json'
d = json.load(open(P, encoding='utf-8'))
c = collections.Counter(x.get('name') for x in d)
dups = {k: v for k, v in c.items() if v > 1}
print('total docs:', len(d), '| unique names:', len(c), '| duplicated names:', dups)

print()
print('=== cash_flow_code.json / custom_field.json duplicate names ===')
for fn in ('cash_flow_code.json', 'custom_field.json'):
    p = os.path.join(os.path.dirname(P), fn)
    dd = json.load(open(p, encoding='utf-8'))
    cc = collections.Counter(x.get('name') for x in dd)
    print(f'  {fn}: {len(dd)} docs, {len(cc)} unique names, dups={ {k:v for k,v in cc.items() if v>1} }')
