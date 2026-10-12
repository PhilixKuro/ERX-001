"""R9 TS-035 第 2 屏用：把测试站现有供应商临时标成内部供应商，截完图恢复。
容器内 bench 目录：env/bin/python /workspace/Spike/P1S6R9/ts035-data.py test.localhost setup|teardown|show
setup 先把原值写进 ts035-data-saved.json，teardown 按该文件写回并删文件。
上游 purchase_invoice.js:221-234 只在前端读 Supplier 的 is_internal_supplier／disabled 决定是否加按钮，
故只改这一处字段即可，不另建单据，测试站不留新记录。"""
import json
import os
import sys

os.chdir("/workspace/frappe-bench/sites")
import frappe

SUPPLIER = "_S6R6 验收供应商"
INVOICE = "ACC-PINV-2026-00006"
SAVED = "/workspace/Spike/P1S6R9/ts035-data-saved.json"
FIELDS = ["is_internal_supplier", "represents_company", "disabled"]
LEAD_PREFIX = "_S6R9TS035-"
LEADS = 21

site, mode = sys.argv[1], sys.argv[2]
frappe.init(site=site, sites_path=".")
frappe.connect()
try:
	if mode == "setup":
		if os.path.exists(SAVED):
			raise SystemExit(f"{SAVED} exists; run teardown first")
		original = frappe.db.get_value("Supplier", SUPPLIER, FIELDS, as_dict=True)
		pi = frappe.db.get_value("Purchase Invoice", INVOICE, ["supplier", "docstatus", "inter_company_invoice_reference"], as_dict=True)
		if pi.supplier != SUPPLIER or pi.docstatus != 1 or pi.inter_company_invoice_reference:
			raise SystemExit(f"{INVOICE} no longer fits: {pi}")
		with open(SAVED, "w", encoding="utf-8") as f:
			json.dump(original, f, ensure_ascii=False)
		frappe.db.set_value("Supplier", SUPPLIER, {"is_internal_supplier": 1, "represents_company": "_FCT CRM 验证"}, update_modified=False)
		# 第 7 屏：CRM 列表每页 20 行，行数少于总数才渲染 Load More（ListFooter.vue:12-16）
		for i in range(LEADS):
			frappe.get_doc({"doctype": "CRM Lead", "first_name": f"{LEAD_PREFIX}{i:02d}"}).insert(ignore_permissions=True)
		frappe.db.commit()
		frappe.clear_document_cache("Supplier", SUPPLIER)
	elif mode == "teardown":
		with open(SAVED, encoding="utf-8") as f:
			original = json.load(f)
		frappe.db.set_value("Supplier", SUPPLIER, original, update_modified=False)
		for name in frappe.get_all("CRM Lead", filters={"first_name": ["like", f"{LEAD_PREFIX}%"]}, pluck="name"):
			frappe.delete_doc("CRM Lead", name, ignore_permissions=True, force=True)
		frappe.db.commit()
		frappe.clear_document_cache("Supplier", SUPPLIER)
		os.remove(SAVED)
	state = frappe.db.get_value("Supplier", SUPPLIER, FIELDS + ["modified"], as_dict=True)
	state["temp_leads"] = frappe.db.count("CRM Lead", {"first_name": ["like", f"{LEAD_PREFIX}%"]})
	state["all_leads"] = frappe.db.count("CRM Lead")
	print(json.dumps(state, ensure_ascii=False, default=str))
finally:
	frappe.destroy()
