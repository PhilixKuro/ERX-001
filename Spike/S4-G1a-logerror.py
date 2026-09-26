# -*- coding: utf-8 -*-
# Replay zelin's log_error call shapes against the REAL v16 frappe signature,
# using inspect.signature on the actual source (no frappe import / no site touch).
import sys, io, re, inspect
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SRC = r'D:\ERX-001\frappe-bench\apps\frappe\frappe\utils\error.py'
src = open(SRC, encoding='utf-8').read()

# extract the real def header verbatim
m = re.search(r'^def log_error\((.*?)\) -> "ErrorLog":', src, re.S | re.M)
print('=== REAL v16 frappe.utils.error.log_error header ===')
print('def log_error(' + m.group(1) + ')')
print()

# build a stub with the identical parameter spec via exec, so binding rules are identical
stub_src = 'def log_error(' + m.group(1) + '):\n    return dict(title=title, message=message)\n'
ns = {}
exec(stub_src, ns)
log_error = ns['log_error']
print('=== stub signature (must equal real) ===')
print(inspect.signature(log_error))
print()

cases = [
    ('A. positional-only  (utils.py:38,59,84,103,178 / install.py:75,115 / doc_events.py:32)',
     ('china_company_default.utils.set_default_accounts',), {}),
    ('B. positional + title= kwarg  (custom_account.py:86,173,189,208,227,245)',
     ('Error rebuilding tree in create_charts2: boom',), {'title': 'Tree Rebuild Error'}),
    ('C. what zelin probably MEANT (message= + title=)',
     (), {'message': 'Error rebuilding tree: boom', 'title': 'Tree Rebuild Error'}),
]
print('=== replay ===')
for label, a, kw in cases:
    try:
        r = log_error(*a, **kw)
        print('  OK        %-72s -> %s' % (label, r))
    except TypeError as e:
        print('  TypeError %-72s -> %s' % (label, e))

print()
print('=== consequence of case A: title carries the message, message stays None ===')
print('    log_error body (error.py:62-68): `if message:` is False  =>')
print('      traceback = frappe.get_traceback(...)   # real traceback still captured')
print('      title     = the string zelin passed     # so A is SLOPPY BUT FUNCTIONAL')
