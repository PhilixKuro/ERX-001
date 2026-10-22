import json

import frappe
from frappe.exceptions import ValidationError


def _validate() -> dict[str, object]:
	entry = frappe.new_doc("Stock Entry")
	entry.purpose = "Manufacture"
	entry.from_bom = 1
	entry.fg_completed_qty = 2061.86
	entry.append(
		"items",
		{
			"item_code": "_HT023 FINISHED",
			"is_finished_item": 1,
			"qty": 1993.86,
		},
	)
	try:
		entry.validate_fg_completed_qty()
	except ValidationError as exc:
		accepted = False
		error = str(exc)
	else:
		accepted = True
		error = None
	finished_qty = frappe.utils.flt(entry.items[0].qty, 2)
	process_loss_qty = frappe.utils.flt(entry.process_loss_qty, 2)
	completed_qty = frappe.utils.flt(entry.fg_completed_qty, 2)
	return {
		"accepted": accepted,
		"error": error,
		"finished_qty": finished_qty,
		"process_loss_qty_after_native_recalculation": entry.process_loss_qty,
		"rounded_process_loss_qty": process_loss_qty,
		"rounded_sum": finished_qty + process_loss_qty,
		"completed_qty": completed_qty,
		"rounded_sum_equals_completed_qty": finished_qty + process_loss_qty == completed_qty,
	}


def run() -> None:
	try:
		observed = _validate()
		precision = frappe.get_precision("Stock Entry Detail", "qty")
		result = {
			"site": frappe.local.site,
			"quantity_precision": precision,
			"fg_completed_qty": 2061.86,
			"finished_qty": 1993.86,
			"observed_case": observed,
		}
		print(json.dumps(result, ensure_ascii=False, sort_keys=True))
		if frappe.local.site != "test.localhost":
			raise RuntimeError(f"unexpected site: {frappe.local.site}")
		if observed["accepted"] or observed["rounded_sum_equals_completed_qty"]:
			raise AssertionError("native process-loss comparison did not reproduce the reported rejection")
	finally:
		frappe.db.rollback()
