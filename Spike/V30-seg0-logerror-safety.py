# V-30 seg0: SAFETY GATE for sub-question (c).
#
# Sub-question (c) requires deliberately raising inside a Custom API method so that
# financial_report_engine.py:1192-1194 runs `frappe.log_error(...)`. log_error INSERTS
# an `Error Log` document -- a real write. Site-safety rule 2 says: grep the path for
# frappe.db.commit() / frappe.enqueue and stop if either is reachable.
#
# Static findings that need empirical confirmation before (c) may run:
#   - frappe/utils/error.py, frappe/core/doctype/error_log/error_log.py: no commit on
#     the insert path (ErrorLog.onload has one, but onload is a UI-open path, not insert).
#   - An insert DOES run on_update (frappe/model/document.py:1453-1454), and frappe's
#     wildcard doc_events on_update list includes handlers that DO contain commit/enqueue:
#       * workflow_action.process_workflow_actions -- commit at :164 is in `confirm_action`
#         (an HTTP endpoint), NOT in the hook; the hook returns at :94-95 with no Workflow.
#       * assignment_rule.apply -- frappe.enqueue at :237, but :269-277 skips `log_types`.
#       * sqlite_search.update_doc_index -- returns at :1841-1842 unless search enabled;
#         its commits are on a separate sqlite connection, and the frappe.enqueue at
#         :1807 is in build_index, not update_doc_index.
#
# This script confirms each guard actually holds on THIS site, then proves empirically
# that an Error Log inserted inside a transaction is fully removed by rollback.
# If the count does not return to baseline, (c) must be reported as 无法判定 instead.
#
# Run (cwd MUST be .../sites, else frappe's logger dies on a relative path):
#   docker exec -i -w /workspace/frappe-bench/sites erx001-frappe-1 \
#     /workspace/frappe-bench/env/bin/python /workspace/Spike/V30-seg0-logerror-safety.py

import json
import traceback

import frappe

SITE = "erx.localhost"
OUT = "/workspace/Spike/V30-out/seg0-logerror-safety.json"

result = {"probe": "V-30 seg0 safety gate: is frappe.log_error rollback-safe here?"}


def rec(k, v):
    result[k] = v
    print("[" + k + "] " + json.dumps(v, ensure_ascii=False, default=str)[:2000], flush=True)


frappe.init(site=SITE)
frappe.connect()
frappe.set_user("Administrator")

baseline = None

try:
    baseline = frappe.db.count("Error Log")
    rec("error_log_baseline", baseline)

    # ---------- guard 1: Error Log is a log type => assignment_rule.apply skips ----------
    from frappe.model.document import Document  # noqa: F401

    # assignment_rule.py:10 imports it from frappe.model (defined at model/__init__.py:125)
    from frappe.model import log_types

    rec("log_types_contains_Error_Log", "Error Log" in list(log_types))
    rec("log_types_sample", sorted(list(log_types))[:20])

    # ---------- guard 2: no Workflow on Error Log => process_workflow_actions returns ----
    from frappe.model.workflow import get_workflow_name

    rec("workflow_name_for_Error_Log", get_workflow_name("Error Log"))
    rec("total_workflows_on_site", frappe.db.count("Workflow"))

    # ---------- guard 3: sqlite search disabled/no index => update_doc_index returns ----
    sqlite_state = {}
    try:
        from frappe.search.sqlite_search import get_search_classes

        classes = get_search_classes()
        sqlite_state["n_search_classes"] = len(classes)
        for cls in classes:
            s = cls()
            sqlite_state[cls.__name__] = {
                "is_search_enabled": bool(s.is_search_enabled()),
                "index_exists": bool(s.index_exists()),
            }
    except Exception as e:
        sqlite_state["probe_note"] = type(e).__name__ + ": " + str(e)[:200]
    rec("sqlite_search_state", sqlite_state)

    # ---------- guard 4: telemetry gates capture_exception (sentry.py:107) ----------
    rec("enable_telemetry", frappe.get_system_settings("enable_telemetry"))

    # ---------- the empirical test: does an Error Log insert roll back? ----------
    # This is the only claim that actually matters. Everything above is corroboration.
    frappe.log_error("V30 seg0 rollback probe -- expected to vanish on rollback")
    after_insert = frappe.db.count("Error Log")
    rec("error_log_after_log_error_call", {
        "count": after_insert,
        "delta_vs_baseline": after_insert - baseline,
        "note": "delta 1 means log_error really did insert (not deferred)",
    })

    # is anything pending that a rollback would NOT undo?
    rec("in_transaction_before_rollback", bool(frappe.db.transaction_writes))

except Exception as e:
    rec("probe_error", {"err": str(e), "tb": traceback.format_exc()[-2500:]})

finally:
    frappe.db.rollback()
    final = frappe.db.count("Error Log")
    rec("error_log_after_rollback", final)
    rec("GATE_rollback_is_clean", final == baseline)
    rec("GATE_verdict", "safe to run (c)" if final == baseline
        else "NOT SAFE -- report 无法判定 for (c)")

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)
    print("\nWROTE " + OUT, flush=True)
