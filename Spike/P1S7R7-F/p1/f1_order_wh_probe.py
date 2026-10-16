# 事务内：两种原料默认仓不同，看按订单规则给出的仓库。rollback。
import frappe
from frappe.utils import today, add_days, getdate
from frappe_china.replenishment.rules import order_proposals
C = "_Test Company"
sfx = frappe.generate_hash(length=5)
def item(code, wh, **kw):
    return frappe.get_doc({"doctype": "Item", "item_code": f"_FCT F1W {code} {sfx}", "item_group": "Products", "stock_uom": "Nos",
        "is_stock_item": 1, "valuation_rate": 2, "item_defaults": [{"company": C, "default_warehouse": wh}], **kw}).insert()
try:
    cur = frappe.db.get_value("Company", C, "default_currency")
    fg = item("FG", "Finished Goods - _TC")
    a = item("A", "Stores - _TC", cn_rule_order=1)
    b = item("B", "Work In Progress - _TC", cn_rule_order=1)
    bom = frappe.get_doc({"doctype": "BOM", "item": fg.name, "company": C, "quantity": 1, "currency": cur,
        "items": [{"item_code": a.name, "qty": 2}, {"item_code": b.name, "qty": 3}]}); bom.insert(); bom.submit()
    cu = frappe.get_doc({"doctype": "Customer", "customer_name": f"_FCT F1W Cust {sfx}", "customer_group": frappe.db.get_value("Customer Group", {"is_group": 0}), "territory": frappe.db.get_value("Territory", {"is_group": 0})}).insert()
    so = frappe.get_doc({"doctype": "Sales Order", "company": C, "customer": cu.name, "transaction_date": today(), "delivery_date": add_days(today(), 5), "currency": cur,
        "selling_price_list": "Standard Selling", "items": [{"item_code": fg.name, "qty": 3, "rate": 10, "warehouse": "Finished Goods - _TC", "delivery_date": add_days(today(), 5)}]}); so.insert(); so.submit()
    print("defaults", {i.name: frappe.db.get_value("Item Default", {"parent": i.name}, "default_warehouse") for i in (a, b)})
    print("proposals", [(p["item_code"][-12:], p["warehouse"], p["qty"]) for p in order_proposals(C, getdate(today()), []) if sfx in p["item_code"]])
    frappe.clear_messages()
finally:
    frappe.db.rollback()
    print("rolled back; leftover", frappe.db.count("Item", {"item_code": ["like", f"_FCT F1W % {sfx}"]}))
