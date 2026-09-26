# -*- coding: utf-8 -*-
import json, os, io, csv, collections

BENCH = r'D:\ERX-001\frappe-bench\apps'
REF = r'D:\ERX-001\Reference'

# 1) cast() tail -- what happens when fieldtype is None?
src = io.open(os.path.join(BENCH, 'frappe', 'frappe', 'utils', 'data.py'),
              encoding='utf-8').read()
i = src.find('def cast(')
seg = src[i:i + 2200]
print('=== cast() full body tail ===')
print(seg[seg.find('elif fieldtype in ('):])

# 2) the Vehicle name typo
ps = os.path.join(REF, 'zelin-tech-erpnext_china', 'erpnext_china', 'fixtures',
                  'property_setter.json')
recs = json.load(io.open(ps, encoding='utf-8'))
print()
print('=== name vs autoname consistency for label records ===')
bad = 0
for r in recs:
    if r.get('property') != 'label':
        continue
    expect = '%s-%s-%s' % (r.get('doc_type'),
                           r.get('field_name') or r.get('row_name') or 'main',
                           r.get('property'))
    if r.get('name') != expect:
        bad += 1
        print('  MISMATCH name=%-34s expected=%s' % (r.get('name'), expect))
print('  mismatches: %d / 25' % bad)

# 3) csv comment / 4th column support -- simulate get_translation_dict_from_file
print()
print('=== simulate csv parser on comment & 4-col rows ===')
sample = [['# a comment line'], ['Src', 'Tgt'], ['Src2', 'Tgt2', 'Ctx'],
          ['Src3', 'Tgt3', 'Ctx3', 'note'], []]
for item in sample:
    if len(item) in [2, 3]:
        if len(item) == 3 and item[2]:
            print('  %-42s -> key=%s (3-col, context)' % (item, item[0] + ':' + item[2]))
        else:
            print('  %-42s -> key=%s (2-col)' % (item, item[0]))
    elif item:
        print('  %-42s -> LOGGED AS "Bad translation"' % item)
    else:
        print('  %-42s -> silently skipped' % item)

# 4) does zelin's own zh.csv use a 3rd column for the colliding words?
cz = os.path.join(REF, 'zelin-tech-erpnext_china', 'erpnext_china',
                  'translations', 'zh.csv')
rows = list(csv.reader(io.open(cz, encoding='utf-8', newline='')))
print()
print('=== zelin zh.csv: reverse-collision check (one zh <- many en) ===')
rev = {}
for r in rows:
    if len(r) >= 2 and r[1]:
        rev.setdefault(r[1], set()).add(r[0])
coll = {k: v for k, v in rev.items() if len(v) > 1}
print('  distinct zh targets: %d ; collided: %d' % (len(rev), len(coll)))
for zh, srcs in sorted(coll.items(), key=lambda kv: -len(kv[1]))[:8]:
    print('    %-12s <- %d : %s' % (zh, len(srcs), ', '.join(sorted(srcs)[:8])))
