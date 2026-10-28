"""R13 TS-037 pause: work orders using WIRE-65MN-3.0 around E, and receipts' rejected share (s8r9 work db, read-only)."""
import os
import frappe
os.chdir("/workspace/frappe-bench/sites")
frappe.init(site="s8r9.localhost", sites_path=".")
frappe.connect()
item = "WIRE-65MN-3.0"
print("WO items (planned_start >= 2026-10-15)")
for r in frappe.db.sql("""select wo.name, wo.sales_order, wo.planned_start_date, wo.docstatus, wo.status, woi.required_qty, woi.transferred_qty, woi.consumed_qty
  from `tabWork Order` wo join `tabWork Order Item` woi on woi.parent=wo.name
  where woi.item_code=%s and wo.planned_start_date>='2026-10-15' order by wo.planned_start_date""", item, as_dict=1):
    print(" ", {k: str(v) for k, v in r.items()})
print("receipts by supplier since 2026-08-01: accepted / rejected")
for r in frappe.db.sql("""select pr.supplier, sum(pri.qty) acc, sum(pri.rejected_qty) rej from `tabPurchase Receipt` pr join `tabPurchase Receipt Item` pri on pri.parent=pr.name
  where pri.item_code=%s and pr.docstatus=1 and pr.posting_date>='2026-08-01' group by pr.supplier""", item, as_dict=1):
    print(" ", r.supplier, round(r.acc, 1), round(r.rej, 1), f"{r.rej/(r.acc+r.rej):.3f}")
print("open SO lines needing the product with no WO")
for r in frappe.db.sql("""select so.name, so.transaction_date, soi.delivery_date, soi.item_code, soi.qty, soi.work_order_qty
  from `tabSales Order` so join `tabSales Order Item` soi on soi.parent=so.name
  where so.docstatus=1 and so.status not in ('Completed','Closed') and soi.delivery_date>='2026-10-20' order by soi.delivery_date""", as_dict=1):
    print(" ", {k: str(v) for k, v in r.items()})
frappe.destroy()
