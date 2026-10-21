"""TS-009 technical preflight; test site only, rollback all data."""
import json
from unittest.mock import patch
import frappe

frappe.init(site='test.localhost', sites_path='/workspace/frappe-bench/sites')
frappe.connect()
try:
    assert frappe.local.site == 'test.localhost'
    frappe.set_user('Administrator')
    frappe.local.lang = 'zh'
    from frappe_china.production_plus.report.spc_control_chart.spc_control_chart import execute
    from frappe_china.tests.spc_data import make_spc_inspections
    fixture = make_spc_inspections()
    result = execute({'item_code':fixture['item'],'specification':fixture['parameter'],'from_date':'2026-10-01','to_date':'2026-10-01'})
    print(json.dumps({'spc_columns':[c['label'] for c in result[0]],'summary':[r['label'] for r in result[4]],'prepared':frappe.db.get_value('Report','SPC Control Chart','prepared_report')},ensure_ascii=False))
    # Probe the proposed field precision without persisting a Custom Field change.
    df = frappe.get_meta('Operation').get_field('cn_piece_rate')
    previous = df.precision
    try:
        df.precision = '4'
        op = frappe.get_doc({'doctype':'Operation','name':'_FCT SL008 precision '+frappe.generate_hash(length=8),'operation':'Wire Coiling','cn_piece_rate':0.004}).insert()
        op.reload()
        print(json.dumps({'precision':op.precision('cn_piece_rate'),'stored':op.cn_piece_rate}))
        assert op.cn_piece_rate == 0.004
    finally:
        df.precision = previous
    from frappe.boot import get_success_action
    print(json.dumps({'success_actions':get_success_action()},ensure_ascii=False,default=str))
finally:
    frappe.db.rollback()
    frappe.destroy()
