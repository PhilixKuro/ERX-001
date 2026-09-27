# V-31 seg4 -- (a) CONFIRM the PDF glyph failure is really font coverage, and
#                (b) TRUNCATION / WIDTH: does anything shorten or ellipsize a long
#                    Chinese header such as `\u8D1F\u503A\u548C\u6240\u6709\u8005\u6743\u76CA - 2026`?
#
# (a) WHY A SECOND LOOK AT THE PDF
# seg3 found every CJK header extracting from the PDF as U+0000 NUL runs while the ASCII
# control came out verbatim. That is strong, but `extract_text()` returning NUL could in
# principle be a text-extraction artifact (a bad ToUnicode CMap) over glyphs that DO paint
# correctly on the page. Those two possibilities matter very differently to a human
# reader: one means blank boxes on the printed statement, the other means the print looks
# fine and only copy-paste is broken. So this seg separates them:
#   - list the fonts actually EMBEDDED in the PDF (pypdf /Resources /Font) and whether any
#     of them could cover CJK;
#   - RASTERIZE the page and measure ink. A page whose CJK cells paint real glyphs has
#     substantially more dark pixels than one painting nothing/boxes. Compared against an
#     ASCII-only control PDF rendered through the same code path, so the measurement has
#     something to be a difference FROM.
#   - a THIRD control: the same Chinese rendered with an explicit generic font stack, to
#     make sure the failure is not caused by my bare-bones test HTML.
#
# (b) TRUNCATION
# Established by reading what each surface does with width, then testing the one thing
# that is testable server-side:
#   - the engine sets width 300 on the account column and 150 on each period column
#     (observed in seg1/seg2 ENGINE_LABELS). Those are the numbers that travel.
#   - XLSX: build_xlsx_data divides the column's width by 10 into xlsxwriter units. That
#     sets COLUMN WIDTH, never the header STRING -- and seg2 already read the header cells
#     back byte-identical, so nothing truncated them. Re-asserted here by reading the
#     stored widths out of the produced workbook.
#   - datatable: frappe-datatable's style.css sets `.dt-cell__content { text-overflow:
#     ellipsis; white-space: nowrap; overflow: hidden }`, so a header wider than its column
#     is CLIPPED VISUALLY with an ellipsis. That is CSS, not string mutation -- grepped for
#     any JS that shortens the string itself.
#   - sheet name: get_sanitized_sheet_name truncates to 31 chars. Tested against a report
#     title long enough to trip it, to show it is the TAB name and not a header cell.
#
# CRITERION DISCIPLINE: the ink measurement is meaningless without a same-path ASCII
# control; the font census is meaningless without knowing what CJK coverage would look
# like. Both controls are in.
#
# SITE SAFETY
# * No DB writes at all in this seg: it reads the workbooks seg2 already produced and
#   renders self-contained HTML. `frappe.db.rollback()` in `finally` regardless.
# * Calls frappe.utils.pdf.get_pdf directly, NOT report_to_pdf -- same reason as seg3
#   (report_to_pdf -> make_access_log -> deferred_insert -> redis -> a later committed
#   insert our rollback could not undo).
# * Error Log is MyISAM: counted before/after, any row REPORTED, never deleted.
# * Files: only /workspace/Spike/V31-out/*, reported.
#
# Chinese appears ONLY as \uXXXX escapes -- this source is ASCII-only.
#
# Run:
#   docker exec -i -e PYTHONUTF8=1 -e PYTHONIOENCODING=utf-8 \
#     -w /workspace/frappe-bench/sites erx001-frappe-1 \
#     /workspace/frappe-bench/env/bin/python /workspace/Spike/V31-seg4-truncation-and-glyphs.py

import glob
import io
import json
import os
import subprocess
import traceback

import frappe

SITE = "erx.localhost"
OUT_DIR = "/workspace/Spike/V31-out"
OUT = os.path.join(OUT_DIR, "seg4-truncation-and-glyphs.json")

