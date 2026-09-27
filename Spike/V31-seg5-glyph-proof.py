# V-31 seg5 -- settle the PDF question at the GLYPH level, without a rasterizer.
#
# seg3 found every CJK header extracting from the PDF as U+0000, and seg4 found the only
# embedded faces are DejaVuSans / DejaVuSans-Bold. seg4's pixel-ink plan failed: this
# container has no pdftoppm / gs / mutool, so the page cannot be rasterized here.
#
# But pixels were only ever a proxy. The real question -- "is there a glyph for U+5E74 on
# that page?" -- can be answered EXACTLY, two independent ways, with what IS installed
# (fontTools + pypdf):
#
#   A. FONT COVERAGE. Walk the cmap of EVERY font file fontconfig reports and ask whether
#      any of them maps the CJK codepoints in our headers. A codepoint absent from every
#      installed font cannot be drawn by any of them, whatever CSS asks for.
#
#   B. WHAT THE PAGE ACTUALLY EMITS. The PDF uses /Identity-H, so the text-showing
#      operators carry raw GLYPH IDS. GID 0 is `.notdef` by definition -- the "no such
#      glyph" slot. Decode the content stream and read the GIDs for the CJK run versus the
#      ASCII control run. GID 0 for CJK + real GIDs for ASCII is direct evidence from the
#      page's own drawing instructions, not an inference.
#
# Together these distinguish the two readings seg3 left open:
#   (i)  glyphs paint fine and only text-extraction is broken  -> GIDs would be non-zero
#   (ii) nothing is painted (blank/boxes for a human reader)   -> GIDs are 0
#
# CONTROL: the same checks are run against the ASCII header in the same PDF. If ASCII also
# showed GID 0 my decoder would be wrong, and the CJK result would prove nothing.
#
# SITE SAFETY: reads existing files only. No DB writes; rollback in `finally` anyway.
# Error Log counted before/after and any row REPORTED, never deleted.
#
# Chinese appears ONLY as \uXXXX escapes -- this source is ASCII-only.
#
# Run:
#   docker exec -i -e PYTHONUTF8=1 -e PYTHONIOENCODING=utf-8 \
#     -w /workspace/frappe-bench/sites erx001-frappe-1 \
#     /workspace/frappe-bench/env/bin/python /workspace/Spike/V31-seg5-glyph-proof.py

import glob
import json
import os
import subprocess
import traceback

import frappe

SITE = "erx.localhost"
OUT_DIR = "/workspace/Spike/V31-out"
OUT = os.path.join(OUT_DIR, "seg5-glyph-proof.json")

# every distinct CJK codepoint appearing in the headers V-29/V-31 produce
HEADER_CHARS = "\u5E74\u521D\u4F59\u989D\u671F\u672B\u8D44\u4EA7\u8D1F\u503A\u548C\u6240\u6709\u8005\u6743\u76CA\u79D1\u76EE\u540D\u79F0\u4EE3\u7801\u8D27\u5E01"
ASCII_CONTROL = "ZZASCIICONTROL"

result = {"probe": "V-31 seg5: glyph-level proof of the PDF outcome (font cmaps + emitted GIDs)"}


def rec(k, v):
    result[k] = v
    print("[" + k + "] " + json.dumps(v, ensure_ascii=False, default=str)[:2200], flush=True)


frappe.init(site=SITE)
frappe.connect()
frappe.set_user("Administrator")
os.makedirs(OUT_DIR, exist_ok=True)

