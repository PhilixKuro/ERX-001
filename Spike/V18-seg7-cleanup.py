# V-18 segment 7: cleanup + verification.
#
# Deleting the test company is safe here on the criteria Company.on_trash cares
# about (checked in segment 6): 0 GL Entry, 0 Stock Ledger Entry, is_group=0, no
# parent_company, not Global Defaults' default_company, not demo_company.
#
# Two things on_trash does NOT clean, and this script handles explicitly:
#   - Tax Category is not company-scoped, so the 7 categories zelin's
#     from_detailed_data() created survive.  They are removed here (they were
#     created by this probe: site had 0 before, see segment 1 baseline).
#   - the Sales/Purchase Taxes and Charges Template rows are deleted with raw
#     `frappe.db.sql`, which does not cascade to their child rows in
#     `tabSales Taxes and Charges` / `tabPurchase Taxes and Charges`.  Orphans
#     are detected and removed.
#
# Run (cwd MUST be .../sites):
#   docker exec -i -w /workspace/frappe-bench/sites erx001-frappe-1 \
#     /workspace/frappe-bench/env/bin/python /workspace/Spike/V18-seg7-cleanup.py

import json

import frappe

SITE = "erx.localhost"
COMPANY = "V18原生乙"
ABBR = "V18B"
PROBE_TAX_CATEGORIES = [
    "P13专票含税", "P3专票含税", "P1专票含税",
    "P13专票未税", "P3专票未税", "P1专票未税", "P0无税",
]
OUT = "/workspace/Spike/V18-out/seg7-cleanup.json"

result = {"segment": "7 cleanup and verification"}


def rec(k, v):
    result[k] = v
    print(f"[{k}] {v}", flush=True)


frappe.init(site=SITE)
frappe.connect()
frappe.set_user("Administrator")

# ---- safety gates -----------------------------------------------------------
gates = {
    "gl_entries": frappe.db.count("GL Entry", {"company": COMPANY}),
    "stock_ledger_entries": frappe.db.count("Stock Ledger Entry", {"company": COMPANY}),
    "is_group": frappe.db.get_value("Company", COMPANY, "is_group"),
    "parent_company": frappe.db.get_value("Company", COMPANY, "parent_company"),
    "is_global_default_company": frappe.db.get_single_value("Global Defaults", "default_company") == COMPANY,
    "is_demo_company": frappe.db.get_single_value("Global Defaults", "demo_company") == COMPANY,
    "child_companies": frappe.get_all("Company", filters={"parent_company": COMPANY}, pluck="name"),
}
rec("safety_gates", gates)
blocked = (gates["gl_entries"] or gates["stock_ledger_entries"] or gates["is_group"]
           or gates["parent_company"] or gates["is_global_default_company"]
           or gates["is_demo_company"] or gates["child_companies"])
if blocked:
    rec("DECISION", "NOT deleting -- a safety gate tripped; leaving company in place")
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=1, default=str)
    frappe.destroy()
    raise SystemExit(1)

rec("accounts_before_delete", frappe.db.count("Account", {"company": COMPANY}))
rec("baseline_accounts_before_delete", frappe.db.count("Account", {"company": "华东弹簧"}))

# ---- delete the company -----------------------------------------------------
try:
    frappe.delete_doc("Company", COMPANY, force=False, ignore_permissions=True)
    frappe.db.commit()
    rec("delete_company", "OK")
except Exception as e:
    frappe.db.rollback()
    import traceback
    rec("delete_company", "FAILED")
    rec("delete_exception", repr(e))
    result["delete_traceback"] = traceback.format_exc()
    print(result["delete_traceback"], flush=True)

rec("company_exists_after_delete", bool(frappe.db.exists("Company", COMPANY)))

# ---- residue that on_trash does not handle ---------------------------------
rec("accounts_left_for_company", frappe.db.count("Account", {"company": COMPANY}))
rec("accounts_left_by_abbr_suffix", frappe.db.sql(
    "select count(*) from tabAccount where name like %s", f"%- {ABBR}"))
rec("cost_centers_left", frappe.db.sql(
    "select name from `tabCost Center` where company=%s or name like %s", (COMPANY, f"%- {ABBR}")))
rec("warehouses_left", frappe.db.sql(
    "select name from tabWarehouse where company=%s or name like %s", (COMPANY, f"%- {ABBR}")))
rec("departments_left", frappe.db.sql(
    "select name from tabDepartment where company=%s or name like %s", (COMPANY, f"%- {ABBR}")))
rec("sales_templates_left", frappe.db.sql(
    "select name from `tabSales Taxes and Charges Template` where company=%s", COMPANY))
