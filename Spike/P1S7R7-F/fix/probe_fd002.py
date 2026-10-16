# FD-002 修后诊断：test.localhost，结尾 rollback。
import json

import frappe

from frappe_china.production.job_card_split import ensure_patched
from frappe_china.tests.test_s7_audit_fixes import TestS7AuditOperationFlow

out = {}
try:
	ensure_patched()
	frappe.db.set_single_value("Manufacturing Settings", "disable_capacity_planning", 1)
	t = TestS7AuditOperationFlow("test_fd002_zero_qty_draft_card_does_not_block_manufacture")
	wo, cards = t._make_work_order(split_second=True)
	t._complete(cards[0], 700)
	seconds = t._cards(wo.name, operation_id=cards[1].operation_id)
	for offset, card in enumerate(seconds[:3], start=1):
		t._complete_at(card, card.for_quantity, offset)
	out["after_second"] = t._operation_rows(wo.name)
	third = t._cards(wo.name, operation_id=cards[2].operation_id)
	out["third_cards"] = [(c.name, c.for_quantity, c.docstatus) for c in third]
	t._complete_at(third[0], third[0].for_quantity, 5)
	out["after_third"] = t._operation_rows(wo.name)
	out["third_card_after"] = frappe.db.get_value(
		"Job Card", third[0].name, ["total_completed_qty", "process_loss_qty", "docstatus"]
	)
finally:
	frappe.db.rollback()
	print(json.dumps(out, ensure_ascii=False, default=str))
