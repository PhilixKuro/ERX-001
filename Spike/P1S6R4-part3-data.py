import json
import os
from pathlib import Path

import frappe
from frappe.utils import nowdate
from frappe_china.tests.utils import make_cn_company

STATE = Path('/workspace/Spike/P1S6R4-part3-state.json')
COMPANY = '_FCT S6 Part3'
PREFIX = '_FCT S6P3'

def prepare():
    assert not frappe.db.exists('Company', COMPANY), 'Existing probe company; cleanup before rerun'
    frappe.local.lang = 'zh'
    company = make_cn_company(COMPANY, 'S6P3')
    state = {'company': COMPANY, 'docs': []}
    def remember(doc):
        state['docs'].append([doc.doctype, doc.name])
        return doc
    account = lambda number: frappe.db.get_value('Account', {'company': COMPANY, 'account_number': number, 'is_group': 0})
    warehouse = remember(frappe.get_doc({'doctype': 'Warehouse', 'warehouse_name': PREFIX, 'company': COMPANY}).insert())
    state['warehouse'] = warehouse.name
    state['employee'] = remember(frappe.get_doc({'doctype': 'Employee', 'first_name': PREFIX, 'gender': 'Male', 'date_of_birth': '1990-01-01', 'date_of_joining': '2025-01-01', 'company': COMPANY, 'status': 'Active'}).insert()).name
    state['items'] = []
    for suffix in ('RAW', 'FG'):
        item = remember(frappe.get_doc({'doctype': 'Item', 'item_code': f'{PREFIX}-{suffix}', 'item_name': f'{PREFIX}-{suffix}', 'item_group': 'Products', 'stock_uom': 'Nos', 'is_stock_item': 1, 'valuation_rate': 10}).insert())
        state['items'].append(item.name)
    state['operation'] = remember(frappe.get_doc({'doctype': 'Operation', 'name': PREFIX, 'operation': PREFIX}).insert()).name
    state['journals'] = {}
    for label, opening in (('opening', 'Yes'), ('normal', 'No')):
        doc = frappe.get_doc({'doctype': 'Journal Entry', 'company': COMPANY, 'posting_date': nowdate(), 'is_opening': opening,
                             'accounts': [{'account': account('1001'), 'debit_in_account_currency': 100, 'cost_center': company.cost_center},
                                          {'account': account('3001'), 'credit_in_account_currency': 100, 'cost_center': company.cost_center}]})
        doc.insert(); doc.submit(); remember(doc)
        state['journals'][label] = doc.name
    stock = frappe.get_doc({'doctype': 'Stock Reconciliation', 'company': COMPANY, 'purpose': 'Opening Stock',
                           'posting_date': nowdate(), 'posting_time': '08:00:00', 'set_posting_time': 1,
                           'expense_account': account('9999'), 'cost_center': company.cost_center,
                           'items': [{'item_code': state['items'][0], 'warehouse': warehouse.name, 'qty': 10, 'valuation_rate': 10}]})
    stock.insert(); stock.submit(); remember(stock)
    state['opening_stock'] = stock.name
    normal = frappe.get_doc({'doctype': 'Stock Entry', 'company': COMPANY, 'stock_entry_type': 'Material Receipt',
                            'posting_date': nowdate(), 'posting_time': '09:00:00', 'set_posting_time': 1,
                            'items': [{'item_code': state['items'][0], 't_warehouse': warehouse.name, 'qty': 1,
                                       'basic_rate': 10, 'expense_account': account('1901'), 'cost_center': company.cost_center}]})
    normal.insert(); normal.submit(); remember(normal)
    state['normal_stock'] = normal.name
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding='utf-8')
    frappe.db.commit()
    print(frappe.as_json(state))

