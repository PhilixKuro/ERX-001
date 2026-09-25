# V-19 segment 3: the boundaries the SA Spec demands before any `go`.
#
#   3.1 repeat on_update -- re-save() company #1, no duplicate accounts, no error
#   3.2 a SECOND company on the same chart -- suffixing and cross-company isolation
#   3.3 error path -- country=China but chart_of_accounts='Standard' (NOT in
#       china_coa), so before_insert's `if` does not hold and
#       ignore_chart_of_accounts is never set, while on_update's creation branch
#       runs regardless of chart_of_accounts.  Which chart lands?  Does either
#       creation path run twice?
#
#   existing_company is deliberately NOT exercised -- recorded as untouched.
#
#   docker exec -i -w /workspace/frappe-bench/sites erx001-frappe-1 \
#     /workspace/frappe-bench/env/bin/python /workspace/Spike/V19-seg3-boundaries.py

import json
import sys
import traceback

import frappe

SITE = "erx.localhost"
C1 = "V19A案一"
A1 = "V19A"
C2 = "V19A案二"
A2 = "V19B"
C3 = "V19A案三"
A3 = "V19C"
CHART = "小企业会计准则(2024)"
BASE = "华东弹簧"
OUT = "/workspace/Spike/V19-out/seg3-boundaries.json"

result = {"segment": "3 boundaries: repeat on_update / second company / error path"}


def rec(k, v):
    result[k] = v
    print("[" + k + "] " + repr(v), flush=True)


frappe.init(site=SITE)
frappe.connect()
frappe.set_user("Administrator")
frappe.flags.in_test = False

# ============ 3.1 repeat on_update ==========================================
before = {
    "accounts_c1": frappe.db.count("Account", {"company": C1}),
    "accounts_total": frappe.db.count("Account"),
    "warehouses_c1": frappe.db.count("Warehouse", {"company": C1}),
    "cost_centers_c1": frappe.db.count("Cost Center", {"company": C1}),
    "departments_c1": frappe.db.count("Department", {"company": C1}),
    "sales_templates_c1": frappe.db.count("Sales Taxes and Charges Template", {"company": C1}),
    "purchase_templates_c1": frappe.db.count("Purchase Taxes and Charges Template", {"company": C1}),
    "tax_rules": frappe.db.count("Tax Rule"),
    "tax_categories": frappe.db.count("Tax Category"),
    "error_logs": frappe.db.count("Error Log"),
}
rec("resave_before", before)
rec("resave_defaults_before", frappe.db.get_value(
    C1 and "Company", C1,
    ["default_receivable_account", "default_payable_account", "default_income_account",
     "default_bank_account", "default_inventory_account", "round_off_account"], as_dict=True))

# a FRESH get_doc -- so the in-memory-only `erpnext_china_in_insert` attribute
# that company_after_insert set is gone (Company has no such docfield)
doc1 = frappe.get_doc("Company", C1)
rec("resave_has_in_insert_attr", doc1.get("erpnext_china_in_insert"))
rec("resave_field_exists_in_meta",
    bool(frappe.get_meta("Company").get_field("erpnext_china_in_insert")))

try:
    doc1.save()
    frappe.db.commit()
    rec("resave_result", "NO EXCEPTION")
    result["resave_failed"] = False
except Exception as e:
    frappe.db.rollback()
    result["resave_failed"] = True
    rec("resave_result", "RAISED")
    rec("resave_exception", type(e).__name__ + ": " + str(e))
    result["resave_traceback"] = traceback.format_exc()
    print(result["resave_traceback"], flush=True)

after = {
    "accounts_c1": frappe.db.count("Account", {"company": C1}),
    "accounts_total": frappe.db.count("Account"),
    "warehouses_c1": frappe.db.count("Warehouse", {"company": C1}),
    "cost_centers_c1": frappe.db.count("Cost Center", {"company": C1}),
    "departments_c1": frappe.db.count("Department", {"company": C1}),
    "sales_templates_c1": frappe.db.count("Sales Taxes and Charges Template", {"company": C1}),
    "purchase_templates_c1": frappe.db.count("Purchase Taxes and Charges Template", {"company": C1}),
    "tax_rules": frappe.db.count("Tax Rule"),
    "tax_categories": frappe.db.count("Tax Category"),
    "error_logs": frappe.db.count("Error Log"),
}
rec("resave_after", after)
rec("resave_delta", dict((k, after[k] - before[k]) for k in before))
rec("resave_defaults_after", frappe.db.get_value(
    "Company", C1,
    ["default_receivable_account", "default_payable_account", "default_income_account",
     "default_bank_account", "default_inventory_account", "round_off_account"], as_dict=True))
