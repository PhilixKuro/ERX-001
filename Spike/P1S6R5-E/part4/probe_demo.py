"""E-step read-only probe for erx.localhost. No writes; db rolled back at end.

Run inside container:
  /workspace/frappe-bench/env/bin/python /workspace/Spike/P1S6R5-E/part4/probe_demo.py
Output: /workspace/Spike/P1S6R5-E/part4/probe_demo.json
"""
import os
import json
from collections import defaultdict
from pathlib import Path

import frappe

OUT = Path('/workspace/Spike/P1S6R5-E/part4/probe_demo.json')
COMPANY = '华东弹簧有限公司'  # HDTH company name
RECEIVABLE = '应收'
RECEIVABLE_ACCT = '应收账款'

os.chdir('/workspace/frappe-bench/sites')
frappe.init(site='erx.localhost', sites_path='.')
frappe.connect()
frappe.set_user('Administrator')
frappe.local.lang = 'zh'
result = {'site': frappe.local.site}
try:
    # 6: baseline counts
    result['counts'] = {dt: frappe.db.count(dt) for dt in [
        'Translation', 'Cash Flow Worksheet', 'GL Entry', 'Stock Ledger Entry',
        'Item', 'Customer', 'Supplier', 'Employee', 'BOM', 'Sales Order', 'Sales Invoice',
        'Purchase Order', 'Purchase Invoice', 'Payment Entry', 'Journal Entry', 'Stock Entry',
        'Delivery Note', 'Work Order', 'Job Card', 'Production Plan', 'Quotation',
        'CRM Lead', 'CRM Deal', 'User']}
    result['worksheet_table'] = frappe.db.table_exists('Cash Flow Worksheet')
    result['old_cash_flow_table'] = frappe.db.table_exists('Cash Flow')
    result['hdth_accounts'] = frappe.db.count('Account', {'company': COMPANY})
    result['companies'] = frappe.get_all('Company', pluck='name')
    prefixed = {}
    for dt in ['Company', 'Warehouse', 'Account', 'Customer', 'Supplier', 'Item', 'Employee',
               'Operation', 'Workstation', 'Routing', 'User', 'Item Price', 'UOM', 'Cost Center',
               'Contact', 'Address', 'CRM Lead', 'CRM Deal']:
        if not frappe.db.table_exists(dt):
            continue
        names = set()
        for pat in ['_FCT%', '_fct%', '_S6%', '_s6%']:
            names.update(frappe.get_all(dt, filters={'name': ['like', pat]}, pluck='name'))
        prefixed[dt] = sorted(names)
    result['prefixed_records'] = prefixed

    # 1: translation_check (find_problems only reads) and check_app_order (reads)
    from frappe_china import translation_check
    result['translation_check'] = translation_check.find_problems()
    from frappe_china.install import check_app_order
    order = check_app_order()
    result['check_app_order'] = {k: order[k] for k in ('ok', 'order', 'order_ok', 'overrides_ok', 'translation_ok', 'company_checks_ok', 'problems')}

    # 4: sidebar section-break duplicates after zh translation
    from frappe import _
    dupes = {}
    for sb in frappe.get_all('Workspace Sidebar', pluck='name'):
        doc = frappe.get_doc('Workspace Sidebar', sb)
        groups = defaultdict(list)
        for item in doc.items:
            if item.type == 'Section Break':
                groups[_(item.label)].append(item.label)
        d = {k: v for k, v in groups.items() if len(v) > 1}
        if d:
            dupes[sb] = d
    result['sidebar_section_dupes'] = dupes
    # 4: account_type options
    opts = (frappe.get_meta('Account').get_field('account_type').options or '').split('\n')
    translated = [_(o) for o in opts if o]
    result['account_type_receivable_hits'] = [(o, _(o)) for o in opts if o and RECEIVABLE in _(o)]
    result['account_type_receivable_acct_count'] = sum(1 for t in translated if t == RECEIVABLE_ACCT)
    # 4: link search
    from frappe.desk.search import search_widget
    rows = search_widget('Account', RECEIVABLE, filters={'company': COMPANY}, page_length=50)
    result['account_link_search'] = [list(r) if not isinstance(r, dict) else r for r in (rows or [])]

    # 5: original entries current export (app != frappe_china)
    snap = {}
    for dt in ('Desktop Icon', 'Workspace Sidebar'):
        meta = frappe.get_meta(dt)
        fields = ['name', 'modified'] + [f for f in ('hidden', 'idx') if meta.has_field(f)]
        snap[dt] = frappe.get_all(dt, filters={'app': ('!=', 'frappe_china')}, fields=fields, order_by='name')
    names = [r.name for r in snap['Workspace Sidebar']]
    snap['Workspace Sidebar Item'] = frappe.get_all('Workspace Sidebar Item', filters={'parent': ('in', names)}, fields=['name', 'parent', 'modified', 'idx'], order_by='name')
    result['original_entries'] = snap
finally:
    frappe.db.rollback()
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=1, default=str), encoding='utf-8')
    frappe.destroy()
print('written')
