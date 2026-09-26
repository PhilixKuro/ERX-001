# -*- coding: utf-8 -*-
import json, os, sys, io, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
CD = os.path.join('D:', os.sep, 'ERX-001', 'Reference', 'zelin-tech-erpnext_china', 'erpnext_china',
                  'chart_of_accounts', 'custom_accounts', 'chart_of_accounts')
V16_ROOT = ['Asset', 'Liability', 'Income', 'Expense', 'Equity']
META = {'account_name','account_number','account_type','account_category','root_type',
        'is_group','tax_rate','account_currency'}

print('===== root_type values used by each CN chart vs v16 Account.root_type options =====')
print('  v16 options: %s   (NO "Common Accounts")' % V16_ROOT)
print('  zelin fixtures/property_setter.json ADDS "Common Accounts" to that Select.')
print()
for fn in sorted(os.listdir(CD)):
    if not fn.endswith('.json'): continue
    d = json.load(open(os.path.join(CD, fn), encoding='utf-8'))
    rts = collections.Counter()
    atypes = collections.Counter()
    def walk(n):
        for k, v in n.items():
            if k in META or not isinstance(v, dict): continue
            if v.get('root_type'): rts[v['root_type']] += 1
            if v.get('account_type'): atypes[v['account_type']] += 1
            walk(v)
    walk(d.get('tree', {}))
    bad = [r for r in rts if r not in V16_ROOT]
    print('  %-42s name=%s' % (fn, d.get('name')))
    print('       root_type used: %s' % dict(rts))
    print('       NOT in v16 options: %s  <== %s' % (bad, 'NEEDS the property_setter patch' if bad else 'ok'))
    print('       account_type values: %s' % dict(atypes))
    print()

print('===== does v16 have an "Account Category" doctype (account_category is a Link)? =====')
p = os.path.join('D:', os.sep, 'ERX-001', 'frappe-bench', 'apps', 'erpnext', 'erpnext', 'accounts',
                 'doctype', 'account_category')
print('  %s exists=%s' % (p, os.path.isdir(p)))
if os.path.isdir(p):
    print('  contents: %s' % sorted(os.listdir(p)))