rec("resave_duplicate_suffix_accounts", frappe.db.sql(
    "select account_number, account_name from tabAccount where company=%s "
    "and account_name regexp ' [0-9]+$'", C1))
rec("resave_nsm_bad_rows", frappe.db.sql(
    "select count(*) from tabAccount where lft is null or rgt is null or lft>=rgt")[0][0])

# ============ 3.2 a second company on the same chart ========================
if frappe.db.exists("Company", C2):
    rec("c2_precondition", "already exists; skipping creation")
else:
    doc2 = frappe.get_doc({
        "doctype": "Company", "company_name": C2, "abbr": A2,
        "default_currency": "CNY", "country": "China", "chart_of_accounts": CHART,
        "create_chart_of_accounts_based_on": "Standard Template",
    })
    try:
        doc2.insert()
        frappe.db.commit()
        rec("c2_insert_result", "NO EXCEPTION")
        result["c2_insert_failed"] = False
    except Exception as e:
        frappe.db.rollback()
        result["c2_insert_failed"] = True
        rec("c2_insert_result", "RAISED")
        rec("c2_exception", type(e).__name__ + ": " + str(e))
        result["c2_traceback"] = traceback.format_exc()
        print(result["c2_traceback"], flush=True)

rec("c2_accounts", frappe.db.count("Account", {"company": C2}))
rec("c1_accounts_after_c2", frappe.db.count("Account", {"company": C1}))
rec("c2_roots", frappe.get_all("Account", filters={"company": C2, "parent_account": ("in", ["", None])},
                               fields=["name", "account_number", "root_type"], order_by="account_number"))
rec("c2_duplicate_suffix_accounts", frappe.db.sql(
    "select account_number, account_name from tabAccount where company=%s "
    "and account_name regexp ' [0-9]+$'", C2))
rec("c2_names_all_carry_abbr", frappe.db.sql(
    "select count(*) from tabAccount where company=%s and name not like %s", (C2, "%- " + A2))[0][0])
rec("c1_names_all_carry_abbr", frappe.db.sql(
    "select count(*) from tabAccount where company=%s and name not like %s", (C1, "%- " + A1))[0][0])
rec("cross_company_parent_refs_c2", frappe.db.sql(
    "select count(*) from tabAccount a join tabAccount b on b.name=a.parent_account "
    "where a.company=%s and b.company!=%s", (C2, C2))[0][0])
rec("cross_company_parent_refs_c1", frappe.db.sql(
    "select count(*) from tabAccount a join tabAccount b on b.name=a.parent_account "
    "where a.company=%s and b.company!=%s", (C1, C1))[0][0])
rec("c2_vs_c1_pair_diff", frappe.db.sql(
    "select count(*) from ("
    " select account_number, account_name from tabAccount where company=%s"
    " union all"
    " select account_number, account_name from tabAccount where company=%s"
    ") t group by account_number, account_name having count(*) != 2", (C1, C2)))
rec("c2_defaults", frappe.db.get_value(
    "Company", C2,
    ["default_receivable_account", "default_payable_account", "default_income_account",
     "default_bank_account", "default_inventory_account", "round_off_account"], as_dict=True))
rec("c2_side_effects", {
    "warehouses": frappe.db.count("Warehouse", {"company": C2}),
    "cost_centers": frappe.db.count("Cost Center", {"company": C2}),
    "departments": frappe.db.count("Department", {"company": C2}),
    "sales_templates": frappe.db.count("Sales Taxes and Charges Template", {"company": C2}),
    "purchase_templates": frappe.db.count("Purchase Taxes and Charges Template", {"company": C2}),
})
rec("tax_categories_after_c2", frappe.db.count("Tax Category"))
rec("nsm_bad_rows_after_c2", frappe.db.sql(
    "select count(*) from tabAccount where lft is null or rgt is null or lft>=rgt")[0][0])
