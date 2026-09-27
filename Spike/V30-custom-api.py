# V-30 probe (a): what a NORMAL flat numeric Custom API return actually produces,
# and whether an arbitrary app's @frappe.whitelist(methods=["GET"]) method can be
# referenced with no upstream modification.
#
# Proposition V-30: for a `Financial Report Row` with data_source == "Custom API",
# is the return value necessarily a flat list of numbers ordered by period -- i.e.
# does Custom API genuinely provide no way to change the NUMBER or NAMES of columns?
#
# V-25 read the call signature at financial_report_engine.py:1185 and inferred this.
# It never ran one. This probe runs one.
#
# Sub-question (a) only. Shapes other than flat -> V30-seg2-shapes.py;
# raising -> V30-seg3-silent-zero.py; column control -> V30-seg4-columns.py.
#
# SENTINEL DESIGN: the method returns 1001 for period 0, 1002 for period 1, ...
# Unique per index, so the mapping value->column PROVES positional ordering by
# period index rather than merely being consistent with it.
#
# TEMP FILE: this probe creates ONE module file inside the erpnext app tree
#   <erpnext app>/zz_v30_probe_tmp.py
# It is ADDITIVE -- no upstream source file is modified -- and it is deleted in
# `finally`, together with its __pycache__, with deletion verified and reported.
# It also cross-checks a zero-filesystem-trace alternative (sys.modules injection)
# so the later probes can legitimately use that instead.
#
# WRITES NOTHING PERMANENT: the template is inserted inside a transaction and
# rolled back. No frappe.db.commit() anywhere. `module` is left EMPTY on purpose:
# FinancialReportTemplate.on_update -> _export_template() writes template JSON into
# the erpnext source tree when module is set (financial_report_template.py:59-65,
# which returns early at :62 when module is falsy), and a filesystem write is NOT
# undone by rollback.
#
# Run (cwd MUST be .../sites, else frappe's logger dies on a relative path):
#   docker exec -i -w /workspace/frappe-bench/sites erx001-frappe-1 \
#     /workspace/frappe-bench/env/bin/python /workspace/Spike/V30-custom-api.py

import glob
import importlib
import json
import os
import sys
import traceback
import types

import frappe

SITE = "erx.localhost"
OUT = "/workspace/Spike/V30-out/a-flat-return.json"
TPL = "ZZ-PROBE-V30-CustomAPI-Flat"
MOD = "erpnext.zz_v30_probe_tmp"
INJ = "erpnext.zz_v30_injected_tmp"

result = {"probe": "V-30 (a) flat numeric Custom API return + whitelist/GET contract"}


def rec(k, v):
    result[k] = v
    print("[" + k + "] " + json.dumps(v, ensure_ascii=False, default=str)[:2400], flush=True)


# ---- source of the temporary probe module (ASCII only) ----
TMP_SRC = '''# TEMPORARY module created by V30-custom-api.py and deleted in the same run.
import frappe

RECEIVED = {}


@frappe.whitelist(methods=["GET"])
def flat_values(filters=None, periods=None, row=None):
    """Well-behaved Custom API: one number per period, unique sentinel per index."""
    RECEIVED["calls"] = RECEIVED.get("calls", 0) + 1
    RECEIVED["filters_type"] = type(filters).__name__
    RECEIVED["filters_is_none"] = filters is None
    if hasattr(filters, "keys"):
        RECEIVED["filters_keys"] = sorted([str(k) for k in filters.keys()])
        RECEIVED["filters_company"] = filters.get("company")
        RECEIVED["filters_periodicity"] = filters.get("periodicity")
    RECEIVED["periods_type"] = type(periods).__name__
    RECEIVED["periods_len"] = len(periods) if periods is not None else None
    if periods:
        RECEIVED["period_keys"] = [p["key"] for p in periods]
        RECEIVED["period_labels"] = [p["label"] for p in periods]
        RECEIVED["period_item_type"] = type(periods[0]).__name__
    RECEIVED["row_type"] = type(row).__name__
    RECEIVED["row_ref"] = getattr(row, "reference_code", None)
    RECEIVED["row_data_source"] = getattr(row, "data_source", None)
    RECEIVED["row_display_name"] = getattr(row, "display_name", None)
    RECEIVED["row_reverse_sign"] = getattr(row, "reverse_sign", None)
    n = len(periods) if periods else 0
    return [1000.0 + i + 1 for i in range(n)]


@frappe.whitelist(methods=["POST"])
def post_only(filters=None, periods=None, row=None):
    return [0.0] * (len(periods) if periods else 0)


def plain_not_whitelisted(filters=None, periods=None, row=None):
    return [0.0] * (len(periods) if periods else 0)
'''

