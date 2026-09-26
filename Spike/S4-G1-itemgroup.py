# -*- coding: utf-8 -*-
import json, os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
CD = os.path.join('D:', os.sep, 'ERX-001', 'Reference', 'zelin-tech-erpnext_china', 'erpnext_china',
                  'chart_of_accounts', 'custom_accounts', 'chart_of_accounts')
META = {'account_name','account_number','account_type','account_category','root_type',
        'is_group','tax_rate','account_currency'}
CHOSEN = '小企业会计准则(2024)'

def index(name):
    for fn in os.listdir(CD):
        if not fn.endswith('.json'): continue
        d = json.load(open(os.path.join(CD, fn), encoding='utf-8'))
        if d.get('name') != name: continue
        leaves, allnames = set(), set()
        def walk(n):
            for k, v in n.items():
                if k in META or not isinstance(v, dict): continue
                allnames.add(k)
                kids = [kk for kk in v if kk not in META and isinstance(v[kk], dict)]
                if not kids and not v.get('is_group'): leaves.add(k)
                walk(v)
        walk(d.get('tree', {}))
        return leaves, allnames
    return set(), set()

print('===== utils.py set_item_group_account : dict is keyed by 准则 NAME =====')
print('  config keys present in code (utils.py:109 and :116):')
print('     "小企业会计准则"          <-- NOTE: no year suffix')
print('     "一般企业会计准则(2024)"')
print()
print('  chosen standard for this project: %s' % CHOSEN)
print('  is it a config key? -> %s' % (CHOSEN in ['小企业会计准则', '一般企业会计准则(2024)']))
print('  utils.py:130-131 therefore FALLS BACK to "小企业会计准则" and uses ITS account list.')
print()
fallback_accts = ['生产成本-基本生产成本', '生产成本-辅助生产成本', '主营业务成本']
leaves2024, all2024 = index(CHOSEN)
leavesOld, allOld = index('小企业会计准则')
print('  fallback list accounts, checked against the %s chart actually installed:' % CHOSEN)
for a in fallback_accts:
    print('     %-22s inChart=%-5s isLeaf(is_group=0)=%-5s' % (a, a in all2024, a in leaves2024))
print()
print('  same accounts against the OLD "小企业会计准则" chart (which the config was written for):')
for a in fallback_accts:
    print('     %-22s inChart=%-5s isLeaf=%-5s' % (a, a in allOld, a in leavesOld))
print()
print('  utils.py:138-146 filters Account by account_name IN list AND is_group=0,')
print('  so a name that is absent (or is a group) yields no account_id and the Item Group')
print('  default is simply never written.')
