"""S8 R8 SB: put s8r9 back on its clean base, clear its registry, mark it as the SPC preview site.

Usage (container, cwd sites/): python s8r9_mark_preview.py
"""

import json
import os
import time

import frappe

SITE = "s8r9.localhost"
os.chdir("/workspace/frappe-bench/sites")
frappe.init(site=SITE, sites_path=".")
frappe.connect()
frappe.set_user("Administrator")
try:
	from frappe.installer import update_site_config

	from frappe_debug.demo import dbops, registry
	from frappe_debug.scenario.quality import PREVIEW_SITE_KEY

	assert frappe.local.site == SITE
	data = registry.refresh()
	base = data.get("base_db") or frappe.conf.db_name
	assert not data.get("acts"), data
	dropped = None
	if data.get("work_db"):
		update_site_config("db_name", base)
		frappe.cache().delete_keys(f"{base}|", shared=True)
		dbops.drop_db(data["work_db"])
		registry.clear_markers(data["work_db"])
		dropped = data["work_db"]
	registry.set_registry({"base_db": None, "acts": {}})
	plan = frappe.get_site_path("private", "frappe_debug", "quality-plan.json")
	archived = None
	if os.path.exists(plan):
		archived = plan.replace("quality-plan.json", f"quality-plan-sbgenonly-{int(time.time())}.json")
		os.replace(plan, archived)
	update_site_config(PREVIEW_SITE_KEY, 1)
	print(json.dumps({"base": base, "dropped": dropped, "plan_archived": archived, PREVIEW_SITE_KEY: 1}))
finally:
	frappe.destroy()
