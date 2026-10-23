"""Read only the registered finished work database; never connect to originals."""
import json
import os
from datetime import timedelta
from pathlib import Path

import frappe
from frappe.utils import flt, getdate

os.chdir('/workspace/frappe-bench/sites')
frappe.init(site='s8dev.localhost', sites_path='.')
registry = json.loads(Path(frappe.get_site_path('private/frappe_debug/snapshots.json')).read_text())
work = registry['work_db']
assert work == registry['base_db'] + '_work' and registry['work_state'] == 'ready'
assert not work.endswith('_o')
frappe.conf.db_name = work
frappe.connect()
frappe.set_user('Administrator')
try:
    from frappe_debug.demo.progress import get_progress
    from frappe_debug.scenario.params import load_scenario
    progress = get_progress()
    refs = progress['refs']
    if isinstance(refs, str):
        refs = json.loads(refs)
    sc = load_scenario()
    assert progress['act'] == 9 and progress['step'] == 6
    checks = {}
    def check(key, ok, detail):
        checks[key] = {'ok': bool(ok), 'detail': detail}
    payment = frappe.get_doc('Payment Entry', refs['payment1'])
    account = frappe.db.get_value('Account', payment.paid_from, 'account_number')
    check('D1_payment', payment.docstatus == 1 and getdate(payment.posting_date) == sc.D1
          and payment.mode_of_payment == 'Wire Transfer' and account == '1002'
          and payment.reference_no == 'DEMO-WIRE-D1' and getdate(payment.reference_date) == sc.D1,
          {'name': payment.name, 'date': payment.posting_date, 'mode': payment.mode_of_payment,
           'paid_from': payment.paid_from, 'account_number': account, 'reference_no': payment.reference_no,
           'reference_date': payment.reference_date})
    order = frappe.get_doc('Work Order', refs['work_order1'])
    cards = frappe.get_all('Job Card', filters={'work_order': order.name},
                           fields=['name','docstatus','for_quantity','total_completed_qty','process_loss_qty','operation_id'])
    manufacture = frappe.get_doc('Stock Entry', refs['manufacture_entry1'])
    output = sum(flt(row.qty) for row in manufacture.items if row.is_finished_item)
    loss = sum(flt(row.process_loss_qty) for row in cards)
    check('production_quantity', len(cards) == 9 and all(row.docstatus == 1 for row in cards)
          and abs(loss - 60) < 1e-6 and abs(output - flt(order.produced_qty)) < 1e-6
          and abs(output - (flt(order.qty) - 60)) < 1e-6,
          {'work_order': order.name, 'qty': order.qty, 'produced_qty': order.produced_qty,
           'manufacture': manufacture.name, 'finished_qty': output, 'loss': loss, 'cards': cards})
    check('production_cost', manufacture.docstatus == 1 and flt(manufacture.total_additional_costs) > 0
          and flt(order.actual_operating_cost) > 0,
          {'actual_operating_cost': order.actual_operating_cost,
           'additional_costs': [row.as_dict() for row in manufacture.additional_costs],
           'total_additional_costs': manufacture.total_additional_costs,
           'total_outgoing_value': manufacture.total_outgoing_value,
           'total_incoming_value': manufacture.total_incoming_value})
    suggestion = frappe.get_doc('Replenishment Suggestion', refs['eoq_suggestion'])
    request = frappe.get_doc('Material Request', refs['mr9'])
    requested = sum(flt(row.qty) for row in request.items if row.item_code == suggestion.item_code)
    check('EOQ_adoption', suggestion.status == 'Adopted' and suggestion.rule == 'EOQ'
          and getdate(suggestion.calculation_date) == sc.E and request.docstatus == 1
          and abs(requested - flt(suggestion.suggested_qty)) < 1e-6,
          {'suggestion': suggestion.name, 'item': suggestion.item_code, 'status': suggestion.status,
           'suggested_qty': suggestion.suggested_qty, 'request': request.name, 'adopted_qty': requested})
    prices = frappe.get_all('Item Price', filters={'item_code': suggestion.item_code, 'buying': 1},
                            fields=['name','supplier','valid_from','valid_upto','price_list_rate'],
                            order_by='valid_from desc')
    effective = [row for row in prices if row.supplier and (not row.valid_from or getdate(row.valid_from) <= sc.E)
                 and (not row.valid_upto or getdate(row.valid_upto) >= sc.E)]
    check('supplier_prices', len({row.supplier for row in effective}) >= 2,
          {'effective': effective, 'history_count': len(prices), 'latest': prices[:20]})
    periods = frappe.get_all('Supplier Scorecard Period', filters={'docstatus': 1},
                             fields=['supplier','start_date','end_date','total_score'])
    cutoff = sc.E.replace(day=1) - timedelta(days=1)
    latest = {}
    for row in periods:
        latest[row.supplier] = max(latest.get(row.supplier, getdate(row.end_date)), getdate(row.end_date))
    check('supplier_scores', len(latest) == 12 and all(day == cutoff for day in latest.values()),
          {'cutoff': cutoff, 'latest_by_supplier': latest, 'periods': len(periods)})
    month_end = sc.D2.replace(day=1) - timedelta(days=1)
    summaries = frappe.get_all('Piece Rate Summary', filters={'docstatus': 1,'to_date': month_end},
                               fields=['name','from_date','to_date','additional_salary','total_amount'])
    check('piece_rate_previous_month', bool(summaries) and all(row.additional_salary for row in summaries), summaries)
    closing = frappe.get_doc('Month End Closing Voucher', refs['closing_voucher'])
    worksheet = frappe.get_doc('Cash Flow Worksheet', refs['cash_flow_worksheet'])
    check('previous_month_closing', closing.docstatus == 1 and int(closing.month) == month_end.month
          and worksheet.docstatus == 1 and int(worksheet.month) == month_end.month,
          {'closing': closing.name,'closing_month': closing.month,'worksheet': worksheet.name,
           'worksheet_month': worksheet.month})
    logs = frappe.db.sql('''select jc.name, tl.from_time, tl.to_time from `tabJob Card` jc
        inner join `tabJob Card Time Log` tl on tl.parent=jc.name
        where jc.work_order=%s''', order.name, as_dict=True)
    actual_logs = [row for row in logs if row.from_time and row.to_time]
    check('production_dates', bool(actual_logs) and all(getdate(row.from_time) == sc.D1
          and getdate(row.to_time) == sc.D1 for row in actual_logs), {'actual': actual_logs, 'all_rows': logs})
    payload = {'site': frappe.local.site,'db': work,'progress': progress,'dates': {key: str(getattr(sc,key)) for key in ('D1','D2','E')},
               'checks': checks,'ok': all(row['ok'] for row in checks.values())}
    target = Path('/workspace/frappe-bench/logs/s8-final-business-readback.json')
    target.write_text(json.dumps(payload, default=str, ensure_ascii=False, indent=2))
    print(json.dumps({'ok': payload['ok'], 'checks': {key: row['ok'] for key,row in checks.items()}}, ensure_ascii=False))
    assert payload['ok'], 'Business readback failed; see evidence JSON'
finally:
    frappe.db.rollback()
    frappe.destroy()
