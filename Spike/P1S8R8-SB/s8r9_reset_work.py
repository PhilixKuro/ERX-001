"""S8 R8 SB: return s8r9 to its clean base, drop the preview work db, archive the exported plan.

Usage (container, cwd sites/): python s8r9_reset_work.py
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

	assert frappe.local.site == SITE
	data = registry.refresh()
	base, work = data["base_db"], data["work_db"]
	assert work == f"{base}_work", data
	assert not data.get("acts"), data
	update_site_config("db_name", base)
	frappe.cache().delete_keys(f"{base}|", shared=True)
	dbops.drop_db(work)
	registry.clear_markers(work)
	registry.set_registry({"base_db": None, "acts": {}})
	plan = frappe.get_site_path("private", "frappe_debug", "quality-plan.json")
	archived = None
	if os.path.exists(plan):
		archived = plan.replace("quality-plan.json", f"quality-plan-sbtry1-{int(time.time())}.json")
		os.replace(plan, archived)
	status = frappe.get_site_path("private", "frappe_debug", "generate.json")
	print(json.dumps({"base": base, "dropped": work, "plan_archived": archived, "status_file": os.path.exists(status)}))
finally:
	frappe.destroy()
