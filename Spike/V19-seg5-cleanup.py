# V-19 segment 5: cleanup + verification.
#
# Three test companies to remove: V19A案一 / V19A案二 (option A, Chinese chart)
# and V19A案三 (the error-path company, native Standard chart).  Segment 4
# confirmed all three pass every gate Company.on_trash cares about: 0 GL Entry,
# 0 Stock Ledger Entry, is_group=0, no parent_company, no child companies, and
# none of them is Global Defaults' default_company or demo_company (that is
# 华东弹簧, which this script never touches).
#
# What on_trash does NOT clean, handled explicitly here:
#   - Tax Category is not company-scoped, so the 7 categories
#     set_company_default's from_detailed_data() created survive.  The site had 0
#     before this probe (segment 0 baseline), so all 7 are probe-created.
#   - the Sales/Purchase Taxes and Charges Template rows are deleted with raw
#     frappe.db.sql, which does not cascade to their child rows in
#     tabSales Taxes and Charges / tabPurchase Taxes and Charges.
#   - Tax Rule rows point at the templates by name.
#
# If a gate trips, this script deletes NOTHING and reports -- per the brief,
# leaving residue and reporting it beats breaking the site.
#
# Run (cwd MUST be .../sites):
#   docker exec -i -w /workspace/frappe-bench/sites erx001-frappe-1 \
#     /workspace/frappe-bench/env/bin/python /workspace/Spike/V19-seg5-cleanup.py

import json
import traceback

import frappe

SITE = "erx.localhost"
COMPANIES = ["V19A案一", "V19A案二", "V19A案三"]
ABBRS = ["V19A", "V19B", "V19C"]
BASE = "华东弹簧"
PROBE_TAX_CATEGORIES = ["P13专票含税", "P3专票含税", "P1专票含税",
                        "P13专票未税", "P3专票未税", "P1专票未税", "P0无税"]
OUT = "/workspace/Spike/V19-out/seg5-cleanup.json"

result = {"segment": "5 cleanup and verification"}


def rec(k, v):
    result[k] = v
    print("[" + k + "] " + repr(v), flush=True)


frappe.init(site=SITE)
frappe.connect()
frappe.set_user("Administrator")

# ---- safety gates, all three companies, before deleting anything -----------
all_gates = {}
blocked = []
for c in COMPANIES:
    if not frappe.db.exists("Company", c):
        all_gates[c] = "does not exist"
        continue
    g = {
        "gl_entries": frappe.db.count("GL Entry", {"company": c}),
        "stock_ledger_entries": frappe.db.count("Stock Ledger Entry", {"company": c}),
        "is_group": frappe.db.get_value("Company", c, "is_group"),
        "parent_company": frappe.db.get_value("Company", c, "parent_company"),
        "is_global_default_company":
            frappe.db.get_single_value("Global Defaults", "default_company") == c,
        "is_demo_company": frappe.db.get_single_value("Global Defaults", "demo_company") == c,
        "child_companies": frappe.get_all("Company", filters={"parent_company": c}, pluck="name"),
    }
    all_gates[c] = g
    if (g["gl_entries"] or g["stock_ledger_entries"] or g["is_group"] or g["parent_company"]
            or g["is_global_default_company"] or g["is_demo_company"] or g["child_companies"]):
        blocked.append(c)
rec("safety_gates", all_gates)
rec("blocked_companies", blocked)

if blocked:
    rec("DECISION", "NOT deleting anything -- a gate tripped: " + ", ".join(blocked))
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=1, default=str)
    frappe.destroy()
    raise SystemExit(1)

rec("accounts_total_before_delete", frappe.db.count("Account"))
rec("BASELINE_accounts_before_delete", frappe.db.count("Account", {"company": BASE}))

