# V-18 segment 4: read-only forensics on the company 1b built, to pin down the
# numbers the待验表 asks for exactly, and to check the quality boundary that a
# bare "it did not raise" would hide.
#
# Specifically:
#   - reconcile 266 JSON nodes vs the Account rows actually created
#   - locate every account the native flow added that is NOT from the JSON
#   - the six roots, their root_type and report_type
#   - all 20 of 2221001..2221020 and which parent each landed under
#     (the待验表 premise says all 20 sit under 2221000; the JSON actually splits
#      them 10 under 2221000 + 10 under 2221 -- record the real shape)
#   - what the native default-account assignment picked (Receivable / Payable /
#     Income / Expense), since a tree that builds cleanly can still be wired up
#     badly
#   - Financial Report Templates, the thing 1a crashed on
#   - baseline company 华东弹簧 untouched, in full
#
# Writes nothing. Run (cwd MUST be .../sites):
#   docker exec -i -w /workspace/frappe-bench/sites erx001-frappe-1 \
#     /workspace/frappe-bench/env/bin/python /workspace/Spike/V18-seg4-forensics.py

import json
import os

import frappe

SITE = "erx.localhost"
COMPANY = "V18原生乙"
CHART = "小企业会计准则(2024)"
OUT = "/workspace/Spike/V18-out/seg4-forensics.json"

result = {"segment": "4 read-only forensics"}


def rec(k, v):
    result[k] = v
    print(f"[{k}] {v}", flush=True)


frappe.init(site=SITE)
frappe.connect()

from erx_v18.chart_of_accounts.custom_accounts import custom_account as app_mod

tree = app_mod.get_chart(CHART)

META = {
    "account_name", "account_number", "account_type", "account_category",
    "root_type", "is_group", "tax_rate", "account_currency",
}

json_nodes = []  # (account_number, account_name)


def walk(node):
    for k, v in node.items():
        if k in META:
            continue
        if isinstance(v, dict):
            json_nodes.append((str(v.get("account_number") or "").strip(), k))
            walk(v)


for k, v in tree.items():
    json_nodes.append((str(v.get("account_number") or "").strip(), k))
    walk(v)

rec("json_node_count", len(json_nodes))
rec("json_number_duplicates", sorted({n for n, _ in json_nodes if [x for x, _ in json_nodes].count(n) > 1}))

db_rows = frappe.get_all(
    "Account", filters={"company": COMPANY},
    fields=["name", "account_name", "account_number", "root_type", "report_type",
            "is_group", "account_type", "parent_account", "creation"],
    order_by="creation")
rec("db_account_count", len(db_rows))

json_pairs = {(n, nm) for n, nm in json_nodes}
db_pairs = {((r["account_number"] or "").strip(), r["account_name"]) for r in db_rows}
rec("in_json_not_in_db", sorted(json_pairs - db_pairs))
extra = sorted(db_pairs - json_pairs)
rec("in_db_not_in_json", extra)
rec("in_db_not_in_json_detail", [
    {k: r[k] for k in ("name", "account_name", "account_number", "root_type",
                       "account_type", "parent_account", "creation")}
    for r in db_rows if ((r["account_number"] or "").strip(), r["account_name"]) in set(extra)])

# six roots
rec("ROOTS", [
    {k: r[k] for k in ("account_number", "account_name", "root_type", "report_type", "is_group")}
    for r in sorted(db_rows, key=lambda r: r["account_number"] or "")
    if not r["parent_account"]])

# the 20 VAT detail lines, with real parents
vat = []
for i in range(1, 21):
    num = f"22210{i:02d}"
    hit = [r for r in db_rows if (r["account_number"] or "").strip() == num]
    vat.append({
        "account_number": num,
        "present": bool(hit),
        "account_name": hit[0]["account_name"] if hit else None,
        "parent_account": hit[0]["parent_account"] if hit else None,
        "account_type": hit[0]["account_type"] if hit else None,
        "root_type": hit[0]["root_type"] if hit else None,
    })
