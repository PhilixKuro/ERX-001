"""
V-27 probe: after a year-end Period Closing Voucher (PCV) is submitted for the
PRIOR fiscal year, does the NEXT year's report show P&L accounts' `Closing
Balance` starting from the current year -- i.e. does it stop folding the prior
year's movements into the opening balance, so that `Closing Balance` genuinely
equals the statutory Chinese "本年累计金额" (year-to-date cumulative)?

V-26 proved `Closing Balance` is a ROLLING balance since inception when no PCV
exists: `_get_opening_balances()` falls back to `_get_opening_balances_from_gl()`
which starts at 1900-01-01, and `_rebase_closing_balances()` folds ALL prior GL
into opening. V-26 did NOT test the PCV branch (engine :536-547) because making
a PCV is a real write. This probe tests it.

------------------------------------------------------------------ DESIGN
The site has only FY2026, and all P&L GL sits in 2026-09 (raw total -719.5).
So this probe MANUFACTURES a prior year inside the transaction:

  FY2025 + a 2025 Journal Entry with P&L movement (credit 销售 5000)

Then it runs the SAME report twice, as a controlled A/B:

  ARM A: FY2025 + 2025 JE, NO PCV        -> expect prior-year 5000 folded in
  ARM B: same, PLUS submitted PCV @2025-12-31 -> expect prior year excluded

ARM A IS NOT OPTIONAL. Without it, seeing 1045 in arm B has two possible
explanations -- "the PCV correctly excluded 2025" or "my 2025 JE was inert and
never reached the report at all". Arm A rules the second one out by showing the
same report DOES fold 5000 in when the PCV is absent. Same transaction, same
template, same filters; the ONLY difference between arms is the PCV.

Predicted discriminator (income row, `Closing Balance`, FY2026 Monthly):
                       jan_2026     dec_2026
  ARM A (no PCV)         5000        6045      (= 5000 prior + 1045 current)
  ARM B (PCV)               0        1045      (= current year only)
Control: the expense row has NO 2025 movement, so it must read 325.5 in BOTH
arms. If the expense control moves between arms, the probe is measuring
something other than prior-year exclusion.

Every engine number is cross-checked against an independently computed raw-GL
sum (no engine involved).

--------------------------------------------------------- SITE SAFETY
The demo site carries demo data. This probe writes REAL documents (Fiscal Year,
Journal Entry, GL Entry, Period Closing Voucher, Account Closing Balance) and
relies on ONE transaction + rollback. Three layers of protection:

 1. GREP AUDIT of the whole legacy submit path (done before writing this file):
      - on_submit (:258) branches on Accounts Settings.use_legacy_controller_for_pcv.
        Site value = 1 -> LEGACY branch -> make_gl_entries(). The non-legacy
        branch builds a `Process Period Closing Voucher`, whose module DOES
        commit (:131,:285,:462,:612) and enqueue (:116,:287,:318). That branch
        is NOT taken, so those are unreachable here.
      - make_gl_entries (:297) enqueues ONLY when
        frappe.db.estimate_count("GL Entry") > 100_000. Measured: 22. So it
        calls process_gl_and_closing_entries(self) directly, in-process.
      - general_ledger.py, account_closing_balance.py, journal_entry.py,
        accounts_controller.py, fiscal_year.py, accounting_period.py,
        frappe/utils/error.py: ZERO db.commit / enqueue (grepped).
      - gl_entry.py:493 commit is inside rename_temporarily_named_docs, reached
        only from the scheduler hook rename_gle_sle_docs (hooks.py:440).
      - accounts/utils.py:1689 commit is in repost_gle_for_stock_vouchers;
        :1963 enqueue is a scheduler-driven revaluation. Neither on this path.
      - document.py commits are behind opt-in flags (db_set(commit=False)
        default; bulk_insert commit_chunks). queue_action is never reached:
        submit() -> _submit() -> save(), and PCV json has no queue_in_background.
      - set_amount_in_reporting_currency -> get_exchange_rate(CNY, CNY) returns
        1 at setup/utils.py:66-67 BEFORE the requests.get branch. Verified
        default_currency == reporting_currency == CNY, so no outbound HTTP.
 2. RUNTIME GUARDS (this file): db.commit, frappe.enqueue, enqueue_doc and
    background_jobs.enqueue are patched to RECORD AND RAISE. A grep proves what
    the source says; these prove what the process actually did. If anything on
    the path tries to escape the transaction it aborts instead of persisting.
 3. before_submit avoidance: perpetual inventory IS on and 12 SLE rows exist,
    so a PCV at 2026-12-31 would demand a Stock Closing Entry (whose submit
    enqueues). Closing 2025 instead makes has_stock_transactions() false (no SLE
    on/before 2025-12-31), so that whole stock branch is skipped by design.

No frappe.db.commit() is ever called by this file. Redis is NOT transactional,
so the `fiscal_years` cache key is deleted in the finally block -- otherwise a
phantom rolled-back FY2025 could linger in cache.

`module` on the temp template is left EMPTY on purpose: FinancialReportTemplate.
on_update -> _export_template() writes JSON into the erpnext source tree when
module is set, and rollback cannot undo a filesystem write.

Run (cwd MUST be .../sites, else frappe's logger dies on a relative path):
  docker exec -i -w /workspace/frappe-bench/sites erx001-frappe-1 \
    /workspace/frappe-bench/env/bin/python /workspace/Spike/V27-pcv-yearend.py
"""