# ---- Tax Rule rows first: they reference the templates ----------------------
probe_rules = frappe.db.sql(
    "select name from `tabTax Rule` where " +
    " or ".join(["sales_tax_template like %s or purchase_tax_template like %s"] * len(ABBRS)),
    tuple(x for a in ABBRS for x in ("%- " + a, "%- " + a)), as_dict=True)
rec("probe_tax_rules_found", [r["name"] for r in probe_rules])
for r in probe_rules:
    try:
        frappe.delete_doc("Tax Rule", r["name"], ignore_permissions=True, force=True)
    except Exception as e:
        rec("tax_rule_delete_FAILED_" + r["name"], repr(e))
frappe.db.commit()
rec("tax_rules_after", frappe.db.count("Tax Rule"))

# ---- delete the companies ---------------------------------------------------
for c in COMPANIES:
    if not frappe.db.exists("Company", c):
        rec("delete_" + c, "already absent")
        continue
    try:
        frappe.delete_doc("Company", c, force=False, ignore_permissions=True)
        frappe.db.commit()
        rec("delete_" + c, "OK")
    except Exception as e:
        frappe.db.rollback()
        rec("delete_" + c, "FAILED: " + type(e).__name__ + ": " + str(e))
        result["delete_traceback_" + c] = traceback.format_exc()
        print(result["delete_traceback_" + c], flush=True)

rec("companies_after_delete", frappe.get_all("Company", fields=["name", "abbr", "lft", "rgt"]))

# ---- residue that on_trash does not handle ---------------------------------
residue = {}
for c, a in zip(COMPANIES, ABBRS):
    residue[a] = {
        "company_exists": bool(frappe.db.exists("Company", c)),
        "accounts_by_company": frappe.db.count("Account", {"company": c}),
        "accounts_by_abbr": frappe.db.sql(
            "select count(*) from tabAccount where name like %s", "%- " + a)[0][0],
        "cost_centers": frappe.db.sql(
            "select name from `tabCost Center` where company=%s or name like %s",
            (c, "%- " + a)),
        "warehouses": frappe.db.sql(
            "select name from tabWarehouse where company=%s or name like %s", (c, "%- " + a)),
        "departments": frappe.db.sql(
            "select name from tabDepartment where company=%s or name like %s", (c, "%- " + a)),
        "sales_templates": frappe.db.sql(
            "select name from `tabSales Taxes and Charges Template` where company=%s or name like %s",
            (c, "%- " + a)),
        "purchase_templates": frappe.db.sql(
            "select name from `tabPurchase Taxes and Charges Template` where company=%s or name like %s",
            (c, "%- " + a)),
        "item_tax_templates": frappe.db.sql(
            "select name from `tabItem Tax Template` where company=%s or name like %s",
            (c, "%- " + a)),
        "item_defaults": frappe.db.sql(
            "select parent, parenttype from `tabItem Default` where company=%s", c),
        "mode_of_payment_accounts": frappe.db.sql(
            "select parent from `tabMode of Payment Account` where company=%s", c),
    }
rec("residue_after_company_delete", residue)

# leftover template rows and their orphan children
for dt, a_list in (("Sales Taxes and Charges Template", ABBRS),
                   ("Purchase Taxes and Charges Template", ABBRS),
                   ("Item Tax Template", ABBRS)):
    left = frappe.db.sql(
        "select name from `tab" + dt + "` where " +
        " or ".join(["name like %s"] * len(a_list)),
        tuple("%- " + a for a in a_list))
    rec("leftover_" + dt.replace(" ", "_"), left)
    for (nm,) in left:
        try:
            frappe.delete_doc(dt, nm, ignore_permissions=True, force=True)
        except Exception as e:
            rec("leftover_delete_FAILED_" + nm, repr(e))
frappe.db.commit()

