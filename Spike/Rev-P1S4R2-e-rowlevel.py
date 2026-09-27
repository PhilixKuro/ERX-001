# REV AUDIT part E: is balance_type really ROW-level, or only effectively
# SEGMENT-level?
#
# WHY THIS PROBE EXISTS. Both V-26 probes put the cumulative rows in segment 0
# and the movement rows in segment 1. That design CANNOT distinguish:
#    (i)  balance_type is honoured per ROW            <- the claim
#    (ii) balance_type is honoured per SEGMENT, and the engine just happens to
#         read it off the first Account Data row it meets in each segment
# Both hypotheses predict exactly the observed output in V26 seg1/seg2.
#
# The discriminator: ONE segment (no Column Break at all), holding two rows that
# select the SAME accounts and differ ONLY in balance_type. If (ii) were true,
# both rows would show the same number. If (i) is true, they must differ.
#
# A second, independent line of evidence needs no probe of mine at all: the
# SHIPPED template `Horizontal Balance Sheet (Columnar)` already mixes
# balance types INSIDE segment 0 -- idx 4..22 are "Closing Balance" while idx 26
# ("Net Profit/(Loss) for the Year") is "Period Movement", and the first Column
# Break after them is at idx 27. So row-level granularity is exercised in
# product, not only by a probe.
#
# Also here: a single-segment run, to confirm the ' - <period>' suffix comes from
# MultiSegmentFormatter and is therefore absent when there is only one segment
# (SingleSegmentFormatter.get_columns returns base_columns untouched). That bounds
# V-25's claim precisely.
#
# SITE SAFETY: one temp template, inserted inside the transaction, rolled back in
# `finally`. `module` left EMPTY. NO frappe.db.commit(), NO frappe.enqueue here.
# Baseline re-counted after rollback.
#
# Run (cwd MUST be .../sites):
#   docker exec -i -w /workspace/frappe-bench/sites erx001-frappe-1 \
#     /workspace/frappe-bench/env/bin/python /workspace/Spike/Rev-P1S4R2-e-rowlevel.py

import json
import os
import traceback

import frappe

SITE = "erx.localhost"
COMPANY = "\u534e\u4e1c\u5f39\u7c27"
OUT = "/workspace/Spike/Rev-out/e-rowlevel.json"
TPL = "ZZREV-SingleSegment-MixedTypes"

EXPECTED_BASELINE = {
    "GL Entry": 22, "Stock Ledger Entry": 12, "Account": 95, "Company": 1,
    "Financial Report Template": 6, "Period Closing Voucher": 0,
    "Account Closing Balance": 0,
}

result = {"probe": "REV audit part E: balance_type row-level vs segment-level"}
created = []


def rec(k, v):
    result[k] = v
    print("[" + k + "] " + json.dumps(v, ensure_ascii=True, default=str)[:1700], flush=True)


frappe.init(site=SITE)
frappe.connect()
frappe.set_user("Administrator")

