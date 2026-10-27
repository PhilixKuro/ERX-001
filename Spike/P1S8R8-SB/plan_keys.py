"""Compare SPC plan keys near the first failing day with the erx work database (read-only)."""
import json
import os

import frappe

os.chdir("/workspace/frappe-bench/sites")
plan = json.load(open("erx.localhost/private/frappe_debug/quality-plan.json", encoding="utf-8"))
keys = sorted(k for k in plan["manifest"] if "2026-01-0" in k)
print("plan keys 2026-01-0x:", len(keys))
for k in keys[:8]:
	print("  ", k)
frappe.init(site="erx.localhost", sites_path=".")
frappe.connect()
try:
	print("erx db:", frappe.conf.db_name)
	rows = frappe.db.sql(
		"""select name, work_order, operation, docstatus from `tabJob Card`
		where name in ('PO-JOB00485','PO-JOB00486','PO-JOB00487','PO-JOB00488') order by name""",
		as_dict=True,
	)
	print(json.dumps(rows, default=str, ensure_ascii=False))
	print("job cards total:", frappe.db.count("Job Card"), "max:", frappe.db.sql("select max(name) from `tabJob Card`")[0][0])
finally:
	frappe.destroy()
