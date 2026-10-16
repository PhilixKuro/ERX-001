# 事务内：①模块与侧栏只读 ②Item Reorder 行 warehouse_group="" 落库值 ③Material Transfer 默认请购类型的原料走按订单规则。全部 rollback。
import frappe
from frappe.utils import today, add_days, getdate
frappe.local.lang = "zh"
print("module_defs", frappe.get_all("Module Def", {"name": ["in", ["Stock Plus", "Production Plus"]]}, ["name", "app_name"]))
print("sidebars", [(n, len(frappe.get_doc("Workspace Sidebar", n).items)) for n in ("Stock Plus", "Production Plus") if frappe.db.exists("Workspace Sidebar", n)])
C, W = "_Test Company", "Stores - _TC"
sfx = frappe.generate_hash(length=5)
def item(code, **kw):
    return frappe.get_doc({"doctype": "Item", "item_code": f"_FCT F1 {code} {sfx}", "item_group": "Products", "stock_uom": "Nos",
        "is_stock_item": 1, "valuation_rate": 2, "item_defaults": [{"company": C, "default_warehouse": W}], **kw}).insert()
try:
    it = item("WG", reorder_levels=[{"warehouse": W, "warehouse_group": "", "warehouse_reorder_level": 5, "warehouse_reorder_qty": 1, "material_request_type": "Purchase"}])
    print("stored_wg", frappe.db.sql("select warehouse_group is null, warehouse_group from `tabItem Reorder` where parent=%s", it.name))
    from frappe_china.replenishment.rules import _reorder_rows, order_proposals
    frappe.db.set_value("Item", it.name, "cn_rule_eoq", 1)
    print("reorder_rows_hit", [r.parent for r in _reorder_rows(C, "cn_rule_eoq") if r.parent == it.name])
    # ③
    cur = frappe.db.get_value("Company", C, "default_currency")
    fg = item("FG"); rm = item("RM", cn_rule_order=1, default_material_request_type="Material Transfer")
    bom = frappe.get_doc({"doctype": "BOM", "item": fg.name, "company": C, "quantity": 1, "currency": cur, "items": [{"item_code": rm.name, "qty": 2}]}); bom.insert(); bom.submit()
    cu = frappe.get_doc({"doctype": "Customer", "customer_name": f"_FCT F1 Cust {sfx}", "customer_group": frappe.db.get_value("Customer Group", {"is_group": 0}), "territory": frappe.db.get_value("Territory", {"is_group": 0})}).insert()
    so = frappe.get_doc({"doctype": "Sales Order", "company": C, "customer": cu.name, "transaction_date": today(), "delivery_date": add_days(today(), 5), "currency": cur,
        "selling_price_list": "Standard Selling", "items": [{"item_code": fg.name, "qty": 3, "rate": 10, "warehouse": "Finished Goods - _TC", "delivery_date": add_days(today(), 5)}]}); so.insert(); so.submit()
    probs = []
    props = [p for p in order_proposals(C, getdate(today()), probs) if p["item_code"] == rm.name]
    print("order_props", [(p["mr_type"], p["qty"]) for p in props])
    from frappe_china.replenishment.suggestion import upsert
    for p in props:
        try:
            print("upsert_ok", upsert(C, getdate(today()), p))
        except Exception as e:
            print("upsert_fail", type(e).__name__, str(e)[:200])
    frappe.clear_messages()
finally:
    frappe.db.rollback()
    print("rolled back; leftover items", frappe.db.count("Item", {"item_code": ["like", f"_FCT F1 % {sfx}"]}))
