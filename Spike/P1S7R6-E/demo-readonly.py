"""E: read-only snapshot of erx.localhost (no writes)."""
import json

import frappe

from frappe_china.install import check_app_order

assert frappe.local.site == "erx.localhost"
r = check_app_order()
out = {
	"check_ok": r["ok"], "problems": r["problems"], "order": r["order"],
	"auto_indent": frappe.db.get_single_value("Stock Settings", "auto_indent"),
	"piece_component": bool(frappe.db.exists("Salary Component", "计件工资")),
	"modules": [m for m in ("Stock Plus", "Production Plus") if frappe.db.exists("Module Def", m)],
	"sidebars": {s: len(frappe.get_doc("Workspace Sidebar", s).items) for s in ("Stock Plus", "Production Plus") if frappe.db.exists("Workspace Sidebar", s)},
	"companies": frappe.get_all("Company", pluck="name"),
	"accounts": frappe.db.count("Account"),
	"translation": frappe.db.count("Translation"),
	"scheduler_disabled": frappe.utils.scheduler.is_scheduler_disabled(),
}
for dt in ("GL Entry", "Stock Ledger Entry", "Customer", "Supplier", "Item", "Sales Invoice", "Purchase Invoice", "Journal Entry",
	"Payment Entry", "Stock Entry", "Work Order", "Job Card", "Material Request", "Replenishment Suggestion", "Piece Rate Summary"):
	out[dt] = frappe.db.count(dt)
print(json.dumps(out, ensure_ascii=False, default=str))
