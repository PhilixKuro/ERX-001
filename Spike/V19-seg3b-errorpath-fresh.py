# V-19 segment 3b: re-run boundary 3.3 in a FRESH process.
#
# In segment 3 the error-path company was created after two China companies in
# the same process, and nothing ever resets
# frappe.local.flags.ignore_chart_of_accounts -- company_before_insert sets it
# and company_on_update sets it to 1, so by the time the third company inserted
# the flag was still 1 and erpnext's own creation branch was skipped.  That made
# zelin's branch the only chart builder, and it crashed.
#
# This process starts with the flag unset, which is what a real HTTP request
# would see (frappe.local is per-request), so it measures the un-leaked
# behaviour.  Both results are reportable: the leaked one is what a script or a
# bulk import inside one process gets.
#
#   docker exec -i -w /workspace/frappe-bench/sites erx001-frappe-1 \
#     /workspace/frappe-bench/env/bin/python /workspace/Spike/V19-seg3b-errorpath-fresh.py

import json
import traceback

import frappe

SITE = "erx.localhost"
C3 = "V19A案三"
A3 = "V19C"
BASE = "华东弹簧"
OUT = "/workspace/Spike/V19-out/seg3b-errorpath-fresh.json"

result = {"segment": "3b error path in a fresh process (no flag leakage)"}


def rec(k, v):
    result[k] = v
    print("[" + k + "] " + repr(v), flush=True)


frappe.init(site=SITE)
frappe.connect()
frappe.set_user("Administrator")
frappe.flags.in_test = False

rec("flag_ignore_coa_at_start", frappe.local.flags.get("ignore_chart_of_accounts", "unset"))
rec("flag_country_change_at_start", frappe.flags.get("country_change", "unset"))
rec("accounts_total_before", frappe.db.count("Account"))
rec("frt_before", frappe.db.count("Financial Report Template"))
rec("error_logs_before", frappe.db.count("Error Log"))
rec("c3_exists_before", bool(frappe.db.exists("Company", C3)))

doc3 = frappe.get_doc({
    "doctype": "Company", "company_name": C3, "abbr": A3,
    "default_currency": "CNY", "country": "China", "chart_of_accounts": "Standard",
    "create_chart_of_accounts_based_on": "Standard Template",
})
try:
    doc3.insert()
    frappe.db.commit()
    rec("c3_insert_result", "NO EXCEPTION")
    result["c3_insert_failed"] = False
except Exception as e:
    frappe.db.rollback()
    result["c3_insert_failed"] = True
    rec("c3_insert_result", "RAISED")
    rec("c3_exception_type", type(e).__name__)
    rec("c3_exception", str(e))
    result["c3_traceback"] = traceback.format_exc()
    print("=== C3B TRACEBACK BEGIN ===", flush=True)
    print(result["c3_traceback"], flush=True)
    print("=== C3B TRACEBACK END ===", flush=True)

rec("flag_ignore_coa_after", frappe.local.flags.get("ignore_chart_of_accounts", "unset"))
rec("flag_country_change_after", frappe.flags.get("country_change", "unset"))
rec("c3_company_exists", bool(frappe.db.exists("Company", C3)))
rec("c3_accounts", frappe.db.count("Account", {"company": C3}))
rec("accounts_total_after", frappe.db.count("Account"))
rec("c3_roots", frappe.get_all("Account",
                               filters={"company": C3, "parent_account": ("in", ["", None])},
                               fields=["name", "account_number", "account_name", "root_type"],
                               order_by="name"))
rec("c3_chinese_root_count", frappe.db.sql(
    "select count(*) from tabAccount where company=%s and account_name in "
    "('资产类','负债类','权益类','成本类','收入类','费用类')", C3)[0][0])
rec("c3_english_root_count", frappe.db.sql(
    "select count(*) from tabAccount where company=%s and account_name in "
    "('Application of Funds (Assets)','Source of Funds (Liabilities)','Income','Expenses','Equity')",
    C3)[0][0])
rec("c3_duplicate_suffix_accounts", frappe.db.sql(
    "select account_number, account_name from tabAccount where company=%s "
    "and account_name regexp ' [0-9]+$'", C3))
rec("c3_duplicate_suffix_count", frappe.db.sql(
    "select count(*) from tabAccount where company=%s and account_name regexp ' [0-9]+$'",
    C3)[0][0])
rec("c3_VAT_account", frappe.db.get_value(
    "Account", {"company": C3, "account_name": "VAT"},
    ["name", "account_number", "parent_account", "account_type", "tax_rate"], as_dict=True))
rec("c3_defaults", frappe.db.get_value(
    "Company", C3,
    ["default_receivable_account", "default_payable_account", "default_income_account",
     "default_bank_account", "default_inventory_account", "round_off_account",
     "default_cash_account", "default_expense_account"], as_dict=True)
    if frappe.db.exists("Company", C3) else None)
rec("c3_side_effects", {
    "warehouses": frappe.db.count("Warehouse", {"company": C3}),
    "cost_centers": frappe.db.count("Cost Center", {"company": C3}),
    "departments": frappe.db.count("Department", {"company": C3}),
    "sales_templates": frappe.db.count("Sales Taxes and Charges Template", {"company": C3}),
    "purchase_templates": frappe.db.count("Purchase Taxes and Charges Template", {"company": C3}),
})
rec("c3_account_category_populated", frappe.db.sql(
    "select count(*) from tabAccount where company=%s and account_category is not null "
    "and account_category != ''", C3)[0][0])
rec("frt_after", frappe.db.count("Financial Report Template"))
rec("error_logs_after", frappe.db.count("Error Log"))
rec("error_logs_today", frappe.db.sql(
    "select name, method, creation, left(error,300) from `tabError Log` "
    "where date(creation)=curdate() order by creation desc"))
rec("nsm_bad_rows_site_wide", frappe.db.sql(
    "select count(*) from tabAccount where lft is null or rgt is null or lft>=rgt")[0][0])
rec("BASELINE_accounts", frappe.db.count("Account", {"company": BASE}))
rec("companies", frappe.get_all("Company", fields=["name", "abbr", "chart_of_accounts"]))

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=1, default=str)
print("wrote " + OUT, flush=True)

frappe.destroy()
