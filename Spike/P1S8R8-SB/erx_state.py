"""Report erx.localhost registry state and D1 job cards after the failed rehearsal (read-only)."""
import json
import os

import frappe

os.chdir("/workspace/frappe-bench/sites")
frappe.init(site="erx.localhost", sites_path=".")
frappe.connect()
try:
	from frappe_debug.demo.registry import get_registry

	reg = get_registry()
	acts = {a: {k: v["state"] for k, v in c.items()} for a, c in (reg.get("acts") or {}).items()}
	print(json.dumps({"db": frappe.conf.db_name, "base": reg.get("base_db"), "work_state": reg.get("work_state"), "acts": acts}))
	rows = frappe.db.sql(
		"""select jc.name, jc.work_order, so.po_no, date(min(tl.from_time)) d from `tabJob Card` jc
		join `tabWork Order` wo on wo.name = jc.work_order left join `tabSales Order` so on so.name = wo.sales_order
		left join `tabJob Card Time Log` tl on tl.parent = jc.name
		where jc.name >= 'PO-JOB00470' group by jc.name order by jc.name""",
		as_dict=True,
	)
	for r in rows:
		print(r.name, r.work_order, r.po_no, r.d)
finally:
	frappe.destroy()
