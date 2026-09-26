# -*- coding: utf-8 -*-
# Reproduces defect 1 and defect 2 failure modes with the REAL upstream signatures,
# without importing frappe or touching the site.

print('=== DEFECT 2: log_error first positional arg is `title` ===')
# exact v16 signature, copied from frappe/utils/error.py L44-49
def log_error(title=None, message=None, reference_doctype=None,
              reference_name=None, *, defer_insert=False):
    return ('title=' + repr(title), 'message=' + repr(message))

print('[ok pattern]  log_error(title=..., message=...) ->',
      log_error(title='T', message='M'))
print('[ok pattern]  log_error("T", "M")              ->', log_error('T', 'M'))
print('[zelin utils.py:38 style] log_error("single")  ->', log_error('single'))
try:
    # this is literally custom_account.py:86 / 173 / 189 / 208 / 227 / 245
    log_error('Error rebuilding tree in create_charts2: boom', title='Tree Rebuild Error')
    print('[zelin custom_account style] NO ERROR (unexpected)')
except TypeError as e:
    print('[zelin custom_account style] TypeError:', e)

print()
print('=== DEFECT 1: 7-key exclusion table vs 8-key upstream ===')

UPSTREAM_8 = ["account_name","account_number","account_type","account_category",
              "root_type","is_group","tax_rate","account_currency"]
ZELIN_7    = ["account_name","account_number","account_type",
              "root_type","is_group","tax_rate","account_currency"]
print('upstream get_chart_metadata_fields():', len(UPSTREAM_8), 'keys')
print('zelin hardcoded (L32-40 / L106-118):', len(ZELIN_7), 'keys')
print('missing from zelin:', set(UPSTREAM_8) - set(ZELIN_7))

# a chart node shaped the way upstream v16 charts are (in_standard_chart_of_accounts.json has it)
node = {
    "应收账款": {
        "account_number": "1122",
        "account_type": "Receivable",
        "account_category": "Trade Receivable",   # the 8th key
        "root_type": "Asset",
        "is_group": 0,
    }
}

def import_accounts(children, exclusion_table, label):
    for account_name, child in children.items():
        for sub_name, sub in child.items():
            if sub_name not in exclusion_table:
                # this is custom_account.py L41
                try:
                    sub.get("account_number")
                    print(f'  [{label}] treated {sub_name!r} as a child account -> .get() ok')
                except AttributeError as e:
                    print(f'  [{label}] treated {sub_name!r} as a child account -> AttributeError: {e}')

print()
print('walking the node with the UPSTREAM 8-key table:')
import_accounts(node, UPSTREAM_8, 'upstream')
print('  (no output above = every metadata key correctly skipped)')
print('walking the node with the ZELIN 7-key table:')
import_accounts(node, ZELIN_7, 'zelin')

print()
print('--- identify_is_group side effect ---')
child = node["应收账款"]
for label, tbl in (('upstream8', UPSTREAM_8), ('zelin7', ZELIN_7)):
    leftover = set(child.keys()) - set(tbl)
    print(f'  [{label}] set(child)-set(table) = {leftover} -> is_group = {1 if len(leftover) else 0}')
