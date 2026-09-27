# V-26 segment 2: does `Closing Balance` on a P&L account carry PRIOR-PERIOD
# amounts into the current period?
#
# Why this matters: V-26 seg1 proved a cumulative column and a single-month
# column can coexist, using balance_type="Closing Balance" as the 本年累计 column.
# But Closing Balance is a BALANCE concept. For 本年累计金额 to be correct it must
# start from zero at the fiscal year boundary. If Closing Balance instead runs
# from the beginning of time, the "cumulative" column is wrong in every year
# after the first -- which would make the whole route unusable.
#
# Method (no writes at all): the demo company's only P&L GL is in 2026-09.
# Run the engine over a Date Range that starts AFTER that -- 2026-10-01..12-31.
#   - if Closing Balance shows 719.5, it carries prior-period amounts  => running balance
#   - if Closing Balance shows 0.0,   it restarts at the period        => period-scoped
# Period Movement is expected to be 0.0 either way (nothing posted in Q4).
#
# Also reads the opening-balance code path to explain whatever is observed, and
# checks whether a Period Closing Voucher exists (that is the thing that would
# zero P&L accounts at a year boundary).
#
# READ-ONLY apart from the temp template, which is inserted in a transaction and
# rolled back. module left EMPTY on purpose (see V26 seg1 header).
#
# Run (cwd MUST be .../sites):
#   docker exec -i -w /workspace/frappe-bench/sites erx001-frappe-1 \
#     /workspace/frappe-bench/env/bin/python /workspace/Spike/V26-seg2-crossperiod.py

import inspect
import json
import traceback

import frappe

SITE = "erx.localhost"
COMPANY = "华东弹簧"
OUT = "/workspace/Spike/V26-out/seg2-crossperiod.json"
TPL = "ZZ-PROBE-V26B-CrossPeriod"

result = {"probe": "V-26 seg2: does Closing Balance carry prior-period amounts on P&L accounts"}


def rec(k, v):
    result[k] = v
    print("[" + k + "] " + json.dumps(v, ensure_ascii=False, default=str)[:2200], flush=True)


frappe.init(site=SITE)
frappe.connect()
frappe.set_user("Administrator")

