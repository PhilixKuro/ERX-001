"""R14 F: read-only. Tax template, tax rows and totals of the act 9 PO vs the latest generator PO of the same wire."""
import json, os
import frappe
os.chdir("/workspace/frappe-bench/sites")
frappe.init(site="erx.localhost", sites_path=".")
frappe.connect()
try:
	from frappe_debug.demo.registry import get_registry
	frappe.local.conf.db_name = get_registry()["work_db"]
	frappe.connect(set_admin_as_user=True)
	rows = frappe.db.sql("""select po.name, po.transaction_date, po.supplier, po.taxes_and_charges, po.net_total, po.total_taxes_and_charges, po.grand_total, po.currency, po.buying_price_list
		from `tabPurchase Order` po join `tabPurchase Order Item` i on i.parent=po.name
		where i.item_code='WIRE-65MN-3.0' and po.docstatus=1 order by po.transaction_date desc, po.creation desc limit 3""", as_dict=True)
	for r in rows:
		r["taxes"] = frappe.get_all("Purchase Taxes and Charges", filters={"parent": r.name}, fields=["account_head", "rate", "tax_amount"])
	print(json.dumps(rows, ensure_ascii=False, default=str))
finally:
	frappe.destroy()