frappe.init(site=SITE)
frappe.connect()
frappe.set_user("Administrator")

tmp_path = None

try:
    # ---------- 0. drop the temporary module into an EXISTING app ----------
    app_dir = frappe.get_app_path("erpnext")
    tmp_path = os.path.join(app_dir, "zz_v30_probe_tmp.py")
    rec("temp_module_path", tmp_path)
    rec("temp_module_existed_before", os.path.exists(tmp_path))
    with open(tmp_path, "w", encoding="ascii") as f:
        f.write(TMP_SRC)
    importlib.invalidate_caches()

    # company is Chinese; read it from the DB to keep this source ASCII-only
    companies = frappe.get_all("Company", pluck="name")
    COMPANY = companies[0]
    rec("company_used", COMPANY)
    rec("company_count", len(companies))

    # ---------- 1. the validation contract: financial_report_validation.py:18-30 ----
    from erpnext.accounts.doctype.financial_report_template.financial_report_validation import (
        get_valid_api_method,
    )

    contract = {}

    def try_resolve(tag, path):
        try:
            m = get_valid_api_method(path)
            contract[tag] = {
                "ok": True,
                "resolved": getattr(m, "__name__", str(m)),
                "allowed_http_methods": list(
                    frappe.allowed_http_methods_for_whitelisted_func.get(m, ())
                ),
            }
        except Exception as e:
            contract[tag] = {
                "ok": False,
                "exc_type": type(e).__name__,
                "msg": str(e)[:300],
            }
            frappe.clear_last_message()

    try_resolve("GET_whitelisted (expect ok)", MOD + ".flat_values")
    try_resolve("POST_only_whitelisted (expect throw)", MOD + ".post_only")
    try_resolve("not_whitelisted (expect throw)", MOD + ".plain_not_whitelisted")
    try_resolve("missing_attr (expect throw)", MOD + ".does_not_exist")
    try_resolve("uninstalled_app (expect throw)", "some_other_app.mod.meth")
    rec("validation_contract_get_valid_api_method", contract)

    # ---------- 1b. zero-filesystem-trace alternative: sys.modules injection ----------
    # Proves the later probes may define their method in-process instead of on disk.
    @frappe.whitelist(methods=["GET"])
    def injected_flat(filters=None, periods=None, row=None):
        return [2000.0 + i + 1 for i in range(len(periods) if periods else 0)]

    inj_mod = types.ModuleType(INJ)
    inj_mod.injected_flat = injected_flat
    sys.modules[INJ] = inj_mod
    try_resolve("sys_modules_injected_GET (expect ok)", INJ + ".injected_flat")
    rec("injection_resolves_identically",
        contract.get("sys_modules_injected_GET (expect ok)", {}).get("ok"))

    # ---------- 2. build a single-segment template with Custom API rows ----------
    # Single segment (no Column Break) => columns are the plain base set, which is
    # the cleanest ground for reading what Custom API did or did not affect.
    rows = [
        {"data_source": "Custom API", "display_name": "API Flat",
         "reference_code": "API_FLAT", "calculation_formula": MOD + ".flat_values",
         "fieldtype": "Currency"},
        {"data_source": "Custom API", "display_name": "API Flat Reversed",
         "reference_code": "API_REV", "calculation_formula": MOD + ".flat_values",
         "reverse_sign": 1, "fieldtype": "Currency"},
        {"data_source": "Calculated Amount", "display_name": "API Doubled",
         "reference_code": "API_X2", "calculation_formula": "API_FLAT * 2",
         "fieldtype": "Currency"},
    ]

    doc = frappe.get_doc({
        "doctype": "Financial Report Template",
        "template_name": TPL,
        "report_type": "Profit and Loss Statement",
        # module deliberately EMPTY -- see header note on _export_template()
        "rows": rows,
    })
    doc.insert(ignore_permissions=True)
    rec("template_inserted", {"name": doc.name, "module": doc.module,
                              "rows": len(doc.rows),
                              "note": "module empty on purpose"})

    # ---------- 3. run the real engine ----------
    from erpnext.accounts.doctype.financial_report_template.financial_report_engine import (
        FinancialReportEngine,
    )

    filters = frappe._dict({
        "company": COMPANY, "report_template": doc.name,
        "filter_based_on": "Fiscal Year",
        "from_fiscal_year": "2026", "to_fiscal_year": "2026",
        "periodicity": "Monthly", "selected_view": "Report",
        "include_default_book_entries": 1,
    })
    err_before = frappe.db.count("Error Log")
    res = FinancialReportEngine().execute(filters)
    err_after = frappe.db.count("Error Log")
    cols, data = res[0], res[1]

    rec("error_log_delta_during_run", {"before": err_before, "after": err_after,
                                       "delta": err_after - err_before,
                                       "note": "0 delta => no silent-zero fallback fired"})

    # ---------- 4. what the method actually received (the real :1185 contract) ------
    received = dict(sys.modules[MOD].RECEIVED)
    rec("kwargs_actually_received_by_method", received)

    # ---------- 5. what reached the report ----------
    rec("engine_columns", [{"fieldname": c.get("fieldname"), "label": c.get("label"),
                            "fieldtype": c.get("fieldtype"), "hidden": c.get("hidden")}
                           for c in cols])
    period_keys = received.get("period_keys") or []
    rec("period_keys_in_order", period_keys)

    delivered = {}
    for r in data:
        nm = r.get("account_name")
        if nm in ("API Flat", "API Flat Reversed", "API Doubled"):
            delivered[nm] = {k: r.get(k) for k in period_keys}
            delivered[nm]["__total__"] = r.get("total")
    rec("delivered_row_values", delivered)

    # ---------- 6. DECISIVE for (a): sentinel -> column mapping ----------
    flat = delivered.get("API Flat", {})
    rev = delivered.get("API Flat Reversed", {})
    x2 = delivered.get("API Doubled", {})
    expected = {k: 1000.0 + i + 1 for i, k in enumerate(period_keys)}
    mismatches = {k: {"expected": v, "got": flat.get(k)}
                  for k, v in expected.items() if flat.get(k) != v}
    rec("DECISIVE_a", {
        "n_periods_method_saw": received.get("periods_len"),
        "n_period_columns_in_report": len([c for c in cols
                                           if c.get("fieldname") in period_keys]),
        "return_len_equals_period_count": received.get("periods_len") == len(period_keys),
        "sentinel_to_column_mapping_exact": len(mismatches) == 0,
        "mismatches": mismatches,
        "ordering_is_positional_by_period_index": len(mismatches) == 0,
        "reverse_sign_negates": all(
            rev.get(k) == -expected[k] for k in period_keys) if rev else None,
        "calculated_amount_can_consume_api_ref": all(
            x2.get(k) == 2 * expected[k] for k in period_keys) if x2 else None,
        "times_method_was_called": received.get("calls"),
    })

    # ---------- 7. does the return value show up anywhere OTHER than cells? --------
    # i.e. did the flat numeric return leak into any column label / fieldname?
    sentinel_strings = [str(int(v)) for v in expected.values()]
    leak = [{"fieldname": c.get("fieldname"), "label": c.get("label")}
            for c in cols
            if any(s in str(c.get("label")) or s in str(c.get("fieldname"))
                   for s in sentinel_strings)]
    rec("return_value_leaked_into_columns", leak)

