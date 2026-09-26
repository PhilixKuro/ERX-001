# -*- coding: utf-8 -*-
import json, io, os, sys

BASE = r'D:\ERX-001\Reference\zelin-tech-erpnext_china\erpnext_china\chart_of_accounts\custom_accounts\chart_of_accounts'
META = {'account_number','account_type','is_group','root_type','account_currency',
        'tax_rate','account_name','account_category','is_tax_withholding_account'}

def walk(node, path, out):
    for k, v in node.items():
        if k in META:
            continue
        if isinstance(v, dict):
            rt = v.get('root_type', '')
            out.append((path + [k], rt, v.get('is_group'), v.get('account_number'), v.get('account_type','')))
            walk(v, path + [k], out)

for fn in sorted(os.listdir(BASE)):
    if not fn.endswith('.json'):
        continue
    p = os.path.join(BASE, fn)
    d = json.load(io.open(p, encoding='utf-8'))
    rows = []
    for top, body in d.items():
        if isinstance(body, dict):
            rows.append(([top], body.get('root_type',''), body.get('is_group'), body.get('account_number'), body.get('account_type','')))
            walk(body, [top], rows)
    print('=' * 70)
    print('FILE:', fn, ' total nodes:', len(rows))
    # root_type value census
    cen = {}
    for path, rt, ig, an, at in rows:
        cen[rt] = cen.get(rt, 0) + 1
    print('  root_type census:', sorted(cen.items(), key=lambda x: -x[1]))
    # top level accounts (depth 1 and 2)
    print('  --- depth<=2 nodes (root_type / is_group / number / name) ---')
    for path, rt, ig, an, at in rows:
        if len(path) <= 2:
            print('    %-2d %-18s %-8s %s' % (len(path), repr(rt), an, ' / '.join(path)))
