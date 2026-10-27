"""S8 R8 SB FD-008 edit script: rotating supplier price trends, no block action in scenario grades."""

import os

ROOT = "d:/ERX-001/frappe-bench/apps/frappe_debug/frappe_debug"


def edit(rel, pairs):
	path = os.path.join(ROOT, rel)
	with open(path, encoding="utf-8") as handle:
		text = handle.read()
	for old, new in pairs:
		assert text.count(old) == 1, (rel, old[:80])
		text = text.replace(old, new)
	with open(path, "w", encoding="utf-8") as handle:
		handle.write(text)


edit(
	"data/scenario.yaml",
	[
		(
			"""prices:
  supplier_trend:
    - {supplier: 钢丝供应商01, item: WIRE-65MN-3.0, base: 7.80, monthly_change: 0.03}
    - {supplier: 钢丝供应商02, item: WIRE-65MN-3.0, base: 8.00, monthly_change: -0.02}
    - {supplier: 钢丝供应商03, item: WIRE-65MN-3.0, base: 7.95, monthly_change: 0.01}
    - {supplier: 钢丝供应商04, item: WIRE-65MN-3.0, base: 8.10, monthly_change: -0.01}
    - {supplier: 钢丝供应商05, item: WIRE-65MN-5.0, base: 7.60, monthly_change: 0.03}
    - {supplier: 钢丝供应商06, item: WIRE-65MN-5.0, base: 7.80, monthly_change: -0.02}
    - {supplier: 钢丝供应商07, item: WIRE-65MN-5.0, base: 7.75, monthly_change: 0.01}
    - {supplier: 钢丝供应商08, item: WIRE-65MN-5.0, base: 7.90, monthly_change: -0.01}
    - {supplier: 钢丝供应商09, item: WIRE-60SI2MN-8.0, base: 8.40, monthly_change: 0.03}
    - {supplier: 钢丝供应商10, item: WIRE-60SI2MN-8.0, base: 8.60, monthly_change: -0.02}
    - {supplier: 钢丝供应商11, item: WIRE-60SI2MN-8.0, base: 8.55, monthly_change: 0.01}
    - {supplier: 钢丝供应商12, item: WIRE-60SI2MN-8.0, base: 8.70, monthly_change: -0.01}""",
			"""# FD-008: the four suppliers of each wire take turns as the month's lowest price
# (months 0-3, 4-6, 7-9, 10-12 from S), so every supplier has orders in the year.
prices:
  supplier_trend:
    - {supplier: 钢丝供应商01, item: WIRE-65MN-3.0, base: 7.80, monthly_change: 0.03}
    - {supplier: 钢丝供应商02, item: WIRE-65MN-3.0, base: 7.86, monthly_change: 0.01}
    - {supplier: 钢丝供应商03, item: WIRE-65MN-3.0, base: 7.98, monthly_change: -0.01}
    - {supplier: 钢丝供应商04, item: WIRE-65MN-3.0, base: 8.16, monthly_change: -0.03}
    - {supplier: 钢丝供应商05, item: WIRE-65MN-5.0, base: 7.60, monthly_change: 0.03}
    - {supplier: 钢丝供应商06, item: WIRE-65MN-5.0, base: 7.66, monthly_change: 0.01}
    - {supplier: 钢丝供应商07, item: WIRE-65MN-5.0, base: 7.78, monthly_change: -0.01}
    - {supplier: 钢丝供应商08, item: WIRE-65MN-5.0, base: 7.96, monthly_change: -0.03}
    - {supplier: 钢丝供应商09, item: WIRE-60SI2MN-8.0, base: 8.40, monthly_change: 0.03}
    - {supplier: 钢丝供应商10, item: WIRE-60SI2MN-8.0, base: 8.46, monthly_change: 0.01}
    - {supplier: 钢丝供应商11, item: WIRE-60SI2MN-8.0, base: 8.58, monthly_change: -0.01}
    - {supplier: 钢丝供应商12, item: WIRE-60SI2MN-8.0, base: 8.76, monthly_change: -0.03}""",
		)
	],
)

edit(
	"scenario/support.py",
	[
		(
			'''def make_supplier_scorecards(sc):''',
			'''def scenario_standings() -> list[dict]:
	"""Native default grades with the block actions turned into warnings (FD-008).

	Months without orders score 0 under the scenario criteria, so a supplier that only won
	early months still grades Very Poor; the native grade would then set ``prevent_pos`` and
	the Act 9 presenter could not order from it. Grades and colours stay native.
	"""
	from erpnext.buying.doctype.supplier_scorecard import supplier_scorecard as native

	standings = native.get_default_scorecard_standing()
	for row in standings:
		for block, warn in (("prevent_pos", "warn_pos"), ("prevent_rfqs", "warn_rfqs")):
			if row.get(block):
				row[block] = 0
				row[warn] = 1
	return standings


def make_supplier_scorecards(sc):''',
		),
		(
			'''			if name:
				frappe.get_doc("Supplier Scorecard", name).save(ignore_permissions=True)''',
			'''			if name:
				doc = frappe.get_doc("Supplier Scorecard", name)
				doc.set("standings", scenario_standings())
				doc.save(ignore_permissions=True)''',
		),
		(
			'''						"standings": native.get_default_scorecard_standing(),''',
			'''						"standings": scenario_standings(),''',
		),
	],
)

edit(
	"scenario/verify.py",
	[
		(
			'''	period_ok = all(row.docstatus == 1 and row.total_score is not None for row in periods)''',
			'''	period_ok = all(row.docstatus == 1 and row.total_score is not None for row in periods)
	# S8 R8 SB FD-008：每家供应商全年都有采购单；评分不触发禁采
	ordered = set(
		frappe.db.sql(
			"""select distinct supplier from `tabPurchase Order`
			where company=%s and docstatus=1 and transaction_date between %s and %s""",
			(company, sc.S, sc.E),
			pluck=True,
		)
	)
	blocked = frappe.get_all(
		"Supplier", filters={"name": ("in", supplier_names), "prevent_pos": 1}, pluck="name"
	)
	_check(
		checks,
		"supplier.rotation",
		{"without_orders": sorted(set(supplier_names) - ordered), "prevent_pos": blocked},
		set(supplier_names) <= ordered and not blocked,
	)''',
		)
	],
)

edit(
	"tests/test_scenario_support.py",
	[
		(
			'''		counts = {dt: frappe.db.count(dt) for dt in ("Supplier Scorecard", "Supplier Scorecard Period")}''',
			'''		# S8 R8 SB FD-008：无单据期评 0 分时原生等级不再禁采，只警告
		for supplier in m["suppliers"].values():
			self.assertEqual(frappe.db.get_value("Supplier", supplier, "prevent_pos"), 0)
			self.assertEqual(frappe.db.get_value("Supplier", supplier, "prevent_rfqs"), 0)
		counts = {dt: frappe.db.count(dt) for dt in ("Supplier Scorecard", "Supplier Scorecard Period")}''',
		)
	],
)
print("ok")
