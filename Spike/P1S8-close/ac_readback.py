"""S8 Stage closure: read-only readback for AC items not covered by scenario verify (AC-001/003/012/015/016).

Reads the erx prerun work db through a second connection; writes nothing.
Usage (container): python ac_readback.py -> frappe-bench/logs/s8-close-ac-readback.json
"""

import json
import os

import frappe

os.chdir("/workspace/frappe-bench/sites")
frappe.init(site="erx.localhost", sites_path=".")
frappe.connect()
out = {}
try:
	from frappe_debug.demo.registry import get_registry

	out["live_db"] = frappe.conf.db_name
	work = get_registry()["work_db"]
	frappe.local.conf.db_name = work
	frappe.connect(set_admin_as_user=True)
	out["db"] = frappe.db.cur_db_name
	company = "华东弹簧有限公司"
	out["AC-001.expenses_added_to_stock_account"] = frappe.db.get_value("Company", company, "expenses_added_to_stock_account")
	out["AC-003.400101"] = frappe.db.sql(
		"select name, account_type from tabAccount where account_number='400101'", as_dict=True
	)
	out["AC-012.cn_piece_rate_precision"] = frappe.db.sql(
		"select dt, fieldname, `precision`, fieldtype from `tabCustom Field` where fieldname='cn_piece_rate'",
		as_dict=True,
	)
	out["AC-012.piece_rate_sample"] = frappe.db.sql(
		"select cn_piece_rate from `tabBOM Operation` where cn_piece_rate>0 limit 5", as_list=True
	)
	out["AC-015.gender"] = frappe.get_all("Gender", pluck="name")
	out["AC-015.salutation"] = frappe.get_all("Salutation", pluck="name")
	out["AC-015.batch_switch"] = {
		k: frappe.db.get_single_value("Stock Settings", k)
		for k in ("use_naming_series", "enable_batch_wise_valuation", "use_serial_batch_fields")
		if frappe.get_meta("Stock Settings").has_field(k)
	}
	out["AC-015.mode_of_payment"] = frappe.db.sql(
		"select parent, default_account from `tabMode of Payment Account` where company=%s", company, as_dict=True
	)
	out["AC-015.admin_name"] = frappe.db.get_value("User", "Administrator", ["first_name", "full_name"], as_dict=True)
	out["AC-016.installed_apps"] = frappe.get_installed_apps()
	from frappe_china.install import check_app_order

	out["AC-016.check_app_order"] = check_app_order()
	out["scheduler_disabled"] = frappe.utils.scheduler.is_scheduler_disabled()
	out["Translation"] = frappe.db.count("Translation")
finally:
	with open("/workspace/frappe-bench/logs/s8-close-ac-readback.json", "w", encoding="utf-8") as stream:
		json.dump(out, stream, ensure_ascii=False, indent=1, default=str)
	print(json.dumps(out, ensure_ascii=False, default=str))
	frappe.destroy()
