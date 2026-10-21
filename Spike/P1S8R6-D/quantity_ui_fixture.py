"""Create/clean a test.localhost-only fixture for SL-003 browser acceptance."""
import json
import sys
from pathlib import Path

import frappe

SITE = "test.localhost"
MANIFEST = Path("/workspace/frappe-bench/logs/s8-quantity-ui-fixture.json")
frappe.init(site=SITE, sites_path="/workspace/frappe-bench/sites")
frappe.connect()
try:
    assert frappe.local.site == SITE
    frappe.set_user("Administrator")
    frappe.local.lang = "zh"
    if sys.argv[1] == "create":
        from frappe_china.tests.test_process_loss import TestProcessLossPlan

        if MANIFEST.exists():
            raise RuntimeError("Clean the previous browser fixture first")
        old_uom = frappe.db.get_value("UOM", "支", "must_be_whole_number")
        settings = {
            field: frappe.db.get_single_value("Manufacturing Settings", field)
            for field in ("disable_capacity_planning", "overproduction_percentage_for_sales_order")
        }
        fixture = TestProcessLossPlan(methodName="runTest")
        fixture._setup_loss_fixture()
        order = fixture._sales_order(5000)
        plan = fixture._plan([order])
        plan.save()
        assert plan.po_items[0].planned_qty == 5264
        plan.po_items[0].planned_qty = 5300
        plan.save()
        plan.reload()
        assert (plan.po_items[0].planned_qty, plan.po_items[0].cn_recommended_qty) == (5300, 5264)
        manifest = {
            "site": SITE, "plan": plan.name, "order": order.name, "bom": fixture.bom.name,
            "customer": order.customer, "item": fixture.bom.item,
            "material": fixture.bom.items[0].item_code,
            "operations": [row.operation for row in fixture.bom.operations],
            "workstation": fixture.bom.operations[0].workstation,
        }
        frappe.db.set_value("UOM", "支", "must_be_whole_number", old_uom)
        for field, value in settings.items():
            frappe.db.set_single_value("Manufacturing Settings", field, value)
        MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
        frappe.db.commit()
        print(json.dumps(manifest, ensure_ascii=False))
    elif sys.argv[1] == "cleanup":
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        assert manifest["site"] == SITE
        targets = [("Production Plan", manifest["plan"]), ("Sales Order", manifest["order"]),
                   ("BOM", manifest["bom"]), ("Customer", manifest["customer"]),
                   ("Item", manifest["item"]), ("Item", manifest["material"])]
        targets += [("Operation", name) for name in manifest["operations"]]
        targets += [("Workstation", manifest["workstation"])]
        for doctype, name in targets:
            if not frappe.db.exists(doctype, name):
                continue
            doc = frappe.get_doc(doctype, name)
            if doc.docstatus == 1:
                doc.cancel()
            frappe.delete_doc(doctype, name)
        frappe.db.commit()
        MANIFEST.unlink()
        print(json.dumps({"site": SITE, "cleaned": len(targets)}))
    else:
        raise ValueError("Expected create or cleanup")
except Exception:
    frappe.db.rollback()
    raise
finally:
    frappe.destroy()
