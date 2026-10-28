"""R13 TS-037 step 2: read-only verify on the erx prerun work db, plus act 9 purchase order and the 12 scorecards.

The site stays on its act 1 main copy; verify reads the work db through a second connection.
Usage (container, cwd sites/): python erx_verify.py  -> frappe-bench/logs/s8-r13d-erx-verify.json
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
	acts = {a: {k: v["state"] for k, v in c.items()} for a, c in (data.get("acts") or {}).items()}
	frappe.local.conf.db_name = work
	frappe.connect(set_admin_as_user=True)
	assert frappe.db.cur_db_name == work, frappe.db.cur_db_name
	from frappe_debug.scenario.params import load_scenario
	from frappe_debug.scenario.verify import verify

	sc = load_scenario()
	result = verify(sc)
	with open("/workspace/frappe-bench/logs/s8-r13d-erx-verify.json", "w", encoding="utf-8") as stream:
		json.dump(result, stream, ensure_ascii=False, indent=1, default=str)
	checks = result["checks"]
	print(json.dumps({"live_db": live, "verified_db": work, "E": str(sc.E), "ok": result["ok"],
		"passed": sum(v["ok"] for v in checks.values()), "total": len(checks), "acts": acts}, ensure_ascii=False))
	print("FAILED", json.dumps({k: v["detail"] for k, v in checks.items() if not v["ok"]}, ensure_ascii=False, default=str)[:3000])
	for key in ("spc.anomaly_window", "act9.eoq", "supplier.rotation", "supplier.scorecards", "supplier.standings"):
		value = checks.get(key)
		print(key, value and value["ok"], json.dumps(value and value["detail"], ensure_ascii=False, default=str)[:700])
	print("INTEGER_UOM", all(v["ok"] for k, v in checks.items() if k.startswith("integer_uom.")))
	rows = frappe.db.sql("""select po.name, po.supplier, po.docstatus, poi.item_code, poi.qty, poi.rate
	  from `tabPurchase Order` po join `tabPurchase Order Item` poi on poi.parent=po.name where po.transaction_date=%s""", sc.E, as_dict=1)
	print("PO_ON_E", json.dumps(rows, ensure_ascii=False, default=str))
	for row in frappe.get_all("Supplier Scorecard", fields=["supplier", "supplier_score", "status"], order_by="supplier"):
		print(" ", row.supplier, row.supplier_score, row.status)
finally:
	frappe.destroy()