import json
import os
import traceback

import frappe

SITE = "erx.localhost"
COMPANY = "华东弹簧"
OUT_DIR = "/workspace/Spike/V27-out"
OUT = os.path.join(OUT_DIR, "pcv-yearend.json")

TPL = "ZZ-PROBE-V27-PL-YearEnd"
PRIOR_FY = "2025"
PRIOR_JE_AMOUNT = 5000.0
INCOME_ACC = "销售 - HDS"
CASH_ACC = "现金 - HDS"
CLOSING_HEAD = "留存收益 - HDS"  # Equity, CNY

result = {"probe": "V-27 year-end PCV makes Closing Balance restart per year"}


def rec(k, v):
    result[k] = v
    print("[" + k + "] " + json.dumps(v, ensure_ascii=False, default=str)[:2400], flush=True)


frappe.init(site=SITE)
frappe.connect()
frappe.set_user("Administrator")

# ------------------------------------------------------------------ RUNTIME GUARDS
# Any attempt to commit or enqueue on the path aborts rather than persisting.
GUARD_HITS = []


def _blocked_commit(*a, **kw):
    GUARD_HITS.append({"call": "frappe.db.commit", "stack": traceback.format_stack()[-6:-1]})
    raise RuntimeError("V27-GUARD: db.commit() blocked -- transaction must stay open")


def _blocked_enqueue(*a, **kw):
    GUARD_HITS.append({"call": "enqueue", "args": str(a)[:300],
                       "stack": traceback.format_stack()[-6:-1]})
    raise RuntimeError("V27-GUARD: enqueue() blocked -- no background job may escape")


import frappe.utils.background_jobs as _bj
from frappe.database.database import Database as _Db

_orig = {
    "db_commit": _Db.commit,
    "frappe_enqueue": frappe.enqueue,
    "frappe_enqueue_doc": getattr(frappe, "enqueue_doc", None),
    "bj_enqueue": _bj.enqueue,
}
_Db.commit = _blocked_commit
frappe.enqueue = _blocked_enqueue
if _orig["frappe_enqueue_doc"] is not None:
    frappe.enqueue_doc = _blocked_enqueue
_bj.enqueue = _blocked_enqueue

rec("guards_installed", {
    "db.commit": "raises",
    "frappe.enqueue": "raises",
    "frappe.enqueue_doc": "raises",
    "background_jobs.enqueue": "raises",
    "note": "grep proves what the source says; these prove what the process did",
})
rec("frappe_in_test_flag", bool(getattr(frappe, "in_test", False)))


def count_all():
    dts = ("GL Entry", "Stock Ledger Entry", "Account", "Company",
           "Financial Report Template", "Fiscal Year", "Period Closing Voucher",
           "Account Closing Balance", "Journal Entry", "Error Log")
    return {d: frappe.db.count(d) for d in dts}


def series_rows():
    return {r["name"]: r["current"] for r in frappe.db.sql(
        "SELECT name, current FROM `tabSeries` ORDER BY name", as_dict=True)}


