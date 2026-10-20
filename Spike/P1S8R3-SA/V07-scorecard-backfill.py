"""P1-S8-R3 SA V-07：把供应商 creation 改到场景起点后调 make_all_scorecards，
是否按月补出从场景起点到今天的全部 Supplier Scorecard Period，且分数非空。
前提：V-04 生成器已在 sa.localhost 造了 2025-10-20 起的逐日采购收货／发票（供应商 宝钢弹簧钢丝）。
只在 sa.localhost 跑，全程 rollback。
用法（容器内 bench 目录）：env/bin/python /workspace/Spike/P1S8R3-SA/V07-scorecard-backfill.py"""
import json
import os

import frappe

SUPPLIER = "宝钢弹簧钢丝"
START = "2025-10-01 00:00:00"


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
		out("before", {"creation": frappe.db.get_value("Supplier", SUPPLIER, "creation"),
			"pr_months": frappe.db.sql("select date_format(posting_date,'%%Y-%%m') m, count(*) from `tabPurchase Receipt` where supplier=%s and docstatus=1 group by m", SUPPLIER)})
		frappe.db.set_value("Supplier", SUPPLIER, "creation", START, update_modified=False)
		# 标准做法：建一张按月的记分卡，挂两条常用标准（准时交货、合格率）
		for name, formula in (("SA 准时交货", "({on_time_shipment_num} / ({total_shipments} + 1)) * 100"),
				("SA 合格率", "({total_accepted_items} / ({total_received_items} + 1)) * 100")):
			if not frappe.db.exists("Supplier Scorecard Criteria", name):
				frappe.get_doc({"doctype": "Supplier Scorecard Criteria", "criteria_name": name, "max_score": 100,
					"weight": 50, "formula": formula}).insert()
		from erpnext.buying.doctype.supplier_scorecard.supplier_scorecard import get_default_scorecard_standing
		sc = frappe.get_doc({"doctype": "Supplier Scorecard", "supplier": SUPPLIER, "period": "Per Month",
			"weighting_function": "{total_score} * max( 0, min ( 1 , (12 - {period_number}) / 12) )",
			"criteria": [{"criteria_name": "SA 准时交货", "weight": 50}, {"criteria_name": "SA 合格率", "weight": 50}],
			# 表单 JS 选等级时会带出等级区间与颜色；脚本建单须自己从等级主数据取（不取则 validate_standings 比较 None 报 TypeError）
			"standings": [frappe.db.get_value("Supplier Scorecard Standing", s["standing_name"],
				["standing_name", "standing_color", "min_grade", "max_grade", "prevent_rfqs", "warn_rfqs", "prevent_pos", "warn_pos", "notify_supplier", "notify_employee"], as_dict=True)
				for s in get_default_scorecard_standing()]})
		sc.insert()  # on_update 内即调 make_all_scorecards（supplier_scorecard.py:57-60）
		periods = frappe.get_all("Supplier Scorecard Period", filters={"scorecard": sc.name},
			fields=["start_date", "end_date", "total_score", "docstatus"], order_by="start_date")
		out("periods", {"count": len(periods), "first": periods[0] if periods else None, "last": periods[-1] if periods else None,
			"null_or_zero_scores": [p for p in periods if not p.total_score],
			"all": [[str(p.start_date), str(p.end_date), float(p.total_score or 0)] for p in periods]})
		sc.reload()
		out("scorecard", {"supplier_score": sc.supplier_score, "status": sc.status})
		# 对照：不改 creation 时（供应商 creation=2026-10-19，即站点创建日）会补几期
	finally:
		frappe.db.rollback()
		out("rollback", {"creation_after_rollback": frappe.db.get_value("Supplier", SUPPLIER, "creation"),
			"scorecards_left": frappe.db.count("Supplier Scorecard")})
		frappe.destroy()


if __name__ == "__main__":
	main()
