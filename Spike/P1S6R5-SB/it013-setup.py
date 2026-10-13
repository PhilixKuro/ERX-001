# R5 IT-013：两条原定做法的临时配置。states-on／states-off／ps-on／ps-off／check。
# 只增删本脚本自己建的行（DocType State 以 title=Unpaid 且 custom=1 认，Property Setter 以 Sales Invoice／status／context 认；执行前两者都为 0），删后核为 0。
import os, sys, json, frappe
DTS = ('Sales Invoice', 'Purchase Invoice')
os.chdir('/workspace/frappe-bench/sites'); frappe.init(site='test.localhost', sites_path='.'); frappe.connect(); frappe.set_user('Administrator')
def mine():
    return {'states': frappe.get_all('DocType State', filters={'parent': ('in', DTS), 'title': 'Unpaid', 'custom': 1}, fields=['name', 'parent', 'color']),
            'ps': frappe.get_all('Property Setter', filters={'doc_type': 'Sales Invoice', 'field_name': 'status', 'property': 'context'}, fields=['name', 'value'])}
try:
    action = sys.argv[1]
    if action == 'states-on':
        assert not mine()['states'], 'states rows already exist'
        for dt in DTS:
            cf = frappe.get_doc('Customize Form'); cf.doc_type = dt; cf.fetch_to_customize()
            cf.append('states', {'title': 'Unpaid', 'color': 'Orange'}); cf.save_customization()
    elif action == 'states-off':
        for row in mine()['states']:
            frappe.db.delete('DocType State', {'name': row.name})
        for dt in DTS: frappe.clear_cache(doctype=dt)
    elif action == 'ps-on':
        assert not mine()['ps'], 'property setter exists'
        frappe.make_property_setter({'doctype': 'Sales Invoice', 'fieldname': 'status', 'property': 'context', 'value': 'Sales Invoice', 'property_type': 'Data'}, validate_fields_for_doctype=False)
        frappe.clear_cache(doctype='Sales Invoice')
    elif action == 'ps-off':
        for name in frappe.get_all('Property Setter', filters={'doc_type': 'Sales Invoice', 'field_name': 'status', 'property': 'context'}, pluck='name'):
            frappe.delete_doc('Property Setter', name)
        frappe.clear_cache(doctype='Sales Invoice')
    frappe.db.commit()
    state = mine()
    state['meta_context'] = frappe.get_meta('Sales Invoice').get_field('status').get('context')
    print(json.dumps({'action': action, **state}, default=str, ensure_ascii=False))
finally:
    frappe.destroy()
