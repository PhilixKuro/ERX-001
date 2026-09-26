# -*- coding: utf-8 -*-
import json, os, sys, io, ast
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
UOMDATA = os.path.join('D:', os.sep, 'ERX-001', 'frappe-bench', 'apps', 'erpnext',
                       'erpnext', 'setup', 'setup_wizard', 'data', 'uom_data.json')
INST = os.path.join('D:', os.sep, 'ERX-001', 'Reference', 'zelin-tech-erpnext_china',
                    'erpnext_china', 'setup', 'install.py')

ship = json.load(open(UOMDATA, encoding='utf-8'))
ship_names = [u.get('uom_name') for u in ship] if isinstance(ship, list) else []
print('===== erpnext v16 ships %d UOMs (uom_data.json) =====' % len(ship_names))
print('  sample: %s' % ship_names[:12])

src = open(INST, encoding='utf-8').read()
start = src.index('uom_list = [')
end = src.index(']', start) + 1
zelin = ast.literal_eval(src[start:end].split('=', 1)[1].strip())
print()
print('===== zelin uom_list = %d entries (all Chinese) =====' % len(zelin))
print('  %s' % zelin[:10])

overlap = [u for u in ship_names if u in zelin]
disabled = [u for u in ship_names if u not in zelin]
print()
print('===== install.py:69  frappe.db.set_value(UOM, {name: (not in, uom_list)}, enabled, 0) =====')
print('  shipped UOMs that SURVIVE (present in zelin list): %d  -> %s' % (len(overlap), overlap))
print('  shipped UOMs that get DISABLED:                    %d' % len(disabled))
print('  sample disabled: %s' % disabled[:20])
print()
print('  => blast radius: every stock/BOM/pricing record referencing any of those %d UOMs' % len(disabled))
print('     loses a usable unit. This is the reason integrated install was rejected.')