def clear_fy_cache(tag):
    """Drop the non-transactional `fiscal_years` cache.

    accounts/utils.py:146,171 store it as a Redis HASH keyed by company, and
    redis_wrapper.hget() consults frappe.local.cache FIRST, so both layers must
    go. FiscalYear.on_update (fiscal_year.py:37) only calls delete_key, which
    left a stale entry visible across processes after a rollback.
    """
    notes = []
    try:
        frappe.cache().hdel("fiscal_years", COMPANY)
        notes.append("hdel(fiscal_years, company)")
    except Exception as e:
        notes.append("hdel err: " + str(e))
    try:
        frappe.cache().delete_key("fiscal_years")
        notes.append("delete_key(fiscal_years)")
    except Exception as e:
        notes.append("delete_key err: " + str(e))
    try:
        frappe.local.cache = {}
        notes.append("reset frappe.local.cache")
    except Exception as e:
        notes.append("local err: " + str(e))
    rec("fy_cache_cleared__" + tag, notes)


clear_fy_cache("process_start")

BASELINE = count_all()
BASELINE_SERIES = series_rows()
rec("BASELINE_counts", BASELINE)
rec("BASELINE_fiscal_years", [r["name"] for r in frappe.db.get_all("Fiscal Year", fields=["name"])])


# ------------------------------------------------------- independent raw-GL truth
def raw_pl_by_year():
    rows = frappe.db.sql(
        """
        SELECT gle.posting_date, a.root_type, gle.debit, gle.credit
          FROM `tabGL Entry` gle JOIN `tabAccount` a ON a.name = gle.account
         WHERE gle.company = %s AND gle.is_cancelled = 0
               AND a.report_type = 'Profit and Loss'
        """, (COMPANY,), as_dict=True)
    out = {}
    for r in rows:
        y = str(r["posting_date"])[:4]
        d = out.setdefault(y, {"income_dr_minus_cr": 0.0, "expense_dr_minus_cr": 0.0})
        key = "income_dr_minus_cr" if r["root_type"] == "Income" else "expense_dr_minus_cr"
        d[key] = round(d[key] + float(r["debit"]) - float(r["credit"]), 4)
    return out


def build_template():
    inc = json.dumps(["root_type", "=", "Income"])
    exp = json.dumps(["root_type", "=", "Expense"])
    rows = [
        {"data_source": "Column Break", "display_name": "本年累计金额"},
        {"data_source": "Account Data", "display_name": "营业收入(累计)",
         "reference_code": "CUM_INC", "balance_type": "Closing Balance",
         "calculation_formula": inc, "reverse_sign": 1, "fieldtype": "Currency"},
        {"data_source": "Account Data", "display_name": "营业成本(累计)",
         "reference_code": "CUM_EXP", "balance_type": "Closing Balance",
         "calculation_formula": exp, "fieldtype": "Currency"},
        {"data_source": "Calculated Amount", "display_name": "净利润(累计)",
         "reference_code": "CUM_NP", "calculation_formula": "CUM_INC - CUM_EXP",
         "fieldtype": "Currency", "bold_text": 1},
        {"data_source": "Column Break", "display_name": "本月金额"},
        {"data_source": "Account Data", "display_name": "营业收入(本月)",
         "reference_code": "MTH_INC", "balance_type": "Period Movement (Debits - Credits)",
         "calculation_formula": inc, "reverse_sign": 1, "fieldtype": "Currency"},
        {"data_source": "Account Data", "display_name": "营业成本(本月)",
         "reference_code": "MTH_EXP", "balance_type": "Period Movement (Debits - Credits)",
         "calculation_formula": exp, "fieldtype": "Currency"},
    ]
    doc = frappe.get_doc({
        "doctype": "Financial Report Template",
        "template_name": TPL,
        "report_type": "Profit and Loss Statement",
        # module deliberately EMPTY -- see header note on _export_template()
        "rows": rows,
    })
    doc.insert(ignore_permissions=True)
    return doc


WATCH = ["jan_2026", "sep_2026", "oct_2026", "dec_2026"]


def run_engine(tpl_name, label):
    """Run the real engine for FY2026 Monthly and pull the watched cells."""
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
    res = FinancialReportEngine().execute(filters)
    cols, data = res[0], res[1]
    out = {"row_count": len(data), "rows": {}}
    for r in data:
        nm = r.get("seg_0_account_name") or r.get("seg_1_account_name")
        if not nm:
            continue
        cell = {}
        for m in WATCH:
            cell["cum_" + m] = r.get("seg_0_" + m)
            cell["mth_" + m] = r.get("seg_1_" + m)
        out["rows"][nm] = cell
    out["visible_column_count"] = len([c for c in cols if not c.get("hidden")])
    rec("engine_" + label, out)
    return out


