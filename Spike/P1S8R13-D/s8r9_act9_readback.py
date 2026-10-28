"""R13 TS-037 step 1: read back the act 9 purchase order on E and the 12 supplier scorecards (s8r9 work db, read-only)."""
import json, os
import frappe
os.chdir("/workspace/frappe-bench/sites")
frappe.init(site="s8r9.localhost", sites_path=".")
frappe.connect()
try:
	assert frappe.conf.db_name.endswith("_work"), frappe.conf.db_name
	rows = frappe.db.sql("""select po.name, po.supplier, po.transaction_date, po.schedule_date, po.docstatus, poi.item_code, poi.qty, poi.rate, poi.material_request
	  from `tabPurchase Order` po join `tabPurchase Order Item` poi on poi.parent=po.name where po.transaction_date='2026-10-28'""", as_dict=1)
	print("PO_ON_E", json.dumps(rows, ensure_ascii=False, default=str))
	for row in frappe.get_all("Supplier Scorecard", fields=["supplier", "supplier_score", "status"], order_by="supplier"):
		print(" ", row.supplier, row.supplier_score, row.status)
finally:
	frappe.destroy()
