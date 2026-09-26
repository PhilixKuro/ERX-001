# -*- coding: utf-8 -*-
import sys, io, json, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print('===== CASCADE: str chart -> AttributeError -> log_error TypeError masks it =====')
def log_error(title=None, message=None, reference_doctype=None, reference_name=None, *, defer_insert=False):
    return 'logged'

# faithful shape of zelin custom_account.py:81-87
def create_charts_shape(chart):
    def _import_accounts(children, parent, root_type, root_account=False):
        for account_name, child in children.items():          # line 28
            if account_name not in ["account_name","account_number","account_type",
                                    "root_type","is_group","tax_rate","account_currency"]:
                child.get("account_number")                     # line 41
    try:
        _import_accounts(chart, None, None, root_account=True)  # line 83
    except Exception as e:                                      # line 85
        # line 86 exactly as written in zelin
        log_error(f"Error rebuilding tree in create_charts2: {e}", title="Tree Rebuild Error")
    return 'no-raise'

print('  -- case A: chart is a str (get_chart total-miss path) --')
try:
    print('     result: %s' % create_charts_shape('{"country_code": "tw", ...}'))
except Exception as e:
    print('     RAISED %s: %s' % (type(e).__name__, e))

print('  -- case B: chart carries account_category (str leaf value) --')
p = os.path.join('D:', os.sep, 'ERX-001', 'frappe-bench', 'apps', 'erpnext', 'erpnext', 'accounts',
                 'doctype', 'account', 'chart_of_accounts', 'verified', 'in_standard_chart_of_accounts.json')
tree = json.load(open(p, encoding='utf-8'))['tree']
try:
    print('     result: %s' % create_charts_shape(tree))
except Exception as e:
    print('     RAISED %s: %s' % (type(e).__name__, e))

print()
print('  => In BOTH cases the inner AttributeError is caught at :85, then the :86 log_error call')
print('     itself raises TypeError (positional msg + keyword title). The TypeError escapes the')
print('     except block, so the ORIGINAL cause never reaches Error Log. Diagnosis gets masked.')

print()
print('===== doc_events gating check =====')
src = open(os.path.join('D:', os.sep, 'ERX-001', 'Reference', 'zelin-tech-erpnext_china',
                        'erpnext_china', 'doc_events.py'), encoding='utf-8').read()
lines = src.splitlines()
for i, l in enumerate(lines, 1):
    if 'def company_on_update' in l:
        for j in range(i, min(i + 9, len(lines) + 1)):
            print('  %3d %s' % (j, lines[j-1]))
print('  => company_before_insert IS gated on (chart in china_coa and country==China);')
print('     company_on_update calls erpnext_china_create_charts with NO such gate.')
