# V-30 probe (c): does RAISING inside the Custom API method produce the reported
# "silent zero" at financial_report_engine.py:1192-1194?
#
#     except Exception as e:
#         frappe.log_error(f"Custom API Error: {api_path} - {e!s}")
#         values = [0.0] * len(self.period_list)
#
# V-25 read this but never triggered it. Probe (b) established something the
# proposition did not anticipate: a WRONG RETURN SHAPE does NOT reach this handler --
# it escapes the guarded block and crashes later at :1672-1673 during formatting.
# So the silent zero can only be reached by an exception raised INSIDE the call.
# This probe raises inside the call, deliberately.
#
# THE DECISIVE CRITERION (designed against the ambiguity the brief warns about):
# "cells are 0.0" alone cannot distinguish a swallowed failure from a legitimate zero.
# So this probe runs a BASELINE method that legitimately returns 0.0 for every period,
# and compares the full delivered report row byte-for-byte against the raising one.
# If the two are indistinguishable, "no error" genuinely does not mean "worked".
# It also captures every channel a user might notice through:
#   frappe.message_log (msgprint), frappe.local.response, the returned tuple, and
#   whether execute() raised at all.
#
# ZERO FILESYSTEM TRACE: method injected via sys.modules (proven equivalent in probe a).
#
# SITE SAFETY: templates inserted in a transaction and rolled back; no frappe.db.commit();
# `module` left EMPTY so _export_template() returns early (financial_report_template.py:62).
# tabError Log is MyISAM = NON-transactional (proven in V30-seg0c), so the Error Log rows
# this probe deliberately causes do NOT roll back. Cleanup is POSITIVELY scoped to rows
# whose `method` text contains my injected module name, so it cannot touch anything else.
#
# Run (cwd MUST be .../sites, else frappe's logger dies on a relative path):
#   docker exec -i -w /workspace/frappe-bench/sites erx001-frappe-1 \
#     /workspace/frappe-bench/env/bin/python /workspace/Spike/V30-seg3-silent-zero.py

import json
import sys
import traceback
import types

import frappe

SITE = "erx.localhost"
OUT = "/workspace/Spike/V30-out/c-silent-zero.json"
INJ = "erpnext.zz_v30_raise_inj"

result = {"probe": "V-30 (c) silent zero at engine.py:1192-1194"}


def rec(k, v):
    result[k] = v
    print("[" + k + "] " + json.dumps(v, ensure_ascii=False, default=str)[:2200], flush=True)


frappe.init(site=SITE)
frappe.connect()
frappe.set_user("Administrator")

MODE = {"mode": "legit_zero"}


@frappe.whitelist(methods=["GET"])
def maybe_raise(filters=None, periods=None, row=None):
    n = len(periods) if periods else 0
    m = MODE["mode"]
    if m == "legit_zero":
        # a genuine, correct answer that happens to be zero everywhere
        return [0.0] * n
    if m == "legit_values":
        return [42.0] * n
    if m == "raise_generic":
        raise Exception("V30 deliberate generic failure inside Custom API")
    if m == "raise_zero_division":
        return [1 / 0 for _ in range(n)]
    if m == "raise_validation":
        frappe.throw("V30 deliberate frappe.throw inside Custom API")
    if m == "raise_permission":
        raise frappe.PermissionError("V30 deliberate PermissionError inside Custom API")
    if m == "raise_keyerror":
        d = {}
        return [d["missing_key"] for _ in range(n)]
    return [0.0] * n


inj = types.ModuleType(INJ)
inj.maybe_raise = maybe_raise
sys.modules[INJ] = inj

MODES = ["legit_zero", "legit_values", "raise_generic", "raise_zero_division",
         "raise_validation", "raise_permission", "raise_keyerror"]

