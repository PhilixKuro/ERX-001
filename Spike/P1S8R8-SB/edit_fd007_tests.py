"""S8 R8 SB FD-007: test assertions and verify check."""

import os

ROOT = "d:/ERX-001/frappe-bench/apps/frappe_debug/frappe_debug"


def edit(rel, pairs):
	path = os.path.join(ROOT, rel)
	with open(path, encoding="utf-8") as handle:
		text = handle.read()
	for old, new in pairs:
		assert text.count(old) == 1, (rel, old[:80])
		text = text.replace(old, new)
	with open(path, "w", encoding="utf-8") as handle:
		handle.write(text)


edit(
	"tests/test_day.py",
	[
		(
			'''		parameters["staff"]["employees"] = 4
''',
			'''		parameters["staff"]["employees"] = 4
		parameters["crm"] = {"open_deal_ratio": 0.5}
''',
		),
		(
			'''		self.assertGreaterEqual(len(orders), 5)
''',
			'''		self.assertGreaterEqual(len(orders), 5)
		# S8 R8 SB FD-007：订单客户来自 30 个客户池；成交商机带订单金额、推进到赢单；另有在途商机
		from frappe_debug.scenario.masters import customer_names

		pool = set(customer_names(scenario))
		order_customers = set(
			frappe.get_all(
				"Sales Order",
				filters={"company": masters["company"], "docstatus": 1},
				pluck="customer_name",
			)
		)
		self.assertTrue(order_customers)
		self.assertLessEqual(order_customers, pool)
		deals = frappe.get_all(
			"CRM Deal",
			filters={"name": ["in", [name for result in results for name in result.deals]]},
			fields=["name", "status", "probability", "expected_deal_value", "deal_value", "closed_date"],
		)
		won = [row for row in deals if row.status == "Won"]
		open_deals = [row for row in deals if row.status != "Won"]
		self.assertEqual(len(won), len(orders))
		self.assertTrue(open_deals)
		self.assertTrue(all(row.probability == 100 and row.deal_value > 0 and row.closed_date for row in won))
		self.assertTrue(
			all(row.status in ("Demo/Making", "Proposal/Quotation", "Negotiation") for row in open_deals)
		)
		self.assertTrue(all(row.expected_deal_value > 0 and row.expected_deal_value != 1000 for row in deals))
		self.assertGreater(len({row.expected_deal_value for row in deals}), 1)
		self.assertTrue(
			all(
				frappe.db.get_value("CRM Deal Status", row.status, "probability") == row.probability
				for row in open_deals
			)
		)
''',
		),
	],
)

edit(
	"scenario/verify.py",
	[
		(
			'''	# S8 R8 SB FD-004：拒收数量不开票''',
			'''	# S8 R8 SB FD-007：订单客户来自客户池；转了订单的商机为赢单；另有在途商机
	from frappe_debug.scenario.masters import customer_names

	pool = set(customer_names(sc))
	outside = frappe.db.sql(
		"""select distinct customer_name from `tabSales Order`
		where company=%s and docstatus=1 and transaction_date between %s and %s""",
		(company, sc.S, sc.E),
		pluck=True,
	)
	outside = sorted(set(outside) - pool)[:20]
	_check(checks, "crm.customer_pool", {"outside_pool": outside}, not outside)
	deal_status = dict(
		frappe.db.sql(
			"""select deal.status, count(*) from `tabCRM Deal` deal
			where exists (select 1 from `tabQuotation` q where q.crm_deal = deal.name
			and q.company=%s and q.docstatus=1)
			group by deal.status""",
			(company,),
		)
	)
	unwon_ordered = frappe.db.sql(
		"""select count(distinct deal.name) from `tabCRM Deal` deal
		join `tabQuotation` q on q.crm_deal = deal.name and q.docstatus=1 and q.company=%s
		join `tabSales Order Item` soi on soi.prevdoc_docname = q.name
		join `tabSales Order` so on so.name = soi.parent and so.docstatus=1
		where deal.status <> 'Won'""",
		(company,),
	)[0][0]
	_check(
		checks,
		"crm.deal_progress",
		{"statuses": deal_status, "ordered_not_won": unwon_ordered},
		not unwon_ordered and any(status != "Won" for status in deal_status),
	)

	# S8 R8 SB FD-004：拒收数量不开票''',
		)
	],
)
print("ok")
