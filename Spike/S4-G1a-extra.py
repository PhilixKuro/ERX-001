# -*- coding: utf-8 -*-
import os, sys, io, json, csv
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
BASE = os.path.join('D:', os.sep, 'ERX-001', 'Reference', 'zelin-tech-erpnext_china', 'erpnext_china')
CA   = os.path.join(BASE, 'chart_of_accounts', 'custom_accounts', 'chart_of_accounts')
CD   = os.path.join(BASE, 'chart_of_accounts', 'company_default')

META8 = ['account_name','account_number','account_type','root_type','is_group',
         'tax_rate','account_currency','account_category']

def load(p):
    with open(p, encoding='utf-8') as f: return json.load(f)

print('===== E1. do any chart json carry account_currency / tax_rate / account_category ? =====')
for fn in sorted(os.listdir(CA)):
    if not fn.endswith('.json'): continue
    raw = open(os.path.join(CA, fn), encoding='utf-8').read()
    d = json.loads(raw)
    print('  %-42s account_currency=%-3d tax_rate=%-3d account_category=%-3d is_group=%-4d account_type=%-4d'
          % (fn, raw.count('"account_currency"'), raw.count('"tax_rate"'),
             raw.count('"account_category"'), raw.count('"is_group"'), raw.count('"account_type"')))

print()
print('===== E2. item_group / warehouse account names referenced by utils.py vs each chart =====')
# names hardcoded in utils.py
REF = {
  'set_warehouse_account': ['库存商品', '在产品'],
  'item_group[小企业会计准则]': ['生产成本-基本生产成本', '生产成本-辅助生产成本', '主营业务成本'],
  'item_group[一般企业会计准则(2024)]': ['制造企业成本-直接材料', '销售商品成本'],
}
def flatten(tree):
    out = []
    def walk(node, parent, rt, depth):
        for k, v in node.items():
            if k in META8 or not isinstance(v, dict): continue
            r = v.get('root_type') or rt
            kids = [kk for kk in v if kk not in META8 and isinstance(v[kk], dict)]
            out.append(dict(name=k, num=str(v.get('account_number','') or ''),
                            is_group=v.get('is_group', 1 if kids else 0), parent=parent))
            walk(v, k, r, depth+1)
    walk(tree, None, None, 0)
    return out

charts = {}
for fn in sorted(os.listdir(CA)):
    if fn.endswith('.json'):
        d = load(os.path.join(CA, fn))
        charts[d['name']] = flatten(d['tree'])

for cname, nodes in charts.items():
    leaves = {n['name'] for n in nodes if not n['is_group']}
    allnm  = {n['name'] for n in nodes}
    print('  --- chart [%s] ---' % cname)
    for grp, names in REF.items():
        for nm in names:
            print('     %-38s %-24s leaf=%-5s anyNode=%s' % (grp, nm, nm in leaves, nm in allnm))

print()
print('===== E3. the KEY TRAP in set_item_group_account (utils.py:108-134) =====')
cfg_keys = ['小企业会计准则', '一般企业会计准则(2024)']
print('  chart_of_accounts_config has ONLY these keys: %s' % cfg_keys)
print('  utils.py:130-131 fallback: if chart_of_accounts not in config -> use 小企业会计准则')
for cname in charts:
    inc = cname in cfg_keys
    used = cname if inc else '小企业会计准则'
    print('     company chart=%-26s inConfig=%-5s -> config used=%s' % (cname, inc, used))
print()
print('  ==> for 小企业会计准则(2024) it falls back to the 小企业会计准则 (non-2024) mapping.')
print('      Are those account names present in the 2024 chart?')
sme2024 = charts['小企业会计准则(2024)']
leaves24 = {n['name'] for n in sme2024 if not n['is_group']}
all24    = {n['name'] for n in sme2024}
for nm in REF['item_group[小企业会计准则]']:
    print('        %-26s leafIn2024=%-5s anyNodeIn2024=%s' % (nm, nm in leaves24, nm in all24))

print()
print('===== E4. tax_template.json : compare the three COA blocks =====')
tt = load(os.path.join(CD, 'tax_template.json'))
blocks = tt['chart_of_accounts']
import hashlib
for k, b in blocks.items():
    s = json.dumps(b, ensure_ascii=False, sort_keys=True)
    print('  [%-22s] sha1=%s len=%d' % (k, hashlib.sha1(s.encode()).hexdigest()[:12], len(s)))
    for sect, items in b.items():
        heads = []
        for it in items:
            for t in it.get('taxes', []):
                ah = t.get('account_head', {}) or {}
                heads.append('%s/%s' % (ah.get('account_number'), ah.get('account_name')))
        print('       %-22s %s' % (sect, heads))
print()
print('  --- are 小企业会计准则 and 小企业会计准则(2024) blocks identical? ---')
a = json.dumps(blocks['小企业会计准则'], ensure_ascii=False, sort_keys=True)
c = json.dumps(blocks['小企业会计准则(2024)'], ensure_ascii=False, sort_keys=True)
print('     identical=%s' % (a == c))

print()
print('===== E5. one full tax template item verbatim (to see all fields from_detailed_data consumes) =====')
print(json.dumps(blocks['小企业会计准则(2024)']['sales_tax_templates'][0], ensure_ascii=False, indent=2))

print()
print('===== E6. UOM disable blast radius (install.py:69) =====')
print('  install.py:69 -> frappe.db.set_value("UOM", {"name": ("not in", uom_list)}, "enabled", 0)')
sys.path.insert(0, '')
src = open(os.path.join(BASE, 'setup', 'install.py'), encoding='utf-8').read()
import re
m = re.search(r'uom_list = \[(.*?)\]', src, re.S)
uoms = [x.strip().strip("'").strip('"') for x in m.group(1).split(',') if x.strip()]
print('  uom_list length = %d' % len(uoms))
print('  uom_list = %s' % uoms)
