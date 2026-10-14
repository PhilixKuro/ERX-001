# Read-only: frappe_china.translation_check.find_problems() on erx.localhost, then rollback.
import json, frappe
frappe.init(site="erx.localhost", sites_path="/workspace/frappe-bench/sites"); frappe.connect()
try:
    from frappe_china.translation_check import find_problems
    print(json.dumps({"find_problems": find_problems(), "translation_rows": frappe.db.count("Translation")}, ensure_ascii=False))
finally:
    frappe.db.rollback(); frappe.destroy()
