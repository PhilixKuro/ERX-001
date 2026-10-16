"""E probe: demand window edges (D-89 included? D-90 excluded?) and projected_qty vs native Bin.projected_qty. Rolled back."""
import json
from datetime import timedelta

import frappe
from erpnext.stock.doctype.stock_entry.stock_entry_utils import make_stock_entry
from frappe.utils import getdate, today

from frappe_china.replenishment.demand import daily_demand, projected_qty

assert frappe.local.site == "test.localhost"
company, wh = "_Test Company", "Stores - _TC"
out = {}
try:
	item = frappe.get_doc({"doctype": "Item", "item_code": "_FCT E window " + frappe.generate_hash(length=6),
		"item_group": "Products", "stock_uom": "Nos", "is_stock_item": 1, "valuation_rate": 1}).insert()
	d = getdate(today()) - timedelta(days=2)
	make_stock_entry(item_code=item.name, qty=100, to_warehouse=wh, rate=1, company=company, posting_date=d - timedelta(days=120))
	for offset, qty in ((90, 1), (89, 2), (0, 4)):
		make_stock_entry(item_code=item.name, qty=qty, from_warehouse=wh, company=company, posting_date=d - timedelta(days=offset))
	series = daily_demand([item.name], [wh], d)[item.name]
	out["len"] = len(series)
	out["sum"] = sum(series)          # expect 2+4=6 if (D-89 .. D] inclusive of D-89 per plan "从 D−89 到 D"
	out["first_slot"] = series[0]     # D-89 slot
	out["last_slot"] = series[-1]
	# projected vs native: reserve some qty for production via Bin field directly
	bin_name = frappe.db.get_value("Bin", {"item_code": item.name, "warehouse": wh})
	frappe.db.set_value("Bin", bin_name, "reserved_qty_for_production", 10)
	b = frappe.get_doc("Bin", bin_name)
	b.set_projected_qty()
	b.db_update()
	ours, _ = projected_qty(item.name, [wh])
	out["projected_ours"] = ours
	out["projected_native"] = frappe.db.get_value("Bin", bin_name, "projected_qty")
except Exception as error:
	out["ERROR"] = f"{type(error).__name__}: {str(error)[:400]}"
finally:
	frappe.db.rollback()
	print(json.dumps(out, ensure_ascii=False, default=str))
