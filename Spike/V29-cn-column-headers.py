# V-29 probe: build a TWO-SEGMENT Balance Sheet `Financial Report Template` whose
# two `Column Break` rows carry CHINESE `display_name` values, run it across TWO
# fiscal years with periodicity=Yearly, and observe the six ACTUAL column labels.
#
# Proposition V-29: are the six labels of the form `中文 - 2025` / `中文 - 2026`?
#
# WHY: V-25 ran the FACTORY template (English segment labels) and established the
# mechanism at financial_report_engine.py:1727-1728 -- segment half from the
# template's Column Break display_name, period half computed by the engine. But
# V-25 never actually RAN a self-built template with Chinese segment labels on the
# "two-segment balance sheet x two fiscal years" combination. V-25's own 复核建议
# item 2 flags exactly this as unverified. This probe closes that gap by RUNNING it.
#
# The verdict must come from printed output, not from re-reading :1727.
#
# WRITES NOTHING PERMANENT. Fiscal Year 2025 and two temp templates are created
# inside a transaction and rolled back in `finally`. There is no
# frappe.db.commit() anywhere in this file.
#
# `module` is deliberately left EMPTY on both templates: FinancialReportTemplate.
# on_update -> _export_template() writes template JSON into the erpnext source
# tree when module is set, and that filesystem write rollback would NOT undo.
# Verified financial_report_template.py:59-65 returns early when module is falsy.
#
# Run (cwd MUST be .../sites, else frappe's logger dies on a relative path;
#      PYTHONUTF8 needed because this file carries Chinese string literals):
#   docker exec -i -e PYTHONUTF8=1 -e PYTHONIOENCODING=utf-8 \
#     -w /workspace/frappe-bench/sites erx001-frappe-1 \
#     /workspace/frappe-bench/env/bin/python /workspace/Spike/V29-cn-column-headers.py

import glob
import json
import os
import traceback

import frappe

SITE = "erx.localhost"
COMPANY = "华东弹簧"
OUT_DIR = "/workspace/Spike/V29-out"
OUT = os.path.join(OUT_DIR, "cn-column-headers.json")

# Template A: the Column Break display_name IS the statutory literal we want.
# If the engine appended nothing, these two names alone would be compliant.
TPL_A = "ZZ-PROBE-V29-BS-StatutoryLiteral"
SEG_A0 = "年初余额"
SEG_A1 = "期末余额"

# Template B: a realistic Chinese two-pane balance sheet layout. Corroborates
# that the behaviour is not an artifact of the particular strings chosen in A.
TPL_B = "ZZ-PROBE-V29-BS-RealisticPanes"
SEG_B0 = "资产"
SEG_B1 = "负债和所有者权益"

# Template C: Column Break display_name left EMPTY. Tests whether the ` - {period}`
# suffix is OPTIONAL -- i.e. whether omitting the segment label buys you a bare
# period column. Bears directly on "what cannot be controlled". :1727 guards the
# concatenation on `if segment.label`, so the suffix should vanish -- but then the
# account column falls back to `Account (Segment N)` and the Chinese is gone too.
TPL_C = "ZZ-PROBE-V29-BS-EmptySegmentLabel"
SEG_C0 = ""
SEG_C1 = ""

result = {"probe": "V-29 chinese Column Break display_name -> actual column labels, 2 FY x Yearly"}


def rec(k, v):
    result[k] = v
    print("[" + k + "] " + json.dumps(v, ensure_ascii=False, default=str)[:2600], flush=True)


def char_dump(s):
    """Verbatim, character-for-character rendering so the separator and any
    stray whitespace cannot hide. Distinguishes ' - ' from '-' from U+00A0 etc."""
    if s is None:
        return None
    return {
        "raw": s,
        "repr": repr(s),
        "len": len(s),
        "codepoints": ["U+%04X" % ord(c) for c in s],
        "has_leading_ws": s != s.lstrip(),
        "has_trailing_ws": s != s.rstrip(),
        "starts_with_hyphen": s.startswith("-"),
        "hyphen_neighbourhood": [
            {"i": i, "prev": repr(s[i - 1]) if i else None,
             "next": repr(s[i + 1]) if i + 1 < len(s) else None}
            for i, c in enumerate(s) if c == "-"
        ],
    }


