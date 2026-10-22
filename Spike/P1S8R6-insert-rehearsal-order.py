"""Insert the planned 5,000-piece order between the first and second S8 segments."""

from datetime import date

import frappe
from frappe.utils import getdate

from frappe_debug.builders.crm import convert_lead_to_deal, create_lead, make_and_submit_quotation
from frappe_debug.builders.selling import make_and_submit_sales_order
from frappe_debug.scenario.params import load_scenario


def run():
	scenario = load_scenario()
	company = frappe.db.get_value("Company", {"company_name": scenario.raw["company"]["name"]}, "name")
	product = scenario.raw["items"]["products"][0]
	warehouse = frappe.db.get_value(
		"Item Default", {"parent": product["code"], "company": company}, "default_warehouse"
	)
	day = scenario.D1 - date.resolution
	delivery_date = scenario.D1 + date.resolution
	lead = create_lead({"first_name": "5000 支续跑订单", "organization": "S8 演示客户 5000"})
	deal = convert_lead_to_deal(
		lead,
		{"expected_deal_value": product["price"] * 5000, "expected_closure_date": delivery_date, "probability": 100},
	)
	quotation = make_and_submit_quotation(
		deal,
		company,
		[{"item_code": product["code"], "qty": 5000, "rate": product["price"], "warehouse": warehouse}],
		day,
		max(day + date.resolution * 30, getdate()),
	)
	order = make_and_submit_sales_order(quotation, day, delivery_date=delivery_date)
	return {"lead": lead, "deal": deal, "quotation": quotation, "sales_order": order, "qty": 5000}
