# V-19 segment 6: post-uninstall verification.  Read-only.
#
# Confirms the throwaway app left nothing behind and that 华东弹簧 is untouched.
#
# Run (cwd MUST be .../sites):
#   docker exec -i -w /workspace/frappe-bench/sites erx001-frappe-1 \
#     /workspace/frappe-bench/env/bin/python /workspace/Spike/V19-seg6-final-verify.py

import json

import frappe

SITE = "erx.localhost"
APP = "erx_v19"
BASE = "华东弹簧"
OUT = "/workspace/Spike/V19-out/seg6-final-verify.json"

result = {"segment": "6 final verify after uninstall"}


def rec(k, v):
    result[k] = v
    print("[" + k + "] " + repr(v), flush=True)


frappe.init(site=SITE)
frappe.connect()

rec("installed_apps", frappe.get_installed_apps())
rec("app_still_installed", APP in frappe.get_installed_apps())
rec("hook_doc_events_Company", frappe.get_hooks("doc_events", {}).get("Company", "ABSENT"))
rec("hook_override_whitelisted_methods", frappe.get_hooks("override_whitelisted_methods", {}))
rec("module_def_rows", frappe.db.sql("select name, app_name from `tabModule Def` where name like %s or app_name like %s", ("%Erx V19%", "%erx_v19%")))
rec("doctype_rows_erx", frappe.db.sql("select name, module from tabDocType where module like %s", "%Erx V19%"))
rec("installed_application_rows", frappe.db.sql("select app_name from `tabInstalled Application`"))
rec("defaultvalue_rows_erx", frappe.db.sql("select parent, defkey from tabDefaultValue where defkey like %s or defvalue like %s", ("%erx_v19%", "%V19%")))
rec("names_like_V19", {
    dt: frappe.db.sql("select name from `tab" + dt + "` where name like %s", "%V19%")
    for dt in ("Company", "Account", "Cost Center", "Warehouse", "Department",
               "Sales Taxes and Charges Template", "Purchase Taxes and Charges Template",
               "Item Tax Template", "Tax Category", "Tax Rule")
})

rec("account_count_total", frappe.db.count("Account"))
rec("companies", frappe.get_all("Company", fields=["name", "abbr", "lft", "rgt"]))
rec("tax_category_count", frappe.db.count("Tax Category"))
rec("tax_rule_count", frappe.db.count("Tax Rule"))
rec("financial_report_template_count", frappe.db.count("Financial Report Template"))
rec("error_log_count", frappe.db.count("Error Log"))
rec("nsm_bad_account_rows", frappe.db.sql(
    "select count(*) from tabAccount where lft is null or rgt is null or lft>=rgt")[0][0])
rec("nsm_bad_company_rows", frappe.db.sql(
    "select count(*) from tabCompany where lft is null or rgt is null or lft>=rgt")[0][0])

for child, parent_dt in (("Sales Taxes and Charges", "Sales Taxes and Charges Template"),
                         ("Purchase Taxes and Charges", "Purchase Taxes and Charges Template"),
                         ("Item Tax Template Detail", "Item Tax Template")):
    rec("orphan_" + child.replace(" ", "_"), frappe.db.sql(
        "select count(*) from `tab" + child + "` c where c.parenttype=%s and not exists "
        "(select 1 from `tab" + parent_dt + "` p where p.name=c.parent)", parent_dt)[0][0])

rec("BASELINE", {
    "accounts": frappe.db.count("Account", {"company": BASE}),
    "gl_entries": frappe.db.count("GL Entry", {"company": BASE}),
    "stock_ledger_entries": frappe.db.count("Stock Ledger Entry", {"company": BASE}),
    "boms": frappe.db.count("BOM", {"company": BASE}),
    "work_orders": frappe.db.count("Work Order", {"company": BASE}),
    "sales_orders": frappe.db.count("Sales Order", {"company": BASE}),
    "items": frappe.db.count("Item"),
    "warehouses": frappe.db.count("Warehouse", {"company": BASE}),
    "cost_centers": frappe.db.count("Cost Center", {"company": BASE}),
    "departments": frappe.db.count("Department", {"company": BASE}),
    "company_row": frappe.db.get_value(
        "Company", BASE,
        ["abbr", "country", "default_currency", "chart_of_accounts",
         "default_receivable_account", "default_payable_account", "default_cash_account",
         "default_bank_account", "default_inventory_account", "default_income_account",
         "round_off_account"], as_dict=True),
    "sales_templates": frappe.get_all("Sales Taxes and Charges Template",
                                      filters={"company": BASE}, fields=["name", "title"]),
    "item_tax_templates": frappe.get_all("Item Tax Template", fields=["name", "company"]),
    "VAT_account": frappe.db.get_value(
        "Account", {"company": BASE, "account_name": "VAT"},
        ["name", "account_number", "parent_account", "account_type", "root_type"], as_dict=True),
})
rec("default_company_global", frappe.db.get_default("company"))
rec("global_defaults_default_company", frappe.db.get_single_value("Global Defaults", "default_company"))

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=1, default=str)
print("\nwrote " + OUT, flush=True)

frappe.destroy()
