# R9 TS-036：演示站状态核查（只读）。第 2 步上线后、第 8 步恢复 A 后、第 9 步出基准点前各跑一次。
# 用法（容器内）：env/bin/python /workspace/Spike/P1S6R9/verify_clean.py [输出 json 路径]
import os, sys, json, frappe
os.chdir('/workspace/frappe-bench/sites'); frappe.init(site='erx.localhost', sites_path='.'); frappe.connect()
frappe.local.lang = 'zh'
from frappe_china.install import check_app_order
from frappe_china.translation_check import find_problems
order = check_app_order()
order = order if isinstance(order, dict) else getattr(order, '__dict__', {'value': str(order)})
out = {
    'Translation': frappe.db.count('Translation'),
    'Cash Flow Worksheet': frappe.db.sql('select count(*) from `tabCash Flow Worksheet`')[0][0],
    'companies': frappe.get_all('Company', pluck='name'),
    'accounts_HDTH': frappe.db.count('Account', {'company': '华东弹簧有限公司'}),
    'scheduler_disabled': frappe.utils.scheduler.is_scheduler_disabled(),
    'installed_apps': frappe.get_installed_apps(),
    'check_app_order': {k: order.get(k) for k in ('ok', 'order_ok', 'overrides_ok', 'translation_ok', 'company_checks_ok', 'problems') if k in order},
    'find_problems': find_problems(),
}
prefix = {}
for dt, field in [('Item', 'item_code'), ('Customer', 'customer_name'), ('Supplier', 'supplier_name'), ('Warehouse', 'warehouse_name'),
                  ('Employee', 'first_name'), ('Workstation', 'workstation_name'), ('Operation', 'name'), ('Routing', 'routing_name'), ('CRM Lead', 'first_name')]:
    prefix[dt] = {p: frappe.db.count(dt, {field: ['like', p + '%']}) for p in ('_S6R9', '_S6R6')}
out['prefix'] = prefix
for dt in ['GL Entry', 'Stock Ledger Entry', 'Sales Invoice', 'Purchase Invoice', 'Journal Entry', 'Payment Entry', 'Stock Entry', 'Work Order',
           'Sales Order', 'Purchase Order', 'BOM', 'Month End Closing Voucher', 'CRM Deal', 'Job Card']:
    out[dt] = frappe.db.count(dt)
text = json.dumps(out, ensure_ascii=False, indent=1, default=str)
if len(sys.argv) > 1:
    open(sys.argv[1], 'w', encoding='utf-8').write(text + '\n')
print(text)
frappe.destroy()
