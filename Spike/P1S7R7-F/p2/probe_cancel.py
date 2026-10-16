# P1-S7-R7 F 片2 探针：拆单工序取消一张已提交卡后 sync_operation_loss 的行为。test.localhost，结尾 rollback。
import json

import frappe

from frappe_china.production.job_card_split import ensure_patched
from frappe_china.tests.test_operation_flow import TestOperationFlow

out = {}
try:
	ensure_patched()
	frappe.db.set_single_value("Manufacturing Settings", "disable_capacity_planning", 1)
	t = TestOperationFlow("test_submit_realigns_idle_cards_and_scheduled_times")
	wo, cards = t._make_work_order(split_second=True)
	op2 = cards[1].operation_id
	t._complete(cards[0], 1000)
	seconds = t._cards(wo.name, operation_id=op2)
	from frappe.utils import add_to_date, now_datetime

	for i, c in enumerate(seconds):
		start = add_to_date(now_datetime(), hours=i + 1)
		c.append("time_logs", {"from_time": start, "to_time": add_to_date(start, minutes=10), "completed_qty": 250})
		c.save()
		c.submit()
		c.reload()
	out["E1_rows_all_four_submitted"] = t._operation_rows(wo.name)
	seconds[-1].cancel()
	out["E2_rows_after_cancel_one"] = t._operation_rows(wo.name)
	row = frappe.get_doc("Work Order", wo.name).operations[1]
	out["E3_pending_for_make_job_card_dialog"] = 1000 - row.completed_qty - row.process_loss_qty
	third = t._cards(wo.name, operation_id=cards[-1].operation_id)[0]
	out["E4_third_qty"] = third.for_quantity
	start = add_to_date(now_datetime(), hours=30)
	third.append("time_logs", {"from_time": start, "to_time": add_to_date(start, minutes=10), "completed_qty": 750})
	third.save()
	third.submit()
	out["E5_rows"] = t._operation_rows(wo.name)
	try:
		m = t._manufacture(frappe.get_doc("Work Order", wo.name))
		out["E6_manufacture_loss_fg"] = [m.process_loss_qty, [r.qty for r in m.items if r.is_finished_item]]
		out["E6_wo"] = frappe.db.get_value("Work Order", wo.name, ["status", "produced_qty", "process_loss_qty"])
	except Exception as e:
		out["E6_manufacture"] = f"{type(e).__name__}: {str(e)[:200]}"
finally:
	frappe.db.rollback()
	print(json.dumps(out, ensure_ascii=False, default=str))
