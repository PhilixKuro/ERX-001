"""Export the verified SPC candidate plan from the completed isolated work database."""
import json
import os

import frappe

site = "s8ts023preview.localhost"
os.chdir("/workspace/frappe-bench/sites")
frappe.init(site=site, sites_path=".")
frappe.connect()
frappe.set_user("Administrator")
try:
	from frappe_debug.demo.registry import get_registry
	from frappe_debug.scenario.params import load_scenario
	from frappe_debug.scenario.quality import export_quality_sample_plan
	from frappe_debug.scenario.runner import _last_generated_date

	registry = get_registry()
	assert frappe.conf.db_name == registry["work_db"]
	assert registry["work_state"] == "ready"
	assert not os.path.exists(frappe.get_site_path("private", "frappe_debug", "quality-plan.json"))
	path = export_quality_sample_plan()
	with open(path, encoding="utf-8") as stream:
		plan = json.load(stream)
	print(json.dumps({
		"site": site,
		"db": frappe.conf.db_name,
		"last_generated": str(_last_generated_date(load_scenario())),
		"plan_path": path,
		"version": plan["version"],
		"attempts": plan["attempts"],
		"groups": len(plan["manifest"]),
		"schedule_fingerprint": plan["schedule_fingerprint"],
	}, ensure_ascii=False), flush=True)
finally:
	frappe.destroy()
