"""S8 R8 SB step 1b: full-year preview generation on the s8r9 work database, then export and verify.

Usage (container, cwd sites/): python s8r9_generate.py generate | export | verify
"""

import json
import os
import sys
import time
from datetime import timedelta

import frappe

SITE = "s8r9.localhost"
step = sys.argv[1]
os.chdir("/workspace/frappe-bench/sites")
frappe.init(site=SITE, sites_path=".")
frappe.connect()
frappe.set_user("Administrator")
try:
	from frappe_debug.demo.registry import get_registry
	from frappe_debug.scenario import runner
	from frappe_debug.scenario.params import load_scenario

	data = get_registry()
	assert data.get("work_state") == "ready", data
	assert frappe.conf.db_name == data["work_db"], (frappe.conf.db_name, data)
	sc = load_scenario()
	if step == "generate":
		assert not runner._quality_plan_path().exists()
		job_id = f"s8r8sb-s8r9-{int(time.time())}"
		runner._write_status({"job_id": job_id, "state": "running", "day": None, "error": None})
		started = time.time()
		print(json.dumps({"job": job_id, "S": str(sc.S), "E": str(sc.E), "D1": str(sc.D1), "D2": str(sc.D2)}), flush=True)
		result = runner.generate(sc.S, sc.E - timedelta(days=1), job_id=job_id, preview_quality_schedule=True)
		payload = result.__json__()
		print(
			json.dumps(
				{"seconds": round(time.time() - started, 1), **{k: v for k, v in payload.items() if k != "day_durations"}},
				default=str,
				ensure_ascii=False,
			),
			flush=True,
		)
	elif step == "export":
		from frappe_debug.scenario.quality import export_quality_sample_plan

		path = export_quality_sample_plan()
		with open(path, encoding="utf-8") as stream:
			plan = json.load(stream)
		print(
			json.dumps(
				{
					"last_generated": str(runner._last_generated_date(sc)),
					"plan_path": path,
					"version": plan["version"],
					"attempts": plan["attempts"],
					"groups": len(plan["manifest"]),
				},
				ensure_ascii=False,
			)
		)
	elif step == "verify":
		from frappe_debug.scenario.verify import verify

		result = verify(sc)
		failed = {key: value for key, value in result["checks"].items() if not value["ok"]}
		out = "/workspace/frappe-bench/logs/s8-r8sb-s8r9-verify.json"
		with open(out, "w", encoding="utf-8") as stream:
			json.dump(result, stream, ensure_ascii=False, indent=1, default=str)
		picked = {
			key: result["checks"].get(key)
			for key in (
				"accounts.received_not_billed",
				"schedule.employee_overlap",
				"staff.reporting_employees",
				"crm.customer_pool",
				"crm.deal_progress",
				"supplier.rotation",
				"schedule.overlap",
				"schedule.cross_day",
			)
		}
		print(json.dumps({"ok": result["ok"], "failed": sorted(failed), "picked": picked}, ensure_ascii=False, default=str))
	else:
		raise SystemExit(f"unknown step {step}")
finally:
	frappe.destroy()
