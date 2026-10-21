import csv
import json
from pathlib import Path

import frappe
from frappe.translate import get_translations_from_apps

frappe.init(site='test.localhost', sites_path='/workspace/frappe-bench/sites')
frappe.connect()
try:
    official = get_translations_from_apps('zh', apps=['frappe','erpnext','crm','hrms','insights','raven'])
    sources = ['Replenishment Strategy Comparison','Comparison Period','Comparison Days','Average Inventory Value',
               'Purchase Order Count','Inventory Related Total Cost','Shortage Count','Period {0}',
               'Company {0} does not exist','SPC Chart']
    print(json.dumps({source: official[source] for source in sources if source in official}, ensure_ascii=False))
    from frappe_china.tests.translation_overrides import OVERRIDES
    from frappe.translate import get_translations_from_csv
    ours = get_translations_from_csv('zh','frappe_china')
    extra = (set(ours) & set(official)) - set(OVERRIDES)
    print(json.dumps({source: {'official': official[source], 'ours': ours[source]} for source in sorted(extra)}, ensure_ascii=False))
finally:
    frappe.destroy()
