# -*- coding: utf-8 -*-
import json, csv, os, sys, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
BASE = r'D:\ERX-001\Reference\zelin-tech-erpnext_china\erpnext_china'
COA_DIR = os.path.join(BASE, 'chart_of_accounts', 'custom_accounts', 'chart_of_accounts')
CD = os.path.join(BASE, 'chart_of_accounts', 'company_default')
SME = '\u5c0f\u4f01\u4e1a\u4f1a\u8ba1\u51c6\u5219(2024)'

def load(p):
    with open(p, 'r', encoding='utf-8') as f:
        return json.load(f)

# ---------- index every chart file: name -> (numbers set, names set) ----------
charts = {}
for fn in sorted(os.listdir(COA_DIR)):
    if not fn.endswith('.json'):
        continue
    d = load(os.path.join(COA_DIR, fn))
    nums, names, leaf_names = set(), set(), set()
    META = {'account_name','account_number','account_type','account_category',
            'root_type','is_group','tax_rate','account_currency'}
    def walk(node):
        for k, v in node.items():
            if k in META or not isinstance(v, dict):
                continue
            num = str(v.get('account_number','')).strip()
            if num:
                nums.add(num)
            names.add(k)
            if v.get('account_name'):
                names.add(v.get('account_name'))
            kids = [kk for kk in v if kk not in META and isinstance(v[kk], dict)]
            if not kids and not v.get('is_group'):
                leaf_names.add(k)
            walk(v)
    walk(d.get('tree', {}))
    charts[d.get('name')] = dict(file=fn, nums=nums, names=names, leaves=leaf_names,
                                 disabled=d.get('disabled'), country=d.get('country'))

print('===== CHART FILES =====')
for nm, c in charts.items():
    print('  name=%s | file=%s | country=%s | disabled=%s | accounts(num)=%d | names=%d'
          % (nm, c['file'], c['country'], c['disabled'], len(c['nums']), len(c['names'])))

sme = charts.get(SME)
print()
print('===== CLAIM 3: tax_template.json account numbers under SME key =====')
tt = load(os.path.join(CD, 'tax_template.json'))
print('  top-level keys: %s' % list(tt.keys()))
sme_block = tt.get(SME, {})
print('  SME block sections: %s' % list(sme_block.keys()))
def scan_accounts(obj, path, out):
    if isinstance(obj, dict):
        if 'account_number' in obj or 'account_name' in obj:
            out.append((path, str(obj.get('account_number','')).strip(), obj.get('account_name','')))
        for k, v in obj.items():
            scan_accounts(v, path + '/' + str(k), out)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            scan_accounts(v, path + '[%d]' % i, out)
refs = []
scan_accounts(sme_block, '', refs)
seen = set()
for path, num, name in refs:
    key = (num, name)
    if key in seen:
        continue
    seen.add(key)
    num_ok = (num in sme['nums']) if num else None
    name_ok = (name in sme['names']) if name else None
    verdict = 'NUM_MISSING' if (num and not num_ok) else 'ok'
    print('  %-58s num=%-12s numfound=%-5s name=%-14s namefound=%s  => %s'
          % (path[:58], num or '-', num_ok, name or '-', name_ok, verdict))

print()
print('===== CLAIM 4: default_accounts.csv rows vs SME chart =====')
with open(os.path.join(CD, 'default_accounts.csv'), 'r', encoding='utf-8') as f:
    rows = [r for r in csv.reader(f) if r and any(x.strip() for x in r)]
print('  total data rows: %d' % len(rows))
miss = []
for i, r in enumerate(rows, 1):
    field = r[0].strip()
    acct = r[1].strip() if len(r) > 1 else ''
    found_any = acct in sme['names']
    found_leaf = acct in sme['leaves']
    if not found_any:
        miss.append((i, field, acct))
    print('  %2d %-42s %-26s inChart=%-5s isLeaf=%s' % (i, field, acct, found_any, found_leaf))
print('  --> NOT FOUND in SME chart: %d rows' % len(miss))
for i, field, acct in miss:
    print('      line %d: %s -> %s' % (i, field, acct))

print()
print('===== tax_rule.csv =====')
with open(os.path.join(CD, 'tax_rule.csv'), 'r', encoding='utf-8') as f:
    for i, r in enumerate(csv.reader(f), 1):
        print('  %d %s' % (i, r))
