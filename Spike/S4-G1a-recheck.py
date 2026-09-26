# -*- coding: utf-8 -*-
import os, sys, io, json, csv
from collections import Counter
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
BASE = os.path.join('D:', os.sep, 'ERX-001', 'Reference', 'zelin-tech-erpnext_china', 'erpnext_china')
CD   = os.path.join(BASE, 'chart_of_accounts', 'company_default')
CA   = os.path.join(BASE, 'chart_of_accounts', 'custom_accounts', 'chart_of_accounts')

META7 = ['account_name','account_number','account_type','root_type','is_group','tax_rate','account_currency']
META8 = META7 + ['account_category']

SME_KEY = '小企业会计准则(2024)'
N_SALES = '销项税额'
N_PURCH = '进项税额'
N_TAXPAY = '应交税费'
N_VAT = '应交增值税'

def load(p):
    with open(p, encoding='utf-8') as f:
        return json.load(f)

def flatten(tree, meta):
    out = []
    def walk(node, parent, root_type, depth):
        for k, v in node.items():
            if k in meta: continue
            if not isinstance(v, dict): continue
            rt = v.get('root_type') or root_type
            kids = [kk for kk in v.keys() if kk not in meta and isinstance(v[kk], dict)]
            ig = v.get('is_group', 1 if kids else 0)
            out.append(dict(name=k, num=str(v.get('account_number','') or '').strip(),
                            is_group=ig, root_type=rt, acct_type=v.get('account_type'),
                            depth=depth, parent=parent, nkids=len(kids),
                            has_cat=('account_category' in v)))
            walk(v, k, rt, depth+1)
    walk(tree, None, None, 0)
    return out

charts = {}
for fn in sorted(os.listdir(CA)):
    if fn.endswith('.json'):
        charts[fn] = load(os.path.join(CA, fn))

print('===== R1. chart files inventory =====')
for fn, d in charts.items():
    nodes = flatten(d.get('tree', {}), META8)
    print('  %-42s name=%-26s cc=%-6s disabled=%-5s nodes=%-4d leaves=%-4d groups=%-4d acct_cat_keys=%d'
          % (fn, d.get('name'), d.get('country_code'), d.get('disabled'),
             len(nodes), sum(1 for n in nodes if not n['is_group']),
             sum(1 for n in nodes if n['is_group']), sum(1 for n in nodes if n['has_cat'])))
    print('       top-level json keys: %s' % list(d.keys()))

SME_FN = 'cn_smes_chart_of_accounts2024.json'
sme = charts[SME_FN]
sme_nodes = flatten(sme['tree'], META8)

print()
print('===== R2. SME(2024) structure =====')
print('  total nodes = %d   (claim was 266)' % len(sme_nodes))
print('  root_type distribution:')
for rt, c in sorted(Counter(str(n['root_type']) for n in sme_nodes).items()):
    print('     %-12s %d' % (rt, c))
print('  nodes whose effective root_type is None: %d'
      % sum(1 for n in sme_nodes if n['root_type'] is None))
print('  max depth = %d' % max(n['depth'] for n in sme_nodes))

byname = {}
for n in sme_nodes: byname.setdefault(n['name'], []).append(n)
dups = {k: v for k, v in byname.items() if len(v) > 1}
print('  distinct names = %d ; names appearing more than once = %d' % (len(byname), len(dups)))
for nm, lst in sorted(dups.items()):
    print('     %-22s x%d : %s' % (nm, len(lst),
          [(n['num'], 'grp' if n['is_group'] else 'leaf', n['acct_type'], n['parent']) for n in lst]))
print('  --- same-name PARENT/CHILD pairs ---')
cnt = 0
for n in sme_nodes:
    if n['parent'] == n['name']:
        cnt += 1
        print('     child name=%-20s num=%-10s is_group=%s acct_type=%s' % (n['name'], n['num'], n['is_group'], n['acct_type']))
print('  same-name parent/child pair count = %d' % cnt)

leaf_names = {n['name'] for n in sme_nodes if not n['is_group']}
all_names  = {n['name'] for n in sme_nodes}
all_nums   = {n['num'] for n in sme_nodes if n['num']}
num2node   = {n['num']: n for n in sme_nodes if n['num']}
print('  numbered nodes = %d ; unique numbers = %d' % (sum(1 for n in sme_nodes if n['num']), len(all_nums)))

print()
print('===== R3. tax_template.json =====')
tt = load(os.path.join(CD, 'tax_template.json'))
print('  top keys: %s' % list(tt.keys()))
print('  tax_categories: %s' % tt.get('tax_categories'))
print('  chart_of_accounts keys: %s' % list(tt['chart_of_accounts'].keys()))
for k, b in tt['chart_of_accounts'].items():
    print('  -- [%s] sections=%s counts=%s' % (k, list(b.keys()), {s: len(v) for s, v in b.items()}))

