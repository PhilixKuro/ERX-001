"""Native production probe on s8dev, business writes rolled back."""
import json
import os
import sys
from pathlib import Path

import frappe
from frappe.utils import getdate

os.chdir('/workspace/frappe-bench/sites')
frappe.init(site='s8dev.localhost', sites_path='/workspace/frappe-bench/sites')
frappe.connect()
try:
    assert frappe.local.site == 's8dev.localhost'
    frappe.set_user('Administrator')
    from frappe_debug.demo.functions import job_cards_for_order, job_card_slot
    from frappe_debug.builders.common import insert_and_submit
    from frappe_debug.builders.manufacturing import make_and_submit_work_orders, make_and_submit_material_transfer
    from erpnext.manufacturing.doctype.work_order.work_order import make_stock_entry

    fixture = json.loads(Path('/workspace/frappe-bench/logs/s8-ts019-fixture.json').read_text())
    day = getdate('2026-01-07')
    insert_and_submit({
        'doctype': 'Stock Entry', 'stock_entry_type': 'Material Receipt',
        'company': fixture['company'],
        'items': [{'item_code': fixture['material'], 'qty': 200, 'basic_rate': 8,
                   't_warehouse': fixture['warehouse']}],
    }, day, time='07:00:00')
    order = insert_and_submit({
        'doctype': 'Sales Order', 'company': fixture['company'], 'customer': fixture['customer'],
        'delivery_date': '2026-01-21', 'po_no': '_FCT-TS024-production',
        'items': [{'item_code': fixture['product'], 'qty': 5000, 'rate': 0.88,
                   'warehouse': fixture['warehouse'], 'delivery_date': '2026-01-21'}],
    }, day)
    plan = frappe.get_doc({'doctype': 'Production Plan', 'company': fixture['company'],
        'posting_date': day, 'get_items_from': 'Sales Order', 'sales_orders': [{'sales_order': order}]})
    plan.get_items()
    plan.insert()
    work_orders = make_and_submit_work_orders(plan.name, day, time='08:00:00')
    assert len(work_orders) == 1
    wo = frappe.get_doc('Work Order', work_orders[0])
    transfer = make_and_submit_material_transfer(wo.name, day, qty=wo.qty, time='07:59:00')
    cards = job_cards_for_order(order)
    result = {'order': order, 'plan': plan.name, 'work_order': wo.name, 'planned_qty': wo.qty, 'transfer': transfer, 'cards': []}
    if '--browser-fixture' in sys.argv:
        result['card_names'] = cards
        result['scene_date'] = str(day)
        Path('/workspace/frappe-bench/logs/s8-ts024-browser-fixture.json').write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str))
        frappe.db.commit()
        print(json.dumps(result, ensure_ascii=False, default=str))
        sys.exit(0)
    for index, name in enumerate(cards):
        card = frappe.get_doc('Job Card', name)
        if card.for_quantity <= 0:
            continue
        print('ALLOCATE', name, card.operation, card.for_quantity, card.time_required, flush=True)
        slot = job_card_slot(name, str(day))
        qty = card.for_quantity
        loss = 60 if index == 0 else 0
        card.start_timer(start_time=slot['start_time'], employees=slot['employee'])
        card.reload()
        card.complete_job_card(qty=qty-loss, for_quantity=qty, pending_qty=0,
            process_loss_qty=loss, end_time=slot['end_time'])
        card.reload()
        card.submit()
        result['cards'].append({'name': name, 'operation': card.operation, 'for_quantity': card.for_quantity,
            'completed_qty': card.total_completed_qty, 'loss': card.process_loss_qty, 'minutes': card.total_time_in_mins, **slot})
    wo.reload()
    entry = frappe.get_doc(make_stock_entry(wo.name, 'Manufacture', qty=wo.qty-wo.produced_qty))
    entry.posting_date = day
    entry.set_posting_time = 1
    entry.posting_time = '17:30:00'
    entry.insert()
    entry.submit()
    wo.reload()
    good = sum(row.qty for row in entry.items if row.is_finished_item)
    result['manufacture'] = {'name': entry.name, 'gross': entry.fg_completed_qty, 'loss': entry.process_loss_qty,
        'good': good, 'produced': wo.produced_qty, 'costs': [row.as_dict() for row in entry.additional_costs]}
    assert good == wo.qty - 60, result['manufacture']
    assert wo.produced_qty == good, result['manufacture']
    assert all(getdate(row['start_time']) == day and getdate(row['end_time']) == day for row in result['cards'])
    Path('/workspace/frappe-bench/logs/s8-ts024-production-native.json').write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    print(json.dumps(result, ensure_ascii=False, default=str))
finally:
    frappe.db.rollback()
    frappe.destroy()
