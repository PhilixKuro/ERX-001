"""R13 TS-037 step 1: after the s8r9 full rehearsal, point the site at its work db, run verify, read supplier standings.

Usage (container, cwd sites/): python s8r9_verify.py
Writes frappe-bench/logs/s8-r13d-s8r9-verify.json; prints failed checks, supplier.*, integer_uom.*, act9.* and the 12 scorecards.
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
finally:
	frappe.destroy()

frappe.init(site=SITE, sites_path=".")
frappe.connect()
frappe.set_user("Administrator")
try:
	from frappe_debug.scenario.params import load_scenario
	from frappe_debug.scenario.verify import verify

	assert frappe.conf.db_name.endswith("_work"), frappe.conf.db_name
	sc = load_scenario()
	result = verify(sc)
	with open("/workspace/frappe-bench/logs/s8-r13d-s8r9-verify.json", "w", encoding="utf-8") as stream:
		json.dump(result, stream, ensure_ascii=False, indent=1, default=str)
	checks = result["checks"]
	print(json.dumps({"db": frappe.conf.db_name, "E": str(sc.E), "ok": result["ok"], "total": len(checks),
		"passed": sum(1 for v in checks.values() if v["ok"])}, ensure_ascii=False))
	print("FAILED", json.dumps({k: v for k, v in checks.items() if not v["ok"]}, ensure_ascii=False, default=str)[:4000])
	for key, value in checks.items():
		if key.startswith(("supplier.", "integer_uom.", "act9.")):
			print(key, value["ok"], json.dumps(value.get("detail"), ensure_ascii=False, default=str)[:1500])
	print("SCORECARDS")
	for row in frappe.get_all("Supplier Scorecard", fields=["supplier", "supplier_score", "status"], order_by="supplier"):
		print(" ", row.supplier, round(row.supplier_score or 0, 1), row.status)
finally:
	frappe.destroy()
