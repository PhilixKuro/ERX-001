# -*- coding: utf-8 -*-
import os, sys, io, json, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print('===== CLAIM 1 mechanism: 7-key list vs a chart carrying account_category =====')
# erpnext v16 in_standard_chart_of_accounts.json carries account_category and is pure JSON.
p = r'D:\ERX-001\frappe-bench\apps\erpnext\erpnext\accounts\doctype\account\chart_of_accounts\verified\in_standard_chart_of_accounts.json'
doc = json.load(open(p, encoding='utf-8'))
tree = doc.get('tree', {})
print('  chart: in_standard_chart_of_accounts.json  name=%s' % doc.get('name'))

ZELIN7 = ["account_name","account_number","account_type","root_type","is_group","tax_rate","account_currency"]
UP8 = ZELIN7 + ["account_category"]

def probe(children, keylist, hits, path=''):
    for account_name, child in children.items():
        if account_name not in keylist:
            if not isinstance(child, dict):
                hits.append((path + '/' + account_name, type(child).__name__, repr(child)[:46]))
                continue
            probe(child, keylist, hits, path + '/' + account_name)

h7, h8 = [], []
probe(tree, ZELIN7, h7)
probe(tree, UP8, h8)
print('  with zelin 7-key list    -> %d non-dict values reached (each => child.get() AttributeError)' % len(h7))
for pth, t, v in h7[:5]:
    print('        %-52s type=%-4s value=%s' % (pth[-52:], t, v))
print('  with upstream 8-key list -> %d non-dict values reached' % len(h8))
print('  => zelin 7-key list treats account_category as a child ACCOUNT NAME; its value is a str,')
print('     so the recursive _import_accounts calls .get() on a str => AttributeError.')

print()
print('  --- do zelin\'s own 4 CN charts carry account_category? ---')
CD = r'D:\ERX-001\Reference\zelin-tech-erpnext_china\erpnext_china\chart_of_accounts\custom_accounts\chart_of_accounts'
for fn in sorted(os.listdir(CD)):
    if not fn.endswith('.json'): continue
    raw = open(os.path.join(CD, fn), encoding='utf-8').read()
    d = json.loads(raw)
    hh = []
    probe(d.get('tree', {}), ZELIN7, hh)
    print('    %-42s account_category=%d  non-dict-reached-with-7key=%d' % (fn, raw.count('account_category'), len(hh)))
print('  => so the 7-key bug does NOT fire on the 4 CN charts; it fires when the OVERRIDDEN')
print('     get_chart/create path is used for a chart that DOES carry account_category.')

print()
print('===== CLAIM 5 mechanism: get_chart returns str (not dict) on total miss =====')
charts_dir = r'D:\ERX-001\frappe-bench\apps\erpnext\erpnext\accounts\doctype\account\chart_of_accounts'
custom_dir = r'D:\ERX-001\Reference\zelin-tech-erpnext_china\erpnext_china\chart_of_accounts\custom_accounts'

def replay_get_chart(chart_template):
    chart = {}                                     # zelin line 152
    for folder in ('verified',):                   # line 162
        path = os.path.join(charts_dir, folder)
        for fname in sorted(os.listdir(path)):
            if fname.endswith('.json'):
                try:
                    with open(os.path.join(path, fname), encoding='utf-8') as f:
                        chart = f.read()           # line 169 -- REASSIGNS chart to str
                        if chart and json.loads(chart).get('name') == chart_template:
                            return json.loads(chart).get('tree')
                except Exception:
                    pass
    for cf in ('chart_of_accounts', 'custom_of_accounts'):   # line 177
        cp = os.path.join(custom_dir, cf)
        if os.path.exists(cp):
            for f1n in sorted(os.listdir(cp)):
                if f1n.endswith('.json'):
                    try:
                        with open(os.path.join(cp, f1n), encoding='utf-8') as f1:
                            chart1 = f1.read()     # line 185 -- separate var; chart stays str
                            if chart1 and json.loads(chart1).get('name') == chart_template:
                                return json.loads(chart1).get('tree')
                    except Exception:
                        pass
    return chart                                   # line 191

for tpl in ['\u5c0f\u4f01\u4e1a\u4f1a\u8ba1\u51c6\u5219(2024)', 'NoSuchChartXYZ']:
    r = replay_get_chart(tpl)
    print('  template=%-30s -> type=%-5s len=%s' % (tpl, type(r).__name__, len(r)))
    if isinstance(r, str):
        print('        first 64 chars: %s' % r[:64].replace('\n', ' '))
        try:
            r.get('x')
        except AttributeError as e:
            print('        caller .get() => AttributeError: %s' % e)
print('  => CONFIRMED: on total miss it returns the LAST read verified chart file as raw TEXT.')
