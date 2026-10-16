"""HT-011 only: db.set_value quantity reduction passes native quantity/sequence checks."""

exec(open('/workspace/Spike/P1S7R5-D/ts012-probe-common.py', encoding='utf-8').read(), globals())

assert frappe.local.site == "test.localhost"
marker = None
wo_name = None
try:
    frappe.local.lang = "en"
    frappe.db.set_single_value("Manufacturing Settings", "disable_capacity_planning", 1)
    marker, wo, cards, _items = make_work_order("HT011")
    wo_name = wo.name
    output("initial", snapshot(wo_name))
    # A rejected submit proves native sequence checking is actually active.
    frappe.db.savepoint("before_sequence_control")
    try:
        complete_card(cards[1])
    except Exception as exc:
        from erpnext.manufacturing.doctype.job_card.job_card import OperationSequenceError
        assert isinstance(exc, OperationSequenceError), (type(exc).__name__, str(exc))
        output("sequence_negative_control", {"exception": type(exc).__name__, "message": str(exc)})
        frappe.db.rollback(save_point="before_sequence_control")
    else:
        raise AssertionError("Native operation sequence check did not reject operation 2 before operation 1")
    first = complete_card(frappe.get_doc("Job Card", cards[0].name))
    assert (first.for_quantity, first.total_completed_qty, first.process_loss_qty) == (1000, 950, 50)
    old_qty = frappe.db.get_value("Job Card", cards[1].name, "for_quantity")
    frappe.db.set_value("Job Card", cards[1].name, "for_quantity", 950)
    second = frappe.get_doc("Job Card", cards[1].name)
    output("db_quantity_change", {"card": second.name, "original": old_qty, "reloaded": second.for_quantity})
    second = complete_card(second)
    assert (second.for_quantity, second.total_completed_qty, second.process_loss_qty, second.docstatus) == (950, 950, 0, 1)
    output("result", {"verdict": "go", **snapshot(wo_name)})
finally:
    frappe.db.rollback()
    output("rollback", {"work_order_exists": bool(wo_name and frappe.db.exists("Work Order", wo_name)),
                        "own_item_count": frappe.db.count("Item", {"name": ["like", f"{marker}%"]}) if marker else 0})

\n