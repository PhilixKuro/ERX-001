"""
V-27 seg5: can ANY engine setting produce a correct 本年累计金额 in year 2+?

seg4 found that with `Date Range` 2026-01-01..2026-09-30 + periodicity Yearly,
the `Period Movement (Debits - Credits)` cell read 1045.0 -- which happens to
equal the correct year-to-date income. But that number CANNOT be trusted as
evidence of cumulative behaviour on this site, because ALL 2026 P&L GL sits in
a single month (2026-09). "Jan..Sep cumulative" and "Sep alone" are the same
number there, so the observation does not discriminate.

This segment makes them discriminate by adding a SECOND 2026 month:
    2026-03-31 income 700  (new)
    2026-09-21 income 1045 (existing)
  => correct 本年累计 through Sep = 1745 ; Sep alone = 1045
Plus the prior-year 2025 income 5000 and a submitted year-end PCV, so the
year-boundary question is live at the same time.

Three things get measured on ONE site state (prior year closed by PCV):
  (M1) Monthly + Closing Balance      -- does it restart in 2026? (the V-27 core)
  (M2) Monthly + Period Movement      -- is it really per-month (=本月金额)?
  (M3) YTD Date Range + Yearly
       + Period Movement              -- does it equal 1745 (true YTD) or 1045?
  (M4) `ignore_account_closing_balance` ON, as a second opening-balance path,
       to check whether that setting changes the year-boundary answer.

Writes: FY2025, 2 JEs, template, PCV, GL, ACB, and a Single-value toggle -- all
in ONE transaction, rolled back. Guards make db.commit / enqueue raise.
The Accounts Settings toggle is a Single DocType write; it is inside the same
transaction and its pre-probe value is recorded and re-asserted after rollback.
"""

import json
import os
import traceback

import frappe

SITE = "erx.localhost"
COMPANY = "华东弹簧"
OUT_DIR = "/workspace/Spike/V27-out"
OUT = os.path.join(OUT_DIR, "seg5-ytd-alt.json")

TPL = "ZZ-PROBE-V27-SEG5"
INCOME_ACC = "销售 - HDS"
CASH_ACC = "现金 - HDS"
CLOSING_HEAD = "留存收益 - HDS"
PRIOR_AMT = 5000.0
MAR_AMT = 700.0
SEP_EXISTING = 1045.0

res = {"probe": "V-27 seg5 is any setting able to yield a correct 本年累计 in year 2+"}


def rec(k, v):
    res[k] = v
    print("[" + k + "] " + json.dumps(v, ensure_ascii=False, default=str)[:2400], flush=True)


frappe.init(site=SITE)
frappe.connect()
frappe.set_user("Administrator")

GUARD_HITS = []


def _blocked(name):
    def f(*a, **kw):
        GUARD_HITS.append({"call": name})
        raise RuntimeError("V27-GUARD: " + name + " blocked")
    return f


import frappe.utils.background_jobs as _bj
from frappe.database.database import Database as _Db

_oc, _oe, _ob = _Db.commit, frappe.enqueue, _bj.enqueue
_Db.commit = _blocked("db.commit")
frappe.enqueue = _blocked("frappe.enqueue")
_bj.enqueue = _blocked("background_jobs.enqueue")


def clear_fy_cache():
    for fn in (lambda: frappe.cache().hdel("fiscal_years", COMPANY),
               lambda: frappe.cache().delete_key("fiscal_years")):
        try:
            fn()
        except Exception:
            pass
    frappe.local.cache = {}


clear_fy_cache()
DTS = ("GL Entry", "Stock Ledger Entry", "Account", "Company",
       "Financial Report Template", "Fiscal Year", "Period Closing Voucher",
       "Account Closing Balance", "Journal Entry")


def counts():
    return {d: frappe.db.count(d) for d in DTS}


BASELINE = counts()
ORIG_IGNORE_ACB = frappe.get_single_value("Accounts Settings",
                                          "ignore_account_closing_balance")
rec("BASELINE_counts", BASELINE)
rec("ORIGINAL_ignore_account_closing_balance", ORIG_IGNORE_ACB)


def add_income_je(date, amt, remark):
    je = frappe.get_doc({
        "doctype": "Journal Entry", "voucher_type": "Journal Entry",
        "company": COMPANY, "posting_date": date, "user_remark": remark,
        "accounts": [
            {"account": CASH_ACC, "debit_in_account_currency": amt,
             "credit_in_account_currency": 0},
            {"account": INCOME_ACC, "debit_in_account_currency": 0,
             "credit_in_account_currency": amt}]})
    je.insert(ignore_permissions=True)
    je.submit()
    return je.name


