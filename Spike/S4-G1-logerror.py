import sys, io, inspect
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, r'D:\ERX-001\frappe-bench\apps\frappe')

src = open(r'D:\ERX-001\frappe-bench\apps\frappe\frappe\utils\error.py', encoding='utf-8').read()
i = src.index('def log_error(')
sig_src = src[i:src.index('"""Log error to Error Log"""', i)]
print('=== REAL v16 log_error signature ===')
print(sig_src.strip())
print()

# Rebuild an equivalent stub with the exact same parameter spec, then replay zelin's call shapes.
def log_error(title=None, message=None, reference_doctype=None, reference_name=None, *, defer_insert=False):
    return ('title=%r' % title, 'message=%r' % message)

print('=== replay of zelin call shapes against that spec ===')
cases = [
    ('custom_account.py:86/173/189/208/227/245 pattern',
     lambda: log_error('Error rebuilding tree: boom', title='Tree Rebuild Error')),
    ('utils.py:38/59/84/103/178 + install.py:75/115 + doc_events.py:32 pattern',
     lambda: log_error('china_company_default.utils.set_default_accounts')),
]
for label, fn in cases:
    try:
        r = fn()
        print('  OK       %-64s -> %s' % (label, r))
    except TypeError as e:
        print('  TypeError %-63s -> %s' % (label, e))
