"""
V-27 seg3: INSTRUMENT the opening-balance path to explain the seg1 surprise.

seg1 (V27-pcv-yearend.py) found ARM B (with a submitted 2025 PCV) byte-identical
to ARM A (no PCV): income Closing Balance jan_2026 = 5000, dec_2026 = 6045 in
BOTH. That has several possible explanations and the report surface cannot tell
them apart:

  (E1) the engine never took the PCV branch at all;
  (E2) it took the branch but _get_closing_balances() returned -5000 instead of
       0, because `Account Closing Balance` holds TWO rows for 销售 (one
       debit 5000, one credit 5000) and something counts only one of them;
  (E3) it took the branch, opening really is 0, and the 5000 re-enters later via
       _get_gl_movements / the gap query;
  (E4) seg1's ARM B measurement was stale.

Also: seg1's own A1/A2 assertions were computed against a raw-GL baseline taken
AFTER the PCV had already reversed 2025 income to zero, so `prior_year_2025_income`
read 0.0 and those two flags were meaningless. This segment captures the raw
prior-year figure BEFORE the PCV and keeps it.

Method: monkeypatch the four functions on the real code path to record their
arguments and return values, then run the SAME engine twice in one transaction
(before and after the PCV). Intermediate values, not report cells, decide.

Writes: FY2025, JE, template, PCV, GL, ACB -- all inside one transaction, rolled
back in finally. Same guards as seg1: db.commit / enqueue raise if called.
"""

import json
import os
import traceback

import frappe

SITE = "erx.localhost"
COMPANY = "华东弹簧"
OUT_DIR = "/workspace/Spike/V27-out"
OUT = os.path.join(OUT_DIR, "seg3-instrument.json")

TPL = "ZZ-PROBE-V27-SEG3"
INCOME_ACC = "销售 - HDS"
CASH_ACC = "现金 - HDS"
CLOSING_HEAD = "留存收益 - HDS"
PRIOR_AMT = 5000.0

res = {"probe": "V-27 seg3 instrument the opening-balance path"}


def rec(k, v):
    res[k] = v
    print("[" + k + "] " + json.dumps(v, ensure_ascii=False, default=str)[:2600], flush=True)


frappe.init(site=SITE)
frappe.connect()
frappe.set_user("Administrator")

# ------------------------------------------------------------------ guards
GUARD_HITS = []


def _blocked(name):
    def f(*a, **kw):
        GUARD_HITS.append({"call": name, "args": str(a)[:200]})
        raise RuntimeError("V27-GUARD: " + name + " blocked")
    return f


import frappe.utils.background_jobs as _bj
from frappe.database.database import Database as _Db

_orig_commit = _Db.commit
_orig_enq = frappe.enqueue
_orig_bj = _bj.enqueue
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


def counts():
    return {d: frappe.db.count(d) for d in
            ("GL Entry", "Stock Ledger Entry", "Account", "Company",
             "Financial Report Template", "Fiscal Year", "Period Closing Voucher",
             "Account Closing Balance", "Journal Entry", "Error Log")}


BASELINE = counts()
rec("BASELINE_counts", BASELINE)

# ------------------------------------------------------------- instrumentation
CALLS = []


