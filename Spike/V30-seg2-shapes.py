# V-30 probe (b): what happens when the Custom API returns something OTHER than a
# flat per-period list -- does the engine coerce, throw, or silently zero?
#
# Sub-question (b) of V-30. The point is to find out whether "a flat list of numbers
# ordered by period" is merely a CONVENTION the engine hopes for, or a contract it
# enforces -- and where a violation surfaces (at the call, or later during formatting).
#
# KEY STRUCTURAL POINT this probe tests: the try/except at
# financial_report_engine.py:1183-1194 wraps ONLY the frappe.call itself. The values
# are consumed much later, in RowFormatterBase._get_period_value (:1671-1675), during
# format_report_data (:222) -- OUTSIDE that try. So a bad shape may pass the guarded
# call and then blow up unguarded, which is a materially different failure mode from
# the silent zero.
#
# ZERO FILESYSTEM TRACE: the whitelisted method is defined in-process and injected via
# sys.modules, which probe (a) proved resolves identically through frappe.get_attr
# (get_valid_api_method reached it and reported allowed_http_methods == ["GET"]).
# Nothing is written to any app directory.
#
# SITE SAFETY: templates are inserted inside a transaction and rolled back; no
# frappe.db.commit() anywhere; `module` left EMPTY so on_update -> _export_template()
# returns early (financial_report_template.py:62) and writes no JSON into the source tree.
# NOTE (from V30-seg0c): tabError Log is MyISAM = NON-transactional, so any Error Log
# row written by the engine's silent-zero path does NOT roll back. Every such row this
# probe causes is deleted explicitly BY NAME at the end, and the count is verified.
#
# Run (cwd MUST be .../sites, else frappe's logger dies on a relative path):
#   docker exec -i -w /workspace/frappe-bench/sites erx001-frappe-1 \
#     /workspace/frappe-bench/env/bin/python /workspace/Spike/V30-seg2-shapes.py

import json
import sys
import traceback
import types

import frappe

SITE = "erx.localhost"
OUT = "/workspace/Spike/V30-out/b-return-shapes.json"
INJ = "erpnext.zz_v30_shapes_inj"

result = {"probe": "V-30 (b) non-flat Custom API return shapes"}


def rec(k, v):
    result[k] = v
    print("[" + k + "] " + json.dumps(v, ensure_ascii=False, default=str)[:2200], flush=True)


frappe.init(site=SITE)
frappe.connect()
frappe.set_user("Administrator")

# ---- state shared with the injected method ----
STATE = {"shape": "flat"}


@frappe.whitelist(methods=["GET"])
def shaped(filters=None, periods=None, row=None):
    """Return whatever shape STATE asks for. Deliberately contract-violating."""
    n = len(periods) if periods else 0
    s = STATE["shape"]
    if s == "flat":
        return [100.0 + i for i in range(n)]
    if s == "dict_keyed_by_period":
        return {p["key"]: 200.0 + i for i, p in enumerate(periods)}
    if s == "dict_arbitrary":
        return {"total": 999.0, "note": "not a list"}
    if s == "short_list":
        return [301.0, 302.0]                      # 2 values for 12 periods
    if s == "long_list":
        return [400.0 + i for i in range(n + 5)]   # 17 values for 12 periods
    if s == "list_of_strings":
        return ["abc"] * n
    if s == "list_of_numeric_strings":
        return [str(500 + i) for i in range(n)]
    if s == "empty_list":
        return []
    if s == "none":
        return None
    if s == "scalar":
        return 777.0
    if s == "list_of_dicts":
        return [{"value": 600.0 + i, "label": "L%d" % i} for i in range(n)]
    if s == "nested_list":
        return [[700.0 + i] for i in range(n)]
    if s == "list_with_none":
        return [None] * n
    return [0.0] * n


inj = types.ModuleType(INJ)
inj.shaped = shaped
sys.modules[INJ] = inj

SHAPES = [
    "flat",
    "dict_keyed_by_period",
    "dict_arbitrary",
    "short_list",
    "long_list",
    "list_of_strings",
    "list_of_numeric_strings",
    "empty_list",
    "none",
    "scalar",
    "list_of_dicts",
    "nested_list",
    "list_with_none",
]

err_names_before = set()

