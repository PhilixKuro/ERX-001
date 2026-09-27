# V-30 pre-flight: record the site baseline BEFORE any write-bearing probe runs,
# and confirm the two environment facts the silent-zero probe depends on
# (telemetry off -> capture_exception is a no-op; developer_mode state).
#
# READ-ONLY. No inserts, no commit.
#
# Run (cwd MUST be .../sites, else frappe's logger dies on a relative path):
#   docker exec -i -w /workspace/frappe-bench/sites erx001-frappe-1 \
#     /workspace/frappe-bench/env/bin/python /workspace/Spike/V30-baseline.py

import json

import frappe

SITE = "erx.localhost"
OUT = "/workspace/Spike/V30-out/baseline-before.json"

result = {"probe": "V-30 baseline before probes"}


def rec(k, v):
    result[k] = v
    print("[" + k + "] " + json.dumps(v, ensure_ascii=False, default=str)[:2000], flush=True)


frappe.init(site=SITE)
frappe.connect()
frappe.set_user("Administrator")

try:
    counts = {}
    for dt in ["GL Entry", "Stock Ledger Entry", "Account", "Company",
               "Financial Report Template", "Fiscal Year", "Error Log"]:
        counts[dt] = frappe.db.count(dt)
    rec("counts", counts)
    rec("fiscal_years", [r.name for r in frappe.get_all("Fiscal Year", fields=["name"])])
    rec("templates", [r.name for r in frappe.get_all("Financial Report Template", fields=["name"])])

    # telemetry gates capture_exception (frappe/utils/sentry.py:107) -- if off, the
    # silent-zero path does nothing but insert an Error Log row inside our transaction.
    rec("enable_telemetry", frappe.get_system_settings("enable_telemetry"))
    rec("developer_mode", bool(frappe.conf.developer_mode))
    rec("read_only_flag", bool(frappe.flags.read_only))
    rec("in_request", bool(frappe.request))

finally:
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)
    print("\nWROTE " + OUT, flush=True)
