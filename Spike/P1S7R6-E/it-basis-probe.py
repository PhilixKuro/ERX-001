"""E probe: real upsert of an EOQ-shaped proposal into Replenishment Suggestion; always rolled back."""
import frappe
from frappe_china.replenishment.rules import _basis
from frappe_china.replenishment.suggestion import upsert

assert frappe.local.site == "test.localhost"
item = frappe.get_all("Item", filters={"is_stock_item": 1, "disabled": 0}, pluck="name", limit=1)[0]
wh = frappe.get_all("Warehouse", filters={"company": "_Test Company", "is_group": 0}, pluck="name", limit=1)[0]
parts = {"actual_qty": 1, "projected_qty": 1, "reorder_level": 5, "eoq": 3}
proposal = {"item_code": item, "warehouse": wh, "rule": "EOQ", "qty": 3, "mr_type": "Purchase",
            "basis": _basis(parts), "sources": []}
try:
    name = upsert("_Test Company", frappe.utils.today(), proposal)
    print("UPSERT OK", name, frappe.get_doc("Replenishment Suggestion", name).basis[0].basis)
except Exception as e:
    print("UPSERT FAILED:", type(e).__name__, str(e)[:300])
finally:
    frappe.db.rollback()
