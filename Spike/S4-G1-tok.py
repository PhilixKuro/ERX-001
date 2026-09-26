# -*- coding: utf-8 -*-
import tokenize, io, sys, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
p = os.path.join('D:', os.sep, 'ERX-001', 'Reference', 'zelin-tech-erpnext_china', 'erpnext_china',
                 'erpnext_china', 'report', 'fin_profit_and_loss_statement', 'fin_profit_and_loss_statement.py')
print('===== is the erpnext_chinacounting import at :359 real code or string content? =====')
toks = list(tokenize.tokenize(open(p, 'rb').readline))
for t in toks:
    if t.start[0] >= 355 and t.type in (tokenize.STRING, tokenize.NAME, tokenize.COMMENT):
        nm = tokenize.tok_name[t.type]
        print('  line %-4d %-8s %s' % (t.start[0], nm, repr(t.string)[:88]))
        if nm == 'STRING' and t.start[0] <= 359 <= t.end[0]:
            print('        >>> line 359 falls INSIDE this STRING token (lines %d-%d)' % (t.start[0], t.end[0]))
print()
print('===== also check: any REAL import of erpnext_chinacounting anywhere? =====')
import re
base = os.path.join('D:', os.sep, 'ERX-001', 'Reference', 'zelin-tech-erpnext_china')
for r, d, f in os.walk(base):
    if '.git' in r: continue
    for n in f:
        if not n.endswith('.py'): continue
        fp = os.path.join(r, n)
        src = open(fp, encoding='utf-8').read()
        if 'chinacounting' not in src: continue
        real = []
        for t in tokenize.tokenize(open(fp, 'rb').readline):
            if t.type == tokenize.NAME and t.string == 'import':
                lines = src.splitlines()
                ln = lines[t.start[0]-1]
                if 'chinacounting' in ln:
                    real.append((t.start[0], ln.strip()[:70]))
        print('  %s -> real import tokens mentioning chinacounting: %s' % (os.path.basename(fp), real or 'NONE (string/comment only)'))
