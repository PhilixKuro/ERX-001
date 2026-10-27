"""Print the newest Error Log entries on erx.localhost (read-only)."""
import os

import frappe

os.chdir("/workspace/frappe-bench/sites")
frappe.init(site="erx.localhost", sites_path=".")
frappe.connect()
try:
	for row in frappe.get_all("Error Log", fields=["creation", "method", "error"], order_by="creation desc", limit=3):
		print("=====", row.creation, row.method)
		print((row.error or "")[-2500:])
finally:
	frappe.destroy()
