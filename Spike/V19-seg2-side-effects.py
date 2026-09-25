# V-19 segment 2: side-effect reconciliation, option A vs the V-18 native run.
# For every item: 多出 / 少掉 / 相同 relative to the native baseline.
#
# The V-18 native numbers are carried here as constants so the diff is computed,
# not eyeballed.  Read-only apart from nothing -- this segment writes no data.
#
#   docker exec -i -w /workspace/frappe-bench/sites erx001-frappe-1 \
#     /workspace/frappe-bench/env/bin/python /workspace/Spike/V19-seg2-side-effects.py

import io
import json
import os

import frappe

SITE = "erx.localhost"
COMPANY = "V19A案一"
ABBR = "V19A"
BASE = "华东弹簧"
OUT = "/workspace/Spike/V19-out/seg2-side-effects.json"

# --- V-18 native baseline (from Spike/V18-out, recorded in 待验表 row V-18) ---
V18 = {
    "accounts": 267,
    "json_nodes": 266,
    "extra_account": "VAT - V18B",
    "warehouses": 5,
    "cost_centers": 2,
    "departments": 13,
    "financial_report_templates": 6,
    "error_log_count": 1,
    "default_receivable_account": "2203 - 预收账款",
    "default_payable_account": "2211010 - 职工工资",
    "default_inventory_account": "1421 消耗性生物资产",
    "default_bank_account": "1012 其他货币资金",
    "default_income_account": None,
    "round_off_account": None,
    "tax_categories": 7,
    "sales_templates": 5,
    "purchase_templates": 5,
}

result = {"segment": "2 side effects, option A vs V-18 native", "V18_baseline": V18}


def rec(k, v):
    result[k] = v
    print("[" + k + "] " + repr(v), flush=True)


def cmp(label, a_val, native_val):
    if a_val == native_val:
        verdict = "相同"
    else:
        verdict = "不同"
    rec("CMP_" + label, {"A": a_val, "native_V18": native_val, "verdict": verdict})


frappe.init(site=SITE)
frappe.connect()

# ============ Q1. the unnumbered 17% VAT account + country_change ============
vat = frappe.db.get_value(
    "Account", {"company": COMPANY, "account_name": "VAT"},
    ["name", "account_number", "parent_account", "account_type", "root_type", "tax_rate"],
    as_dict=True)
rec("A_VAT_account", vat)
cmp("VAT_account_present", bool(vat), True)

# any account at all in this company that is not in the chart JSON?
rec("A_accounts_with_empty_number", frappe.get_all(
    "Account", filters={"company": COMPANY, "account_number": ("in", ["", None])},
    fields=["name", "account_name", "parent_account", "account_type"]))

# what created the native one: Company.create_default_tax_template() reading
# erpnext's country_wise_tax.json, gated on frappe.flags.country_change
with io.open("/workspace/frappe-bench/apps/erpnext/erpnext/setup/setup_wizard/data/"
             "country_wise_tax.json", encoding="utf-8") as f:
    rec("erpnext_country_wise_tax_China", json.load(f).get("China"))

rec("A_native_China_Tax_templates", {
    "sales": frappe.get_all("Sales Taxes and Charges Template",
                            filters={"company": COMPANY, "title": "China Tax"}, pluck="name"),
    "purchase": frappe.get_all("Purchase Taxes and Charges Template",
                               filters={"company": COMPANY, "title": "China Tax"}, pluck="name"),
})

# install_country_fixtures: does a China module even exist to import?
REG = "/workspace/frappe-bench/apps/erpnext/erpnext/regional"
rec("erpnext_regional_dirs", sorted([d for d in os.listdir(REG)
                                     if os.path.isdir(os.path.join(REG, d))]))
rec("erpnext_regional_china_exists", os.path.isdir(os.path.join(REG, "china")))
rec("scrub_China", frappe.scrub("China"))
try:
    frappe.get_attr("erpnext.regional.china.setup.setup")
    rec("install_country_fixtures_import", "IMPORTED (unexpected)")
except ImportError as e:
    rec("install_country_fixtures_import", "ImportError -> silently passed: " + str(e))
