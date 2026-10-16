"""E probe: real run_daily for one EOQ+periodic item at a triggering state; always rolled back."""
import json
from datetime import timedelta
import frappe
from frappe.utils import getdate, today
from erpnext.stock.doctype.stock_entry.stock_entry_utils import make_stock_entry
from frappe_china.replenishment.daily import run_daily

assert frappe.local.site == "test.localhost"
company = "_Test Company"
wh = "Stores - _TC"
d = getdate(today()) - timedelta(days=2)
before_errors = set(frappe.get_all("Error Log", pluck="name"))
try:
    frappe.db.set_value("Company", company, {"cn_replenishment_enabled": 1, "cn_order_cost": 20,
        "cn_holding_rate": 20, "cn_review_days": 1,  "cn_review_start_date": d - timedelta(days=10), "cn_service_level": 95})
    item = frappe.get_doc({"doctype": "Item", "item_code": "_FCT E probe " + frappe.generate_hash(length=6),
        "item_group": "Products", "stock_uom": "Nos", "is_stock_item": 1, "valuation_rate": 2, "lead_time_days": 30,
        "cn_auto_replenishment_params": 1, "cn_rule_eoq": 1, "cn_rule_periodic": 1,
        "reorder_levels": [{"warehouse": wh, "warehouse_reorder_level": 50, "warehouse_reorder_qty": 1,
                            "material_request_type": "Purchase"}]}).insert()
    make_stock_entry(item_code=item.name, qty=11, to_warehouse=wh, rate=2, company=company, posting_date=d - timedelta(days=30))
    for k in range(10):  # leaves projected 1
        make_stock_entry(item_code=item.name, qty=1, from_warehouse=wh, company=company, posting_date=d - timedelta(days=k))
    out = run_daily(d, company)
    print(json.dumps(out, ensure_ascii=False, default=str)[:1500])
    print("SUGGESTIONS", frappe.get_all("Replenishment Suggestion", filters={"item_code": item.name}, fields=["rule", "suggested_qty"]))
finally:
    frappe.db.rollback()
    new = [n for n in frappe.get_all("Error Log", pluck="name") if n not in before_errors]
    for n in new:
        frappe.delete_doc("Error Log", n, ignore_permissions=True)
    frappe.db.commit()
    print("ERROR LOGS REMOVED", len(new))
