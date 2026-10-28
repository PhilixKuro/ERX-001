"""R13 TS-037 pause: read-only look at WIRE-65MN-3.0 around the act 9 hold (s8r9 work db)."""
import json, os
from datetime import timedelta
import frappe
os.chdir("/workspace/frappe-bench/sites")
frappe.init(site="s8r9.localhost", sites_path=".")
frappe.connect()
from frappe_debug.demo.registry import get_registry
from frappe_debug.scenario.params import load_scenario
from frappe_debug.scenario.targets import act9_hold_start
from frappe_china.replenishment.demand import projected_qty, warehouses_of_row
reg = get_registry()
print("db", frappe.conf.db_name, reg.get("work_db"), reg.get("work_state"))
sc = load_scenario()
item = "WIRE-65MN-3.0"
hs = act9_hold_start(sc)
print("S", sc.S, "E", sc.E, "hold_start", hs, "rule dates", sc.rule_dates)
rows = frappe.get_all("Item Reorder", filters={"parent": item}, fields=["warehouse","warehouse_group","warehouse_reorder_level","warehouse_reorder_qty"])
for r in rows:
    print("reorder", dict(r), "projected", projected_qty(item, warehouses_of_row(r)))
print("bin", frappe.db.sql("select warehouse, actual_qty, ordered_qty, indented_qty, reserved_qty_for_production, projected_qty from tabBin where item_code=%s", item, as_dict=1))
since = hs - timedelta(days=30)
print("suggestions")
for s in frappe.get_all("Replenishment Suggestion", filters={"item_code": item, "calculation_date": [">=", since]}, fields=["name","rule","calculation_date","status","suggested_qty" if frappe.get_meta("Replenishment Suggestion").has_field("suggested_qty") else "name as n"], order_by="calculation_date"):
    print(" ", dict(s))
print("POs")
for p in frappe.db.sql("""select po.name, po.supplier, po.transaction_date, po.schedule_date, po.docstatus, po.status, poi.qty, poi.received_qty, poi.material_request
  from `tabPurchase Order` po join `tabPurchase Order Item` poi on poi.parent=po.name
  where poi.item_code=%s and po.transaction_date>=%s order by po.transaction_date""", (item, since), as_dict=1):
    print(" ", {k: str(v) for k, v in p.items()})
print("MRs")
for p in frappe.db.sql("""select mr.name, mr.transaction_date, mr.docstatus, mr.status, mri.qty, mri.ordered_qty
  from `tabMaterial Request` mr join `tabMaterial Request Item` mri on mri.parent=mr.name
  where mri.item_code=%s and mr.transaction_date>=%s order by mr.transaction_date""", (item, since), as_dict=1):
    print(" ", {k: str(v) for k, v in p.items()})
print("SLE daily net since hold-30")
for p in frappe.db.sql("""select posting_date, voucher_type, warehouse, sum(actual_qty) q from `tabStock Ledger Entry`
  where item_code=%s and posting_date>=%s and is_cancelled=0 group by posting_date, voucher_type, warehouse order by posting_date""", (item, since), as_dict=1):
    print(" ", p.posting_date, p.voucher_type, p.warehouse, round(p.q, 2))
frappe.destroy()
