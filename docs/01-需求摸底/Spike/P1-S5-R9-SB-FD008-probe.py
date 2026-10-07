"""FD-008 探针：复制建账的中式公司若纳入建账自检，能否通过。只在测试站跑，最后整体 rollback。"""
import json
import frappe

frappe.init(site="test.localhost", sites_path=".")
frappe.connect()
try:
	frappe.set_user("Administrator")
	from frappe_china.accounting import selfcheck
	from frappe_china.accounting.company import is_cn_company
	from frappe_china.tests.utils import make_cn_company

	src = make_cn_company("_FCT 探针源", "FPS").name
	copy = frappe.get_doc({
		"doctype": "Company", "company_name": "_FCT 探针复制", "abbr": "FPC",
		"default_currency": "CNY", "country": "China",
		"create_chart_of_accounts_based_on": "Existing Company", "existing_company": src,
	}).insert(ignore_permissions=True).name
	print("chart_of_accounts of copy:", repr(frappe.db.get_value("Company", copy, "chart_of_accounts")))
	print("is_cn_company(copy):", is_cn_company(copy))
	orig = selfcheck.is_cn_chart
	selfcheck.is_cn_chart = lambda _chart: True
	try:
		r = selfcheck.check_company_chart(copy)
	finally:
		selfcheck.is_cn_chart = orig
	print(json.dumps(r, ensure_ascii=False, indent=1))
	print("all companies on site:", frappe.get_all("Company", fields=["name", "chart_of_accounts", "existing_company"]))
finally:
	frappe.db.rollback()
	frappe.destroy()
