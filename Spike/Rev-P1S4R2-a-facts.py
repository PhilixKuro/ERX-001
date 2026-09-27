# REV AUDIT of V-25 / V-26 -- part A: READ-ONLY facts.
#
# Independently re-derives every load-bearing DATA claim without reusing the
# original probes' helpers where a rawer route exists (direct SQL instead of
# frappe.get_all, frappe.get_meta + DB doctype rows instead of the app's JSON
# files alone).
#
# NO WRITES AT ALL in this file. No frappe.db.commit(), no frappe.enqueue.
#
# Run (cwd MUST be .../sites):
#   docker exec -i -w /workspace/frappe-bench/sites erx001-frappe-1 \
#     /workspace/frappe-bench/env/bin/python /workspace/Spike/Rev-P1S4R2-a-facts.py

import json
import os

import frappe

SITE = "erx.localhost"
OUT = "/workspace/Spike/Rev-out/a-facts.json"

result = {"probe": "REV audit part A: read-only independent facts"}


def rec(k, v):
    result[k] = v
    # ASCII-only stdout so the Windows host console cannot mangle it
    print("[" + k + "] " + json.dumps(v, ensure_ascii=True, default=str)[:1800], flush=True)


frappe.init(site=SITE)
frappe.connect()
frappe.set_user("Administrator")

