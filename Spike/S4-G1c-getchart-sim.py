# -*- coding: utf-8 -*-
# Replicates the else-branch control flow of zelin custom_account.py get_chart (L152-191)
# and of upstream chart_of_accounts.py get_chart (L102-131), against the REAL chart dir.
# Pure python, no frappe, no site touched.
import os, json

CHARTS = r'D:/ERX-001/frappe-bench/apps/erpnext/erpnext/accounts/doctype/account/chart_of_accounts'

def zelin_get_chart(chart_template, allow_unverified=False):
    chart = {}                                  # L152
    folders = ('verified',)
    if allow_unverified:
        folders = ('verified', 'unverified')
    for folder in folders:                      # L162
        path = os.path.join(CHARTS, folder)
        for fname in sorted(os.listdir(path)):  # L164
            if fname.endswith('.json'):
                try:
                    with open(os.path.join(path, fname), encoding='utf-8') as f:
                        chart = f.read()        # L169  <-- rebinds `chart` to str
                        if chart and json.loads(chart).get('name') == chart_template:
                            return json.loads(chart).get('tree')   # L171
                except Exception:
                    pass
    # zelin then scans custom folders into chart1 (separate name); those do not exist here
    return chart                                # L191  <-- the added line

def upstream_get_chart(chart_template, allow_unverified=False):
    chart = {}                                  # upstream L103
    folders = ('verified',)
    if allow_unverified:
        folders = ('verified', 'unverified')
    for folder in folders:
        path = os.path.join(CHARTS, folder)
        for fname in sorted(os.listdir(path)):
            if fname.endswith('.json'):
                with open(os.path.join(path, fname), encoding='utf-8') as f:
                    chart = f.read()            # upstream L129
                    if chart and json.loads(chart).get('name') == chart_template:
                        return json.loads(chart).get('tree')
    # upstream has NO trailing `return chart` -> falls off the end

BOGUS = '小企业会计准则'   # a China CoA name that is NOT in upstream verified/
print('template asked for:', BOGUS)
print()
z = zelin_get_chart(BOGUS)
print('ZELIN   get_chart ->', type(z).__name__, '| truthy:', bool(z), '| len:', len(z))
print('  first 90 chars:', repr(z[:90]) if isinstance(z, str) else z)
u = upstream_get_chart(BOGUS)
print('UPSTREAM get_chart ->', type(u).__name__, '| truthy:', bool(u))
print()
print('--- what the caller then does ---')
for name, val in (('zelin', z), ('upstream', u)):
    print(f'[{name}] `if chart:` ->', bool(val))
    try:
        val.items()
        print(f'[{name}] chart.items() -> ok')
    except AttributeError as e:
        print(f'[{name}] chart.items() -> AttributeError: {e}')
    except Exception as e:
        print(f'[{name}] chart.items() -> {type(e).__name__}: {e}')
    try:
        val.get('x')
        print(f'[{name}] chart.get() -> ok')
    except AttributeError as e:
        print(f'[{name}] chart.get()   -> AttributeError: {e}')
    except Exception as e:
        print(f'[{name}] chart.get()   -> {type(e).__name__}: {e}')
print()
print('which file was last read in verified/ (that is what zelin returns):')
vs = sorted(f for f in os.listdir(os.path.join(CHARTS, 'verified')) if f.endswith('.json'))
print('  ', vs[-1], '| total verified json:', len(vs))
