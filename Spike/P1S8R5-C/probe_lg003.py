"""P1-S8 R5 C 探针：LG-003 BOM 损耗百分比与整数单位校验。只在 test.localhost 跑，全程回滚。"""

import frappe

COMPANY = "_Test Company"
UOM = "_P1S8R5C支"
FG = "_P1S8R5C-FG"
RM = "_P1S8R5C-RM"


def _setup():
	frappe.get_doc({"doctype": "UOM", "uom_name": UOM, "must_be_whole_number": 1}).insert()
	for code in (FG, RM):
		frappe.get_doc(
			{
				"doctype": "Item",
				"item_code": code,
				"item_name": code,
				"item_group": "All Item Groups",
				"stock_uom": UOM,
				"is_stock_item": 1,
				"valuation_rate": 1,
			}
		).insert()


def _try(pct, qty=1000):
	bom = frappe.get_doc(
		{
			"doctype": "BOM",
			"item": FG,
			"company": COMPANY,
			"quantity": qty,
			"process_loss_percentage": pct,
			"rm_cost_as_per": "Valuation Rate",
			"items": [{"item_code": RM, "qty": qty, "rate": 1}],
		}
	)
	py_qty = float(qty) * float(pct) / 100
	try:
		bom.insert()
		stored = frappe.db.get_value("BOM", bom.name, ["process_loss_percentage", "process_loss_qty"])
		return f"pct={pct!r} py_qty={py_qty!r} -> 保存成功, 存储(pct,qty)={stored}"
	except Exception as e:
		frappe.clear_last_message()
		return f"pct={pct!r} py_qty={py_qty!r} -> 拒绝: {type(e).__name__}: {str(e)[:90]}"


def run():
	out = []
	try:
		_setup()
		out.append(f"UOM must_be_whole_number={frappe.db.get_value('UOM', UOM, 'must_be_whole_number')}")
		out.append(f"BOM process_loss_percentage precision={frappe.get_meta('BOM').get_field('process_loss_percentage').precision!r} "
		           f"doc.precision={frappe.new_doc('BOM').precision('process_loss_percentage')}")
		for pct in (4.9303, 4.9, 4.93, 4.0, 5, 0.1, 0.7, 2.3, 4.6):
			out.append(_try(pct))
		# 向下取整损耗数量再回算百分比
		import math

		q = 1000
		loss_qty = math.floor(q * 4.9303 / 100)
		back = loss_qty / q * 100
		out.append(f"floor 方案: loss_qty={loss_qty} back_pct={back!r} -> " + _try(back))
		# 扫 0.1..10.0 步长 0.1 的整数损耗候选，看浮点乘法误差导致误拒的有多少
		bad2 = [p for p in (round(i / 10, 1) for i in range(1, 101)) if (q * p / 100) % 1 != 0]
		out.append(f"qty=1000, pct=0.1..10.0(步长0.1，数学上损耗皆整数) 中 Python 浮点下 %1!=0 的: {bad2}")
	finally:
		frappe.db.rollback()
	print("\n".join(out))