rec("error_logs_after_c2", frappe.db.count("Error Log"))

# ============ 3.3 error path: country=China, chart_of_accounts='Standard' ====
# before_insert's `if chart in china_coa` is FALSE, so ignore_chart_of_accounts
# is never set and erpnext's own on_update creation branch runs
# (sync_financial_report_templates + create_default_accounts).  Then zelin's
# company_on_update ALSO runs -- but its guard is `not exists Account for this
# company`, which by then is False, so the second creation should be skipped.
# Whether that holds is exactly what this measures.
frt_before_c3 = frappe.db.count("Financial Report Template")
err_before_c3 = frappe.db.count("Error Log")
rec("c3_frt_before", frt_before_c3)
rec("c3_error_logs_before", err_before_c3)

if frappe.db.exists("Company", C3):
    rec("c3_precondition", "already exists; skipping creation")
else:
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
        print("=== C3 TRACEBACK BEGIN ===", flush=True)
        print(result["c3_traceback"], flush=True)
        print("=== C3 TRACEBACK END ===", flush=True)

rec("c3_company_exists", bool(frappe.db.exists("Company", C3)))
rec("c3_accounts", frappe.db.count("Account", {"company": C3}))
rec("c3_chart_field", frappe.db.get_value("Company", C3, "chart_of_accounts")
    if frappe.db.exists("Company", C3) else None)
rec("c3_roots", frappe.get_all("Account", filters={"company": C3, "parent_account": ("in", ["", None])},
                               fields=["name", "account_number", "account_name", "root_type"],
                               order_by="name"))
# which chart landed?  the Standard chart has English root names
# (Application of Funds / Source of Funds / Income / Expenses), the Chinese one
# has 资产类/负债类/权益类/成本类/收入类/费用类
rec("c3_has_chinese_roots", frappe.db.sql(
    "select count(*) from tabAccount where company=%s and account_name in "
    "('资产类','负债类','权益类','成本类','收入类','费用类')", C3)[0][0])
rec("c3_sample_accounts", frappe.get_all("Account", filters={"company": C3},
                                         fields=["name", "account_number", "account_name",
                                                 "root_type", "is_group"],
                                         order_by="lft", limit=15))
rec("c3_duplicate_suffix_accounts", frappe.db.sql(
    "select account_number, account_name from tabAccount where company=%s "
    "and account_name regexp ' [0-9]+$'", C3))
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
rec("c3_frt_after", frappe.db.count("Financial Report Template"))
rec("c3_frt_delta", frappe.db.count("Financial Report Template") - frt_before_c3)
rec("c3_error_logs_after", frappe.db.count("Error Log"))
rec("c3_error_logs_new", frappe.db.sql(
    "select name, method, creation, left(error,400) from `tabError Log` "
    "where date(creation)=curdate() order by creation desc"))

# ============ untouched / final state =======================================
rec("UNTOUCHED_existing_company_path",
    "not exercised: no company was created with existing_company set")
rec("UNTOUCHED_hrms_same_hook", "hrms not installed; not exercised (LG-101)")
rec("installed_apps", frappe.get_installed_apps())

rec("nsm_bad_rows_site_wide_final", frappe.db.sql(
    "select count(*) from tabAccount where lft is null or rgt is null or lft>=rgt")[0][0])
rec("account_count_total_final", frappe.db.count("Account"))
rec("companies_final", frappe.get_all("Company", fields=["name", "abbr", "country",
                                                         "chart_of_accounts"]))
rec("BASELINE_accounts_final", frappe.db.count("Account", {"company": BASE}))
rec("BASELINE_gl_entries_final", frappe.db.count("GL Entry", {"company": BASE}))
rec("BASELINE_sles_final", frappe.db.count("Stock Ledger Entry", {"company": BASE}))
rec("BASELINE_row_final", frappe.db.get_value(
    "Company", BASE,
    ["abbr", "country", "default_currency", "chart_of_accounts",
     "default_receivable_account", "default_payable_account", "default_cash_account",
     "default_bank_account", "default_inventory_account", "default_income_account",
     "round_off_account"], as_dict=True))

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=1, default=str)
print("wrote " + OUT, flush=True)

frappe.destroy()
