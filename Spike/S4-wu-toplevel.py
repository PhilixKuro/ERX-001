# -*- coding: utf-8 -*-
import json, io, os
BASE = r'D:\ERX-001\Reference\zelin-tech-erpnext_china\erpnext_china\chart_of_accounts\custom_accounts\chart_of_accounts'
for fn in sorted(os.listdir(BASE)):
    if not fn.endswith('.json'):
        continue
    d = json.load(io.open(os.path.join(BASE, fn), encoding='utf-8'))
    print('FILE:', fn)
    for k, v in d.items():
        if isinstance(v, dict):
            print('   %-16s -> dict with %d keys: %s' % (k, len(v), list(v.keys())[:8]))
        else:
            print('   %-16s -> %r' % (k, v))
    print()
