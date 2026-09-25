# V-19 segment 0: baseline snapshot taken BEFORE the test app is installed.
#
# Everything the later segments diff against comes from here, so it must run
# first and must write nothing.
#
# Run (cwd MUST be .../sites, else frappe's logger dies on a relative path):
#   docker exec -i -w /workspace/frappe-bench/sites erx001-frappe-1 \
#     /workspace/frappe-bench/env/bin/python /workspace/Spike/V19-seg0-baseline.py

import json

import frappe

SITE = "erx.localhost"
BASE = "华东弹簧"
OUT = "/workspace/Spike/V19-out/seg0-baseline.json"

result = {"segment": "0 baseline before app install"}


def rec(k, v):
    result[k] = v
    print(f"[{k}] {v}", flush=True)


frappe.init(site=SITE)
frappe.connect()

rec("installed_apps", frappe.get_installed_apps())
rec("hook_doc_events_Company", frappe.get_hooks("doc_events", {}).get("Company", "ABSENT"))
rec("hook_override_whitelisted_methods", frappe.get_hooks("override_whitelisted_methods", {}))

for dt in ("Account", "Company", "Error Log", "Tax Category", "Financial Report Template",
           "Item Tax Template", "Sales Taxes and Charges Template",
           "Purchase Taxes and Charges Template", "Tax Rule", "Cost Center",
           "Warehouse", "Department", "GL Entry", "Stock Ledger Entry",
           "BOM", "Work Order", "Sales Order", "Item"):
    rec(f"count_{dt}", frappe.db.count(dt))

rec("companies", frappe.get_all("Company", fields=["name", "abbr", "country", "chart_of_accounts"]))
rec("financial_report_templates", frappe.get_all(
    "Financial Report Template", fields=["name", "module", "report_type"], order_by="name"))
rec("tax_categories", frappe.get_all("Tax Category", pluck="name"))
rec("error_logs", frappe.get_all("Error Log", fields=["name", "method", "creation"],
                                 order_by="creation desc", limit=10))

# baseline company, item by item
rec("BASELINE_accounts", frappe.db.count("Account", {"company": BASE}))
rec("BASELINE_gl_entries", frappe.db.count("GL Entry", {"company": BASE}))
rec("BASELINE_stock_ledger_entries", frappe.db.count("Stock Ledger Entry", {"company": BASE}))
rec("BASELINE_boms", frappe.db.count("BOM", {"company": BASE}))
rec("BASELINE_work_orders", frappe.db.count("Work Order", {"company": BASE}))
rec("BASELINE_sales_orders", frappe.db.count("Sales Order", {"company": BASE}))
rec("BASELINE_items", frappe.db.count("Item"))
rec("BASELINE_warehouses", frappe.db.count("Warehouse", {"company": BASE}))
rec("BASELINE_cost_centers", frappe.db.count("Cost Center", {"company": BASE}))
rec("BASELINE_departments", frappe.db.count("Department", {"company": BASE}))
rec("BASELINE_company_row", frappe.db.get_value(
    "Company", BASE,
    ["abbr", "country", "default_currency", "chart_of_accounts",
     "default_receivable_account", "default_payable_account", "default_cash_account",
     "default_bank_account", "default_inventory_account", "default_income_account",
     "round_off_account"], as_dict=True))
rec("BASELINE_sales_templates", frappe.get_all(
    "Sales Taxes and Charges Template", filters={"company": BASE}, fields=["name", "title"]))
rec("BASELINE_VAT_account", frappe.db.get_value(
    "Account", {"company": BASE, "account_name": "VAT"},
    ["name", "account_number", "parent_account", "account_type", "root_type"], as_dict=True))

rec("default_company_global", frappe.db.get_default("company"))
rec("global_defaults_default_company", frappe.db.get_single_value("Global Defaults", "default_company"))
rec("global_defaults_demo_company", frappe.db.get_single_value("Global Defaults", "demo_company"))
rec("nsm_bad_account_rows", frappe.db.sql(
    "select count(*) from tabAccount where lft is null or rgt is null or lft>=rgt"))

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=1, default=str)
print(f"\nwrote {OUT}", flush=True)

frappe.destroy()
