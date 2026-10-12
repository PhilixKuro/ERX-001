# TS-023 不通过屏定性：查命中词背后是数据还是界面文案（只读）
import os, frappe
os.chdir('/workspace/frappe-bench/sites'); frappe.init(site='erx.localhost', sites_path='.'); frappe.connect()
print('raven channels', frappe.get_all('Raven Channel', fields=['name', 'channel_name', 'owner', 'creation'], limit=5))
print('uom Nos', frappe.db.exists('UOM', 'Nos'), frappe.get_meta('UOM').translated_doctype)
print('deal status', frappe.get_all('CRM Deal Status', pluck='name'))
print('lead source', frappe.get_all('CRM Lead Source', pluck='name') if frappe.db.table_exists('CRM Lead Source') else None)
print('item price', frappe.get_all('Item Price', fields=['name', 'item_code'], limit=5))
print('version null sample', frappe.db.sql("select count(*) from tabVersion where data like '%%null%%'"))
frappe.local.lang = 'zh'
from frappe import _
for s in ['Purchase Receipt', 'Journal Entry', 'Nos', 'Qualification', 'Empty', 'Forecasted Sales', 'Select', 'of', 'Nov', 'general', '1 Filter Applied', '{0} Filter Applied', 'Click to sort by {0}']:
    print(repr(s), '->', repr(_(s)))
frappe.destroy()