rec("VAT_20_lines", vat)
rec("VAT_present_count", sum(1 for v in vat if v["present"]))
rec("VAT_parent_histogram", {
    p: sum(1 for v in vat if v["parent_account"] == p) for p in {v["parent_account"] for v in vat}})

# how the native flow wired the company up
rec("company_default_fields", frappe.db.get_value(
    "Company", COMPANY,
    ["default_receivable_account", "default_payable_account", "default_income_account",
     "default_expense_account", "default_cash_account", "default_bank_account",
     "round_off_account", "default_inventory_account", "stock_adjustment_account",
     "cost_center", "enable_perpetual_inventory", "chart_of_accounts", "country",
     "default_currency", "abbr"],
    as_dict=True))

for at in ("Receivable", "Payable", "Tax", "Bank", "Cash", "Stock", "Cost of Goods Sold",
           "Income Account", "Expense Account", "Depreciation", "Round Off"):
    hits = [
        {"account_number": r["account_number"], "account_name": r["account_name"], "name": r["name"]}
        for r in db_rows if r["account_type"] == at and not r["is_group"]]
    rec(f"accounts_with_account_type_{at.replace(' ', '_')}", {"count": len(hits), "first_5": hits[:5]})

rec("root_type_histogram", frappe.db.sql(
    "select root_type, count(*) from tabAccount where company=%s group by root_type order by root_type",
    COMPANY))
rec("report_type_histogram", frappe.db.sql(
    "select report_type, count(*) from tabAccount where company=%s group by report_type", COMPANY))
rec("is_group_histogram", frappe.db.sql(
    "select is_group, count(*) from tabAccount where company=%s group by is_group", COMPANY))
rec("nsm_bad_rows", frappe.db.sql(
    "select count(*) from tabAccount where company=%s and (lft is null or rgt is null or lft>=rgt)",
    COMPANY))
rec("nsm_root_span", frappe.db.sql(
    "select min(lft), max(rgt) from tabAccount where company=%s", COMPANY))
rec("accounts_with_empty_account_number", [
    {"name": r["name"], "account_name": r["account_name"], "parent_account": r["parent_account"]}
    for r in db_rows if not (r["account_number"] or "").strip()])

# what 1a crashed on
rec("financial_report_template_count", frappe.db.count("Financial Report Template"))
rec("financial_report_templates", frappe.get_all(
    "Financial Report Template", pluck="name", limit=40))

# cost centers, warehouses, fiscal artifacts
rec("cost_centers", frappe.get_all("Cost Center", filters={"company": COMPANY}, fields=["name", "is_group"]))
rec("warehouses", frappe.get_all("Warehouse", filters={"company": COMPANY}, fields=["name", "account"]))
rec("departments_count", frappe.db.count("Department", {"company": COMPANY}))

# ---- baseline company must be fully intact ---------------------------------
rec("BASELINE_accounts", frappe.db.count("Account", {"company": "华东弹簧"}))
rec("BASELINE_gl_entries", frappe.db.count("GL Entry", {"company": "华东弹簧"}))
rec("BASELINE_stock_ledger_entries", frappe.db.count("Stock Ledger Entry", {"company": "华东弹簧"}))
rec("BASELINE_bom", frappe.db.count("BOM"))
rec("BASELINE_work_orders", frappe.db.count("Work Order"))
rec("BASELINE_sales_orders", frappe.db.count("Sales Order"))
rec("BASELINE_items", frappe.db.count("Item"))
rec("BASELINE_warehouses", frappe.db.count("Warehouse", {"company": "华东弹簧"}))
rec("BASELINE_company_row", frappe.db.get_value(
    "Company", "华东弹簧",
    ["abbr", "country", "default_currency", "chart_of_accounts",
     "default_receivable_account", "default_payable_account"], as_dict=True))
rec("BASELINE_sales_tax_templates", frappe.get_all(
    "Sales Taxes and Charges Template", filters={"company": "华东弹簧"}, fields=["name", "title"]))
rec("all_companies", frappe.get_all("Company", fields=["name", "abbr", "chart_of_accounts"]))
rec("error_log_count", frappe.db.count("Error Log"))

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=1, default=str)
print(f"\nwrote {OUT}", flush=True)

frappe.destroy()
