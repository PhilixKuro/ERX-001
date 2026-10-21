"""Read-only SL-010 acceptance data, always restricted to the test site."""

import json

import frappe

frappe.init(site="test.localhost", sites_path="/workspace/frappe-bench/sites")
frappe.connect()
try:
    assert frappe.local.site == "test.localhost"
    from frappe_china.accounting.chart import CN_CHART_NAME

    result = {
        "site": frappe.local.site,
        "genders": frappe.get_all("Gender", pluck="name", order_by="name"),
        "salutations": frappe.get_all("Salutation", pluck="name", order_by="name"),
        "batch_enabled": frappe.db.get_single_value(
            "Stock Settings", "enable_serial_and_batch_no_for_item"
        ),
        "administrator": frappe.db.get_value(
            "User", "Administrator", ["first_name", "full_name"], as_dict=True
        ),
        "crm_company": frappe.db.get_single_value("ERPNext CRM Settings", "erpnext_company"),
        "cn_companies": frappe.get_all(
            "Company", filters={"chart_of_accounts": CN_CHART_NAME}, pluck="name"
        ),
    }
    print(json.dumps(result, default=str, ensure_ascii=False))
finally:
    frappe.destroy()
