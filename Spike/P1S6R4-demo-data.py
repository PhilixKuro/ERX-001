import os
import frappe

COMPANY = '华东弹簧有限公司'
PREFIX = '_S6 Demo'

def main():
    os.chdir('/workspace/frappe-bench/sites')
    frappe.init(site='erx.localhost', sites_path='.')
    frappe.connect()
    frappe.set_user('Administrator')
    try:
        abbr = frappe.db.get_value('Company', COMPANY, 'abbr')
        warehouse = f'{PREFIX} Warehouse - {abbr}'
        if not frappe.db.exists('Warehouse', warehouse):
            frappe.get_doc({'doctype':'Warehouse','warehouse_name':PREFIX+' Warehouse','company':COMPANY}).insert()
        supplier_group = frappe.db.get_value('Supplier Group', {'is_group': 0}, 'name')
        customer_group = frappe.db.get_value('Customer Group', {'is_group': 0}, 'name')
        item_group = frappe.db.get_value('Item Group', {'is_group': 0}, 'name')
        territory = frappe.db.get_value('Territory', {'is_group': 0}, 'name')
        if not frappe.db.exists('Supplier', PREFIX+' Supplier'):
            frappe.get_doc({'doctype':'Supplier','supplier_name':PREFIX+' Supplier','supplier_group':supplier_group,'supplier_type':'Company'}).insert()
        if not frappe.db.exists('Customer', PREFIX+' Customer'):
            frappe.get_doc({'doctype':'Customer','customer_name':PREFIX+' Customer','customer_group':customer_group,'territory':territory}).insert()
        if not frappe.db.exists('Item', PREFIX+' Raw'):
            frappe.get_doc({'doctype':'Item','item_code':PREFIX+' Raw','item_name':PREFIX+' Raw','item_group':item_group,'stock_uom':'Nos','is_stock_item':1}).insert()
        frappe.db.commit()
        print(frappe.as_json({'company':COMPANY,'warehouse':warehouse,'prefix':PREFIX}))
    finally:
        frappe.destroy()

if __name__ == '__main__': main()
