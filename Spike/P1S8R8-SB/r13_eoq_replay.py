"""R13 TS-037: replay the last day (E-1) without commit (assertion on unless R13_SKIP_ASSERT=1), report, roll back (s8r9 work db)."""
import json, os, shutil
from unittest.mock import patch
import frappe
os.chdir("/workspace/frappe-bench/sites")
frappe.init(site="s8r9.localhost", sites_path=".")
frappe.connect()
frappe.set_user("Administrator")
from datetime import timedelta
from frappe_debug.scenario import runner, targets
from frappe_debug.scenario.params import load_scenario
from frappe_china.replenishment.demand import projected_qty, warehouses_of_row
status = runner._status_path()
backup = status.with_suffix(".r13-backup.json")
shutil.copy(status, backup)
sc = load_scenario()
item = "WIRE-65MN-3.0"
day = sc.E - timedelta(days=1)
def snap(tag):
    row = frappe.get_all("Item Reorder", filters={"parent": item}, fields=["warehouse", "warehouse_group", "warehouse_reorder_level"])[0]
    q, parts = projected_qty(item, warehouses_of_row(row))
    print(tag, "reorder", round(row.warehouse_reorder_level, 2), "projected", round(q, 2), {k: round(v, 2) for k, v in parts.items() if v})
snap("before")
try:
    if os.environ.get("R13_SKIP_ASSERT"):
        with patch.object(targets, "assert_act9_eoq_ready", lambda _sc: None):
            runner.generate(day, day, job_id="r13-replay", preview_quality_schedule=True, commit=False)
    else:
        runner.generate(day, day, job_id="r13-replay", preview_quality_schedule=True, commit=False)
    snap("after")
    print("new docs on", day)
    for dt, f in (("Purchase Receipt", "posting_date"), ("Purchase Order", "transaction_date"), ("Work Order", "creation"), ("Material Request", "transaction_date"), ("Replenishment Suggestion", "calculation_date")):
        filt = {f: [">=", day]} if f != "creation" else {"planned_start_date": [">=", day]}
        names = frappe.get_all(dt, filters=filt, pluck="name")
        print(" ", dt, names[:20])
    for r in frappe.db.sql("""select pr.name, pr.supplier, pri.qty, pri.rejected_qty, pri.purchase_order from `tabPurchase Receipt` pr join `tabPurchase Receipt Item` pri on pri.parent=pr.name where pri.item_code=%s and pr.posting_date=%s""", (item, day), as_dict=1):
        print("  PR", dict(r))
    for r in frappe.db.sql("""select wo.name, wo.sales_order, wo.status, woi.required_qty from `tabWork Order` wo join `tabWork Order Item` woi on woi.parent=wo.name where woi.item_code=%s and wo.creation >= now() - interval 1 hour""", item, as_dict=1):
        print("  WO", dict(r))
    for s in frappe.get_all("Replenishment Suggestion", filters={"item_code": item, "calculation_date": [">=", day]}, fields=["name", "rule", "calculation_date", "status", "suggested_qty"]):
        print("  RS", dict(s))
    for p in frappe.db.sql("""select posting_date, voucher_type, warehouse, sum(actual_qty) q from `tabStock Ledger Entry` where item_code=%s and posting_date>=%s and is_cancelled=0 group by 1,2,3""", (item, day), as_dict=1):
        print("  SLE", p.posting_date, p.voucher_type, p.warehouse, round(p.q, 2))
finally:
    frappe.db.rollback()
    shutil.copy(backup, status)
    backup.unlink()
    snap("after-rollback")
    frappe.destroy()
