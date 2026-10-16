# P1-S7-R7 F 片2 探针：工序数量传递与损耗补写的副作用。只在 test.localhost 跑，结尾 rollback。
import json

import frappe
from erpnext.manufacturing.doctype.work_order import work_order as wo_mod

from frappe_china.tests.test_operation_flow import TestOperationFlow

out = {}
try:
	# A. bench execute 进程里拆单补丁是否已装（未经 before_request / before_submit）
	out["A_patched_in_bench_execute"] = wo_mod.split_qty_based_on_batch_size.__module__

	from frappe_china.production.job_card_split import ensure_patched

	ensure_patched()
	frappe.db.set_single_value("Manufacturing Settings", "disable_capacity_planning", 1)
	t = TestOperationFlow("test_submit_realigns_idle_cards_and_scheduled_times")

	def ops(wo):
		return t._operation_rows(wo)

	def cardq(wo, op_id):
		return [
			(c.for_quantity, [round(i.required_qty, 3) for i in c.items], c.time_required)
			for c in t._cards(wo, operation_id=op_id)
		]

	# B. 拆单第二道 4×250，前道 700 完工 → 一张扣到 0；再取消前道 → 加回
	wo, cards = t._make_work_order(split_second=True)
	op2 = cards[1].operation_id
	out["B0_before"] = cardq(wo.name, op2)
	t._complete(cards[0], 700)
	out["B1_after_700"] = cardq(wo.name, op2)
	cards[0].cancel()
	out["B2_after_cancel"] = cardq(wo.name, op2)

	# C. 同一工序只建了部分数量的卡（人手把首道卡改成 600），提交后看工序行损耗
	wo, cards = t._make_work_order()
	first = cards[0]
	first.for_quantity = 600
	first.save()
	t._complete(first, 600)
	out["C_rows_after_600_partial_card"] = ops(wo.name)
	out["C_first_card_loss"] = frappe.db.get_value("Job Card", first.name, "process_loss_qty")
	out["C_second_card_qty"] = frappe.db.get_value("Job Card", cards[1].name, "for_quantity")

	# D. 后道卡在前道提交前已被打开（陈旧表单），级联后再保存陈旧文档
	wo, cards = t._make_work_order()
	stale = frappe.get_doc("Job Card", cards[1].name)
	t._complete(cards[0], 950)
	out["D_db_qty_after_cascade"] = frappe.db.get_value("Job Card", stale.name, "for_quantity")
	try:
		stale.save()
		out["D_stale_save"] = "saved"
	except Exception as e:
		out["D_stale_save"] = f"{type(e).__name__}: {e}"[:200]
	out["D_db_qty_after_stale_save"] = frappe.db.get_value(
		"Job Card", stale.name, ["for_quantity", "time_required"]
	)
finally:
	frappe.db.rollback()
	print(json.dumps(out, ensure_ascii=False, default=str, indent=1))
