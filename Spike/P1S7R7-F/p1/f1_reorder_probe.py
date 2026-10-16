# 只读：Item Reorder.warehouse_group 空串与 NULL 分布；BOM 工序行与工作中心费率对照
import frappe
print("wg_dist", frappe.db.sql("select warehouse_group is null, warehouse_group='', count(*) from `tabItem Reorder` group by 1,2"))
print("coalesce_empty_join", frappe.db.sql("select coalesce('', 'X'), coalesce(NULL,'X')"))
print("bom_ops", frappe.db.sql("""select b.name, bo.workstation, bo.hour_rate, w.hour_rate, b.conversion_rate from `tabBOM Operation` bo join tabBOM b on b.name=bo.parent
 left join tabWorkstation w on w.name=bo.workstation where b.docstatus=1"""))
frappe.db.rollback()
