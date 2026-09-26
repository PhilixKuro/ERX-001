# -*- coding: utf-8 -*-
import json, os, io, csv, collections

BENCH = r'D:\ERX-001\frappe-bench\apps'
REF = r'D:\ERX-001\Reference'

# 1) cast() behaviour with fieldtype None
src = io.open(os.path.join(BENCH, 'frappe', 'frappe', 'utils', 'data.py'),
              encoding='utf-8').read()
i = src.find('def cast(')
print('=== frappe/utils/data.py  cast() ===')
print(src[i:i + 900])

# 2) Property Setter fixture: names + property_type null count
ps = os.path.join(REF, 'zelin-tech-erpnext_china', 'erpnext_china', 'fixtures',
                  'property_setter.json')
recs = json.load(io.open(ps, encoding='utf-8'))
lab = [r for r in recs if r.get('property') == 'label']
print()
print('=== label records: property_type values ===')
print(' ', collections.Counter(repr(r.get('property_type')) for r in lab))
print('=== sample names ===')
for r in lab[:5]:
    print('  name=%s' % r.get('name'))

# 3) saoxia comparison
sx = os.path.join(REF, 'saoxia-erpnext_china')
print()
print('=== saoxia-erpnext_china layout ===')
for sub in ('translations', 'locale', 'fixtures'):
    for root, dirs, files in os.walk(sx):
        if os.path.basename(root) == sub:
            print('  %s -> %s' % (root.replace(REF, '<REF>'), files))

# 4) does saoxia ship label property setters?
for root, dirs, files in os.walk(sx):
    if 'property_setter.json' in files:
        p = os.path.join(root, 'property_setter.json')
        rs = json.load(io.open(p, encoding='utf-8'))
        c = collections.Counter(r.get('property') for r in rs)
        print('  saoxia property_setter.json: %d recs; label=%d' % (len(rs), c.get('label', 0)))
        for r in rs:
            if r.get('property') == 'label':
                print('     %s.%s -> %s' % (r.get('doc_type'), r.get('field_name'), r.get('value')))

# 5) confirm official apps ship no csv
print()
print('=== official apps: csv vs po ===')
for app in ('frappe', 'erpnext'):
    cp = os.path.join(BENCH, app, app, 'translations')
    pp = os.path.join(BENCH, app, app, 'locale')
    print('  %-8s translations/ exists=%-5s  contents=%s' % (
        app, os.path.exists(cp), os.listdir(cp) if os.path.exists(cp) else '-'))
    print('  %-8s locale/       exists=%-5s  zh files=%s' % (
        app, os.path.exists(pp),
        [f for f in os.listdir(pp) if f.startswith('zh')] if os.path.exists(pp) else '-'))
