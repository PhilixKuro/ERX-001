"""P1-S8-R3 SA V-04：以正常提交（出 GL／SLE）造「模拟日」全链单据，逐日计时。
一个模拟日＝一条完整链：销售订单 → 采购订单 → 采购收货 → 采购发票 → 付款 → 工单 → 发料 → 工序卡×3（带报工）
→ 过程检 → 完工入库 → 发货 → 销售发票 → 收款，共 15 张单据。
只在临时站 sa.localhost 跑；物料、BOM 用 SA- 前缀新建，与 R2 留下的单据隔离（不触发其物料的回溯重估）。
用法（容器内 bench 目录）：env/bin/python /workspace/Spike/P1S8R3-SA/V04-day-generator.py <起始日 YYYY-MM-DD> <天数> [<输出 jsonl>] [<每天几条链，缺省 1>]
每天一个事务、提交后打印一行 JSON：{date, seconds, docs}。"""
import json
import os
import sys
import time

import frappe
from frappe.utils import add_days, getdate

SITE = "sa.localhost"
COMPANY = "华东弹簧有限公司"
PREFIX = os.environ.get("SA_PREFIX", "SA-")  # 换前缀即换一套物料，免得新数据早于旧数据触发回溯重估
RAW, FG = PREFIX + "WIRE-65MN-2.0", PREFIX + "SPR-C-2.0-16-50"
SRC_BOM = "BOM-SPR-C-2.0-16-50-001"
WH_RAW, WH_WIP, WH_FG = "仓库 - HDTH", "进行中 - HDTH", "成品 - HDTH"
CUSTOMER, SUPPLIER = "江南机械", "宝钢弹簧钢丝"
EMPLOYEES = ["HR-EMP-00001", "HR-EMP-00002", "HR-EMP-00003"]
QTY = 500  # 每天一张 500 支的订单：一道工序一张卡（拆单阈值 2000）


def masters():
	if not frappe.db.exists("Item", RAW):
		frappe.get_doc({"doctype": "Item", "item_code": RAW, "item_name": RAW, "item_group": "Raw Material",
			"stock_uom": "Kg", "is_stock_item": 1, "valuation_rate": 7.5,
			"item_defaults": [{"company": COMPANY, "default_warehouse": WH_RAW}]}).insert()
	if not frappe.db.exists("Item", FG):
		frappe.get_doc({"doctype": "Item", "item_code": FG, "item_name": FG, "item_group": "Products",
			"stock_uom": "支", "is_stock_item": 1, "valuation_rate": 0.1, "has_batch_no": 1, "create_new_batch": 1,
			"batch_number_series": PREFIX.replace("-", "") + "SPR-.#####", "cn_unit_length_m": 0.352,
			"item_defaults": [{"company": COMPANY, "default_warehouse": WH_FG}]}).insert()
	bom = frappe.db.get_value("BOM", {"item": FG, "is_default": 1, "docstatus": 1})
	if not bom:
		src = frappe.get_doc("BOM", SRC_BOM)
		new = frappe.copy_doc(src)
		new.item = FG
		new.is_default = 1
		for row in new.items:
			row.item_code = RAW
			row.source_warehouse = WH_RAW
		new.insert()
		new.submit()
		bom = new.name
	if not frappe.db.exists("Fiscal Year", "2025"):  # 一年场景从 2025-10 起，跨两个会计年度
		frappe.get_doc({"doctype": "Fiscal Year", "year": "2025", "year_start_date": "2025-01-01",
			"year_end_date": "2025-12-31", "companies": [{"company": COMPANY}]}).insert()
	frappe.db.set_single_value("Manufacturing Settings", "disable_capacity_planning", 1)
	frappe.db.commit()
	return bom


def dated(doc, d, t="10:00:00"):
	if doc.meta.has_field("set_posting_time"):
		doc.set_posting_time = 1
	if doc.meta.has_field("posting_date"):
		doc.posting_date = d
	if doc.meta.has_field("posting_time"):
		doc.posting_time = t
	return doc


