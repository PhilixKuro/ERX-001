# P1-S7-R7 F 片1 只读探针：meta 布局、默认值、精度、Select 校验、译名。不写库（Select 校验只调 _validate_selects，不 insert）。
import frappe
frappe.local.lang = "zh"
out = {}
def section_of(dt, names):
    meta = frappe.get_meta(dt)
    cur = None; res = {}; seq = []
    for df in meta.fields:
        if df.fieldtype == "Section Break":
            cur = df.fieldname
        seq.append((df.fieldname, df.fieldtype, cur))
    return seq
for dt, anchor in (("Company", "cn_replenishment_section"), ("Item", "cn_replenishment_section")):
    seq = section_of(dt, None)
    idx = [i for i, s in enumerate(seq) if s[0] == anchor][0]
    out[dt] = seq[idx - 3: idx + 16]
out["item_new_doc_service_level"] = frappe.new_doc("Item").get("cn_service_level")
out["item_col_default"] = frappe.db.sql("""select column_default from information_schema.columns
  where table_schema=database() and table_name='tabItem' and column_name='cn_service_level'""")
out["item_sl_distribution"] = frappe.db.sql("select cn_service_level, count(*) from tabItem group by cn_service_level")
out["cf_item_sl_default"] = frappe.db.get_value("Custom Field", "Item-cn_service_level", "default")
out["precision_item_safety_stock"] = repr(frappe.get_meta("Item").get_field("safety_stock").precision)
out["precision_reorder_level"] = repr(frappe.get_meta("Item Reorder").get_field("warehouse_reorder_level").precision)
out["hooks_fixture_has_mr"] = any("Material Request-cn_replenishment_suggestion" in str(f) for f in frappe.get_hooks("fixtures", app_name="frappe_china"))
out["cf_mr_exists"] = frappe.db.exists("Custom Field", "Material Request-cn_replenishment_suggestion")
# Select 校验：按订单规则可能带出的请购类型
res = {}
for mrt in ("Purchase", "Material Transfer", "Customer Provided"):
    doc = frappe.get_doc({"doctype": "Replenishment Suggestion", "material_request_type": mrt, "rule": "Against Sales Order", "status": "Pending"})
    try:
        doc._validate_selects(); res[mrt] = "ok"
    except Exception as e:
        res[mrt] = f"{type(e).__name__}: {e}"
    frappe.clear_messages()
out["select_validation"] = res
out["item_default_mr_type_distribution"] = frappe.db.sql("select default_material_request_type, count(*) from tabItem group by 1")
out["tr"] = {s: frappe._(s) for s in ("Pending", "Adopted", "Ignored", "Against Sales Order", "Periodic Review", "EOQ", "Reserved Qty", "Reserved Qty for Production", "Reserved Qty for Production Plan", "Reserved Qty for Subcontract", "Projected Qty", "frappe_china override self-check failed", "Replenishment Suggestion")}
for k, v in out.items():
    print(k, "=>", v)
frappe.db.rollback()
