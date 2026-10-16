"""Inventory only the first migration's deferred browser errors, without dumping trace locals."""
import hashlib
import json
from collections import Counter
from pathlib import Path

import frappe

assert frappe.local.site == "erx.localhost"
root = Path("/workspace/Spike/P1S7R5-D")
before = json.loads((root / "s7-erx.localhost-before.json").read_text(encoding="utf-8"))
baseline = {r["name"] for r in before["error_logs"]}
rows = []
for record in frappe.get_all("Error Log", fields=["name", "creation", "method"], order_by="creation"):
    if record.name in baseline:
        continue
    log = frappe.get_doc("Error Log", record.name)
    metadata = json.loads(log.metadata or "{}")
    rows.append({"name": record.name, "creation": str(record.creation), "method": record.method,
                 "metadata": metadata, "trace_sha256": hashlib.sha256(log.error.encode()).hexdigest()})
(root / "ts017-deferred-errors.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
print("count", len(rows))
print("paths", dict(Counter(r["metadata"].get("path") for r in rows)))
print("times", rows[0]["creation"], rows[-1]["creation"])
