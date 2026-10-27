"""Dates of act-created documents in the erx rehearsal work db (read-only)."""
import json
import os

import frappe

os.chdir("/workspace/frappe-bench/sites")
frappe.init(site="erx.localhost", sites_path=".")
frappe.connect()
try:
	from frappe_debug.demo.registry import get_registry

	frappe.local.conf.db_name = get_registry()["work_db"]
	frappe.connect(set_admin_as_user=True)
	from frappe_debug.scenario.params import load_scenario

	sc = load_scenario()
	print("D1", sc.D1, "D2", sc.D2, "E", sc.E, "segments", sc.segments)
	print(frappe.db.sql("""select name, transaction_date, customer_name, po_no from `tabSales Order` where customer_name like %s""", ("%第1幕%",), as_dict=True))
	print(frappe.db.sql("""select d.name, d.status, q.name q, q.transaction_date from `tabCRM Deal` d join `tabQuotation` q on q.crm_deal=d.name where d.status<>'Won' and exists(select 1 from `tabSales Order Item` i join `tabSales Order` s on s.name=i.parent and s.docstatus=1 where i.prevdoc_docname=q.name)""", as_dict=True))
	print(frappe.db.sql("""select date(min(tl.from_time)), date(max(tl.from_time)), count(*) from `tabJob Card Time Log` tl join `tabJob Card` jc on jc.name=tl.parent where jc.name between 'PO-JOB00474' and 'PO-JOB00486'"""))
	days = frappe.db.sql("""select distinct posting_date from `tabStock Entry` where docstatus=1 and posting_date in %s""", ((sc.D1, sc.D2, sc.E),))
	print("stock entries on act days", days)
finally:
	frappe.destroy()
