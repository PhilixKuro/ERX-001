import json
import os
import frappe
from frappe.translate import get_all_translations
os.chdir('/workspace/frappe-bench/sites')
frappe.init(site='s8dev.localhost', sites_path='.')
frappe.connect()
try:
    keys = ['Quotation','Sales Order','Purchase Order','Purchase Receipt','Purchase Invoice','Payment Entry','Work Order','Job Card','SPC Chart','Piece Rate Summary','Supplier Scorecard','Capacity Load','Material Request','Replenishment Suggestion']
    translations = get_all_translations('zh')
    print(json.dumps({key: translations.get(key, key) for key in keys}, ensure_ascii=False))
finally:
    frappe.db.rollback()
    frappe.destroy()
