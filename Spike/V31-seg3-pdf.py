# V-31 seg3 -- PDF / PRINT: do the header characters survive into the PDF a human
# receives?
#
# TWO SEPARATE QUESTIONS, and they have different answers, so they are asked separately:
#
#   Q1 (TEXT): does the print path re-translate the header STRING?
#       The report PDF is built CLIENT-side: query_report.js renders the print_grid
#       microtemplate and POSTs the resulting HTML to
#       frappe.utils.print_format.report_to_pdf. print_grid.html emits the header cell as
#           {{ __(col.name) }}
#       -- i.e. the print path applies __() to the header, where the datatable itself
#       does not (query_report.js:1434 skips __() for a non-query report). So the print
#       path carries a translation step the screen does not. This probe reproduces that
#       transform against the SAME dict the browser gets (frappe.boot.__messages ==
#       get_messages_for_boot() == get_all_translations(lang)) and reports both cells.
#
#   Q2 (GLYPHS): can the PDF engine actually DRAW those characters?
#       A string can survive every transform and still reach the human as blank boxes if
#       the renderer has no font covering the codepoints. `fc-list` in this container
#       returns 11 fonts and `fc-match sans-serif:lang=zh-cn` falls back to DejaVu Sans,
#       which has no CJK coverage. So this is asked EMPIRICALLY: render a real PDF through
#       frappe.utils.pdf.get_pdf (the same function report_to_pdf calls) and extract the
#       text back out with pypdf, an independent reader.
#
# CRITERION DISCIPLINE: same NEG/POS split as seg1/seg2.
#   NEG  Chinese statutory headers  -> tests whether __() leaves them alone
#   POS  a header that IS a live key -> must come out SUBSTITUTED, otherwise the
#        NEG result is not evidence of anything
#   ASCII control in the glyph test -> if the ASCII header extracts cleanly from the same
#        PDF while the Chinese does not, the failure is font coverage, not my extractor.
#
# SITE SAFETY
# * Read-only as far as the DB is concerned apart from the templates, which live inside a
#   transaction rolled back in `finally`. No commit anywhere. `module` left EMPTY.
# * DELIBERATELY NOT CALLING `report_to_pdf`. Pre-flight grep of that path found
#   frappe/utils/print_format.py:266 `make_access_log(...)` ->
#   Document.deferred_insert() (model/document.py:1985) -> frappe.cache.rpush into
#   `insert_queue_for_Access Log`. That is a REDIS write my transaction does not own, and
#   frappe/deferred_insert.py:save_to_db() later inserts it AND COMMITS. rollback could
#   not undo it. So this probe calls frappe.utils.pdf.get_pdf directly -- the exact
#   function report_to_pdf delegates the rendering to (print_format.py:268) -- which
#   pre-flight shows has no db.commit, no enqueue, no save_file and no make_access_log.
#   The consequence for the finding is stated honestly in the report: the rendering is
#   real, the access-log bookkeeping around it is skipped.
# * get_pdf writes a /tmp cookie-jar ONLY when `frappe.local.request` exists
#   (pdf.py:255); a CLI probe has no request, so no jar is created. Asserted below, and
#   /tmp is swept for `*.jar` before/after either way.
# * Error Log is MyISAM: counted before/after, any row REPORTED, never deleted.
# * Files written: only /workspace/Spike/V31-out/*.pdf and *.html, on purpose, reported.
#
# Chinese appears ONLY as \uXXXX escapes -- this source is ASCII-only.
#
# Run:
#   docker exec -i -e PYTHONUTF8=1 -e PYTHONIOENCODING=utf-8 \
#     -w /workspace/frappe-bench/sites erx001-frappe-1 \
#     /workspace/frappe-bench/env/bin/python /workspace/Spike/V31-seg3-pdf.py

import glob
import inspect
import io
import json
import os
import subprocess
import traceback

import frappe

SITE = "erx.localhost"
COMPANY = "\u534E\u4E1C\u5F39\u7C27"
OUT_DIR = "/workspace/Spike/V31-out"
OUT = os.path.join(OUT_DIR, "seg3-pdf.json")
REPORT_NAME = "Custom Financial Statement"