try:
    # ---------- 0. the thing that would zero P&L at a year boundary ----------
    rec("period_closing_vouchers", frappe.get_all(
        "Period Closing Voucher",
        fields=["name", "docstatus", "period_end_date", "closing_account_head", "company"]))
    rec("accounts_settings_flags", {
        "ignore_account_closing_balance": frappe.get_single_value(
            "Accounts Settings", "ignore_account_closing_balance"),
        "ignore_is_opening_check_for_reporting": frappe.get_single_value(
            "Accounts Settings", "ignore_is_opening_check_for_reporting"),
    })
    rec("account_closing_balance_rows", frappe.db.count("Account Closing Balance"))

    # ---------- 1. the code path that decides opening balances ----------
    from erpnext.accounts.doctype.financial_report_template import financial_report_engine as fre

    rec("get_opening_balances_source",
        inspect.getsource(fre.FinancialQueryBuilder._get_opening_balances))
    rec("get_opening_balances_from_gl_source",
        inspect.getsource(fre.FinancialQueryBuilder._get_opening_balances_from_gl))
    rec("rebase_closing_balances_source",
        inspect.getsource(fre.FinancialQueryBuilder._rebase_closing_balances))

    # ---------- 2. independent truth: all P&L GL, with dates ----------
    pl_accounts = frappe.get_all(
        "Account",
        filters={"company": COMPANY, "is_group": 0, "root_type": ["in", ["Income", "Expense"]]},
        pluck="name")
    gl = frappe.get_all(
        "GL Entry",
        filters={"company": COMPANY, "is_cancelled": 0, "account": ["in", pl_accounts]},
        fields=["account", "posting_date", "debit", "credit", "is_opening", "voucher_type"],
        order_by="posting_date")
    rec("raw_pl_gl_entries", [dict(r) for r in gl])
    rec("raw_pl_net", round(sum((r.debit or 0) - (r.credit or 0) for r in gl), 4))

    # ---------- 3. temp template: same accounts, the two balance types ----------
    inc_filter = json.dumps(["root_type", "=", "Income"])
    exp_filter = json.dumps(["root_type", "=", "Expense"])
    rows = [
        {"data_source": "Column Break", "display_name": "CLOSING"},
        {"data_source": "Account Data", "display_name": "Income CLOSING",
         "reference_code": "C_INC", "balance_type": "Closing Balance",
         "calculation_formula": inc_filter, "reverse_sign": 1, "fieldtype": "Currency"},
        {"data_source": "Account Data", "display_name": "Expense CLOSING",
         "reference_code": "C_EXP", "balance_type": "Closing Balance",
         "calculation_formula": exp_filter, "fieldtype": "Currency"},
        {"data_source": "Column Break", "display_name": "MOVEMENT"},
        {"data_source": "Account Data", "display_name": "Income MOVEMENT",
         "reference_code": "M_INC", "balance_type": "Period Movement (Debits - Credits)",
         "calculation_formula": inc_filter, "reverse_sign": 1, "fieldtype": "Currency"},
        {"data_source": "Account Data", "display_name": "Expense MOVEMENT",
         "reference_code": "M_EXP", "balance_type": "Period Movement (Debits - Credits)",
         "calculation_formula": exp_filter, "fieldtype": "Currency"},
    ]
    doc = frappe.get_doc({
        "doctype": "Financial Report Template",
        "template_name": TPL,
        "report_type": "Profit and Loss Statement",
        "rows": rows,
    })
    doc.insert(ignore_permissions=True)
    rec("template_inserted", {"name": doc.name, "module": doc.module})

    from erpnext.accounts.doctype.financial_report_template.financial_report_engine import (
        FinancialReportEngine,
    )

    def run(label, extra):
        base = {
            "company": COMPANY, "report_template": doc.name,
            "selected_view": "Report", "include_default_book_entries": 1,
        }
        base.update(extra)
        try:
            res = FinancialReportEngine().execute(frappe._dict(base))
            cols, data = res[0], res[1]
            period_keys = [c["fieldname"] for c in cols
                           if c["fieldname"].startswith("seg_0_")
                           and c["fieldname"] not in (
                               "seg_0_account", "seg_0_acc_name",
                               "seg_0_acc_number", "seg_0_currency")]
            out = {"filters": base, "seg_0_period_fields": period_keys, "rows": []}
            for r in data:
                row = {"closing_name": r.get("seg_0_account_name"),
                       "movement_name": r.get("seg_1_account_name")}
                for pk in period_keys:
                    suffix = pk[len("seg_0_"):]
                    row["CLOSING_" + suffix] = r.get("seg_0_" + suffix)
                    row["MOVEMENT_" + suffix] = r.get("seg_1_" + suffix)
                out["rows"].append(row)
            rec("run_" + label, out)
            return out
        except Exception as e:
            rec("run_error_" + label, {"err": str(e), "tb": traceback.format_exc()[-1200:]})
            return None

    # (a) period STARTS AFTER all the GL -- the decisive run
    after = run("range_Q4_after_all_GL", {
        "filter_based_on": "Date Range",
        "period_start_date": "2026-10-01", "period_end_date": "2026-12-31",
        "periodicity": "Monthly",
    })

    # (b) control: period CONTAINS the GL
    run("range_Sep_to_Dec_contains_GL", {
        "filter_based_on": "Date Range",
        "period_start_date": "2026-09-01", "period_end_date": "2026-12-31",
        "periodicity": "Monthly",
    })

    # (c) Yearly over the one fiscal year -- how many columns per segment?
    yearly = run("fiscal_2026_yearly", {
        "filter_based_on": "Fiscal Year",
        "from_fiscal_year": "2026", "to_fiscal_year": "2026",
        "periodicity": "Yearly",
    })
    if yearly:
        rec("yearly_column_count_per_segment", len(yearly["seg_0_period_fields"]))

    # ---------- 4. verdict ----------
    verdict = {}
    if after and after["rows"]:
        inc = next((r for r in after["rows"] if r.get("closing_name") == "Income CLOSING"), None)
        if inc:
            oct_c = inc.get("CLOSING_oct_2026")
            oct_m = inc.get("MOVEMENT_oct_2026")
            verdict = {
                "income_CLOSING_in_Oct_when_period_starts_Oct": oct_c,
                "income_MOVEMENT_in_Oct_when_period_starts_Oct": oct_m,
                "closing_carries_prior_period_amounts": bool(oct_c not in (0, 0.0, None, "")),
                "movement_is_period_scoped": oct_m in (0, 0.0),
            }
    verdict["implication"] = (
        "if closing_carries_prior_period_amounts is true, Closing Balance is a "
        "running balance from the beginning of time, NOT a fiscal-year-to-date "
        "figure -- so it only equals 本年累计金额 while no prior year has P&L "
        "activity, or while a Period Closing Voucher zeroes it at year end")
    rec("DECISIVE_seg2", verdict)

except Exception as e:
    rec("probe_error", {"err": str(e), "tb": traceback.format_exc()[-2500:]})

finally:
    frappe.db.rollback()
    rec("template_exists_after_rollback", bool(frappe.db.exists("Financial Report Template", TPL)))
    rec("frt_count_final", frappe.db.count("Financial Report Template"))
    rec("gl_count_final", frappe.db.count("GL Entry"))

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)
    print("\nWROTE " + OUT, flush=True)