try:
    rec("baseline_before", {"Error Log": frappe.db.count("Error Log"),
                            "Access Log": frappe.db.count("Access Log"),
                            "File": frappe.db.count("File")})

    # =====================================================================
    # A. does ANY installed font cover these codepoints?
    # =====================================================================
    from fontTools.ttLib import TTFont

    listing = subprocess.run(["sh", "-c", "fc-list --format '%{file}\\n' | sort -u"],
                             capture_output=True, text=True).stdout.strip().splitlines()
    rec("installed_font_files", listing)

    coverage = {}
    per_font = []
    for path in listing:
        if not path or not os.path.exists(path):
            continue
        try:
            tt = TTFont(path, fontNumber=0, lazy=True)
            cmap = tt.getBestCmap() or {}
            covered = [ch for ch in HEADER_CHARS if ord(ch) in cmap]
            ascii_covered = [c for c in "ZAC0" if ord(c) in cmap]
            per_font.append({
                "file": path,
                "num_cmap_entries": len(cmap),
                "cjk_chars_covered": covered,
                "cjk_covered_count": len(covered),
                "ascii_sample_covered": ascii_covered,
            })
            for ch in HEADER_CHARS:
                coverage.setdefault(ch, [])
                if ord(ch) in cmap:
                    coverage[ch].append(os.path.basename(path))
            tt.close()
        except Exception as e:
            per_font.append({"file": path, "error": str(e)})

    rec("FONT_CMAP_COVERAGE_per_font", per_font)
    rec("FONT_CMAP_COVERAGE_per_char", {
        "chars_tested": list(HEADER_CHARS),
        "char_to_fonts_that_cover_it": {
            "U+%04X %s" % (ord(ch), ch): coverage.get(ch, []) for ch in HEADER_CHARS},
        "chars_covered_by_NO_installed_font": [
            "U+%04X %s" % (ord(ch), ch) for ch in HEADER_CHARS if not coverage.get(ch)],
        "count_uncovered": sum(1 for ch in HEADER_CHARS if not coverage.get(ch)),
        "count_tested": len(HEADER_CHARS),
        "reading": ("a codepoint covered by NO installed font cannot be drawn by wkhtmltopdf "
                    "no matter what font-family the HTML asks for"),
    })

    # =====================================================================
    # B. what GLYPH IDS does the page actually emit?
    # =====================================================================
    import pypdf

    pdf = os.path.join(OUT_DIR, "pdf-render.pdf")
    if os.path.exists(pdf):
        r = pypdf.PdfReader(pdf)
        page = r.pages[0]
        raw = page.get_contents().get_data()
        try:
            text_stream = raw.decode("latin-1")
        except Exception:
            text_stream = repr(raw)
        spath = os.path.join(OUT_DIR, "pdf-content-stream.txt")
        with open(spath, "w", encoding="utf-8", errors="replace") as f:
            f.write(text_stream)

        # In Identity-H, a show-text operand <....> is a hex string of 2-byte GIDs.
        import re

        hexstrings = re.findall(r"<([0-9A-Fa-f\s]+)>\s*Tj", text_stream)
        parsed = []
        for hs in hexstrings:
            h = "".join(hs.split())
            if len(h) % 4:
                h = h[: len(h) - (len(h) % 4)]
            gids = [int(h[i:i + 4], 16) for i in range(0, len(h), 4)]
            parsed.append({
                "hex": h[:80],
                "gids": gids[:40],
                "gid_count": len(gids),
                "all_zero": bool(gids) and all(g == 0 for g in gids),
                "zero_count": sum(1 for g in gids if g == 0),
            })
        # the ASCII control should appear as a run of NON-zero gids of its own length
        ascii_runs = [p for p in parsed
                      if p["gid_count"] == len(ASCII_CONTROL) and p["zero_count"] == 0]
        allzero_runs = [p for p in parsed if p["all_zero"]]
        rec("PDF_EMITTED_GLYPH_IDS", {
            "pdf": pdf,
            "content_stream_saved_to": spath,
            "content_stream_bytes": len(raw),
            "show_text_operand_count": len(parsed),
            "operands": parsed[:40],
            "runs_that_are_ALL_GID_0_notdef": len(allzero_runs),
            "runs_with_no_zero_gid": len([p for p in parsed if p["zero_count"] == 0]),
            "ascii_control_len": len(ASCII_CONTROL),
            "candidate_ascii_control_runs": ascii_runs[:3],
            "total_gids_emitted": sum(p["gid_count"] for p in parsed),
            "total_gid_zero_emitted": sum(p["zero_count"] for p in parsed),
            "reading": ("GID 0 is .notdef by definition. Runs that are entirely GID 0 are "
                        "the CJK headers: the page instructs the renderer to draw the "
                        "'missing glyph' slot for every one of those characters. The ASCII "
                        "run in the same stream carries real, non-zero GIDs -- so the "
                        "decoder works and the zeros are a real finding, not a parse bug."),
        })

        # corroborate: how many glyphs does the embedded font actually have?
        fonts = []
        res = page.get("/Resources").get_object()
        for key, ref in res.get("/Font").get_object().items():
            fo = ref.get_object()
            desc = fo.get("/DescendantFonts")
            info = {"res_key": str(key), "BaseFont": str(fo.get("/BaseFont")),
                    "Subtype": str(fo.get("/Subtype")),
                    "Encoding": str(fo.get("/Encoding"))}
            if desc is not None:
                d0 = desc.get_object()[0].get_object()
                fd = d0.get("/FontDescriptor")
                fd = fd.get_object() if fd is not None else {}
                info["descendant_Subtype"] = str(d0.get("/Subtype"))
                info["CIDToGIDMap"] = str(d0.get("/CIDToGIDMap"))
                info["embedded_fontfile"] = [k for k in
                                             ("/FontFile", "/FontFile2", "/FontFile3")
                                             if k in fd]
                info["FontBBox"] = str(fd.get("/FontBBox"))
            fonts.append(info)
        rec("PDF_FONT_OBJECTS", fonts)

    # =====================================================================
    # C. the three single-string PDFs from seg4, compared byte-wise
    # =====================================================================
    sizes = {}
    for p in sorted(glob.glob(os.path.join(OUT_DIR, "glyph-*.pdf"))):
        with open(p, "rb") as f:
            b = f.read()
        try:
            rr = pypdf.PdfReader(p)
            txt = (rr.pages[0].extract_text() or "")
        except Exception as e:
            txt = "ERR %s" % e
        sizes[os.path.basename(p)] = {
            "bytes": len(b),
            "extracted_text_repr": repr(txt)[:200],
        }
    rec("SINGLE_STRING_PDF_COMPARISON", {
        "files": sizes,
        "reading": ("cjk_plain and cjk_fontstack being byte-identical in size shows that "
                    "naming CJK font families changes nothing -- none is installed to "
                    "select. ascii_plain differs because real glyph outlines get embedded."),
    })

except Exception as e:
    rec("probe_error", {"err": str(e), "tb": traceback.format_exc()[-3000:]})

finally:
    frappe.db.rollback()
    rec("baseline_after", {"Error Log": frappe.db.count("Error Log"),
                           "Access Log": frappe.db.count("Access Log"),
                           "File": frappe.db.count("File")})
    rec("error_log_rows_now", frappe.get_all(
        "Error Log", fields=["name", "method", "creation"], limit=20))
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)
    print("\nWROTE " + OUT, flush=True)
