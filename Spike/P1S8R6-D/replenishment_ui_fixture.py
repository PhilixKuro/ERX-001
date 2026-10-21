"""Temporary SL-007 browser fixture, restricted to test.localhost."""
import json
from pathlib import Path

import frappe

SITE = "test.localhost"
COMPANY = "_Test Company"
WAREHOUSE = "Stores - _TC"
MANIFEST = Path("/workspace/frappe-bench/logs/s8-ts008-ui-fixture.json")

def create():
	assert frappe.local.site == SITE
	if MANIFEST.exists():
		raise RuntimeError("Clean the previous replenishment fixture first")
	company_before = frappe.db.get_value(
		"Company", COMPANY, ["cn_replenishment_enabled", "cn_service_level"], as_dict=True
	)
	item_code = f"_FCT SL007 UI {frappe.generate_hash(length=7)}"
	item = frappe.get_doc(
		{
			"doctype": "Item",
			"item_code": item_code,
			"item_group": "Products",
			"stock_uom": "Nos",
			"is_stock_item": 1,
			"valuation_rate": 10,
			"cn_auto_replenishment_params": 1,
			"lead_time_days": 7,
			"cn_service_level": 95,
			"safety_stock": 2,
			"reorder_levels": [{"warehouse": WAREHOUSE, "warehouse_reorder_level": 5, "warehouse_reorder_qty": 1}],
		}
	).insert(ignore_permissions=True)
	frappe.db.set_value("Company", COMPANY, "cn_replenishment_enabled", 1)
	manifest = {"site": SITE, "company": COMPANY, "item": item.name, "company_before": dict(company_before)}
	MANIFEST.write_text(json.dumps(manifest), encoding="utf-8")
	frappe.db.commit()
	return manifest


def cleanup():
	assert frappe.local.site == SITE
	manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
	item = manifest["item"]
	for name in frappe.get_all("Replenishment Suggestion", filters={"item_code": item}, pluck="name"):
		frappe.delete_doc("Replenishment Suggestion", name, ignore_permissions=True)
	if frappe.db.exists("Item", item):
		frappe.delete_doc("Item", item, ignore_permissions=True)
	frappe.db.set_value("Company", manifest["company"], manifest["company_before"])
	frappe.db.commit()
	MANIFEST.unlink()
	return {"site": SITE, "cleaned_item": item}
