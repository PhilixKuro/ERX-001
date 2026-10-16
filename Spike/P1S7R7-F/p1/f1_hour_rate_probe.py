# 事务内改工作中心费率，看 _unit_cost 是否随之变化；结束 rollback，不 commit。
import frappe
from frappe_china.production.bom_selection import _unit_cost
bom = "BOM-_S6R6 验收成品弹簧-001"
ws = frappe.db.get_value("BOM Operation", {"parent": bom}, "workstation")
before = _unit_cost(frappe.get_doc("BOM", bom))
frappe.db.set_value("Workstation", ws, "hour_rate", 600)
frappe.clear_document_cache("Workstation", ws)
after = _unit_cost(frappe.get_doc("BOM", bom))
print("workstation", ws, "ws_rate_now", frappe.db.get_value("Workstation", ws, "hour_rate"))
print("before", before["operating_cost"], before["unit_cost"])
print("after_ws_600", after["operating_cost"], after["unit_cost"])
print("row_hour_rate_in_db", frappe.db.get_all("BOM Operation", {"parent": bom}, ["hour_rate", "time_in_mins"]))
frappe.db.rollback()
print("rolled back; ws_rate", frappe.db.get_value("Workstation", ws, "hour_rate"))
