"""S8 R8 SB: after the s8r9 full rehearsal, point the site at its work db and export the SPC plan.

Usage (container, cwd sites/): python s8r9_export_from_rehearsal.py
"""

import json
import os

import frappe

SITE = "s8r9.localhost"
os.chdir("/workspace/frappe-bench/sites")
frappe.init(site=SITE, sites_path=".")
frappe.connect()
frappe.set_user("Administrator")
try:
	from frappe.installer import update_site_config

	from frappe_debug.demo import registry

	assert frappe.local.site == SITE
	data = registry.refresh()
	assert data.get("work_state") == "ready", data
	work = data["work_db"]
	if frappe.conf.db_name != work:
		update_site_config("db_name", work)
		frappe.cache().delete_keys(f"{work}|", shared=True)
	print(json.dumps({"registry_base": data["base_db"], "work": work, "scenario_end": data.get("scenario_end")}))
finally:
	frappe.destroy()

frappe.init(site=SITE, sites_path=".")
frappe.connect()
frappe.set_user("Administrator")
try:
	from frappe_debug.scenario.params import load_scenario
	from frappe_debug.scenario.quality import export_quality_sample_plan
	from frappe_debug.scenario.runner import _last_generated_date

	assert frappe.conf.db_name.endswith("_work"), frappe.conf.db_name
	sc = load_scenario()
	path = export_quality_sample_plan()
	with open(path, encoding="utf-8") as stream:
		plan = json.load(stream)
	print(
		json.dumps(
			{
				"db": frappe.conf.db_name,
				"E": str(sc.E),
				"last_generated": str(_last_generated_date(sc)),
				"plan_path": path,
				"attempts": plan["attempts"],
				"groups": len(plan["manifest"]),
				"d1_job_card_keys": sorted(k for k in plan["manifest"] if '"2026-01-08","Job Card"' in k)[:3],
			},
			ensure_ascii=False,
		)
	)
finally:
	frappe.destroy()
