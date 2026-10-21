"""SL-006 browser fixtures, confined to test.localhost and explicitly cleaned."""
import json
import sys
from pathlib import Path

import frappe

SITE = "test.localhost"
MANIFEST = Path("/workspace/frappe-bench/logs/s8-bom-confirmation-fixture.json")
frappe.init(site=SITE, sites_path="/workspace/frappe-bench/sites")
frappe.connect()
try:
    assert frappe.local.site == SITE
    frappe.set_user("Administrator")
    frappe.local.lang = "zh"
    if sys.argv[1] == "create":
        from frappe_china.tests.test_bom_selection_hooks import COMPANY, TestBomSelectionHooks

        if MANIFEST.exists():
            raise RuntimeError("Clean the previous SL-006 fixture first")
        fixture = TestBomSelectionHooks(methodName="runTest")
        fixture.suffix = frappe.generate_hash(length=6)
        fixture.fg = fixture._item("UI FG", cn_auto_select_bom=1)
        raw_default = fixture._item("UI RM Default")
        raw_cheap = fixture._item("UI RM Cheap")
        default_bom = fixture._bom(raw_default, hour_rate=600, is_default=1)
        cheap_bom = fixture._bom(raw_cheap, hour_rate=60, is_default=0)
        order = fixture._sales_order(30)
        boms = [frappe.get_doc("BOM", name) for name in (cheap_bom, default_bom)]
        manifest = {
            "site": SITE, "company": COMPANY, "item": fixture.fg,
            "raw_items": [raw_default, raw_cheap], "boms": [cheap_bom, default_bom],
            "default_bom": default_bom, "cheap_bom": cheap_bom,
            "operations": [row.operation for bom in boms for row in bom.operations],
            "workstations": [row.workstation for bom in boms for row in bom.operations],
            "order": order.name, "customer": order.customer,
        }
        MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
        frappe.db.commit()
        print(json.dumps(manifest, ensure_ascii=False))
    elif sys.argv[1] == "cleanup":
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        assert manifest["site"] == SITE
        work_orders = frappe.get_all("Work Order", filters={"production_item": manifest["item"]}, pluck="name")
        plan_names = set(frappe.get_all("Production Plan Item", filters={"item_code": manifest["item"]}, pluck="parent"))
        targets = [("Work Order", name) for name in work_orders]
        targets += [("Production Plan", name) for name in sorted(plan_names)]
        targets += [("Sales Order", manifest["order"])]
        targets += [("BOM", name) for name in manifest["boms"]]
        targets += [("Customer", manifest["customer"]), ("Item", manifest["item"])]
        targets += [("Item", name) for name in manifest["raw_items"]]
        targets += [("Operation", name) for name in manifest["operations"]]
        targets += [("Workstation", name) for name in manifest["workstations"]]
        cleaned = []
        for doctype, name in targets:
            if not frappe.db.exists(doctype, name):
                continue
            doc = frappe.get_doc(doctype, name)
            if doc.docstatus == 1:
                doc.cancel()
            frappe.delete_doc(doctype, name)
            cleaned.append([doctype, name])
        assert not frappe.db.exists("Item", manifest["item"])
        frappe.db.commit()
        MANIFEST.unlink()
        print(json.dumps({"site": SITE, "cleaned": cleaned}, ensure_ascii=False))
    else:
        raise ValueError("Expected create or cleanup")
except Exception:
    frappe.db.rollback()
    raise
finally:
    frappe.destroy()
