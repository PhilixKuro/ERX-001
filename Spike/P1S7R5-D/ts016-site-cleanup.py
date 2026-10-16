import json
from pathlib import Path

import frappe

assert frappe.local.site == "test.localhost"
fixture = json.loads(Path("/workspace/Spike/P1S7R5-D/ts016-fixture.json").read_text(encoding="utf-8"))
assert fixture["prefix"].startswith("_FCT SPC ")
for name in fixture["inspections"]:
    assert name.startswith(fixture["prefix"])
    doc = frappe.get_doc("Quality Inspection", name)
    doc.cancel()
    frappe.delete_doc("Quality Inspection", name)
for dt, name in (("Stock Entry", fixture["entry"]), ("Item", fixture["item"]), ("Quality Inspection Parameter", fixture["parameter"])):
    assert name.startswith(fixture["prefix"])
    frappe.delete_doc(dt, name)
frappe.db.commit()
print("TS-016 fixture removed; no force or ignore_links used")
