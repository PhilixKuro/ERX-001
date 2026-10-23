import json
import os

import frappe

os.chdir('/workspace/frappe-bench/sites')
frappe.init(site='s8dev.localhost', sites_path='/workspace/frappe-bench/sites')
frappe.connect()
try:
    assert frappe.local.site == 's8dev.localhost'
    frappe.set_user('Administrator')
    result = {}
    result['orders'] = frappe.get_all('Work Order', filters={'docstatus': 1}, fields=['name', 'sales_order', 'qty', 'produced_qty', 'planned_start_date', 'status'], order_by='creation desc', limit=5)
    result['bins'] = frappe.get_all('Bin', filters={'item_code': 'WIRE-65MN-3.0'}, fields=['warehouse', 'actual_qty'])
    result['cards'] = frappe.get_all('Job Card', filters={'work_order': result['orders'][0]['name']}, fields=['name','for_quantity','time_required','operation','operation_id','docstatus','status','workstation'])
    result['progress'] = frappe.get_doc('Demo Progress', 'Demo Progress').as_dict()
    result['settings'] = frappe.get_single('Manufacturing Settings').as_dict()
    print(json.dumps(result, ensure_ascii=False, default=str))
finally:
    frappe.db.rollback()
    frappe.destroy()
