# V-30 probe (e), addendum: is a BAD api_path loud or silent?
#
# This completes the failure-mode map. get_valid_api_method is called at
# financial_report_engine.py:1181 -- OUTSIDE the try that begins at :1183. So a path
# that is missing / not whitelisted / POST-only should throw out of execute() rather
# than be swallowed into the silent zero. That distinction decides what "Custom API
# failed" actually looks like to a user, which is the practical half of the question
# "is this outlet safe to rely on".
#
# Also checks whether Financial Report Template.validate() (via TemplateValidator ->
# _validate_custom_api, financial_report_validation.py:525-552) blocks a bad path at
# SAVE time -- i.e. whether the bad path can even be persisted.
#
# ZERO FILESYSTEM TRACE: sys.modules injection only.
# SITE SAFETY: transaction + rollback, no commit, `module` left EMPTY.
# Error Log cleanup positively scoped to rows naming my injected module.
#
# Run (cwd MUST be .../sites, else frappe's logger dies on a relative path):
#   docker exec -i -w /workspace/frappe-bench/sites erx001-frappe-1 \
#     /workspace/frappe-bench/env/bin/python /workspace/Spike/V30-seg5-badpath.py

import json
import sys
import traceback
import types

import frappe

SITE = "erx.localhost"
OUT = "/workspace/Spike/V30-out/e-bad-path.json"
INJ = "erpnext.zz_v30_bad_inj"

result = {"probe": "V-30 (e) bad api_path: loud throw vs silent zero"}


def rec(k, v):
    result[k] = v
    print("[" + k + "] " + json.dumps(v, ensure_ascii=False, default=str)[:2200], flush=True)


frappe.init(site=SITE)
frappe.connect()
frappe.set_user("Administrator")


@frappe.whitelist(methods=["GET"])
def good(filters=None, periods=None, row=None):
    return [7.0] * (len(periods) if periods else 0)


@frappe.whitelist(methods=["POST"])
def post_only(filters=None, periods=None, row=None):
    return [8.0] * (len(periods) if periods else 0)


def not_whitelisted(filters=None, periods=None, row=None):
    return [9.0] * (len(periods) if periods else 0)


inj = types.ModuleType(INJ)
inj.good = good
inj.post_only = post_only
inj.not_whitelisted = not_whitelisted
sys.modules[INJ] = inj

CASES = {
    "good_GET": INJ + ".good",
    "post_only": INJ + ".post_only",
    "not_whitelisted": INJ + ".not_whitelisted",
    "missing_attribute": INJ + ".nope_does_not_exist",
    "uninstalled_app": "no_such_app.mod.meth",
    "no_dot_at_all": "garbage",
}

try:
    COMPANY = frappe.get_all("Company", pluck="name")[0]
    rec("company_used", COMPANY)
    rec("error_log_count_at_start", frappe.db.count("Error Log"))

    from erpnext.accounts.doctype.financial_report_template.financial_report_engine import (
        FinancialReportEngine,
    )

    findings = {}
    for tag, path in CASES.items():
        entry = {"api_path": path}
        # ---- does validate() block it at SAVE time? ----
        try:
            doc = frappe.get_doc({
                "doctype": "Financial Report Template",
                "template_name": "ZZ-PROBE-V30-Bad-" + tag,
                "report_type": "Profit and Loss Statement",
                "rows": [{
                    "data_source": "Custom API", "display_name": "API Row",
                    "reference_code": "API_ROW", "calculation_formula": path,
                    "fieldtype": "Currency",
                }],
            })
            doc.insert(ignore_permissions=True)
            entry["save_blocked"] = False
        except Exception as e:
            entry["save_blocked"] = True
            entry["save_exc_type"] = type(e).__name__
            entry["save_exc_msg"] = str(e)[:250]
            frappe.clear_last_message()
            findings[tag] = entry
            print("  -> " + tag + ": SAVE BLOCKED (" + entry["save_exc_type"] + ")",
                  flush=True)
            continue

        # ---- if it saved, what does execute() do? ----
        try:
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
            entry["cells_sample"] = ({k: api_row.get(k) for k in pkeys[:3]}
                                     if api_row else None)
            entry["all_cells_zero"] = (
                all(v == 0.0 for v in {k: api_row.get(k) for k in pkeys}.values())
                if api_row else None)
        except Exception as e:
            entry["execute_raised"] = True
            entry["exc_type"] = type(e).__name__
            entry["exc_msg"] = str(e)[:250]
            frappe.clear_last_message()

        findings[tag] = entry
        print("  -> " + tag + ": saved, execute_raised="
              + str(entry.get("execute_raised")) + " exc="
              + str(entry.get("exc_type")), flush=True)

    rec("findings", findings)

    rec("DECISIVE_e", {
        tag: {
            "save_blocked": e.get("save_blocked"),
            "execute_raised": e.get("execute_raised"),
            "exc_type": e.get("exc_type") or e.get("save_exc_type"),
            "silently_zeroed": (e.get("execute_raised") is False
                                and e.get("all_cells_zero") is True),
        }
        for tag, e in findings.items()
    })
    rec("interpretation", {
        "resolution_failures_are_loud_not_silent": all(
            (e.get("save_blocked") or e.get("execute_raised"))
            for tag, e in findings.items() if tag != "good_GET"),
        "reason": ("get_valid_api_method runs at engine.py:1181, outside the try at "
                   ":1183, so a bad PATH cannot reach the silent-zero handler; only an "
                   "exception raised INSIDE the call can"),
    })

except Exception as e:
    rec("probe_error", {"err": str(e), "tb": traceback.format_exc()[-3000:]})

finally:
    frappe.db.rollback()
    rec("probe_templates_left",
        frappe.get_all("Financial Report Template",
                       filters={"template_name": ["like", "ZZ-PROBE-V30%"]},
                       pluck="name"))
    mine = frappe.get_all("Error Log", filters={"method": ["like", "%" + INJ + "%"]},
                          fields=["name", "method"])
    rec("error_log_rows_created_by_this_probe",
        [{"name": m["name"], "method": (m["method"] or "")[:110]} for m in mine])
    for m in mine:
        frappe.db.delete("Error Log", {"name": m["name"]})
    rec("error_log_count_final", frappe.db.count("Error Log"))
    counts = {}
    for dt in ["GL Entry", "Stock Ledger Entry", "Account", "Company",
               "Financial Report Template", "Fiscal Year"]:
        counts[dt] = frappe.db.count(dt)
    rec("counts_after_rollback", counts)

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)
    print("\nWROTE " + OUT, flush=True)
