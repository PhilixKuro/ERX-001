"""
V-27 seg4: PROVE the mechanism seg3 exposed, and re-confirm the report surface.

seg3's instrumentation showed that WITH a submitted 2025 year-end PCV the engine
DOES take the closing-balance branch (_get_opening_balances :557-560, and
ignore_opening_entries flipped to True), but _get_closing_balances returned
-5000.0 for the income account instead of 0.0 -- even though the two
`Account Closing Balance` rows for that account net to exactly 0:

    debit 5000 / credit    0 , is_period_closing_voucher_entry = 1  (PCV reversal)
    debit    0 / credit 5000 , is_period_closing_voucher_entry = 0  (carried balance)

Suspected cause: _apply_standard_filters (:723-735) drops ACB rows whose
is_period_closing_voucher_entry = 1 unless the account is a PCV
closing_account_head. That removes the reversal leg and leaves the full
prior-year balance behind.

This segment proves it by running the SAME aggregate three ways against the real
ACB rows and comparing:
    (Q1) no filter at all                      -> expect  0.0
    (Q2) the engine's actual filter             -> expect -5000.0
    (Q3) engine filter, account treated as a
         closing head (the exempted branch)     -> expect  0.0
If Q1 == 0 and Q2 == -5000, the filter is the cause and nothing else is.

It also rebuilds the TWO-segment template so the report surface populates
(seg3 used a single segment, so the `seg_0_` prefixed keys did not exist and its
cell dict came back empty -- the instrumented internals carried that segment).

Side observation (factual, not a recommendation): what `Period Movement` reports
when the report range itself starts at the fiscal-year start, since that bounds
what the engine can express about 本年累计金额.

Writes: FY2025, JE, template, PCV, GL, ACB -- one transaction, rolled back.
Guards: db.commit / enqueue raise if anything tries to escape.
"""

import json
import os
import traceback

import frappe

SITE = "erx.localhost"
COMPANY = "华东弹簧"
OUT_DIR = "/workspace/Spike/V27-out"
OUT = os.path.join(OUT_DIR, "seg4-filter-proof.json")

TPL = "ZZ-PROBE-V27-SEG4"
INCOME_ACC = "销售 - HDS"
CASH_ACC = "现金 - HDS"
CLOSING_HEAD = "留存收益 - HDS"
PRIOR_AMT = 5000.0

res = {"probe": "V-27 seg4 prove the ACB PCV-entry filter causes the non-reset"}


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
       "Account Closing Balance", "Journal Entry", "Error Log")


def counts():
    return {d: frappe.db.count(d) for d in DTS}


BASELINE = counts()
rec("BASELINE_counts", BASELINE)

WATCH = ["jan_2026", "sep_2026", "oct_2026", "dec_2026"]


def make_template():
    inc = json.dumps(["root_type", "=", "Income"])
    exp = json.dumps(["root_type", "=", "Expense"])
    return frappe.get_doc({
        "doctype": "Financial Report Template", "template_name": TPL,
        "report_type": "Profit and Loss Statement",
        # module EMPTY on purpose: _export_template() would write to the source tree
        "rows": [
            {"data_source": "Column Break", "display_name": "本年累计金额"},
            {"data_source": "Account Data", "display_name": "营业收入(累计)",
             "reference_code": "CUM_INC", "balance_type": "Closing Balance",
             "calculation_formula": inc, "reverse_sign": 1, "fieldtype": "Currency"},
            {"data_source": "Account Data", "display_name": "营业成本(累计)",
             "reference_code": "CUM_EXP", "balance_type": "Closing Balance",
             "calculation_formula": exp, "fieldtype": "Currency"},
            {"data_source": "Column Break", "display_name": "本月金额"},
            {"data_source": "Account Data", "display_name": "营业收入(本月)",
             "reference_code": "MTH_INC",
             "balance_type": "Period Movement (Debits - Credits)",
             "calculation_formula": inc, "reverse_sign": 1, "fieldtype": "Currency"},
        ]}).insert(ignore_permissions=True)


