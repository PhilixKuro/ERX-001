"""Compare naming-series counters of the erx and s8r9 clean base databases (read-only)."""
import json
import os

import frappe

os.chdir("/workspace/frappe-bench/sites")
out = {}
for site, db in (("erx.localhost", "_2bd5b09209543e8e"), ("s8r9.localhost", "_0a40885136138661")):
	frappe.init(site=site, sites_path=".")
	frappe.connect()
	rows = frappe.db.sql(f"select name, current from `{db}`.`tabSeries` order by name")
	out[site] = dict(rows)
	out[site + ":counts"] = {
		dt: frappe.db.sql(f"select count(*) from `{db}`.`tab{dt}`")[0][0]
		for dt in ("Item", "Customer", "Supplier", "Employee", "BOM", "Workstation", "CRM Lead", "User")
	}
	frappe.destroy()
a, b = out["erx.localhost"], out["s8r9.localhost"]
diff = {k: (a.get(k), b.get(k)) for k in sorted(set(a) | set(b)) if a.get(k) != b.get(k)}
print(json.dumps({"series_diff": diff, "erx": out["erx.localhost:counts"], "s8r9": out["s8r9.localhost:counts"]}, ensure_ascii=False))
