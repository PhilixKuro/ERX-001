import os, io, csv
BENCH = r'D:\ERX-001\frappe-bench\apps'
miss = ['Vihicle Maker','Weightage','Bank Account Name','SELECT','Make','Weight','Select','Account Name']
for app in ('frappe','erpnext'):
    cp = os.path.join(BENCH, app, app, 'translations', 'zh.csv')
    pp = os.path.join(BENCH, app, app, 'locale', 'zh.po')
    print('=== %s : csv exists=%s  po exists=%s ===' % (app, os.path.exists(cp), os.path.exists(pp)))
    if os.path.exists(cp):
        rows = list(csv.reader(io.open(cp, encoding='utf-8', newline='')))
        print('   csv rows:', len(rows))
    if os.path.exists(pp):
        txt = io.open(pp, encoding='utf-8').read()
        print('   po bytes:', len(txt), ' msgid count:', txt.count('\nmsgid '))
        for m in miss:
            tag = 'msgid "%s"' % m
            if tag in txt:
                i = txt.index(tag)
                seg = txt[i:i+220].split('\n')
                nxt = [l for l in seg[1:4] if l.startswith('msgstr')]
                print('     %-20s -> %s' % (m, nxt[0] if nxt else '?'))
            else:
                print('     %-20s -> ABSENT' % m)
# mo files compiled?
loc = os.path.join(r'D:\ERX-001\frappe-bench','sites','assets','locale')
print('=== compiled mo dir exists:', os.path.exists(loc), '===')
if os.path.exists(loc):
    for root, dirs, files in os.walk(loc):
        for f in files:
            if 'zh' in root and f.endswith('.mo'):
                print('   ', os.path.join(root,f))