def run_engine(tpl_name, arm, extra=None):
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
    out = {}
    for r in data:
        nm = r.get("seg_0_account_name") or r.get("seg_1_account_name") or r.get("account_name")
        if not nm:
            continue
        cell = {}
        for m in WATCH:
            for pref in ("seg_0_", "seg_1_", ""):
                key = pref + m
                if r.get(key) is not None:
                    cell[pref + m] = r.get(key)
        out[nm] = cell
    rec("engine_cells_" + arm, out)
    return out


try:
    # ---------------- setup: prior year with P&L movement ----------------
    frappe.get_doc({"doctype": "Fiscal Year", "year": "2025",
                    "year_start_date": "2025-01-01",
                    "year_end_date": "2025-12-31"}).insert(ignore_permissions=True)
    clear_fy_cache()
    from erpnext.accounts.utils import get_fiscal_year
    if not get_fiscal_year("2025-06-30", company=COMPANY, raise_on_missing=False):
        raise RuntimeError("V27-ABORT: FY2025 unresolvable; prior-year arm inert")

    je = frappe.get_doc({
        "doctype": "Journal Entry", "voucher_type": "Journal Entry",
        "company": COMPANY, "posting_date": "2025-06-30",
        "user_remark": "V27 seg4 prior-year P&L",
        "accounts": [
            {"account": CASH_ACC, "debit_in_account_currency": PRIOR_AMT,
             "credit_in_account_currency": 0},
            {"account": INCOME_ACC, "debit_in_account_currency": 0,
             "credit_in_account_currency": PRIOR_AMT}]})
    je.insert(ignore_permissions=True)
    je.submit()
    rec("prior_year_je", {"name": je.name, "amount": PRIOR_AMT,
                          "posting_date": str(je.posting_date)})

    tpl = make_template()
    cells_a = run_engine(tpl.name, "ARM_A_no_pcv")

    # ---------------- submit the year-end PCV ----------------
    pcv = frappe.get_doc({
        "doctype": "Period Closing Voucher", "company": COMPANY,
        "fiscal_year": "2025",
        "period_start_date": "2025-01-01", "period_end_date": "2025-12-31",
        "closing_account_head": CLOSING_HEAD,
        "remarks": "V27 seg4 year-end close of 2025",
        "transaction_date": "2025-12-31"})
    pcv.insert(ignore_permissions=True)
    pcv.submit()
    pcv.reload()
    rec("pcv_submitted", {"name": pcv.name, "docstatus": pcv.docstatus,
                          "status": pcv.gle_processing_status, "err": pcv.error_message})

    cells_b = run_engine(tpl.name, "ARM_B_with_pcv")

    # ---------------- THE MECHANISM PROOF: same aggregate, three filterings ----
    # Q1: no filter -- the true net of what the PCV stored
    q1 = frappe.db.sql(
        """SELECT SUM(debit-credit) AS net, COUNT(*) AS rows_counted
             FROM `tabAccount Closing Balance`
            WHERE account=%s AND period_closing_voucher=%s AND company=%s""",
        (INCOME_ACC, pcv.name, COMPANY), as_dict=True)[0]

    # Q2: the engine's own filter (financial_report_engine.py:729-735)
    q2 = frappe.db.sql(
        """SELECT SUM(acb.debit-acb.credit) AS net, COUNT(*) AS rows_counted
             FROM `tabAccount Closing Balance` acb
            WHERE acb.account=%s AND acb.period_closing_voucher=%s AND acb.company=%s
              AND ( acb.is_period_closing_voucher_entry != 1
                    OR acb.account IN (SELECT closing_account_head
                                         FROM `tabPeriod Closing Voucher`
                                        WHERE docstatus=1) )""",
        (INCOME_ACC, pcv.name, COMPANY), as_dict=True)[0]

    # Q3: same filter but for the closing-account-head (the exempted branch)
    q3 = frappe.db.sql(
        """SELECT SUM(acb.debit-acb.credit) AS net, COUNT(*) AS rows_counted
             FROM `tabAccount Closing Balance` acb
            WHERE acb.account=%s AND acb.period_closing_voucher=%s AND acb.company=%s
              AND ( acb.is_period_closing_voucher_entry != 1
                    OR acb.account IN (SELECT closing_account_head
                                         FROM `tabPeriod Closing Voucher`
                                        WHERE docstatus=1) )""",
        (CLOSING_HEAD, pcv.name, COMPANY), as_dict=True)[0]

    rec("MECHANISM_PROOF", {
        "Q1_income_no_filter": q1,
        "Q2_income_engine_filter": q2,
        "Q3_closing_head_engine_filter": q3,
        "acb_rows_income": frappe.db.sql(
            """SELECT debit, credit, is_period_closing_voucher_entry
                 FROM `tabAccount Closing Balance`
                WHERE account=%s AND period_closing_voucher=%s
                ORDER BY debit DESC""", (INCOME_ACC, pcv.name), as_dict=True),
        "interpretation": (
            "Q1 is the true net the PCV stored; Q2 is what the engine actually "
            "aggregates. If Q1=0 and Q2=-5000 the ACB "
            "is_period_closing_voucher_entry filter is the sole cause of the "
            "prior year surviving into the new year's opening balance."),
    })

    # ---------------- side observation: Period Movement over a YTD range -------
    # Factual observation only. Range starts at FY start, Yearly periodicity, so
    # the single period IS Jan-1..Sep-30 -- i.e. a year-to-date span.
    ytd = run_engine(tpl.name, "YTD_range_jan_to_sep_yearly", extra={
        "filter_based_on": "Date Range",
        "period_start_date": "2026-01-01", "period_end_date": "2026-09-30",
        "periodicity": "Yearly",
    })

    # ---------------- decisive ----------------
    a = cells_a.get("营业收入(累计)", {})
    b = cells_b.get("营业收入(累计)", {})
    rec("DECISIVE_seg4", {
        "ARM_A_no_pcv_income": a,
        "ARM_B_with_pcv_income": b,
        "raw_prior_year_income": PRIOR_AMT,
        "raw_current_year_income": 1045.0,
        "arms_identical": a == b,
        "armB_jan_is_zero__PROPOSITION": (b.get("seg_0_jan_2026") in (0, 0.0)),
        "armB_dec_equals_current_year_only":
            b.get("seg_0_dec_2026") == 1045.0,
        "armB_dec_actual": b.get("seg_0_dec_2026"),
        "armB_dec_expected_if_ytd": 1045.0,
        "armB_dec_expected_if_since_inception": 6045.0,
        "q1_vs_q2_gap": [q1.get("net"), q2.get("net")],
        "VERDICT_pcv_makes_closing_balance_ytd": bool(
            b.get("seg_0_jan_2026") in (0, 0.0)
            and b.get("seg_0_dec_2026") == 1045.0),
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
    rec("count_deltas", {k: [BASELINE[k], AFTER[k]] for k in BASELINE
                         if BASELINE[k] != AFTER[k]} or "none")
    rec("fiscal_years_after", [r["name"] for r in frappe.db.get_all("Fiscal Year", fields=["name"])])
    rec("pcv_count_after", frappe.db.count("Period Closing Voucher"))
    rec("acb_count_after", frappe.db.count("Account Closing Balance"))
    rec("template_exists_after", bool(frappe.db.exists("Financial Report Template", TPL)))
    rec("guard_hits", GUARD_HITS or "none")
    import glob
    rec("stray_exported_files", glob.glob(frappe.get_app_path(
        "erpnext", "accounts", "financial_report_template", "*SEG4*")) or "none")

    os.makedirs(OUT_DIR, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=2, default=str)
    print("\nWROTE " + OUT, flush=True)
