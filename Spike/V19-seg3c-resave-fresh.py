# V-19 segment 3c: boundary 3.1 (repeat on_update) re-run in a FRESH process.
#
# Segment 3 did the re-save in the same process that had just created two China
# companies, and frappe.flags IS frappe.local.flags (verified), so
# ignore_chart_of_accounts was still 1 from company_before_insert -- erpnext's
# own `if not ignore_chart_of_accounts` guards at company.py:346 and :362 were
# therefore skipped for reasons that had nothing to do with the re-save.
#
# Here the flag starts unset, which is what a desk save (one request, fresh
# frappe.local) actually sees.  Company #2 has never been re-saved, so it is the
# clean subject; company #1 is re-saved again afterwards for comparison.
#
#   docker exec -i -w /workspace/frappe-bench/sites erx001-frappe-1 \
#     /workspace/frappe-bench/env/bin/python /workspace/Spike/V19-seg3c-resave-fresh.py

import json
import traceback

import frappe

SITE = "erx.localhost"
C2 = "V19A案二"
BASE = "华东弹簧"
OUT = "/workspace/Spike/V19-out/seg3c-resave-fresh.json"

FIELDS = ["default_receivable_account", "default_payable_account", "default_income_account",
          "default_bank_account", "default_inventory_account", "round_off_account",
          "default_cash_account", "default_expense_account", "stock_adjustment_account"]

result = {"segment": "3c repeat on_update in a fresh process"}


def rec(k, v):
    result[k] = v
    print("[" + k + "] " + repr(v), flush=True)


def snap(company):
    return {
        "accounts": frappe.db.count("Account", {"company": company}),
        "accounts_total": frappe.db.count("Account"),
        "warehouses": frappe.db.count("Warehouse", {"company": company}),
        "cost_centers": frappe.db.count("Cost Center", {"company": company}),
        "departments": frappe.db.count("Department", {"company": company}),
        "sales_templates": frappe.db.count("Sales Taxes and Charges Template", {"company": company}),
        "purchase_templates": frappe.db.count("Purchase Taxes and Charges Template", {"company": company}),
        "tax_rules": frappe.db.count("Tax Rule"),
        "tax_categories": frappe.db.count("Tax Category"),
        "error_logs": frappe.db.count("Error Log"),
        "frt": frappe.db.count("Financial Report Template"),
        "dup_suffix": frappe.db.sql(
            "select count(*) from tabAccount where company=%s and account_name regexp ' [0-9]+$'",
            company)[0][0],
    }


frappe.init(site=SITE)
frappe.connect()
frappe.set_user("Administrator")
frappe.flags.in_test = False

rec("flag_ignore_coa_at_start", frappe.local.flags.get("ignore_chart_of_accounts", "unset"))
rec("flag_country_change_at_start", frappe.flags.get("country_change", "unset"))
rec("flags_are_same_object", frappe.flags is frappe.local.flags)

before = snap(C2)
rec("before", before)
rec("defaults_before", frappe.db.get_value("Company", C2, FIELDS, as_dict=True))

doc = frappe.get_doc("Company", C2)
rec("has_in_insert_attr", doc.get("erpnext_china_in_insert"))
try:
    doc.save()
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

after = snap(C2)
rec("after", after)
rec("delta", dict((k, after[k] - before[k]) for k in before))
rec("defaults_after", frappe.db.get_value("Company", C2, FIELDS, as_dict=True))
rec("flag_ignore_coa_after", frappe.local.flags.get("ignore_chart_of_accounts", "unset"))
rec("flag_country_change_after", frappe.flags.get("country_change", "unset"))
rec("defaults_changed", dict(
    (f, (before_v, after_v)) for f, before_v, after_v in
    [(f, result["defaults_before"].get(f), result["defaults_after"].get(f)) for f in FIELDS]
    if before_v != after_v))
rec("dup_suffix_rows_after", frappe.db.sql(
    "select account_number, account_name from tabAccount where company=%s "
    "and account_name regexp ' [0-9]+$'", C2))
rec("nsm_bad_rows_site_wide", frappe.db.sql(
    "select count(*) from tabAccount where lft is null or rgt is null or lft>=rgt")[0][0])
rec("error_logs_today", frappe.db.sql(
    "select name, method, creation, left(error,300) from `tabError Log` "
    "where date(creation)=curdate() order by creation desc"))
rec("BASELINE_accounts", frappe.db.count("Account", {"company": BASE}))

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=1, default=str)
print("wrote " + OUT, flush=True)

frappe.destroy()
