# -*- coding: utf-8 -*-
import json, io, os
BASE = r'D:\ERX-001\Reference\zelin-tech-erpnext_china\erpnext_china\chart_of_accounts\custom_accounts\chart_of_accounts'
META = {'account_number','account_type','is_group','root_type','account_currency',
        'tax_rate','account_name','account_category','is_tax_withholding_account'}
def count(node):
    n = 0
    for k, v in node.items():
        if k in META or not isinstance(v, dict):
            continue
        n += 1 + count(v)
    return n
for fn in sorted(os.listdir(BASE)):
    if not fn.endswith('.json'):
        continue
    d = json.load(io.open(os.path.join(BASE, fn), encoding='utf-8'))
    tree = d.get('tree', {})
    print('%-42s name=%-24s accounts=%d' % (fn, d.get('name',''), count(tree)))
