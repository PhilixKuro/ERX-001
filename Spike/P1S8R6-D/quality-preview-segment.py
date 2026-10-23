"""CLI-only SPC schedule capture on the disposable preview work database."""
import json
import os
import sys

import frappe

site, start, end, job_id = sys.argv[1:]
assert site == "s8ts023preview.localhost"
os.chdir("/workspace/frappe-bench/sites")
frappe.init(site=site, sites_path=".")
frappe.connect()
frappe.set_user("Administrator")
try:
    from frappe_debug.demo.registry import get_registry
    from frappe_debug.scenario import runner

    data = get_registry()
    assert data.get("work_state") == "ready"
    assert frappe.conf.db_name == data["work_db"]
    assert not runner._quality_plan_path().exists()
    runner._write_status({"job_id": job_id, "state": "running", "day": None, "error": None})
    print(json.dumps({"started": job_id}), flush=True)
    result = runner.generate(start, end, job_id=job_id, preview_quality_schedule=True)
    print(json.dumps(result.__json__(), default=str), flush=True)
finally:
    frappe.destroy()