except Exception as e:
    rec("install_country_fixtures_import", type(e).__name__ + ": " + str(e))

# ============ Q2. the six default accounts ==================================
# NOTE: v16 tabCompany has no default_payroll_payable_account and no
# stock_received_but_not_billed column; the list below is what the schema has.
DEFAULT_FIELDS = ["default_receivable_account", "default_payable_account",
                  "default_inventory_account", "default_bank_account",
                  "default_income_account", "round_off_account",
                  "default_cash_account", "default_expense_account",
                  "stock_adjustment_account", "default_provisional_account",
                  "write_off_account", "default_discount_account",
                  "exchange_gain_loss_account", "default_operating_cost_account",
                  "cost_center", "round_off_cost_center", "default_finance_book"]
defaults = frappe.db.get_value("Company", COMPANY, DEFAULT_FIELDS, as_dict=True)
rec("A_company_defaults", defaults)

SIX = ["default_receivable_account", "default_payable_account",
       "default_inventory_account", "default_bank_account",
       "default_income_account", "round_off_account"]
six_cmp = {}
for f in SIX:
    a = defaults.get(f)
    n = V18.get(f)
    # V-18 recorded the human-readable "<number> - <name>"; compare on the
    # number+name prefix so the abbr suffix does not create a false difference
    a_short = None
    if a:
        parts = a.split(" - ")
        if parts and parts[-1] == ABBR:
            a_short = " - ".join(parts[:-1])
        else:
            a_short = a
    six_cmp[f] = {"A_raw": a, "A_short": a_short, "native_V18": n,
                  "same": (a_short == n) if (a_short and n) else (a_short == n)}
rec("A_six_defaults_vs_native", six_cmp)

# what set_company_default's CSV asked for, and whether the account exists
CSV = ("/workspace/frappe-bench/apps/erx_v19/erx_v19/chart_of_accounts/"
       "company_default/default_accounts.csv")
import csv as _csv
wanted = []
with io.open(CSV, encoding="utf-8") as f:
    for row in _csv.reader(f):
        if len(row) >= 2 and row[0].strip():
            wanted.append((row[0].strip(), row[1].strip()))
rec("csv_row_count", len(wanted))
csv_check = []
for field, acct_name in wanted:
    hit = frappe.db.get_value("Account", {"company": COMPANY, "account_name": acct_name,
                                          "is_group": 0}, "name")
    csv_check.append({"field": field, "csv_account_name": acct_name,
                      "resolved": hit,
                      "is_current_value": (defaults.get(field) == hit) if hit else None})
rec("csv_field_resolution", csv_check)
unresolved = [c for c in csv_check if not c["resolved"]]
rec("csv_rows_unresolved_count", len(unresolved))
rec("csv_rows_unresolved", unresolved)

# which accounts the native unordered get_value would have picked
for at in ("Receivable", "Payable", "Bank", "Cash", "Stock", "Round Off"):
    rec("unordered_pick_" + at.replace(" ", "_"), frappe.db.get_value(
        "Account", {"company": COMPANY, "account_type": at, "is_group": 0}))

# ============ Q3. Error Log: did the bare `except` fire? =====================
rec("A_error_log_count", frappe.db.count("Error Log"))
cmp("error_log_count", frappe.db.count("Error Log"), V18["error_log_count"])
rec("A_error_logs_all", frappe.get_all(
    "Error Log", fields=["name", "method", "creation"], order_by="creation desc", limit=20))
rec("A_error_logs_set_company_default", frappe.db.sql(
    "select name, creation, left(error, 400) from `tabError Log` "
    "where error like %s order by creation desc", "%set company default%"))
rec("A_error_logs_company_on_update_method", frappe.db.sql(
    "select name, creation, left(error, 400) from `tabError Log` "
    "where method like %s order by creation desc", "%company_on_update%"))
rec("A_error_logs_create_charts2", frappe.db.sql(
    "select name, creation, left(error, 400) from `tabError Log` "
    "where error like %s order by creation desc", "%create_charts2%"))
rec("A_error_logs_today", frappe.db.sql(
    "select name, method, creation, left(error, 300) from `tabError Log` "
    "where date(creation) = curdate() order by creation desc"))

