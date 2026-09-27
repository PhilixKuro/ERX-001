# REV AUDIT part C: can ANYTHING inject `accumulated_values` onto the FRT report
# path, and does the template layer reach ANY column name?
#
# Redo of the section that died in part A on a wrong tabReport column name
# (`filters` is a child TABLE on Report, not a column), plus a much wider sweep
# than the original probe's 3-file grep: directory listings, synonym scan over
# every .py/.js/.json in every installed app, the Report doc AS STORED IN THE DB,
# Report Filter child rows, Custom Report json, Property Setter / Client Script /
# Server Script, and hooks.py of every installed app.
#
# READ-ONLY. No writes. No frappe.db.commit(), no frappe.enqueue.
#
# Run (cwd MUST be .../sites):
#   docker exec -i -w /workspace/frappe-bench/sites erx001-frappe-1 \
#     /workspace/frappe-bench/env/bin/python /workspace/Spike/Rev-P1S4R2-c-inject.py

import json
import os

import frappe

SITE = "erx.localhost"
OUT = "/workspace/Spike/Rev-out/c-inject.json"

result = {"probe": "REV audit part C: accumulated_values injection surface + column-name surface"}


def rec(k, v):
    result[k] = v
    print("[" + k + "] " + json.dumps(v, ensure_ascii=True, default=str)[:1600], flush=True)


frappe.init(site=SITE)
frappe.connect()
frappe.set_user("Administrator")

