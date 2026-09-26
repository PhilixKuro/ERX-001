# -*- coding: utf-8 -*-
import sys, os
sys.path.insert(0, r'D:/ERX-001/frappe-bench/env/lib/python3.14/site-packages')
from babel.messages.pofile import read_po
from babel.messages.mofile import read_mo

P = r'D:/ERX-001/Reference/zelin-tech-erpnext_china/erpnext_china/locale/zh.po'
with open(P, 'rb') as f:
    cat = read_po(f)
entries = [(m.id if isinstance(m.id, str) else m.id[0],
            m.string if isinstance(m.string, str) else (m.string[0] if m.string else ''),
            [loc[0] for loc in (m.locations or [])])
           for m in cat if m.id]
print('zelin locale/zh.po entries:', len(entries))
print('locale header present:', cat.locale)
untr = [e for e in entries if not e[1]]
print('untranslated:', len(untr))

# provenance from reference comments
import collections
apps = collections.Counter()
for _id, _s, locs in entries:
    if not locs:
        apps['(no reference comment)'] += 1
    for l in locs:
        apps[l.split('/')[0]] += 1
print('reference-comment provenance:', dict(apps))

# overlap with runtime mo
MO = r'D:/ERX-001/frappe-bench/sites/assets/locale/zh/LC_MESSAGES'
mo = {}
for app in ('frappe', 'erpnext'):
    with open(os.path.join(MO, app + '.mo'), 'rb') as f:
        c = read_mo(f)
    for m in c:
        if not m.id: continue
        mid = m.id if isinstance(m.id, str) else m.id[0]
        s = m.string if isinstance(m.string, str) else (m.string[0] if m.string else '')
        if s: mo.setdefault(mid, s)
ids = {e[0] for e in entries}
print()
print('overlap with official runtime zh.mo:', len(ids & set(mo)))
print('po-only (no official zh):', len(ids - set(mo)))

# overlap with zelin's own csv
import csv, io
ZH = r'D:/ERX-001/Reference/zelin-tech-erpnext_china/erpnext_china/translations/zh.csv'
rows = list(csv.reader(io.StringIO(open(ZH, encoding='utf-8').read())))
csvk = {r[0]: r[1] for r in rows if len(r) >= 2 and r[0].strip()}
print('po ids also in zelin OWN csv:', len(ids & set(csvk)))
inboth = ids & set(csvk)
d = {i for i in inboth if csvk[i].strip() != dict((e[0], e[1]) for e in entries)[i].strip()}
print('  of those, po and csv DISAGREE on the translation:', len(d))
for i in list(d)[:5]:
    print(f'    {i[:60]!r}: csv={csvk[i][:30]!r} po={dict((e[0],e[1]) for e in entries)[i][:30]!r}')
