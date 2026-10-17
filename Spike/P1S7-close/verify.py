import json, pathlib
import frappe
frappe.init(site="erx.localhost"); frappe.connect()
from frappe_china.install import check_app_order
print("installed:", frappe.get_installed_apps())
print("check_app_order:", check_app_order())
print("patch logged:", bool(frappe.db.exists("Patch Log", {"patch": ["like", "%s7_replenishment_source_terms%"]})))
print("Translation rows:", frappe.db.count("Translation"))
for dt in ["GL Entry", "Stock Ledger Entry", "Customer", "Supplier", "Item", "Sales Invoice", "Purchase Invoice", "Work Order", "Job Card"]:
    print(f"{dt}: {frappe.db.count(dt)}")
# 对比自有 app 各 DocType json 的字段与站上 meta
root = pathlib.Path(frappe.get_app_path("frappe_china"))
missing = []
n = 0
for p in root.rglob("doctype/*/*.json"):
    if p.stem != p.parent.name: continue
    d = json.loads(p.read_text(encoding="utf-8"))
    if d.get("doctype") != "DocType": continue
    n += 1
    if not frappe.db.exists("DocType", d["name"]):
        missing.append((d["name"], "DOCTYPE")); continue
    meta = frappe.get_meta(d["name"])
    for f in d.get("fields", []):
        if not meta.get_field(f["fieldname"]): missing.append((d["name"], f["fieldname"]))
        elif f.get("options") and meta.get_field(f["fieldname"]).options != f["options"]:
            missing.append((d["name"], f["fieldname"] + " options differ"))
print("own doctypes:", n, "mismatches:", missing)
# Custom Field fixtures
fx = root / "fixtures" / "custom_field.json"
if fx.exists():
    rows = json.loads(fx.read_text(encoding="utf-8"))
    miss = [r["name"] for r in rows if not frappe.db.exists("Custom Field", r["name"])]
    print("custom fields:", len(rows), "missing:", miss)
