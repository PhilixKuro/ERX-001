# REV AUDIT part D: re-run the REAL engine and try to BREAK both verdicts.
#
# ASCII-ONLY SOURCE. Chinese appears only as \uXXXX escapes.
#
# What this adds over the original V-25 / V-26 probes:
#
#  (1) V-26's decisive numbers are reproduced from scratch, AND the weaker
#      alternative explanation is attacked. "Cumulative holds in Oct" is also
#      satisfied by a column that merely REPEATS its last value. To separate
#      those two WITHOUT writing GL, use an ASSET (Stock) account plus a Date
#      Range starting BETWEEN the site's two GL days (2026-09-20 / 2026-09-21):
#          opening(Sep) = 750.0    (the 09-20 receipt, now before the window)
#          movement(Sep) = -325.5  (the 09-21 postings, inside the window)
#          closing(Sep) = 424.5    = opening + movement
#      A "repeats the movement" implementation cannot produce 424.5, and a
#      "repeats the last value" implementation cannot make closing != movement
#      inside the FIRST period. The original probe had opening == 0, so there
#      closing == movement in Sep and this discrimination was not available.
#  (2) A third segment with balance_type "Opening Balance" exposes the chain:
#      opening(Oct) must equal closing(Sep) for a genuine running balance.
#  (3) _get_opening_balances_from_gl / _get_closing_balances / _get_gap_movements
#      are wrapped so the run RECORDS which opening-balance branch actually
#      executed, instead of inferring it from a PCV count.
#  (4) V-25's six column labels are re-derived, and the combination the original
#      probe left untested is tested: a self-built two-segment Balance Sheet with
#      CHINESE Column Break display_names across TWO fiscal years.
#
# SITE SAFETY
#  - Every write (Fiscal Year 2025, two temp templates) happens inside the
#    transaction and is rolled back in `finally`. There is NO frappe.db.commit()
#    and NO frappe.enqueue anywhere in this file.
#  - `module` is left EMPTY on every template: FinancialReportTemplate.on_update
#    -> _export_template() returns early without a module, so nothing is written
#    into the erpnext source tree (a filesystem write rollback could not undo).
#  - Grepped before running: no frappe.db.commit / frappe.enqueue in
#    financial_report_template.py, financial_report_validation.py,
#    financial_report_engine.py, financial_report_row.py, fiscal_year.py,
#    account_category.py.
#  - Baseline is re-counted after rollback and compared against expected values.
#
# Run (cwd MUST be .../sites):
#   docker exec -i -w /workspace/frappe-bench/sites erx001-frappe-1 \
#     /workspace/frappe-bench/env/bin/python /workspace/Spike/Rev-P1S4R2-d-runtime.py

import json
import os
import traceback

import frappe

SITE = "erx.localhost"
COMPANY = "\u534e\u4e1c\u5f39\u7c27"
OUT = "/workspace/Spike/Rev-out/d-runtime.json"

TPL_PL = "ZZREV-PL-ThreeType"
TPL_BS = "ZZREV-BS-ChineseSegments"

# Chinese labels under test, as escapes
CN_OPENING = "\u5e74\u521d\u4f59\u989d"   # nian chu yu e  (statutory opening column)
CN_CLOSING = "\u671f\u672b\u4f59\u989d"   # qi mo yu e     (statutory closing column)
CN_ASSET = "\u8d44\u4ea7"                 # zi chan
CN_LIAB = "\u8d1f\u503a"                  # fu zhai

EXPECTED_BASELINE = {
    "GL Entry": 22, "Stock Ledger Entry": 12, "Account": 95, "Company": 1,
    "Financial Report Template": 6, "Period Closing Voucher": 0,
    "Account Closing Balance": 0,
}

result = {"probe": "REV audit part D: adversarial re-run of the real engine"}
created = []


def rec(k, v):
    result[k] = v
    print("[" + k + "] " + json.dumps(v, ensure_ascii=True, default=str)[:1700], flush=True)


frappe.init(site=SITE)
frappe.connect()
frappe.set_user("Administrator")

_orig_from_gl = _orig_from_pcv = _orig_gap = None