try:
    rec("raw_pl_by_year_BEFORE_setup", raw_pl_by_year())

    # ---------------- 1. manufacture the prior fiscal year + prior-year P&L -------
    fy = frappe.get_doc({
        "doctype": "Fiscal Year", "year": PRIOR_FY,
        "year_start_date": "2025-01-01", "year_end_date": "2025-12-31",
    })
    fy.insert(ignore_permissions=True)
    rec("prior_fiscal_year_created", {"name": fy.name,
                                      "start": str(fy.year_start_date),
                                      "end": str(fy.year_end_date)})

    # Redis is NOT transactional and `fiscal_years` is a hash keyed by company
    # (accounts/utils.py:146,171) while FiscalYear.on_update only calls
    # delete_key (fiscal_year.py:37). A stale list from an earlier rolled-back
    # run made one attempt fail with "Date 2025-06-30 is not in any active
    # Fiscal Year". Drop the key explicitly, then ASSERT resolution works --
    # a silent miss here would make the whole prior-year setup inert and the
    # comparison meaningless.
    clear_fy_cache("after_prior_fy_insert")
    from erpnext.accounts.utils import get_fiscal_year
    resolved = get_fiscal_year("2025-06-30", company=COMPANY, raise_on_missing=False)
    rec("prior_fy_resolves_for_je_date", {"date": "2025-06-30", "resolved": resolved})
    if not resolved:
        raise RuntimeError(
            "V27-ABORT: FY2025 not resolvable for 2025-06-30 even after cache drop; "
            "the prior-year arm would be inert, so the A/B comparison is invalid")

    je = frappe.get_doc({
        "doctype": "Journal Entry", "voucher_type": "Journal Entry",
        "company": COMPANY, "posting_date": "2025-06-30",
        "user_remark": "V27 probe prior-year P&L movement",
        "accounts": [
            {"account": CASH_ACC, "debit_in_account_currency": PRIOR_JE_AMOUNT, "credit_in_account_currency": 0},
            {"account": INCOME_ACC, "debit_in_account_currency": 0, "credit_in_account_currency": PRIOR_JE_AMOUNT},
        ],
    })
    je.insert(ignore_permissions=True)
    je.submit()
    rec("prior_year_je", {"name": je.name, "docstatus": je.docstatus,
                          "posting_date": str(je.posting_date),
                          "amount": PRIOR_JE_AMOUNT})
    rec("raw_pl_by_year_AFTER_je", raw_pl_by_year())

    tpl = build_template()
    rec("template_inserted", {"name": tpl.name, "module": tpl.module, "rows": len(tpl.rows)})

    # ---------------- 2. ARM A: prior-year movement present, NO PCV --------------
    rec("ARM_A_precondition_pcv_count", frappe.db.count("Period Closing Voucher",
                                                        {"docstatus": 1}))
    arm_a = run_engine(tpl.name, "ARM_A_no_pcv")

    # ---------------- 3. create + submit the year-end PCV for 2025 ---------------
    pcv = frappe.get_doc({
        "doctype": "Period Closing Voucher", "company": COMPANY,
        "fiscal_year": PRIOR_FY,
        "period_start_date": "2025-01-01", "period_end_date": "2025-12-31",
        "closing_account_head": CLOSING_HEAD,
        "remarks": "V27 probe year-end close of 2025",
        "transaction_date": "2025-12-31",
    })
    pcv.insert(ignore_permissions=True)
    rec("pcv_inserted", {"name": pcv.name, "docstatus": pcv.docstatus})

    pcv.submit()
    pcv.reload()
    rec("pcv_submitted", {
        "name": pcv.name, "docstatus": pcv.docstatus,
        "gle_processing_status": pcv.gle_processing_status,
        "error_message": pcv.error_message,
    })
    rec("guard_hits_after_pcv_submit", GUARD_HITS)

    # what the PCV actually wrote
    # NOTE: is_period_closing_voucher_entry is a field on Account Closing Balance,
    # NOT on GL Entry (GL Entry has no such column in v16).
    rec("pcv_gl_entries", frappe.db.sql(
        """SELECT gle.account, a.root_type, gle.debit, gle.credit, gle.posting_date,
                  gle.is_opening, gle.fiscal_year
             FROM `tabGL Entry` gle JOIN `tabAccount` a ON a.name = gle.account
            WHERE gle.voucher_type='Period Closing Voucher' AND gle.voucher_no=%s
            ORDER BY a.root_type, gle.account""", (pcv.name,), as_dict=True))
    acb = frappe.db.sql(
        """SELECT acb.account, a.root_type, acb.debit, acb.credit, acb.closing_date
             FROM `tabAccount Closing Balance` acb
             JOIN `tabAccount` a ON a.name = acb.account
            WHERE acb.period_closing_voucher=%s ORDER BY a.root_type, acb.account""",
        (pcv.name,), as_dict=True)
    rec("account_closing_balance_rows_count", len(acb))
    rec("account_closing_balance_rows", acb)
    # the crux: do P&L accounts net to ZERO in Account Closing Balance?
    pl_net = {}
    for r in acb:
        if r["root_type"] in ("Income", "Expense"):
            pl_net[r["account"]] = round(pl_net.get(r["account"], 0.0)
                                        + float(r["debit"]) - float(r["credit"]), 4)
    rec("acb_pl_account_net_debit_minus_credit", pl_net)

    # ---------------- 4. ARM B: same report, PCV now submitted ------------------
    arm_b = run_engine(tpl.name, "ARM_B_with_pcv")

    # ---------------- 5. which opening-balance branch did the engine take? ------
    from erpnext.accounts.doctype.financial_report_template import financial_report_engine as fre
    import inspect
    src = inspect.getsource(fre.FinancialQueryBuilder._get_opening_balances)
    rec("engine_took_pcv_branch_probe", {
        "submitted_pcv_before_2026_01_01": frappe.db.get_all(
            "Period Closing Voucher",
            filters={"docstatus": 1, "company": COMPANY,
                     "period_end_date": ("<", "2026-01-01")},
            fields=["name", "period_end_date"]),
        "note": "non-empty => _get_opening_balances() takes the closing-balance "
                "branch (:557-560) instead of the 1900-01-01 fallback (:562)",
    })
    rec("get_opening_balances_source", src)

    # ---------------- 6. THE DECISIVE COMPARISON --------------------------------
    raw = raw_pl_by_year()
    cur_income = abs(raw.get("2026", {}).get("income_dr_minus_cr", 0.0))
    cur_expense = raw.get("2026", {}).get("expense_dr_minus_cr", 0.0)
    prior_income = abs(raw.get("2025", {}).get("income_dr_minus_cr", 0.0))

    a_inc = arm_a["rows"].get("营业收入(累计)", {})
    b_inc = arm_b["rows"].get("营业收入(累计)", {})
    a_exp = arm_a["rows"].get("营业成本(累计)", {})
    b_exp = arm_b["rows"].get("营业成本(累计)", {})

    decisive = {
        "raw_gl_independent": {
            "prior_year_2025_income": prior_income,
            "current_year_2026_income": cur_income,
            "current_year_2026_expense": cur_expense,
            "since_inception_income": round(prior_income + cur_income, 4),
        },
        "ARM_A_no_pcv_income_closing": {m: a_inc.get("cum_" + m) for m in WATCH},
        "ARM_B_with_pcv_income_closing": {m: b_inc.get("cum_" + m) for m in WATCH},
        "ARM_A_no_pcv_expense_closing": {m: a_exp.get("cum_" + m) for m in WATCH},
        "ARM_B_with_pcv_expense_closing": {m: b_exp.get("cum_" + m) for m in WATCH},
    }
    # setup effectiveness: without a PCV the prior year MUST be folded in,
    # otherwise arm B proves nothing.
    decisive["A1_setup_effective__armA_jan_carries_prior_year"] = (
        a_inc.get("cum_jan_2026") == prior_income)
    decisive["A2_setup_effective__armA_dec_is_since_inception"] = (
        a_inc.get("cum_dec_2026") == round(prior_income + cur_income, 4))
    # the proposition itself
    decisive["B1_pcv_resets_opening__armB_jan_is_zero"] = (
        b_inc.get("cum_jan_2026") in (0, 0.0))
    decisive["B2_pcv_makes_closing_equal_ytd__armB_dec_is_current_year_only"] = (
        b_inc.get("cum_dec_2026") == cur_income)
    decisive["B3_arms_actually_differ"] = (
        a_inc.get("cum_dec_2026") != b_inc.get("cum_dec_2026"))
    # control: expense had no 2025 movement, must be identical in both arms
    decisive["C1_expense_control_unchanged_between_arms"] = (
        a_exp.get("cum_dec_2026") == b_exp.get("cum_dec_2026"))
    decisive["C2_expense_matches_raw_current_year"] = (
        b_exp.get("cum_dec_2026") == cur_expense)

    decisive["PROPOSITION_V27_HOLDS"] = bool(
        decisive["A1_setup_effective__armA_jan_carries_prior_year"]
        and decisive["A2_setup_effective__armA_dec_is_since_inception"]
        and decisive["B1_pcv_resets_opening__armB_jan_is_zero"]
        and decisive["B2_pcv_makes_closing_equal_ytd__armB_dec_is_current_year_only"]
        and decisive["B3_arms_actually_differ"]
        and decisive["C1_expense_control_unchanged_between_arms"])
    rec("DECISIVE", decisive)

