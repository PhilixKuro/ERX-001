# -*- coding: utf-8 -*-
# Cross-check the crude PO parse using a real PO library if available.
import csv, io, os, sys
BENCH = r'D:/ERX-001/frappe-bench/apps'
ZH = r'D:/ERX-001/Reference/zelin-tech-erpnext_china/erpnext_china/translations/zh.csv'

lib = None
try:
    import polib
    lib = 'polib'
except ImportError:
    pass
print('polib available:', lib is not None)

if lib:
    official = {}
    for app in ('frappe', 'erpnext'):
        p = os.path.join(BENCH, app, app, 'locale', 'zh.po')
        po = polib.pofile(p)
        d = {e.msgid: e.msgstr for e in po if e.msgid}
        print(f'{app}/locale/zh.po: total entries {len(po)}, unique msgid {len(d)}, '
              f'translated {sum(1 for e in po if e.msgstr)}')
        official[app] = d
    allofficial = set()
    for d in official.values():
        allofficial |= set(d)
    print('official universe:', len(allofficial))

    rows = list(csv.reader(io.StringIO(open(ZH, encoding='utf-8').read())))
    zelin = {}
    for r in rows:
        if len(r) >= 2 and r[0].strip():
            zelin.setdefault(r[0], r[1])
    zk = set(zelin)
    inter = zk & allofficial
    print('zelin unique:', len(zk))
    print('OVERLAP with official:', len(inter))
    print('zelin-only (no official zh msgid):', len(zk - inter))
    same = diff = 0
    difflist = []
    for k in inter:
        off = official['frappe'].get(k)
        if off is None:
            off = official['erpnext'].get(k)
        if (off or '').strip() == zelin[k].strip():
            same += 1
        else:
            diff += 1
            difflist.append(k)
    print('  identical:', same, '| DIFFERENT:', diff)
    print()
    print('=> vocabulary material = zelin-only + differing =',
          len(zk - inter), '+', diff, '=', len(zk - inter) + diff)
else:
    print('SKIP: install-free cross-check unavailable; crude parse stands unverified')