def make_template():
    inc = json.dumps(["root_type", "=", "Income"])
    return frappe.get_doc({
        "doctype": "Financial Report Template", "template_name": TPL,
        "report_type": "Profit and Loss Statement",
        # module EMPTY on purpose
        "rows": [
            {"data_source": "Column Break", "display_name": "累计列(Closing Balance)"},
            {"data_source": "Account Data", "display_name": "收入-CB",
             "reference_code": "CB_INC", "balance_type": "Closing Balance",
             "calculation_formula": inc, "reverse_sign": 1, "fieldtype": "Currency"},
            {"data_source": "Column Break", "display_name": "发生额列(Period Movement)"},
            {"data_source": "Account Data", "display_name": "收入-PM",
             "reference_code": "PM_INC",
             "balance_type": "Period Movement (Debits - Credits)",
             "calculation_formula": inc, "reverse_sign": 1, "fieldtype": "Currency"},
        ]}).insert(ignore_permissions=True)


def run_engine(tpl_name, arm, extra=None, watch=None):
    from erpnext.accounts.doctype.financial_report_template.financial_report_engine import (
        FinancialReportEngine,
    )
    filters = frappe._dict({
        "company": COMPANY, "report_template": tpl_name,
        "filter_based_on": "Fiscal Year",
        "from_fiscal_year": "2026", "to_fiscal_year": "2026",
        "periodicity": "Monthly", "selected_view": "Report",
        "include_default_book_entries": 1,
    })
    if extra:
        filters.update(extra)
    cols, data = FinancialReportEngine().execute(filters)[:2]
    keys = watch or ["jan_2026", "mar_2026", "sep_2026", "dec_2026"]
    out = {}
    for r in data:
        nm = r.get("seg_0_account_name") or r.get("seg_1_account_name")
        if not nm:
            continue
        cell = {}
        for m in keys:
            cell["CB_" + m] = r.get("seg_0_" + m)
            cell["PM_" + m] = r.get("seg_1_" + m)
        out[nm] = cell
    rec("engine_" + arm, {"cells": out,
                          "visible_cols": len([c for c in cols if not c.get("hidden")])})
    return out


