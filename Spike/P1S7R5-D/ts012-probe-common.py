"""Disposable construction helpers; no proposition or production-code changes."""

import json
import frappe
from frappe.utils import add_to_date, now_datetime


def make_work_order(probe):
    marker = f"_FCT SA-{probe}-{frappe.generate_hash(length=8)}"
    company = "_Test Company"
    items = []
    for kind in ("FG", "RM"):
        item = frappe.get_doc({
            "doctype": "Item", "item_code": f"{marker}-{kind}",
            "item_name": f"{marker}-{kind}", "item_group": "Products",
            "stock_uom": "Nos", "is_stock_item": 1,
            "include_item_in_manufacturing": 1,
        }).insert(ignore_permissions=True)
        items.append(item.name)
    bom = frappe.get_doc({
        "doctype": "BOM", "item": items[0], "company": company, "quantity": 1,
        "currency": frappe.db.get_value("Company", company, "default_currency"),
        "with_operations": 1,
    })
    bom.append("items", {"item_code": items[1], "qty": 1, "uom": "Nos", "stock_uom": "Nos"})
    for sequence in (1, 2, 3):
        workstation = frappe.get_doc({
            "doctype": "Workstation", "workstation_name": f"{marker}-WS{sequence}",
            "production_capacity": 1,
        }).insert(ignore_permissions=True)
        operation = frappe.get_doc({
            "doctype": "Operation", "name": f"{marker}-OP{sequence}",
            "workstation": workstation.name, "create_job_card_based_on_batch_size": 0,
        }).insert(ignore_permissions=True)
        bom.append("operations", {
            "operation": operation.name, "workstation": workstation.name,
            "time_in_mins": 40, "batch_size": 1000, "sequence_id": sequence,
        })
    bom.insert(ignore_permissions=True)
    bom.submit()
    wo = frappe.get_doc({
        "doctype": "Work Order", "company": company, "production_item": items[0],
        "bom_no": bom.name, "qty": 1000, "stock_uom": "Nos",
        "source_warehouse": "Stores - _TC", "fg_warehouse": "Finished Goods - _TC",
        "skip_transfer": 1, "reserve_stock": 0, "planned_start_date": now_datetime(),
    })
    wo.get_items_and_operations_from_bom()
    wo.insert(ignore_permissions=True)
    wo.submit()
    cards = [frappe.get_doc("Job Card", name) for name in frappe.get_all(
        "Job Card", filters={"work_order": wo.name, "docstatus": ["<", 2]},
        pluck="name", order_by="sequence_id",
    )]
    assert len(cards) == 3 and [c.sequence_id for c in cards] == [1, 2, 3]
    assert [c.for_quantity for c in cards] == [1000, 1000, 1000]
    assert all(not c.is_corrective_job_card and not c.track_semi_finished_goods for c in cards)
    return marker, wo, cards, items


def complete_card(card):
    start = now_datetime()
    card.append("time_logs", {
        "from_time": start, "to_time": add_to_date(start, minutes=40), "completed_qty": 950,
    })
    card.save()
    card.reload()
    card.submit()
    card.reload()
    return card


def snapshot(wo_name):
    wo = frappe.get_doc("Work Order", wo_name)
    return {
        "work_order": {key: wo.get(key) for key in (
            "name", "qty", "produced_qty", "process_loss_qty", "status", "docstatus",
        )},
        "cards": frappe.get_all("Job Card", filters={"work_order": wo_name}, fields=[
            "name", "operation_id", "sequence_id", "for_quantity", "total_completed_qty",
            "process_loss_qty", "pending_qty", "docstatus", "status", "is_corrective_job_card",
        ], order_by="sequence_id"),
        "operations": frappe.get_all("Work Order Operation", filters={"parent": wo_name}, fields=[
            "name", "idx", "sequence_id", "completed_qty", "process_loss_qty", "status",
        ], order_by="idx"),
    }


def output(event, data):
    print(json.dumps({"event": event, **data}, ensure_ascii=False, default=str, sort_keys=True))
