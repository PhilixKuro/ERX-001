"""S8 R8 SB FD-020 edit script: move the act 4/5 on-stage master-data writes into the generator's D1-1 step."""

import os

ROOT = "d:/ERX-001/frappe-bench/apps/frappe_debug/frappe_debug"


def edit(rel, pairs):
	path = os.path.join(ROOT, rel)
	with open(path, encoding="utf-8", newline="") as handle:
		text = handle.read()
	for old, new in pairs:
		if new and new in text:
			continue
		assert text.count(old) == 1, (rel, old[:80])
		text = text.replace(old, new)
	with open(path, "w", encoding="utf-8", newline="") as handle:
		handle.write(text)


edit(
	"scenario/targets.py",
	[
		(
			'''def prepare_act1(sc):
	"""Reserve an unconverted lead for the presenter's native CRM conversion."""
	prepare_act4(sc)''',
			'''def prepare_production_masters(sc):
	"""Production master data acts 4 and 5 rely on, set before D1 (FD-020).

	Act 4's BOM cost recommendation reads the workstation rates; act 5's finished-goods entry
	books operating cost to the company's default operating cost account. Both used to be
	written on stage as the first step of those acts.
	"""
	for config in sc.raw["workstations"]:
		name = frappe.db.get_value("Workstation", {"workstation_name": config["name"]}, "name")
		if name and frappe.db.get_value("Workstation", name, "hour_rate") != config["hour_rate"]:
			frappe.db.set_value("Workstation", name, "hour_rate", config["hour_rate"], update_modified=False)
	company = frappe.db.get_value("Company", {"company_name": sc.raw["company"]["name"]}, "name")
	account = frappe.db.get_value("Company", company, "expenses_added_to_stock_account")
	if not account:
		frappe.throw(f"场景公司 {company} 缺少计入存货费用科目")
	if not frappe.db.get_value("Company", company, "default_operating_cost_account"):
		frappe.db.set_value("Company", company, "default_operating_cost_account", account, update_modified=False)
	return account


def prepare_act1(sc):
	"""Reserve an unconverted lead for the presenter's native CRM conversion."""
	prepare_production_masters(sc)
	prepare_act4(sc)''',
		)
	],
)

edit(
	"data/demo.yaml",
	[
		(
			'''    steps:
      - action: call
        fn: prepare_act4_bom_recommendation
        say: 按场景工位费率核算 BOM，并保留原生推荐确认。
      - action: open_new
        doctype: Production Plan''',
			'''    steps:
      - action: open_new
        doctype: Production Plan''',
		),
		(
			'''    steps:
      - action: call
        fn: prepare_act5_operating_cost_account
        say: 完工费用按公司的存货结转科目自动入账。
      - action: call
        fn: report_remaining_job_cards''',
			'''    steps:
      - action: call
        fn: report_remaining_job_cards''',
		),
	],
)

edit(
	"public/js/demo/functions.js",
	[
		(
			'''	demo.register("prepare_act4_bom_recommendation", async () => {
		const result = await demo.call("frappe_debug.scenario.rehearsal.prepare_act4_bom_recommendation");
		if (!result) throw Error("场景没有可确认的 BOM 推荐");
		return result;
	});
	demo.register("prepare_act5_operating_cost_account", async () => {
		return demo.call("frappe_debug.scenario.rehearsal.prepare_act5_operating_cost_account");
	});
''',
			"",
		)
	],
)

edit(
	"scenario/rehearsal.py",
	[
		(
			'''@frappe.whitelist(methods=["POST"])
def prepare_act4_bom_recommendation() -> str:
	"""Apply configured workstation rates and reserve a default BOM for confirmation."""
	_require_administrator()
	scenario = load_scenario()
	for config in scenario.raw["workstations"]:
		name = frappe.db.get_value("Workstation", {"workstation_name": config["name"]}, "name")
		if name:
			frappe.db.set_value("Workstation", name, "hour_rate", config["hour_rate"], update_modified=False)
	from frappe_debug.scenario.targets import prepare_act4

	return prepare_act4(scenario)


@frappe.whitelist(methods=["POST"])
def prepare_act5_operating_cost_account() -> str:
	"""Ensure manufacturing costs use the configured Chinese inventory cost account."""
	_require_administrator()
	scenario = load_scenario()
	company = frappe.db.get_value("Company", {"company_name": scenario.raw["company"]["name"]}, "name")
	account = frappe.db.get_value("Company", company, "expenses_added_to_stock_account")
	if not account:
		frappe.throw(f"场景公司 {company} 缺少计入存货费用科目")
	if not frappe.db.get_value("Company", company, "default_operating_cost_account"):
		frappe.db.set_value(
			"Company", company, "default_operating_cost_account", account, update_modified=False
		)
	return account


''',
			"",
		)
	],
)

edit(
	"tests/test_demo_auth.py",
	[
		(
			'''		from frappe_debug.demo.snapshot import snapshot_status
		from frappe_debug.scenario.rehearsal import (
			prepare_act4_bom_recommendation,
			prepare_act5_operating_cost_account,
		)

		frappe.set_user("Guest")
		for method in (prepare_act4_bom_recommendation, prepare_act5_operating_cost_account, snapshot_status):''',
			'''		# FD-020 moved the two act 4/5 master-data writes into the generator; only the registry stays.
		from frappe_debug.demo.snapshot import snapshot_status

		frappe.set_user("Guest")
		for method in (snapshot_status,):''',
		),
		(
			'''		from frappe_debug.demo import functions
		from frappe_debug.scenario import rehearsal

		for method in (
			functions.make_quotation_for_deal,
			functions.close_previous_month,
			functions.prepare_cash_flow_worksheet,
			rehearsal.prepare_act4_bom_recommendation,
			rehearsal.prepare_act5_operating_cost_account,
		):''',
			'''		from frappe_debug.demo import functions

		for method in (
			functions.make_quotation_for_deal,
			functions.close_previous_month,
			functions.prepare_cash_flow_worksheet,
		):''',
		),
	],
)
print("ok")
