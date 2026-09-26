# -*- coding: utf-8 -*-
import json, csv, os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
BASE = r'D:\ERX-001\Reference\zelin-tech-erpnext_china\erpnext_china'
COA_DIR = os.path.join(BASE, 'chart_of_accounts', 'custom_accounts', 'chart_of_accounts')
CD = os.path.join(BASE, 'chart_of_accounts', 'company_default')
SME = '\u5c0f\u4f01\u4e1a\u4f1a\u8ba1\u51c6\u5219(2024)'
META8 = {'account_name','account_number','account_type','account_category',
         'root_type','is_group','tax_rate','account_currency'}
META7 = META8 - {'account_category'}

def load(p):
    with open(p, 'r', encoding='utf-8') as f:
        return json.load(f)

print('===== CLAIM 1: does any chart JSON carry account_category? =====')
for fn in sorted(os.listdir(COA_DIR)):
    if not fn.endswith('.json'): continue
    raw = open(os.path.join(COA_DIR, fn), 'r', encoding='utf-8').read()
    d = json.loads(raw)
    cnt = raw.count('account_category')
    keys = set()
    def collect(n):
        for k, v in n.items():
            keys.add(k)
            if isinstance(v, dict): collect(v)
    collect(d.get('tree', {}))
    nonmeta7 = keys - META7
    print('  %-42s account_category occurrences=%d' % (fn, cnt))
    print('       top-level json keys: %s' % sorted(d.keys()))
    print('       keys NOT in zelin 7-key list (would be treated as child accts): sample %s'
          % sorted(list(nonmeta7))[:6])

print()
print('===== CLAIM 3 (corrected): tax_template.json structure =====')
tt = load(os.path.join(CD, 'tax_template.json'))
print('  top keys: %s' % list(tt.keys()))
coa_block = tt.get('chart_of_accounts', {})
print('  chart_of_accounts sub-keys (准则 names): %s' % list(coa_block.keys()))
print('  tax_categories: %s' % tt.get('tax_categories'))

# index SME chart
d = None
for fn in os.listdir(COA_DIR):
    if fn.endswith('.json'):
        c = load(os.path.join(COA_DIR, fn))
        if c.get('name') == SME:
            d = c
nums, names, leaves = set(), set(), set()
def walk(node):
    for k, v in node.items():
        if k in META8 or not isinstance(v, dict): continue
        n = str(v.get('account_number','')).strip()
        if n: nums.add(n)
        names.add(k)
        kids = [kk for kk in v if kk not in META8 and isinstance(v[kk], dict)]
        if not kids and not v.get('is_group'): leaves.add(k)
        walk(v)
walk(d.get('tree', {}))
print('  SME chart: %d numbered accounts, %d names, %d leaves' % (len(nums), len(names), len(leaves)))

sme_tax = coa_block.get(SME)
if sme_tax is None:
    print('  !! SME key absent under chart_of_accounts; keys are: %s' % list(coa_block.keys()))
else:
    out = []
    def scan(obj, path):
        if isinstance(obj, dict):
            if 'account_number' in obj or 'account_name' in obj:
                out.append((path, str(obj.get('account_number','')).strip(), obj.get('account_name','')))
            for k, v in obj.items(): scan(v, path + '/' + str(k))
        elif isinstance(obj, list):
            for i, v in enumerate(obj): scan(v, path + '[%d]' % i)
    scan(sme_tax, '')
    print('  account refs under SME: %d' % len(out))
    seen = set()
    for path, num, name in out:
        if (num, name) in seen: continue
        seen.add((num, name))
        nf = (num in nums) if num else None
        mf = (name in names) if name else None
        flag = 'NUM_NOT_IN_CHART' if (num and not nf) else 'ok'
        rescue = ''
        if num and not nf and name and mf:
            rescue = ' (OR-filter rescues via account_name)'
        print('    %-46s num=%-11s inChart=%-5s name=%-12s inChart=%-5s %s%s'
              % (path[-46:], num or '-', nf, name or '-', mf, flag, rescue))

print()
print('===== CLAIM 4 (refined): distinct company fields left UNSET =====')
rows = [r for r in csv.reader(open(os.path.join(CD,'default_accounts.csv'),'r',encoding='utf-8')) if r and any(x.strip() for x in r)]
# utils.py filters is_group=0 -> only leaves are matchable
from collections import OrderedDict
byfield = OrderedDict()
for r in rows:
    byfield.setdefault(r[0].strip(), []).append(r[1].strip())
unmatched_rows = [r for r in rows if r[1].strip() not in leaves]
print('  total rows=%d ; rows whose account is NOT a leaf in SME chart=%d' % (len(rows), len(unmatched_rows)))
print('  distinct company fields=%d' % len(byfield))
dead = []
for f, accts in byfield.items():
    hits = [a for a in accts if a in leaves]
    if not hits:
        dead.append((f, accts))
print('  fields with NO candidate resolvable (=> stay unset): %d' % len(dead))
for f, accts in dead:
    print('      %-40s candidates=%s' % (f, accts))
print('  --- rows not matching a leaf (detail) ---')
for r in unmatched_rows:
    inchart = r[1].strip() in names
    print('      %-40s %-24s inChartAtAll=%s (group or absent)' % (r[0].strip(), r[1].strip(), inchart))