try:
    COMPANY = frappe.get_all("Company", pluck="name")[0]
    rec("company_used", COMPANY)
    err_before_all = frappe.db.count("Error Log")
    rec("error_log_count_at_start", err_before_all)

    from erpnext.accounts.doctype.financial_report_template.financial_report_engine import (
        FinancialReportEngine,
    )

    findings = {}

    for mode in MODES:
        MODE["mode"] = mode
        entry = {}
        try:
            frappe.local.message_log = []
            doc = frappe.get_doc({
                "doctype": "Financial Report Template",
                "template_name": "ZZ-PROBE-V30-Raise-" + mode,
                "report_type": "Profit and Loss Statement",
                "rows": [{
                    "data_source": "Custom API",
                    "display_name": "API Row",
                    "reference_code": "API_ROW",
                    "calculation_formula": INJ + ".maybe_raise",
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

            entry["execute_raised"] = False
            entry["error_log_delta"] = e_after - e_before
            entry["cells"] = {k: api_row.get(k) for k in pkeys} if api_row else None
            entry["n_period_columns"] = len(pkeys)
            entry["column_labels"] = [c.get("label") for c in cols]
            # every channel a user could possibly notice through
            entry["message_log"] = [str(m)[:200] for m in (frappe.local.message_log or [])]
            entry["n_messages"] = len(frappe.local.message_log or [])
            # newest Error Log row text, if one appeared
            if e_after > e_before:
                newest = frappe.get_all(
                    "Error Log", filters={"method": ["like", "%" + INJ + "%"]},
                    fields=["name", "method"], order_by="creation desc", limit=1)
                entry["error_log_method_text"] = (
                    newest[0]["method"][:220] if newest else None)

        except Exception as e:
            entry["execute_raised"] = True
            entry["exc_type"] = type(e).__name__
            entry["exc_msg"] = str(e)[:250]
            entry["tb_tail"] = traceback.format_exc()[-600:]
            frappe.clear_last_message()

        findings[mode] = entry
        print("  -> " + mode + ": raised=" + str(entry.get("execute_raised"))
              + " errlog_delta=" + str(entry.get("error_log_delta"))
              + " msgs=" + str(entry.get("n_messages")), flush=True)

    rec("mode_findings", findings)

    # ---------- DECISIVE for (c) ----------
    legit = findings.get("legit_zero", {})
    gen = findings.get("raise_generic", {})
    zdiv = findings.get("raise_zero_division", {})
    keyerr = findings.get("raise_keyerror", {})

    def cells_all_zero(e):
        c = e.get("cells")
        return (c is not None) and all(v == 0.0 for v in c.values())

    rec("DECISIVE_c", {
        "raise_generic_swallowed_report_still_returned":
            gen.get("execute_raised") is False,
        "raise_generic_wrote_error_log": gen.get("error_log_delta", 0) > 0,
        "raise_generic_cells_all_zero": cells_all_zero(gen),
        "raise_zero_division_swallowed": zdiv.get("execute_raised") is False,
        "raise_keyerror_swallowed": keyerr.get("execute_raised") is False,
        # the anti-ambiguity test: is a swallowed failure distinguishable from a real 0?
        "legit_zero_cells": legit.get("cells"),
        "raise_generic_cells": gen.get("cells"),
        "swallowed_failure_INDISTINGUISHABLE_from_legit_zero":
            legit.get("cells") == gen.get("cells"),
        "any_user_facing_message_on_failure": gen.get("n_messages"),
        "columns_unchanged_by_failure":
            gen.get("column_labels") == legit.get("column_labels"),
        "note": ("if INDISTINGUISHABLE is true and message count is 0, then 'no error "
                 "on screen' does not mean 'worked'"),
    })

    # frappe.throw raises ValidationError: does that one also get swallowed?
    rec("frappe_throw_and_permission_behaviour", {
        "raise_validation": findings.get("raise_validation", {}).get("execute_raised"),
        "raise_validation_errlog_delta":
            findings.get("raise_validation", {}).get("error_log_delta"),
        "raise_validation_cells_all_zero": cells_all_zero(findings.get("raise_validation", {})),
        "raise_permission": findings.get("raise_permission", {}).get("execute_raised"),
        "raise_permission_errlog_delta":
            findings.get("raise_permission", {}).get("error_log_delta"),
        "note": ("except Exception at :1192 catches ValidationError/PermissionError too, "
                 "since both subclass Exception"),
    })

except Exception as e:
    rec("probe_error", {"err": str(e), "tb": traceback.format_exc()[-3000:]})

finally:
    frappe.db.rollback()
    rec("probe_templates_left",
        frappe.get_all("Financial Report Template",
                       filters={"template_name": ["like", "ZZ-PROBE-V30%"]},
                       pluck="name"))

    # tabError Log is MyISAM: rollback does not remove rows. Delete ONLY rows whose
    # text names my injected module. Scoped positively so no other row can match.
    mine = frappe.get_all("Error Log", filters={"method": ["like", "%" + INJ + "%"]},
                          fields=["name", "method"])
    rec("error_log_rows_created_by_this_probe",
        [{"name": m["name"], "method": (m["method"] or "")[:110]} for m in mine])
    for m in mine:
        frappe.db.delete("Error Log", {"name": m["name"]})
    rec("my_error_log_rows_remaining",
        frappe.get_all("Error Log", filters={"method": ["like", "%" + INJ + "%"]},
                       pluck="name"))
    rec("error_log_count_final", frappe.db.count("Error Log"))
    rec("error_log_all_rows_final",
        [{"name": r.name, "method": (r.method or "")[:70]}
         for r in frappe.get_all("Error Log", fields=["name", "method"])])

    counts = {}
    for dt in ["GL Entry", "Stock Ledger Entry", "Account", "Company",
               "Financial Report Template", "Fiscal Year"]:
        counts[dt] = frappe.db.count(dt)
    rec("counts_after_rollback", counts)
    rec("fiscal_years_after_rollback", frappe.get_all("Fiscal Year", pluck="name"))

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)
    print("\nWROTE " + OUT, flush=True)
