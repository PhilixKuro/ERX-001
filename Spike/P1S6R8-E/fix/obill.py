import sys, frappe
frappe.init(site=sys.argv[1], sites_path="/workspace/frappe-bench/sites"); frappe.connect()
if len(sys.argv) > 2:
    frappe.db.set_single_value("Accounts Settings", "over_billing_allowance", float(sys.argv[2])); frappe.db.commit()
print(repr(frappe.db.get_single_value("Accounts Settings", "over_billing_allowance")), repr(frappe.db.get_single_value("Accounts Settings", "role_allowed_to_over_bill")))