for child, parent_dt in (("Sales Taxes and Charges", "Sales Taxes and Charges Template"),
                         ("Purchase Taxes and Charges", "Purchase Taxes and Charges Template"),
                         ("Item Tax Template Detail", "Item Tax Template")):
    try:
        orphans = frappe.db.sql(
            "select c.name, c.parent from `tab" + child + "` c where c.parenttype=%s "
            "and not exists (select 1 from `tab" + parent_dt + "` p where p.name=c.parent)",
            parent_dt)
        rec("orphan_" + child.replace(" ", "_"), orphans)
        if orphans:
            frappe.db.sql(
                "delete from `tab" + child + "` where parenttype=%s and parent not in "
                "(select name from `tab" + parent_dt + "`)", parent_dt)
            frappe.db.commit()
            rec("orphan_" + child.replace(" ", "_") + "_deleted", len(orphans))
        rec("orphan_" + child.replace(" ", "_") + "_after", frappe.db.sql(
            "select count(*) from `tab" + child + "` c where c.parenttype=%s and not exists "
            "(select 1 from `tab" + parent_dt + "` p where p.name=c.parent)", parent_dt)[0][0])
    except Exception as e:
        rec("orphan_" + child.replace(" ", "_") + "_ERROR", repr(e))

# Tax Category: site had 0 before this probe (segment 0), so all 7 are ours
for tc in PROBE_TAX_CATEGORIES:
    if frappe.db.exists("Tax Category", tc):
        try:
            frappe.delete_doc("Tax Category", tc, ignore_permissions=True, force=True)
        except Exception as e:
            rec("tax_category_delete_FAILED_" + tc, repr(e))
frappe.db.commit()
rec("tax_categories_after", frappe.get_all("Tax Category", pluck="name"))
rec("tax_category_count_after", frappe.db.count("Tax Category"))

# Item Tax Template from the error-path company carries no abbr in some paths
rec("item_tax_templates_all_after", frappe.get_all(
    "Item Tax Template", fields=["name", "company"]))
for nm in [d["name"] for d in frappe.get_all("Item Tax Template", fields=["name"])
           if "V19" in d["name"]]:
    try:
        frappe.delete_doc("Item Tax Template", nm, ignore_permissions=True, force=True)
        rec("item_tax_template_deleted", nm)
    except Exception as e:
        rec("item_tax_template_delete_FAILED_" + nm, repr(e))
frappe.db.commit()

# anything still named after a probe company, whatever the doctype we checked
rec("names_like_V19", {
    dt: frappe.db.sql("select name from `tab" + dt + "` where name like %s", "%V19%")
    for dt in ("Company", "Account", "Cost Center", "Warehouse", "Department",
               "Sales Taxes and Charges Template", "Purchase Taxes and Charges Template",
               "Item Tax Template", "Tax Category")
})

# ---- baseline company, item by item, must equal segment 0 -------------------
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

# ---- site-wide state --------------------------------------------------------
rec("account_count_total_after", frappe.db.count("Account"))
rec("companies_all_after", frappe.get_all("Company", fields=["name", "abbr", "lft", "rgt"]))
rec("default_company_global", frappe.db.get_default("company"))
rec("global_defaults_default_company",
    frappe.db.get_single_value("Global Defaults", "default_company"))
rec("global_defaults_demo_company",
    frappe.db.get_single_value("Global Defaults", "demo_company"))
rec("financial_report_template_count", frappe.db.count("Financial Report Template"))
rec("error_log_count", frappe.db.count("Error Log"))
rec("error_logs", frappe.get_all("Error Log", fields=["name", "method", "creation"],
                                 order_by="creation desc", limit=10))
rec("nsm_bad_account_rows", frappe.db.sql(
    "select count(*) from tabAccount where lft is null or rgt is null or lft>=rgt")[0][0])
rec("nsm_bad_company_rows", frappe.db.sql(
    "select count(*) from tabCompany where lft is null or rgt is null or lft>=rgt")[0][0])
rec("tax_rule_count_after", frappe.db.count("Tax Rule"))

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=1, default=str)
print("\nwrote " + OUT, flush=True)

frappe.destroy()