try:
    # ---------- 1. the Report doc as stored in the DB ----------
    rec("report_row", frappe.db.sql("""
        select name, report_type, is_standard, ref_doctype, module, disabled,
               ifnull(json,'') as json, ifnull(query,'') as query,
               ifnull(javascript,'') as javascript, ifnull(report_script,'') as report_script,
               prepared_report, reference_report
        from tabReport where name = 'Custom Financial Statement'
    """, as_dict=True))
    # schema-agnostic: read the child tables through the ORM, not guessed columns
    for child_dt in ("Report Filter", "Report Column"):
        try:
            rows = frappe.get_all(
                child_dt,
                filters={"parent": "Custom Financial Statement"},
                fields=["*"], order_by="idx")
            rec("child_rows_" + child_dt.replace(" ", "_"), [dict(r) for r in rows])
        except Exception as e:
            rec("child_rows_error_" + child_dt.replace(" ", "_"), str(e))
        # and the whole table, to see if ANY report anywhere declares the switch
        try:
            allrows = frappe.get_all(child_dt, fields=["*"])
            rec("all_" + child_dt.replace(" ", "_") + "_rows_total", len(allrows))
            rec("all_" + child_dt.replace(" ", "_") + "_mentioning_accum",
                [dict(r) for r in allrows
                 if "accumulated" in json.dumps(dict(r), default=str).lower()])
        except Exception as e:
            rec("all_rows_error_" + child_dt.replace(" ", "_"), str(e))

    # any Report anywhere whose stored code/json mentions the switch
    rec("reports_mentioning_accumulated_values", frappe.db.sql("""
        select name, report_type, reference_report from tabReport
        where ifnull(json,'') like '%%accumulated_values%%'
           or ifnull(javascript,'') like '%%accumulated_values%%'
           or ifnull(query,'') like '%%accumulated_values%%'
           or ifnull(report_script,'') like '%%accumulated_values%%'
    """, as_dict=True))
    rec("report_filters_mentioning_accumulated", frappe.db.sql("""
        select parent, fieldname from `tabReport Filter`
        where fieldname like '%%accumulated%%'
    """, as_dict=True))
    # any Custom Report built ON TOP of Custom Financial Statement?
    rec("custom_reports_referencing_cfs", frappe.db.sql("""
        select name, report_type, reference_report, ifnull(json,'') as json from tabReport
        where reference_report = 'Custom Financial Statement'
           or ifnull(json,'') like '%%report_template%%'
    """, as_dict=True))
    rec("all_reports_count", frappe.db.count("Report"))
    rec("all_custom_reports", frappe.db.sql("""
        select name, reference_report from tabReport where report_type = 'Custom Report'
    """, as_dict=True))

    # ---------- 2. stored client/server-side overrides ----------
    for dt in ("Property Setter", "Client Script", "Server Script", "Custom Field",
               "DocType Layout", "Report View Settings", "List View Settings",
               "Dashboard Chart", "Number Card", "Workspace"):
        if not frappe.db.exists("DocType", dt):
            rec("scan_missing_" + dt.replace(" ", "_"), True)
            continue
        try:
            names = frappe.get_all(dt, pluck="name")
            flagged = []
            for n in names:
                blob = json.dumps(frappe.get_doc(dt, n).as_dict(), default=str, ensure_ascii=False)
                low = blob.lower()
                if "accumulated_values" in low or "financial_report" in low \
                        or "custom financial statement" in low:
                    flagged.append(n)
            rec("scan_" + dt.replace(" ", "_"), {"rows": len(names), "flagged": flagged})
        except Exception as e:
            rec("scan_error_" + dt.replace(" ", "_"), str(e))

    # ---------- 3. filesystem: listings first, grep second ----------
    rec("installed_apps", frappe.get_installed_apps())

    all_files = []
    for app in frappe.get_installed_apps():
        root = frappe.get_app_path(app)
        for dirpath, dirnames, files in os.walk(root):
            dirnames[:] = [d for d in dirnames
                           if d not in ("node_modules", ".git", "__pycache__", "dist", "locale")]
            for fn in files:
                if fn.endswith((".py", ".js", ".json", ".html", ".md")):
                    all_files.append(os.path.join(dirpath, fn))
    rec("scanned_file_count", len(all_files))

    needles = ["accumulated_values", "accumulated", "cumulative", "year_to_date", "ytd",
               "running_balance", "accumulate", "balance_type", "report_template"]
    hits = {n: {} for n in needles}
    for p in all_files:
        try:
            with open(p, encoding="utf-8") as f:
                txt = f.read()
        except (OSError, UnicodeDecodeError):
            continue
        low = txt.lower()
        for n in needles:
            c = low.count(n)
            if c:
                hits[n][p] = c
    rec("needle_total_files", {n: len(v) for n, v in hits.items()})
    rec("accumulated_values_every_file", hits["accumulated_values"])

    # the exact three files the original probe counted, plus every sibling in
    # those directories so "not found" cannot hide a file it never opened
    for d in [("erpnext", "accounts", "report", "custom_financial_statement"),
              ("erpnext", "public", "js"),
              ("erpnext", "accounts", "report", "balance_sheet"),
              ("erpnext", "accounts", "report", "profit_and_loss_statement"),
              ("erpnext", "accounts", "doctype", "financial_report_template"),
              ("erpnext", "accounts", "doctype", "financial_report_row")]:
        p = frappe.get_app_path(*d)
        try:
            rec("listing_" + "_".join(d[1:]), sorted(os.listdir(p)))
        except OSError as e:
            rec("listing_error_" + "_".join(d[1:]), str(e))

    # ---------- 4. hooks of every installed app ----------
    hk = {}
    for app in frappe.get_installed_apps():
        try:
            with open(frappe.get_app_path(app, "hooks.py"), encoding="utf-8") as f:
                t = f.read().lower()
            hk[app] = {k: (k in t) for k in
                       ("financial_report", "custom_financial", "accumulated",
                        "override_whitelisted_methods", "doc_events")}
        except OSError as e:
            hk[app] = "ERR " + str(e)
    rec("hooks_scan", hk)
    # does any app monkeypatch get_period_list / get_columns / the engine?
    patchy = {}
    for p, c in hits["report_template"].items():
        if "erpnext" not in p:
            patchy[p] = c
    rec("non_erpnext_files_mentioning_report_template", patchy)

    # ---------- 5. label-assignment census, with line numbers ----------
    fs = frappe.get_app_path("erpnext", "accounts", "report", "financial_statements.py")
    eng = frappe.get_app_path("erpnext", "accounts", "doctype",
                              "financial_report_template", "financial_report_engine.py")
    with open(fs, encoding="utf-8") as f:
        fs_lines = f.read().splitlines()
    with open(eng, encoding="utf-8") as f:
        eng_lines = f.read().splitlines()

    fs_label = {str(i + 1): l.strip() for i, l in enumerate(fs_lines)
                if ("label =" in l or 'label"]' in l or "label']" in l)
                and not l.strip().startswith("#")}
    rec("fs_label_assignment_lines", fs_label)
    rec("fs_label_assignment_count", len(fs_label))

    eng_label = {str(i + 1): l.strip() for i, l in enumerate(eng_lines)
                 if ('["label"]' in l or ".label =" in l or "label =" in l)
                 and not l.strip().startswith("#")}
    rec("engine_label_assignment_lines", eng_label)

    def cite(lines, nums):
        return {str(n): lines[n - 1] for n in nums if 1 <= n <= len(lines)}

    rec("cited_engine_lines", cite(eng_lines,
        [60, 61, 62, 63, 64, 65, 66, 705, 709, 710, 711, 712, 713, 714, 715, 716, 717, 718,
         719, 720, 1185, 1417, 1418, 1712, 1723, 1724, 1725, 1726, 1727, 1728, 1770, 1771]))
    rec("engine_initialize_context_268_292", cite(eng_lines, list(range(268, 293))))
    rec("fs_get_period_list_84_100", cite(fs_lines, list(range(84, 101))))
    rec("fs_lines_279_288_for_contrast", cite(fs_lines, list(range(279, 289))))

    # does the ENGINE ever pass accumulated_values into get_period_list anywhere?
    rec("engine_get_period_list_callsites",
        {str(i + 1): l.strip() for i, l in enumerate(eng_lines) if "get_period_list(" in l})
    rec("engine_lines_after_each_get_period_list",
        {str(i + 1): "\n".join(eng_lines[i:i + 14]) for i, l in enumerate(eng_lines)
         if "get_period_list(" in l})

except Exception as e:
    import traceback
    rec("probe_error", {"err": str(e), "tb": traceback.format_exc()[-2500:]})

finally:
    frappe.db.rollback()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)
    print("\nWROTE " + OUT, flush=True)
