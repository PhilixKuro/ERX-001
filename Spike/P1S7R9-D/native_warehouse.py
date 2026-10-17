"""V-01: native expanded raw input preserves warehouses and purchase conversion.

Run in frappe container from /workspace/frappe-bench/sites:
/workspace/frappe-bench/env/bin/python /workspace/Spike/P1S7R9-D/native_warehouse.py
"""

import json

import frappe
from erpnext.manufacturing.doctype.production_plan.production_plan import (
	get_exploded_items,
	get_items_for_material_requests,
)

frappe.init(site="test.localhost", sites_path="/workspace/frappe-bench/sites")
frappe.connect()
assert frappe.local.site == "test.localhost"
frappe.set_user("Administrator")
frappe.local.lang = "zh"
prefix = f"_FCT R9 Native {frappe.generate_hash(length=8)}"
company = "_Test Company"


def item(label, warehouse, **extra):
	return frappe.get_doc({
		"doctype": "Item", "item_code": f"{prefix} {label}",
		"item_group": "Products", "stock_uom": "Nos", "is_stock_item": 1,
		"item_defaults": [{"company": company, "default_warehouse": warehouse}], **extra,
	}).insert()


try:
	if not frappe.db.exists("UOM", "Box"):
		frappe.get_doc({"doctype": "UOM", "uom_name": "Box"}).insert()
	fg = item("FG", "Finished Goods - _TC")
	a = item("A", "Stores - _TC", purchase_uom="Box", uoms=[
		{"uom": "Nos", "conversion_factor": 1}, {"uom": "Box", "conversion_factor": 2},
	])
	b = item("B", "Work In Progress - _TC")
	missing = item("C", None)
	bom = frappe.get_doc({
		"doctype": "BOM", "item": fg.name, "company": company, "quantity": 1,
		"currency": frappe.db.get_value("Company", company, "default_currency"),
		"items": [{"item_code": a.name, "qty": 2}, {"item_code": b.name, "qty": 3},
			{"item_code": missing.name, "qty": 4}],
	}).insert()
	bom.submit()
	options = {"company": company, "ignore_existing_ordered_qty": 1,
		"include_subcontracted_items": 1, "include_non_stock_items": 0,
		"include_safety_stock": 0, "consider_minimum_order_qty": 0}
	native = get_items_for_material_requests({**options, "po_items": [
		{"item_code": fg.name, "bom_no": bom.name, "planned_qty": 5, "include_exploded_items": 1},
	]})
	details = get_exploded_items({}, company, bom.name, 0, planned_qty=5)
	assert details[a.name].qty == 10 and details[b.name].qty == 15
	assert not details[missing.name].default_warehouse
	groups = {}
	for code, detail in details.items():
		if detail.default_warehouse:
			groups.setdefault(detail.default_warehouse, []).append({
				"item_code": code, "required_qty": detail.qty, "include_exploded_items": 0,
			})
	grouped = [row for wh, rows in groups.items() for row in get_items_for_material_requests(
		{**options, "for_warehouse": wh, "po_items": rows})]
	actual = {row["item_code"]: (row["warehouse"], row["quantity"], row["conversion_factor"]) for row in grouped}
	assert actual[a.name] == ("Stores - _TC", 5, 2), actual
	assert actual[b.name] == ("Work In Progress - _TC", 15, 1), actual
	assert len({row["warehouse"] for row in native}) == 1, native
	assert missing.name not in actual
	print(json.dumps({"native": native, "grouped": grouped, "missing_default": missing.name}, ensure_ascii=False, default=str))
finally:
	frappe.db.rollback()
	leftover = frappe.db.count("Item", {"item_code": ["like", f"{prefix}%"]})
	print("rollback leftover items:", leftover)
	assert leftover == 0
	frappe.destroy()
