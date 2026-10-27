"""S8 R8 SB: run the read-only scenario verify on the erx rehearsal work database.

The site stays on its act 1 main copy; verify reads the work db through a second connection so
the live site is not switched. Usage (container, cwd sites/): python erx_verify.py
"""

import json
import os

import frappe

SITE = "erx.localhost"
os.chdir("/workspace/frappe-bench/sites")
frappe.init(site=SITE, sites_path=".")
frappe.connect()
try:
	from frappe_debug.demo.registry import get_registry

	data = get_registry()
	work = data["work_db"]
	live = frappe.conf.db_name
	frappe.local.conf.db_name = work
	frappe.connect(set_admin_as_user=True)
	assert frappe.db.cur_db_name == work, frappe.db.cur_db_name
	from frappe_debug.scenario.params import load_scenario
	from frappe_debug.scenario.verify import verify

	result = verify(load_scenario())
	out = "/workspace/frappe-bench/logs/s8-r8sb-erx-verify.json"
	with open(out, "w", encoding="utf-8") as stream:
		json.dump(result, stream, ensure_ascii=False, indent=1, default=str)
	failed = {key: value for key, value in result["checks"].items() if not value["ok"]}
	print(
		json.dumps(
			{
				"live_db": live,
				"verified_db": work,
				"ok": result["ok"],
				"passed": sum(v["ok"] for v in result["checks"].values()),
				"total": len(result["checks"]),
				"failed": {k: json.dumps(v["detail"], ensure_ascii=False, default=str)[:600] for k, v in failed.items()},
			},
			ensure_ascii=False,
		)
	)
finally:
	frappe.destroy()
