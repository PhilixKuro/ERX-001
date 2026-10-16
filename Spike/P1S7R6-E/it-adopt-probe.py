"""E probe: SL-005 ③④⑦⑩ on real records — adopt/ignore/bulk, order rule flag + MR coverage, run_now roles. Rolled back."""
import json

import frappe
from frappe.utils import add_days, today

from frappe_china.replenishment.rules import order_proposals
from frappe_china.stock_plus.doctype.replenishment_suggestion.replenishment_suggestion import adopt, bulk_action, ignore

assert frappe.local.site == "test.localhost"
company = "_Test Company"
currency = frappe.db.get_value("Company", company, "default_currency")
tag = frappe.generate_hash(length=6)
wh = "Stores - _TC"
out = {}
before_errors = set(frappe.get_all("Error Log", pluck="name"))


def item(code, **kw):
	return frappe.get_doc({"doctype": "Item", "item_code": f"_FCT E {code} {tag}", "item_group": "Products",
		"stock_uom": "Nos", "is_stock_item": 1, "valuation_rate": 1, "default_warehouse": wh,
		"item_defaults": [{"company": company, "default_warehouse": wh}], **kw}).insert()


def suggestion(it, qty=5):
	return frappe.get_doc({"doctype": "Replenishment Suggestion", "company": company, "item_code": it, "warehouse": wh,
		"rule": "EOQ", "calculation_date": add_days(today(), -1), "suggested_qty": qty, "material_request_type": "Purchase",
		"basis": [{"basis": "EOQ", "value": qty}]}).insert()


try:
	customer = frappe.get_doc({"doctype": "Customer", "customer_name": "_FCT E Cust " + tag, "customer_group": frappe.db.get_value("Customer Group", {"is_group": 0}), "territory": frappe.db.get_value("Territory", {"is_group": 0})}).insert().name
	rm = item("RM")
	s1, s2, s3 = suggestion(rm.name), suggestion(rm.name), suggestion(rm.name)
	mr = adopt(s1.name, 7)
	mrd = frappe.get_doc("Material Request", mr)
	s1.reload()
	out["3_adopt"] = dict(mr_docstatus=mrd.docstatus, mr_date=str(mrd.transaction_date), calc=str(s1.calculation_date),
		backref=mrd.cn_replenishment_suggestion == s1.name, status=s1.status, qty=s1.suggested_qty, linked=s1.material_request == mr)
	n_mr = frappe.db.count("Material Request", {"cn_replenishment_suggestion": s2.name})
	ignore(s2.name)
	out["3_ignore"] = dict(status=frappe.db.get_value("Replenishment Suggestion", s2.name, "status"),
		no_mr=frappe.db.count("Material Request", {"cn_replenishment_suggestion": s2.name}) == n_mr == 0)
	res = bulk_action(json.dumps([s3.name, s2.name]), "adopt")
	out["4_bulk"] = [(r["ok"], r.get("error", "")[:60]) for r in res]
	# ⑦ order rule: FG with BOM; one RM flagged, one not
	fg = item("FG")
	rm_flag, rm_noflag = item("RMF", cn_rule_order=1), item("RMN")
	b = frappe.get_doc({"doctype": "BOM", "item": fg.name, "company": company, "quantity": 1, "currency": currency,
		"items": [{"item_code": rm_flag.name, "qty": 2}, {"item_code": rm_noflag.name, "qty": 3}]})
	b.insert(); b.submit()
	so = frappe.get_doc({"doctype": "Sales Order", "company": company, "customer": customer,
		"transaction_date": today(), "delivery_date": add_days(today(), 10), "currency": currency, "selling_price_list": "Standard Selling",
		"items": [{"item_code": fg.name, "qty": 5, "rate": 10, "warehouse": "Finished Goods - _TC", "delivery_date": add_days(today(), 10)}]})
	so.insert(); so.submit()
	problems = []
	props = order_proposals(company, frappe.utils.getdate(today()), problems)
	mine = {p["item_code"]: p["qty"] for p in props if p["item_code"] in (rm_flag.name, rm_noflag.name)}
	out["7_order_flagged_only"] = {"flagged": mine.get(rm_flag.name), "unflagged_present": rm_noflag.name in mine, "problems": problems[:3]}
	mr2 = frappe.get_doc({"doctype": "Material Request", "material_request_type": "Purchase", "company": company,
		"transaction_date": today(), "schedule_date": today(),
		"items": [{"item_code": rm_flag.name, "qty": 4, "warehouse": wh, "schedule_date": today(), "uom": "Nos", "conversion_factor": 1}]})
	mr2.insert(); mr2.submit()
	props = order_proposals(company, frappe.utils.getdate(today()), [])
	out["7_after_mr_4"] = {p["item_code"][-10:]: p["qty"] for p in props if p["item_code"] == rm_flag.name}
	# ⑩ roles
	for role in ("Stock User", "Stock Manager"):
		email = f"fct-e-{role.replace(' ', '').lower()}-{tag}@example.com"
		u = frappe.get_doc({"doctype": "User", "email": email, "first_name": "E", "send_welcome_email": 0,
			"roles": [{"role": role}]}).insert(ignore_permissions=True)
		frappe.set_user(u.name)
		try:
			from unittest.mock import patch
			from frappe_china.replenishment import daily
			with patch.object(daily, "run_daily", return_value={"ok": True}), patch.object(daily.frappe.db, "commit"):
				daily.run_now()
			out[f"10_{role}"] = "allowed"
		except frappe.PermissionError:
			out[f"10_{role}"] = "denied"
		finally:
			frappe.set_user("Administrator")
except Exception as error:
	out["ERROR"] = f"{type(error).__name__}: {str(error)[:400]}"
	out["TRACE"] = frappe.get_traceback()[-1200:]
finally:
	frappe.db.rollback()
	new = [n for n in frappe.get_all("Error Log", pluck="name") if n not in before_errors]
	for n in new:
		frappe.delete_doc("Error Log", n, ignore_permissions=True)
	frappe.db.commit()
	out["error_logs_removed"] = len(new)
	print(json.dumps(out, ensure_ascii=False, default=str, indent=1))
