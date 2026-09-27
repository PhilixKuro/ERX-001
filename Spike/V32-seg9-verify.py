# V-32 seg9: independent post-run site verification. READ-ONLY, no writes.
#
# Re-checks every baseline the site-safety rules name, in a FRESH process, so the
# verification does not depend on any state left in a probe's own interpreter.
# Also checks tabSeries (naming-series counters): probe (b) inserted a Sales Order and a
# Sales Taxes and Charges Template before rolling back, and a naming counter that had
# advanced non-transactionally would be a real, unreported side effect.
#
# Run (cwd MUST be .../sites):
#   docker exec -i -e PYTHONUTF8=1 -e PYTHONIOENCODING=utf-8 \
#     -w /workspace/frappe-bench/sites erx001-frappe-1 \
#     /workspace/frappe-bench/env/bin/python /workspace/Spike/V32-seg9-verify.py

import json
import os
import traceback

import frappe

SITE = "erx.localhost"
OUTDIR = "/workspace/Spike/V32-out"
OUT = os.path.join(OUTDIR, "seg9-verify.json")

EXPECTED = {
    "GL Entry": 22,
    "Stock Ledger Entry": 12,
    "Account": 95,
    "Company": 1,
    "Financial Report Template": 6,
    "Fiscal Year": 1,
    "Property Setter": 182,
    "Error Log": 0,
}

result = {"probe": "V-32 seg9 independent post-run verification; read-only"}


def rec(k, v):
    result[k] = v
    print("{0} = {1}".format(k, json.dumps(v, ensure_ascii=False, default=str)))


frappe.init(site=SITE)
frappe.connect()
frappe.set_user("Administrator")

try:
    actual = {dt: frappe.db.count(dt) for dt in EXPECTED}
    rec("expected", EXPECTED)
    rec("actual", actual)
    rec("mismatches", {k: [EXPECTED[k], actual[k]] for k in EXPECTED if EXPECTED[k] != actual[k]})
    rec("ALL_BASELINES_MATCH", actual == EXPECTED)

    rec("fiscal_years", frappe.get_all("Fiscal Year", pluck="name"))
    rec("fiscal_year_only_2026", frappe.get_all("Fiscal Year", pluck="name") == ["2026"])

    rec(
        "other_counts",
        {
            dt: frappe.db.count(dt)
            for dt in (
                "Sales Order",
                "Sales Taxes and Charges Template",
                "Sales Taxes and Charges",
                "Purchase Receipt",
                "Repost Item Valuation",
                "Version",
                "Data Import Log",
            )
        },
    )

    # charge_type options must be byte-identical to the shipped value
    EXPECTED_OPTIONS = "\nActual\nOn Net Total\nOn Previous Row Amount\nOn Previous Row Total\nOn Item Quantity"
    for dt in ("Sales Taxes and Charges", "Purchase Taxes and Charges"):
        opts = frappe.get_meta(dt, cached=False).get_field("charge_type").options
        rec("charge_type_options__" + dt.replace(" ", "_"), opts)
        rec("charge_type_options_pristine__" + dt.replace(" ", "_"), opts == EXPECTED_OPTIONS)

    rec(
        "property_setters_on_charge_type",
        frappe.get_all(
            "Property Setter", filters={"field_name": "charge_type"}, fields=["name", "property", "value"]
        ),
    )
    rec("options_property_setters_sitewide", frappe.db.count("Property Setter", {"property": "options"}))

    rec(
        "book_stock_expense_gl_entries",
        frappe.db.get_single_value("Accounts Settings", "book_stock_expense_gl_entries", cache=False),
    )
    rec(
        "book_stock_expense_setting_is_0_as_before",
        str(
            frappe.db.get_single_value(
                "Accounts Settings", "book_stock_expense_gl_entries", cache=False
            )
        )
        == "0",
    )

    # naming-series counters: did any advance non-transactionally?
    rec(
        "series_rows",
        frappe.db.sql(
            "select name, current from tabSeries where name in "
            "('SAL-ORD-.YYYY.-','MAT-PRE-.YYYY.-') or name like 'SAL-ORD%' or name like 'MAT-PRE%'",
            as_dict=True,
        ),
    )
    rec(
        "max_sales_order",
        frappe.db.sql("select max(name) from `tabSales Order`"),
    )

    # any probe leftovers anywhere?
    leftovers = {}
    for marker in ("V32PROBEA", "V32PROBEB", "V32PROBEC", "V32"):
        leftovers[marker] = {
            "templates": frappe.db.sql(
                "select name from `tabSales Taxes and Charges Template` where title like %s",
                "%" + marker + "%",
                as_dict=True,
            ),
            "tax_rows": frappe.db.sql(
                "select name from `tabSales Taxes and Charges` where description like %s",
                "%" + marker + "%",
                as_dict=True,
            ),
            "property_setters": frappe.db.sql(
                "select name from `tabProperty Setter` where value like %s or name like %s",
                ("%" + marker + "%", "%" + marker + "%"),
                as_dict=True,
            ),
            "error_logs": frappe.db.sql(
                "select name from `tabError Log` where error like %s", "%" + marker + "%", as_dict=True
            ),
        }
    rec("probe_leftovers_by_marker", leftovers)
    rec(
        "NO_PROBE_LEFTOVERS",
        all(not any(v.values()) for v in leftovers.values()),
    )

    # any custom charge_type value anywhere in the real data?
    rec(
        "distinct_charge_types_in_data",
        frappe.db.sql(
            "select distinct charge_type from `tabSales Taxes and Charges` "
            "union select distinct charge_type from `tabPurchase Taxes and Charges`",
            as_dict=True,
        ),
    )

    rec("transaction_writes_at_end", frappe.db.transaction_writes)
    rec("ok", True)
except Exception:
    result["fatal"] = traceback.format_exc()
    print(result["fatal"])
finally:
    try:
        frappe.db.rollback()
    except Exception:
        pass
    os.makedirs(OUTDIR, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=1, default=str)
    print("WROTE " + OUT)
    frappe.destroy()
