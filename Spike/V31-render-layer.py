# V-31 seg1 (spine) -- does the translation machinery touch column labels between the
# engine and the human?
#
# PROPOSITION V-31: do the engine's column header strings survive intact all the way to
# what a human sees -- Desk datatable, XLSX, PDF/print? This script answers the part
# that both other segments depend on: IS `_()` / `__()` APPLIED TO LABELS, and if so,
# CAN it substitute a Chinese one?
#
# V-29 established the DATA layer: the engine emits literally
#   \u5E74\u521D\u4F59\u989D / \u5E74\u521D\u4F59\u989D - 2025 / \u5E74\u521D\u4F59\u989D - 2026 / \u671F\u672B\u4F59\u989D / ...
# This script starts from those same labels (V-29's bs_rows is reused verbatim so the
# strings are directly comparable) and asks what the render layer does to them.
#
# ---------------------------------------------------------------------------
# CRITERION DISCIPLINE -- the point that makes this probe worth anything
# ---------------------------------------------------------------------------
# "The Chinese label came out unchanged" is ambiguous. It can mean either
#   (a) the render layer does not translate labels, or
#   (b) the render layer DOES translate labels, but this particular Chinese string
#       happened to have no entry in the translation dict to collide with.
# Those are completely different answers for a project with 747 known key collisions.
# So this probe runs FOUR cells, not one:
#
#   NEG  Chinese statutory labels (\u5E74\u521D\u4F59\u989D ...)   -- the real case
#   POS  a label that IS a live key in the zh dict -- if this one comes out SUBSTITUTED
#        while NEG comes out intact, then `_()` is provably live and the criterion can
#        see substitution. If POS also came out intact, my NEG result would be worthless.
#   CJK  a Chinese label WITH an injected entry     -- proves a Chinese string is not
#        somehow immune; the only thing protecting it is dict contents.
#   LANG the same labels under lang=en vs lang=zh   -- the dict that applies depends on
#        the viewer's language, so the answer must be stated per-language.
#
# ---------------------------------------------------------------------------
# SITE SAFETY
# ---------------------------------------------------------------------------
# * Everything inside one transaction, `frappe.db.rollback()` in `finally`. No commit.
# * `module` left EMPTY on every template: FinancialReportTemplate.on_update ->
#   _export_template() writes JSON into the erpnext source tree when module is set,
#   and rollback cannot undo a filesystem write.
# * PRE-FLIGHT FINDING (V31-seg0-recon) -- the reason this file patches a framework
#   function: frappe/core/doctype/report/report.py:192 arms
#     threading.Timer(15s, enable_prepared_report, {report, site})
#   for any Script Report with prepared_report=0 and disable_prepared_report_automation=0,
#   which `Custom Financial Statement` is (seg0: timer_arms=true). enable_prepared_report
#   does frappe.init + frappe.connect + db.set_value("Report",...,"prepared_report",1)
#   + frappe.db.commit() ON ITS OWN CONNECTION -- our rollback could not undo it. It only
#   fires if the report takes >15s (the `finally` cancels it otherwise), but "probably
#   fast enough" is not a safety argument. So this file replaces that function with a
#   recorder no-op BEFORE calling run(), and afterwards re-reads Report.prepared_report
#   straight from the DB to prove it is still 0.
# * Error Log (`tabError Log`) is MyISAM -- rollback does NOT undo writes to it. This
#   probe writes nothing there deliberately; the count is asserted before and after, and
#   any row that did appear is reported, NEVER deleted by exclusion.
# * The translation-dict injections are IN-PROCESS ONLY: `frappe.translate
#   .get_all_translations` is monkey-patched inside this python process. Nothing is
#   written to the Translation doctype and nothing is written to the redis cache, so no
#   other process's translations are affected. All patches are undone in `finally`.
#
# Chinese appears ONLY as \uXXXX escapes -- this source is ASCII-only (the Windows host
# parses shell-fed Chinese as GBK).
#
# Run:
#   docker exec -i -e PYTHONUTF8=1 -e PYTHONIOENCODING=utf-8 \
#     -w /workspace/frappe-bench/sites erx001-frappe-1 \
#     /workspace/frappe-bench/env/bin/python /workspace/Spike/V31-render-layer.py

import glob
import inspect
import json
import os
import traceback

import frappe