def install_instrumentation():
    from erpnext.accounts.doctype.financial_report_template import financial_report_engine as fre
    QB = fre.FinancialQueryBuilder

    o_open = QB._get_opening_balances
    o_close = QB._get_closing_balances
    o_rebase = QB._rebase_closing_balances
    o_gl = QB._get_gl_movements
    o_gap = QB._get_gap_movements

    def w_open(self, accounts):
        out = o_open(self, accounts)
        CALLS.append({
            "fn": "_get_opening_balances",
            "arm": ARM[0],
            "ignore_opening_entries_after": getattr(self, "ignore_opening_entries", None),
            "first_period_from": str(self.periods[0]["from_date"]),
            "returned_for_income": _dump_acct(out.get(INCOME_ACC)),
        })
        return out

    def w_close(self, account_names, closing_voucher):
        out = o_close(self, account_names, closing_voucher)
        CALLS.append({
            "fn": "_get_closing_balances",
            "arm": ARM[0],
            "closing_voucher": closing_voucher,
            "income_closing_balance": out.get(INCOME_ACC),
            "note": "this is Sum(debit-credit) over Account Closing Balance for that PCV",
        })
        return out

    def w_rebase(self, closing_data, closing_date):
        out = o_rebase(self, closing_data, closing_date)
        CALLS.append({
            "fn": "_rebase_closing_balances",
            "arm": ARM[0],
            "closing_date_arg": str(closing_date),
            "income_closing_data_in": closing_data.get(INCOME_ACC),
            "income_opening_out": _dump_acct(out.get(INCOME_ACC)),
        })
        return out

    def w_gl(self, account_names):
        out = o_gl(self, account_names)
        row = next((r for r in out if r.get("account") == INCOME_ACC), None)
        CALLS.append({
            "fn": "_get_gl_movements",
            "arm": ARM[0],
            "ignore_opening_entries": getattr(self, "ignore_opening_entries", None),
            "income_row": {k: v for k, v in (row or {}).items()
                           if k in ("account", "jan_2026", "sep_2026", "dec_2026")},
        })
        return out

    def w_gap(self, account_names, from_date, to_date):
        out = o_gap(self, account_names, from_date, to_date)
        CALLS.append({
            "fn": "_get_gap_movements", "arm": ARM[0],
            "from_date": str(from_date), "to_date": str(to_date),
            "income_gap": out.get(INCOME_ACC),
        })
        return out

    QB._get_opening_balances = w_open
    QB._get_closing_balances = w_close
    QB._rebase_closing_balances = w_rebase
    QB._get_gl_movements = w_gl
    QB._get_gap_movements = w_gap


def _dump_acct(ad):
    """AccountData -> the first period's stored opening numbers."""
    if ad is None:
        return None
    try:
        pv = list(ad.periods.values())[0] if getattr(ad, "periods", None) else None
    except Exception:
        pv = None
    if pv is None:
        return str(ad)[:200]
    return {"period": getattr(pv, "key", None),
            "opening": getattr(pv, "opening", None),
            "closing": getattr(pv, "closing", None),
            "debit": getattr(pv, "debit", None),
            "credit": getattr(pv, "credit", None),
            "repr": str(pv)[:200]}


ARM = ["(unset)"]
WATCH = ["jan_2026", "sep_2026", "dec_2026"]


def run_engine(tpl_name, arm):
    ARM[0] = arm
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
    cols, data = FinancialReportEngine().execute(filters)[:2]
    out = {}
    for r in data:
        nm = r.get("seg_0_account_name")
        if nm:
            out[nm] = {m: r.get("seg_0_" + m) for m in WATCH}
    rec("engine_cells_" + arm, out)
    return out


def raw_pl_by_year():
    rows = frappe.db.sql(
        """SELECT gle.posting_date, a.root_type, gle.debit, gle.credit, gle.voucher_type
             FROM `tabGL Entry` gle JOIN `tabAccount` a ON a.name = gle.account
            WHERE gle.company=%s AND gle.is_cancelled=0
                  AND a.report_type='Profit and Loss'""", (COMPANY,), as_dict=True)
    out = {}
    for r in rows:
        y = str(r["posting_date"])[:4]
        d = out.setdefault(y, {})
        k = r["root_type"]
        d[k] = round(d.get(k, 0.0) + float(r["debit"]) - float(r["credit"]), 4)
    return out


