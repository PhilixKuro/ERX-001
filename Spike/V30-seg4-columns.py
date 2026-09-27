# V-30 probe (d): can ANYTHING a Custom API method does influence the NUMBER or the
# NAMES of the report's columns?
#
# This is the core of proposition V-30. The brief warns of a specific trap:
# "column labels did not change" could mean (i) the mechanism cannot change them, or
# (ii) my particular return shape merely did not happen to. Probe (b) already showed
# 13 different return shapes all leaving the 16 columns identical -- but that alone
# cannot rule out (ii), because it does not prove the harness would NOTICE a change.
#
# So this probe carries a POSITIVE CONTROL. Structural facts found by reading:
#   - engine.py:1185 passes `periods=self.period_list` and `filters=self.context.filters`
#     BY REFERENCE -- not copies.
#   - engine.py:221-222: process_calculations() (which calls the API) runs BEFORE
#     format_report_data() (which builds columns).
#   - DataFormatter._generate_columns() (:1414-1424) reads self.context.period_list and
#     self.context.filters, the very same objects, and financial_statements.py:702-711
#     builds one column per period from period.key / period.label.
# Therefore a method that MUTATES `periods` in place should be able to move the columns.
# If it does, the harness demonstrably detects column changes, so the return-value
# result is a real negative, not a blind instrument. Two channels, reported separately:
#     RETURN-VALUE channel  -- what data_source "Custom API" is contracted to use
#     MUTATION channel      -- an unintended side-effect path, tested to calibrate
#
# ZERO FILESYSTEM TRACE: method injected via sys.modules (proven equivalent in probe a).
# Mutations touch only in-memory objects (a list of frappe._dict built fresh per run by
# get_period_list, and the filters _dict this probe constructs per run). No DB write.
#
# SITE SAFETY: templates inserted in a transaction and rolled back; no frappe.db.commit();
# `module` left EMPTY so _export_template() returns early (financial_report_template.py:62).
# tabError Log is MyISAM = non-transactional (V30-seg0c), so Error Log rows do not roll
# back; cleanup is POSITIVELY scoped to rows naming my injected module.
#
# Run (cwd MUST be .../sites, else frappe's logger dies on a relative path):
#   docker exec -i -w /workspace/frappe-bench/sites erx001-frappe-1 \
#     /workspace/frappe-bench/env/bin/python /workspace/Spike/V30-seg4-columns.py

import json
import sys
import traceback
import types

import frappe

SITE = "erx.localhost"
OUT = "/workspace/Spike/V30-out/d-column-control.json"
INJ = "erpnext.zz_v30_cols_inj"

result = {"probe": "V-30 (d) can Custom API influence column count or labels?"}


def rec(k, v):
    result[k] = v
    print("[" + k + "] " + json.dumps(v, ensure_ascii=False, default=str)[:2400], flush=True)


frappe.init(site=SITE)
frappe.connect()
frappe.set_user("Administrator")

MODE = {"mode": "baseline"}
SEEN = {}


@frappe.whitelist(methods=["GET"])
def col_probe(filters=None, periods=None, row=None):
    """Each mode attempts a different route to the column axis."""
    m = MODE["mode"]
    n = len(periods) if periods else 0

    # ---------------- RETURN-VALUE channel ----------------
    if m == "baseline":
        return [10.0] * n
    if m == "return_dict_with_columns_key":
        # the shape someone would try if they believed the return could define columns
        return {"columns": [{"label": "NIANCHU YUE", "fieldname": "custom_a"},
                            {"label": "QIMO YUE", "fieldname": "custom_b"}],
                "values": [1.0, 2.0]}
        # (dict returns crash later at :1673 per probe (b); captured here for the record)
    if m == "return_two_values_for_two_wanted_columns":
        # "I want exactly 2 columns" expressed the only way the contract allows
        return [111.0, 222.0]

    # ---------------- MUTATION channel (positive control) ----------------
    if m == "mutate_period_label":
        SEEN["labels_before"] = [p["label"] for p in periods]
        periods[0]["label"] = "NIANCHU YUE E"     # ASCII stand-in for a statutory header
        periods[1]["label"] = "QIMO YUE E"
        SEEN["labels_after"] = [p["label"] for p in periods]
        return [20.0] * n
    if m == "mutate_append_period":
        SEEN["len_before"] = len(periods)
        base = dict(periods[-1])
        base["key"] = "zz_extra_col"
        base["label"] = "EXTRA COLUMN"
        periods.append(frappe._dict(base))
        SEEN["len_after"] = len(periods)
        return [30.0] * len(periods)
    if m == "mutate_truncate_periods":
        SEEN["len_before"] = len(periods)
        del periods[2:]                            # keep only 2 periods
        SEEN["len_after"] = len(periods)
        return [40.0] * len(periods)
    if m == "mutate_filters_periodicity":
        SEEN["periodicity_before"] = filters.get("periodicity")
        filters["periodicity"] = "Yearly"
        SEEN["periodicity_after"] = filters.get("periodicity")
        return [50.0] * n
    if m == "mutate_row_display_name":
        row.display_name = "MUTATED ROW NAME"
        return [60.0] * n
    return [0.0] * n


inj = types.ModuleType(INJ)
inj.col_probe = col_probe
sys.modules[INJ] = inj

