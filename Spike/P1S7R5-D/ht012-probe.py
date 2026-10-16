"""HT-012 only: Manufacture 950 + process loss 50 and inspect work-order/operation statuses."""

exec(open('/workspace/Spike/P1S7R5-D/ts012-probe-common.py', encoding='utf-8').read(), globals())

assert frappe.local.site == "test.localhost"
marker = None
wo_name = None
try:
    frappe.local.lang = "en"
    frappe.db.set_single_value("Manufacturing Settings", "disable_capacity_planning", 1)
    marker, wo, cards, items = make_work_order("HT012")
    wo_name = wo.name
    output("initial", snapshot(wo_name))
    complete_card(cards[0])
    for card in cards[1:]:
        old_qty = frappe.db.get_value("Job Card", card.name, "for_quantity")
        frappe.db.set_value("Job Card", card.name, "for_quantity", 950)
        reloaded = frappe.get_doc("Job Card", card.name)
        output("db_quantity_change", {"card": card.name, "original": old_qty, "reloaded": reloaded.for_quantity})
        complete_card(reloaded)
    output("before_manufacture", snapshot(wo_name))
    # Provide real stock so the manufacture submit reaches its normal native validators.
    receipt = frappe.get_doc({"doctype": "Stock Entry", "stock_entry_type": "Material Receipt", "company": wo.company})
    receipt.append("items", {"item_code": items[1], "qty": 1000, "t_warehouse": wo.source_warehouse, "basic_rate": 1})
    receipt.insert(ignore_permissions=True)
    receipt.submit()
    from erpnext.manufacturing.doctype.work_order.work_order import make_stock_entry
    manufacture = frappe.get_doc(make_stock_entry(wo_name, "Manufacture", 950))
    manufacture.process_loss_qty = 50
    output("manufacture_input", {"fg_completed_qty": manufacture.fg_completed_qty, "process_loss_qty": manufacture.process_loss_qty,
        "items": [{key: row.get(key) for key in ("item_code", "qty", "is_finished_item")} for row in manufacture.items]})
    try:
        manufacture.insert(ignore_permissions=True)
        manufacture.submit()
    except frappe.ValidationError as exc:
        output("result", {"verdict": "no-go", "exception": type(exc).__name__, "message": str(exc), **snapshot(wo_name)})
    else:
        manufacture.reload()
        after = snapshot(wo_name)
        output("result", {"verdict": "go" if after["work_order"]["status"] == "Completed" else "no-go",
            "manufacture": {key: manufacture.get(key) for key in ("name", "fg_completed_qty", "process_loss_qty", "docstatus")}, **after})
finally:
    frappe.db.rollback()
    output("rollback", {"work_order_exists": bool(wo_name and frappe.db.exists("Work Order", wo_name)),
                        "own_item_count": frappe.db.count("Item", {"name": ["like", f"{marker}%"]}) if marker else 0})

\n