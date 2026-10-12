# TS-023 第 9 步：恢复 A 后核清洁状态（只读）
import os, json, frappe
os.chdir('/workspace/frappe-bench/sites'); frappe.init(site='erx.localhost', sites_path='.'); frappe.connect()
out = {
    'Translation': frappe.db.count('Translation'),
    'Cash Flow Worksheet': frappe.db.sql('select count(*) from `tabCash Flow Worksheet`')[0][0],
    'companies': frappe.get_all('Company', pluck='name'),
    'accounts_HDTH': frappe.db.count('Account', {'company': '华东弹簧有限公司'}),
    'scheduler_disabled': frappe.utils.scheduler.is_scheduler_disabled(),
}
prefix = {}
for dt, field in [('Item', 'item_code'), ('Customer', 'customer_name'), ('Supplier', 'supplier_name'), ('Warehouse', 'warehouse_name'),
                  ('Employee', 'first_name'), ('Workstation', 'workstation_name'), ('Operation', 'name'), ('Routing', 'routing_name'), ('CRM Lead', 'first_name')]:
    prefix[dt] = frappe.db.count(dt, {field: ['like', '_S6R6%']})
out['_S6R6_prefix'] = prefix
for dt in ['GL Entry', 'Stock Ledger Entry', 'Sales Invoice', 'Purchase Invoice', 'Journal Entry', 'Payment Entry', 'Stock Entry', 'Work Order', 'Sales Order', 'Purchase Order', 'BOM', 'Month End Closing Voucher', 'CRM Deal']:
    out[dt] = frappe.db.count(dt)
print(json.dumps(out, ensure_ascii=False, indent=1))
frappe.destroy()
