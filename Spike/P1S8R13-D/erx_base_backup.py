"""R13 TS-037 step 3: back up the erx clean base db (with files) while the live site stays on its act 1 main copy.

The base db is read through a second connection (same as erx_verify.py); counts are asserted clean first.
Usage (container, cwd sites/): python erx_base_backup.py
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

	base = get_registry()["base_db"]
	live = frappe.conf.db_name
	assert live != base and live.startswith(base), (live, base)
	frappe.local.conf.db_name = base
	frappe.connect(set_admin_as_user=True)
	assert frappe.db.cur_db_name == base, frappe.db.cur_db_name
	counts = {dt: frappe.db.count(dt) for dt in ("Company", "Translation", "GL Entry", "Stock Ledger Entry", "Sales Order")}
	assert counts == {"Company": 1, "Translation": 0, "GL Entry": 0, "Stock Ledger Entry": 0, "Sales Order": 0}, counts
	from frappe.utils.backups import new_backup

	backup = new_backup(ignore_files=False, force=True)
	print(json.dumps({"live_db": live, "backed_up_db": base, "counts": counts,
		"files": [backup.backup_path_db, backup.backup_path_files, backup.backup_path_private_files, backup.backup_path_conf]}, ensure_ascii=False))
finally:
	frappe.destroy()
