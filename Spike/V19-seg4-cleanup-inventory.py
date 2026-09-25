# V-19 segment 4: inventory BEFORE cleanup.
#
# Three test companies were built (V19A案一 / V19A案二 / V19A案三).  Company.on_trash
# handles the company-scoped records, but several things these flows created are
# NOT company-scoped and would survive deleting the companies.  List them
# explicitly so the待验表 can report exactly what remains rather than claiming a
# clean site.
#
# Read-only.  Run (cwd MUST be .../sites):
#   docker exec -i -w /workspace/frappe-bench/sites erx001-frappe-1 \
#     /workspace/frappe-bench/env/bin/python /workspace/Spike/V19-seg4-cleanup-inventory.py

import json

import frappe

SITE = "erx.localhost"
COMPANIES = ["V19A案一", "V19A案二", "V19A案三"]
ABBRS = ["V19A", "V19B", "V19C"]
APP = "erx_v19"
BASE = "华东弹簧"
CUTOFF = "2026-09-25 10:50:00"  # backup 20260925_185058 was taken just before this session's writes
OUT = "/workspace/Spike/V19-out/seg4-cleanup-inventory.json"

result = {"segment": "4 pre-cleanup inventory"}


def rec(k, v):
    result[k] = v
    print("[" + k + "] " + repr(v), flush=True)


frappe.init(site=SITE)
frappe.connect()

rec("cutoff_used", CUTOFF)
rec("companies_all", frappe.get_all("Company", fields=["name", "abbr", "lft", "rgt",
                                                       "is_group", "parent_company"]))

for dt in ("Tax Category", "Financial Report Template", "Item Tax Template",
           "Sales Taxes and Charges Template", "Purchase Taxes and Charges Template",
           "Tax Rule", "Company", "Cost Center", "Warehouse", "Department",
           "Account", "Module Def", "Error Log"):
    try:
        total = frappe.db.count(dt)
        new = frappe.get_all(dt, filters={"creation": (">", CUTOFF)},
                             fields=["name", "creation"], order_by="creation")
        rec(dt + "__total_and_new", {"total": total, "new_count": len(new),
                                     "new_sample": [(r["name"], str(r["creation"]))
                                                    for r in new[:12]]})
    except Exception as e:
        rec(dt + "__ERROR", repr(e))

for c, a in zip(COMPANIES, ABBRS):
    rec("PER_COMPANY_" + a, {
        "exists": bool(frappe.db.exists("Company", c)),
        "accounts": frappe.db.count("Account", {"company": c}),
        "accounts_by_abbr": frappe.db.sql(
            "select count(*) from tabAccount where name like %s", "%- " + a)[0][0],
        "gl_entries": frappe.db.count("GL Entry", {"company": c}),
        "sles": frappe.db.count("Stock Ledger Entry", {"company": c}),
        "warehouses": frappe.db.count("Warehouse", {"company": c}),
        "cost_centers": frappe.db.count("Cost Center", {"company": c}),
        "departments": frappe.db.count("Department", {"company": c}),
        "sales_templates": frappe.db.count("Sales Taxes and Charges Template", {"company": c}),
        "purchase_templates": frappe.db.count("Purchase Taxes and Charges Template", {"company": c}),
        "item_tax_templates": frappe.db.count("Item Tax Template", {"company": c}),
        "tax_rules": frappe.db.sql(
            "select count(*) from `tabTax Rule` where sales_tax_template like %s "
            "or purchase_tax_template like %s", ("%- " + a, "%- " + a))[0][0],
        "item_defaults": frappe.db.sql(
            "select count(*) from `tabItem Default` where company=%s", c)[0][0],
        "mode_of_payment_accounts": frappe.db.sql(
            "select count(*) from `tabMode of Payment Account` where company=%s", c)[0][0],
        "is_group": frappe.db.get_value("Company", c, "is_group"),
        "parent_company": frappe.db.get_value("Company", c, "parent_company"),
        "child_companies": frappe.get_all("Company", filters={"parent_company": c}, pluck="name"),
    })

rec("global_defaults_default_company", frappe.db.get_single_value("Global Defaults", "default_company"))
rec("global_defaults_demo_company", frappe.db.get_single_value("Global Defaults", "demo_company"))
rec("default_company_global", frappe.db.get_default("company"))
rec("tax_categories_all", frappe.get_all("Tax Category", fields=["name", "creation"]))
rec("module_defs_for_app", frappe.get_all("Module Def", filters={"app_name": APP},
                                          fields=["name", "module_name"]))
rec("doctypes_for_app", frappe.db.sql(
    "select name, module from tabDocType where module in "
    "(select name from `tabModule Def` where app_name=%s)", APP))
rec("BASELINE_accounts", frappe.db.count("Account", {"company": BASE}))
rec("installed_apps", frappe.get_installed_apps())

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=1, default=str)
print("wrote " + OUT, flush=True)

frappe.destroy()
