"""E probe: SL-004 on real BOMs (select, no write-back, WO/SO/PP paths, manual, unchecked). Always rolled back."""
import json

import frappe
from frappe.utils import add_days, today

from frappe_china.production.bom_selection import select_bom

assert frappe.local.site == "test.localhost"
company = "_Test Company"
currency = frappe.db.get_value("Company", company, "default_currency")
tag = frappe.generate_hash(length=6)
out = {}


def item(code, rate=0, **kw):
	return frappe.get_doc({"doctype": "Item", "item_code": f"_FCT E {code} {tag}", "item_group": "Products",
		"stock_uom": "Nos", "is_stock_item": 1, "valuation_rate": rate, "include_item_in_manufacturing": 1,
		"default_bom": None, **kw}).insert()


def bom(fg, rm, rm_qty, quantity, loss, minutes, ws):
	b = frappe.get_doc({"doctype": "BOM", "item": fg, "company": company, "quantity": quantity, "currency": currency,
		"rm_cost_as_per": "Valuation Rate", "with_operations": 1, "process_loss_percentage": loss})
	b.append("items", {"item_code": rm, "qty": rm_qty})
	b.append("operations", {"operation": op.name, "workstation": ws, "time_in_mins": minutes})
	b.insert()
	b.submit()
	return b.name