try:
    rec("baseline_before", {dt: frappe.db.count(dt) for dt in EXPECTED_BASELINE})

    # ---------- evidence line 1: the SHIPPED template already mixes types in one segment
    shipped_rows = frappe.db.sql("""
        select idx, data_source, display_name, ifnull(balance_type,'') as balance_type
        from `tabFinancial Report Row`
        where parent = 'Horizontal Balance Sheet (Columnar)' order by idx
    """, as_dict=True)
    seg_idx = 0
    per_segment = {}
    for r in shipped_rows:
        if r["data_source"] == "Column Break":
            seg_idx += 1
            continue
        if r["balance_type"]:
            per_segment.setdefault("segment_" + str(seg_idx), {}).setdefault(
                r["balance_type"], []).append({"idx": r["idx"], "name": r["display_name"]})
    rec("shipped_template_types_per_segment",
        {k: {bt: len(v) for bt, v in d.items()} for k, d in per_segment.items()})
    rec("shipped_segment_0_mixes_types",
        len(per_segment.get("segment_0", {})) > 1)
    rec("shipped_segment_0_detail", per_segment.get("segment_0"))

    # ---------- evidence line 2: ONE segment, two rows, same accounts, diff type
    inc_f = json.dumps(["root_type", "=", "Income"])
    stock_f = json.dumps(["account_type", "=", "Stock"])
    rows = [
        # NO Column Break anywhere -> exactly one segment
        {"data_source": "Account Data", "display_name": "INC as CLOSING",
         "reference_code": "R1", "balance_type": "Closing Balance",
         "calculation_formula": inc_f, "reverse_sign": 1, "fieldtype": "Currency"},
        {"data_source": "Account Data", "display_name": "INC as MOVEMENT",
         "reference_code": "R2", "balance_type": "Period Movement (Debits - Credits)",
         "calculation_formula": inc_f, "reverse_sign": 1, "fieldtype": "Currency"},
        {"data_source": "Account Data", "display_name": "INC as OPENING",
         "reference_code": "R3", "balance_type": "Opening Balance",
         "calculation_formula": inc_f, "reverse_sign": 1, "fieldtype": "Currency"},
        {"data_source": "Account Data", "display_name": "STOCK as CLOSING",
         "reference_code": "R4", "balance_type": "Closing Balance",
         "calculation_formula": stock_f, "fieldtype": "Currency"},
        {"data_source": "Account Data", "display_name": "STOCK as MOVEMENT",
         "reference_code": "R5", "balance_type": "Period Movement (Debits - Credits)",
         "calculation_formula": stock_f, "fieldtype": "Currency"},
        {"data_source": "Account Data", "display_name": "STOCK as OPENING",
         "reference_code": "R6", "balance_type": "Opening Balance",
         "calculation_formula": stock_f, "fieldtype": "Currency"},
        {"data_source": "Calculated Amount", "display_name": "CLOSING minus MOVEMENT",
         "reference_code": "R7", "calculation_formula": "R4 - R5",
         "fieldtype": "Currency"},
    ]
    doc = frappe.get_doc({"doctype": "Financial Report Template",
                          "template_name": TPL,
                          "report_type": "Profit and Loss Statement",
                          "rows": rows})  # module intentionally omitted
    doc.insert(ignore_permissions=True)
    created.append(("Financial Report Template", doc.name))
    rec("tpl_inserted", {"name": doc.name, "module": doc.module,
                         "column_breaks": len([r for r in doc.rows
                                               if r.data_source == "Column Break"])})
    rec("tpl_stored_rows", frappe.db.sql("""
        select idx, data_source, display_name, ifnull(balance_type,'<null>') as balance_type
        from `tabFinancial Report Row` where parent = %s order by idx
    """, (doc.name,), as_dict=True))

    from erpnext.accounts.doctype.financial_report_template.financial_report_engine import (
        FinancialReportEngine,
    )

    def run(label, extra):
        base = {"company": COMPANY, "report_template": doc.name,
                "selected_view": "Report", "include_default_book_entries": 1}
        base.update(extra)
        try:
            res = FinancialReportEngine().execute(frappe._dict(base))
            cols, data = res[0], res[1]
            out = {
                "filters": base,
                "column_labels": [{"fieldname": c.get("fieldname"), "label": c.get("label"),
                                   "hidden": c.get("hidden", 0)} for c in cols],
                "visible_column_count": len([c for c in cols if not c.get("hidden")]),
                "uses_seg_prefix": any(str(c.get("fieldname", "")).startswith("seg_")
                                       for c in cols),
                "rows": [],
            }
            for r in data:
                keep = {}
                for k, v in r.items():
                    if k.startswith("_") or k == "segment_values":
                        continue
                    if k.endswith(("child_accounts", "period_start_date", "period_end_date",
                                   "acc_name", "acc_number", "currency", "indent")):
                        continue
                    keep[k] = v
                out["rows"].append(keep)
            rec("run_" + label, out)
            return out
        except Exception as exc:
            rec("run_error_" + label, {"err": str(exc), "tb": traceback.format_exc()[-1500:]})
            return None

    # window starting between the two GL days -> Stock has nonzero opening
    a = run("single_segment_daterange_from_0921", {
        "filter_based_on": "Date Range", "period_start_date": "2026-09-21",
        "period_end_date": "2026-12-31", "periodicity": "Monthly"})
    b = run("single_segment_FY2026_monthly", {
        "filter_based_on": "Fiscal Year", "from_fiscal_year": "2026",
        "to_fiscal_year": "2026", "periodicity": "Monthly"})

    def by_name(out):
        if not out:
            return {}
        m = {}
        for r in out["rows"]:
            nm = r.get("account_name") or r.get("seg_0_account_name")
            if nm:
                m[nm] = r
        return m

    verdict = {}
    m = by_name(a)
    if m:
        def val(nm, key):
            r = m.get(nm) or {}
            return r.get(key, r.get("seg_0_" + key.replace("seg_0_", "")))

        sc = val("STOCK as CLOSING", "sep_2026")
        sm = val("STOCK as MOVEMENT", "sep_2026")
        so = val("STOCK as OPENING", "sep_2026")
        ic = val("INC as CLOSING", "sep_2026")
        im = val("INC as MOVEMENT", "sep_2026")
        verdict = {
            "rows_present": sorted(m.keys()),
            "STOCK_closing_sep": sc, "STOCK_movement_sep": sm, "STOCK_opening_sep": so,
            "INC_closing_sep": ic, "INC_movement_sep": im,
            "three_types_differ_in_ONE_segment": len({sc, sm, so}) == 3,
            "closing_equals_opening_plus_movement": (
                round((so or 0) + (sm or 0), 4) == round(sc or 0, 4)),
            "so_balance_type_is_row_level": bool(
                sc != sm and sc != so and sm != so),
            "note": ("all three values come from rows in the SAME segment of the SAME "
                     "template in the SAME run, so balance_type cannot be a "
                     "segment-level or report-level setting"),
        }
    rec("DECISIVE_row_level", verdict)

    # single-segment column labels: does the ' - <period>' suffix appear?
    if a:
        labs = [c["label"] for c in a["column_labels"] if not c.get("hidden")]
        rec("single_segment_column_labels", {
            "labels": labs,
            "any_label_has_dash_period": any(" - " in l for l in labs),
            "uses_seg_prefix": a["uses_seg_prefix"],
            "note": ("no Column Break -> SingleSegmentFormatter -> base get_columns() "
                     "labels survive untouched, so the ' - <period>' suffix is a "
                     "MULTI-segment artifact only"),
        })
    if b:
        rec("single_segment_FY_labels",
            [c["label"] for c in b["column_labels"] if not c.get("hidden")])

except Exception as e:
    rec("probe_error", {"err": str(e), "tb": traceback.format_exc()[-3000:]})

finally:
    frappe.db.rollback()
    after = {dt: frappe.db.count(dt) for dt in EXPECTED_BASELINE}
    rec("baseline_after_rollback", after)
    rec("baseline_matches_expected", after == EXPECTED_BASELINE)
    rec("created_docs_still_present",
        [[dt, n] for dt, n in created if frappe.db.exists(dt, n)])
    import glob
    strays = []
    for pat in ("*zzrev*", "*ZZREV*", "*probe*"):
        strays += glob.glob(frappe.get_app_path(
            "erpnext", "accounts", "financial_report_template", pat))
    rec("stray_exported_files", strays)
    rec("fiscal_years_after", frappe.get_all("Fiscal Year", pluck="name"))

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(result, fh, ensure_ascii=False, indent=2, default=str)
    print("\nWROTE " + OUT, flush=True)
