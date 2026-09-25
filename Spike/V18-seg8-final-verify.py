# V-18 segment 8: final residue check after uninstalling the test app.
#
# Mirrors Spike/V16-cleanup-check.py's checklist, plus the Company-side tables
# this probe touched.  Read-only except that it reports; it changes nothing.
#
# Run (cwd MUST be .../sites):
#   docker exec -i -w /workspace/frappe-bench/sites erx001-frappe-1 \
#     /workspace/frappe-bench/env/bin/python /workspace/Spike/V18-seg8-final-verify.py

import json

import frappe

SITE = "erx.localhost"
APP = "erx_v18"
OUT = "/workspace/Spike/V18-out/seg8-final-verify.json"

result = {"segment": "8 final residue verification"}


def rec(k, v):
    result[k] = v
    print(f"[{k}] {v}", flush=True)


frappe.init(site=SITE)
frappe.connect()

rec("installed_apps", frappe.get_installed_apps())
rec("app_in_installed", APP in frappe.get_installed_apps())

# app-owned records
rec("module_def_rows", frappe.db.sql(
    "select name, app_name from `tabModule Def` where app_name=%s or name like %s", (APP, "%Erx V18%")))
rec("doctype_rows", frappe.db.sql("select name, module from tabDocType where module like %s", "%Erx V18%"))
for dt in ("Desktop Icon", "Workspace Sidebar", "Workspace Sidebar Item"):
    try:
        rec(f"{dt}_rows", frappe.db.sql(
            f"select count(*) from `tab{dt}` where name like %s", f"%{APP}%"))
    except Exception as e:
        rec(f"{dt}_rows_ERROR", repr(e))
rec("defaultvalue_rows", frappe.db.sql(
    "select parent, defkey, defvalue from tabDefaultValue where defkey like %s or defvalue like %s",
    (f"%{APP}%", f"%{APP}%")))
rec("installed_application_rows", frappe.db.sql(
    "select value from tabSingles where doctype='Installed Applications' limit 5"))

# company-side residue from the test companies
for abbr in ("V18A", "V18B", "V18C"):
    rec(f"accounts_named_with_{abbr}", frappe.db.sql(
        "select count(*) from tabAccount where name like %s", f"%- {abbr}"))
rec("companies", frappe.get_all("Company", fields=["name", "abbr", "lft", "rgt"]))
rec("company_names_like_V18", frappe.db.sql("select name from tabCompany where name like %s", "%V18%"))
rec("tax_category_count", frappe.db.count("Tax Category"))
rec("tax_categories", frappe.get_all("Tax Category", pluck="name"))
rec("sales_templates_all", frappe.get_all(
    "Sales Taxes and Charges Template", fields=["name", "company"]))
rec("purchase_templates_all", frappe.get_all(
    "Purchase Taxes and Charges Template", fields=["name", "company"]))
rec("item_tax_templates_all", frappe.get_all("Item Tax Template", fields=["name", "company"]))
rec("orphan_sales_charge_rows", frappe.db.sql(
    "select count(*) from `tabSales Taxes and Charges` c where c.parenttype='Sales Taxes and Charges Template' "
    "and not exists (select 1 from `tabSales Taxes and Charges Template` p where p.name=c.parent)"))
rec("orphan_purchase_charge_rows", frappe.db.sql(
    "select count(*) from `tabPurchase Taxes and Charges` c where c.parenttype='Purchase Taxes and Charges Template' "
    "and not exists (select 1 from `tabPurchase Taxes and Charges Template` p where p.name=c.parent)"))

# baseline demo data, full check
rec("BASELINE", {
    "accounts": frappe.db.count("Account", {"company": "华东弹簧"}),
    "gl_entries": frappe.db.count("GL Entry", {"company": "华东弹簧"}),
    "stock_ledger_entries": frappe.db.count("Stock Ledger Entry", {"company": "华东弹簧"}),
    "bom": frappe.db.count("BOM"),
    "work_orders": frappe.db.count("Work Order"),
    "sales_orders": frappe.db.count("Sales Order"),
    "items": frappe.db.count("Item"),
    "warehouses": frappe.db.count("Warehouse", {"company": "华东弹簧"}),
    "cost_centers": frappe.db.count("Cost Center", {"company": "华东弹簧"}),
    "departments": frappe.db.count("Department", {"company": "华东弹簧"}),
    "fiscal_years": frappe.get_all("Fiscal Year", pluck="name"),
})
rec("default_company", frappe.db.get_default("company"))
rec("system_settings_country", frappe.db.get_single_value("System Settings", "country"))
rec("financial_report_template_count", frappe.db.count("Financial Report Template"))
rec("error_log_count", frappe.db.count("Error Log"))
rec("error_logs", frappe.get_all("Error Log", fields=["name", "method", "creation"],
                                 order_by="creation desc", limit=5))
rec("account_count_total", frappe.db.count("Account"))
rec("nsm_bad_account_rows", frappe.db.sql(
    "select count(*) from tabAccount where lft is null or rgt is null or lft>=rgt"))

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=1, default=str)
print(f"\nwrote {OUT}", flush=True)

frappe.destroy()
