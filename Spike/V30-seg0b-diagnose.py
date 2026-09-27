# V-30 seg0b: WHY did the Error Log row survive rollback in seg0?
#
# seg0 found: frappe.log_error() inserted a row (count 2 -> 3) and frappe.db.rollback()
# did NOT remove it (still 3). That blocks sub-question (c) under site-safety rule 2
# until the mechanism is understood, because "rollback protects the site" is the
# assumption every other probe in this spike rests on.
#
# Experiment: patch frappe.db.commit to a RECORDING NO-OP before calling log_error.
#   - If the row now rolls back cleanly -> an explicit commit() on the log_error path
#     was the cause, and the captured traceback names the caller.
#   - If the row still survives -> the write bypasses this connection/transaction
#     entirely (separate connection, autocommit, or deferred flush).
# Patching commit to a no-op is itself the conservative choice: it can only leave
# writes UNcommitted, never commit more.
#
# Also identifies WHICH Error Log rows exist, to rule out the alternative reading
# that rollback worked and some unrelated row appeared.
#
# Run (cwd MUST be .../sites, else frappe's logger dies on a relative path):
#   docker exec -i -w /workspace/frappe-bench/sites erx001-frappe-1 \
#     /workspace/frappe-bench/env/bin/python /workspace/Spike/V30-seg0b-diagnose.py

import json
import traceback

import frappe

SITE = "erx.localhost"
OUT = "/workspace/Spike/V30-out/seg0b-diagnose.json"
MARK = "V30 seg0b diagnose -- commit patched to no-op"

result = {"probe": "V-30 seg0b: why log_error survived rollback"}


def rec(k, v):
    result[k] = v
    print("[" + k + "] " + json.dumps(v, ensure_ascii=False, default=str)[:2500], flush=True)


frappe.init(site=SITE)
frappe.connect()
frappe.set_user("Administrator")

orig_commit = frappe.db.commit
commit_calls = []

try:
    # ---------- who is already in there? (identify seg0's survivor) ----------
    def snap():
        return [
            {"name": r.name, "method": (r.method or "")[:70], "creation": str(r.creation)}
            for r in frappe.get_all(
                "Error Log", fields=["name", "method", "creation"],
                order_by="creation desc", limit=8)
        ]

    rec("error_log_rows_at_start", snap())
    baseline = frappe.db.count("Error Log")
    rec("baseline_count", baseline)

    # is autocommit on? is there an independent connection?
    rec("db_engine", frappe.db.db_type)
    rec("auto_commit_on_many_writes", getattr(frappe.db, "auto_commit_on_many_writes", None))
    rec("transaction_writes_at_start", getattr(frappe.db, "transaction_writes", None))

    # ---------- patch commit to a recording no-op ----------
    def fake_commit(*args, **kwargs):
        commit_calls.append(traceback.format_stack()[-12:-1])
        return None

    frappe.db.commit = fake_commit

    frappe.log_error(MARK)

    after = frappe.db.count("Error Log")
    rec("count_after_log_error_with_commit_noop", {
        "count": after, "delta": after - baseline})
    rec("n_commit_calls_intercepted", len(commit_calls))
    rec("commit_call_stacks", ["".join(s)[-1400:] for s in commit_calls])
    rec("transaction_writes_after_insert", getattr(frappe.db, "transaction_writes", None))

    # ---------- now roll back with commit still neutered ----------
    frappe.db.rollback()
    after_rb = frappe.db.count("Error Log")
    rec("count_after_rollback_with_commit_noop", {
        "count": after_rb, "delta_vs_baseline": after_rb - baseline})
    rec("DIAGNOSIS_rollback_works_when_commit_suppressed", after_rb == baseline)
    rec("my_marker_row_survived",
        bool(frappe.db.exists("Error Log", {"method": ["like", "%V30 seg0b%"]})))
    rec("error_log_rows_after_rollback", snap())

    rec("INTERPRETATION", (
        "rollback clean + commit intercepted => an explicit commit() on the log_error "
        "path caused seg0's survivor; see commit_call_stacks for the caller"
        if after_rb == baseline else
        "row survived even with commit suppressed => write bypasses this transaction "
        "(separate connection / autocommit / deferred flush)"))

except Exception as e:
    rec("probe_error", {"err": str(e), "tb": traceback.format_exc()[-2500:]})

finally:
    frappe.db.commit = orig_commit
    frappe.db.rollback()
    rec("final_error_log_count", frappe.db.count("Error Log"))
    counts = {}
    for dt in ["GL Entry", "Stock Ledger Entry", "Account", "Company",
               "Financial Report Template", "Fiscal Year"]:
        counts[dt] = frappe.db.count(dt)
    rec("business_data_counts", counts)

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)
    print("\nWROTE " + OUT, flush=True)
