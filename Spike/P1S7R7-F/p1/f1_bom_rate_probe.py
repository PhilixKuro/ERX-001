# 只读：BOM 工序行 hour_rate 是否保存后恒非零（若恒非零，_unit_cost 永不读工作中心现价）。
import frappe
print("bom_op_rows", frappe.db.sql("""select count(*), sum(bo.hour_rate>0), sum(bo.hour_rate=0 or bo.hour_rate is null)
 from `tabBOM Operation` bo join tabBOM b on b.name=bo.parent where b.docstatus=1"""))
print("mismatch_vs_workstation", frappe.db.sql("""select count(*) from `tabBOM Operation` bo join tabBOM b on b.name=bo.parent
 join tabWorkstation w on w.name=bo.workstation where b.docstatus=1 and abs(bo.hour_rate - w.hour_rate) > 0.0001"""))
frappe.db.rollback()