try:
    # ---------------- prior year + PCV, and a SECOND current-year month -------
    frappe.get_doc({"doctype": "Fiscal Year", "year": "2025",
                    "year_start_date": "2025-01-01",
                    "year_end_date": "2025-12-31"}).insert(ignore_permissions=True)
    clear_fy_cache()
    from erpnext.accounts.utils import get_fiscal_year
    if not get_fiscal_year("2025-06-30", company=COMPANY, raise_on_missing=False):
        raise RuntimeError("V27-ABORT: FY2025 unresolvable")

    je25 = add_income_je("2025-06-30", PRIOR_AMT, "V27 seg5 prior-year income")
    je26 = add_income_je("2026-03-31", MAR_AMT, "V27 seg5 second current-year month")
    rec("journal_entries", {"prior_2025": je25, "current_2026_03": je26})

    # independent raw truth, BEFORE any PCV reversal touches it
    raw = frappe.db.sql(
        """SELECT LEFT(gle.posting_date,7) AS ym,
                  SUM(gle.credit-gle.debit) AS income_credit_net
             FROM `tabGL Entry` gle JOIN `tabAccount` a ON a.name=gle.account
            WHERE gle.company=%s AND gle.is_cancelled=0 AND a.root_type='Income'
            GROUP BY ym ORDER BY ym""", (COMPANY,), as_dict=True)
    rec("RAW_income_by_month_BEFORE_pcv", raw)
    ytd_through_sep = round(MAR_AMT + SEP_EXISTING, 2)
    rec("EXPECTED_values", {
        "correct_本年累计_through_sep_2026": ytd_through_sep,
        "sep_alone_本月": SEP_EXISTING,
        "mar_alone_本月": MAR_AMT,
        "since_inception_through_sep": round(PRIOR_AMT + ytd_through_sep, 2),
        "why": "mar and sep now differ, so cumulative vs single-month are "
               "distinguishable -- seg4 could not tell them apart",
    })

    tpl = make_template()

    # ---------------- close 2025 with a year-end PCV ----------------
    pcv = frappe.get_doc({
        "doctype": "Period Closing Voucher", "company": COMPANY,
        "fiscal_year": "2025",
        "period_start_date": "2025-01-01", "period_end_date": "2025-12-31",
        "closing_account_head": CLOSING_HEAD,
        "remarks": "V27 seg5 year-end close of 2025",
        "transaction_date": "2025-12-31"})
    pcv.insert(ignore_permissions=True)
    pcv.submit()
    pcv.reload()
    rec("pcv_submitted", {"name": pcv.name, "docstatus": pcv.docstatus,
                          "status": pcv.gle_processing_status})

    # ---- M1 + M2: Monthly, both balance types, prior year CLOSED ----
    m12 = run_engine(tpl.name, "M1M2_monthly_after_pcv")

    # ---- M3: YTD date range (Jan 1 -> Sep 30), Yearly => one YTD period ----
    m3 = run_engine(tpl.name, "M3_ytd_range_yearly", extra={
        "filter_based_on": "Date Range",
        "period_start_date": "2026-01-01", "period_end_date": "2026-09-30",
        "periodicity": "Yearly"}, watch=["sep_2026"])

    # ---- M4: the other opening-balance path ----
    frappe.db.set_single_value("Accounts Settings", "ignore_account_closing_balance", 1)
    frappe.clear_cache()
    rec("ignore_acb_now", frappe.get_single_value("Accounts Settings",
                                                  "ignore_account_closing_balance"))
    m4 = run_engine(tpl.name, "M4_monthly_ignore_acb_on")
    frappe.db.set_single_value("Accounts Settings", "ignore_account_closing_balance",
                               ORIG_IGNORE_ACB or 0)
    frappe.clear_cache()
    rec("ignore_acb_restored_in_txn",
        frappe.get_single_value("Accounts Settings", "ignore_account_closing_balance"))

    # ---------------- decisive ----------------
    k = "收入-CB"
    cb = m12.get(k, {})
    pm3 = m3.get(k, {})
    cb4 = m4.get(k, {})
    rec("DECISIVE_seg5", {
        "M1_monthly_closing_balance": {"jan": cb.get("CB_jan_2026"),
                                       "mar": cb.get("CB_mar_2026"),
                                       "sep": cb.get("CB_sep_2026"),
                                       "dec": cb.get("CB_dec_2026")},
        "M1_jan_should_be_0_if_pcv_resets": cb.get("CB_jan_2026") in (0, 0.0),
        "M1_sep_true_ytd_would_be": ytd_through_sep,
        "M1_sep_since_inception_would_be": round(PRIOR_AMT + ytd_through_sep, 2),
        "M2_monthly_period_movement": {"mar": cb.get("PM_mar_2026"),
                                       "sep": cb.get("PM_sep_2026")},
        "M2_is_true_per_month": (cb.get("PM_mar_2026") == MAR_AMT
                                 and cb.get("PM_sep_2026") == SEP_EXISTING),
        "M3_ytd_range_period_movement_sep": pm3.get("PM_sep_2026"),
        "M3_equals_true_ytd_1745": pm3.get("PM_sep_2026") == ytd_through_sep,
        "M3_equals_sep_alone_1045": pm3.get("PM_sep_2026") == SEP_EXISTING,
        "M3_closing_balance_sep": pm3.get("CB_sep_2026"),
        "M4_ignore_acb_closing_balance": {"jan": cb4.get("CB_jan_2026"),
                                          "sep": cb4.get("CB_sep_2026")},
        "M4_changes_year_boundary": cb4.get("CB_jan_2026") != cb.get("CB_jan_2026"),
    })

except Exception as e:
    rec("probe_error", {"err": str(e), "tb": traceback.format_exc()[-3500:]})

finally:
    _Db.commit = _oc
    frappe.db.rollback()
    frappe.enqueue, _bj.enqueue = _oe, _ob
    clear_fy_cache()
    try:
        frappe.clear_cache()
    except Exception:
        pass

    AFTER = counts()
    rec("AFTER_counts", AFTER)
    rec("baseline_restored", AFTER == BASELINE)
    rec("count_deltas", {k2: [BASELINE[k2], AFTER[k2]] for k2 in BASELINE
                         if BASELINE[k2] != AFTER[k2]} or "none")
    rec("fiscal_years_after", [r["name"] for r in frappe.db.get_all("Fiscal Year", fields=["name"])])
    rec("ignore_account_closing_balance_after_rollback",
        frappe.get_single_value("Accounts Settings", "ignore_account_closing_balance"))
    rec("setting_matches_original",
        (frappe.get_single_value("Accounts Settings", "ignore_account_closing_balance")
         or 0) == (ORIG_IGNORE_ACB or 0))
    rec("template_exists_after", bool(frappe.db.exists("Financial Report Template", TPL)))
    rec("guard_hits", GUARD_HITS or "none")
    import glob
    rec("stray_exported_files", glob.glob(frappe.get_app_path(
        "erpnext", "accounts", "financial_report_template", "*SEG5*")) or "none")

    os.makedirs(OUT_DIR, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=2, default=str)
    print("\nWROTE " + OUT, flush=True)
