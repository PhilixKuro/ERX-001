"""FD-002／003／004／027：operation_flow.py。"""

import sys

sys.path.insert(0, r"D:\ERX-001\Spike\P1S7R7-F\fix")
from repl import apply

A = r"D:\ERX-001\frappe-bench\apps\frappe_china\frappe_china"
OLD_MSG = "Operation {0}: all Job Cards have started; {1} units differ from the previous operation's expected output."
NEW_MSG = OLD_MSG + " Please adjust manually."
apply(
	A + r"\production\operation_flow.py",
	[
		(f'"{OLD_MSG}"', f'"{NEW_MSG}"'),
		(
			"\t\tif not cards or any(card.docstatus == 0 for card in cards):\n",
			"\t\t# 扣到 0 的草稿卡（总纲偏离 4 保留）原生提交不了，不算未完成（R7 F FD-002）\n"
			"\t\tif not cards or any(card.docstatus == 0 and flt(card.for_quantity) for card in cards):\n",
		),
		(
			'\t\t{"for_quantity": new_qty, "time_required": time_required},\n\t\tupdate_modified=False,\n\t)\n',
			'\t\t{"for_quantity": new_qty, "time_required": time_required},\n'
			"\t)  # 更新 modified：此前打开的表单再保存会被原生「已被修改」拦下，不会写回旧数量（R7 F FD-003）\n",
		),
		(
			"\tfor item in items:\n"
			"\t\trequired_qty = (\n"
			"\t\t\tflt(item.required_qty) * ratio\n"
			"\t\t\tif old_qty\n"
			"\t\t\telse flt(item.required_qty) * new_qty / flt(work_order.qty)\n"
			"\t\t)\n",
			"\tper_unit = _required_per_unit(work_order, operation) if not old_qty else {}\n"
			"\tfor item in items:\n"
			"\t\t# 从 0 加回时比例无从算起，按工单原料的单位用量重取（同原生 get_required_items，R7 F FD-004）\n"
			"\t\trequired_qty = (\n"
			"\t\t\tflt(item.required_qty) * ratio if old_qty else per_unit.get(item.item_code, 0) * new_qty\n"
			"\t\t)\n",
		),
		(
			'\t\tfields=["name", "required_qty"],\n\t\torder_by="idx",\n\t)\n',
			'\t\tfields=["name", "item_code", "required_qty"],\n\t\torder_by="idx",\n\t)\n',
		),
		(
			"def _update_scheduled_time(",
			"def _required_per_unit(work_order, operation) -> dict[str, float]:\n"
			"\t\"\"\"工单原料中属于该工序的每件用量（job_card.py get_required_items 的同一判据）。\"\"\"\n"
			"\tif not flt(work_order.qty):\n"
			"\t\treturn {}\n"
			"\tper_unit: dict[str, float] = {}\n"
			"\tfor row in work_order.get(\"required_items\") or []:\n"
			"\t\tif row.operation == operation.operation or row.get(\"operation_row_id\") == operation.name:\n"
			"\t\t\tper_unit[row.item_code] = per_unit.get(row.item_code, 0) + flt(row.required_qty) / flt(work_order.qty)\n"
			"\treturn per_unit\n\n\n"
			"def _update_scheduled_time(",
		),
	],
)
apply(
	A + r"\translations\zh.csv",
	[(f"{OLD_MSG},工序 {{0}}：所有生产任务单均已开工，与前一道工序的预计产出相差 {{1}} 件。", f"{NEW_MSG},工序 {{0}}：所有生产任务单均已开工，与前一道工序的预计产出相差 {{1}} 件，请手动调整。")],
)
print("done")
