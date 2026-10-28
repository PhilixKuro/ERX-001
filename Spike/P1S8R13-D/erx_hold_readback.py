"""R13 TS-037: on the erx work db, list target-wire suggestions from E-7 and shortage events after D1 (read-only, second connection)."""
import json, os
import frappe
os.chdir("/workspace/frappe-bench/sites")
frappe.init(site="erx.localhost", sites_path=".")
frappe.connect()
try:
	from frappe_debug.demo.registry import get_registry
	frappe.local.conf.db_name = get_registry()["work_db"]
	frappe.connect(set_admin_as_user=True)
	from frappe_debug.scenario.params import load_scenario
	from datetime import timedelta
	sc = load_scenario()
	item = sc.raw["act_targets"]["act9_eoq_item"]
	rows = frappe.get_all("Replenishment Suggestion", filters={"item_code": item, "calculation_date": [">=", sc.E - timedelta(days=8)]},
		fields=["name", "rule", "calculation_date", "status", "suggested_qty"], order_by="calculation_date, rule")
	for r in rows:
		print(r.calculation_date, r.rule, r.status, r.suggested_qty, r.name)
	late = frappe.get_all("Scenario Event", filters={"event_type": "缺料推迟", "event_date": [">", sc.D1]}, fields=["event_date", "work_order", "item_code"], order_by="event_date")
	print("shortage_after_D1", len(late), json.dumps(sorted({str(r.event_date) for r in late}), default=str, ensure_ascii=False))
finally:
	frappe.destroy()
