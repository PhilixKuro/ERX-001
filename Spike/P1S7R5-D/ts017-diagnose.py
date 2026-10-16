import json
from pathlib import Path
import frappe

assert frappe.local.site == "erx.localhost"
print("site", frappe.local.site)
print("module paths", {m: frappe.get_module_path(m) for m in ("Stock Plus", "Production Plus")})
print("app doctypes", frappe.get_all("DocType", filters={"module": ["in", ["Stock Plus", "Production Plus"]]}, fields=["name", "module"]))
print("pages", frappe.get_all("Page", filters={"name": "spc-chart"}, fields=["name", "module"]))
print("custom fields", frappe.get_all("Custom Field", filters={"fieldname": "cn_unit_length_m"}, fields=["name", "modified"]))
before = json.loads(Path("/workspace/Spike/P1S7R5-D/s7-erx.localhost-before.json").read_text(encoding="utf-8"))
names = {e["name"] for e in before["error_logs"]}
print("new errors", [dict(e) for e in frappe.get_all("Error Log", fields=["name", "method", "creation"], order_by="creation") if e.name not in names])
print("physical app path", frappe.get_app_path("frappe_china"))
print("schema exists", Path(frappe.get_app_path("frappe_china", "production_plus", "doctype", "piece_rate_summary", "piece_rate_summary.json")).exists())
print("app modules", frappe.local.app_modules.get("frappe_china"))
first = next(e for e in frappe.get_all("Error Log", fields=["name", "method", "creation"], order_by="creation") if e.name not in names)
log = frappe.get_doc("Error Log", first.name)
print("deferred error metadata", log.get("metadata"))
print("deferred error final line", log.error.splitlines()[-1][:300])
