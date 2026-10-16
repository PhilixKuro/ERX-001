"""HT-012b (route A): after each downstream card submit, write cumulative upstream loss onto its
Work Order Operation row, then Manufacture with fg_completed_qty=qty and expect Completed.

Case 1: op1 950+50, op2 950, op3 950            -> manufacture 1000/50, FG 950.
Case 2: op1 950+50, op2 930+20, op3 930          -> manufacture 1000/70, FG 930.
Also: cancel op3 card then check the row reverts by native recompute (informational)."""

exec(open('/workspace/Spike/P1S7R5-D/ts012-probe-common.py', encoding='utf-8').read(), globals())

from erpnext.manufacturing.doctype.work_order.work_order import make_stock_entry

assert frappe.local.site == "test.localhost"


def finish(card, qty):
    start = now_datetime()
    card.append("time_logs", {"from_time": start, "to_time": add_to_date(start, minutes=40), "completed_qty": qty})
    card.save()
    card.reload()
    card.submit()
    card.reload()
    return card


def write_upstream_loss(wo_name, upto_idx):
    """Mimic route-A hook: row loss = wo.qty - row.completed_qty (= own + cumulative upstream loss)."""
    qty = frappe.db.get_value("Work Order", wo_name, "qty")
    for row in frappe.get_all("Work Order Operation", filters={"parent": wo_name, "idx": ["<=", upto_idx]},
                              fields=["name", "completed_qty"]):
        frappe.db.set_value("Work Order Operation", row.name, {"process_loss_qty": qty - row.completed_qty,
                            "status": "Completed"}, update_modified=False)


def run_case(label, quantities):
    marker, wo, cards, items = make_work_order(f"HT012B{label}")
    finish(cards[0], quantities[0])
    for idx, card in enumerate(cards[1:], start=2):
        frappe.db.set_value("Job Card", card.name, "for_quantity", quantities[idx - 2])
        card = finish(frappe.get_doc("Job Card", card.name), quantities[idx - 1])
        write_upstream_loss(wo.name, idx)
    output(f"case{label}_before_manufacture", snapshot(wo.name))
    receipt = frappe.get_doc({"doctype": "Stock Entry", "stock_entry_type": "Material Receipt", "company": wo.company})
    receipt.append("items", {"item_code": items[1], "qty": 1000, "t_warehouse": wo.source_warehouse, "basic_rate": 1})
    receipt.insert(ignore_permissions=True)
    receipt.submit()
    manufacture = frappe.get_doc(make_stock_entry(wo.name, "Manufacture", 1000))
    output(f"case{label}_manufacture_input", {"fg_completed_qty": manufacture.fg_completed_qty,
           "process_loss_qty": manufacture.process_loss_qty,
           "fg_rows": [row.qty for row in manufacture.items if row.is_finished_item]})
    try:
        manufacture.insert(ignore_permissions=True)
        manufacture.submit()
    except frappe.ValidationError as exc:
        output(f"case{label}_result", {"verdict": "no-go", "exception": type(exc).__name__, "message": str(exc)})
        return
    manufacture.reload()
    after = snapshot(wo.name)
    expected_fg = quantities[-1]
    fg = [row.qty for row in manufacture.items if row.is_finished_item]
    ok = after["work_order"]["status"] == "Completed" and fg == [expected_fg]
    output(f"case{label}_result", {"verdict": "go" if ok else "no-go", "fg_rows": fg,
           "manufacture_loss": manufacture.process_loss_qty, **after})


try:
    frappe.local.lang = "en"
    frappe.db.set_single_value("Manufacturing Settings", "disable_capacity_planning", 1)
    run_case("1", [950, 950, 950])
    run_case("2", [950, 930, 930])
finally:
    frappe.db.rollback()
    output("rollback", {"probe_items": frappe.db.count("Item", {"name": ["like", "_FCT SA-HT012B%"]})})
