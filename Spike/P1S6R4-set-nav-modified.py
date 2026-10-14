import os,frappe,sys
os.chdir('/workspace/frappe-bench/sites'); frappe.init(site=sys.argv[1],sites_path='.'); frappe.connect(); frappe.db.set_value('Workspace Sidebar','Business Flow','modified',sys.argv[2]); frappe.db.commit(); frappe.destroy()
