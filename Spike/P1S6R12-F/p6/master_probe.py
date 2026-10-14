# Read-only: Workstation dashboard group labels under zh on erx.localhost.
import json, frappe
frappe.init(site="erx.localhost", sites_path="/workspace/frappe-bench/sites"); frappe.connect()
try:
    frappe.local.lang = "zh"
    from frappe.desk.notifications import get_open_count  # noqa
    from erpnext.manufacturing.doctype.workstation.workstation_dashboard import get_data
    print(json.dumps({"workstation_groups": [g["label"] for g in get_data()["transactions"]],
                      "merged_Master": frappe.translate.get_all_translations("zh").get("Master")}, ensure_ascii=False))
finally:
    frappe.db.rollback(); frappe.destroy()