# ============ Q4. warehouses / cost centers / departments / templates =======
counts = {
    "warehouses": frappe.db.count("Warehouse", {"company": COMPANY}),
    "cost_centers": frappe.db.count("Cost Center", {"company": COMPANY}),
    "departments": frappe.db.count("Department", {"company": COMPANY}),
}
rec("A_side_effect_counts", counts)
cmp("warehouses", counts["warehouses"], V18["warehouses"])
cmp("cost_centers", counts["cost_centers"], V18["cost_centers"])
cmp("departments", counts["departments"], V18["departments"])

rec("A_warehouses", frappe.get_all("Warehouse", filters={"company": COMPANY},
                                   fields=["name", "is_group", "warehouse_type", "account"]))
rec("A_cost_centers", frappe.get_all("Cost Center", filters={"company": COMPANY},
                                     fields=["name", "is_group"]))

# Financial Report Template is NOT company-scoped: sync_financial_report_templates
# is skipped in option A (ignore_chart_of_accounts short-circuits it), so the
# question is whether the site-wide count moved at all.
frt = frappe.get_all("Financial Report Template", fields=["name", "module"], order_by="name")
rec("A_financial_report_templates", frt)
rec("A_financial_report_template_count", len(frt))
cmp("financial_report_templates", len(frt), V18["financial_report_templates"])
rec("frt_has_company_field", bool(frappe.get_meta("Financial Report Template").get_field("company")))

# ============ tax side: what set_company_default's setup_tax_template built ==
sales = frappe.get_all("Sales Taxes and Charges Template",
                       filters={"company": COMPANY}, fields=["name", "title", "tax_category"])
purch = frappe.get_all("Purchase Taxes and Charges Template",
                       filters={"company": COMPANY}, fields=["name", "title", "tax_category"])
rec("A_sales_templates", sales)
rec("A_purchase_templates", purch)
cmp("sales_template_count", len(sales), V18["sales_templates"])
cmp("purchase_template_count", len(purch), V18["purchase_templates"])
rec("A_tax_categories_site_wide", frappe.get_all("Tax Category", pluck="name"))
cmp("tax_category_count", frappe.db.count("Tax Category"), V18["tax_categories"])
rec("A_tax_rules", frappe.get_all("Tax Rule", filters={"company": COMPANY},
                                  fields=["name", "tax_category", "sales_tax_template",
                                          "purchase_tax_template"]))
rec("A_item_tax_templates", frappe.get_all("Item Tax Template",
                                           filters={"company": COMPANY}, fields=["name"]))
rec("A_tax_template_account_heads", frappe.db.sql(
    "select parenttype, parent, account_head, rate from `tabSales Taxes and Charges` "
    "where parent in (select name from `tabSales Taxes and Charges Template` where company=%s) "
    "union all "
    "select parenttype, parent, account_head, rate from `tabPurchase Taxes and Charges` "
    "where parent in (select name from `tabPurchase Taxes and Charges Template` where company=%s)",
    (COMPANY, COMPANY)))
rec("A_mode_of_payment_accounts", frappe.db.sql(
    "select parent, company, default_account from `tabMode of Payment Account` where company=%s",
    COMPANY))
rec("A_item_group_defaults", frappe.db.sql(
    "select parent, parenttype, company, income_account, expense_account "
    "from `tabItem Default` where company=%s", COMPANY))

# ============ the baseline company must be untouched ========================
rec("BASELINE_accounts", frappe.db.count("Account", {"company": BASE}))
rec("BASELINE_row", frappe.db.get_value("Company", BASE, DEFAULT_FIELDS, as_dict=True))
rec("BASELINE_warehouses", frappe.db.count("Warehouse", {"company": BASE}))
rec("BASELINE_cost_centers", frappe.db.count("Cost Center", {"company": BASE}))
rec("BASELINE_departments", frappe.db.count("Department", {"company": BASE}))
rec("BASELINE_gl_entries", frappe.db.count("GL Entry", {"company": BASE}))
rec("BASELINE_sles", frappe.db.count("Stock Ledger Entry", {"company": BASE}))

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=1, default=str)
print("wrote " + OUT, flush=True)

frappe.destroy()