try:
    rec("baseline_before", {dt: frappe.db.count(dt) for dt in EXPECTED_BASELINE})
    rec("fiscal_years_before", frappe.get_all("Fiscal Year", pluck="name"))

    from erpnext.accounts.doctype.financial_report_template import financial_report_engine as fre
    from erpnext.accounts.doctype.financial_report_template.financial_report_engine import (
        FinancialReportEngine,
    )

    # ---------- instrument the opening-balance branches (in-process only) ----------
    branch_log = []
    _orig_from_gl = fre.FinancialQueryBuilder._get_opening_balances_from_gl
    _orig_from_pcv = fre.FinancialQueryBuilder._get_closing_balances
    _orig_gap = fre.FinancialQueryBuilder._get_gap_movements

    def spy_from_gl(self, accounts):
        branch_log.append({"branch": "_get_opening_balances_from_gl",
                           "earliest_date_literal": "1900-01-01",
                           "n_accounts": len(accounts),
                           "first_period_from": str(self.periods[0]["from_date"])})
        return _orig_from_gl(self, accounts)

    def spy_from_pcv(self, account_names, closing_voucher):
        branch_log.append({"branch": "_get_closing_balances(PCV)", "pcv": closing_voucher})
        return _orig_from_pcv(self, account_names, closing_voucher)

    def spy_gap(self, account_names, from_date, to_date):
        out = _orig_gap(self, account_names, from_date, to_date)
        branch_log.append({"branch": "_get_gap_movements",
                           "from_date": str(from_date), "to_date": str(to_date),
                           "nonzero": {k: v for k, v in out.items() if v}})
        return out

    fre.FinancialQueryBuilder._get_opening_balances_from_gl = spy_from_gl
    fre.FinancialQueryBuilder._get_closing_balances = spy_from_pcv
    fre.FinancialQueryBuilder._get_gap_movements = spy_gap

    # ---------- template 1: same accounts, THREE balance types side by side ----------
    inc_f = json.dumps(["root_type", "=", "Income"])
    exp_f = json.dumps(["root_type", "=", "Expense"])
    # Stock asset account: has GL on BOTH 2026-09-20 and 2026-09-21, so a window
    # starting 09-21 gives it a NONZERO opening. Selected by account_type to keep
    # this source ASCII-only.
    stock_f = json.dumps(["account_type", "=", "Stock"])

    rows = []
    for seg_name, btype in (("CLOSING", "Closing Balance"),
                            ("MOVEMENT", "Period Movement (Debits - Credits)"),
                            ("OPENING", "Opening Balance")):
        rows.append({"data_source": "Column Break", "display_name": seg_name})
        rows.append({"data_source": "Account Data", "display_name": "INC " + seg_name,
                     "reference_code": "I_" + seg_name, "balance_type": btype,
                     "calculation_formula": inc_f, "reverse_sign": 1,
                     "fieldtype": "Currency"})
        rows.append({"data_source": "Account Data", "display_name": "EXP " + seg_name,
                     "reference_code": "E_" + seg_name, "balance_type": btype,
                     "calculation_formula": exp_f, "fieldtype": "Currency"})
        rows.append({"data_source": "Account Data", "display_name": "STOCK " + seg_name,
                     "reference_code": "S_" + seg_name, "balance_type": btype,
                     "calculation_formula": stock_f, "fieldtype": "Currency"})
        rows.append({"data_source": "Calculated Amount", "display_name": "NP " + seg_name,
                     "reference_code": "NP_" + seg_name,
                     "calculation_formula": "I_" + seg_name + " - E_" + seg_name,
                     "fieldtype": "Currency"})

    tpl = frappe.get_doc({"doctype": "Financial Report Template",
                          "template_name": TPL_PL,
                          "report_type": "Profit and Loss Statement",
                          "rows": rows})  # module intentionally omitted
    tpl.insert(ignore_permissions=True)
    created.append(("Financial Report Template", tpl.name))
    rec("tpl_pl_inserted", {"name": tpl.name, "module": tpl.module, "rows": len(tpl.rows),
                            "balance_types_stored": sorted({r.balance_type or "<none>"
                                                            for r in tpl.rows})})
    # prove the stored child rows really carry PER-ROW balance_type
    rec("tpl_pl_stored_rows", frappe.db.sql("""
        select idx, data_source, display_name, ifnull(balance_type,'<null>') as balance_type
        from `tabFinancial Report Row` where parent = %s order by idx
    """, (tpl.name,), as_dict=True))

    def run(label, extra, template):
        base = {"company": COMPANY, "report_template": template,
                "selected_view": "Report", "include_default_book_entries": 1}
        base.update(extra)
        del branch_log[:]
        try:
            res = FinancialReportEngine().execute(frappe._dict(base))
            cols, data = res[0], res[1]
            seg_keys = {}
            for c in cols:
                fn = c["fieldname"]
                if fn.startswith("seg_") and not fn.endswith(
                        ("_account", "_acc_name", "_acc_number", "_currency")):
                    parts = fn.split("_")
                    seg_keys.setdefault(parts[0] + "_" + parts[1], []).append(fn)
            out = {
                "filters": base,
                "all_column_labels": [{"fieldname": c.get("fieldname"), "label": c.get("label"),
                                       "hidden": c.get("hidden", 0)} for c in cols],
                "visible_column_count": len([c for c in cols if not c.get("hidden")]),
                "segment_period_fields": seg_keys,
                "opening_balance_branches": list(branch_log),
                "rows": [],
            }
            for r in data:
                row = {}
                for k, v in r.items():
                    if k.startswith("_") or k == "segment_values":
                        continue
                    if k.endswith(("_child_accounts", "_period_start_date",
                                   "_period_end_date", "_acc_name", "_acc_number",
                                   "_currency", "_indent")):
                        continue
                    row[k] = v
                out["rows"].append(row)
            rec("run_" + label, out)
            return out
        except Exception as exc:
            rec("run_error_" + label, {"err": str(exc), "tb": traceback.format_exc()[-1500:]})
            return None

    # ===== (A) reproduce V-26's decisive run, from scratch =====
    a = run("A_FY2026_monthly", {
        "filter_based_on": "Fiscal Year", "from_fiscal_year": "2026",
        "to_fiscal_year": "2026", "periodicity": "Monthly"}, TPL_PL)

    # ===== (B) THE DISCRIMINATOR: window starts between the two GL days =====
    b = run("B_daterange_from_0921_monthly", {
        "filter_based_on": "Date Range", "period_start_date": "2026-09-21",
        "period_end_date": "2026-12-31", "periodicity": "Monthly"}, TPL_PL)

    # ===== (C) reproduce seg2: window entirely AFTER all GL =====
    c = run("C_daterange_Q4_after_all_GL", {
        "filter_based_on": "Date Range", "period_start_date": "2026-10-01",
        "period_end_date": "2026-12-31", "periodicity": "Monthly"}, TPL_PL)

    # ===== (D) Yearly, for the per-segment column count claim =====
    d = run("D_FY2026_yearly", {
        "filter_based_on": "Fiscal Year", "from_fiscal_year": "2026",
        "to_fiscal_year": "2026", "periodicity": "Yearly"}, TPL_PL)

    # ---------- verdict extraction ----------
    def pick(out, name_prefix, seg):
        if not out:
            return None
        for r in out["rows"]:
            if str(r.get(seg + "_account_name") or "").startswith(name_prefix):
                return r
        return None

    months = ("aug_2026", "sep_2026", "oct_2026", "dec_2026")

    v26 = {}
    if a:
        np_row = pick(a, "NP CLOSING", "seg_0")
        if np_row:
            v26 = {
                "cumulative_by_month": {m: np_row.get("seg_0_" + m) for m in months},
                "monthly_by_month": {m: np_row.get("seg_1_" + m) for m in months},
                "opening_by_month": {m: np_row.get("seg_2_" + m) for m in months},
            }
            v26["cumulative_holds_after_sep"] = (
                v26["cumulative_by_month"]["oct_2026"] == v26["cumulative_by_month"]["sep_2026"]
                == v26["cumulative_by_month"]["dec_2026"] == 719.5)
            v26["monthly_drops_after_sep"] = (
                v26["monthly_by_month"]["sep_2026"] == 719.5
                and v26["monthly_by_month"]["oct_2026"] in (0, 0.0)
                and v26["monthly_by_month"]["dec_2026"] in (0, 0.0))
            v26["two_columns_differ_in_oct"] = (
                v26["cumulative_by_month"]["oct_2026"] != v26["monthly_by_month"]["oct_2026"])
            v26["opening_oct_equals_closing_sep"] = (
                v26["opening_by_month"]["oct_2026"] == v26["cumulative_by_month"]["sep_2026"])
        inc = pick(a, "INC CLOSING", "seg_0")
        exp = pick(a, "EXP CLOSING", "seg_0")
        if inc and exp:
            v26["revenue_sep_closing"] = inc.get("seg_0_sep_2026")
            v26["cost_sep_closing"] = exp.get("seg_0_sep_2026")
            v26["revenue_minus_cost"] = round(
                (inc.get("seg_0_sep_2026") or 0) - (exp.get("seg_0_sep_2026") or 0), 6)
            v26["matches_raw_gl_719_5"] = v26["revenue_minus_cost"] == 719.5
    rec("DECISIVE_V26_reproduced", v26)

    disc = {}
    if b:
        st = pick(b, "STOCK CLOSING", "seg_0")
        if st:
            disc = {
                "stock_closing_sep": st.get("seg_0_sep_2026"),
                "stock_movement_sep": st.get("seg_1_sep_2026"),
                "stock_opening_sep": st.get("seg_2_sep_2026"),
                "stock_closing_oct": st.get("seg_0_oct_2026"),
                "stock_movement_oct": st.get("seg_1_oct_2026"),
                "stock_opening_oct": st.get("seg_2_oct_2026"),
            }
            disc["opening_is_nonzero"] = bool(disc["stock_opening_sep"])
            disc["closing_differs_from_movement_in_first_period"] = (
                disc["stock_closing_sep"] != disc["stock_movement_sep"])
            disc["closing_equals_opening_plus_movement"] = (
                round((disc["stock_opening_sep"] or 0) + (disc["stock_movement_sep"] or 0), 4)
                == round(disc["stock_closing_sep"] or 0, 4))
            disc["closing_carries_into_next_period"] = (
                disc["stock_closing_oct"] == disc["stock_closing_sep"]
                and disc["stock_opening_oct"] == disc["stock_closing_sep"])
            disc["rules_out_repeat_last_value"] = bool(
                disc["opening_is_nonzero"]
                and disc["closing_differs_from_movement_in_first_period"]
                and disc["closing_equals_opening_plus_movement"])
            disc["note"] = ("closing == opening + movement INSIDE one period, with a nonzero "
                            "opening, proves a running sum rather than a repeated value. "
                            "Cross-MONTH accumulation with movement in two different months is "
                            "NOT testable on this site: all GL sits in 2026-09.")
            disc["gap_branch_log"] = b["opening_balance_branches"]
    rec("DISCRIMINATOR_cumulative_not_just_repeat", disc)

    seg2 = {}
    if c:
        inc = pick(c, "INC CLOSING", "seg_0")
        if inc:
            seg2 = {
                "income_closing_oct_window_starts_oct": inc.get("seg_0_oct_2026"),
                "income_movement_oct": inc.get("seg_1_oct_2026"),
                "income_opening_oct": inc.get("seg_2_oct_2026"),
                "closing_carries_prior_period_amounts": bool(inc.get("seg_0_oct_2026")),
                "branches_taken": c["opening_balance_branches"],
            }
    rec("DECISIVE_seg2_reproduced", seg2)

    if d:
        rec("yearly_period_columns_per_segment",
            {k: len(v) for k, v in d["segment_period_fields"].items()})

    # ---------- V-25: create FY 2025 (in txn) and re-derive the six labels ----------
    if not frappe.db.exists("Fiscal Year", "2025"):
        fy = frappe.get_doc({"doctype": "Fiscal Year", "year": "2025",
                             "year_start_date": "2025-01-01", "year_end_date": "2025-12-31"})
        fy.insert(ignore_permissions=True)
        created.append(("Fiscal Year", fy.name))
        rec("fy2025_created_in_txn", fy.name)

    shipped = "Horizontal Balance Sheet (Columnar)"
    e = run("E_shipped_columnar_BS_two_FY_yearly", {
        "report_template": shipped, "filter_based_on": "Fiscal Year",
        "from_fiscal_year": "2025", "to_fiscal_year": "2026",
        "periodicity": "Yearly"}, shipped)
    if e:
        six = [{"fieldname": x["fieldname"], "label": x["label"]}
               for x in e["all_column_labels"]]
        rec("V25_all_columns_two_FY", six)
        expected = [
            ("seg_0_account", "Equity & Liabilities"),
            ("seg_0_dec_2025", "Equity & Liabilities - 2025"),
            ("seg_0_dec_2026", "Equity & Liabilities - 2026"),
            ("seg_1_account", "Assets"),
            ("seg_1_dec_2025", "Assets - 2025"),
            ("seg_1_dec_2026", "Assets - 2026"),
        ]
        got = {x["fieldname"]: x["label"] for x in six}
        rec("V25_six_labels_char_for_char", {
            "expected": dict(expected),
            "actual": {fn: got.get(fn) for fn, _lbl in expected},
            "all_match": all(got.get(fn) == lbl for fn, lbl in expected),
            "engine_rowcount": len(e["rows"]),
        })

    # ---------- V-25 untested combination: CHINESE Column Break labels, 2 FY, BS ----------
    asset_f = json.dumps(["root_type", "=", "Asset"])
    liab_f = json.dumps(["root_type", "=", "Liability"])
    cn_rows = [
        {"data_source": "Column Break", "display_name": CN_OPENING},
        {"data_source": "Account Data", "display_name": CN_ASSET,
         "reference_code": "A_OPEN", "balance_type": "Opening Balance",
         "calculation_formula": asset_f, "fieldtype": "Currency"},
        {"data_source": "Column Break", "display_name": CN_CLOSING},
        {"data_source": "Account Data", "display_name": CN_LIAB,
         "reference_code": "L_CLOSE", "balance_type": "Closing Balance",
         "calculation_formula": liab_f, "reverse_sign": 1, "fieldtype": "Currency"},
    ]
    tpl2 = frappe.get_doc({"doctype": "Financial Report Template",
                           "template_name": TPL_BS,
                           "report_type": "Balance Sheet",
                           "rows": cn_rows})
    tpl2.insert(ignore_permissions=True)
    created.append(("Financial Report Template", tpl2.name))
    rec("tpl_bs_inserted", {"name": tpl2.name, "module": tpl2.module})

    f = run("F_chinese_segments_two_FY_yearly", {
        "report_template": tpl2.name, "filter_based_on": "Fiscal Year",
        "from_fiscal_year": "2025", "to_fiscal_year": "2026",
        "periodicity": "Yearly"}, tpl2.name)
    if f:
        labs = [x["label"] for x in f["all_column_labels"] if not x.get("hidden")]
        rec("V25_chinese_segment_labels", {
            "visible_labels": labs,
            "any_label_is_exactly_CN_OPENING": CN_OPENING in labs,
            "any_label_is_exactly_CN_CLOSING": CN_CLOSING in labs,
            "labels_carrying_period_suffix": [l for l in labs if " - " in l],
            "period_column_labels": [
                x["label"] for x in f["all_column_labels"]
                if x["fieldname"].endswith(("_dec_2025", "_dec_2026"))],
            "conclusion": ("the bare segment label survives on the ACCOUNT column, but every "
                           "PERIOD column gets ' - <period>' appended, so no period column "
                           "can read exactly the statutory two labels"),
        })

    g = run("G_chinese_segments_one_FY_yearly", {
        "report_template": tpl2.name, "filter_based_on": "Fiscal Year",
        "from_fiscal_year": "2026", "to_fiscal_year": "2026",
        "periodicity": "Yearly"}, tpl2.name)
    if g:
        rec("V25_chinese_one_FY_labels",
            [x["label"] for x in g["all_column_labels"] if not x.get("hidden")])

    # ---------- does passing accumulated_values explicitly flatten the two columns? ----------
    # This is the claim "the switch only flattens the whole report when explicitly
    # passed". Test it by passing it on the FRT path, which the UI never does.
    for av in (0, 1):
        run("H_FY2026_monthly_accumulated_values_" + str(av), {
            "filter_based_on": "Fiscal Year", "from_fiscal_year": "2026",
            "to_fiscal_year": "2026", "periodicity": "Monthly",
            "accumulated_values": av}, TPL_PL)

    h0 = result.get("run_H_FY2026_monthly_accumulated_values_0")
    h1 = result.get("run_H_FY2026_monthly_accumulated_values_1")
    flat = {}
    for tag, out in (("av_0", h0), ("av_1", h1)):
        if not out:
            continue
        np_row = pick(out, "NP CLOSING", "seg_0")
        if np_row:
            flat[tag] = {
                "closing_by_month": {m: np_row.get("seg_0_" + m) for m in months},
                "movement_by_month": {m: np_row.get("seg_1_" + m) for m in months},
                "columns_still_differ_in_oct": (
                    np_row.get("seg_0_oct_2026") != np_row.get("seg_1_oct_2026")),
            }
    rec("EXPLICIT_accumulated_values_effect", flat)

