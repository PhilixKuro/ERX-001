# -*- coding: utf-8 -*-
import json, os, glob, io

BENCH = r'D:\ERX-001\frappe-bench\apps'

# 1) ToDo.owner : is it in fields[] at all?
p = os.path.join(BENCH, 'frappe', 'frappe', 'desk', 'doctype', 'todo', 'todo.json')
d = json.load(io.open(p, encoding='utf-8'))
fns = [f.get('fieldname') for f in d.get('fields', [])]
print('=== ToDo.json ===')
print('  fieldnames:', fns)
print('  owner in fields[]?', 'owner' in fns)
print('  field_order has owner?', 'owner' in (d.get('field_order') or []))

# 2) is_translatable filter
u = os.path.join(BENCH, 'frappe', 'frappe', 'gettext', 'extractors', 'utils.py')
txt = io.open(u, encoding='utf-8').read()
i = txt.find('def is_translatable')
print()
print('=== is_translatable ===')
print(txt[i:i + 700])

# 3) Custom Field label + how many custom fields zelin ships
cf = r'D:\ERX-001\Reference\zelin-tech-erpnext_china\erpnext_china\fixtures\custom_field.json'
recs = json.load(io.open(cf, encoding='utf-8'))
print()
print('=== zelin custom_field.json ===')
print('  records:', len(recs))
import collections
haszh = 0
for r in recs:
    lbl = r.get('label') or ''
    if any('\u4e00' <= ch <= '\u9fff' for ch in lbl):
        haszh += 1
print('  custom fields whose label contains CJK:', haszh)
print('  sample labels:', [r.get('label') for r in recs[:12]])