def bs_rows(seg0_name, seg1_name):
    """Two-segment Balance Sheet template.

    Segment 0 and segment 1 both use balance_type 'Closing Balance' so both
    panes carry real numbers -- otherwise an empty pane could not prove the
    label came out of a live column. Only the Column Break display_name differs
    between template A and B; every other row is identical.
    """
    asset_f = json.dumps(["root_type", "=", "Asset"])
    liab_f = json.dumps(["root_type", "=", "Liability"])
    eq_f = json.dumps(["root_type", "=", "Equity"])

    return [
        # ---- segment 0 ----
        {"data_source": "Column Break", "display_name": seg0_name},
        {"data_source": "Account Data", "display_name": "资产合计",
         "reference_code": "S0_ASSET", "balance_type": "Closing Balance",
         "calculation_formula": asset_f, "fieldtype": "Currency", "bold_text": 1},
        {"data_source": "Account Data", "display_name": "负债合计",
         "reference_code": "S0_LIAB", "balance_type": "Closing Balance",
         "calculation_formula": liab_f, "reverse_sign": 1, "fieldtype": "Currency"},
        # ---- segment 1 ----
        {"data_source": "Column Break", "display_name": seg1_name},
        {"data_source": "Account Data", "display_name": "所有者权益合计",
         "reference_code": "S1_EQ", "balance_type": "Closing Balance",
         "calculation_formula": eq_f, "reverse_sign": 1, "fieldtype": "Currency", "bold_text": 1},
        {"data_source": "Account Data", "display_name": "负债合计(右栏)",
         "reference_code": "S1_LIAB", "balance_type": "Closing Balance",
         "calculation_formula": liab_f, "reverse_sign": 1, "fieldtype": "Currency"},
    ]


frappe.init(site=SITE)
frappe.connect()
frappe.set_user("Administrator")

os.makedirs(OUT_DIR, exist_ok=True)