SITE = "erx.localhost"
COMPANY = "\u534E\u4E1C\u5F39\u7C27"
OUT_DIR = "/workspace/Spike/V31-out"
OUT = os.path.join(OUT_DIR, "seg1-render-layer.json")

REPORT_NAME = "Custom Financial Statement"

# --- NEG cell: V-29's template A, the statutory literals -------------------
TPL_NEG = "ZZ-PROBE-V31-NEG-StatutoryLiteral"
SEG_NEG_0 = "\u5E74\u521D\u4F59\u989D"          # opening balance
SEG_NEG_1 = "\u671F\u672B\u4F59\u989D"          # closing balance

# --- long-label cell (for the truncation question, seg4) -------------------
TPL_LONG = "ZZ-PROBE-V31-LONG-RealisticPanes"
SEG_LONG_0 = "\u8D44\u4EA7"
SEG_LONG_1 = "\u8D1F\u503A\u548C\u6240\u6709\u8005\u6743\u76CA"   # 8 chars -> `... - 2026` is 15

# --- POS cell: display_name chosen at RUNTIME from the live zh dict --------
TPL_POS = "ZZ-PROBE-V31-POS-TranslatedKey"

# --- CJK cell: Chinese label with an injected dict entry ------------------
TPL_CJK = "ZZ-PROBE-V31-CJK-InjectedEntry"
SEG_CJK_0 = "\u5E74\u521D\u4F59\u989D"
SEG_CJK_1 = "\u671F\u672B\u4F59\u989D"
# what the injected entry maps it to -- deliberately WRONG, so a substitution is obvious
CJK_INJECTED_VALUE = "\u88AB\u7FFB\u8BD1\u5C42\u66FF\u6362\u4E86"   # "replaced by the translation layer"

result = {"probe": "V-31 seg1: is _()/__() applied to column labels, and can it alter Chinese?"}


def rec(k, v):
    result[k] = v
    print("[" + k + "] " + json.dumps(v, ensure_ascii=False, default=str)[:2400], flush=True)


def char_dump(s):
    """Verbatim, character-for-character. Same helper as V-29 so the two probes'
    strings are directly comparable, separators and stray whitespace included."""
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
    }


def bs_rows(seg0_name, seg1_name):
    """Two-segment Balance Sheet template. Copied from V-29 unchanged so the labels
    this probe observes are the same strings V-29 reported."""
    asset_f = json.dumps(["root_type", "=", "Asset"])
    liab_f = json.dumps(["root_type", "=", "Liability"])
    eq_f = json.dumps(["root_type", "=", "Equity"])

    return [
        {"data_source": "Column Break", "display_name": seg0_name},
        {"data_source": "Account Data", "display_name": "\u8D44\u4EA7\u5408\u8BA1",
         "reference_code": "S0_ASSET", "balance_type": "Closing Balance",
         "calculation_formula": asset_f, "fieldtype": "Currency", "bold_text": 1},
        {"data_source": "Account Data", "display_name": "\u8D1F\u503A\u5408\u8BA1",
         "reference_code": "S0_LIAB", "balance_type": "Closing Balance",
         "calculation_formula": liab_f, "reverse_sign": 1, "fieldtype": "Currency"},
        {"data_source": "Column Break", "display_name": seg1_name},
        {"data_source": "Account Data", "display_name": "\u6240\u6709\u8005\u6743\u76CA\u5408\u8BA1",
         "reference_code": "S1_EQ", "balance_type": "Closing Balance",
         "calculation_formula": eq_f, "reverse_sign": 1, "fieldtype": "Currency",
         "bold_text": 1},
        {"data_source": "Account Data", "display_name": "\u8D1F\u503A\u5408\u8BA1(\u53F3\u680F)",
         "reference_code": "S1_LIAB", "balance_type": "Closing Balance",
         "calculation_formula": liab_f, "reverse_sign": 1, "fieldtype": "Currency"},
    ]


def baseline():
    return {
        "GL Entry": frappe.db.count("GL Entry"),
        "Stock Ledger Entry": frappe.db.count("Stock Ledger Entry"),
        "Account": frappe.db.count("Account"),
        "Company": frappe.db.count("Company"),
        "Financial Report Template": frappe.db.count("Financial Report Template"),
        "Fiscal Year": sorted(r.name for r in frappe.get_all("Fiscal Year", fields=["name"])),
        "Error Log": frappe.db.count("Error Log"),
        "Translation": frappe.db.count("Translation"),
        "Prepared Report": frappe.db.count("Prepared Report"),
    }


