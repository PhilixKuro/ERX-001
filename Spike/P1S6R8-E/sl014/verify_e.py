# E 只读核演示站清洁状态（不写库、不清缓存）
import os, json, frappe
os.chdir('/workspace/frappe-bench/sites'); frappe.init(site='erx.localhost', sites_path='.'); frappe.connect()
try:
    out = {'Translation': frappe.db.count('Translation'),
           'CFW': frappe.db.sql('select count(*) from `tabCash Flow Worksheet`')[0][0],
           'GL': frappe.db.count('GL Entry'), 'SLE': frappe.db.count('Stock Ledger Entry'),
           'Stock Reconciliation': frappe.db.count('Stock Reconciliation'),
           'companies': frappe.get_all('Company', pluck='name'),
           'accounts_HDTH': frappe.db.count('Account', {'company': '华东弹簧有限公司'})}
    # 前缀：扫所有含 name 的业务表，name 或常见标题字段 like '%S6R6%'
    hits = {}
    for dt in ['Item','Customer','Supplier','Warehouse','Employee','Workstation','Operation','Routing','CRM Lead','CRM Deal','Company','Item Price','UOM','Raven Channel','Contact','Address','Project']:
        try:
            n = frappe.db.sql(f"select count(*) from `tab{dt}` where name like '%%S6R6%%'")[0][0]
            if n: hits[dt] = n
        except Exception as e: hits[dt] = 'err ' + str(e)[:60]
    out['S6R6_name_hits'] = hits
    from frappe_china.install import check_app_order
    r = check_app_order()
    out['check_app_order'] = {k: (v if not isinstance(v, (list, dict)) else v) for k, v in (r.items() if isinstance(r, dict) else vars(r).items())} if r else r
    from frappe_china import translation_check
    out['translation_check'] = translation_check.find_problems()
finally:
    frappe.db.rollback()
print(json.dumps(out, ensure_ascii=False, indent=1, default=str))
frappe.destroy()
