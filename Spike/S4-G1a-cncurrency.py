# -*- coding: utf-8 -*-
# Run zelin's cncurrency() as a PURE function (no frappe, no site).
# Extract the function source verbatim from print_utils.py and exec it standalone.
import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from decimal import Decimal
import warnings

SRC = r'D:\ERX-001\Reference\zelin-tech-erpnext_china\erpnext_china\print_utils.py'
src = open(SRC, encoding='utf-8').read()

i = src.index('def cncurrency(')
j = len(src)
fn_src = src[i:j]
ns = {'Decimal': Decimal, 'warnings': warnings}
exec(fn_src, ns)
cncurrency = ns['cncurrency']

print('=== extracted function, %d chars ===' % len(fn_src))
print()
cases = ['0.00', '1.23', '-1.23', '-100.00', '10000.05', '100000000.00',
         '0.05', '0.50', '1234567.89', '-0.01']
print('%-16s %-8s %s' % ('input', 'sign?', 'cncurrency(value)'))
for c in cases:
    try:
        r = cncurrency(c)
        neg = c.startswith('-')
        has = r.startswith('负')
        flag = 'OK' if (neg == has) else ('LOST_SIGN' if neg else 'SPURIOUS')
        print('%-16s %-8s %s' % (c, flag, r))
    except Exception as e:
        print('%-16s %-8s EXC %s: %s' % (c, 'ERR', type(e).__name__, e))

print()
print('=== classical/capital combos for 1.00 ===')
for cap in (True, False):
    for cl in (None, True, False):
        try:
            print('  capital=%-5s classical=%-5s -> %s' % (cap, cl, cncurrency('1.00', capital=cap, classical=cl)))
        except Exception as e:
            print('  capital=%-5s classical=%-5s -> EXC %s' % (cap, cl, e))

print()
print('=== prefix= arg: is it honored? (signature says prefix=False means no 人民币 prefix) ===')
for p in (True, False):
    print('  prefix=%-5s -> %s' % (p, cncurrency('1.00', prefix=p)))
print()
print('  NOTE print_utils.py:109 does `prefix = \'\'` unconditionally,')
print('       which discards BOTH the caller\'s prefix arg AND the later 负 concat at :127-129.')
