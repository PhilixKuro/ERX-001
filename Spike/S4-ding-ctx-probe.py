# -*- coding: utf-8 -*-
import io, os

BENCH = r'D:\ERX-001\frappe-bench\apps'
words = ['Make', 'Weight', 'Select', 'Margin', 'Manufacture', 'Minute',
         'Number', 'Level', 'Ref Code', 'Rate', 'Tax Rate', 'Setup', 'Settings']

Q = chr(34)  # ASCII double quote, avoid literal in source


def unq(line, prefix):
    # line like:  msgid "Foo"
    rest = line[len(prefix):].strip()
    if rest.startswith(Q) and rest.endswith(Q) and len(rest) >= 2:
        return rest[1:-1]
    return rest


def blocks(path):
    txt = io.open(path, encoding='utf-8').read()
    for blk in txt.split('\n\n'):
        mid = mstr = None
        mctx = None
        for line in blk.split('\n'):
            s = line.strip()
            if s.startswith('msgid ') and mid is None:
                mid = unq(s, 'msgid ')
            elif s.startswith('msgstr ') and mstr is None:
                mstr = unq(s, 'msgstr ')
            elif s.startswith('msgctxt '):
                mctx = unq(s, 'msgctxt ')
        if mid:
            yield mid, (mstr or ''), mctx


for app in ('frappe', 'erpnext'):
    pp = os.path.join(BENCH, app, app, 'locale', 'zh.po')
    print('===== %s =====' % app)
    tot = ctxcnt = 0
    store = {}
    rev = {}
    for mid, mstr, mctx in blocks(pp):
        tot += 1
        if mctx:
            ctxcnt += 1
        if mid in words:
            store.setdefault(mid, []).append((mctx, mstr))
        if mstr:
            rev.setdefault(mstr, []).append((mid, mctx))
    print('  blocks=%d  with-msgctxt=%d' % (tot, ctxcnt))
    for w in words:
        for mctx, mstr in store.get(w, []):
            print('    %-12s ctx=%-30s -> %s' % (w, mctx, mstr))
    # collision detection: one Chinese target, many English sources
    coll = {k: v for k, v in rev.items() if len({m for m, _c in v}) > 1}
    print('  distinct zh targets: %d ; targets hit by >1 distinct en source: %d'
          % (len(rev), len(coll)))
    worst = sorted(coll.items(), key=lambda kv: -len({m for m, _c in kv[1]}))[:12]
    print('  --- worst collisions (zh target <- many en sources) ---')
    for zh, lst in worst:
        srcs = sorted({m for m, _c in lst})
        print('    %-14s <- %d sources: %s' % (zh, len(srcs), ', '.join(srcs[:9])))
