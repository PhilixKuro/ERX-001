# -*- coding: utf-8 -*-
import json, os, sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
Z = os.path.join('D:', os.sep, 'ERX-001', 'Reference', 'zelin-tech-erpnext_china', 'erpnext_china')
E = os.path.join('D:', os.sep, 'ERX-001', 'frappe-bench', 'apps', 'erpnext', 'erpnext')

item = json.load(open(os.path.join(Z, 'erpnext_china', 'doctype', 'cash_flow_item',
                                  'cash_flow_item.json'), encoding='utf-8'))
have = {f['fieldname'] for f in item['fields']}
print('===== WRITE side: cash_flow.py get_cash_flow_items() selects these, then self.append(items, d) =====')
selected = ['gl_entry', 'posting_date', 'account', 'party_type', 'party', 'cost_center',
            'debit', 'credit', 'against', 'voucher_type', 'voucher_no', 'project', 'remarks']
print('  selected from GL Entry: %s' % selected)
print()
print('===== READ side: Cash Flow Item DocType declares %d fields =====' % len(have))
missing = [s for s in selected if s not in have]
print('  selected-but-NOT-declared on Cash Flow Item: %s' % (missing or 'none'))
if missing:
    print('  => those values are silently dropped by the child table (no such docfield).')
    print('     cash_flow.js / report display of %s would therefore be blank.' % missing)

print()
print('===== voucher_type Select coverage vs real GL Entry voucher types in v16 =====')
vt = [f for f in item['fields'] if f['fieldname'] == 'voucher_type'][0]
opts = [o for o in (vt.get('options') or '').split('\n') if o.strip()]
print('  Cash Flow Item.voucher_type Select options (%d): %s' % (len(opts), opts))
# gather voucher types that actually produce GL Entries in v16
gl_producers = set()
for root, dirs, files in os.walk(E):
    for fn in files:
        if fn.endswith('.py'):
            try:
                src = open(os.path.join(root, fn), encoding='utf-8').read()
            except Exception:
                continue
            if 'make_gl_entries' in src or 'get_gl_entries' in src:
                m = re.search(r'"voucher_type":\s*"([^"]+)"', src)
                if m: gl_producers.add(m.group(1))
print('  sample voucher_type literals found in erpnext GL code: %s' % sorted(gl_producers)[:14])
notcovered = sorted(v for v in gl_producers if v not in opts)
print('  GL-producing voucher types NOT in the Select: %s' % notcovered)
print('  NOTE: Select validation in frappe is a warning-level coercion for child rows appended in')
print('        python; treat the functional impact as UNVERIFIED (needs a live site to confirm).')