rec("purchase_templates_left", frappe.db.sql(
    "select name from `tabPurchase Taxes and Charges Template` where company=%s", COMPANY))
rec("item_tax_templates_left", frappe.db.sql(
    "select name from `tabItem Tax Template` where company=%s", COMPANY))
rec("mode_of_payment_accounts_left", frappe.db.sql(
    "select parent, company from `tabMode of Payment Account` where company=%s", COMPANY))

# orphan child rows of the raw-SQL-deleted tax templates
for child, parent_dt in (
    ("Sales Taxes and Charges", "Sales Taxes and Charges Template"),
    ("Purchase Taxes and Charges", "Purchase Taxes and Charges Template"),
):
    orphans = frappe.db.sql(
        f"select c.name, c.parent, c.account_head from `tab{child}` c "
        f"where c.parenttype=%s and not exists "
        f"(select 1 from `tab{parent_dt}` p where p.name=c.parent)", parent_dt)
    rec(f"orphan_{child.replace(' ', '_')}_rows", orphans)
    if orphans:
        frappe.db.sql(
            f"delete from `tab{child}` where parenttype=%s and parent not in "
            f"(select name from `tab{parent_dt}`)", parent_dt)
        frappe.db.commit()
        rec(f"orphan_{child.replace(' ', '_')}_deleted", len(orphans))
    rec(f"orphan_{child.replace(' ', '_')}_after", frappe.db.sql(
        f"select count(*) from `tab{child}` c where c.parenttype=%s and not exists "
        f"(select 1 from `tab{parent_dt}` p where p.name=c.parent)", parent_dt))

# Tax Category: not company-scoped, survives on_trash.  Site had 0 before this probe.
for tc in PROBE_TAX_CATEGORIES:
    if frappe.db.exists("Tax Category", tc):
        try:
            frappe.delete_doc("Tax Category", tc, ignore_permissions=True)
        except Exception as e:
            rec(f"tax_category_delete_FAILED_{tc}", repr(e))
frappe.db.commit()
rec("tax_categories_after", frappe.get_all("Tax Category", pluck="name"))
rec("tax_category_count_after", frappe.db.count("Tax Category"))

# ---- baseline company must be exactly as it was ----------------------------
rec("BASELINE_accounts", frappe.db.count("Account", {"company": "华东弹簧"}))
rec("BASELINE_gl_entries", frappe.db.count("GL Entry", {"company": "华东弹簧"}))
rec("BASELINE_stock_ledger_entries", frappe.db.count("Stock Ledger Entry", {"company": "华东弹簧"}))
rec("BASELINE_bom", frappe.db.count("BOM"))
rec("BASELINE_work_orders", frappe.db.count("Work Order"))
rec("BASELINE_sales_orders", frappe.db.count("Sales Order"))
rec("BASELINE_items", frappe.db.count("Item"))
rec("BASELINE_warehouses", frappe.db.count("Warehouse", {"company": "华东弹簧"}))
rec("BASELINE_cost_centers", frappe.db.count("Cost Center", {"company": "华东弹簧"}))
rec("BASELINE_departments", frappe.db.count("Department", {"company": "华东弹簧"}))
rec("BASELINE_sales_templates", frappe.get_all(
    "Sales Taxes and Charges Template", filters={"company": "华东弹簧"}, fields=["name", "title"]))
rec("BASELINE_item_tax_templates", frappe.get_all(
    "Item Tax Template", filters={"company": "华东弹簧"}, pluck="name"))
rec("BASELINE_company_row", frappe.db.get_value(
    "Company", "华东弹簧",
    ["abbr", "country", "default_currency", "chart_of_accounts",
     "default_receivable_account", "default_payable_account", "default_cash_account"], as_dict=True))
rec("companies_all", frappe.get_all("Company", fields=["name", "abbr", "lft", "rgt"]))
rec("default_company_global", frappe.db.get_default("company"))
rec("global_defaults_default_company", frappe.db.get_single_value("Global Defaults", "default_company"))
rec("financial_report_template_count", frappe.db.count("Financial Report Template"))
rec("error_log_count", frappe.db.count("Error Log"))
rec("nsm_bad_company_rows", frappe.db.sql(
    "select count(*) from tabCompany where lft is null or rgt is null or lft>=rgt"))
rec("nsm_bad_account_rows", frappe.db.sql(
    "select count(*) from tabAccount where lft is null or rgt is null or lft>=rgt"))

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=1, default=str)
print(f"\nwrote {OUT}", flush=True)

frappe.destroy()