frappe.init(site=SITE)
frappe.connect()
frappe.set_user("Administrator")
os.makedirs(OUT_DIR, exist_ok=True)

_orig_enable_prepared_report = None
_orig_get_all_translations = None
report_mod = None
translate_mod = None

try:
    rec("baseline_before", baseline())

    from frappe.core.doctype.report import report as report_mod
    import frappe.translate as translate_mod
    from frappe.translate import get_all_translations, get_user_lang
    from frappe.utils.translations import _ as underscore
    from erpnext.accounts.doctype.financial_report_template.financial_report_engine import (
        FinancialReportEngine,
    )

    # ---------- 0. neutralize the prepared-report commit BEFORE any run() -------
    enable_prepared_report_calls = []

    def _no_op_enable_prepared_report(report=None, site=None):
        enable_prepared_report_calls.append({"report": report, "site": site})

    _orig_enable_prepared_report = report_mod.enable_prepared_report
    report_mod.enable_prepared_report = _no_op_enable_prepared_report
    rec("prepared_report_commit_neutralized", {
        "patched": "frappe.core.doctype.report.report.enable_prepared_report",
        "original_source": inspect.getsource(_orig_enable_prepared_report),
        "why": ("it does db.set_value + db.commit() on a SEPARATE connection; our "
                "rollback could not undo it. Timer at report.py:192 arms for this report "
                "(seg0: timer_arms=true)."),
        "report_prepared_report_field_before": frappe.db.get_value(
            "Report", REPORT_NAME, "prepared_report"),
    })

    # ---------- 1. the language that actually applies ----------
    real_lang = get_user_lang("Administrator")
    rec("lang_facts", {
        "process_default_frappe.local.lang": getattr(frappe.local, "lang", None),
        "get_user_lang(Administrator)": real_lang,
        "note": ("a python probe's frappe.local.lang defaults to 'en'; a real Desk "
                 "request resolves it from the session user. The UI language here is "
                 "zh, so every render-layer test below is run under lang=zh, and "
                 "lang=en is kept as a contrast cell."),
    })

    zh_dict = get_all_translations("zh")
    rec("zh_dict_shape", {
        "entry_count": len(zh_dict),
        "keys_with_any_cjk": sum(
            1 for k in zh_dict
            if any(0x2E80 <= ord(c) <= 0x9FFF or 0xF900 <= ord(c) <= 0xFAFF
                   or 0xFF00 <= ord(c) <= 0xFFEF for c in k)),
        "note": ("`_()` looks up all_translations.get(label). A dict whose msgids are "
                 "all English can never match a Chinese label. This count is the whole "
                 "reason the NEG cell comes out clean -- it is a property of the DICT, "
                 "not of the render layer."),
    })

    # ---------- 2. pick the POS label from the LIVE dict at runtime ----------
    # Deterministic: shortest ASCII key whose translation differs, among plausible
    # balance-sheet words. Chosen at runtime rather than hardcoded so the cell cannot
    # silently stop being a positive control if the dict changes.
    pos_candidates = ["Assets", "Liabilities", "Equity", "Total", "Account",
                      "Balance Sheet", "Opening", "Closing", "Currency", "Account Name"]
    pos_found = [
        {"key": k, "zh_value": zh_dict[k]}
        for k in pos_candidates if k in zh_dict and zh_dict[k] != k
    ]
    rec("pos_control_candidates", {"tested": pos_candidates, "live_keys_found": pos_found})
    if not pos_found:
        rec("pos_control_UNAVAILABLE", "no candidate is a live zh key -- POS cell skipped")
        seg_pos_0 = seg_pos_1 = None
    else:
        seg_pos_0 = pos_found[0]["key"]
        seg_pos_1 = pos_found[1]["key"] if len(pos_found) > 1 else pos_found[0]["key"]
        rec("pos_control_chosen", {
            "segment_0_display_name": seg_pos_0,
            "segment_0_zh_translation": zh_dict[seg_pos_0],
            "segment_1_display_name": seg_pos_1,
            "segment_1_zh_translation": zh_dict[seg_pos_1],
            "prediction": ("the ACCOUNT column label is exactly this key, so `_()` should "
                           "SUBSTITUTE it; the PERIOD column label is '<key> - 2026', which "
                           "is NOT a key, so it should pass through. Two different outcomes "
                           "in one export = the criterion demonstrably discriminates."),
        })

    # ---------- 3. create FY 2025 so a two-year axis exists ----------
    if not frappe.db.exists("Fiscal Year", "2025"):
        fy = frappe.get_doc({"doctype": "Fiscal Year", "year": "2025",
                             "year_start_date": "2025-01-01", "year_end_date": "2025-12-31"})
        fy.insert(ignore_permissions=True)
        rec("created_fiscal_year", {"name": fy.name, "note": "inside txn, rolled back"})

    # ---------- 4. build the templates ----------
    def make_tpl(name, s0, s1):
        doc = frappe.get_doc({
            "doctype": "Financial Report Template",
            "template_name": name,
            "report_type": "Balance Sheet",
            # module deliberately EMPTY -- see header note on _export_template()
            "rows": bs_rows(s0, s1),
        })
        doc.insert(ignore_permissions=True)
        return doc

    built = {}
    cells = [("NEG_statutory_chinese", TPL_NEG, SEG_NEG_0, SEG_NEG_1),
             ("LONG_realistic_panes", TPL_LONG, SEG_LONG_0, SEG_LONG_1),
             ("CJK_injected_entry", TPL_CJK, SEG_CJK_0, SEG_CJK_1)]
    if seg_pos_0:
        cells.append(("POS_translated_key", TPL_POS, seg_pos_0, seg_pos_1))

    for tag, name, s0, s1 in cells:
        d = make_tpl(name, s0, s1)
        built[tag] = d.name
        rec("template_built_" + tag, {
            "name": d.name, "module": d.module,
            "column_breaks": [{"idx": r.idx, "display_name": r.display_name}
                              for r in d.rows if r.data_source == "Column Break"],
        })

    def filters_for(tpl):
        return frappe._dict({
            "company": COMPANY, "report_template": tpl,
            "filter_based_on": "Fiscal Year",
            "from_fiscal_year": "2025", "to_fiscal_year": "2026",
            "periodicity": "Yearly", "selected_view": "Report",
            "include_default_book_entries": 1,
        })

    # ---------- 5. ENGINE labels (the V-29 baseline, re-established here) ----------
    engine_cols = {}
    for tag, tpl in built.items():
        cols = FinancialReportEngine().execute(filters_for(tpl))[0]
        engine_cols[tag] = cols
        rec("ENGINE_LABELS_" + tag, [
            {"fieldname": c.get("fieldname"), "label": c.get("label"),
             "hidden": c.get("hidden", 0), "width": c.get("width"),
             "fieldtype": c.get("fieldtype")}
            for c in cols])
    rec("ENGINE_LABELS_CHARDUMP_NEG", [
        {"fieldname": c.get("fieldname"), "label_chars": char_dump(c.get("label"))}
        for c in engine_cols["NEG_statutory_chinese"]])
    # reproduce V-29's exact expectation so any drift is visible
    rec("V29_REPRODUCTION_CHECK", {
        "expected": [SEG_NEG_0, SEG_NEG_0 + " - 2025", SEG_NEG_0 + " - 2026",
                     SEG_NEG_1, SEG_NEG_1 + " - 2025", SEG_NEG_1 + " - 2026"],
        "observed_visible": [c["label"] for c in engine_cols["NEG_statutory_chinese"]
                             if not c.get("hidden")],
        "matches_V29": ([c["label"] for c in engine_cols["NEG_statutory_chinese"]
                         if not c.get("hidden")]
                        == [SEG_NEG_0, SEG_NEG_0 + " - 2025", SEG_NEG_0 + " - 2026",
                            SEG_NEG_1, SEG_NEG_1 + " - 2025", SEG_NEG_1 + " - 2026"]),
    })

    # ---------- 6. what `_()` does to each label, per language ----------
    # This IS the XLSX header transform: query_report.py:692 is literally
    #     column_data.append(_(column.get("label")))
    xlsx_line = [ln.strip() for ln in inspect.getsource(
        __import__("frappe.desk.query_report", fromlist=["x"])).splitlines()
        if "column_data.append" in ln]
    rec("xlsx_header_transform_is_literally", xlsx_line)

    for lang in ["zh", "en"]:
        frappe.local.lang = lang
        per_lang = {}
        for tag, cols in engine_cols.items():
            rows = []
            for c in cols:
                lbl = c.get("label")
                out = underscore(lbl)
                rows.append({
                    "fieldname": c.get("fieldname"),
                    "engine_label": lbl,
                    "after_underscore": out,
                    "changed": out != lbl,
                    "is_dict_key": lbl in get_all_translations(lang),
                })
            per_lang[tag] = {
                "columns": rows,
                "any_changed": any(r["changed"] for r in rows),
                "changed_fieldnames": [r["fieldname"] for r in rows if r["changed"]],
            }
        rec("UNDERSCORE_ON_LABELS_lang_" + lang, per_lang)
    frappe.local.lang = "zh"

    # ---------- 7. CJK cell: inject a Chinese entry, in-process only ----------
    # Proves a Chinese string is not immune -- the only thing protecting it upstream is
    # that the shipped zh dict has no CJK msgids. If a Translation row (or any future
    # zh msgid) ever carried one of these strings, the header WOULD change.
    _orig_get_all_translations = translate_mod.get_all_translations
    injected = dict(zh_dict)
    injected[SEG_CJK_0] = CJK_INJECTED_VALUE
    injected[SEG_CJK_1 + " - 2026"] = CJK_INJECTED_VALUE

    def _patched_get_all_translations(lang):
        return injected if lang == "zh" else _orig_get_all_translations(lang)

    translate_mod.get_all_translations = _patched_get_all_translations
    try:
        cjk_rows = []
        for c in engine_cols["CJK_injected_entry"]:
            lbl = c.get("label")
            out = underscore(lbl)
            cjk_rows.append({"fieldname": c.get("fieldname"), "engine_label": lbl,
                             "after_underscore": out, "changed": out != lbl})
        rec("CJK_INJECTION_RESULT", {
            "injected_entries": {SEG_CJK_0: CJK_INJECTED_VALUE,
                                 SEG_CJK_1 + " - 2026": CJK_INJECTED_VALUE},
            "columns": cjk_rows,
            "any_changed": any(r["changed"] for r in cjk_rows),
            "conclusion_if_changed": ("`_()` will happily replace a Chinese header. The "
                                      "NEG cell's clean result is therefore a fact about "
                                      "the dict's contents, not about label immunity."),
        })
    finally:
        translate_mod.get_all_translations = _orig_get_all_translations
        _orig_get_all_translations = None
    rec("cjk_injection_reverted", {
        "get_all_translations_restored": translate_mod.get_all_translations is not
        _patched_get_all_translations,
        "reverted_label_check": underscore(SEG_CJK_0) == SEG_CJK_0,
    })

    # ---------- 8. WHAT THE SERVER SENDS THE CLIENT (datatable input) ----------
    # frappe.desk.query_report.run is exactly what the Desk calls. Its `columns` payload
    # is what query_report.js feeds the datatable.
    from frappe.desk.query_report import run as qr_run

    for tag in ["NEG_statutory_chinese", "LONG_realistic_panes"]:
        payload = qr_run(REPORT_NAME, filters=dict(filters_for(built[tag])),
                         ignore_prepared_report=True, are_default_filters=False)
        rec("RUN_PAYLOAD_COLUMNS_" + tag, [
            {"fieldname": c.get("fieldname"), "label": c.get("label"),
             "hidden": c.get("hidden", 0), "width": c.get("width")}
            for c in payload.get("columns", [])])
        rec("RUN_PAYLOAD_META_" + tag, {
            "add_total_row": payload.get("add_total_row"),
            "row_count": len(payload.get("result") or []),
            "skip_total_row": payload.get("skip_total_row"),
            "prepared_report": payload.get("prepared_report"),
            "labels_identical_to_engine": (
                [c.get("label") for c in payload.get("columns", [])]
                == [c.get("label") for c in engine_cols[tag]]),
        })
    rec("RUN_PAYLOAD_CHARDUMP_NEG", [
        {"fieldname": c.get("fieldname"), "label_chars": char_dump(c.get("label"))}
        for c in qr_run(REPORT_NAME,
                        filters=dict(filters_for(built["NEG_statutory_chinese"])),
                        ignore_prepared_report=True,
                        are_default_filters=False).get("columns", [])])

    # ---------- 9. the client-side consumer, quoted from live source ----------
    js = frappe.get_app_path("frappe", "public", "js", "frappe", "views", "reports",
                             "query_report.js")
    with open(js, encoding="utf-8") as f:
        js_src = f.read()
    lines = js_src.splitlines()
    name_line_idx = [i for i, ln in enumerate(lines) if "is_query_generated_report ? __(" in ln]
    rec("datatable_label_assignment_js", {
        "path": js,
        "line_numbers_1based": [i + 1 for i in name_line_idx],
        "context": ["%d: %s" % (i + 1, lines[i].strip())
                    for idx in name_line_idx for i in range(max(0, idx - 5), idx + 2)],
    })
    guard_idx = [i for i, ln in enumerate(lines) if "let is_query_generated_report" in ln]
    rec("is_query_generated_report_guard_js", {
        "line_numbers_1based": [i + 1 for i in guard_idx],
        "source": ["%d: %s" % (i + 1, lines[i].strip())
                   for idx in guard_idx for i in range(idx, min(len(lines), idx + 4))],
        "report_query_field_live_value": frappe.db.get_value("Report", REPORT_NAME, "query"),
        "therefore_is_query_generated_report": bool(
            frappe.db.get_value("Report", REPORT_NAME, "query")),
        "meaning": ("false => the datatable column name is `column.label`, the raw server "
                    "string, with NO __() applied"),
    })
    # does either report-side JS touch labels?
    for tag, p in [
        ("custom_financial_statement.js", frappe.get_app_path(
            "erpnext", "accounts", "report", "custom_financial_statement",
            "custom_financial_statement.js")),
        ("erpnext_financial_statements.js", frappe.get_app_path(
            "erpnext", "public", "js", "financial_statements.js")),
    ]:
        with open(p, encoding="utf-8") as f:
            s = f.read()
        rec("report_js_label_mutation_" + tag, {
            "path": p,
            "assigns_column_label": ("column.label =" in s or "col.label =" in s
                                     or "columns[" in s and ".label =" in s),
            "has_get_datatable_options": "get_datatable_options" in s,
            "has_get_columns": "get_columns" in s,
            "underscore_on_column_label": "__(column.label" in s or "__(col.label" in s,
            "occurrences_of_column_label": s.count("column.label") + s.count("col.label"),
        })

    # ---------- 10. safety re-assertions ----------
    rec("prepared_report_timer_outcome", {
        "no_op_was_called": enable_prepared_report_calls,
        "Report.prepared_report_from_db_now": frappe.db.get_value(
            "Report", REPORT_NAME, "prepared_report"),
        "expect": 0,
    })

