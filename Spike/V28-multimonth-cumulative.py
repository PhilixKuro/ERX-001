# V-28 probe: when SEVERAL months carry postings, does the `Closing Balance`
# column increase CORRECTLY month over month?
#
# Proposition V-28: the cumulative semantics demonstrated by V-26 actually hold
# arithmetically across multiple months -- not merely in the degenerate
# "only one month has postings" case.
#
# WHY V-26 COULD NOT ANSWER THIS. V-26 proved a cumulative column and a
# single-month column can coexist in one report, using the fact that the demo
# company's PL GL sits entirely in 2026-09 ({"2026-09": -719.5}): the cumulative
# column held 719.5 into Oct/Dec while the monthly column dropped to 0.0. That is
# a valid falsification test, but a column that merely REPEATS ITS LAST VALUE
# would pass it too. V-26's own review section named this as unverified:
# "multi-month cumulative correctness -- the site has only one month of postings,
# cannot be tested".
#
# METHOD. Give the site a second and third month of postings INSIDE a rolled-back
# transaction, then check the chain identity
#       cumulative[m] == cumulative[m-1] + monthly[m]
# against raw-GL sums computed WITHOUT the engine. The injected amounts are chosen
# so that every month's figure is DISTINCT (Sep 719.5 / Oct 120 / Nov 470), which
# is what makes the observation discriminating:
#   - a column that repeats its last value     -> fails assertion cum_strictly_increases
#   - a column that always shows the grand total -> fails cum_sep == raw_cum_sep
#   - a column that is really single-month      -> fails the chain identity
#
# HOW THE SECOND MONTH IS CREATED, AND WHY THIS WAY.
# The engine reads the `GL Entry` TABLE directly (financial_report_engine.py:642
# `_get_gl_movements`), so raw GL rows are sufficient -- no voucher needed. Rows
# are written with `db_insert()`, which runs a plain INSERT and fires NO controller
# hooks, no validate, no on_submit. This is strictly less invasive than submitting
# a Journal Entry. Explicit names (ZZPROBE-V28-*) are set so frappe's naming series
# counter in `tabSeries` is never touched either.
#
# COMMIT / ENQUEUE AUDIT of the path this probe triggers (done before writing):
#   gl_entry.py:493            frappe.db.commit()  -> inside rename_temporarily_named_docs(),
#                              reachable only from scheduler cron "30 * * * *" (hooks.py:440)
#                              or tests. NOT on any insert/submit path.
#   accounts/utils.py:1689     commit inside the stock-GL repost chunk loop
#                              (Repost Item Valuation). Not triggered.
#   accounts/utils.py:1963     enqueue inside _auto_create_exchange_rate_revaluation_for,
#                              a scheduler helper. Not triggered.
#   document.py:1574           db_set(commit=False) -- opt-in parameter, default off.
#   document.py:2076           bulk_insert(commit_chunks) -- opt-in parameter, not used.
#   transaction_deletion_record.py:592  enqueue inside TDR.enqueue_task. The doc_events["*"]
#                              validate hook is check_for_running_deletion_job (:1120),
#                              a cache read that only frappe.throw()s. Different function.
#   financial_report_engine.py / financial_statements.py: zero commit, zero enqueue.
# db_insert() bypasses controllers entirely, so none of the above is even in reach.
#
# WRITES NOTHING PERMANENT. Everything in one transaction, rollback() in finally,
# NO frappe.db.commit() anywhere. The temp template's `module` is deliberately left
# EMPTY: FinancialReportTemplate.on_update -> _export_template() writes json into the
# erpnext source tree when module is set (guard at financial_report_template.py:61
# `if not self.module: return`), and that filesystem write rollback would NOT undo.
#
# Run (cwd MUST be .../sites, else frappe's logger dies on a relative path):
#   docker exec -i -w /workspace/frappe-bench/sites erx001-frappe-1 \
#     /workspace/frappe-bench/env/bin/python /workspace/Spike/V28-multimonth-cumulative.py

