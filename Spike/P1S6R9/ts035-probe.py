"""R9 TS-035 准备：只读查测试站，给各屏挑现成单据。
容器内 bench 目录：env/bin/python /workspace/Spike/P1S6R9/ts035-probe.py test.localhost"""
import json
import os
import sys

os.chdir("/workspace/frappe-bench/sites")
import frappe

frappe.init(site=sys.argv[1], sites_path=".")
frappe.connect()
out = {}
out["gl_by_company"] = frappe.db.sql("select company, count(*) n, min(posting_date) d0, max(posting_date) d1 from `tabGL Entry` group by company", as_dict=True)
out["gl_voucher_types"] = frappe.db.sql("select distinct voucher_type, against_voucher_type, party_type from `tabGL Entry`", as_dict=True)
out["sle_by_company"] = frappe.db.sql("select company, voucher_type, count(*) n, min(posting_date) d0, max(posting_date) d1 from `tabStock Ledger Entry` group by company, voucher_type", as_dict=True)
out["pi_submitted"] = frappe.get_all("Purchase Invoice", filters={"docstatus": 1}, fields=["name", "company", "supplier", "inter_company_invoice_reference"])
out["si_draft"] = frappe.get_all("Sales Invoice", filters={"docstatus": 0}, fields=["name", "company", "customer"])
# 修改记录：changed 里旧值为空、新值非空
versions = []
for v in frappe.get_all("Version", fields=["name", "ref_doctype", "docname", "data"], order_by="creation desc", limit=500):
	try:
		data = json.loads(v.data or "{}")
	except Exception:
		continue
	hits = [c for c in data.get("changed") or [] if c[1] in (None, "") and c[2] not in (None, "")]
	if hits and frappe.db.exists(v.ref_doctype, v.docname):
		versions.append({"name": v.name, "ref": f"{v.ref_doctype}/{v.docname}", "hits": hits[:3]})
out["versions_empty_to_value"] = versions[:8]
out["raven_admin"] = frappe.db.get_value("Raven User", {"user": "Administrator"}, ["name", "availability_status"], as_dict=True)
out["crm_lead"] = frappe.get_all("CRM Lead", fields=["name", "lead_owner", "creation"])
out["crm_deal"] = frappe.get_all("CRM Deal", fields=["name", "deal_owner"])
out["contact"] = frappe.get_all("Contact", fields=["name", "salutation"], limit=3)
out["workstation"] = frappe.get_all("Workstation", fields=["name", "status"])
out["work_order"] = frappe.get_all("Work Order", fields=["name", "company", "docstatus"])
out["suppliers"] = frappe.get_all("Supplier", fields=["name"], limit=5)
frappe.destroy()
print(json.dumps(out, ensure_ascii=False, default=str, indent=1))
