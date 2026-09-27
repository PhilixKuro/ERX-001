# V-25 probe: what do the COLUMN HEADERS of the columnar (two-pane) Balance Sheet
# actually look like when the report spans TWO fiscal years?
#
# Proposition V-25 (SH-P1S4002 half 1): with a two-pane template + two fiscal
# years, the engine's column headers are period labels (years), NOT the statutory
# Chinese labels 年初余额 / 期末余额, and nothing in the template layer can
# override them.
#
# This is one of the two judgement bases behind the R1 decision "BS+PL 自写".
# If headers turn out to BE controllable from the template layer, that decision
# must be re-judged (back to "配模板 + Custom API").
#
# WRITES NOTHING PERMANENT. Fiscal Year 2025 is created inside a transaction
# purely so the engine can build a 2-FY period list, then rolled back.
# There is no frappe.db.commit() anywhere in this file.
#
# Run (cwd MUST be .../sites, else frappe's logger dies on a relative path):
#   docker exec -i -w /workspace/frappe-bench/sites erx001-frappe-1 \
#     /workspace/frappe-bench/env/bin/python /workspace/Spike/V25-column-headers.py

import inspect
import json
import traceback

import frappe

SITE = "erx.localhost"
COMPANY = "华东弹簧"
OUT = "/workspace/Spike/V25-out/column-headers.json"

result = {"probe": "V-25 columnar BS column headers across two fiscal years"}


def rec(k, v):
    result[k] = v
    print("[" + k + "] " + json.dumps(v, ensure_ascii=False, default=str)[:2000], flush=True)


frappe.init(site=SITE)
frappe.connect()
frappe.set_user("Administrator")

created_fy = None
try:
    # ---------- 0. baseline ----------
    rec("fiscal_years_before", frappe.get_all(
        "Fiscal Year", fields=["name", "year_start_date", "year_end_date", "disabled"],
        order_by="year_start_date"))

    # ---------- 1. get_period_list is a pure function: read its labels directly ----------
    from erpnext.accounts.report.financial_statements import get_columns, get_period_list

    # Date Range + ignore_fiscal_year=True needs NO Fiscal Year record at all,
    # so this part is a genuinely read-only probe of the label builder.
    for periodicity in ("Yearly", "Monthly"):
        for accum in (False, True):
            pl = get_period_list(
                from_fiscal_year=None, to_fiscal_year=None,
                period_start_date="2025-01-01", period_end_date="2026-12-31",
                filter_based_on="Date Range", periodicity=periodicity,
                accumulated_values=accum, company=COMPANY, ignore_fiscal_year=True)
            tag = "accumulated" if accum else "unaccumulated"
            rec("period_labels_" + periodicity + "_" + tag,
                [{"key": p["key"], "label": p["label"]} for p in pl])

        cols = get_columns(periodicity, pl, accumulated_values=1, company=COMPANY)
        rec("get_columns_" + periodicity,
            [{"fieldname": c["fieldname"], "label": c["label"], "hidden": c.get("hidden", 0)}
             for c in cols])

    # ---------- 2. create FY 2025 so the real engine can span two FYs ----------
    if not frappe.db.exists("Fiscal Year", "2025"):
        fy = frappe.get_doc({
            "doctype": "Fiscal Year", "year": "2025",
            "year_start_date": "2025-01-01", "year_end_date": "2025-12-31",
        })
        fy.insert(ignore_permissions=True)
        created_fy = fy.name
        rec("created_fiscal_year", {"name": fy.name, "note": "inside txn, rolled back at end"})

    # ---------- 3. run the REAL engine on the shipped two-pane BS template ----------
    from erpnext.accounts.doctype.financial_report_template.financial_report_engine import (
        FinancialReportEngine,
    )
    from erpnext.accounts.doctype.financial_report_template import financial_report_engine as fre

    tpl = "Horizontal Balance Sheet (Columnar)"
    tpl_doc = frappe.get_doc("Financial Report Template", tpl)
    rec("template_shape", {
        "name": tpl_doc.name,
        "report_type": tpl_doc.report_type,
        "rows": len(tpl_doc.rows),
        "column_breaks": [{"idx": r.idx, "display_name": r.display_name}
                          for r in tpl_doc.rows if r.data_source == "Column Break"],
        "section_breaks": [{"idx": r.idx, "display_name": r.display_name}
                           for r in tpl_doc.rows if r.data_source == "Section Break"],
        "distinct_balance_types": sorted({r.balance_type or "" for r in tpl_doc.rows}),
    })

    runs = [
        ("two_FY_yearly", {
            "company": COMPANY, "report_template": tpl,
            "filter_based_on": "Fiscal Year",
            "from_fiscal_year": "2025", "to_fiscal_year": "2026",
            "periodicity": "Yearly", "selected_view": "Report",
            "include_default_book_entries": 1,
        }),
        ("one_FY_monthly", {
            "company": COMPANY, "report_template": tpl,
            "filter_based_on": "Fiscal Year",
            "from_fiscal_year": "2026", "to_fiscal_year": "2026",
            "periodicity": "Monthly", "selected_view": "Report",
            "include_default_book_entries": 1,
        }),
    ]

    for label, filters in runs:
        try:
            res = FinancialReportEngine().execute(frappe._dict(filters))
            cols, data = res[0], res[1]
            rec("engine_columns_" + label,
                [{"fieldname": c.get("fieldname"), "label": c.get("label"),
                  "fieldtype": c.get("fieldtype"), "hidden": c.get("hidden", 0)} for c in cols])
            rec("engine_rowcount_" + label, len(data))
            rec("engine_first_rows_" + label, [
                {k: v for k, v in r.items() if not k.startswith("_") and k != "segment_values"}
                for r in data[:3]])
        except Exception as e:
            rec("engine_error_" + label, {"err": str(e), "tb": traceback.format_exc()[-1500:]})

    # ---------- 4. can the TEMPLATE layer influence a column label at all? ----------
    src_engine = inspect.getsource(fre)
    import erpnext.accounts.report.financial_statements as fs_mod
    src_fs = inspect.getsource(fs_mod)

    rec("label_assignment_sites", {
        "engine_label_lines": [l.strip() for l in src_engine.splitlines()
                               if "label" in l and ("=" in l)][:40],
        "financial_statements_label_lines": [l.strip() for l in src_fs.splitlines()
                                             if "label" in l and ("=" in l)][:40],
    })

    row_fields = [f.fieldname for f in frappe.get_meta("Financial Report Row").fields]
    tpl_fields = [f.fieldname for f in frappe.get_meta("Financial Report Template").fields]
    rec("row_doctype_fields", row_fields)
    rec("template_doctype_fields", tpl_fields)
    rec("any_column_label_field", {
        "row_label_or_header_fields": [f for f in row_fields
                                       if "label" in f.lower() or "header" in f.lower()],
        "template_label_or_header_fields": [f for f in tpl_fields
                                            if "label" in f.lower() or "header" in f.lower()],
    })

    # ---------- 5. what does a Custom API row control -- values, or columns? ----------
    rec("custom_api_contract", {
        "call_site": "financial_report_engine.py:1185",
        "source_lines": [l.strip() for l in src_engine.splitlines() if "frappe.call(method" in l],
        "note": "return value is bound to `values`, a flat list of one number per period",
    })

finally:
    frappe.db.rollback()
    remaining = [r.name for r in frappe.get_all("Fiscal Year", fields=["name"])]
    rec("fiscal_years_after_rollback", remaining)
    rec("rollback_clean", (created_fy is None) or (created_fy not in remaining))

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)
    print("\nWROTE " + OUT, flush=True)
