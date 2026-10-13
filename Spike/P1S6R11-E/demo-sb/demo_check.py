# R11 E：演示站只读核查（不写库、不 commit）。容器内：env/bin/python /workspace/Spike/P1S6R11-E/demo-sb/demo_check.py
import os, sys, json, frappe
os.chdir('/workspace/frappe-bench/sites'); frappe.init(site='erx.localhost', sites_path='.'); frappe.connect()
frappe.local.lang = 'zh'
from frappe_china.install import check_app_order
from frappe_china.translation_check import find_problems
o = check_app_order(); o = o if isinstance(o, dict) else o.__dict__
out = {'installed_apps': frappe.get_installed_apps(),
       'check_app_order': o, 'find_problems': find_problems(),
       'Translation': frappe.db.sql('select count(*) from tabTranslation')[0][0],
       'CFW': frappe.db.sql('select count(*) from `tabCash Flow Worksheet`')[0][0],
       'companies': frappe.db.sql('select name, chart_of_accounts from tabCompany'),
       'accounts_by_company': frappe.db.sql('select company, count(*) from tabAccount group by company'),
       }
# 全表扫前缀：所有含 name 的业务表里 name/标题字段 like _S6R%
hits = {}
tables = [r[0] for r in frappe.db.sql("select table_name from information_schema.tables where table_schema=database() and table_name like 'tab%%'")]
for t in tables:
    cols = [r[0] for r in frappe.db.sql("select column_name from information_schema.columns where table_schema=database() and table_name=%s and data_type in ('varchar','text','longtext','smalltext')", t)]
    want = [c for c in cols if c in ('name','title','item_code','item_name','customer','customer_name','supplier','supplier_name','production_item','first_name','lead_name','company','warehouse_name','workstation_name','routing_name','employee_name','party','party_name','item','parent')]
    for c in want:
        n = frappe.db.sql(f"select count(*) from `{t}` where `{c}` like %s", ('%\_S6R%',))[0][0]
        if n: hits[f'{t}.{c}'] = n
out['prefix_S6R_hits'] = hits
counts = {}
for t in ['tabGL Entry','tabStock Ledger Entry','tabPayment Ledger Entry','tabSales Invoice','tabPurchase Invoice','tabJournal Entry','tabPayment Entry','tabStock Entry','tabWork Order','tabSales Order','tabPurchase Order','tabBOM','tabJob Card','tabDelivery Note','tabPurchase Receipt','tabQuotation','tabProduction Plan','tabMonth End Closing Voucher','tabItem','tabCustomer','tabSupplier','tabCRM Lead','tabCRM Deal','tabEmployee','tabWorkstation','tabOperation','tabRouting','tabWarehouse','tabVersion','tabDeleted Document']:
    try: counts[t] = frappe.db.sql(f'select count(*) from `{t}`')[0][0]
    except Exception as e: counts[t] = repr(e)
out['counts'] = counts
out['business_flow_sidebar'] = frappe.db.sql("select name, modified from `tabWorkspace Sidebar` where name='Business Flow'")
out['patch_log_china'] = frappe.db.sql("select count(*) from `tabPatch Log` where patch like 'frappe_china%%'")
print(json.dumps(out, ensure_ascii=False, indent=1, default=str))
frappe.db.rollback(); frappe.destroy()
