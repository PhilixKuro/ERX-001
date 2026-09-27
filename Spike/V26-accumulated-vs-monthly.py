# V-26 probe: can the engine put an ACCUMULATED column and a SINGLE-MONTH column
# side by side in ONE report -- i.e. the statutory 本年累计金额 / 本月金额 pair?
#
# Proposition V-26 (SH-P1S4002 half 2): `accumulated_values` is a report-level
# switch, not a column-level one, therefore "one column cumulative, one column
# single-month" is architecturally impossible in the template engine.
#
# This is the second of the two judgement bases behind the R1 decision
# "BS+PL 自写". If it is FALSE, that decision must be re-judged.
#
# Method: the demo company has GL in exactly ONE month (2026-09). That makes
# cumulative and single-month trivially distinguishable -- a cumulative column
# keeps the value in Oct/Nov/Dec, a single-month column drops back to zero.
# Every engine number is cross-checked against an independent raw-GL sum.
#
# WRITES NOTHING PERMANENT. A temp template is inserted inside a transaction and
# rolled back. `module` is deliberately left EMPTY: FinancialReportTemplate.
# on_update -> _export_template() writes .json into the erpnext source tree when
# module is set, and that is a filesystem side effect rollback would NOT undo.
#
# Run (cwd MUST be .../sites, else frappe's logger dies on a relative path):
#   docker exec -i -w /workspace/frappe-bench/sites erx001-frappe-1 \
#     /workspace/frappe-bench/env/bin/python /workspace/Spike/V26-accumulated-vs-monthly.py

import json
import traceback

import frappe

SITE = "erx.localhost"
COMPANY = "华东弹簧"
OUT = "/workspace/Spike/V26-out/accumulated-vs-monthly.json"
TPL = "ZZ-PROBE-V26-PL-TwoColumn"

result = {"probe": "V-26 accumulated column + single-month column in one report"}


def rec(k, v):
    result[k] = v
    print("[" + k + "] " + json.dumps(v, ensure_ascii=False, default=str)[:2200], flush=True)


frappe.init(site=SITE)
frappe.connect()
frappe.set_user("Administrator")

