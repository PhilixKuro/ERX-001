import json
import os
from pathlib import Path

import frappe
from frappe_china.install import check_app_order

doctypes = ["GL Entry", "Stock Ledger Entry", "Customer", "Supplier", "Item", "Sales Invoice", "Purchase Invoice",
            "Sales Order", "Purchase Order", "Delivery Note", "Purchase Receipt", "Stock Entry", "Journal Entry",
            "Payment Entry", "Work Order", "Job Card", "Replenishment Suggestion", "Piece Rate Summary", "Translation"]
state = {"site": frappe.local.site, "companies": frappe.get_all("Company", pluck="name"),
         "items": frappe.get_all("Item", fields=["name", "creation", "owner", "modified"]),
         "accounts": frappe.db.count("Account"), "counts": {dt: frappe.db.count(dt) if frappe.db.exists("DocType", dt) else None for dt in doctypes},
         "app_order": check_app_order(), "auto_indent": frappe.db.get_single_value("Stock Settings", "auto_indent"),
         "salary_component": frappe.db.exists("Salary Component", "计件工资") if frappe.db.exists("DocType", "Salary Component") else None,
         "sidebars": {name: frappe.db.count("Workspace Sidebar Item", {"parent": name}) for name in ("Stock Plus", "Production Plus")},
         "error_logs": frappe.get_all("Error Log", fields=["name", "method"], order_by="creation")}
suffix = os.environ.get("S7_STATE_SUFFIX", "before")
path = Path("/workspace/Spike/P1S7R5-D") / f"s7-{frappe.local.site}-{suffix}.json"
path.write_text(json.dumps(state, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
print(json.dumps(state, ensure_ascii=False, default=str))
