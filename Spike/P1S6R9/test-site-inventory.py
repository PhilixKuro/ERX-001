"""R9 TS-035 准备：只读查测试站现有数据，决定哪些屏要临时造数。
容器内 bench 目录：env/bin/python /workspace/Spike/P1S6R9/test-site-inventory.py test.localhost"""
import json
import os
import sys

os.chdir("/workspace/frappe-bench/sites")
import frappe

frappe.init(site=sys.argv[1], sites_path=".")
frappe.connect()
out = {}
for doctype, filters in [
	("Company", {}), ("Work Order", {}), ("Purchase Invoice", {"docstatus": 1}), ("Supplier", {"is_internal_supplier": 1}),
	("GL Entry", {}), ("Stock Ledger Entry", {}), ("Version", {}), ("Sales Invoice", {"docstatus": 0}), ("Timesheet", {}),
	("Raven User", {}), ("CRM Lead", {}), ("CRM Deal", {}), ("Contact", {}), ("Salutation", {}), ("Workstation", {}),
	("Customer", {}), ("Item", {}), ("BOM", {"docstatus": 1}),
]:
	try:
		out[doctype] = frappe.db.count(doctype, filters)
	except Exception as error:
		out[doctype] = f"ERR {error}"
out["salutations"] = frappe.get_all("Salutation", pluck="name")
out["companies"] = frappe.get_all("Company", fields=["name", "country", "default_currency"], limit=10)
out["lang"] = frappe.db.get_single_value("System Settings", "language")
out["admin_lang"] = frappe.db.get_value("User", "Administrator", "language")
print(json.dumps(out, ensure_ascii=False, default=str, indent=1))
frappe.destroy()
