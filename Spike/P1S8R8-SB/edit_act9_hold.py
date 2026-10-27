"""S8 R8 SB: act 9 hold covers EOQ and periodic review over lead time + one review period (user ruling A, 2026-10-27)."""

import os

ROOT = "d:/ERX-001/frappe-bench/apps/frappe_debug/frappe_debug"
CRLF, LF = chr(13) + chr(10), chr(10)


def edit(rel, pairs):
	path = os.path.join(ROOT, rel)
	with open(path, encoding="utf-8", newline="") as handle:
		text = handle.read()
	crlf = CRLF in text
	text = text.replace(CRLF, LF)
	for old, new in pairs:
		if new in text:
			continue
		assert text.count(old) == 1, (rel, old[:80])
		text = text.replace(old, new)
	if crlf:
		text = text.replace(LF, CRLF)
	with open(path, "w", encoding="utf-8", newline="") as handle:
		handle.write(text)


edit(
	"scenario/targets.py",
	[
		(
			'''def hold_act9_suggestion(sc, day, suggestion):
	item_code = sc.raw["act_targets"]["act9_eoq_item"]
	item = next(row for row in sc.raw["items"]["materials"] if row["code"] == item_code)
	return (
		suggestion.item_code == item_code
		and suggestion.rule == "EOQ"
		and sc.E - timedelta(days=item["lead_time_days"]) <= getdate(day) < sc.E
	)
''',
			'''# Rules the act 9 hold keeps unadopted; order-driven replenishment still runs (no shortage).
ACT9_HELD_RULES = ("EOQ", "Periodic Review")


def act9_hold_start(sc):
	"""First day of the act 9 hold: lead time plus one review period before E.

	Holding only EOQ over the lead time left E to chance: a periodic or EOQ adoption just before
	the hold could keep stock above the reorder level on E, and act 9 had no EOQ suggestion
	(S8 R8 SB, s8r9 full-year run 2026-10-27). Over a full review period the periodic rule is
	held through at least one review day too, so stock drifts down to the reorder level.
	"""
	item_code = sc.raw["act_targets"]["act9_eoq_item"]
	item = next(row for row in sc.raw["items"]["materials"] if row["code"] == item_code)
	return sc.E - timedelta(days=item["lead_time_days"] + sc.raw["company"]["review_days"])


def hold_act9_suggestion(sc, day, suggestion):
	return (
		suggestion.item_code == sc.raw["act_targets"]["act9_eoq_item"]
		and suggestion.rule in ACT9_HELD_RULES
		and act9_hold_start(sc) <= getdate(day) < sc.E
	)


def assert_act9_eoq_ready(sc):
	"""Fail the generator, not the show, when E has no EOQ suggestion for act 9."""
	from frappe_china.replenishment.demand import projected_qty, warehouses_of_row

	item_code = sc.raw["act_targets"]["act9_eoq_item"]
	company = sc.raw["company"]["name"]
	if frappe.db.exists(
		"Replenishment Suggestion",
		{
			"company": company,
			"item_code": item_code,
			"rule": "EOQ",
			"calculation_date": sc.E,
			"status": "Awaiting Decision",
		},
	):
		return
	rows = frappe.get_all(
		"Item Reorder",
		filters={"parent": item_code},
		fields=["parent", "warehouse", "warehouse_group", "warehouse_reorder_level"],
	)
	detail = [
		f"{row.warehouse}：计划量 {projected_qty(item_code, warehouses_of_row(row))[0]:g}，再订货点 {row.warehouse_reorder_level:g}"
		for row in rows
	]
	frappe.throw(
		f"场景终点 {sc.E} 没有 {item_code} 的经济订货量建议，第 9 幕无法演示（{'；'.join(detail) or '无再订货设置'}）",
		frappe.ValidationError,
	)
''',
		),
		(
			'''			"status": "Awaiting Decision",
			"item_code": sc.raw["act_targets"]["act9_eoq_item"],
			"rule": "EOQ",
		},''',
			'''			"status": "Awaiting Decision",
			"item_code": sc.raw["act_targets"]["act9_eoq_item"],
			"rule": ["in", ACT9_HELD_RULES],
		},''',
		),
	],
)

