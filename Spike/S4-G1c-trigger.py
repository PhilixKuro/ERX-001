# -*- coding: utf-8 -*-
import os, json, re
CH = r'D:/ERX-001/frappe-bench/apps/erpnext/erpnext/accounts/doctype/account/chart_of_accounts'
ZC = r'D:/ERX-001/Reference/zelin-tech-erpnext_china/erpnext_china/chart_of_accounts/custom_accounts'

def count_key(obj, key):
    n = 0
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == key: n += 1
            n += count_key(v, key)
    return n

print('=== upstream verified/ + unverified/ charts containing account_category ===')
hits = []
for folder in ('verified', 'unverified'):
    d = os.path.join(CH, folder)
    if not os.path.isdir(d): continue
    for f in sorted(os.listdir(d)):
        if not f.endswith('.json'): continue
        try:
            j = json.load(open(os.path.join(d, f), encoding='utf-8'))
        except Exception as e:
            print('  parse fail', f, e); continue
        c = count_key(j.get('tree', {}), 'account_category')
        if c:
            hits.append((folder, f, j.get('name'), c))
for h in hits:
    print(f'  {h[0]}/{h[1]}  name={h[2]!r}  account_category nodes={h[3]}')
print('  total json charts with account_category:', len(hits))

print()
print('=== the python (Standard) charts ===')
for f in ('standard_chart_of_accounts.py', 'standard_chart_of_accounts_with_account_number.py'):
    p = os.path.join(CH, 'verified', f)
    txt = open(p, encoding='utf-8').read()
    print(f'  {f}: "account_category" occurrences = {txt.count("account_category")}')

print()
print('=== zelin china charts ===')
for sub in ('chart_of_accounts', 'custom_of_accounts'):
    d = os.path.join(ZC, sub)
    if not os.path.isdir(d):
        print(f'  {sub}/ : ABSENT'); continue
    for f in sorted(os.listdir(d)):
        if not f.endswith('.json'): continue
        j = json.load(open(os.path.join(d, f), encoding='utf-8'))
        c = count_key(j.get('tree', {}), 'account_category')
        print(f'  {sub}/{f}: name={j.get("name")!r} cc={j.get("country_code")!r} account_category nodes={c}')