try:
    # ---------- 0. baseline BEFORE any write ----------
    baseline_before = {
        "GL Entry": frappe.db.count("GL Entry"),
        "Stock Ledger Entry": frappe.db.count("Stock Ledger Entry"),
        "Account": frappe.db.count("Account"),
        "Company": frappe.db.count("Company"),
        "Financial Report Template": frappe.db.count("Financial Report Template"),
        "Fiscal Year": sorted(r.name for r in frappe.get_all("Fiscal Year", fields=["name"])),
    }
    rec("baseline_before", baseline_before)
    rec("existing_templates", sorted(
        r.name for r in frappe.get_all("Financial Report Template", fields=["name"])))

    # ---------- 1. confirm the write path carries no commit / enqueue ----------
    # (grepped from the shell too; asserted here from live source so the JSON is
    #  self-contained and the claim is reproducible)
    import inspect

    from erpnext.accounts.doctype.financial_report_template import financial_report_engine as fre
    from erpnext.accounts.doctype.financial_report_template import (
        financial_report_template as frt_mod,
    )
    import erpnext.accounts.report.financial_statements as fs_mod
    from erpnext.accounts.doctype.fiscal_year import fiscal_year as fy_mod

    danger = {}
    for tag, mod in [("financial_report_engine", fre), ("financial_report_template", frt_mod),
                     ("financial_statements", fs_mod), ("fiscal_year", fy_mod)]:
        src = inspect.getsource(mod)
        danger[tag] = {
            "db.commit": src.count("db.commit"),
            "frappe.enqueue": src.count("frappe.enqueue"),
            "enqueue_doc": src.count("enqueue_doc"),
        }
    rec("write_path_commit_enqueue_scan", danger)
    rec("export_template_guard", inspect.getsource(frt_mod.FinancialReportTemplate._export_template))

    # ---------- 2. create FY 2025 inside the txn so a 2-FY period axis exists ----------
    created_fy = None
    if not frappe.db.exists("Fiscal Year", "2025"):
        fy = frappe.get_doc({
            "doctype": "Fiscal Year", "year": "2025",
            "year_start_date": "2025-01-01", "year_end_date": "2025-12-31",
        })
        fy.insert(ignore_permissions=True)
        created_fy = fy.name
        rec("created_fiscal_year", {"name": fy.name, "note": "inside txn, rolled back at end"})

    from erpnext.accounts.doctype.financial_report_template.financial_report_engine import (
        FinancialReportEngine,
    )

    # ---------- 3. build + run both templates ----------
    for tag, tpl_name, s0, s1 in [("A_statutory_literal", TPL_A, SEG_A0, SEG_A1),
                                  ("B_realistic_panes", TPL_B, SEG_B0, SEG_B1),
                                  ("C_empty_segment_label", TPL_C, SEG_C0, SEG_C1)]:
        doc = frappe.get_doc({
            "doctype": "Financial Report Template",
            "template_name": tpl_name,
            "report_type": "Balance Sheet",
            # module deliberately EMPTY -- see header note on _export_template()
            "rows": bs_rows(s0, s1),
        })
        doc.insert(ignore_permissions=True)
        rec("template_inserted_" + tag, {
            "name": doc.name,
            "module": doc.module,
            "report_type": doc.report_type,
            "rows": len(doc.rows),
            "column_breaks": [{"idx": r.idx, "display_name": r.display_name}
                              for r in doc.rows if r.data_source == "Column Break"],
        })
        # prove what actually landed in the DB child rows (not just what we sent)
        rec("column_breaks_readback_" + tag, frappe.get_all(
            "Financial Report Row",
            filters={"parent": doc.name, "data_source": "Column Break"},
            fields=["idx", "display_name"], order_by="idx"))

        filters = frappe._dict({
            "company": COMPANY, "report_template": doc.name,
            "filter_based_on": "Fiscal Year",
            "from_fiscal_year": "2025", "to_fiscal_year": "2026",
            "periodicity": "Yearly", "selected_view": "Report",
            "include_default_book_entries": 1,
        })
        rec("filters_used_" + tag, dict(filters))

        try:
            res = FinancialReportEngine().execute(filters)
            cols, data = res[0], res[1]

            rec("engine_column_count_" + tag, len(cols))
            rec("OBSERVED_LABELS_" + tag, [
                {"fieldname": c.get("fieldname"),
                 "label": c.get("label"),
                 "fieldtype": c.get("fieldtype"),
                 "hidden": c.get("hidden", 0)}
                for c in cols])
            # verbatim, character-for-character
            rec("LABELS_CHAR_DUMP_" + tag, [
                {"fieldname": c.get("fieldname"), "label_chars": char_dump(c.get("label"))}
                for c in cols])

            # does each observed label equal exactly f"{segment} - {period}"?
            # :1727 guards the concatenation on `if segment.label`, and :1724 falls
            # back to `Account (Segment N)`. Encode both branches so the empty-label
            # case is scored against what the code says, not against the A/B pattern.
            expected = {}
            for seg_i, seg_label in enumerate([s0, s1]):
                for period in ("2025", "2026"):
                    expected["seg_%d_dec_%s" % (seg_i, period)] = (
                        seg_label + " - " + period if seg_label else period)
                expected["seg_%d_account" % seg_i] = (
                    seg_label if seg_label else "Account (Segment %d)" % (seg_i + 1))
            match = []
            for c in cols:
                fn = c.get("fieldname")
                if fn in expected:
                    match.append({
                        "fieldname": fn,
                        "observed": c.get("label"),
                        "expected_if_seg_space_hyphen_space_period": expected[fn],
                        "exact_match": c.get("label") == expected[fn],
                    })
            rec("HYPOTHESIS_CHECK_" + tag, {
                "per_column": match,
                "all_exact": bool(match) and all(m["exact_match"] for m in match),
                "checked": len(match),
            })

            # numbers must be real, else a label could belong to a dead column
            rec("engine_rowcount_" + tag, len(data))
            sample = []
            for r in data[:6]:
                sample.append({k: v for k, v in r.items()
                               if not str(k).startswith("_") and k != "segment_values"})
            rec("engine_sample_rows_" + tag, sample)
            nonzero = {}
            for c in cols:
                fn = c.get("fieldname")
                if fn and fn.endswith(("2025", "2026")):
                    nonzero[fn] = sum(1 for r in data if r.get(fn))
            rec("nonzero_value_count_per_period_column_" + tag, nonzero)

        except Exception as e:
            rec("engine_error_" + tag, {"err": str(e), "tb": traceback.format_exc()[-2000:]})

    # ---------- 4. is the segment half translated anywhere? ----------
    src_engine = inspect.getsource(fre.MultiSegmentFormatter.get_columns)
    rec("multisegment_get_columns_source", src_engine)
    rec("segment_label_is_translated", {
        "uses_underscore_call_on_segment_label": "_(segment.label" in src_engine,
        "note": "if False, the Chinese string is passed through verbatim, no translation layer",
    })
    rec("get_label_source", inspect.getsource(fs_mod.get_label))

    # ---------- 5. any template-side entry point for the PERIOD half? ----------
    row_fields = [f.fieldname for f in frappe.get_meta("Financial Report Row").fields]
    tpl_fields = [f.fieldname for f in frappe.get_meta("Financial Report Template").fields]
    rec("row_doctype_field_count", len(row_fields))
    rec("row_doctype_fields", row_fields)
    rec("template_doctype_fields", tpl_fields)
    rec("period_label_entry_points_in_template_layer", {
        "row_fields_matching_label_or_header": [f for f in row_fields
                                                if "label" in f.lower() or "header" in f.lower()],
        "template_fields_matching_label_or_header": [f for f in tpl_fields
                                                     if "label" in f.lower() or "header" in f.lower()],
        "row_fields_matching_period": [f for f in row_fields if "period" in f.lower()],
    })