except Exception as e:
    rec("probe_error", {"err": str(e), "tb": traceback.format_exc()[-3000:]})

finally:
    if _orig_get_all_translations is not None and translate_mod is not None:
        translate_mod.get_all_translations = _orig_get_all_translations
    if _orig_enable_prepared_report is not None and report_mod is not None:
        report_mod.enable_prepared_report = _orig_enable_prepared_report
        rec("patches_reverted", {
            "enable_prepared_report_restored":
                report_mod.enable_prepared_report is _orig_enable_prepared_report,
        })

    frappe.db.rollback()

    rec("baseline_after_rollback", baseline())
    rec("templates_exist_after_rollback", {
        n: bool(frappe.db.exists("Financial Report Template", n))
        for n in [TPL_NEG, TPL_LONG, TPL_POS, TPL_CJK]})
    rec("Report_prepared_report_after_rollback",
        frappe.db.get_value("Report", REPORT_NAME, "prepared_report"))
    # any Error Log row at all is reported, never deleted -- MyISAM, and another probe
    # this round destroyed pre-existing rows by deleting "rows not in my baseline"
    rec("error_log_rows_now", frappe.get_all(
        "Error Log", fields=["name", "method", "creation"], limit=20))

    strays = []
    for pat in ("*probe*", "*PROBE*", "*v31*", "*V31*", "*zz*", "*ZZ*"):
        strays += glob.glob(frappe.get_app_path(
            "erpnext", "accounts", "financial_report_template", pat))
        strays += glob.glob(frappe.get_app_path(
            "erpnext", "accounts", "doctype", "financial_report_template", pat))
    rec("stray_exported_files", sorted(set(strays)))

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)
    print("\nWROTE " + OUT, flush=True)