try:
    install_instrumentation()

    # ---- prior year + prior-year P&L ----
    frappe.get_doc({"doctype": "Fiscal Year", "year": "2025",
                    "year_start_date": "2025-01-01",
                    "year_end_date": "2025-12-31"}).insert(ignore_permissions=True)
    clear_fy_cache()
    from erpnext.accounts.utils import get_fiscal_year
    if not get_fiscal_year("2025-06-30", company=COMPANY, raise_on_missing=False):
        raise RuntimeError("V27-ABORT: FY2025 unresolvable, prior-year arm would be inert")

    je = frappe.get_doc({
        "doctype": "Journal Entry", "voucher_type": "Journal Entry",
        "company": COMPANY, "posting_date": "2025-06-30",
        "user_remark": "V27 seg3 prior-year P&L",
        "accounts": [
            {"account": CASH_ACC, "debit_in_account_currency": PRIOR_AMT,
             "credit_in_account_currency": 0},
            {"account": INCOME_ACC, "debit_in_account_currency": 0,
             "credit_in_account_currency": PRIOR_AMT},
        ]})
    je.insert(ignore_permissions=True)
    je.submit()

    # RAW TRUTH CAPTURED BEFORE THE PCV -- seg1's bug was reading this after.
    RAW_BEFORE_PCV = raw_pl_by_year()
    rec("RAW_pl_by_year_BEFORE_pcv", RAW_BEFORE_PCV)
    prior_income_abs = abs(RAW_BEFORE_PCV.get("2025", {}).get("Income", 0.0))
    cur_income_abs = abs(RAW_BEFORE_PCV.get("2026", {}).get("Income", 0.0))
    rec("raw_prior_year_income_abs_BEFORE_pcv", prior_income_abs)
    rec("raw_current_year_income_abs", cur_income_abs)

    tpl = frappe.get_doc({
        "doctype": "Financial Report Template", "template_name": TPL,
        "report_type": "Profit and Loss Statement",
        # module EMPTY on purpose (avoids _export_template writing to source tree)
        "rows": [
            {"data_source": "Column Break", "display_name": "本年累计金额"},
            {"data_source": "Account Data", "display_name": "营业收入(累计)",
             "reference_code": "CUM_INC", "balance_type": "Closing Balance",
             "calculation_formula": json.dumps(["root_type", "=", "Income"]),
             "reverse_sign": 1, "fieldtype": "Currency"},
        ]}).insert(ignore_permissions=True)

    # ---- ARM A: no PCV ----
    cells_a = run_engine(tpl.name, "ARM_A_no_pcv")

    # ---- create + submit year-end PCV for 2025 ----
    pcv = frappe.get_doc({
        "doctype": "Period Closing Voucher", "company": COMPANY,
        "fiscal_year": "2025",
        "period_start_date": "2025-01-01", "period_end_date": "2025-12-31",
        "closing_account_head": CLOSING_HEAD,
        "remarks": "V27 seg3 year-end close of 2025",
        "transaction_date": "2025-12-31"})
    pcv.insert(ignore_permissions=True)
    pcv.submit()
    pcv.reload()
    rec("pcv_submitted", {"name": pcv.name, "docstatus": pcv.docstatus,
                          "status": pcv.gle_processing_status,
                          "err": pcv.error_message})

    # every ACB row for the income account, WITH the discriminating flag
    rec("acb_rows_for_income", frappe.db.sql(
        """SELECT account, debit, credit, closing_date, finance_book, cost_center,
                  project, is_period_closing_voucher_entry, period_closing_voucher
             FROM `tabAccount Closing Balance`
            WHERE account=%s ORDER BY debit DESC""", (INCOME_ACC,), as_dict=True))
    rec("acb_income_net_sum_debit_minus_credit", frappe.db.sql(
        """SELECT SUM(debit-credit) AS net FROM `tabAccount Closing Balance`
            WHERE account=%s AND period_closing_voucher=%s""",
        (INCOME_ACC, pcv.name), as_dict=True))
    rec("RAW_pl_by_year_AFTER_pcv", raw_pl_by_year())

    # ---- ARM B: same report, PCV now present ----
    cells_b = run_engine(tpl.name, "ARM_B_with_pcv")

    rec("INSTRUMENTED_CALLS", CALLS)

    a_inc = cells_a.get("营业收入(累计)", {})
    b_inc = cells_b.get("营业收入(累计)", {})
    rec("DECISIVE_seg3", {
        "raw_prior_year_income_BEFORE_pcv": prior_income_abs,
        "raw_current_year_income": cur_income_abs,
        "ARM_A_income_closing": a_inc,
        "ARM_B_income_closing": b_inc,
        # setup effectiveness, now measured against the PRE-PCV raw figure
        "A1_armA_jan_carries_prior_year": a_inc.get("jan_2026") == prior_income_abs,
        "A2_armA_dec_is_since_inception":
            a_inc.get("dec_2026") == round(prior_income_abs + cur_income_abs, 4),
        # the proposition
        "B1_armB_jan_is_zero": b_inc.get("jan_2026") in (0, 0.0),
        "B2_armB_dec_equals_current_year_only": b_inc.get("dec_2026") == cur_income_abs,
        "B3_arms_differ": a_inc.get("dec_2026") != b_inc.get("dec_2026"),
    })

except Exception as e:
    rec("probe_error", {"err": str(e), "tb": traceback.format_exc()[-3500:]})

finally:
    _Db.commit = _orig_commit
    frappe.db.rollback()
    frappe.enqueue = _orig_enq
    _bj.enqueue = _orig_bj
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
    rec("guard_hits", GUARD_HITS or "none")
    import glob
    rec("stray_exported_files", glob.glob(frappe.get_app_path(
        "erpnext", "accounts", "financial_report_template", "*SEG3*")) or "none")

    os.makedirs(OUT_DIR, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=2, default=str)
    print("\nWROTE " + OUT, flush=True)