def one_day(d, bom):
	from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry
	from erpnext.buying.doctype.purchase_order.purchase_order import make_purchase_receipt
	from erpnext.manufacturing.doctype.work_order.work_order import make_stock_entry
	from erpnext.selling.doctype.sales_order.sales_order import make_delivery_note
	from erpnext.stock.doctype.delivery_note.delivery_note import make_sales_invoice
	from erpnext.stock.doctype.purchase_receipt.purchase_receipt import make_purchase_invoice

	docs = []

	def done(doc):
		doc.submit()
		docs.append(doc.doctype)
		return doc

	ds = str(d)
	so = frappe.get_doc({"doctype": "Sales Order", "company": COMPANY, "customer": CUSTOMER, "transaction_date": ds,
		"delivery_date": str(add_days(d, 7)), "currency": "CNY", "selling_price_list": "Standard Selling",
		"taxes_and_charges": "P13专票未税 - HDTH",
		"items": [{"item_code": FG, "qty": QTY, "rate": 0.22, "warehouse": WH_FG, "delivery_date": str(add_days(d, 7))}]})
	done(so.insert())
	po = frappe.get_doc({"doctype": "Purchase Order", "company": COMPANY, "supplier": SUPPLIER, "transaction_date": ds,
		"schedule_date": ds, "currency": "CNY", "buying_price_list": "Standard Buying",
		"taxes_and_charges": "P13专票未税 - HDTH",
		"items": [{"item_code": RAW, "qty": 5, "rate": 7.5, "schedule_date": ds, "warehouse": WH_RAW}]})
	done(po.insert())
	pr = done(dated(make_purchase_receipt(po.name), ds, "08:00:00").insert())
	pi = make_purchase_invoice(pr.name)
	pi = done(dated(pi, ds, "08:10:00").insert())
	pay = get_payment_entry("Purchase Invoice", pi.name)
	pay.posting_date = ds
	pay.reference_no, pay.reference_date = f"{PREFIX}P-{ds}-{po.name}", ds
	done(pay.insert())

	wo = frappe.get_doc({"doctype": "Work Order", "company": COMPANY, "production_item": FG, "bom_no": bom, "qty": QTY,
		"wip_warehouse": WH_WIP, "fg_warehouse": WH_FG, "source_warehouse": WH_RAW, "sales_order": so.name,
		"planned_start_date": f"{ds} 08:30:00"})
	wo.get_items_and_operations_from_bom()
	done(wo.insert())
	tr = frappe.get_doc(make_stock_entry(wo.name, "Material Transfer for Manufacture", QTY))
	done(dated(tr, ds, "08:40:00").insert())
	cards = frappe.get_all("Job Card", filters={"work_order": wo.name, "docstatus": 0}, pluck="name", order_by="sequence_id asc")
	hour = 9
	for i, name in enumerate(cards):
		card = frappe.get_doc("Job Card", name)
		if card.meta.has_field("posting_date"):
			card.posting_date = ds
		card.append("time_logs", {"employee": EMPLOYEES[i % 3], "from_time": f"{ds} {hour:02d}:00:00",
			"to_time": f"{ds} {hour:02d}:50:00", "completed_qty": card.for_quantity})
		hour += 1
		card.save()
		done(card)
		if i == len(cards) - 1:
			qi = frappe.get_doc({"doctype": "Quality Inspection", "inspection_type": "In Process", "reference_type": "Job Card",
				"reference_name": card.name, "item_code": FG, "sample_size": 5, "inspected_by": "Administrator",
				"report_date": ds, "status": "Accepted",
				"readings": [{"specification": "自由长度", "numeric": 1, "min_value": 49.5, "max_value": 50.5,
					**{f"reading_{k}": str(round(50 + (hash((ds, k)) % 9 - 4) / 20, 2)) for k in range(1, 6)}}]})
			done(qi.insert())
	mf = frappe.get_doc(make_stock_entry(wo.name, "Manufacture", QTY))
	for c in mf.additional_costs:
		c.expense_account = c.expense_account or "410199 - 制造费用-结转库存 - HDTH"
	done(dated(mf, ds, "13:00:00").insert())
	fin = next(r for r in mf.items if r.is_finished_item)
	batch, made_qty = fin.batch_no, fin.qty  # BOM 带损耗率，实际产出少于 QTY，按实际产出发货
	dn = make_delivery_note(so.name)
	for r in dn.items:
		r.batch_no = batch
		r.qty = made_qty
		r.use_serial_batch_fields = 1
	dn = done(dated(dn, ds, "15:00:00").insert())
	si = done(dated(make_sales_invoice(dn.name), ds, "15:10:00").insert())
	rec = get_payment_entry("Sales Invoice", si.name)
	rec.posting_date = ds
	rec.reference_no, rec.reference_date = f"{PREFIX}R-{ds}-{si.name}", ds
	done(rec.insert())
	return docs


def main():
	assert len(sys.argv) >= 3
	start, days = getdate(sys.argv[1]), int(sys.argv[2])
	out = open(sys.argv[3], "a", encoding="utf-8") if len(sys.argv) > 3 and sys.argv[3] != "-" else None
	chains = int(sys.argv[4]) if len(sys.argv) > 4 else 1
	os.chdir("/workspace/frappe-bench/sites")
	frappe.init(site=SITE, sites_path=".")
	frappe.connect()
	assert frappe.local.site == SITE
	frappe.set_user("Administrator")
	frappe.local.lang = "zh"
	try:
		bom = masters()
		d, made = start, 0
		while made < days:
			if d.weekday() < 6:  # 周日不开工
				t0 = time.monotonic()
				try:
					docs = [x for _ in range(chains) for x in one_day(d, bom)]
					frappe.db.commit()
					row = {"date": str(d), "seconds": round(time.monotonic() - t0, 2), "docs": len(docs)}
				except Exception as e:
					frappe.db.rollback()
					row = {"date": str(d), "error": f"{type(e).__name__}: {e}"[:500]}
					print(json.dumps(row, ensure_ascii=False), flush=True)
					raise
				line = json.dumps(row, ensure_ascii=False)
				print(line, flush=True)
				if out:
					out.write(line + "\n")
					out.flush()
				made += 1
			d = add_days(d, 1)
	finally:
		frappe.db.rollback()
		frappe.destroy()


if __name__ == "__main__":
	main()
