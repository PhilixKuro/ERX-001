"""P1-S8-R3 SA V-05：生产计划 planned_qty=5264、挂 5000 支销售订单、overproduction_percentage_for_sales_order=0，
由生产计划生成工单（make_work_order）时是否被 validate_work_order_against_so 拦下；分别看「建草稿」与「提交」两段。
只在 sa.localhost 跑，全程 rollback 不落库。
用法（容器内 bench 目录）：env/bin/python /workspace/Spike/P1S8R3-SA/V05-pp-overproduction.py"""
import json
import os

import frappe
from frappe.utils import add_days, nowdate

COMPANY = "华东弹簧有限公司"
FG = "Y1-SPR-C-2.0-16-50"  # V-04 生成器造的物料（库存与 BOM 已就位）
WH_FG, WH_WIP, WH_RAW = "成品 - HDTH", "进行中 - HDTH", "仓库 - HDTH"


def out(k, v):
	print(json.dumps({k: v}, ensure_ascii=False, default=str), flush=True)


def main():
	os.chdir("/workspace/frappe-bench/sites")
	frappe.init(site="sa.localhost", sites_path=".")
	frappe.connect()
	assert frappe.local.site == "sa.localhost"
	frappe.set_user("Administrator")
	frappe.local.lang = "en"
	try:
		out("setting", frappe.db.get_single_value("Manufacturing Settings", "overproduction_percentage_for_sales_order"))
		so = frappe.get_doc({"doctype": "Sales Order", "company": COMPANY, "customer": "江南机械", "transaction_date": nowdate(),
			"delivery_date": add_days(nowdate(), 7), "currency": "CNY", "selling_price_list": "Standard Selling",
			"items": [{"item_code": FG, "qty": 5000, "rate": 0.22, "warehouse": WH_FG, "delivery_date": add_days(nowdate(), 7)}]})
		so.insert()
		so.submit()
		pp = frappe.get_doc({"doctype": "Production Plan", "company": COMPANY, "get_items_from": "Sales Order",
			"posting_date": nowdate(), "for_warehouse": WH_RAW,
			"sales_orders": [{"sales_order": so.name, "sales_order_date": so.transaction_date, "customer": so.customer, "grand_total": so.grand_total}]})
		pp.get_items()
		for row in pp.po_items:
			row.planned_qty = 5264
			row.warehouse = WH_FG
		pp.insert()
		pp.submit()
		out("pp", {"name": pp.name, "po_items": [{"item": r.item_code, "planned_qty": r.planned_qty, "sales_order": r.sales_order} for r in pp.po_items]})
		pp.reload()
		try:
			pp.make_work_order()
			stage1 = "make_work_order 未抛异常"
		except Exception as e:
			stage1 = f"make_work_order 抛 {type(e).__name__}: {e}"
		wos = frappe.get_all("Work Order", filters={"production_plan": pp.name}, fields=["name", "qty", "sales_order", "docstatus"])
		out("stage1_create", {"result": stage1, "work_orders": wos, "messages": [m.get("message") if isinstance(m, dict) else str(m) for m in (frappe.message_log or [])][-3:]})
		for w in wos:
			wo = frappe.get_doc("Work Order", w.name)
			wo.wip_warehouse = wo.wip_warehouse or WH_WIP
			wo.source_warehouse = wo.source_warehouse or WH_RAW
			try:
				wo.submit()
				out("stage2_submit", {"wo": wo.name, "qty": wo.qty, "result": "提交成功", "docstatus": wo.docstatus})
			except Exception as e:
				out("stage2_submit", {"wo": wo.name, "qty": wo.qty, "result": f"{type(e).__name__}", "message": str(e)})
		# 对照：放行比例改为 6% 后，同样数量的工单能否提交（证明拦截确由该比例控制）
		frappe.db.set_single_value("Manufacturing Settings", "overproduction_percentage_for_sales_order", 6)
		for w in frappe.get_all("Work Order", filters={"production_plan": pp.name, "docstatus": 0}, pluck="name"):
			wo = frappe.get_doc("Work Order", w)
			try:
				wo.submit()
				out("control_6pct", {"wo": wo.name, "qty": wo.qty, "result": "提交成功"})
			except Exception as e:
				out("control_6pct", {"wo": wo.name, "result": type(e).__name__, "message": str(e)})
	finally:
		frappe.db.rollback()
		out("rollback", {"pp_left": frappe.db.count("Production Plan", {"posting_date": nowdate(), "company": COMPANY, "docstatus": 1})})
		frappe.destroy()


if __name__ == "__main__":
	main()
