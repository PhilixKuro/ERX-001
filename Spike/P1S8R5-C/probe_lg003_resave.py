"""P1-S8 R5 C 探针三：回算百分比入库后（9 位小数）再次保存能否通过；以及可校验的选值算法。全程回滚。"""

import math

import frappe
from frappe.utils import flt

from probe_lg003 import FG, RM, UOM, _setup

COMPANY = "_Test Company"


def _passes(q, p):
	# 与 bom.py:1353 / 1371 同一表达式
	return (flt(q) * flt(p) / 100) % 1 == 0


def pick_pct(q, target):
	"""从向下取整的损耗数量往下找，取第一个“入库前后两次判定都整”的百分比。"""
	loss = math.floor(flt(q) * flt(target) / 100)
	while loss >= 0:
		p = loss / q * 100
		if _passes(q, p) and _passes(q, flt(p, 9)):
			return p, loss
		p2 = flt(p, 9)
		if _passes(q, p2):
			return p2, loss
		loss -= 1
	return 0.0, 0


def run():
	out = []
	try:
		_setup()
		for q, p in ((300, 4.666666666666667), (1234, 4.862236628849271)):
			bom = frappe.get_doc(
				{
					"doctype": "BOM",
					"item": FG,
					"company": COMPANY,
					"quantity": q,
					"process_loss_percentage": p,
					"rm_cost_as_per": "Valuation Rate",
					"items": [{"item_code": RM, "qty": q, "rate": 1}],
				}
			).insert()
			doc = frappe.get_doc("BOM", bom.name)
			try:
				doc.save()
				out.append(f"q={q} 入库 pct={doc.process_loss_percentage!r} 重存 -> 成功 qty={doc.process_loss_qty!r}")
			except Exception as e:
				frappe.clear_last_message()
				out.append(f"q={q} 入库 pct={doc.process_loss_percentage!r} 重存 -> 拒绝 {type(e).__name__}")
		for q in (3, 300, 1000, 1234, 1500, 7, 2500):
			out.append(f"pick_pct(q={q}, 4.9303) -> {pick_pct(q, 4.9303)}")
	finally:
		frappe.db.rollback()
	print("\n".join(out))