except Exception as e:
    rec("probe_error", {"err": str(e), "tb": traceback.format_exc()[-3000:]})

finally:
    try:
        if _orig_from_gl:
            fre.FinancialQueryBuilder._get_opening_balances_from_gl = _orig_from_gl
            fre.FinancialQueryBuilder._get_closing_balances = _orig_from_pcv
            fre.FinancialQueryBuilder._get_gap_movements = _orig_gap
    except Exception:
        pass

    frappe.db.rollback()

    after = {dt: frappe.db.count(dt) for dt in EXPECTED_BASELINE}
    rec("baseline_after_rollback", after)
    rec("baseline_matches_expected", after == EXPECTED_BASELINE)
    rec("fiscal_years_after_rollback", frappe.get_all("Fiscal Year", pluck="name"))
    rec("created_docs_still_present",
        [[dt, n] for dt, n in created if frappe.db.exists(dt, n)])

    import glob
    strays = []
    for pat in ("*zzrev*", "*ZZREV*", "*probe*"):
        strays += glob.glob(frappe.get_app_path(
            "erpnext", "accounts", "financial_report_template", pat))
    rec("stray_exported_files", strays)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(result, fh, ensure_ascii=False, indent=2, default=str)
    print("\nWROTE " + OUT, flush=True)