try:
    companies = frappe.get_all("Company", pluck="name")
    COMPANY = companies[0]
    rec("company_used", COMPANY)

    # NOTE: pluck="name" returns plain STRINGS, not objects. An earlier version of this
    # script wrote `{r.name for r in ...}` here, which raised AttributeError, left this
    # set EMPTY, and made the finally-block's "rows not in baseline" logic delete the
    # two PRE-EXISTING rows. Cleanup is now positively scoped by marker instead.
    err_names_before = set(frappe.get_all("Error Log", pluck="name"))
    rec("error_log_count_before", len(err_names_before))
    rec("error_log_names_before", sorted(err_names_before))

    from erpnext.accounts.doctype.financial_report_template.financial_report_engine import (
        FinancialReportEngine,
    )

    findings = {}

    for shape in SHAPES:
        STATE["shape"] = shape
        tpl_name = "ZZ-PROBE-V30-Shape-" + shape
        entry = {}
        try:
            doc = frappe.get_doc({
                "doctype": "Financial Report Template",
                "template_name": tpl_name,
                "report_type": "Profit and Loss Statement",
                "rows": [{
                    "data_source": "Custom API",
                    "display_name": "API Row",
                    "reference_code": "API_ROW",
                    "calculation_formula": INJ + ".shaped",
                    "fieldtype": "Currency",
                }],
            })
            doc.insert(ignore_permissions=True)

            filters = frappe._dict({
                "company": COMPANY, "report_template": doc.name,
                "filter_based_on": "Fiscal Year",
                "from_fiscal_year": "2026", "to_fiscal_year": "2026",
                "periodicity": "Monthly", "selected_view": "Report",
                "include_default_book_entries": 1,
            })

            e_before = frappe.db.count("Error Log")
            res = FinancialReportEngine().execute(filters)
            e_after = frappe.db.count("Error Log")

            cols, data = res[0], res[1]
            pkeys = [c["fieldname"] for c in cols
                     if c["fieldname"] not in ("account", "acc_name", "acc_number",
                                               "currency", "total")]
            api_row = None
            for r in data:
                if r.get("account_name") == "API Row":
                    api_row = r
            entry["outcome"] = "engine_returned"
            entry["error_log_delta"] = e_after - e_before
            entry["silent_zero_fired"] = (e_after - e_before) > 0
            entry["n_columns_total"] = len(cols)
            entry["n_period_columns"] = len(pkeys)
            entry["column_labels"] = [c.get("label") for c in cols]
            if api_row is not None:
                entry["first_3_cells"] = {k: api_row.get(k) for k in pkeys[:3]}
                entry["last_2_cells"] = {k: api_row.get(k) for k in pkeys[-2:]}
                entry["all_cells"] = {k: api_row.get(k) for k in pkeys}
            else:
                entry["row_missing"] = True

        except Exception as e:
            entry["outcome"] = "RAISED_to_caller"
            entry["exc_type"] = type(e).__name__
            entry["exc_msg"] = str(e)[:300]
            entry["tb_tail"] = traceback.format_exc()[-700:]
            frappe.clear_last_message()

        findings[shape] = entry
        print("  -> " + shape + ": " + str(entry.get("outcome"))
              + " / silent_zero=" + str(entry.get("silent_zero_fired")), flush=True)

    rec("shape_findings", findings)

    # ---------- DECISIVE for (b) ----------
    summary = {}
    for shape, e in findings.items():
        summary[shape] = {
            "outcome": e.get("outcome"),
            "silent_zero": e.get("silent_zero_fired"),
            "n_period_columns": e.get("n_period_columns"),
            "exc": e.get("exc_type"),
        }
    rec("DECISIVE_b_summary", summary)

    # did ANY shape alter the column count or labels?
    baseline_labels = findings.get("flat", {}).get("column_labels")
    col_changes = {}
    for shape, e in findings.items():
        lbls = e.get("column_labels")
        if lbls is not None and lbls != baseline_labels:
            col_changes[shape] = lbls
    rec("shapes_that_changed_columns", col_changes)
    rec("any_shape_changed_columns", bool(col_changes))
    rec("baseline_flat_column_labels", baseline_labels)

except Exception as e:
    rec("probe_error", {"err": str(e), "tb": traceback.format_exc()[-3000:]})

finally:
    frappe.db.rollback()
    rec("any_probe_template_left",
        [r.name for r in frappe.get_all("Financial Report Template",
                                        filters={"template_name": ["like", "ZZ-PROBE-V30%"]},
                                        fields=["name"])])

    # ---- tabError Log is MyISAM: rollback will NOT remove rows (proven in seg0c).
    # Cleanup is POSITIVELY scoped: only rows whose method names MY injected module
    # (INJ) can match, so a bookkeeping slip can never reach a pre-existing row.
    # The engine writes "Custom API Error: {api_path} - {err}" at engine.py:1193,
    # and api_path here is always INJ + ".shaped".
    mine = frappe.get_all("Error Log", filters={"method": ["like", "%" + INJ + "%"]},
                          fields=["name", "method"])
    rec("error_log_rows_created_by_this_probe",
        [{"name": m["name"], "method": (m["method"] or "")[:90]} for m in mine])
    for m in mine:
        frappe.db.delete("Error Log", {"name": m["name"]})
    rec("error_log_rows_remaining_with_my_marker",
        frappe.get_all("Error Log", filters={"method": ["like", "%" + INJ + "%"]},
                       pluck="name"))
    # report, but never delete, anything else that appeared
    other_new = [n for n in frappe.get_all("Error Log", pluck="name")
                 if n not in err_names_before]
    rec("other_new_error_log_rows_left_untouched", other_new)
    rec("error_log_count_final", frappe.db.count("Error Log"))

    counts = {}
    for dt in ["GL Entry", "Stock Ledger Entry", "Account", "Company",
               "Financial Report Template", "Fiscal Year"]:
        counts[dt] = frappe.db.count(dt)
    rec("counts_after_rollback", counts)
    rec("fiscal_years_after_rollback",
        [r.name for r in frappe.get_all("Fiscal Year", fields=["name"])])

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)
    print("\nWROTE " + OUT, flush=True)
