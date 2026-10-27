"""S8 R8 SB step 1a: prepare the isolated s8r9 preview work database (FD-013 plan, step 1).

Usage (container, cwd sites/): python s8r9_prepare.py config | work
- config: write root_password from $DB_ROOT_PASSWORD into s8r9 site_config (never printed)
- work:   clone the clean base into the work db with quality_preview=1, then point the site at it
"""

import json
import os
import sys
import time

import frappe

SITE = "s8r9.localhost"
step = sys.argv[1]
os.chdir("/workspace/frappe-bench/sites")
frappe.init(site=SITE, sites_path=".")
frappe.connect()
frappe.set_user("Administrator")
try:
	from frappe.installer import update_site_config

	from frappe_debug.demo import registry

	assert frappe.local.site == SITE
	if step == "config":
		password = os.environ.get("DB_ROOT_PASSWORD")
		assert password, "DB_ROOT_PASSWORD not passed"
		update_site_config("root_password", password)
		print(json.dumps({"root_password": "set"}))
	elif step == "work":
		from frappe_debug.demo import workspace

		data = registry.refresh()
		assert not data.get("acts") and not data.get("work_db"), data
		counts = {dt: frappe.db.count(dt) for dt in ("Company", "Sales Order", "GL Entry", "Translation")}
		assert counts == {"Company": 1, "Sales Order": 0, "GL Entry": 0, "Translation": 0}, counts
		assert not os.path.exists(frappe.get_site_path("private", "frappe_debug", "quality-plan.json"))
		base = frappe.conf.db_name
		started = time.time()
		result = workspace.prepare_work(quality_preview=1)
		for _ in range(600):
			data = registry.refresh()
			if data.get("work_state") != "cloning":
				break
			time.sleep(2)
		assert data.get("work_state") == "ready", data
		update_site_config("db_name", data["work_db"])
		frappe.cache().delete_keys(f"{data['work_db']}|", shared=True)
		print(
			json.dumps(
				{
					"base": base,
					"work": result["db"],
					"scenario_end": data["scenario_end"],
					"clone_seconds": round(time.time() - started, 1),
					"counts": counts,
				},
				ensure_ascii=False,
			)
		)
	else:
		raise SystemExit(f"unknown step {step}")
finally:
	frappe.destroy()