except Exception as e:
    rec("probe_error", {"err": str(e), "tb": traceback.format_exc()[-4000:]})

finally:
    # -------------------------------------------------------------- ROLLBACK
    _Db.commit = _orig["db_commit"]          # restore before rollback
    frappe.db.rollback()
    frappe.enqueue = _orig["frappe_enqueue"]
    if _orig["frappe_enqueue_doc"] is not None:
        frappe.enqueue_doc = _orig["frappe_enqueue_doc"]
    _bj.enqueue = _orig["bj_enqueue"]

    # Redis is NOT transactional: FiscalYear.on_update deleted the key and
    # _get_fiscal_years may have re-cached a now-rolled-back FY2025. Drop it.
    # FY2025 no longer exists in the DB after the rollback; make sure no cache
    # layer still advertises it to the NEXT process.
    try:
        clear_fy_cache("after_rollback")
        frappe.clear_cache()
        cache_cleared = True
    except Exception as ce:
        cache_cleared = "error: " + str(ce)
    rec("fiscal_years_cache_cleared", cache_cleared)
    try:
        from erpnext.accounts.utils import get_fiscal_year as _gfy
        rec("post_rollback_2025_resolves_should_be_false",
            bool(_gfy("2025-06-30", company=COMPANY, raise_on_missing=False)))
    except Exception as ce:
        rec("post_rollback_2025_resolves_should_be_false", "error: " + str(ce))

    AFTER = count_all()
    rec("AFTER_counts", AFTER)
    rec("baseline_restored", AFTER == BASELINE)
    rec("count_deltas", {k: AFTER[k] - BASELINE[k] for k in BASELINE if AFTER[k] != BASELINE[k]}
        or "none")
    rec("AFTER_fiscal_years", [r["name"] for r in frappe.db.get_all("Fiscal Year", fields=["name"])])
    rec("template_exists_after_rollback", bool(frappe.db.exists("Financial Report Template", TPL)))
    rec("pcv_exists_after_rollback", frappe.db.count("Period Closing Voucher"))
    rec("acb_rows_after_rollback", frappe.db.count("Account Closing Balance"))
    rec("guard_hits_total", GUARD_HITS or "none -- nothing tried to commit or enqueue")

    # tabSeries is DML inside the txn, but verify it came back too
    AFTER_SERIES = series_rows()
    rec("series_unchanged", AFTER_SERIES == BASELINE_SERIES)
    rec("series_deltas", {k: [BASELINE_SERIES.get(k), AFTER_SERIES.get(k)]
                          for k in set(BASELINE_SERIES) | set(AFTER_SERIES)
                          if BASELINE_SERIES.get(k) != AFTER_SERIES.get(k)} or "none")

    # no stray template JSON in the app source tree
    import glob
    strays = []
    for pat in ("*probe*", "*PROBE*", "*v27*", "*V27*"):
        strays += glob.glob(frappe.get_app_path(
            "erpnext", "accounts", "financial_report_template", pat))
    rec("stray_exported_files", strays or "none")

    os.makedirs(OUT_DIR, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)
    print("\nWROTE " + OUT, flush=True)
