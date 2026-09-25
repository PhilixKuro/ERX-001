# V-18 segment 6: inventory BEFORE cleanup.
#
# The test company is company-scoped and Company.on_trash handles most of it, but
# several things the native flow created are NOT company-scoped and would survive
# deleting the company.  List them explicitly so the待验表 can report exactly
# what remains, rather than claiming a clean site.
#
# Read-only.  Run (cwd MUST be .../sites):
#   docker exec -i -w /workspace/frappe-bench/sites erx001-frappe-1 \
#     /workspace/frappe-bench/env/bin/python /workspace/Spike/V18-seg6-cleanup-inventory.py

import json

import frappe

SITE = "erx.localhost"
COMPANY = "V18原生乙"
APP = "erx_v18"
CUTOFF = "2026-09-25 01:40:00"  # this Session started ~01:47 (backup timestamp)
OUT = "/workspace/Spike/V18-out/seg6-cleanup-inventory.json"

result = {"segment": "6 pre-cleanup inventory"}


def rec(k, v):
    result[k] = v
    print(f"[{k}] {v}", flush=True)


frappe.init(site=SITE)
frappe.connect()

rec("cutoff_used", CUTOFF)

# ---- site-wide doctypes the native / zelin flows touch ----------------------
for dt in ("Tax Category", "Financial Report Template", "Item Tax Template",
           "Sales Taxes and Charges Template", "Purchase Taxes and Charges Template",
           "Tax Rule", "Company", "Cost Center", "Warehouse", "Department",
           "Module Def", "Desktop Icon", "Workspace Sidebar", "DocType"):
    try:
        total = frappe.db.count(dt)
        new = frappe.get_all(dt, filters={"creation": (">", CUTOFF)},
                             fields=["name", "creation"], order_by="creation")
        rec(f"{dt}__total_and_new", {"total": total, "new_this_session": [
            (r["name"], str(r["creation"])) for r in new]})
    except Exception as e:
        rec(f"{dt}__ERROR", repr(e))

# ---- does the test app own any DB records? ---------------------------------
rec("module_defs_for_app", frappe.get_all(
    "Module Def", filters={"app_name": APP}, fields=["name", "module_name"]))
rec("doctypes_for_app", frappe.db.sql(
    "select name, module from tabDocType where module in (select name from `tabModule Def` where app_name=%s)",
    APP))
for dt in ("Desktop Icon", "Workspace Sidebar"):
    try:
        rec(f"{dt}_rows_for_app", frappe.db.sql(
            f"select name from `tab{dt}` where name like %s or app like %s", (f"%{APP}%", f"%{APP}%")))
    except Exception as e:
        rec(f"{dt}_rows_for_app_ERROR", repr(e))
rec("installed_apps", frappe.get_installed_apps())

# ---- defaults / singles that must survive unchanged ------------------------
rec("default_company_global", frappe.db.get_default("company"))
rec("global_defaults_default_company", frappe.db.get_single_value("Global Defaults", "default_company"))
rec("global_defaults_demo_company", frappe.db.get_single_value("Global Defaults", "demo_company"))
rec("system_settings_country", frappe.db.get_single_value("System Settings", "country"))
rec("defaultvalue_rows_mentioning_V18", frappe.db.sql(
    "select parent, defkey, defvalue from tabDefaultValue where defvalue like %s", "V18%"))

# ---- blockers to deleting the company --------------------------------------
rec("gl_entries_for_test_company", frappe.db.count("GL Entry", {"company": COMPANY}))
rec("stock_ledger_entries_for_test_company", frappe.db.count("Stock Ledger Entry", {"company": COMPANY}))
rec("accounts_for_test_company", frappe.db.count("Account", {"company": COMPANY}))
rec("test_company_is_group_or_child", frappe.db.get_value(
    "Company", COMPANY, ["is_group", "parent_company", "lft", "rgt"], as_dict=True))
rec("companies_all", frappe.get_all("Company", fields=["name", "is_group", "parent_company", "lft", "rgt"]))

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=1, default=str)
print(f"\nwrote {OUT}", flush=True)

frappe.destroy()