TPL_NEG = "ZZ-PROBE-V31P-NEG-StatutoryLiteral"
SEG_NEG_0 = "\u5E74\u521D\u4F59\u989D"
SEG_NEG_1 = "\u671F\u672B\u4F59\u989D"
TPL_LONG = "ZZ-PROBE-V31P-LONG-RealisticPanes"
SEG_LONG_0 = "\u8D44\u4EA7"
SEG_LONG_1 = "\u8D1F\u503A\u548C\u6240\u6709\u8005\u6743\u76CA"
TPL_POS = "ZZ-PROBE-V31P-POS-TranslatedKey"

ASCII_CONTROL_HEADER = "ZZASCIICONTROL"   # must extract cleanly, or my reader is at fault

result = {"probe": "V-31 seg3: PDF/print header text transform + glyph coverage"}


def rec(k, v):
    result[k] = v
    print("[" + k + "] " + json.dumps(v, ensure_ascii=False, default=str)[:2400], flush=True)


def char_dump(s):
    if s is None:
        return None
    return {"raw": s, "repr": repr(s), "len": len(s),
            "codepoints": ["U+%04X" % ord(c) for c in s],
            "has_leading_ws": s != s.lstrip(), "has_trailing_ws": s != s.rstrip()}


def bs_rows(seg0_name, seg1_name):
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
        "Access Log": frappe.db.count("Access Log"),
        "Translation": frappe.db.count("Translation"),
        "File": frappe.db.count("File"),
    }


frappe.init(site=SITE)
frappe.connect()
frappe.set_user("Administrator")
os.makedirs(OUT_DIR, exist_ok=True)

_orig_enable_prepared_report = None
report_mod = None
files_written = []

