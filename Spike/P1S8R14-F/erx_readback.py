"""R14 F re-review: read-only checks on the erx prerun work db (second connection, no writes).

1. 12 scorecards: stored supplier_score/status vs a recomputation from submitted periods with the
   R12 weighting (only periods with total_received_items > 0, weight (12 - period_number) / 12).
2. Criteria formulas and weighting functions equal the R12 constants.
3. Act 9: purchase orders dated E, supplier/rate/schedule_date/docstatus; E prices of the 4 wire suppliers.
4. Target-wire suggestions from E-8 on, by rule and status.
Usage (container, cwd sites/): python -I erx_readback.py  -> frappe-bench/logs/s8-r14f-erx-readback.json
"""

import json
import os
from datetime import timedelta

import frappe

os.chdir("/workspace/frappe-bench/sites")
frappe.init(site="erx.localhost", sites_path=".")
frappe.connect()
out = {}
try:
	from frappe_debug.demo.registry import get_registry

	work = get_registry()["work_db"]
	out["live_db"] = frappe.conf.db_name
	frappe.local.conf.db_name = work
	frappe.connect(set_admin_as_user=True)
	out["work_db"] = frappe.db.cur_db_name
	from frappe_debug.scenario.params import load_scenario
	from frappe_debug.scenario.support import SCORECARD_CRITERIA, SCORECARD_WEIGHTING

	sc = load_scenario()
	out["E"] = str(sc.E)
	names = sorted({s for m in sc.raw["items"]["materials"] for s in m["suppliers"]})
	cards = []
	for display in names:
		supplier = frappe.db.get_value("Supplier", {"supplier_name": display}, "name")
		card = frappe.get_doc("Supplier Scorecard", {"supplier": supplier})
		periods = frappe.db.sql(
			"""select p.name, p.start_date, p.total_score, p.docstatus,
			(select v.value from `tabSupplier Scorecard Scoring Variable` v
			 where v.parent=p.name and v.param_name='total_received_items') received
			from `tabSupplier Scorecard Period` p where p.supplier=%s order by p.start_date desc""",
			(supplier,),
			as_dict=True,
		)
		num = den = 0.0
		# Native calculate_total_score: submitted periods only, newest first, period_number from 0.
		for n, p in enumerate(p for p in periods if p.docstatus == 1):
			w = max(0, min(1, (12 - n) / 12)) * (1 if float(p.received or 0) > 0 else 0)
			num += float(p.total_score) * w
			den += 100 * w
		cards.append(
			{
				"supplier": display,
				"stored_score": round(float(card.supplier_score), 2),
				"recomputed": round(num / den * 100, 2) if den else 100,
				"status": card.status,
				"periods": len(periods),
				"submitted": sum(p.docstatus == 1 for p in periods),
				"scored": sum(float(p.received or 0) > 0 for p in periods),
				"weighting_ok": card.weighting_function == SCORECARD_WEIGHTING,
				"criteria": [(c.criteria_name, c.weight) for c in card.criteria],
			}
		)
	out["cards"] = cards
	out["criteria_ok"] = [
		frappe.db.get_value("Supplier Scorecard Criteria", n, "formula") == f for n, f in SCORECARD_CRITERIA
	]
	item = sc.raw["act_targets"]["act9_eoq_item"]
	out["act9_pos"] = frappe.db.sql(
		"""select po.name, po.supplier, po.docstatus, po.transaction_date, po.schedule_date,
		poi.item_code, poi.qty, poi.rate, poi.material_request
		from `tabPurchase Order` po join `tabPurchase Order Item` poi on poi.parent=po.name
		where po.transaction_date=%s and poi.item_code=%s""",
		(sc.E, item),
		as_dict=True,
	)
	out["lead_time_days"] = frappe.db.get_value("Item", item, "lead_time_days")
	wire = next(m for m in sc.raw["items"]["materials"] if m["code"] == item)
	prices = {}
	for display in wire["suppliers"]:
		supplier = frappe.db.get_value("Supplier", {"supplier_name": display}, "name")
		prices[display] = frappe.db.get_value(
			"Item Price",
			{"item_code": item, "price_list": "Standard Buying", "supplier": supplier, "valid_from": ("<=", sc.E)},
			"price_list_rate",
			order_by="valid_from desc",
		)
	out["act9_prices"] = prices
	out["suggestions"] = frappe.get_all(
		"Replenishment Suggestion",
		filters={"item_code": item, "calculation_date": (">=", sc.E - timedelta(days=8))},
		fields=["calculation_date", "rule", "status", "suggested_qty"],
		order_by="calculation_date, rule",
	)
	out["rejection_by_supplier"] = frappe.db.sql(
		"""select pr.supplier, sum(pri.received_qty) received, sum(pri.rejected_qty) rejected
		from `tabPurchase Receipt` pr join `tabPurchase Receipt Item` pri on pri.parent=pr.name
		where pr.docstatus=1 group by pr.supplier order by pr.supplier""",
		as_dict=True,
	)
finally:
	frappe.destroy()
with open("/workspace/frappe-bench/logs/s8-r14f-erx-readback.json", "w", encoding="utf-8") as stream:
	json.dump(out, stream, ensure_ascii=False, indent=1, default=str)
print(json.dumps(out, ensure_ascii=False, default=str)[:6000])
