"""R7: point a demo site back at its base DB and drop every registered snapshot/work DB.

Used after the 2026-10-25 disk-full crash left registries stuck in ``cloning`` (no clone
process alive), which the guarded ``drop_snapshots`` path rightly refuses. Only databases
listed in the site's own registry are dropped, through ``dbops.drop_db`` and its guards; the
base database is never touched.

Run inside the frappe container:
    env/bin/python /workspace/Spike/P1S8R7-E/reset_registry.py <site>
"""

import json
import os
import sys
from pathlib import Path

import frappe

site = sys.argv[1]
assert site in {"erx.localhost", "s8ts023preview.localhost", "s8dev.localhost"}, site
os.chdir("/workspace/frappe-bench/sites")
frappe.init(site=site, sites_path=".")
from frappe.installer import update_site_config  # noqa: E402

from frappe_debug.demo import dbops, registry  # noqa: E402

data = registry.get_registry()
base = data.get("base_db")
assert base, "registry has no base_db"
if frappe.conf.db_name != base:
	update_site_config("db_name", base)
	frappe.destroy()
	frappe.init(site=site, sites_path=".")
frappe.connect()
assert frappe.conf.db_name == base, frappe.conf.db_name

names = [entry["db"] for copies in data.get("acts", {}).values() for entry in copies.values()]
if data.get("work_db"):
	names.append(data["work_db"])
dropped = []
for name in names:
	if dbops.database_exists(name):
		dbops.drop_db(name)
		dropped.append(name)
	registry.clear_markers(name)
registry.set_registry({"base_db": None, "acts": {}})
for stale in Path(registry.registry_path()).parent.glob("*.clone.*"):
	stale.unlink()
counts = {
	doctype: frappe.db.count(doctype)
	for doctype in ("Company", "GL Entry", "Stock Ledger Entry", "Translation", "Sales Order")
}
frappe.destroy()
print(json.dumps({"site": site, "base": base, "dropped": len(dropped), "counts": counts}, ensure_ascii=False))