RETURN_MODES = ["baseline", "return_dict_with_columns_key",
                "return_two_values_for_two_wanted_columns"]
MUTATION_MODES = ["mutate_period_label", "mutate_append_period",
                  "mutate_truncate_periods", "mutate_filters_periodicity",
                  "mutate_row_display_name"]

try:
    COMPANY = frappe.get_all("Company", pluck="name")[0]
    rec("company_used", COMPANY)
    rec("error_log_count_at_start", frappe.db.count("Error Log"))

    from erpnext.accounts.doctype.financial_report_template.financial_report_engine import (
        FinancialReportEngine,
    )

    findings = {}

    for mode in RETURN_MODES + MUTATION_MODES:
        MODE["mode"] = mode
        SEEN.clear()
        entry = {"channel": "return-value" if mode in RETURN_MODES else "mutation"}
        try:
            doc = frappe.get_doc({
                "doctype": "Financial Report Template",
                "template_name": "ZZ-PROBE-V30-Col-" + mode,
                "report_type": "Profit and Loss Statement",
                "rows": [{
                    "data_source": "Custom API",
                    "display_name": "API Row",
                    "reference_code": "API_ROW",
                    "calculation_formula": INJ + ".col_probe",
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

            entry["execute_raised"] = False
            entry["error_log_delta"] = e_after - e_before
            entry["n_columns_total"] = len(cols)
            entry["column_fieldnames"] = [c.get("fieldname") for c in cols]
            entry["column_labels"] = [c.get("label") for c in cols]
            entry["method_side_observations"] = dict(SEEN)
            api_row = None
            for r in data:
                if r.get("account_name") == "API Row":
                    api_row = r
            if api_row:
                entry["row_account_name_delivered"] = api_row.get("account_name")
        except Exception as e:
            entry["execute_raised"] = True
            entry["exc_type"] = type(e).__name__
            entry["exc_msg"] = str(e)[:200]
            entry["method_side_observations"] = dict(SEEN)
            frappe.clear_last_message()

        findings[mode] = entry
        print("  -> " + mode + " [" + entry["channel"] + "]: ncols="
              + str(entry.get("n_columns_total")) + " raised="
              + str(entry.get("execute_raised")), flush=True)

    rec("mode_findings", findings)

    base = findings.get("baseline", {})
    base_labels = base.get("column_labels")
    base_n = base.get("n_columns_total")
    rec("baseline_columns", {"n": base_n, "labels": base_labels})

    # ---------- DECISIVE (d) part 1: the RETURN-VALUE channel ----------
    ret = {}
    for m in RETURN_MODES:
        e = findings[m]
        ret[m] = {
            "raised": e.get("execute_raised"),
            "n_columns": e.get("n_columns_total"),
            "labels_equal_baseline": e.get("column_labels") == base_labels,
            "n_equal_baseline": e.get("n_columns_total") == base_n,
        }
    rec("DECISIVE_d_return_value_channel", ret)
    rec("return_value_ever_changed_columns",
        any((e.get("n_columns_total") is not None
             and (e.get("n_columns_total") != base_n
                  or e.get("column_labels") != base_labels))
            for m, e in findings.items() if m in RETURN_MODES))

    # ---------- DECISIVE (d) part 2: the MUTATION channel (positive control) ----------
    mut = {}
    for m in MUTATION_MODES:
        e = findings[m]
        mut[m] = {
            "raised": e.get("execute_raised"),
            "n_columns": e.get("n_columns_total"),
            "n_changed_vs_baseline": (e.get("n_columns_total") != base_n
                                      if e.get("n_columns_total") is not None else None),
            "labels_changed_vs_baseline": (e.get("column_labels") != base_labels
                                           if e.get("column_labels") is not None else None),
            "labels": e.get("column_labels"),
            "method_saw": e.get("method_side_observations"),
        }
    rec("DECISIVE_d_mutation_channel", mut)

    any_mut_changed = any(
        (v.get("n_changed_vs_baseline") or v.get("labels_changed_vs_baseline"))
        for v in mut.values())
    rec("mutation_channel_moved_columns", any_mut_changed)

    # ---------- the anti-ambiguity statement ----------
    rec("HARNESS_CALIBRATION", {
        "harness_can_detect_column_changes": any_mut_changed,
        "meaning": ("if True, then 'return value never changed columns' is a REAL "
                    "negative about the return-value channel -- the instrument is "
                    "demonstrably sensitive to column changes, so the null result "
                    "cannot be blamed on a blind harness"),
        "return_value_channel_result": "no column change in any shape tested",
        "mutation_channel_result": ("columns DID move" if any_mut_changed
                                    else "columns did not move either"),
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
    rec("my_error_log_rows_remaining",
        frappe.get_all("Error Log", filters={"method": ["like", "%" + INJ + "%"]},
                       pluck="name"))
    rec("error_log_count_final", frappe.db.count("Error Log"))

    counts = {}
    for dt in ["GL Entry", "Stock Ledger Entry", "Account", "Company",
               "Financial Report Template", "Fiscal Year"]:
        counts[dt] = frappe.db.count(dt)
    rec("counts_after_rollback", counts)
    rec("fiscal_years_after_rollback", frappe.get_all("Fiscal Year", pluck="name"))

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)
    print("\nWROTE " + OUT, flush=True)
