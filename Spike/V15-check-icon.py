import json, os, frappe
os.chdir("/workspace/frappe-bench/sites")
frappe.init(site="erx.localhost", sites_path="."); frappe.connect()
print(json.dumps({
 "frappe_framework_icon": frappe.get_all("Desktop Icon", filters={"label":["like","%Frappe%"]}, fields=["name","icon_type","app","standard"]),
 "app_type_icons": frappe.get_all("Desktop Icon", filters={"icon_type":"App"}, fields=["name","app"]),
 "total": frappe.db.count("Desktop Icon"),
}, ensure_ascii=False, indent=1, default=str))
frappe.destroy()