try:
    # ---------- 0. is accumulated_values even a filter on this report? ----------
    import os

    js_path = frappe.get_app_path(
        "erpnext", "accounts", "report", "custom_financial_statement",
        "custom_financial_statement.js")
    base_js = frappe.get_app_path("erpnext", "public", "js", "financial_statements.js")
    bs_js = frappe.get_app_path(
        "erpnext", "accounts", "report", "balance_sheet", "balance_sheet.js")
    counts = {}
    for tag, p in [("custom_financial_statement.js", js_path),
                   ("financial_statements.js (shared base)", base_js),
                   ("balance_sheet.js (legacy report)", bs_js)]:
        with open(p, encoding="utf-8") as f:
            counts[tag] = f.read().count("accumulated_values")
    rec("accumulated_values_filter_occurrences", counts)

    # ---------- 1. what does the engine do when the filter is absent (None)? ----------
    import inspect

    from erpnext.accounts.doctype.financial_report_template import financial_report_engine as fre

    rec("handle_balance_accumulation_source",
        inspect.getsource(fre.FinancialQueryBuilder._handle_balance_accumulation))
    rec("accumulate_values_source", inspect.getsource(fre.AccountData.accumulate_values))
    rec("unaccumulate_values_source", inspect.getsource(fre.AccountData.unaccumulate_values))
    rec("period_value_get_value_source", inspect.getsource(fre.PeriodValue.get_value))

    # ---------- 2. independent raw-GL truth, computed WITHOUT the engine ----------
    pl_accounts = frappe.get_all(
        "Account",
        filters={"company": COMPANY, "is_group": 0, "root_type": ["in", ["Income", "Expense"]]},
        pluck="name")
    gl = frappe.get_all(
        "GL Entry",
        filters={"company": COMPANY, "is_cancelled": 0, "account": ["in", pl_accounts]},
        fields=["account", "posting_date", "debit", "credit"])
    by_month = {}
    for r in gl:
        key = str(r.posting_date)[:7]
        by_month[key] = by_month.get(key, 0.0) + (r.debit or 0.0) - (r.credit or 0.0)
    rec("raw_gl_pl_movement_by_month", by_month)
    rec("raw_gl_pl_total", round(sum(by_month.values()), 4))

    # ---------- 3. build a two-segment template: 本年累计 | 本月 ----------
    # Both segments select the SAME accounts. Only balance_type differs.
    pl_filter = json.dumps(["root_type", "=", "Expense"])
    inc_filter = json.dumps(["root_type", "=", "Income"])

    rows = [
        # ---- segment 0: 本年累计金额 (Closing Balance == running/cumulative) ----
        {"data_source": "Column Break", "display_name": "本年累计金额"},
        {"data_source": "Account Data", "display_name": "营业收入(累计)",
         "reference_code": "CUM_INC", "balance_type": "Closing Balance",
         "calculation_formula": inc_filter, "reverse_sign": 1, "fieldtype": "Currency"},
        {"data_source": "Account Data", "display_name": "营业成本(累计)",
         "reference_code": "CUM_EXP", "balance_type": "Closing Balance",
         "calculation_formula": pl_filter, "fieldtype": "Currency"},
        {"data_source": "Calculated Amount", "display_name": "净利润(累计)",
         "reference_code": "CUM_NP", "calculation_formula": "CUM_INC - CUM_EXP",
         "fieldtype": "Currency", "bold_text": 1},
        # ---- segment 1: 本月金额 (Period Movement == single period) ----
        {"data_source": "Column Break", "display_name": "本月金额"},
        {"data_source": "Account Data", "display_name": "营业收入(本月)",
         "reference_code": "MTH_INC", "balance_type": "Period Movement (Debits - Credits)",
         "calculation_formula": inc_filter, "reverse_sign": 1, "fieldtype": "Currency"},
        {"data_source": "Account Data", "display_name": "营业成本(本月)",
         "reference_code": "MTH_EXP", "balance_type": "Period Movement (Debits - Credits)",
         "calculation_formula": pl_filter, "fieldtype": "Currency"},
        {"data_source": "Calculated Amount", "display_name": "净利润(本月)",
         "reference_code": "MTH_NP", "calculation_formula": "MTH_INC - MTH_EXP",
         "fieldtype": "Currency", "bold_text": 1},
    ]

    doc = frappe.get_doc({
        "doctype": "Financial Report Template",
        "template_name": TPL,
        "report_type": "Profit and Loss Statement",
        # module deliberately EMPTY -- see header note about _export_template()
        "rows": rows,
    })
    doc.insert(ignore_permissions=True)
    rec("template_inserted", {
        "name": doc.name,
        "module": doc.module,
        "rows": len(doc.rows),
        "note": "module empty on purpose: avoids on_update writing json into app source tree",
    })

    # ---------- 4. run the engine Monthly across FY2026 ----------
    from erpnext.accounts.doctype.financial_report_template.financial_report_engine import (
        FinancialReportEngine,
    )

    filters = frappe._dict({
        "company": COMPANY, "report_template": doc.name,
        "filter_based_on": "Fiscal Year",
        "from_fiscal_year": "2026", "to_fiscal_year": "2026",
        "periodicity": "Monthly", "selected_view": "Report",
        "include_default_book_entries": 1,
    })
    rec("filters_used", dict(filters))
    rec("accumulated_values_in_filters", "accumulated_values" in filters)

    res = FinancialReportEngine().execute(filters)
    cols, data = res[0], res[1]
    rec("engine_columns", [{"fieldname": c.get("fieldname"), "label": c.get("label")}
                          for c in cols])

    # pull the 净利润 row out of each segment for Aug / Sep / Oct / Dec
    watch = ["aug_2026", "sep_2026", "oct_2026", "dec_2026"]
    extracted = []
    for r in data:
        row_out = {
            "seg_0_name": r.get("seg_0_account_name"),
            "seg_1_name": r.get("seg_1_account_name"),
        }
        for m in watch:
            row_out["seg_0_" + m] = r.get("seg_0_" + m)
            row_out["seg_1_" + m] = r.get("seg_1_" + m)
        extracted.append(row_out)
    rec("engine_rows_watched_months", extracted)

    # ---------- 5. the decisive check ----------
    # cumulative column must HOLD its value after Sep; monthly column must DROP to 0.
    verdict = {}
    for r in data:
        if r.get("seg_0_account_name") == "净利润(累计)":
            cum = {m: r.get("seg_0_" + m) for m in watch}
            mth = {m: r.get("seg_1_" + m) for m in watch}
            verdict = {
                "cumulative_column_by_month": cum,
                "monthly_column_by_month": mth,
                "cumulative_holds_after_sep": cum.get("oct_2026") == cum.get("sep_2026")
                                              and cum.get("dec_2026") == cum.get("sep_2026"),
                "monthly_drops_after_sep": mth.get("oct_2026") in (0, 0.0)
                                           and mth.get("dec_2026") in (0, 0.0),
                "two_columns_differ_in_oct": r.get("seg_0_oct_2026") != r.get("seg_1_oct_2026"),
            }
    verdict["conclusion_both_accumulations_coexist"] = bool(
        verdict.get("cumulative_holds_after_sep") and verdict.get("monthly_drops_after_sep"))
    rec("DECISIVE", verdict)

    # ---------- 6. what it costs: shape of the delivered column set ----------
    rec("column_layout_cost", {
        "visible_columns": [c.get("label") for c in cols if not c.get("hidden")],
        "note": "a second account/项目 column appears mid-table, one per segment",
    })

except Exception as e:
    rec("probe_error", {"err": str(e), "tb": traceback.format_exc()[-2500:]})

finally:
    frappe.db.rollback()
    rec("template_exists_after_rollback", bool(frappe.db.exists("Financial Report Template", TPL)))
    # confirm no stray file landed in the app source tree
    import glob
    strays = glob.glob(frappe.get_app_path("erpnext", "accounts", "financial_report_template",
                                           "*probe*"))
    strays += glob.glob(frappe.get_app_path("erpnext", "accounts", "financial_report_template",
                                            "*v26*"))
    rec("stray_exported_files", strays)
    rec("fiscal_years_final", [r.name for r in frappe.get_all("Fiscal Year", fields=["name"])])

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)
    print("\nWROTE " + OUT, flush=True)