try:
	customer = frappe.get_doc({"doctype": "Customer", "customer_name": "_FCT E Cust " + tag, "customer_group": frappe.db.get_value("Customer Group", {"is_group": 0}), "territory": frappe.db.get_value("Territory", {"is_group": 0})}).insert().name
	ws = frappe.get_doc({"doctype": "Workstation", "workstation_name": f"_FCT E WS {tag}"}).insert()
	frappe.db.set_value("Workstation", ws.name, "hour_rate", 60)
	op = frappe.get_doc({"doctype": "Operation", "name": f"_FCT E OP {tag}", "workstation": ws.name}).insert()
	fg = item("FG", cn_auto_select_bom=1)
	rm_a, rm_b = item("RMA", 1), item("RMB", 3)
	# unit costs: A=(1*10*1 + 60*60/60)/10/(1-0)=... computed below by hand
	b1 = bom(fg.name, rm_a.name, 10, 1, 0, 60, ws.name)      # (10 + 60)/1/1      = 70
	b2 = bom(fg.name, rm_b.name, 200, 20, 5, 120, ws.name)   # (600 + 120)/20/.95 = 37.894737
	b3 = bom(fg.name, rm_a.name, 300, 100, 2, 600, ws.name)  # (300 + 600)/100/.98= 9.183673
	out["0_native_defaults"] = [{b1: "B1", b2: "B2", b3: "B3"}.get(x, x) for x in __import__("frappe_china.production.bom_selection", fromlist=["x"]).default_boms(fg.name)]
	out["0_item_default_bom"] = {b1: "B1", b2: "B2", b3: "B3"}.get(frappe.db.get_value("Item", fg.name, "default_bom"))
	out["0_is_default"] = {k: frappe.db.get_value("BOM", v, "is_default") for k, v in (("B1", b1), ("B2", b2), ("B3", b3))}
	for n, v in ((b1, 1), (b2, 0), (b3, 0)):
		frappe.db.set_value("BOM", n, "is_default", v)
	frappe.db.set_value("Item", fg.name, "default_bom", b1)
	frappe.clear_cache()
	out["0b_native_defaults_after"] = [{b1: "B1", b2: "B2", b3: "B3"}.get(x, x) for x in __import__("frappe_china.production.bom_selection", fromlist=["x"]).default_boms(fg.name)]
	snap = lambda: {n: frappe.db.get_value("BOM", n, ["raw_material_cost", "operating_cost", "total_cost", "modified"], as_dict=True) for n in (b1, b2, b3)}
	before = snap()
	choice = select_bom(fg.name, company)
	out["1_candidates"] = [(c["bom"] == b1 and "B1" or c["bom"] == b2 and "B2" or "B3", c["unit_cost"]) for c in choice["candidates"]]
	out["1_selected_is_B3"] = choice["bom"] == b3
	out["2_bom_rows_unchanged"] = snap() == before
	frappe.db.set_value("Item", rm_a.name, "valuation_rate", 50)
	out["2_after_price_change_selected"] = {b1: "B1", b2: "B2", b3: "B3"}[select_bom(fg.name, company)["bom"]]
	frappe.db.set_value("Item", rm_a.name, "valuation_rate", 1)
	# 3: form-style WO with native default
	from erpnext.manufacturing.doctype.work_order.work_order import get_item_details
	wo = frappe.new_doc("Work Order")
	wo.update({"company": company, "production_item": fg.name, "qty": 10, "fg_warehouse": "Finished Goods - _TC",
		"wip_warehouse": "Work In Progress - _TC", "planned_start_date": frappe.utils.now_datetime()})
	wo.bom_no = get_item_details(fg.name).get("bom_no")
	out["3_native_default_is_B1"] = wo.bom_no == b1
	wo.get_items_and_operations_from_bom()
	wo.insert()
	out["3_wo_bom_is_B3"] = wo.bom_no == b3
	out["3_ops_bom"] = sorted({r.bom for r in wo.operations}) == [b3]
	out["3_items"] = sorted(r.item_code for r in wo.required_items) == [rm_a.name]
	out["3_comment"] = bool(frappe.get_all("Comment", filters={"reference_name": wo.name, "comment_type": "Comment"}))
	# 5: manual
	wo2 = frappe.new_doc("Work Order")
	wo2.update({"company": company, "production_item": fg.name, "qty": 10, "bom_no": b2, "fg_warehouse": "Finished Goods - _TC",
		"wip_warehouse": "Work In Progress - _TC", "planned_start_date": frappe.utils.now_datetime()})
	wo2.get_items_and_operations_from_bom()
	wo2.insert()
	c = frappe.get_all("Comment", filters={"reference_name": wo2.name}, pluck="content")
	out["5_manual_kept"] = wo2.bom_no == b2
	out["5_comment_has_manual"] = any("手动指定" in (x or "") or "Manually" in (x or "") for x in c)
	# 4a: sales order path
	from erpnext.selling.doctype.sales_order.sales_order import make_work_orders
	so = frappe.get_doc({"doctype": "Sales Order", "company": company, "customer": customer,
		"transaction_date": today(), "delivery_date": add_days(today(), 10), "currency": currency,
		"selling_price_list": "Standard Selling",
		"items": [{"item_code": fg.name, "qty": 5, "rate": 100, "warehouse": "Finished Goods - _TC", "delivery_date": add_days(today(), 10)}]})
	so.insert(); so.submit()
	from erpnext.selling.doctype.sales_order.sales_order import get_work_order_items
	items = get_work_order_items(so.name)
	out["4a_so_item_bom_offered"] = {b1: "B1", b2: "B2", b3: "B3"}.get(items[0].get("bom"), items[0].get("bom")) if items else None
	names = make_work_orders(json.dumps({"items": items}), so.name, company)
	out["4a_so_wo_bom"] = [{b1: "B1", b2: "B2", b3: "B3"}.get(frappe.db.get_value("Work Order", n, "bom_no")) for n in names]
	# 4b: production plan path
	pp = frappe.get_doc({"doctype": "Production Plan", "company": company, "get_items_from": "Sales Order",
		"posting_date": today(), "sales_orders": [{"sales_order": so.name}]})
	pp.get_items()
	out["4b_pp_rows"] = [(r.item_code == fg.name, r.bom_no) for r in pp.po_items]
	out["4b_pp_row_bom_before_save"] = {b1: "B1", b2: "B2", b3: "B3"}.get(pp.po_items[0].bom_no) if pp.po_items else None
	pp.save()
	pp.reload()
	out["4b_pp_row_bom_after_save"] = {b1: "B1", b2: "B2", b3: "B3"}.get(pp.po_items[0].bom_no)
	from erpnext.manufacturing.doctype.production_plan.production_plan import get_items_for_material_requests
	mr_items = get_items_for_material_requests(pp.as_dict())
	out["4b_mr_items"] = sorted({r.get("item_code") for r in mr_items}) == [rm_a.name]
	pp.submit()
	pp.make_work_order()
	out["4b_pp_wo_bom"] = [{b1: "B1", b2: "B2", b3: "B3"}.get(x) for x in frappe.get_all("Work Order", filters={"production_plan": pp.name}, pluck="bom_no")]
	# 6: unchecked
	frappe.db.set_value("Item", fg.name, "cn_auto_select_bom", 0)
	wo3 = frappe.new_doc("Work Order")
	wo3.update({"company": company, "production_item": fg.name, "qty": 10, "bom_no": b1, "fg_warehouse": "Finished Goods - _TC",
		"wip_warehouse": "Work In Progress - _TC", "planned_start_date": frappe.utils.now_datetime()})
	wo3.get_items_and_operations_from_bom()
	wo3.insert()
	out["6_unchecked_kept_B1"] = wo3.bom_no == b1
	out["6_no_comment"] = not frappe.get_all("Comment", filters={"reference_name": wo3.name, "comment_type": "Comment"})
	# 7
	frappe.db.set_value("Item", fg.name, "cn_auto_select_bom", 1)
	fg2 = item("FG2", cn_auto_select_bom=1)
	out["7_no_bom"] = select_bom(fg2.name, company)["bom"] is None
except Exception as error:
	out["ERROR"] = f"{type(error).__name__}: {str(error)[:400]}"
	out["TRACE"] = frappe.get_traceback()[-1500:]
finally:
	frappe.db.rollback()
	print(json.dumps(out, ensure_ascii=False, default=str, indent=1))
