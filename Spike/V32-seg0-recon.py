# V-32 seg0: READ-ONLY reconnaissance. No writes at all.
#
# Gathers the site state the three write-probes need:
#   - baselines required by the site-safety rules (GL Entry / SLE / Account / Company /
#     Financial Report Template / Fiscal Year / Property Setter / Error Log)
#   - storage engine of every table the probes will touch (rollback-safety gate:
#     a non-InnoDB table means frappe.db.rollback() will NOT undo the write)
#   - whether sqlite_search is enabled (its doc_events on_update hook carries commits
#     on a separate connection; it must return early at sqlite_search.py:1841-1842)
#   - whether any Assignment Rule / Workflow exists for the doctypes the probes save
#     (their wildcard on_update hooks carry frappe.enqueue only in OTHER functions,
#      but an early return is a stronger guarantee than reading the call graph)
#   - a usable tax Account + Company + Cost Center for probe (a)
#   - the current charge_type Select options, verbatim
#
# Run (cwd MUST be .../sites, else frappe's logger dies on a relative path):
#   docker exec -i -e PYTHONUTF8=1 -e PYTHONIOENCODING=utf-8 \
#     -w /workspace/frappe-bench/sites erx001-frappe-1 \
#     /workspace/frappe-bench/env/bin/python /workspace/Spike/V32-seg0-recon.py

import json
import os
import traceback

import frappe

SITE = "erx.localhost"
OUTDIR = "/workspace/Spike/V32-out"
OUT = os.path.join(OUTDIR, "seg0-recon.json")

result = {"probe": "V-32 seg0 read-only recon; no writes"}


def rec(k, v):
    result[k] = v
    print("{0} = {1}".format(k, json.dumps(v, ensure_ascii=False, default=str)))


frappe.init(site=SITE)
frappe.connect()
frappe.set_user("Administrator")

try:
    # ---- baselines mandated by the site-safety rules -------------------------
    baseline = {}
    for dt in (
        "GL Entry",
        "Stock Ledger Entry",
        "Account",
        "Company",
        "Financial Report Template",
        "Fiscal Year",
        "Property Setter",
        "Error Log",
        "Sales Taxes and Charges Template",
        "Sales Taxes and Charges",
        "Version",
    ):
        baseline[dt] = frappe.db.count(dt)
    rec("baseline_counts", baseline)
    rec("fiscal_years", frappe.get_all("Fiscal Year", pluck="name"))
    rec("companies", frappe.get_all("Company", fields=["name", "abbr", "country", "default_currency"]))

    # ---- rollback-safety gate: engine of every table the probes touch --------
    engines = {}
    for tbl in (
        "tabProperty Setter",
        "tabSales Taxes and Charges Template",
        "tabSales Taxes and Charges",
        "tabSingles",
        "tabVersion",
        "tabError Log",
        "tabData Import Log",
    ):
        row = frappe.db.sql(
            "select ENGINE from information_schema.tables "
            "where TABLE_SCHEMA = database() and TABLE_NAME = %s",
            tbl,
        )
        engines[tbl] = row[0][0] if row else None
    rec("table_engines", engines)
    rec(
        "GATE_all_probe_tables_innodb",
        all(
            engines[t] == "InnoDB"
            for t in (
                "tabProperty Setter",
                "tabSales Taxes and Charges Template",
                "tabSales Taxes and Charges",
                "tabSingles",
                "tabVersion",
            )
        ),
    )

    # ---- wildcard on_update hooks: prove the early returns actually hold -----
    try:
        from frappe.search.sqlite_search import get_search_classes

        se = []
        for SearchClass in get_search_classes():
            s = SearchClass()
            se.append(
                {
                    "cls": SearchClass.__name__,
                    "search_enabled": bool(s.is_search_enabled()),
                    "index_exists": bool(s.index_exists()),
                }
            )
        rec("sqlite_search_classes", se)
        rec(
            "GATE_sqlite_search_returns_early",
            all(not (x["search_enabled"] and x["index_exists"]) for x in se),
        )
    except Exception as e:
        rec("sqlite_search_probe_error", repr(e))

    probe_doctypes = ["Property Setter", "Sales Taxes and Charges Template"]
    rec(
        "assignment_rules_for_probe_doctypes",
        frappe.get_all(
            "Assignment Rule",
            filters={"document_type": ("in", probe_doctypes), "disabled": 0},
            fields=["name", "document_type"],
        ),
    )
    rec("assignment_rule_total", frappe.db.count("Assignment Rule"))
    rec(
        "workflows_for_probe_doctypes",
        frappe.get_all(
            "Workflow", filters={"document_type": ("in", probe_doctypes)}, fields=["name", "is_active"]
        ),
    )
    rec("workflow_total", frappe.db.count("Workflow"))
    rec("notification_total", frappe.db.count("Notification"))
    rec("server_script_total", frappe.db.count("Server Script"))
    rec(
        "custom_doc_events_hook",
        {k: str(v) for k, v in (frappe.get_hooks("doc_events") or {}).items() if k in probe_doctypes},
    )

    # ---- charge_type Select options, verbatim --------------------------------
    for dt in ("Sales Taxes and Charges", "Purchase Taxes and Charges"):
        df = frappe.get_meta(dt).get_field("charge_type")
        rec(
            "charge_type_options__" + dt.replace(" ", "_"),
            {"raw": df.options, "split": (df.options or "").split("\n"), "reqd": df.reqd},
        )
    rec(
        "existing_property_setters_on_charge_type",
        frappe.get_all(
            "Property Setter",
            filters={"field_name": "charge_type"},
            fields=["name", "doc_type", "property", "value"],
        ),
    )

    # ---- a usable tax Account / Cost Center for probe (a) --------------------
    rec(
        "candidate_tax_accounts",
        frappe.get_all(
            "Account",
            filters={"is_group": 0, "root_type": ("in", ["Liability", "Asset"]), "company": "华东弹簧"},
            fields=["name", "account_type", "root_type"],
            limit=25,
        ),
    )
    rec(
        "cost_centers",
        frappe.get_all("Cost Center", filters={"is_group": 0}, fields=["name", "company"], limit=10),
    )
    rec(
        "existing_sales_tax_templates",
        frappe.get_all("Sales Taxes and Charges Template", fields=["name", "company", "is_default"]),
    )

    # ---- (c) inputs: the Accounts Settings switch + existing Purchase Receipts
    rec(
        "book_stock_expense_gl_entries_current",
        frappe.db.get_single_value("Accounts Settings", "book_stock_expense_gl_entries"),
    )
    rec(
        "singles_row_for_switch",
        frappe.db.sql(
            "select doctype, field, value from tabSingles "
            "where doctype='Accounts Settings' and field='book_stock_expense_gl_entries'",
            as_dict=True,
        ),
    )
    rec("purchase_receipt_count", frappe.db.count("Purchase Receipt"))
    rec(
        "purchase_receipts",
        frappe.get_all("Purchase Receipt", fields=["name", "docstatus"], limit=5),
    )

    # ---- confirm no pending writes were made by this read-only probe ---------
    rec("transaction_writes_at_end", frappe.db.transaction_writes)
    rec("ok", True)
except Exception:
    result["fatal"] = traceback.format_exc()
    print(result["fatal"])
finally:
    # read-only, but roll back unconditionally so nothing can escape
    try:
        frappe.db.rollback()
    except Exception:
        pass
    os.makedirs(OUTDIR, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=1, default=str)
    print("WROTE " + OUT)
    frappe.destroy()
