import json, os, frappe
os.chdir("/workspace/frappe-bench/sites")
frappe.init(site="erx.localhost", sites_path="."); frappe.connect()
out = {
 "V15TEST_in_sidebar_items": frappe.db.sql("select name,parent,label from `tabWorkspace Sidebar Item` where label like '%V15TEST%'", as_dict=True),
 "V15TEST_in_sidebars": frappe.db.sql("select name from `tabWorkspace Sidebar` where title like '%V15TEST%'", as_dict=True),
 "V15TEST_in_icons": frappe.db.sql("select name from `tabDesktop Icon` where label like '%V15TEST%'", as_dict=True),
 "bug_icon_records": frappe.db.sql("select name from `tabDesktop Icon` where icon='bug'", as_dict=True)
   + frappe.db.sql("select name from `tabWorkspace Sidebar` where header_icon='bug'", as_dict=True),
 "counts_now": {
   "Workspace Sidebar": frappe.db.count("Workspace Sidebar"),
   "Workspace Sidebar Item": frappe.db.count("Workspace Sidebar Item"),
   "Desktop Icon": frappe.db.count("Desktop Icon"),
 },
 "demo_data": {
   "Company": frappe.get_all("Company", pluck="name"),
   "Account_count": frappe.db.count("Account"),
   "Warehouse_count": frappe.db.count("Warehouse"),
   "Fiscal Year": frappe.get_all("Fiscal Year", pluck="name"),
   "Item": frappe.get_all("Item", pluck="name"),
   "BOM_count": frappe.db.count("BOM"),
   "Sales Order": frappe.get_all("Sales Order", fields=["name","status","docstatus"]),
 },
}
print("===V15-CLEAN-BEGIN==="); print(json.dumps(out, ensure_ascii=False, indent=1, default=str)); print("===V15-CLEAN-END===")
frappe.destroy()
