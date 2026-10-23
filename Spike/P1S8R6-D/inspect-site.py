"""Read-only diagnosis of the two S8 development sites; never inspect credentials."""
import json
import os
import sys

import frappe

site = sys.argv[1]
assert site in {"s8dev.localhost", "s8ts023preview.localhost", "test.localhost"}
os.chdir("/workspace/frappe-bench/sites")
frappe.init(site=site, sites_path=".")
frappe.connect()
frappe.set_user("Administrator")
try:
    from frappe_debug.demo.progress import get_progress
    from frappe_debug.demo.registry import get_registry
    from frappe_debug.scenario.params import load_scenario
    from frappe_debug.scenario.runner import _last_generated_date

    result = {"site": site, "db": frappe.conf.db_name,
              "last_generated": _last_generated_date(load_scenario()),
              "registry": get_registry(), "progress": get_progress(),
              "counts": {dt: frappe.db.count(dt) for dt in
                         ("Sales Order", "GL Entry", "Stock Ledger Entry", "Scenario Event", "Work Order")}}
    print(json.dumps(result, default=str, ensure_ascii=False))
finally:
    frappe.db.rollback()
    frappe.destroy()