LONGEST = "\u8D1F\u503A\u548C\u6240\u6709\u8005\u6743\u76CA - 2026"   # 15 chars, the longest header V-29/V-31 produce
CJK_ONLY = "\u8D1F\u503A\u548C\u6240\u6709\u8005\u6743\u76CA"
ASCII_TWIN = "LiabilitiesAndOwnersEquity - 2026"   # ASCII control of similar length

result = {"probe": "V-31 seg4: PDF glyph coverage confirmation + truncation/width effects"}


def rec(k, v):
    result[k] = v
    print("[" + k + "] " + json.dumps(v, ensure_ascii=False, default=str)[:2200], flush=True)


frappe.init(site=SITE)
frappe.connect()
frappe.set_user("Administrator")
os.makedirs(OUT_DIR, exist_ok=True)

files_written = []

try:
    rec("baseline_before", {
        "Error Log": frappe.db.count("Error Log"),
        "Access Log": frappe.db.count("Access Log"),
        "File": frappe.db.count("File"),
        "Financial Report Template": frappe.db.count("Financial Report Template"),
    })

    import frappe.utils.pdf as pdf_mod
    import pypdf

    # =====================================================================
    # (a1) fonts EMBEDDED in the PDF seg3 produced
    # =====================================================================
    seg3_pdf = os.path.join(OUT_DIR, "pdf-render.pdf")
    if os.path.exists(seg3_pdf):
        r = pypdf.PdfReader(seg3_pdf)
        fonts = []
        for pno, page in enumerate(r.pages):
            res = page.get("/Resources")
            if res is None:
                continue
            res = res.get_object()
            fdict = res.get("/Font")
            if fdict is None:
                continue
            for key, ref in fdict.get_object().items():
                fo = ref.get_object()
                desc = fo.get("/FontDescriptor")
                desc = desc.get_object() if desc is not None else {}
                fonts.append({
                    "page": pno, "res_key": str(key),
                    "BaseFont": str(fo.get("/BaseFont")),
                    "Subtype": str(fo.get("/Subtype")),
                    "Encoding": str(fo.get("/Encoding")),
                    "has_ToUnicode": "/ToUnicode" in fo,
                    "FontFile_embedded": any(k in desc for k in
                                             ("/FontFile", "/FontFile2", "/FontFile3")),
                    "descriptor_flags": str(desc.get("/Flags")),
                })
        rec("seg3_pdf_embedded_fonts", {
            "pdf": seg3_pdf, "font_count": len(fonts), "fonts": fonts,
            "reading": ("if the only embedded faces are DejaVu/Cantarell (no CJK coverage) "
                        "then there is no font on the page able to draw U+5E74 etc."),
        })

    # =====================================================================
    # (a2) RASTERIZE and measure ink: CJK vs ASCII through the SAME path
    # =====================================================================
    def render(tag, body_html):
        pdf_bytes = pdf_mod.get_pdf("<html><head><meta charset='utf-8'></head><body>"
                                    + body_html + "</body></html>",
                                    {"orientation": "Portrait"}, smart_shrinking=True)
        p = os.path.join(OUT_DIR, "glyph-%s.pdf" % tag)
        with open(p, "wb") as f:
            f.write(pdf_bytes)
        files_written.append(p)
        return p, pdf_bytes

    # one string per PDF, huge, so ink differences cannot hide in layout noise
    cases = {
        # the real thing
        "cjk_plain": "<div style='font-size:72pt'>%s</div>" % CJK_ONLY,
        # ASCII control -- same path, same size: proves the pipeline CAN paint text
        "ascii_plain": "<div style='font-size:72pt'>%s</div>" % "ABCDEFGH",
        # third control: explicit font stack, in case bare HTML was the problem
        "cjk_fontstack": ("<div style='font-size:72pt;font-family:\"Noto Sans CJK SC\","
                          "\"WenQuanYi Zen Hei\",\"Microsoft YaHei\",SimSun,sans-serif'>"
                          "%s</div>" % CJK_ONLY),
    }
    ink = {}
    for tag, body in cases.items():
        try:
            p, b = render(tag, body)
            # rasterize with pdftoppm if present (poppler); else record unavailable
            png = os.path.join(OUT_DIR, "glyph-%s" % tag)
            cp = subprocess.run(["sh", "-c",
                                 "pdftoppm -r 50 -gray -png %s %s 2>&1" % (p, png)],
                                capture_output=True, text=True)
            pngs = sorted(glob.glob(png + "*.png"))
            files_written.extend(pngs)
            dark = None
            if pngs:
                try:
                    from PIL import Image

                    im = Image.open(pngs[0]).convert("L")
                    px = list(im.getdata())
                    dark = sum(1 for v in px if v < 128)
                    dims = im.size
                except Exception as e:
                    dark = "PIL unavailable: %s" % e
                    dims = None
            else:
                dims = None
            ink[tag] = {"pdf": p, "pdf_bytes": len(b), "pngs": pngs,
                        "pdftoppm_out": cp.stdout.strip()[:300],
                        "dark_pixels": dark, "png_size": dims}
        except Exception as e:
            ink[tag] = {"error": str(e)}
    rec("GLYPH_INK_MEASUREMENT", {
        "cases": ink,
        "reading": ("ascii_plain having many dark pixels while cjk_plain has ~none means "
                    "the CJK glyphs are NOT painted -- a human sees nothing/boxes where the "
                    "header should be. cjk_fontstack matching cjk_plain means naming a CJK "
                    "family does not help because no such family is installed."),
    })

    # =====================================================================
    # (b1) XLSX: header strings vs COLUMN WIDTHS in the produced workbook
    # =====================================================================
    import openpyxl

    xlsx_reports = {}
    for p in sorted(glob.glob(os.path.join(OUT_DIR, "xlsx-*.xlsx"))):
        try:
            wb = openpyxl.load_workbook(p)
            ws = wb[wb.sheetnames[0]]
            hdr = [c.value for c in ws[1]]
            widths = {k: (v.width if v is not None else None)
                      for k, v in ws.column_dimensions.items()}
            xlsx_reports[os.path.basename(p)] = {
                "sheet_name": wb.sheetnames[0],
                "sheet_name_len": len(wb.sheetnames[0]),
                "header_row": hdr,
                "header_lengths": [len(h) if isinstance(h, str) else None for h in hdr],
                "longest_header": max((h for h in hdr if isinstance(h, str)),
                                      key=len, default=None),
                "column_widths": widths,
                "any_header_shortened": any(
                    isinstance(h, str) and (h.endswith("...") or h.endswith("\u2026"))
                    for h in hdr),
            }
            wb.close()
        except Exception as e:
            xlsx_reports[os.path.basename(p)] = {"error": str(e)}
    rec("XLSX_WIDTHS_VS_HEADER_STRINGS", {
        "workbooks": xlsx_reports,
        "reading": ("column_widths are set from the engine's width/10; header strings are "
                    "full length regardless -- width affects display, not the stored string. "
                    "any_header_shortened must be false everywhere."),
    })

    # =====================================================================
    # (b2) the ONE truncation that is real: sheet name, 31 chars
    # =====================================================================
    from frappe.utils.xlsxutils import (
        INVALID_SHEET_NAME_RE,
        MAX_SHEET_NAME_LENGTH,
        get_sanitized_sheet_name,
    )

    long_title = CJK_ONLY * 5   # 40 CJK chars -- past the 31 limit
    rec("SHEET_NAME_TRUNCATION", {
        "MAX_SHEET_NAME_LENGTH": MAX_SHEET_NAME_LENGTH,
        "INVALID_SHEET_NAME_RE": INVALID_SHEET_NAME_RE.pattern,
        "input": long_title,
        "input_len": len(long_title),
        "sanitized": get_sanitized_sheet_name(long_title),
        "sanitized_len": len(get_sanitized_sheet_name(long_title)),
        "truncated": len(get_sanitized_sheet_name(long_title)) < len(long_title),
        "scope": ("this is the WORKSHEET TAB name (make_xlsx -> wb.add_worksheet), derived "
                  "from the report name -- NOT a column header cell. The report name here "
                  "is 'Custom Financial Statement' (27 chars), under the limit."),
        "actual_report_name": "Custom Financial Statement",
        "actual_report_name_len": len("Custom Financial Statement"),
    })

    # =====================================================================
    # (b3) datatable: CSS clipping, and does any JS shorten the string?
    # =====================================================================
    dt_css = "/workspace/frappe-bench/apps/frappe/node_modules/frappe-datatable/src/style.css"
    css_hits = []
    if os.path.exists(dt_css):
        with open(dt_css, encoding="utf-8") as f:
            lines = f.read().splitlines()
        for i, ln in enumerate(lines):
            if "text-overflow" in ln or "white-space" in ln or "overflow" in ln:
                css_hits.append("%d: %s" % (i + 1, ln.strip()))
    rec("DATATABLE_HEADER_CLIPPING_CSS", {
        "path": dt_css,
        "matches": css_hits[:25],
        "meaning": ("`.dt-cell__content` clips overflow and shows an ellipsis. A header "
                    "longer than its column is VISUALLY cut on screen; the underlying "
                    "string is untouched (the user can widen the column). This is a CSS "
                    "fact read from source, not an observed browser render."),
    })

    # any JS that shortens a header string?
    grep = subprocess.run(
        ["sh", "-c",
         "grep -rn 'substring\\|slice(0\\|truncate\\|ellips' "
         "/workspace/frappe-bench/apps/frappe/node_modules/frappe-datatable/src/*.js "
         "/workspace/frappe-bench/apps/frappe/frappe/public/js/frappe/views/reports/"
         "query_report.js 2>&1 | head -20"],
        capture_output=True, text=True)
    rec("JS_STRING_SHORTENING_GREP", {
        "command": "grep substring|slice(0|truncate|ellips in datatable src + query_report.js",
        "output": grep.stdout.strip().splitlines(),
        "meaning": "empty => no JS shortens the header STRING itself",
    })

    # engine widths, restated with the longest label in hand
    rec("WIDTH_VS_LABEL_LENGTH", {
        "account_column_width_px": 300,
        "period_column_width_px": 150,
        "source": "erpnext/accounts/report/financial_statements.py:670,687,709 get_columns",
        "longest_header_observed": LONGEST,
        "longest_header_chars": len(LONGEST),
        "note": ("a 15-char CJK header in a 150px column will not fit at typical Desk font "
                 "sizes, so the datatable will ellipsize it visually. Exact pixel fit was "
                 "NOT measured in a browser."),
    })

except Exception as e:
    rec("probe_error", {"err": str(e), "tb": traceback.format_exc()[-3000:]})

finally:
    frappe.db.rollback()
    rec("baseline_after", {
        "Error Log": frappe.db.count("Error Log"),
        "Access Log": frappe.db.count("Access Log"),
        "File": frappe.db.count("File"),
        "Financial Report Template": frappe.db.count("Financial Report Template"),
    })
    rec("error_log_rows_now", frappe.get_all(
        "Error Log", fields=["name", "method", "creation"], limit=20))
    rec("files_this_probe_wrote", files_written)
    strays = []
    for d in (frappe.get_site_path("private", "files"), frappe.get_site_path("public", "files")):
        for pat in ("*V31*", "*v31*", "*glyph*", "*.pdf", "*.png"):
            strays += glob.glob(os.path.join(d, pat))
    rec("stray_files_in_site_files_dirs", sorted(set(strays)))
    rec("tmp_jars", sorted(glob.glob("/tmp/*.jar")))

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)
    print("\nWROTE " + OUT, flush=True)