try:
    rec("baseline_before", baseline())
    jars_before = sorted(glob.glob("/tmp/*.jar"))
    rec("tmp_jars_before", jars_before)

    from frappe.core.doctype.report import report as report_mod
    import frappe.utils.pdf as pdf_mod
    import frappe.utils.print_format as pf_mod
    from frappe.translate import get_all_translations, get_messages_for_boot, get_user_lang
    from frappe.utils.translations import _ as underscore
    from erpnext.accounts.doctype.financial_report_template.financial_report_engine import (
        FinancialReportEngine,
    )

    def _no_op_enable_prepared_report(report=None, site=None):
        rec("UNEXPECTED_enable_prepared_report_call", {"report": report, "site": site})

    _orig_enable_prepared_report = report_mod.enable_prepared_report
    report_mod.enable_prepared_report = _no_op_enable_prepared_report

    # ---------- 0. why report_to_pdf is NOT called ----------
    rec("why_not_report_to_pdf", {
        "report_to_pdf_source": inspect.getsource(pf_mod.report_to_pdf),
        "side_effect": ("make_access_log -> Document.deferred_insert -> frappe.cache.rpush "
                        "'insert_queue_for_Access Log'; frappe/deferred_insert.py save_to_db() "
                        "later inserts AND COMMITS -> outside our transaction, rollback "
                        "cannot undo it"),
        "what_this_probe_calls_instead": "frappe.utils.pdf.get_pdf (print_format.py:268)",
        "get_pdf_side_effect_census": {
            "db.commit": inspect.getsource(pdf_mod).count("db.commit"),
            "frappe.enqueue": inspect.getsource(pdf_mod).count("frappe.enqueue"),
            "save_file": inspect.getsource(pdf_mod).count("save_file"),
            "make_access_log": inspect.getsource(pdf_mod).count("make_access_log"),
        },
        "has_frappe_local_request": hasattr(frappe.local, "request"),
        "so_cookiejar_written": bool(frappe.session and frappe.session.sid
                                     and hasattr(frappe.local, "request")),
    })

    # ---------- 1. the dict the BROWSER gets, per language ----------
    real_lang = get_user_lang("Administrator")
    frappe.local.lang = real_lang
    boot_msgs = get_messages_for_boot()
    rec("browser_translation_dict", {
        "lang": real_lang,
        "source": "frappe/boot.py:234 bootinfo['__messages'] = get_messages_for_boot()",
        "consumed_by": ("request.js:293-294 $.extend(frappe._messages, data.__messages); "
                        "translate.js frappe._ reads frappe._messages[key] || txt"),
        "entry_count": len(boot_msgs),
        "keys_with_cjk": sum(1 for k in boot_msgs
                             if any(0x2E80 <= ord(c) <= 0x9FFF or 0xF900 <= ord(c) <= 0xFAFF
                                    or 0xFF00 <= ord(c) <= 0xFFEF for c in k)),
        "identical_to_get_all_translations": boot_msgs == get_all_translations(real_lang),
    })

    # ---------- 2. templates ----------
    if not frappe.db.exists("Fiscal Year", "2025"):
        fy = frappe.get_doc({"doctype": "Fiscal Year", "year": "2025",
                             "year_start_date": "2025-01-01", "year_end_date": "2025-12-31"})
        fy.insert(ignore_permissions=True)
        rec("created_fiscal_year", {"name": fy.name, "note": "inside txn, rolled back"})

    zh_dict = get_all_translations(real_lang)
    pos_candidates = ["Assets", "Liabilities", "Equity", "Total", "Account"]
    pos_found = [k for k in pos_candidates if k in zh_dict and zh_dict[k] != k]
    seg_pos_0 = pos_found[0] if pos_found else None
    seg_pos_1 = pos_found[1] if len(pos_found) > 1 else seg_pos_0

    cells = [("NEG_statutory_chinese", TPL_NEG, SEG_NEG_0, SEG_NEG_1),
             ("LONG_realistic_panes", TPL_LONG, SEG_LONG_0, SEG_LONG_1)]
    if seg_pos_0:
        cells.append(("POS_translated_key", TPL_POS, seg_pos_0, seg_pos_1))

    built = {}
    for tag, name, s0, s1 in cells:
        d = frappe.get_doc({"doctype": "Financial Report Template", "template_name": name,
                            "report_type": "Balance Sheet", "rows": bs_rows(s0, s1)})
        d.insert(ignore_permissions=True)
        built[tag] = d.name

    def filters_for(tpl):
        return {"company": COMPANY, "report_template": tpl,
                "filter_based_on": "Fiscal Year",
                "from_fiscal_year": "2025", "to_fiscal_year": "2026",
                "periodicity": "Yearly", "selected_view": "Report",
                "include_default_book_entries": 1}

    # ---------- 3. Q1: the print-path TEXT transform, reproduced ----------
    # print_grid.html emits `{{ __(col.name) }}`; col.name for this report is the RAW
    # column.label (query_report.js:1434, is_query_generated_report false). So the print
    # header string is dict.get(label, label) against the boot dict. Reproduced here with
    # the same dict and the same lookup semantics.
    tpl_path = frappe.get_app_path("frappe", "public", "js", "frappe", "views", "reports",
                                   "print_grid.html")
    with open(tpl_path, encoding="utf-8") as f:
        grid_tpl = f.read()
    rec("print_grid_header_line", {
        "path": tpl_path,
        "lines": [ln.strip() for ln in grid_tpl.splitlines() if "col.name" in ln],
    })

    engine_labels = {}
    print_text = {}
    for tag, tpl in built.items():
        cols = FinancialReportEngine().execute(frappe._dict(filters_for(tpl)))[0]
        engine_labels[tag] = [{"fieldname": c.get("fieldname"), "label": c.get("label"),
                               "hidden": c.get("hidden", 0)} for c in cols]
        rows = []
        for c in cols:
            lbl = c.get("label")
            # datatable name: no __() for this report (is_query_generated_report false)
            dt_name = lbl
            # print_grid: __(col.name) against the boot dict (JS frappe._ semantics:
            # frappe._messages[key] || txt -- no .strip(), unlike python's _())
            printed = boot_msgs.get(dt_name, dt_name)
            rows.append({"fieldname": c.get("fieldname"), "engine_label": lbl,
                         "datatable_name_no_underscore": dt_name,
                         "print_grid_after_js_underscore": printed,
                         "print_differs_from_screen": printed != dt_name})
        print_text[tag] = rows
        rec("PRINT_HEADER_TEXT_" + tag, {
            "columns": rows,
            "any_changed_by_print_underscore": any(r["print_differs_from_screen"] for r in rows),
            "changed": [r["fieldname"] for r in rows if r["print_differs_from_screen"]],
        })

    # ---------- 4. Q2: can wkhtmltopdf DRAW these characters? ----------
    rec("font_environment", {
        "fc_list_count": subprocess.run(["sh", "-c", "fc-list | wc -l"],
                                        capture_output=True, text=True).stdout.strip(),
        "fc_list": subprocess.run(["sh", "-c", "fc-list : family | sort -u"],
                                  capture_output=True, text=True).stdout.strip().splitlines(),
        "fc_match_zh_cn": subprocess.run(
            ["sh", "-c", "fc-match -s 'sans-serif:lang=zh-cn' | head -3"],
            capture_output=True, text=True).stdout.strip().splitlines(),
        "wkhtmltopdf_version": subprocess.run(["wkhtmltopdf", "--version"],
                                              capture_output=True, text=True).stdout.strip(),
    })

    # Build a print_grid-shaped table carrying the ACTUAL header strings + an ASCII control
    neg_headers = [c["label"] for c in engine_labels["NEG_statutory_chinese"]
                   if not c["hidden"]]
    long_headers = [c["label"] for c in engine_labels["LONG_realistic_panes"]
                    if not c["hidden"]]
    all_headers = [ASCII_CONTROL_HEADER] + neg_headers + long_headers

    th = "".join("<th>%s</th>" % h for h in all_headers)
    html = ("<html><head><meta charset='utf-8'></head><body>"
            "<h2>%s</h2><table border='1'><thead><tr>%s</tr></thead>"
            "<tbody><tr>%s</tr></tbody></table></body></html>"
            % ("".join(neg_headers), th,
               "".join("<td>%d</td>" % i for i in range(len(all_headers)))))
    hpath = os.path.join(OUT_DIR, "pdf-input.html")
    with open(hpath, "w", encoding="utf-8") as f:
        f.write(html)
    files_written.append(hpath)
    rec("pdf_input_html", {"path": hpath, "headers_embedded": all_headers})

    try:
        pdf_bytes = pdf_mod.get_pdf(html, {"orientation": "Landscape"}, smart_shrinking=True)
        ppath = os.path.join(OUT_DIR, "pdf-render.pdf")
        with open(ppath, "wb") as f:
            f.write(pdf_bytes)
        files_written.append(ppath)

        import pypdf

        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        text = "\n".join((p.extract_text() or "") for p in reader.pages)
        tpath = os.path.join(OUT_DIR, "pdf-extracted-text.txt")
        with open(tpath, "w", encoding="utf-8") as f:
            f.write(text)
        files_written.append(tpath)

        rec("PDF_GLYPH_TEST", {
            "pdf_file": ppath,
            "pdf_bytes": len(pdf_bytes),
            "pages": len(reader.pages),
            "extracted_text_file": tpath,
            "extracted_text_len": len(text),
            "extracted_text_verbatim": text,
            "ascii_control_present": ASCII_CONTROL_HEADER in text,
            "per_header_found": [
                {"header": h, "found_verbatim_in_pdf_text": h in text,
                 "chars": char_dump(h)}
                for h in all_headers],
            "cjk_headers_found": sum(1 for h in neg_headers + long_headers if h in text),
            "cjk_headers_total": len(neg_headers + long_headers),
            "reading": ("ascii_control_present true + cjk_headers_found 0 => the string "
                        "reached the renderer but no font could draw it, i.e. a GLYPH "
                        "failure, not a string transform. Both true => characters survive."),
        })
    except Exception as e:
        rec("PDF_RENDER_ERROR", {"err": str(e), "tb": traceback.format_exc()[-2000:]})

