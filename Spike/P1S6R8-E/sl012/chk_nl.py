import importlib.util as u, csv, json, re
B = 'D:/ERX-001/frappe-bench/apps/'
s = u.spec_from_file_location('w', B + 'frappe_china/frappe_china/tests/translation_whitelist.py'); m = u.module_from_spec(s); s.loader.exec_module(m)
U = m.UNTRANSLATED
BS = chr(92)
LIT = BS + 'n'
nl = [k for k in U if LIT in k]
print('whitelist keys with literal backslash-n:', len(nl))
rows = list(csv.reader(open(B + 'frappe_china/frappe_china/translations/zh.csv', encoding='utf-8', newline='')))
csvk = {r[0].replace(LIT, '\n'): r for r in rows}
merged = json.load(open('erx_merged.json', encoding='utf-8'))
han = re.compile('[\u4e00-\u9fff]')
for k in nl:
    real = k.replace(LIT, '\n')
    r = csvk.get(real)
    print('-', k[:70], '| csv row exists:', bool(r), '| raw has literal:', (LIT in r[0]) if r else None,
          '| merged(real) chinese:', bool(han.search(merged.get(real) or '')), '| merged(literal) :', repr((merged.get(k) or '')[:20]))
lit = [r for r in rows if LIT in r[0]]
realn = [r for r in rows if '\n' in r[0]]
print('csv rows with literal backslash-n in source:', len(lit), ' with real newline:', len(realn))
# pot entries whose msgid contains escaped backslash followed by n (i.e. literal \n in the string)
cnt = []
for app in ['frappe', 'erpnext', 'crm', 'hrms', 'insights', 'raven']:
    t = open(B + f'{app}/{app}/locale/main.pot', encoding='utf-8').read()
    for mm in re.finditer(r'^msgid "(.*)"$', t, re.M):
        if BS + BS + 'n' in mm.group(1):
            cnt.append((app, mm.group(1)[:60]))
print('pot msgids containing literal backslash-n:', len(cnt))
for c in cnt: print('  ', c)
