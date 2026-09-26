# -*- coding: utf-8 -*-
import json, os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
Z = os.path.join('D:', os.sep, 'ERX-001', 'Reference', 'zelin-tech-erpnext_china', 'erpnext_china')
CD = os.path.join(Z, 'chart_of_accounts', 'custom_accounts', 'chart_of_accounts')
META = {'account_name','account_number','account_type','account_category','root_type',
        'is_group','tax_rate','account_currency'}

def index(target):
    for fn in os.listdir(CD):
        if not fn.endswith('.json'): continue
        d = json.load(open(os.path.join(CD, fn), encoding='utf-8'))
        if d.get('name') != target: continue
        nums = set()
        def walk(n):
            for k, v in n.items():
                if k in META or not isinstance(v, dict): continue
                num = str(v.get('account_number', '')).strip()
                if num: nums.add(num)
                walk(v)
        walk(d.get('tree', {}))
        return nums
    return set()

n2024 = index('小企业会计准则(2024)')
nold = index('小企业会计准则')
print('===== chart account_number sets =====')
print('  小企业会计准则(2024): %d numbers' % len(n2024))
print('  小企业会计准则(旧)  : %d numbers' % len(nold))

def collect(path, fields):
    d = json.load(open(path, encoding='utf-8'))
    out = []
    for it in d['items']:
        for f in fields:
            v = it.get(f)
            if v:
                for tok in str(v).split(','):
                    tok = tok.strip().lstrip('-')
                    if tok:
                        out.append((it.get('idx'), f, tok))
    return out

for label, path, fields in [
    ('Balance Sheet Settings', os.path.join(Z, 'erpnext_china', 'doctype', 'balance_sheet_settings',
                                            'example_data.json'), ['lft_calc_sources', 'rgt_calc_sources']),
    ('P&L Settings', os.path.join(Z, 'erpnext_china', 'doctype', 'profit_and_loss_statement_settings',
                                  'example_data.json'), ['calc_sources']),
]:
    print()
    print('===== %s example_data.json =====' % label)
    # Closing Balance rows only carry account numbers; Calculate Rows carry row indices
    d = json.load(open(path, encoding='utf-8'))
    acct_refs, row_refs = [], 0
    for it in d['items']:
        for tf, sf in [('calc_type','calc_sources'), ('lft_calc_type','lft_calc_sources'),
                       ('rgt_calc_type','rgt_calc_sources')]:
            ct, cs = it.get(tf), it.get(sf)
            if not cs: continue
            if ct == 'Closing Balance':
                for tok in str(cs).split(','):
                    tok = tok.strip().lstrip('-')
                    if tok: acct_refs.append((it.get('idx'), sf, tok))
            elif ct == 'Calculate Rows':
                row_refs += 1
    print('  rows=%d  account refs (Closing Balance)=%d  Calculate-Rows cells=%d'
          % (len(d['items']), len(acct_refs), row_refs))
    miss24 = [r for r in acct_refs if r[2] not in n2024]
    missold = [r for r in acct_refs if r[2] not in nold]
    print('  refs NOT found in 小企业会计准则(2024): %d / %d' % (len(miss24), len(acct_refs)))
    print('  refs NOT found in 小企业会计准则(旧)  : %d / %d' % (len(missold), len(acct_refs)))
    if miss24:
        print('  --- missing against 2024 chart ---')
        for idx, f, tok in miss24:
            print('      idx=%-4s %-18s %s' % (idx, f, tok))