blk = tt['chart_of_accounts'][SME_KEY]
for sect, items in blk.items():
    print('  ## %s (%d)' % (sect, len(items)))
    for i, it in enumerate(items):
        print('     [%d] title=%-18s tax_category=%-16s' % (i, it.get('title'), it.get('tax_category')))
        for t in it.get('taxes', []):
            ah = t.get('account_head', {}) or {}
            num = str(ah.get('account_number', '') or '')
            nm  = ah.get('account_name')
            nd  = num2node.get(num)
            verdict = 'NUM_OK' if num in all_nums else 'NUM_MISSING'
            print('         num=%-10s %-11s name=%-10s nameInChart=%-5s nameIsLeaf=%-5s rate=%s root_type=%s'
                  % (num, verdict, nm, nm in all_names, nm in leaf_names, t.get('rate'), ah.get('root_type')))

print('  --- VAT-related nodes in SME chart ---')
for n in sme_nodes:
    if n['name'] in (N_SALES, N_PURCH, N_TAXPAY, N_VAT):
        print('     %-12s num=%-10s is_group=%s root_type=%-10s acct_type=%-10s parent=%s'
              % (n['name'], n['num'], n['is_group'], n['root_type'], n['acct_type'], n['parent']))
print('  2221005 present=%s node=%s' % ('2221005' in all_nums, num2node.get('2221005')))
for bad in ('222105', '22210005'):
    print('  %-9s present=%s' % (bad, bad in all_nums))

print()
print('===== R4. default_accounts.csv =====')
rows = list(csv.reader(open(os.path.join(CD, 'default_accounts.csv'), encoding='utf-8')))
print('  raw rows = %d ; first row = %s' % (len(rows), rows[0]))
data = [r for r in rows if r and len(r) >= 2 and r[0].strip()]
print('  usable data rows = %d' % len(data))
miss_any, miss_leaf = [], []
for i, r in enumerate(data, 1):
    fld, acct = r[0].strip(), r[1].strip()
    if acct not in all_names: miss_any.append((i, fld, acct))
    if acct not in leaf_names: miss_leaf.append((i, fld, acct, acct in all_names))
print('  ABSENT from chart entirely : %d' % len(miss_any))
for i, f, a in miss_any: print('     line %-3d %-42s %s' % (i, f, a))
print('  NOT a leaf (is_group=0 filter in utils.py:25 makes these fail) : %d' % len(miss_leaf))
for i, f, a, ia in miss_leaf:
    print('     line %-3d %-42s %-22s existsAsGroup=%s' % (i, f, a, ia))
fields = {}
for r in data: fields.setdefault(r[0].strip(), []).append(r[1].strip())
unres = {f: c for f, c in fields.items() if not any(a in leaf_names for a in c)}
print('  distinct company fields = %d ; fields with NO resolvable leaf = %d' % (len(fields), len(unres)))
for f, c in unres.items(): print('     %-42s candidates=%s' % (f, c))
print('  --- fields with >1 resolvable candidate (dict comprehension => LAST wins) ---')
for f, c in fields.items():
    ok = [a for a in c if a in leaf_names]
    if len(ok) > 1: print('     %-42s resolvable=%s => WINNER=%s' % (f, ok, ok[-1]))

print()
print('===== R5. tax_rule.csv cross-check =====')
tr = list(csv.reader(open(os.path.join(CD, 'tax_rule.csv'), encoding='utf-8')))
print('  rows=%d header=%s' % (len(tr), tr[0]))
cats_decl = set(tt.get('tax_categories') or [])
used_tmpl = {r[7].strip() for r in tr[1:] if len(r) > 7 and r[7].strip()}
for coa_key, block in tt['chart_of_accounts'].items():
    ts = set()
    for sect, items in block.items():
        for it in items: ts.add(it.get('title'))
    print('  titles under [%s]: %s' % (coa_key, sorted(ts)))
    print('       tax_rule refs missing here: %s' % sorted(used_tmpl - ts))
print('  tax_rule referenced templates: %s' % sorted(used_tmpl))
cats_used = {r[0].strip() for r in tr[1:] if r and r[0].strip()}
print('  tax_category used by tax_rule: %s' % sorted(cats_used))
print('  used but NOT declared in tax_categories: %s' % sorted(cats_used - cats_decl))
print('  declared but never used by tax_rule: %s' % sorted(cats_decl - cats_used))
