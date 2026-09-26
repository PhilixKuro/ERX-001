# -*- coding: utf-8 -*-
import csv, os, io, re

BENCH = r'D:/ERX-001/frappe-bench/apps'
ZH = r'D:/ERX-001/Reference/zelin-tech-erpnext_china/erpnext_china/translations/zh.csv'

rows = list(csv.reader(io.StringIO(open(ZH, encoding='utf-8').read())))
zelin = {}
for r in rows:
    if len(r) >= 2 and r[0].strip():
        zelin.setdefault(r[0], r[1])
print('zelin unique keys:', len(zelin))

# official v16 translation sources
print()
print('=== official translation files present ===')
for app in ('frappe', 'erpnext'):
    for sub in ('locale', 'translations'):
        d = os.path.join(BENCH, app, app, sub)
        if os.path.isdir(d):
            fs = sorted(os.listdir(d))
            zh = [f for f in fs if f.startswith('zh')]
            print(f'{app}/{sub}: {len(fs)} files; zh*: {zh}')
        else:
            print(f'{app}/{sub}: MISSING')

def po_msgids(path):
    ids = {}
    cur = None
    buf = []
    mode = None
    out = {}
    txt = open(path, encoding='utf-8').read()
    # simple po parse
    msgid = None; msgstr = None; state=None
    for line in txt.splitlines():
        line = line.rstrip()
        if line.startswith('msgid '):
            if msgid is not None:
                out[msgid] = msgstr or ''
            msgid = line[6:].strip().strip('"'); msgstr=None; state='id'
        elif line.startswith('msgstr '):
            msgstr = line[7:].strip().strip('"'); state='str'
        elif line.startswith('"') and state=='id':
            msgid += line.strip().strip('"')
        elif line.startswith('"') and state=='str':
            msgstr += line.strip().strip('"')
        elif not line:
            if msgid is not None:
                out[msgid]=msgstr or ''
                msgid=None; msgstr=None; state=None
    if msgid is not None:
        out[msgid]=msgstr or ''
    out.pop('', None)
    return out

official = {}
for app in ('frappe', 'erpnext'):
    p = os.path.join(BENCH, app, app, 'locale', 'zh.po')
    if os.path.exists(p):
        d = po_msgids(p)
        print(f'  {app}/locale/zh.po msgids: {len(d)}')
        official[app] = d

allofficial = set()
for d in official.values():
    allofficial |= set(d.keys())
print()
print('official zh msgid universe (frappe+erpnext):', len(allofficial))

zk = set(zelin.keys())
inter = zk & allofficial
print('zelin keys that exist as official zh msgid:', len(inter))
print('zelin keys NOT in official zh po:', len(zk - allofficial))

# how many of those differ in translation
diff = 0; same = 0
for k in inter:
    off = None
    for app in official:
        if k in official[app]:
            off = official[app][k]; break
    if off is not None:
        if off.strip() == zelin[k].strip(): same += 1
        else: diff += 1
print('  of the overlap: identical translation:', same, '| different:', diff)