except Exception as e:
    rec("probe_error", {"err": str(e), "tb": traceback.format_exc()[-3000:]})

finally:
    if _orig_enable_prepared_report is not None and report_mod is not None:
        report_mod.enable_prepared_report = _orig_enable_prepared_report

    frappe.db.rollback()

    rec("baseline_after_rollback", baseline())
    rec("templates_exist_after_rollback", {
        n: bool(frappe.db.exists("Financial Report Template", n))
        for n in [TPL_NEG, TPL_LONG, TPL_POS]})
    rec("error_log_rows_now", frappe.get_all(
        "Error Log", fields=["name", "method", "creation"], limit=20))
    jars_after = sorted(glob.glob("/tmp/*.jar"))
    rec("tmp_jars_after", {"jars": jars_after, "new_jars": sorted(set(jars_after) - set(jars_before))})
    rec("files_this_probe_wrote", files_written)
    strays = []
    for d in (frappe.get_site_path("private", "files"), frappe.get_site_path("public", "files")):
        for pat in ("*V31*", "*v31*", "*PROBE*", "*probe*", "*.pdf"):
            strays += glob.glob(os.path.join(d, pat))
    rec("stray_files_in_site_files_dirs", sorted(set(strays)))

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)
    print("\nWROTE " + OUT, flush=True)