import json
import os
import traceback

import frappe

SITE = "erx.localhost"
COMPANY = "华东弹簧"
OUTDIR = "/workspace/Spike/V28-out"
OUT = OUTDIR + "/multimonth-cumulative.json"
TPL = "ZZ-PROBE-V28-PL-MultiMonth"
GL_PREFIX = "ZZPROBE-V28-"

INCOME_ACC = "销售 - HDS"
EXPENSE_ACC = "销货成本 - HDS"
CASH_ACC = "现金 - HDS"

# Injected postings. Amounts deliberately DIFFERENT per month so each month's
# cumulative and monthly figure is unique and the two cannot be confused.
#   Oct: income 200 credit, expense  80 debit  -> PL movement -120
#   Nov: income 500 credit, expense  30 debit  -> PL movement -470
INJECT = [
    {"date": "2026-10-15", "income": 200.0, "expense": 80.0},
    {"date": "2026-11-20", "income": 500.0, "expense": 30.0},
]

MONTHS = ["aug_2026", "sep_2026", "oct_2026", "nov_2026", "dec_2026"]

result = {"probe": "V-28 multi-month cumulative correctness of Closing Balance column"}


def rec(k, v):
    result[k] = v
    print("[" + k + "] " + json.dumps(v, ensure_ascii=False, default=str)[:2500], flush=True)


frappe.init(site=SITE)
frappe.connect()
frappe.set_user("Administrator")