edit(
	"scenario/monthly.py",
	[
		(
			'''	from frappe_debug.scenario.targets import (
		ignore_held_act9_suggestions,''',
			'''	from frappe_debug.scenario.targets import (
		assert_act9_eoq_ready,
		ignore_held_act9_suggestions,''',
		),
		(
			'''		if not result["ok"]:
			frappe.throw(f"场景终点 {sc.E} 补货计算失败：{frappe.as_json(result)}")''',
			'''		if not result["ok"]:
			frappe.throw(f"场景终点 {sc.E} 补货计算失败：{frappe.as_json(result)}")
		assert_act9_eoq_ready(sc)''',
		),
	],
)

edit(
	"tests/test_targets.py",
	[
		(
			'''	def test_act9_holds_only_target_eoq_during_final_lead_time(self):
		from frappe_debug.scenario.targets import hold_act9_suggestion

		suggestion = frappe._dict(item_code="_FCT WIRE", rule="EOQ")
		self.assertFalse(hold_act9_suggestion(self.sc, self.sc.E - timedelta(days=8), suggestion))
		self.assertTrue(hold_act9_suggestion(self.sc, self.sc.E - timedelta(days=7), suggestion))
		suggestion.rule = "Order"
		self.assertFalse(hold_act9_suggestion(self.sc, self.sc.E - timedelta(days=1), suggestion))''',
			'''	def test_act9_holds_target_eoq_and_periodic_over_lead_time_plus_review_period(self):
		from frappe_debug.scenario.targets import hold_act9_suggestion

		# small_parameters: lead time 7, review period 14 -> hold from E-21
		suggestion = frappe._dict(item_code="_FCT WIRE", rule="EOQ")
		self.assertFalse(hold_act9_suggestion(self.sc, self.sc.E - timedelta(days=22), suggestion))
		self.assertTrue(hold_act9_suggestion(self.sc, self.sc.E - timedelta(days=21), suggestion))
		self.assertFalse(hold_act9_suggestion(self.sc, self.sc.E, suggestion))
		suggestion.rule = "Periodic Review"
		self.assertTrue(hold_act9_suggestion(self.sc, self.sc.E - timedelta(days=1), suggestion))
		suggestion.rule = "By Sales Order"
		self.assertFalse(hold_act9_suggestion(self.sc, self.sc.E - timedelta(days=1), suggestion))
		suggestion.update(rule="EOQ", item_code="_FCT OTHER")
		self.assertFalse(hold_act9_suggestion(self.sc, self.sc.E - timedelta(days=1), suggestion))

	def test_missing_act9_eoq_on_e_fails_the_generator_with_stock_detail(self):
		from frappe_debug.scenario.targets import assert_act9_eoq_ready

		with self.assertRaisesRegex(frappe.ValidationError, "第 9 幕"):
			assert_act9_eoq_ready(self.sc)
		frappe.get_doc(
			{
				"doctype": "Replenishment Suggestion",
				"company": self.m["company"],
				"item_code": "_FCT WIRE",
				"warehouse": self.m["warehouses"]["stores"],
				"rule": "EOQ",
				"calculation_date": self.sc.E,
				"suggested_qty": 10,
				"material_request_type": "Purchase",
			}
		).insert(ignore_permissions=True)
		self.assertIsNone(assert_act9_eoq_ready(self.sc))''',
		),
		(
			'''		for item, rule, calculated in (
			("_FCT WIRE", "EOQ", day),
			("_FCT WIRE", "By Sales Order", day),
			("_FCT WIRE", "EOQ", day - timedelta(days=20)),
		):''',
			'''		for item, rule, calculated in (
			("_FCT WIRE", "EOQ", day),
			("_FCT WIRE", "By Sales Order", day),
			("_FCT WIRE", "EOQ", day - timedelta(days=30)),
			("_FCT WIRE", "Periodic Review", day - timedelta(days=10)),
		):''',
		),
		(
			'''			patch("frappe_debug.scenario.support.make_supplier_scorecards"),
			patch("frappe_debug.scenario.support.clear_admin_list_filters"),
		):''',
			'''			patch("frappe_debug.scenario.support.make_supplier_scorecards"),
			patch("frappe_debug.scenario.support.clear_admin_list_filters"),
			patch("frappe_debug.scenario.targets.assert_act9_eoq_ready"),
		):''',
		),
		(
			'''			["Ignored", "Awaiting Decision", "Awaiting Decision"],''',
			'''			["Ignored", "Awaiting Decision", "Awaiting Decision", "Ignored"],''',
		),
	],
)
print("ok")
