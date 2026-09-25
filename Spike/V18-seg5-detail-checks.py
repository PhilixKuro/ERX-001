# V-18 segment 5: read-only follow-ups on two things segment 4 surfaced.
#
#  (a) the one Account that exists in the DB but not in the JSON: `VAT - V18B`,
#      no account number, parented under 2221000 应交增值税.  Where did it come
#      from -- the chart, or erpnext's own native tax setup?  (erpnext's
#      country_wise_tax.json has China -> {"China Tax": {"account_name": "VAT",
#      "tax_rate": 17.0}}, and Company.on_update calls
#      create_default_tax_template() whenever frappe.flags.country_change, which
#      get_or_create_account() would then satisfy by creating a `VAT` account.)
#
#  (b) which accounts the native default-account wiring picked, and why they
#      look wrong: default_receivable_account landed on 2203 预收账款 (a
#      *liability*, customer prepayments) rather than 1122 应收账款, and
#      default_payable_account on 2211010 职工工资 (payroll) rather than 2202
#      应付账款.  Company.create_default_accounts() uses
#      frappe.db.get_value("Account", {...account_type: Receivable...}) with NO
#      order_by, so it takes whatever the DB hands back first.
#
# Writes nothing.  Run (cwd MUST be .../sites):
#   docker exec -i -w /workspace/frappe-bench/sites erx001-frappe-1 \
#     /workspace/frappe-bench/env/bin/python /workspace/Spike/V18-seg5-detail-checks.py

import io
import json

import frappe

SITE = "erx.localhost"
COMPANY = "V18原生乙"
OUT = "/workspace/Spike/V18-out/seg5-detail-checks.json"

result = {"segment": "5 detail checks on the extra VAT account and default-account picks"}


def rec(k, v):
    result[k] = v
    print(f"[{k}] {v}", flush=True)


frappe.init(site=SITE)
frappe.connect()

# ---- (a) where did `VAT` come from? ----------------------------------------
rec("company_creation", str(frappe.db.get_value("Company", COMPANY, "creation")))
newest = frappe.get_all("Account", filters={"company": COMPANY},
                        fields=["name", "creation"], order_by="creation desc", limit=3)
rec("newest_3_accounts", [(r["name"], str(r["creation"])) for r in newest])
first = frappe.get_all("Account", filters={"company": COMPANY},
                       fields=["name", "creation"], order_by="creation", limit=1)
rec("first_account", (first[0]["name"], str(first[0]["creation"])))
rec("VAT_is_the_last_created", newest[0]["name"] == "VAT - V18B")
rec("VAT_row", frappe.db.get_value(
    "Account", "VAT - V18B",
    ["account_name", "account_number", "root_type", "account_type", "report_type",
     "parent_account", "is_group", "creation"], as_dict=True))

with io.open("/workspace/frappe-bench/apps/erpnext/erpnext/setup/setup_wizard/data/country_wise_tax.json",
             encoding="utf-8") as f:
    cwt = json.load(f)
rec("erpnext_country_wise_tax_China", cwt.get("China"))
rec("native_China_Tax_templates_on_test_company", {
    "sales": frappe.get_all("Sales Taxes and Charges Template",
                            filters={"company": COMPANY, "title": "China Tax"}, pluck="name"),
    "purchase": frappe.get_all("Purchase Taxes and Charges Template",
                               filters={"company": COMPANY, "title": "China Tax"}, pluck="name"),
})
rec("VAT_referenced_by", frappe.db.sql(
    "select parent, parenttype, rate from `tabSales Taxes and Charges` where account_head=%s "
    "union all select parent, parenttype, rate from `tabPurchase Taxes and Charges` where account_head=%s",
    ("VAT - V18B", "VAT - V18B")))
rec("baseline_has_same_shaped_VAT", frappe.db.get_value(
    "Account", {"company": "华东弹簧", "account_name": "VAT"},
    ["name", "account_number", "parent_account", "account_type"], as_dict=True))

# ---- (b) default-account picks ----------------------------------------------
rec("company_defaults", frappe.db.get_value(
    "Company", COMPANY,
    ["default_receivable_account", "default_payable_account", "default_income_account",
     "default_expense_account", "default_cash_account", "default_bank_account",
     "default_inventory_account", "stock_adjustment_account", "round_off_account"],
    as_dict=True))

for at in ("Receivable", "Payable"):
    rec(f"all_{at}_accounts_by_lft", frappe.get_all(
        "Account", filters={"company": COMPANY, "account_type": at, "is_group": 0},
        fields=["name", "account_number", "account_name", "root_type", "lft"], order_by="lft"))
    # exactly what Company.create_default_accounts() does: no order_by at all
    rec(f"unordered_get_value_{at}", frappe.db.get_value(
        "Account", {"company": COMPANY, "account_type": at, "is_group": 0}))

CHART_PATH = ("/workspace/frappe-bench/apps/erx_v18/erx_v18/chart_of_accounts/"
              "custom_accounts/chart_of_accounts/cn_smes_chart_of_accounts2024.json")
with io.open(CHART_PATH, encoding="utf-8") as f:
    tree = json.load(f)["tree"]

META = {"account_name", "account_number", "account_type", "account_category",
        "root_type", "is_group", "tax_rate", "account_currency"}
typed = []


def walk(node, path):
    for k, v in node.items():
        if k in META:
            continue
        if isinstance(v, dict):
            if v.get("account_type"):
                typed.append({"account_number": v.get("account_number"), "account_name": k,
                              "account_type": v.get("account_type"), "path": " > ".join(path)})
            walk(v, path + [k])


walk(tree, [])
rec("JSON_accounts_typed_Receivable", [t for t in typed if t["account_type"] == "Receivable"])
rec("JSON_accounts_typed_Payable", [t for t in typed if t["account_type"] == "Payable"])
rec("JSON_account_type_histogram", {
    t: sum(1 for x in typed if x["account_type"] == t) for t in {x["account_type"] for x in typed}})
rec("JSON_typed_total", len(typed))

# other side effects worth counting
rec("item_default_rows_for_V18", frappe.db.sql(
    "select parent, parenttype, company, expense_account from `tabItem Default` where company like %s",
    "V18%"))
rec("mode_of_payment_accounts_for_V18", frappe.db.sql(
    "select parent, company, default_account from `tabMode of Payment Account` where company like %s", "V18%"))
rec("tax_category_count_site_wide", frappe.db.count("Tax Category"))
rec("tax_rule_count", frappe.db.count("Tax Rule"))
rec("item_tax_templates", frappe.get_all("Item Tax Template", fields=["name", "company"]))

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=1, default=str)
print(f"\nwrote {OUT}", flush=True)

frappe.destroy()
