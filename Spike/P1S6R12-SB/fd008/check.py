# R12 SB FD-008：zh 下 Standard 科目表根节点与首页 Expenses 图标的译名（只读，不建公司）。
import os, json, frappe
os.chdir('/workspace/frappe-bench/sites'); frappe.init(site='test.localhost', sites_path='.'); frappe.connect()
try:
    frappe.local.lang = 'zh'; frappe.local.lang_full_dict = None
    from erpnext.accounts.doctype.account.chart_of_accounts.verified import standard_chart_of_accounts as std
    roots = list(std.get().keys())
    print(json.dumps({'standard_chart_roots': roots, 'Expenses': frappe._('Expenses')}, ensure_ascii=False))
finally:
    frappe.destroy()
