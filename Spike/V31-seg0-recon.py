# V-31 seg0 -- RECON, STRICTLY READ-ONLY. No inserts. Nothing to roll back.
#
# Purpose: map the translation landscape BEFORE testing the render layer, and settle
# the site-safety question about the frappe.desk.query_report.run path.
#
# Questions:
#   1. What lang does `_()` actually resolve to for this site / Administrator?
#   2. How big is the merged translation dict, and do any of its KEYS contain CJK?
#      This matters enormously: `_()` looks up all_translations.get(msg) where msg is
#      the label itself. A dict whose msgids are all English can never collide with a
#      Chinese label. A dict carrying CJK msgids CAN.
#   3. Are our candidate statutory labels present as keys?
#   4. Does `Custom Financial Statement` arm the prepared-report threading.Timer?
#      report.py:192 -- if not self.prepared_report and not
#      self.disable_prepared_report_automation: threading.Timer(15s,
#      enable_prepared_report) -- and enable_prepared_report does frappe.db.set_value
#      + frappe.db.commit() ON A SEPARATE CONNECTION. Our rollback cannot undo that.
#      Governs whether we may call query_report.run at all.
#   5. Count Translation doctype rows -- a site admin can give those an arbitrary
#      (possibly Chinese) source_text, which is the live collision vector.
#
# Chinese is written ONLY as \uXXXX escapes; this source stays ASCII-only because the
# Windows host parses shell-fed Chinese as GBK.
#
# Run:
#   docker exec -i -e PYTHONUTF8=1 -e PYTHONIOENCODING=utf-8 \
#     -w /workspace/frappe-bench/sites erx001-frappe-1 \
#     /workspace/frappe-bench/env/bin/python /workspace/Spike/V31-seg0-recon.py

import json
import os
import traceback

import frappe

SITE = "erx.localhost"
OUT_DIR = "/workspace/Spike/V31-out"
OUT = os.path.join(OUT_DIR, "seg0-recon.json")

L_OPENING = "\u5E74\u521D\u4F59\u989D"          # nian chu yu e   (opening balance)
L_CLOSING = "\u671F\u672B\u4F59\u989D"          # qi mo yu e      (closing balance)
L_ASSET = "\u8D44\u4EA7"                        # zi chan         (assets)
L_LIAB_EQ = "\u8D1F\u503A\u548C\u6240\u6709\u8005\u6743\u76CA"  # liabilities+equity
COMPANY = "\u534E\u4E1C\u5F39\u7C27"

result = {"probe": "V-31 seg0 recon: translation landscape + prepared-report timer safety"}


def rec(k, v):
    result[k] = v
    print("[" + k + "] " + json.dumps(v, ensure_ascii=False, default=str)[:2400], flush=True)


def has_cjk(s):
    for ch in str(s):
        o = ord(ch)
        if 0x2E80 <= o <= 0x9FFF or 0xF900 <= o <= 0xFAFF or 0xFF00 <= o <= 0xFFEF:
            return True
    return False


frappe.init(site=SITE)
frappe.connect()
frappe.set_user("Administrator")
os.makedirs(OUT_DIR, exist_ok=True)

