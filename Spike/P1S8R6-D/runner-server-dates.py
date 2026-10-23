"""Native server-created document acceptance. Only adds named s8dev fixtures."""
import json
import os
from pathlib import Path

import frappe
from frappe.utils import add_days, getdate, today


def run():
	assert frappe.local.site == "s8dev.localhost"
	frappe.set_user("Administrator")
	fixture = json.loads(Path("/workspace/frappe-bench/logs/s8-ts019-fixture.json").read_text())
	refs = frappe.get_doc("Demo Progress", "Demo Progress").refs
	refs = json.loads(refs) if isinstance(refs, str) else refs
	day = fixture["selftest"]["dates"]["D1"]
	assert frappe.db.get_single_value("Demo Progress", "active", cache=False)
	assert str(frappe.db.get_single_value("Demo Progress", "scene_date", cache=False)) == day
	results = {}

	from erpnext.buying.doctype.purchase_order.purchase_order import make_purchase_receipt
	receipt = make_purchase_receipt(refs["purchase_order"])
	receipt.posting_date = today()
	receipt.insert()
	assert str(receipt.posting_date) == day
	assert receipt.set_posting_time == 1
	results["server_receipt"] = {"name": receipt.name, "date": receipt.posting_date, "flag": receipt.set_posting_time}

	request = frappe.get_doc({"doctype": "Material Request", "company": fixture["company"],
		"material_request_type": "Purchase", "transaction_date": today(),
		"schedule_date": add_days(day, 7), "items": [{"item_code": fixture["material"],
		"qty": 1, "warehouse": fixture["warehouse"], "schedule_date": add_days(day, 7)}]})
	request.insert()
	request.submit()
	assert str(request.transaction_date) == day
	from erpnext.stock.doctype.material_request.material_request import make_purchase_order
	order = make_purchase_order(request.name, args={"supplier": fixture["supplier"]})
	order.transaction_date = today()
	order.insert()
	assert str(order.transaction_date) == day
	results["request_order"] = {"request": request.name, "name": order.name, "date": order.transaction_date}

	plan = frappe.get_doc({"doctype": "Production Plan", "company": fixture["company"],
		"posting_date": today(), "get_items_from": "Sales Order", "sales_orders": [{"sales_order": refs["sales_order"]}]})
	plan.get_items()
	assert plan.po_items
	for row in plan.po_items:
		row.planned_start_date = f"{today()} 08:30:00"
	plan.insert()
	plan.submit()
	assert str(plan.posting_date) == day
	plan.make_work_order()
	work_orders = frappe.get_all("Work Order", filters={"production_plan": plan.name}, pluck="name")
	assert work_orders
	results["manufacturing"] = {"plan": plan.name, "orders": []}
	for name in work_orders:
		work_order = frappe.get_doc("Work Order", name)
		assert getdate(work_order.planned_start_date) == getdate(day)
		work_order.submit()
		cards = frappe.get_all("Job Card", filters={"work_order": name}, fields=["name", "posting_date"])
		assert cards
		assert all(getdate(card.posting_date) == getdate(day) for card in cards)
		results["manufacturing"]["orders"].append({"name": name, "date": work_order.planned_start_date, "cards": cards})
	frappe.db.commit()
	Path("/workspace/frappe-bench/logs/s8-ts019-server-dates.json").write_text(json.dumps(results, ensure_ascii=False, indent=2, default=str))
	print(json.dumps(results, ensure_ascii=False, default=str))


if __name__ == "__main__":
	os.chdir("/workspace/frappe-bench/sites")
	frappe.init(site="s8dev.localhost", sites_path="/workspace/frappe-bench/sites")
	frappe.connect()
	try:
		run()
	finally:
		frappe.destroy()
