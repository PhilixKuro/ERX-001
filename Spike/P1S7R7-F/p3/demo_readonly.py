"""F 片3：erx.localhost 只读快照（只 SELECT，末尾 rollback，不 commit）。"""
import json
from pathlib import Path

import frappe
import frappe.utils.scheduler

assert frappe.local.site == "erx.localhost"
before = json.loads(Path("/workspace/Spike/P1S7R5-D/s7-erx.localhost-after.json").read_text(encoding="utf-8"))
known = {e["name"] for e in before.get("error_logs", [])}
q = frappe.db.sql
out = {
	"order": frappe.get_installed_apps(),
	"auto_indent": q("select value from tabSingles where doctype='Stock Settings' and field='auto_indent'"),
	"piece_component": q("select name from `tabSalary Component` where name='计件工资'"),
	"modules": q("select name, app_name from `tabModule Def` where name in ('Stock Plus','Production Plus')"),
	"reports": q("select name, module, modified, prepared_report, disabled from tabReport where name in ('Capacity Load','SPC Control Chart')", as_dict=True),
	"report_roles": q("select parent, role from `tabHas Role` where parenttype='Report' and parent in ('Capacity Load','SPC Control Chart') order by parent, role"),
	"page": q("select name, module, modified from tabPage where name='spc-chart'", as_dict=True),
	"page_roles": q("select role from `tabHas Role` where parenttype='Page' and parent='spc-chart'"),
	"sidebars": q("select s.name, (select count(*) from `tabWorkspace Sidebar Item` i where i.parent=s.name) from `tabWorkspace Sidebar` s where s.name in ('Stock Plus','Production Plus')"),
	"translation": q("select count(*) from tabTranslation"),
	"error_log_total": q("select count(*) from `tabError Log`"),
	"error_logs_new_since_D_after": [
		r for r in q("select name, creation, left(method,120) m from `tabError Log` order by creation", as_dict=True)
		if r.name not in known
	],
	"notification_selfcheck": q("select name, creation, for_user, subject from `tabNotification Log` where subject like %s order by creation", ("%self-check%",), as_dict=True),
	"scheduler_disabled": frappe.utils.scheduler.is_scheduler_disabled(),
}
for dt in ("GL Entry", "Stock Ledger Entry", "Customer", "Supplier", "Item", "Sales Invoice", "Purchase Invoice",
	"Journal Entry", "Payment Entry", "Stock Entry", "Work Order", "Job Card", "Material Request",
	"Quality Inspection", "Workstation", "Replenishment Suggestion", "Piece Rate Summary", "Additional Salary"):
	out[dt] = q(f"select count(*) from `tab{dt}`")[0][0]
frappe.db.rollback()
print(json.dumps(out, ensure_ascii=False, default=str, indent=1))
