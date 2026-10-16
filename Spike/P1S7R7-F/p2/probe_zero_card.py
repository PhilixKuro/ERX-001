# P1-S7-R7 F 片2 探针：拆单后道扣到 0 的草稿卡（偏离 4 保留）与 sync_operation_loss「全部卡已提交」前提的拼装。
# test.localhost，结尾 rollback。
import json

import frappe
from frappe.utils import add_to_date, now_datetime

from frappe_china.production.job_card_split import ensure_patched
from frappe_china.tests.test_operation_flow import TestOperationFlow

out = {}
MODE = frappe.flags.get('probe_mode') or 'none'
out['mode'] = MODE
try:
	ensure_patched()
	frappe.db.set_single_value("Manufacturing Settings", "disable_capacity_planning", 1)
	t = TestOperationFlow("test_submit_realigns_idle_cards_and_scheduled_times")
	wo, cards = t._make_work_order(split_second=True)
	op2 = cards[1].operation_id
	t._complete(cards[0], 700)  # 首道损耗 300
	seconds = t._cards(wo.name, operation_id=op2)
	out["F0_second_qty"] = [c.for_quantity for c in seconds]
	for i, c in enumerate(seconds):
		if not c.for_quantity:
			frappe.db.savepoint("zero_card")
			try:
				c.submit()
				out["F1_zero_card_submit"] = "submitted"
			except Exception as e:
				out["F1_zero_card_submit"] = f"{type(e).__name__}: {str(e)[:160]}"
				frappe.db.rollback(save_point="zero_card")
			out["F1b_zero_card_docstatus_in_db"] = frappe.db.get_value("Job Card", c.name, "docstatus")
			if MODE == "timelog0":
				c.reload()
				start = add_to_date(now_datetime(), hours=20)
				c.append("time_logs", {"from_time": start, "to_time": add_to_date(start, minutes=1), "completed_qty": 0})
				c.save()
				c.submit()
				out["F1c_zero_card_with_0_log"] = frappe.db.get_value("Job Card", c.name, ["docstatus", "process_loss_qty"])
			elif MODE == "delete":
				frappe.delete_doc("Job Card", c.name)
				out["F1c_zero_card_deleted"] = not frappe.db.exists("Job Card", c.name)
			continue
		start = add_to_date(now_datetime(), hours=i + 1)
		c.append(
			"time_logs",
			{"from_time": start, "to_time": add_to_date(start, minutes=10), "completed_qty": c.for_quantity},
		)
		c.save()
		c.submit()
	out["F2_rows_after_nonzero_submitted"] = t._operation_rows(wo.name)
	third = t._cards(wo.name, operation_id=cards[-1].operation_id)[0]
	out["F3_third_qty"] = third.for_quantity
	t._complete(third, third.for_quantity)
	out["F4_rows_all_done"] = t._operation_rows(wo.name)
	try:
		m = t._manufacture(frappe.get_doc("Work Order", wo.name))
		out["F5_manufacture"] = [m.process_loss_qty, [r.qty for r in m.items if r.is_finished_item]]
		out["F5_wo_status"] = frappe.db.get_value("Work Order", wo.name, "status")
	except Exception as e:
		out["F5_manufacture"] = f"{type(e).__name__}: {str(e)[:200]}"
finally:
	frappe.db.rollback()
	print(json.dumps(out, ensure_ascii=False, default=str))