try:
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
        }

    rec("baseline_before", baseline())

    # ---------- 1. which lang does _() use ----------
    from frappe.translate import get_all_translations, get_user_lang, get_user_translations

    lang_live = getattr(frappe.local, "lang", None) or get_user_lang("Administrator")
    rec("lang_resolution", {
        "frappe.local.lang": getattr(frappe.local, "lang", None),
        "get_user_lang(Administrator)": get_user_lang("Administrator"),
        "User.language": frappe.db.get_value("User", "Administrator", "language"),
        "SystemSettings.language": frappe.get_system_settings("language"),
        "lang_used_below": lang_live,
        "note": "_() in frappe/utils/translations.py uses frappe.local.lang when no lang arg",
    })

    # ---------- 2. the merged dict, per candidate lang ----------
    for lang in sorted({"zh", "zh-CN", "en", lang_live}):
        try:
            d = get_all_translations(lang)
        except Exception as e:
            rec("translations_" + lang + "_ERROR", str(e))
            continue
        cjk_keys = [k for k in d if has_cjk(k)]
        rec("translations_" + lang + "_summary", {
            "entry_count": len(d),
            "keys_containing_cjk": len(cjk_keys),
            "sample_cjk_keys": sorted(cjk_keys)[:40],
            "sample_keys": list(d)[:8],
        })

    # ---------- 3. are the V-29 labels themselves keys? ----------
    live = get_all_translations(lang_live)
    probe_labels = [
        L_OPENING, L_CLOSING, L_ASSET, L_LIAB_EQ,
        L_OPENING + " - 2025", L_OPENING + " - 2026",
        L_CLOSING + " - 2025", L_CLOSING + " - 2026",
        L_ASSET + " - 2026", L_LIAB_EQ + " - 2026",
        "2025", "2026",
        "Account Name", "Account Number", "Currency", "Total",
        "Assets", "Liabilities", "Equity", "Account (Segment 1)",
    ]
    hits = {}
    for lbl in probe_labels:
        hits[lbl] = {
            "is_key": lbl in live,
            "value_if_key": live.get(lbl),
            "stripped_is_key": lbl.strip() in live,
        }
    rec("candidate_label_translation_hits", {"lang": lang_live, "hits": hits})

    # ---------- 4. THE SAFETY QUESTION: prepared-report timer ----------
    rep = frappe.get_doc("Report", "Custom Financial Statement")
    rec("report_doc_flags", {
        "name": rep.name,
        "report_type": rep.report_type,
        "is_standard": rep.is_standard,
        "prepared_report": rep.prepared_report,
        "disable_prepared_report_automation": rep.get("disable_prepared_report_automation"),
        "add_translate_data": rep.get("add_translate_data"),
        "query": rep.get("query"),
        "snapshot_report": rep.get("snapshot_report"),
        "add_total_row": rep.get("add_total_row"),
        "timeout": rep.get("timeout"),
        "letterhead": rep.get("letterhead"),
    })
    rec("prepared_report_timer_would_arm", {
        "guard_source": "if not self.prepared_report and not self.disable_prepared_report_automation",
        "not_prepared_report": (not rep.prepared_report),
        "not_disable_automation": (not rep.get("disable_prepared_report_automation")),
        "timer_arms": bool((not rep.prepared_report)
                           and (not rep.get("disable_prepared_report_automation"))),
        "consequence_if_arms": ("threading.Timer(15s) -> enable_prepared_report() -> "
                                "frappe.init/connect on a SEPARATE connection -> "
                                "db.set_value('Report',...,'prepared_report',1) -> db.commit(). "
                                "frappe.db.rollback() in THIS process cannot undo that."),
        "mitigation_planned": ("patch report_mod.enable_prepared_report to a no-op BEFORE "
                               "calling run(); the Timer resolves that global name at "
                               "Timer-construction time, so the patch neutralizes it"),
    })

    import inspect

    from frappe.core.doctype.report import report as report_mod

    rec("execute_script_report_source", inspect.getsource(report_mod.Report.execute_script_report))
    rec("enable_prepared_report_source", inspect.getsource(report_mod.enable_prepared_report))

    # commit / enqueue census over every module on the render path
    import frappe.desk.query_report as qr_mod
    import frappe.desk.utils as du_mod
    import frappe.utils.xlsxutils as xu_mod
    from frappe.utils import translations as tr_mod

    census = {}
    for tag, mod in [("desk.query_report", qr_mod), ("utils.xlsxutils", xu_mod),
                     ("desk.utils", du_mod), ("utils.translations", tr_mod),
                     ("core.doctype.report.report", report_mod)]:
        src = inspect.getsource(mod)
        census[tag] = {
            "db.commit": src.count("db.commit"),
            "frappe.enqueue": src.count("frappe.enqueue"),
            "enqueue_doc": src.count("enqueue_doc"),
            "threading.Timer": src.count("threading.Timer"),
            "save_file": src.count("save_file"),
            "log_error": src.count("log_error"),
        }
    rec("render_path_commit_enqueue_census", census)

    # the _() site on column labels, quoted from live source
    qr_src = inspect.getsource(qr_mod)
    rec("build_xlsx_data_label_line", [ln.strip() for ln in qr_src.splitlines()
                                       if "column_data.append" in ln])
    rec("build_xlsx_data_source", inspect.getsource(qr_mod.build_xlsx_data))
    rec("get_column_as_dict_source", inspect.getsource(qr_mod.get_column_as_dict))
    rec("translate_report_data_source", inspect.getsource(qr_mod.translate_report_data))
    rec("underscore_source", inspect.getsource(tr_mod._))

    # ---------- 5. user translations (arbitrary source_text risk) ----------
    rec("user_translations_live", {
        "Translation_row_count": frappe.db.count("Translation"),
        "rows": frappe.get_all("Translation",
                               fields=["name", "language", "source_text", "translated_text",
                                       "context"],
                               limit=50),
    })
    try:
        ut = get_user_translations(lang_live)
        rec("get_user_translations_live", {
            "lang": lang_live,
            "count": len(ut),
            "cjk_keys": [k for k in ut if has_cjk(k)][:30],
        })
    except Exception as e:
        rec("get_user_translations_ERROR", str(e))

    # ---------- 6. print path: the template that renders PDF/print headers ----------
    tpl_path = frappe.get_app_path(
        "frappe", "public", "js", "frappe", "views", "reports", "print_grid.html")
    with open(tpl_path, encoding="utf-8") as f:
        tpl = f.read()
    rec("print_grid_template", {
        "path": tpl_path,
        "header_cell_lines": [ln.strip() for ln in tpl.splitlines()
                              if "col.name" in ln or "__(title)" in ln],
        "applies_underscore_to_header": "__(col.name)" in tpl,
    })

    rec("baseline_after", baseline())

except Exception as e:
    rec("probe_error", {"err": str(e), "tb": traceback.format_exc()[-2500:]})

finally:
    frappe.db.rollback()
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)
    print("\nWROTE " + OUT, flush=True)