except Exception as e:
    rec("probe_error", {"err": str(e), "tb": traceback.format_exc()[-2500:]})

finally:
    frappe.db.rollback()

    baseline_after = {
        "GL Entry": frappe.db.count("GL Entry"),
        "Stock Ledger Entry": frappe.db.count("Stock Ledger Entry"),
        "Account": frappe.db.count("Account"),
        "Company": frappe.db.count("Company"),
        "Financial Report Template": frappe.db.count("Financial Report Template"),
        "Fiscal Year": sorted(r.name for r in frappe.get_all("Fiscal Year", fields=["name"])),
    }
    rec("baseline_after_rollback", baseline_after)
    rec("templates_exist_after_rollback", {
        TPL_A: bool(frappe.db.exists("Financial Report Template", TPL_A)),
        TPL_B: bool(frappe.db.exists("Financial Report Template", TPL_B)),
        TPL_C: bool(frappe.db.exists("Financial Report Template", TPL_C)),
    })

    strays = []
    for pat in ("*probe*", "*PROBE*", "*v29*", "*V29*", "*zz*", "*ZZ*"):
        strays += glob.glob(frappe.get_app_path(
            "erpnext", "accounts", "financial_report_template", pat))
        strays += glob.glob(frappe.get_app_path(
            "erpnext", "accounts", "doctype", "financial_report_template", pat))
    rec("stray_exported_files", sorted(set(strays)))
    rec("exported_template_dir_listing", sorted(
        os.path.basename(p) for p in glob.glob(frappe.get_app_path(
            "erpnext", "accounts", "financial_report_template", "*"))))

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)
    print("\nWROTE " + OUT, flush=True)
