"""TS-003/004 readback probe: test.localhost only, all business writes rolled back."""
import json

import frappe

frappe.init(site="test.localhost", sites_path="/workspace/frappe-bench/sites")
frappe.connect()
try:
    assert frappe.local.site == "test.localhost"
    frappe.set_user("Administrator")
    frappe.local.lang = "zh"
    from frappe_china.production.process_loss import overall_loss_percentage, required_input_qty
    from frappe_china.tests.test_process_loss import TestProcessLoss

    fields = frappe.get_all(
        "Custom Field",
        filters={"name": ["in", [
            "BOM Operation-cn_process_loss_percentage",
            "Production Plan Item-cn_demand_qty",
            "Production Plan Item-cn_recommended_qty",
            "Production Plan Item-cn_recommended_bom",
        ]]},
        fields=["name", "fieldtype", "read_only", "hidden"],
    )
    frappe.db.set_value("UOM", "支", "must_be_whole_number", 1)
    bom = TestProcessLoss._make_bom(None, 1000, "支", (None, None, None))
    bom.process_loss_percentage = 5
    bom.save()
    before = bom.process_loss_percentage
    bom.reload()
    rates = [row.cn_process_loss_percentage for row in bom.operations]
    readback = {"stored_overall": bom.process_loss_percentage, "operation_values": rates,
                "computed_overall": overall_loss_percentage(bom),
                "recommended_input_for_5000": required_input_qty(bom.name, 5000)}
    bom.save()
    print(json.dumps({"site": frappe.local.site, "fields": fields,
        "before_reload": before, "after_reload": readback,
        "overall_after_resave": bom.process_loss_percentage}, ensure_ascii=False))
finally:
    frappe.db.rollback()
    frappe.destroy()