try:
    # ---------- 0. baseline the site, before anything ----------
    companies = frappe.db.sql("select name, default_currency from tabCompany", as_dict=True)
    rec("companies", companies)
    company = companies[0]["name"]

    rec("baseline_counts", {
        "GL Entry": frappe.db.count("GL Entry"),
        "GL Entry not cancelled": frappe.db.count("GL Entry", {"is_cancelled": 0}),
        "Stock Ledger Entry": frappe.db.count("Stock Ledger Entry"),
        "Account": frappe.db.count("Account"),
        "Company": frappe.db.count("Company"),
        "Financial Report Template": frappe.db.count("Financial Report Template"),
        "Fiscal Year": frappe.db.count("Fiscal Year"),
        "Period Closing Voucher": frappe.db.count("Period Closing Voucher"),
        "Account Closing Balance": frappe.db.count("Account Closing Balance"),
    })
    rec("fiscal_years", frappe.db.sql(
        "select name, year_start_date, year_end_date, disabled from `tabFiscal Year`"
        " order by year_start_date", as_dict=True))
    rec("frt_names", frappe.db.sql(
        "select name, report_type, module, disabled from `tabFinancial Report Template`"
        " order by name", as_dict=True))

    # ---------- 1. PCV / ACB -- the thing that would zero P&L at a year end ----------
    rec("pcv_all_docstatus", frappe.db.sql(
        "select name, docstatus, period_end_date, company from `tabPeriod Closing Voucher`",
        as_dict=True))
    rec("acb_rows_raw_sql", frappe.db.sql(
        "select count(*) as n from `tabAccount Closing Balance`", as_dict=True))
    rec("accounts_settings", {
        "ignore_account_closing_balance": frappe.get_single_value(
            "Accounts Settings", "ignore_account_closing_balance"),
        "ignore_is_opening_check_for_reporting": frappe.get_single_value(
            "Accounts Settings", "ignore_is_opening_check_for_reporting"),
        "use_legacy_controller_for_pcv": frappe.get_single_value(
            "Accounts Settings", "use_legacy_controller_for_pcv"),
    })

    # ---------- 2. EVERY GL entry, raw SQL, with root_type -- independent of probe ----------
    all_gl = frappe.db.sql("""
        select g.name, g.account, a.root_type, a.account_type, g.posting_date,
               g.debit, g.credit, g.is_opening, g.is_cancelled, g.voucher_type, g.company
        from `tabGL Entry` g
        left join `tabAccount` a on a.name = g.account
        order by g.posting_date, g.account
    """, as_dict=True)
    rec("all_gl_entries_count", len(all_gl))
    rec("all_gl_entries", all_gl)

    # month x root_type spread: does ANY month other than 2026-09 carry postings?
    spread = {}
    for r in all_gl:
        if r["is_cancelled"]:
            continue
        m = str(r["posting_date"])[:7]
        rt = r["root_type"] or "?"
        d = spread.setdefault(m, {})
        e = d.setdefault(rt, {"debit": 0.0, "credit": 0.0, "n": 0})
        e["debit"] += float(r["debit"] or 0)
        e["credit"] += float(r["credit"] or 0)
        e["n"] += 1
    rec("gl_month_x_roottype", spread)

    # ---------- 3. independent recompute of the 1045.0 / 325.5 / 719.5 triple ----------
    # Pure SQL. No engine, no probe helper.
    pl_sql = frappe.db.sql("""
        select a.root_type,
               sum(g.debit) as dr, sum(g.credit) as cr,
               sum(g.debit - g.credit) as net,
               count(*) as n
        from `tabGL Entry` g join `tabAccount` a on a.name = g.account
        where g.company = %s and g.is_cancelled = 0 and a.is_group = 0
              and a.root_type in ('Income','Expense')
        group by a.root_type
    """, (company,), as_dict=True)
    rec("pl_by_roottype_raw_sql", pl_sql)

    income_net = sum(float(r["net"]) for r in pl_sql if r["root_type"] == "Income")
    expense_net = sum(float(r["net"]) for r in pl_sql if r["root_type"] == "Expense")
    rec("independent_triple", {
        "income_net_debit_minus_credit": round(income_net, 6),
        "income_reverse_signed": round(-income_net, 6),
        "expense_net_debit_minus_credit": round(expense_net, 6),
        "revenue_equals_1045": round(-income_net, 6) == 1045.0,
        "cost_equals_325_5": round(expense_net, 6) == 325.5,
        "difference": round(-income_net - expense_net, 6),
        "difference_equals_719_5": round(-income_net - expense_net, 6) == 719.5,
        "raw_net_equals_minus_719_5": round(income_net + expense_net, 6) == -719.5,
    })
    # per-account detail so the 325.5 can be seen to be a NET of two accounts
    rec("pl_by_account_raw_sql", frappe.db.sql("""
        select g.account, a.root_type, sum(g.debit) as dr, sum(g.credit) as cr,
               sum(g.debit - g.credit) as net, min(g.posting_date) as first_date,
               max(g.posting_date) as last_date, count(*) as n
        from `tabGL Entry` g join `tabAccount` a on a.name = g.account
        where g.company = %s and g.is_cancelled = 0 and a.is_group = 0
              and a.root_type in ('Income','Expense')
        group by g.account, a.root_type order by a.root_type, g.account
    """, (company,), as_dict=True))

    # ---------- 4. balance_type: is it really a ROW-level field? ----------
    # (a) DocField rows straight out of the DB, with their parent doctype
    rec("docfield_balance_type_rows", frappe.db.sql("""
        select parent, fieldname, fieldtype, label, options
        from tabDocField where fieldname = 'balance_type'
    """, as_dict=True))
    # (b) is the parent a child table?
    rec("doctype_flags", frappe.db.sql("""
        select name, istable, is_submittable, module
        from tabDocType where name in ('Financial Report Row','Financial Report Template')
    """, as_dict=True))
    # (c) any Custom Field named balance_type anywhere?
    rec("custom_fields_balance_type", frappe.db.sql("""
        select dt, fieldname, fieldtype from `tabCustom Field`
        where fieldname like '%%balance_type%%'
    """, as_dict=True))
    # (d) meta field counts, and any label/header-ish field
    for dt in ("Financial Report Row", "Financial Report Template"):
        meta = frappe.get_meta(dt)
        names = [f.fieldname for f in meta.fields]
        rec("meta_" + dt.replace(" ", "_"), {
            "field_count": len(names),
            "fieldnames": names,
            "istable": meta.istable,
            "label_or_header_fields": [n for n in names
                                       if "label" in n.lower() or "header" in n.lower()],
            "column_name_ish": [n for n in names
                                if any(t in n.lower() for t in
                                       ("label", "header", "caption", "title",
                                        "col_name", "column_name", "heading"))],
        })
    # (e) does the template row table actually store balance_type per row? sample the
    #     shipped columnar BS template and show balance_type varying row by row
    rec("shipped_columnar_rows", frappe.db.sql("""
        select idx, data_source, display_name, balance_type, reference_code
        from `tabFinancial Report Row`
        where parent = 'Horizontal Balance Sheet (Columnar)' order by idx
    """, as_dict=True))
    rec("shipped_columnar_balance_type_histogram", frappe.db.sql("""
        select balance_type, count(*) as n from `tabFinancial Report Row`
        where parent = 'Horizontal Balance Sheet (Columnar)'
        group by balance_type
    """, as_dict=True))
    # (f) across ALL shipped templates: do any two rows in ONE template differ in
    #     balance_type? if so, row-level granularity is already exercised in-product.
    rec("templates_with_mixed_balance_types", frappe.db.sql("""
        select parent, count(distinct balance_type) as distinct_types,
               group_concat(distinct balance_type) as types
        from `tabFinancial Report Row`
        where ifnull(balance_type,'') != ''
        group by parent having distinct_types > 1
    """, as_dict=True))

    # ---------- 5. accumulated_values: can anything inject it on the FRT path? ----------
    # (a) the Report doc AS STORED IN THE DB (not just the app's .json on disk)
    rep = frappe.db.sql("""
        select name, report_type, is_standard, ref_doctype, module, disabled,
               json, filters, columns, prepared_report
        from tabReport where name = 'Custom Financial Statement'
    """, as_dict=True)
    rec("report_doc_db_row", rep)
    rec("report_filters_child_rows", frappe.db.sql("""
        select parent, parentfield, fieldname, label, fieldtype, default_value
        from `tabReport Filter` where parent = 'Custom Financial Statement'
    """, as_dict=True) if frappe.db.exists("DocType", "Report Filter") else "no Report Filter doctype")
    # (b) every Report row whose stored filters/json mentions accumulated_values
    rec("reports_mentioning_accumulated_values", frappe.db.sql("""
        select name from tabReport
        where ifnull(json,'') like '%%accumulated_values%%'
           or ifnull(filters,'') like '%%accumulated_values%%'
    """, as_dict=True))
    # (c) any saved user filter / Report View Settings preset
    for dt in ("Report View Settings", "List View Settings", "Property Setter",
               "Client Script", "Server Script", "Custom HTML Block"):
        if not frappe.db.exists("DocType", dt):
            continue
        try:
            hits = frappe.db.sql(
                "select name from `tab{0}`".format(dt), as_dict=True)
            flagged = []
            for h in hits:
                doc = frappe.get_doc(dt, h["name"])
                blob = json.dumps(doc.as_dict(), default=str, ensure_ascii=False)
                if "accumulated_values" in blob:
                    flagged.append(h["name"])
            rec("scan_" + dt.replace(" ", "_"), {"rows": len(hits), "mentioning": flagged})
        except Exception as e:
            rec("scan_error_" + dt.replace(" ", "_"), str(e))

    # (d) directory listing, not just grep: every financial_statements.js on disk,
    #     and every js under the two report dirs
    app_root = frappe.get_app_path("erpnext")
    js_hits = []
    for root, _dirs, files in os.walk(app_root):
        for fn in files:
            if fn.endswith(".js") and "financial" in fn:
                js_hits.append(os.path.join(root, fn))
    rec("all_financial_js_files", sorted(js_hits))

    def count_in(path, needle):
        try:
            with open(path, encoding="utf-8") as f:
                return f.read().count(needle)
        except OSError as e:
            return "ERR " + str(e)

    rec("accumulated_values_counts_per_js",
        {p: count_in(p, "accumulated_values") for p in sorted(js_hits)})
    rec("cfs_report_dir_listing", sorted(os.listdir(frappe.get_app_path(
        "erpnext", "accounts", "report", "custom_financial_statement"))))
    rec("public_js_listing", sorted(os.listdir(frappe.get_app_path("erpnext", "public", "js"))))

    # (e) grep synonyms across the whole app (py + js), not just the one token
    syn = ["accumulated_values", "accumulated", "cumulative", "ytd", "year_to_date",
           "running_balance", "accumulate"]
    syn_hits = {s: [] for s in syn}
    for root, _dirs, files in os.walk(app_root):
        if "node_modules" in root or "/.git" in root:
            continue
        for fn in files:
            if not (fn.endswith(".py") or fn.endswith(".js") or fn.endswith(".json")):
                continue
            p = os.path.join(root, fn)
            try:
                with open(p, encoding="utf-8") as f:
                    txt = f.read()
            except (OSError, UnicodeDecodeError):
                continue
            low = txt.lower()
            for s in syn:
                if s in low:
                    syn_hits[s].append(os.path.relpath(p, app_root) + ":" + str(low.count(s)))
    rec("synonym_scan_counts", {s: len(v) for s, v in syn_hits.items()})
    rec("synonym_scan_engine_and_cfs_only", {
        s: [h for h in v if ("financial_report_template" in h
                             or "custom_financial_statement" in h
                             or "public/js" in h or "public\\js" in h)]
        for s, v in syn_hits.items()})

    # (f) does anything in the installed apps (not just erpnext) hook the CFS report
    #     or the engine?
    rec("installed_apps", frappe.get_installed_apps())
    hooks_hits = {}
    for app in frappe.get_installed_apps():
        try:
            hp = frappe.get_app_path(app, "hooks.py")
            with open(hp, encoding="utf-8") as f:
                txt = f.read()
            hooks_hits[app] = {
                "mentions_financial_report": "financial_report" in txt.lower(),
                "mentions_custom_financial": "custom_financial" in txt.lower(),
                "mentions_accumulated": "accumulated" in txt.lower(),
            }
        except OSError as e:
            hooks_hits[app] = "ERR " + str(e)
    rec("hooks_scan", hooks_hits)

    # ---------- 6. the exact engine lines the verdicts cite ----------
    eng = frappe.get_app_path("erpnext", "accounts", "doctype",
                              "financial_report_template", "financial_report_engine.py")
    fs = frappe.get_app_path("erpnext", "accounts", "report", "financial_statements.py")
    with open(eng, encoding="utf-8") as f:
        eng_lines = f.read().splitlines()
    with open(fs, encoding="utf-8") as f:
        fs_lines = f.read().splitlines()

    def cite(lines, nums):
        return {str(n): lines[n - 1] for n in nums if 1 <= n <= len(lines)}

    rec("cited_engine_lines", cite(eng_lines,
        [60, 61, 62, 63, 64, 65, 66, 705, 709, 711, 712, 713, 714, 715,
         1185, 1417, 1418, 1712, 1726, 1727, 1728, 1770, 1771]))
    rec("cited_fs_lines", cite(fs_lines, [279, 280, 281, 282, 283, 284, 285, 286, 287, 288]))
    rec("engine_lines_279_288_note",
        "V-25 cites _initialize_context():279-288 in the ENGINE file, not financial_statements.py")
    rec("engine_lines_268_292", cite(eng_lines, list(range(268, 293))))

    # every label-assignment line in financial_statements.py, with numbers
    rec("fs_label_assignment_lines",
        {str(i + 1): l.strip() for i, l in enumerate(fs_lines)
         if "label" in l and "=" in l and not l.strip().startswith("#")})
    # every place the engine sets a column label
    rec("engine_label_assignment_lines",
        {str(i + 1): l.strip() for i, l in enumerate(eng_lines)
         if ('["label"]' in l or "'label'" in l or ".label =" in l) and "=" in l})

    # ---------- 7. does the template layer reach ANY column name? ----------
    # list every distinct Column Break display_name shipped, and how the engine
    # formats a segment label into a column label
    rec("all_column_break_display_names", frappe.db.sql("""
        select parent, idx, ifnull(display_name,'<NULL>') as display_name
        from `tabFinancial Report Row` where data_source = 'Column Break'
        order by parent, idx
    """, as_dict=True))

except Exception as e:
    import traceback
    rec("probe_error", {"err": str(e), "tb": traceback.format_exc()[-2500:]})

finally:
    # read-only probe: rollback is a no-op safety net, never a commit
    frappe.db.rollback()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)
    print("\nWROTE " + OUT, flush=True)