try:
    # ---------- 0. baseline BEFORE any write ----------
    def counts():
        return {dt: frappe.db.count(dt) for dt in
                ["GL Entry", "Stock Ledger Entry", "Account", "Company",
                 "Financial Report Template", "Fiscal Year", "Journal Entry",
                 "Period Closing Voucher", "Account Closing Balance"]}

    rec("baseline_counts_before", counts())
    rec("fiscal_years_before", [r.name for r in frappe.get_all("Fiscal Year", fields=["name"])])

    fy = frappe.db.get_value("Fiscal Year", "2026",
                             ["year_start_date", "year_end_date"], as_dict=True)
    rec("fiscal_year_2026_range", fy)

    # opening-balance path preconditions (which branch of _get_opening_balances runs)
    rec("opening_balance_path_preconditions", {
        "ignore_account_closing_balance": frappe.get_single_value(
            "Accounts Settings", "ignore_account_closing_balance"),
        "submitted_period_closing_vouchers": frappe.db.count(
            "Period Closing Voucher", {"docstatus": 1}),
        "account_closing_balance_rows": frappe.db.count("Account Closing Balance"),
        "note": "0 PCV + 0 ACB -> _get_opening_balances_from_gl() branch, 1900-01-01 start",
    })

    currency = frappe.db.get_value("Account", INCOME_ACC, "account_currency") \
        or frappe.db.get_value("Company", COMPANY, "default_currency")
    rec("account_currency_used", currency)

    # ---------- 1. inject a 2nd and 3rd month of GL, inside the transaction ----------
    def add_gl(idx, account, posting_date, debit, credit):
        d = frappe.get_doc({
            "doctype": "GL Entry",
            "company": COMPANY,
            "account": account,
            "posting_date": posting_date,
            "fiscal_year": "2026",
            "debit": debit,
            "credit": credit,
            "debit_in_account_currency": debit,
            "credit_in_account_currency": credit,
            "account_currency": currency,
            "voucher_type": "Journal Entry",
            "voucher_no": GL_PREFIX + "JV-" + str(idx),
            "is_opening": "No",
            "is_cancelled": 0,
        })
        d.name = GL_PREFIX + str(idx).zfill(3)
        # db_insert(): plain INSERT, no validate / no hooks / no naming series touched
        d.db_insert()
        return d.name

    injected = []
    i = 0
    for spec in INJECT:
        # income: credit; expense: debit; cash carries the balancing legs
        i += 1
        injected.append(add_gl(i, INCOME_ACC, spec["date"], 0.0, spec["income"]))
        i += 1
        injected.append(add_gl(i, EXPENSE_ACC, spec["date"], spec["expense"], 0.0))
        i += 1
        injected.append(add_gl(i, CASH_ACC, spec["date"], spec["income"], 0.0))
        i += 1
        injected.append(add_gl(i, CASH_ACC, spec["date"], 0.0, spec["expense"]))

    rec("injected_gl_names", injected)
    rec("counts_after_inject", counts())
    rec("inject_is_balanced_per_month", [
        {"date": s["date"],
         "debits": s["expense"] + s["income"],
         "credits": s["income"] + s["expense"],
         "balanced": True} for s in INJECT])

    # ---------- 2. independent raw-GL truth, computed WITHOUT the engine ----------
    pl_accounts = frappe.get_all(
        "Account",
        filters={"company": COMPANY, "is_group": 0,
                 "root_type": ["in", ["Income", "Expense"]]},
        pluck="name")
    gl = frappe.get_all(
        "GL Entry",
        filters={"company": COMPANY, "is_cancelled": 0, "account": ["in", pl_accounts]},
        fields=["account", "posting_date", "debit", "credit", "root_type" if False else "voucher_type"])
    # re-fetch with root_type via account map
    rt_of = {a.name: a.root_type for a in frappe.get_all(
        "Account", filters={"name": ["in", pl_accounts]}, fields=["name", "root_type"])}

    raw_mov = {}          # month -> PL movement (debit - credit)
    raw_inc = {}          # month -> income movement (credit - debit, i.e. sign-reversed)
    raw_exp = {}          # month -> expense movement (debit - credit)
    for r in gl:
        m = str(r.posting_date)[:7]
        v = (r.debit or 0.0) - (r.credit or 0.0)
        raw_mov[m] = round(raw_mov.get(m, 0.0) + v, 4)
        if rt_of.get(r.account) == "Income":
            raw_inc[m] = round(raw_inc.get(m, 0.0) - v, 4)
        else:
            raw_exp[m] = round(raw_exp.get(m, 0.0) + v, 4)

    rec("raw_gl_pl_movement_by_month", raw_mov)
    rec("raw_gl_income_by_month_signreversed", raw_inc)
    rec("raw_gl_expense_by_month", raw_exp)
    rec("raw_gl_distinct_months", sorted(raw_mov.keys()))

    # independent RUNNING cumulative, computed by hand in month order
    ordered = ["2026-01", "2026-02", "2026-03", "2026-04", "2026-05", "2026-06",
               "2026-07", "2026-08", "2026-09", "2026-10", "2026-11", "2026-12"]
    key_of = {"2026-08": "aug_2026", "2026-09": "sep_2026", "2026-10": "oct_2026",
              "2026-11": "nov_2026", "2026-12": "dec_2026"}
    raw_cum_np = {}
    raw_mth_np = {}
    run_inc = 0.0
    run_exp = 0.0
    for m in ordered:
        run_inc = round(run_inc + raw_inc.get(m, 0.0), 4)
        run_exp = round(run_exp + raw_exp.get(m, 0.0), 4)
        if m in key_of:
            raw_cum_np[key_of[m]] = round(run_inc - run_exp, 4)
            raw_mth_np[key_of[m]] = round(raw_inc.get(m, 0.0) - raw_exp.get(m, 0.0), 4)
    rec("raw_expected_cumulative_netprofit", raw_cum_np)
    rec("raw_expected_monthly_netprofit", raw_mth_np)

    # ---------- 3. build V-26's two-segment template (same construction) ----------
    inc_filter = json.dumps(["root_type", "=", "Income"])
    exp_filter = json.dumps(["root_type", "=", "Expense"])

    rows = [
        {"data_source": "Column Break", "display_name": "本年累计金额"},
        {"data_source": "Account Data", "display_name": "营业收入(累计)",
         "reference_code": "CUM_INC", "balance_type": "Closing Balance",
         "calculation_formula": inc_filter, "reverse_sign": 1, "fieldtype": "Currency"},
        {"data_source": "Account Data", "display_name": "营业成本(累计)",
         "reference_code": "CUM_EXP", "balance_type": "Closing Balance",
         "calculation_formula": exp_filter, "fieldtype": "Currency"},
        {"data_source": "Calculated Amount", "display_name": "净利润(累计)",
         "reference_code": "CUM_NP", "calculation_formula": "CUM_INC - CUM_EXP",
         "fieldtype": "Currency", "bold_text": 1},
        {"data_source": "Column Break", "display_name": "本月金额"},
        {"data_source": "Account Data", "display_name": "营业收入(本月)",
         "reference_code": "MTH_INC", "balance_type": "Period Movement (Debits - Credits)",
         "calculation_formula": inc_filter, "reverse_sign": 1, "fieldtype": "Currency"},
        {"data_source": "Account Data", "display_name": "营业成本(本月)",
         "reference_code": "MTH_EXP", "balance_type": "Period Movement (Debits - Credits)",
         "calculation_formula": exp_filter, "fieldtype": "Currency"},
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
    rec("template_inserted", {"name": doc.name, "module": doc.module, "rows": len(doc.rows)})

    # ---------- 4. run the real engine, Monthly across FY2026 ----------
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
    rec("engine_visible_column_count", len([c for c in cols if not c.get("hidden")]))

    # ---------- 5. pull every watched row, both segments ----------
    table = []
    for r in data:
        row = {"seg_0_name": r.get("seg_0_account_name"), "seg_1_name": r.get("seg_1_account_name")}
        for m in MONTHS:
            row["cum_" + m] = r.get("seg_0_" + m)
            row["mth_" + m] = r.get("seg_1_" + m)
        table.append(row)
    rec("engine_rows_all_watched_months", table)

    cum_np = {}
    mth_np = {}
    cum_inc = {}
    mth_inc = {}
    cum_exp = {}
    mth_exp = {}
    for r in data:
        n0 = r.get("seg_0_account_name")
        if n0 == "净利润(累计)":
            for m in MONTHS:
                cum_np[m] = r.get("seg_0_" + m)
                mth_np[m] = r.get("seg_1_" + m)
        if n0 == "营业收入(累计)":
            for m in MONTHS:
                cum_inc[m] = r.get("seg_0_" + m)
                mth_inc[m] = r.get("seg_1_" + m)
        if n0 == "营业成本(累计)":
            for m in MONTHS:
                cum_exp[m] = r.get("seg_0_" + m)
                mth_exp[m] = r.get("seg_1_" + m)

    rec("engine_netprofit_cumulative_by_month", cum_np)
    rec("engine_netprofit_monthly_by_month", mth_np)
    rec("engine_income_cumulative_by_month", cum_inc)
    rec("engine_income_monthly_by_month", mth_inc)
    rec("engine_expense_cumulative_by_month", cum_exp)
    rec("engine_expense_monthly_by_month", mth_exp)

    # ---------- 6. THE DECISIVE CHECKS ----------
    def eq(a, b):
        return a is not None and b is not None and abs(float(a) - float(b)) < 0.005

    posting_months = ["sep_2026", "oct_2026", "nov_2026"]

    # (a) engine cumulative == independently computed running cumulative, every month
    cum_matches_raw = {m: {"engine": cum_np.get(m), "raw": raw_cum_np.get(m),
                           "match": eq(cum_np.get(m), raw_cum_np.get(m))} for m in MONTHS}
    # (b) engine monthly == independently computed per-month movement, every month
    mth_matches_raw = {m: {"engine": mth_np.get(m), "raw": raw_mth_np.get(m),
                           "match": eq(mth_np.get(m), raw_mth_np.get(m))} for m in MONTHS}

    # (c) THE CHAIN IDENTITY: cumulative[m] == cumulative[m-1] + monthly[m]
    chain = []
    for idx in range(1, len(MONTHS)):
        prev_m, cur_m = MONTHS[idx - 1], MONTHS[idx]
        expected = round(float(cum_np.get(prev_m) or 0.0) + float(mth_np.get(cur_m) or 0.0), 4)
        chain.append({
            "month": cur_m,
            "cum_prev": cum_np.get(prev_m),
            "plus_monthly": mth_np.get(cur_m),
            "expected_cum": expected,
            "actual_cum": cum_np.get(cur_m),
            "holds": eq(expected, cum_np.get(cur_m)),
        })
    rec("chain_identity_cum_prev_plus_monthly", chain)

    # (d) rule out the V-26 blind spot: a column that merely REPEATS its last value
    repeats_last = all(eq(cum_np.get(MONTHS[i]), cum_np.get(MONTHS[i - 1]))
                       for i in range(1, len(MONTHS)))
    # cumulative must STRICTLY INCREASE across the three posting months
    strictly_increases = (
        float(cum_np.get("oct_2026") or 0) > float(cum_np.get("sep_2026") or 0)
        and float(cum_np.get("nov_2026") or 0) > float(cum_np.get("oct_2026") or 0))

    # (e) rule out "cumulative column is really the grand total repeated"
    grand_total = raw_cum_np.get("dec_2026")
    equals_total_everywhere = all(eq(cum_np.get(m), grand_total) for m in posting_months)

    # (f) monthly column must actually VARY (not constant), and differ from cumulative
    monthly_varies = not eq(mth_np.get("oct_2026"), mth_np.get("nov_2026"))
    cum_differs_from_mth = (not eq(cum_np.get("oct_2026"), mth_np.get("oct_2026"))
                           and not eq(cum_np.get("nov_2026"), mth_np.get("nov_2026")))

    # (g) after the last posting month, cumulative HOLDS and monthly drops to 0
    holds_after_last = eq(cum_np.get("dec_2026"), cum_np.get("nov_2026"))
    monthly_zero_after_last = eq(mth_np.get("dec_2026"), 0.0)

    decisive = {
        "cumulative_matches_independent_raw_every_month": cum_matches_raw,
        "monthly_matches_independent_raw_every_month": mth_matches_raw,
        "all_cumulative_match": all(v["match"] for v in cum_matches_raw.values()),
        "all_monthly_match": all(v["match"] for v in mth_matches_raw.values()),
        "chain_identity_holds_every_month": all(c["holds"] for c in chain),
        "cumulative_strictly_increases_over_posting_months": strictly_increases,
        "REFUTED_column_merely_repeats_last_value": not repeats_last,
        "REFUTED_column_is_grand_total_repeated": not equals_total_everywhere,
        "monthly_column_actually_varies": monthly_varies,
        "cumulative_differs_from_monthly": cum_differs_from_mth,
        "cumulative_holds_after_last_posting_month": holds_after_last,
        "monthly_drops_to_zero_after_last_posting_month": monthly_zero_after_last,
        "distinct_months_with_postings": sorted(raw_mov.keys()),
    }
    decisive["CONCLUSION_multimonth_cumulative_arithmetically_correct"] = bool(
        decisive["all_cumulative_match"]
        and decisive["all_monthly_match"]
        and decisive["chain_identity_holds_every_month"]
        and strictly_increases
        and not repeats_last
        and not equals_total_everywhere
        and monthly_varies
        and cum_differs_from_mth
        and holds_after_last
        and monthly_zero_after_last
        and len(raw_mov) >= 3)
    rec("DECISIVE", decisive)

    # also verify income and expense rows independently (not just the derived NP row)
    inc_ok = {m: eq(cum_inc.get(m), None) for m in []}  # placeholder removed below
    raw_cum_inc = {}
    raw_cum_exp = {}
    ri = 0.0
    re_ = 0.0
    for m in ordered:
        ri = round(ri + raw_inc.get(m, 0.0), 4)
        re_ = round(re_ + raw_exp.get(m, 0.0), 4)
        if m in key_of:
            raw_cum_inc[key_of[m]] = ri
            raw_cum_exp[key_of[m]] = re_
    rec("component_rows_cross_check", {
        "income_cumulative": {m: {"engine": cum_inc.get(m), "raw": raw_cum_inc.get(m),
                                  "match": eq(cum_inc.get(m), raw_cum_inc.get(m))} for m in MONTHS},
        "expense_cumulative": {m: {"engine": cum_exp.get(m), "raw": raw_cum_exp.get(m),
                                   "match": eq(cum_exp.get(m), raw_cum_exp.get(m))} for m in MONTHS},
        "income_monthly": {m: {"engine": mth_inc.get(m), "raw": raw_inc.get(
            [k for k, v in key_of.items() if v == m][0], 0.0),
            "match": eq(mth_inc.get(m), raw_inc.get(
                [k for k, v in key_of.items() if v == m][0], 0.0))} for m in MONTHS},
    })

except Exception as e:
    rec("probe_error", {"err": str(e), "tb": traceback.format_exc()[-3000:]})

finally:
    frappe.db.rollback()

    # ---------- 7. SITE SAFETY verification AFTER rollback ----------
    after = {dt: frappe.db.count(dt) for dt in
             ["GL Entry", "Stock Ledger Entry", "Account", "Company",
              "Financial Report Template", "Fiscal Year", "Journal Entry",
              "Period Closing Voucher", "Account Closing Balance"]}
    rec("baseline_counts_after_rollback", after)
    rec("expected_baseline", {"GL Entry": 22, "Stock Ledger Entry": 12, "Account": 95,
                              "Company": 1, "Financial Report Template": 6, "Fiscal Year": 1})
    rec("baseline_restored", {
        "GL Entry": after["GL Entry"] == 22,
        "Stock Ledger Entry": after["Stock Ledger Entry"] == 12,
        "Account": after["Account"] == 95,
        "Company": after["Company"] == 1,
        "Financial Report Template": after["Financial Report Template"] == 6,
        "Fiscal Year_only_2026": [r.name for r in frappe.get_all(
            "Fiscal Year", fields=["name"])] == ["2026"],
    })
    rec("template_exists_after_rollback", bool(frappe.db.exists("Financial Report Template", TPL)))
    rec("injected_gl_exists_after_rollback",
        frappe.db.count("GL Entry", {"voucher_no": ["like", GL_PREFIX + "%"]}))
    rec("injected_gl_by_name_after_rollback",
        [r.name for r in frappe.get_all("GL Entry", filters={"name": ["like", GL_PREFIX + "%"]},
                                        fields=["name"])])
    rec("gl_months_after_rollback", sorted({
        str(r.posting_date)[:7] for r in frappe.get_all(
            "GL Entry", filters={"company": COMPANY, "is_cancelled": 0},
            fields=["posting_date"])}))

    # no stray exported template files in the erpnext source tree
    import glob
    d = frappe.get_app_path("erpnext", "accounts", "financial_report_template")
    rec("financial_report_template_dir_listing",
        sorted(os.path.basename(p) for p in glob.glob(d + "/*")))
    strays = [os.path.basename(p) for p in glob.glob(d + "/*")
              if "probe" in p.lower() or "v28" in p.lower() or "zz" in os.path.basename(p).lower()]
    rec("stray_exported_files", strays)

    if not os.path.isdir(OUTDIR):
        os.makedirs(OUTDIR)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)
    print("\nWROTE " + OUT, flush=True)
