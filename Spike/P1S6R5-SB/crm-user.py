# R5 IT-027：非管理员 CRM 探针用户。create／zh／en／cleanup；只动本脚本建的用户
import os, sys, frappe
from frappe.utils.password import update_password
EMAIL = '_fct_s6_crm_probe@example.com'
os.chdir('/workspace/frappe-bench/sites'); frappe.init(site='test.localhost', sites_path='.'); frappe.connect(); frappe.set_user('Administrator')
try:
    action = sys.argv[1]
    if action == 'create':
        assert not frappe.db.exists('User', EMAIL), 'probe user exists; cleanup first'
        user = frappe.get_doc({'doctype': 'User', 'email': EMAIL, 'first_name': 'S6 CRM probe', 'user_type': 'System User', 'send_welcome_email': 0, 'language': 'zh'})
        user.append('roles', {'role': 'Sales User'})
        user.insert()
        update_password(EMAIL, 'S6CrmProbe2026', logout_all_sessions=True)
    elif action in ('zh', 'en'):
        user = frappe.get_doc('User', EMAIL); user.language = action; user.save(); frappe.clear_cache(user=EMAIL)
    elif action == 'cleanup':
        if frappe.db.exists('User', EMAIL): frappe.delete_doc('User', EMAIL, ignore_permissions=True)
    frappe.db.commit()
    exists = frappe.db.exists('User', EMAIL)
    print({'action': action, 'exists': bool(exists), 'roles': frappe.get_roles(EMAIL) if exists else [], 'lang': frappe.db.get_value('User', EMAIL, 'language') if exists else None})
finally:
    frappe.destroy()
