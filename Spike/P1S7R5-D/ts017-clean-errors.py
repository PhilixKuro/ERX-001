"""Clean only inventoried browser verification failures after preserving their identities."""
import hashlib
import json
from pathlib import Path

import frappe

assert frappe.local.site == "erx.localhost"
root = Path("/workspace/Spike/P1S7R5-D")
rows = json.loads((root / "ts017-deferred-errors.json").read_text(encoding="utf-8"))
assert len(rows) == 47
old = [r for r in rows if r["creation"].startswith("2026-10-16 16:29:3")]
page = [r for r in rows if r["name"] == "rurh1i4cku" and r["method"] == "页面 spc-chart未找到"]
lock = [r for r in rows if r["creation"] == "2026-10-16 16:56:16.111149" and "bench_migrate.lock" in r["method"]]
assert len(old) == 45 and len(page) == 1 and len(lock) == 1
for row in rows:
    log = frappe.get_doc("Error Log", row["name"])
    assert log.method == row["method"]
    assert hashlib.sha256(log.error.encode()).hexdigest() == row["trace_sha256"]
    assert row["metadata"]["type"] == "http_request"
    frappe.delete_doc("Error Log", row["name"])
frappe.db.commit()
print("Removed exact 45 deferred historical browser errors, one page-registration check failure, and one overlapping-migrate lock record; manifest retained")