def cleanup():
    state = json.loads(STATE.read_text(encoding='utf-8'))
    assert state['company'] == COMPANY
    for doctype, name in reversed(state['docs']):
        if not frappe.db.exists(doctype, name):
            continue
        doc = frappe.get_doc(doctype, name)
        if doc.docstatus == 1:
            doc.cancel()
        if doctype in ('Journal Entry', 'Stock Entry', 'Stock Reconciliation'):
            for ledger in ('GL Entry', 'Stock Ledger Entry'):
                frappe.db.delete(ledger, {'company': COMPANY, 'voucher_type': doctype, 'voucher_no': name})
            for row in frappe.get_all('Repost Item Valuation', filters={'based_on': 'Transaction', 'voucher_type': doctype, 'voucher_no': name}, pluck='name'):
                frappe.db.delete('Repost Item Valuation', {'name': row})
        if doctype == 'Item':
            for row in frappe.get_all('Repost Item Valuation', filters={'item_code': name}, pluck='name'):
                frappe.db.delete('Repost Item Valuation', {'name': row})
        if doctype == 'Warehouse':
            for row in frappe.get_all('Bin', filters={'warehouse': name}, pluck='name'):
                frappe.delete_doc('Bin', row, ignore_permissions=True)
        frappe.delete_doc(doctype, name, ignore_permissions=True)
    for row in frappe.get_all('Bin', filters={'warehouse': state['warehouse']}, pluck='name'):
        frappe.delete_doc('Bin', row, ignore_permissions=True)
    frappe.delete_doc('Company', COMPANY, ignore_permissions=True)
    frappe.db.commit()
    assert not frappe.db.exists('Company', COMPANY)
    assert not any(frappe.db.exists(dt, name) for dt, name in state['docs'])
    state['cleanup_verified'] = True
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding='utf-8')
    print(frappe.as_json(state))

def manufacturing_setup():
    state = json.loads(STATE.read_text(encoding='utf-8'))
    if not state.get('workstation'):
        workstation = frappe.get_doc({'doctype': 'Workstation', 'workstation_name': PREFIX,
                                      'production_capacity': 1,
                                      'working_hours': [{'start_time': '00:00:00', 'end_time': '23:59:59'}]}).insert()
        state['workstation'] = workstation.name
        state['docs'].append([workstation.doctype, workstation.name])
        STATE.write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding='utf-8')
        frappe.db.commit()
    print(frappe.as_json(state))

def make_work_order():
    state = json.loads(STATE.read_text(encoding='utf-8'))
    bom = frappe.get_doc('BOM', frappe.db.get_value('BOM', {'item': state['items'][1], 'company': COMPANY}, 'name'))
    state['bom'] = bom.name
    if ['BOM', bom.name] not in state['docs']:
        state['docs'].append(['BOM',bom.name])
    if bom.docstatus == 0:
        bom.submit()
    old = frappe.db.get_single_value('Manufacturing Settings','disable_capacity_planning')
    try:
        frappe.db.set_single_value('Manufacturing Settings','disable_capacity_planning',1)
        order = frappe.get_doc({'doctype':'Work Order','production_item':state['items'][1],'bom_no':bom.name,
                               'company':COMPANY,'qty':1,'source_warehouse':state['warehouse'],
                               'wip_warehouse':state['warehouse'],'fg_warehouse':state['warehouse'],
                               'skip_transfer':1,'planned_start_date':frappe.utils.now_datetime()})
        order.set_work_order_operations()
        order.get_items_and_operations_from_bom()
        order.insert();order.submit()
        state['work_order'] = order.name
        state['docs'].append(['Work Order',order.name])
        cards = frappe.get_all('Job Card',filters={'work_order':order.name},pluck='name')
        assert len(cards)==1,cards
        state['job_card'] = cards[0]
        card = frappe.get_doc('Job Card',cards[0]);card.skip_material_transfer=1;card.save()
        state['docs'].append(['Job Card',cards[0]])
    finally:
        frappe.db.set_single_value('Manufacturing Settings','disable_capacity_planning',old)
    STATE.write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding='utf-8')
    frappe.db.commit()
    print(frappe.as_json(state))

def reset_job():
    state = json.loads(STATE.read_text(encoding='utf-8'))
    card = frappe.get_doc('Job Card',state['job_card'])
    assert card.company == COMPANY and card.docstatus == 0
    card.set('time_logs',[]);card.set('employee',[])
    card.is_paused=0;card.current_time=0;card.started_time=None
    card.total_completed_qty=0;card.total_time_in_mins=0
    card.save();frappe.db.commit()
    print(frappe.as_json({'job_card':card.name,'time_logs':len(card.time_logs),'status':card.status}))

def main(action):
    os.chdir('/workspace/frappe-bench/sites')
    frappe.init(site='test.localhost', sites_path='.')
    frappe.connect(); frappe.set_user('Administrator')
    try:
        {'prepare': prepare, 'cleanup': cleanup, 'manufacturing-setup':manufacturing_setup,'work-order':make_work_order,'reset-job':reset_job}[action]()
    finally:
        frappe.db.rollback(); frappe.destroy()

if __name__ == '__main__':
    import sys
    main(sys.argv[1])
