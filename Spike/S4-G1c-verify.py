# -*- coding: utf-8 -*-
import csv, os, json, io, sys

ZH = r'D:/ERX-001/Reference/zelin-tech-erpnext_china/erpnext_china/translations/zh.csv'

print('=== translations/zh.csv ===')
raw = open(ZH, 'rb').read()
print('bytes:', len(raw))
print('newline count (LF):', raw.count(b'\n'))
print('ends with newline:', raw.endswith(b'\n'))
txt = raw.decode('utf-8')
rows = list(csv.reader(io.StringIO(txt)))
print('csv.reader row count:', len(rows))
widths = {}
for r in rows:
    widths[len(r)] = widths.get(len(r), 0) + 1
print('row widths:', dict(sorted(widths.items())))
pairs = [r for r in rows if len(r) >= 2 and r[0].strip()]
print('usable pairs (>=2 cols, nonempty key):', len(pairs))
keys = [r[0] for r in pairs]
print('unique source strings:', len(set(keys)))
dups = len(keys) - len(set(keys))
print('duplicate source keys:', dups)
# blank translation
blank = sum(1 for r in pairs if not r[1].strip())
print('pairs with EMPTY translation:', blank)
# 3-col rows (context)
three = [r for r in rows if len(r) >= 3 and r[2].strip()]
print('rows with a 3rd nonempty col (context):', len(three))
