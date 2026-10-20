"""P1-S8 R5 C 探针二：向下取整损耗数量再回算百分比，在 quantity 不整除时是否仍过校验。全程回滚。"""

import math

import frappe

from probe_lg003 import _setup, _try


def run():
	out = []
	try:
		_setup()
		for q, p in ((1000, 4.9303), (3, 40.0), (7, 4.9303), (300, 4.9303), (1234, 4.9303), (1500, 4.9303)):
			loss = math.floor(q * p / 100)
			back = loss / q * 100
			out.append(f"q={q} loss={loss} back={back!r}: " + _try(back, qty=q))
	finally:
		frappe.db.rollback()
	print("\n".join(out))
