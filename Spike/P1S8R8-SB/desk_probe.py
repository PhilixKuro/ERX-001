"""Render /desk for Administrator on erx.localhost and print the real exception (read-only)."""
import os
import traceback

import frappe

os.chdir("/workspace/frappe-bench/sites")
frappe.init(site="erx.localhost", sites_path=".")
frappe.connect()
frappe.set_user("Administrator")
try:
	from frappe.boot import get_bootinfo

	boot = get_bootinfo()
	print("boot ok", len(str(boot)))
	from frappe.website.serve import get_response_without_exception_handling as get_response

	frappe.local.request = None
	response = get_response("desk")
	print("status", response.status_code)
except Exception:
	traceback.print_exc()
finally:
	frappe.destroy()