except Exception as e:
    rec("probe_error", {"err": str(e), "tb": traceback.format_exc()[-3000:]})

finally:
    frappe.db.rollback()
    rec("template_exists_after_rollback",
        bool(frappe.db.exists("Financial Report Template", TPL)))

    # ---- remove the temporary module + its bytecode, and PROVE it is gone ----
    removed = []
    if tmp_path and os.path.exists(tmp_path):
        os.remove(tmp_path)
        removed.append(tmp_path)
    pyc = glob.glob(os.path.join(frappe.get_app_path("erpnext"),
                                 "__pycache__", "zz_v30_probe_tmp*"))
    for p in pyc:
        os.remove(p)
        removed.append(p)
    rec("temp_files_removed", removed)
    rec("temp_module_gone", (not tmp_path) or (not os.path.exists(tmp_path)))
    rec("temp_pycache_gone",
        glob.glob(os.path.join(frappe.get_app_path("erpnext"),
                               "__pycache__", "zz_v30_probe_tmp*")) == [])

    # ---- no stray exported template JSON anywhere in the app tree ----
    strays = []
    for pat in ["*v30*", "*V30*", "*probe*", "*zz_*"]:
        strays += glob.glob(os.path.join(frappe.get_app_path("erpnext"), "accounts",
                                         "financial_report_template", pat))
    rec("stray_exported_template_files", strays)

    counts = {}
    for dt in ["GL Entry", "Stock Ledger Entry", "Account", "Company",
               "Financial Report Template", "Fiscal Year", "Error Log"]:
        counts[dt] = frappe.db.count(dt)
    rec("counts_after_rollback", counts)
    rec("fiscal_years_after_rollback",
        [r.name for r in frappe.get_all("Fiscal Year", fields=["name"])])

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)
    print("\nWROTE " + OUT, flush=True)
