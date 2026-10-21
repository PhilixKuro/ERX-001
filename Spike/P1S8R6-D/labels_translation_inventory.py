import json
import frappe
from frappe.translate import get_translations_from_apps, get_translations_from_csv

frappe.init(site='test.localhost', sites_path='/workspace/frappe-bench/sites')
try:
    official = get_translations_from_apps('zh', apps=['frappe','erpnext','crm','hrms','insights','raven'])
    ours = get_translations_from_csv('zh','frappe_china')
    from frappe_china.tests.translation_overrides import OVERRIDES
    overlaps = set(ours) & set(official)
    print(json.dumps({'unregistered':{k:[official[k],ours[k]] for k in sorted(overlaps-set(OVERRIDES))},'not_overlapped':sorted(set(OVERRIDES)-overlaps),'wrong_official':{k:[v.official,official.get(k)] for k,v in OVERRIDES.items() if v.official != official.get(k)}},ensure_ascii=False))
    keys = ['Incoming','Outgoing','In Process','New','Contacted','Nurture','Qualified','Converted','Unqualified','Junk','Qualification','Demo/Making','Proposal/Quotation','Negotiation','Ready to Close','Won','Lost','Problems','None']
    print(json.dumps({k:official.get(k) for k in keys},ensure_ascii=False))
finally:
    frappe.destroy()
