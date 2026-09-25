# V-18 segment 2: run zelin's `setup_tax_template` VERBATIM against the company
# built in 1b, with the account-number typos in tax_template.json LEFT AS-IS
# (sales P13含税 says 222105, sales P13未税 says 22210005; the chart has 2221005).
#
# Three questions the待验表 asks:
#   1. do the two 13% Sales templates (含税 / 未税) exist at all?
#   2. if so, what exactly does account_head point to -- the correct
#      `2221005 销项税额`, or a freshly-created stray `222105` / `22210005`?
#   3. is there an Error Log row for
#      china_company_default.utils.setup_tax_template (i.e. did the bare
#      `except` actually fire)?
#
# Run (cwd MUST be .../sites):
#   docker exec -i -w /workspace/frappe-bench/sites erx001-frappe-1 \
#     /workspace/frappe-bench/env/bin/python /workspace/Spike/V18-seg2-tax-template.py

import json

import frappe

SITE = "erx.localhost"
COMPANY = "V18原生乙"
OUT = "/workspace/Spike/V18-out/seg2-tax-template.json"

result = {"segment": "2 tax template with the account-number bug UNFIXED"}


def rec(k, v):
    result[k] = v
    print(f"[{k}] {v}", flush=True)


frappe.init(site=SITE)
frappe.connect()
frappe.set_user("Administrator")

if not frappe.db.exists("Company", COMPANY):
    rec("precondition_ERROR", f"{COMPANY} missing -- run V18-seg1b first")
    frappe.destroy()
    raise SystemExit(2)

rec("company_chart_of_accounts", frappe.db.get_value("Company", COMPANY, "chart_of_accounts"))
rec("accounts_before", frappe.db.count("Account", {"company": COMPANY}))
rec("error_log_count_before", frappe.db.count("Error Log"))
rec("tax_categories_before", frappe.get_all("Tax Category", pluck="name"))
rec("sales_templates_before", frappe.get_all(
    "Sales Taxes and Charges Template", filters={"company": COMPANY}, fields=["name", "title"]))

# the buggy numbers, as they stand in the JSON
for num in ("222105", "22210005", "2221005"):
    rec(f"account_number_{num}_exists_before", frappe.get_all(
        "Account", filters={"company": COMPANY, "account_number": num},
        fields=["name", "account_name", "root_type"]))
rec("accounts_named_销项税额_before", frappe.get_all(
    "Account", filters={"company": COMPANY, "account_name": "销项税额"},
    fields=["name", "account_number", "root_type", "is_group"]))

# ---- confirm the payload really still carries the typos ---------------------
import erx_v18.chart_of_accounts.company_default.utils as app_utils
import os

tpl_path = os.path.join(os.path.dirname(app_utils.__file__), "tax_template.json")
with open(tpl_path, encoding="utf-8") as f:
    tpl = json.load(f)
sales = tpl["chart_of_accounts"]["小企业会计准则(2024)"]["sales_tax_templates"]
rec("payload_sales_entries", [
    {
        "title": t["title"],
        "account_number": t["taxes"][0]["account_head"].get("account_number"),
        "account_name": t["taxes"][0]["account_head"].get("account_name"),
        "tax_rate": t["taxes"][0]["account_head"].get("tax_rate"),
    }
    for t in sales
])

# ---- run it, unmodified ----------------------------------------------------
rec("call", "erx_v18...company_default.utils.setup_tax_template(company)")
app_utils.setup_tax_template(COMPANY)
frappe.db.commit()
rec("call_returned", "no exception propagated (function has a bare except)")

# ---- Q3: did the bare except fire? -----------------------------------------
rec("error_log_count_after", frappe.db.count("Error Log"))
rec("error_logs_matching_setup_tax_template", frappe.get_all(
    "Error Log",
    filters={"error": ("like", "%setup_tax_template%")},
    fields=["name", "method", "creation"], order_by="creation desc", limit=10))
rec("error_logs_method_matching", frappe.get_all(
    "Error Log",
    filters={"method": ("like", "%setup_tax_template%")},
    fields=["name", "method", "creation"], order_by="creation desc", limit=10))
rec("error_logs_all_recent", frappe.get_all(
    "Error Log", fields=["name", "method", "creation"], order_by="creation desc", limit=10))

# ---- Q1 + Q2: templates and where their account_head points ----------------
rec("tax_categories_after", frappe.get_all("Tax Category", pluck="name"))

for dt, child_dt in (
    ("Sales Taxes and Charges Template", "Sales Taxes and Charges"),
    ("Purchase Taxes and Charges Template", "Purchase Taxes and Charges"),
):
    heads = frappe.get_all(
        dt, filters={"company": COMPANY},
        fields=["name", "title", "tax_category", "is_default"], order_by="title")
    rows = []
    for h in heads:
        kids = frappe.get_all(
            child_dt, filters={"parent": h["name"], "parenttype": dt},
            fields=["idx", "charge_type", "account_head", "rate",
                    "included_in_print_rate", "description", "cost_center"],
            order_by="idx")
        rows.append({"template": h, "taxes": kids})
    rec(f"{dt}__rows", rows)

# spotlight the two 13% sales templates
for title in ("P13专票含税", "P13专票未税"):
    name = frappe.db.get_value(
        "Sales Taxes and Charges Template", {"company": COMPANY, "title": title}, "name")
    rec(f"Q1_template_{title}_exists", bool(name))
    if name:
        kids = frappe.get_all(
            "Sales Taxes and Charges",
            filters={"parent": name, "parenttype": "Sales Taxes and Charges Template"},
            fields=["account_head", "rate", "included_in_print_rate", "description"], order_by="idx")
        rec(f"Q2_account_head_{title}", kids)
        for k in kids:
            if k["account_head"]:
                rec(f"Q2_account_head_{title}_detail", frappe.db.get_value(
                    "Account", k["account_head"],
                    ["name", "account_name", "account_number", "root_type",
                     "account_type", "parent_account", "is_group"], as_dict=True))

# ---- did a stray account get created? --------------------------------------
for num in ("222105", "22210005"):
    rec(f"stray_account_number_{num}_after", frappe.get_all(
        "Account", filters={"company": COMPANY, "account_number": num},
        fields=["name", "account_name", "root_type", "parent_account", "creation"]))
rec("accounts_named_销项税额_after", frappe.get_all(
    "Account", filters={"company": COMPANY, "account_name": "销项税额"},
    fields=["name", "account_number", "root_type", "parent_account", "is_group"]))
rec("accounts_after", frappe.db.count("Account", {"company": COMPANY}))
rec("accounts_added_by_segment2", frappe.db.count("Account", {"company": COMPANY}) - result["accounts_before"])
rec("newest_accounts", frappe.get_all(
    "Account", filters={"company": COMPANY},
    fields=["name", "account_name", "account_number", "root_type", "parent_account", "creation"],
    order_by="creation desc", limit=8))

# baseline company must be untouched -- but note zelin's 含税 UPDATE is not
# scoped to a company, so check it explicitly
rec("baseline_company_accounts", frappe.db.count("Account", {"company": "华东弹簧"}))
rec("baseline_company_sales_templates", frappe.get_all(
    "Sales Taxes and Charges Template", filters={"company": "华东弹簧"}, fields=["name", "title"]))
rec("baseline_included_in_print_rate_rows", frappe.db.sql(
    "select c.parent, c.account_head, c.included_in_print_rate from `tabSales Taxes and Charges` c "
    "join `tabSales Taxes and Charges Template` h on h.name=c.parent where h.company=%s", "华东弹簧"))

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=1, default=str)
print(f"\nwrote {OUT}", flush=True)

frappe.destroy()
