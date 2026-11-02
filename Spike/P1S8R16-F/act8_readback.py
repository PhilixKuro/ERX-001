"""S8 R16 F: read-only check of the act 8 narration against the strategy comparison on a work db.

R15 receipt review note 3: after PT-061 (EOQ holding cost at the stock moving average) the act 8
numbers changed; the narration claims order-based keeps the least stock, buys most often and runs
short most, and EOQ has the lowest total cost. Runs the report with the same periods as the demo's
set_strategy_periods and prints each claim. Reads through a second connection; nothing is written.

Usage (container, cwd sites/): python act8_readback.py <site>   -> logs/s8-r16f-<site>-act8.json
"""

import json
import os
import sys
from datetime import timedelta

import frappe

SITE = sys.argv[1]
assert SITE in {"erx.localhost", "s8r9.localhost"}, SITE
os.chdir("/workspace/frappe-bench/sites")
frappe.init(site=SITE, sites_path=".")
frappe.connect()
try:
	from frappe_debug.demo.registry import get_registry

	work = get_registry()["work_db"]
	frappe.local.conf.db_name = work
	frappe.connect(set_admin_as_user=True)
	assert frappe.db.cur_db_name == work, frappe.db.cur_db_name
	from frappe_china.stock_plus.report.replenishment_strategy_comparison.replenishment_strategy_comparison import (
		execute,
	)

	from frappe_debug.scenario.params import load_scenario

	sc = load_scenario()
	rules = sc.rule_dates
	day_before = lambda day: day - timedelta(days=1)  # noqa: E731
	periods = [
		(rules["order"], day_before(rules["eoq"])),
		(rules["eoq"], day_before(rules["periodic"])),
		(rules["periodic"], day_before(sc.E)),
	]
	filters = {"company": sc.raw["company"]["name"]}
	for index, (start, end) in enumerate(periods, 1):
		filters[f"period_{index}_from"], filters[f"period_{index}_to"] = str(start), str(end)
	_columns, rows, *_ = execute(frappe._dict(filters))
	rows = [dict(row) for row in rows]
	pick = lambda key: [round(float(row.get(key) or 0), 2) for row in rows]  # noqa: E731
	value, count, total, shortage = pick("avg_value"), pick("po_count"), pick("total"), pick("shortage")
	claims = {
		"order_least_stock": value[0] == min(value),
		"order_most_purchases": count[0] == max(count),
		"order_most_shortages": shortage[0] == max(shortage),
		"eoq_lowest_total": total[1] == min(total),
	}
	result = {"site": SITE, "db": work, "E": str(sc.E), "filters": filters, "rows": rows, "claims": claims}
	with open(f"/workspace/frappe-bench/logs/s8-r16f-{SITE.split('.')[0]}-act8.json", "w", encoding="utf-8") as out:
		json.dump(result, out, ensure_ascii=False, indent=1, default=str)
	print(json.dumps({"avg_value": value, "po_count": count, "total": total, "shortage": shortage, "claims": claims}, ensure_ascii=False))
finally:
	frappe.destroy()
