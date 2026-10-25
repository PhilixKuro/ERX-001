"""IT-015 / IT-004 readback on a scratch clone of one act's original snapshot.

Run inside the frappe container:
    env/bin/python /workspace/Spike/P1S8R7-E/act_readback.py <site> <scratch_db> <act>
The caller clones ``<base>_a<act>_o`` into ``<scratch_db>`` first and drops it afterwards,
so the demo site's live databases are never connected to. Nothing is committed.
"""

import json
import os
import sys
from datetime import timedelta

import frappe

site, scratch_db, act = sys.argv[1], sys.argv[2], int(sys.argv[3])
assert site == "erx.localhost"
assert scratch_db.startswith("r7e_scratch_a"), scratch_db
os.chdir("/workspace/frappe-bench/sites")
frappe.init(site=site, sites_path=".")
frappe.local.conf.db_name = scratch_db
frappe.connect()
frappe.set_user("Administrator")
out = {"site": site, "scratch_db": scratch_db, "act": act}
try:
	from frappe_debug.demo.progress import get_progress
	from frappe_debug.scenario.params import load_scenario

	progress = get_progress()
	out["progress"] = {key: progress.get(key) for key in ("act", "step", "scene_date")}
	# The site registry records the rehearsal's scenario_end, so dates match the snapshots.
	sc = load_scenario()
	company = frappe.db.get_value("Company", {"company_name": sc.raw["company"]["name"]}, "name")

	if act == 6:
		# IT-015: native capacity report for the target week, as it stands at D2.
		from frappe_china.production_plus.report.capacity_load.capacity_load import execute

		target = sc.raw["act_targets"]["act6_overload"]
		week_start = sc.D2 - timedelta(days=sc.D2.weekday()) + timedelta(weeks=target["week_after_d2"])
		_columns, rows, _message, _chart = execute(
			{
				"company": company,
				"from_date": week_start,
				"to_date": week_start + timedelta(days=6),
				"bucket": "Week",
				"workstations": [target["workstation"]],
			}
		)
		out["capacity"] = {"week": str(week_start), "target_pct": target["load_pct"], "rows": rows}
		out["capacity_ok"] = any(
			row.get("bucket") == str(week_start) and (row.get("load_percent") or 0) > 100 for row in rows
		)

	if act in (7, 8):
		# LG-001: balance sheet of the previous closed month, as act 7/8 shows it.
		from frappe_debug.demo.functions import previous_month_filters
		from frappe_china.accounting.statements.balance_sheet import execute

		filters = previous_month_filters(str(progress.get("scene_date")), company)
		filters.pop("period_type", None)
		_columns, data, notes, _chart, summary, _skip = execute(filters)
		rows = {int(row["a_no"]): row for row in data if row.get("a_no") and int(row["a_no"]) in (9, 10, 11, 12, 13)}
		components = sum(float(rows[n].get("a_close") or 0) for n in (10, 11, 12, 13) if n in rows)
		out["balance_sheet"] = {
			"filters": filters,
			"inventory_row9_close": rows.get(9, {}).get("a_close"),
			"components_close": round(components, 2),
			"summary": summary,
			"notes": notes,
			"lg001_negative_inventory": float(rows.get(9, {}).get("a_close") or 0) < 0,
		}
		# IT-018: absorbed operating cost vs work-order cost, and overhead accounts netting to zero.
		out["operating_cost"] = frappe.db.sql(
			"""SELECT COUNT(*) AS entries, ROUND(SUM(se.total_additional_costs), 2) AS booked,
				ROUND(SUM((SELECT SUM(op.actual_operating_cost) FROM `tabWork Order Operation` op
					WHERE op.parent = se.work_order) * se.fg_completed_qty / wo.qty), 2) AS expected
			FROM `tabStock Entry` se JOIN `tabWork Order` wo ON wo.name = se.work_order
			WHERE se.docstatus = 1 AND se.purpose = 'Manufacture'""",
			as_dict=True,
		)[0]
		out["overhead_accounts"] = frappe.db.sql(
			"""SELECT a.account_number, ROUND(SUM(g.debit), 2) AS debit, ROUND(SUM(g.credit), 2) AS credit
			FROM `tabGL Entry` g JOIN `tabAccount` a ON a.name = g.account
			WHERE g.is_cancelled = 0 AND a.account_number IN ('4101', '410199')
			GROUP BY a.account_number""",
			as_dict=True,
		)
		out["overhead_entries"] = frappe.db.count(
			"Journal Entry", {"docstatus": 1, "user_remark": ["like", "S8 场景制造费用 %"]}
		)
		from frappe_china.accounting.statements.profit_and_loss import execute as profit_and_loss

		_pl_columns, pl_rows, *_rest = profit_and_loss(filters)
		out["profit_and_loss"] = [
			{key: row.get(key) for key in ("line_no", "project", "ytd_amount", "period_amount")}
			for row in pl_rows
			if row.get("line_no") in (1, 2, 21, 30, 32)
		]
		out["largest_additional_cost"] = frappe.db.sql(
			"""SELECT name, fg_completed_qty, total_additional_costs FROM `tabStock Entry`
			WHERE docstatus = 1 AND purpose = 'Manufacture'
			ORDER BY total_additional_costs DESC LIMIT 3""",
			as_dict=True,
		)

	# IT-012 / IT-013: purchasing spread and rejected receipts across the generated history.
	out["po_by_supplier"] = frappe.db.sql(
		"""SELECT supplier, COUNT(*) AS orders FROM `tabPurchase Order`
		WHERE docstatus = 1 GROUP BY supplier ORDER BY supplier""",
		as_dict=True,
	)
	out["rejected_rows"] = frappe.db.sql(
		"""SELECT COUNT(*) AS rows_, ROUND(SUM(pri.rejected_qty), 2) AS qty,
			ROUND(SUM(pri.rejected_qty) / NULLIF(SUM(pri.received_qty), 0) * 100, 2) AS pct,
			GROUP_CONCAT(DISTINCT pri.rejected_warehouse) AS warehouses
		FROM `tabPurchase Receipt Item` pri JOIN `tabPurchase Receipt` pr ON pr.name = pri.parent
		WHERE pr.docstatus = 1 AND pri.rejected_qty > 0""",
		as_dict=True,
	)[0]
	out["receipts"] = frappe.db.count("Purchase Receipt", {"docstatus": 1})
finally:
	frappe.db.rollback()
	frappe.destroy()
print(json.dumps(out, ensure_ascii=False, default=str))
