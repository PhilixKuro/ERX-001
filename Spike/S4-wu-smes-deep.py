# -*- coding: utf-8 -*-
import json, io

P = r'D:\ERX-001\Reference\zelin-tech-erpnext_china\erpnext_china\chart_of_accounts\custom_accounts\chart_of_accounts\cn_smes_chart_of_accounts2024.json'
META = {'account_number','account_type','is_group','root_type','account_currency',
        'tax_rate','account_name','account_category','is_tax_withholding_account'}

rows = []
def walk(node, path):
    for k, v in node.items():
        if k in META or not isinstance(v, dict):
            continue
        rows.append((path + [k], v.get('root_type',''), v.get('is_group'), v.get('account_number')))
        walk(v, path + [k])

d = json.load(io.open(P, encoding='utf-8'))
for top, body in d.items():
    if isinstance(body, dict):
        rows.append(([top], body.get('root_type',''), body.get('is_group'), body.get('account_number')))
        walk(body, [top])

print('TOTAL NODES:', len(rows))
print()
print('### A. nodes with NON-EMPTY root_type at depth >= 3 (anomalies)')
for path, rt, ig, an in rows:
    if rt and len(path) >= 3:
        print('   depth=%d  root_type=%-12s num=%-8s  %s' % (len(path), rt, an, ' / '.join(path)))
print()
keys = [u'\u5171\u540c',          # 共同
        u'\u884d\u751f\u5de5\u5177', # 衍生工具
        u'\u5957\u671f',          # 套期
        u'\u88ab\u5957\u671f']    # 被套期
print('### B. search for hedging / common-class account names anywhere in SMEs chart')
hit = False
for path, rt, ig, an in rows:
    full = ' / '.join(path)
    for kw in keys:
        if kw in full:
            print('   HIT kw=%s  num=%s rt=%r  %s' % (kw, an, rt, full))
            hit = True
if not hit:
    print('   NO HIT for any of: 共同 / 衍生工具 / 套期 / 被套期')
print()
print('### C. raw substring scan of the file text')
txt = io.open(P, encoding='utf-8').read()
for kw in keys + [u'Common Accounts']:
    print('   %-14s -> count %d' % (kw, txt.count(kw)))
print()
print('### D. top-level (depth 2) root nodes with account_number, in file order')
for path, rt, ig, an in rows:
    if len(path) == 2:
        print('   num=%-6s root_type=%-10s %s' % (an, rt, path[-1]))
