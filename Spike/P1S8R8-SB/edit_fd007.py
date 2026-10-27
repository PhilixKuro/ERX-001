"""S8 R8 SB FD-007 edit script: deal values, stage progression, open deals, customer pool."""

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
	"scenario/masters.py",
	[
		(
			'''def _customers(sc, company, customer_group, territory):
	result = []
	for index in range(sc.raw["parties"]["customers"]):
		city = sc.raw["parties"]["name_pool"][index % len(sc.raw["parties"]["name_pool"])]
		suffix = f"{index + 1:02d}" if index >= len(sc.raw["parties"]["name_pool"]) else ""
		name = f"{city}{suffix}弹簧厂"
		customer = _insert_if_missing(''',
			'''def customer_names(sc) -> list[str]:
	"""Names of the scenario customer pool, in creation order (FD-007 orders draw from it)."""
	pool = sc.raw["parties"]["name_pool"]
	names = []
	for index in range(sc.raw["parties"]["customers"]):
		city = pool[index % len(pool)]
		suffix = f"{index + 1:02d}" if index >= len(pool) else ""
		names.append(f"{city}{suffix}弹簧厂")
	return names


def _customers(sc, company, customer_group, territory):
	result = []
	for name in customer_names(sc):
		customer = _insert_if_missing(''',
		)
	],
)

edit(
	"scenario/day.py",
	[
		(
			"def _new_orders(sc, day, rng, masters, result):",
			'''def _stream(sc, day, tag: str) -> random.Random:
	"""A separate repeatable stream, so new draws leave the day's main stream unchanged."""
	key = f"{sc.raw.get('seed', 0)}:{getdate(day).isoformat()}:{tag}".encode()
	return random.Random(int.from_bytes(hashlib.sha256(key).digest()[:8], "big"))


def _status_probability(status: str) -> float:
	return flt(frappe.db.get_value("CRM Deal Status", status, "probability"))


def _advance_deal(deal: str, status: str, **values) -> None:
	"""Move a deal forward through the native save so CRM writes its status log (FD-007)."""
	doc = frappe.get_doc("CRM Deal", deal)
	doc.update({"status": status, "probability": _status_probability(status), **values})
	doc.save(ignore_permissions=True)


def _customer_pool(sc) -> list[str]:
	from frappe_debug.scenario.masters import customer_names

	names = customer_names(sc)
	if not names:
		frappe.throw("场景客户池为空（parties.customers）")
	return names


def _demand_qty(sc, day, rng, product) -> float:
	qty_config = demand_quantity_config(sc, day)
	return max(
		qty_config["round"],
		round(rng.gauss(qty_config["mean"], qty_config["sd"]) / qty_config["round"]) * qty_config["round"],
	)


def _open_deals(sc, day, count, masters, result):
	"""Deals still in progress at the end of the day, with no sales order (FD-007)."""
	ratio = flt((sc.raw.get("crm") or {}).get("open_deal_ratio"))
	if ratio <= 0 or count <= 0:
		return
	stream = _stream(sc, day, "open-deals")
	expected = count * ratio
	extra = int(expected) + int(stream.random() < expected % 1)
	customers = _customer_pool(sc)
	for _index in range(extra):
		organization = stream.choice(customers)
		product = choose_demand_product(sc, stream)
		qty = _demand_qty(sc, day, stream, product)
		lead = create_lead({"first_name": "采购联系人", "organization": organization})
		deal = convert_lead_to_deal(
			lead,
			{
				"expected_deal_value": flt(qty * product["price"], 2),
				"expected_closure_date": day + timedelta(days=stream.randint(7, 30)),
				"probability": _status_probability("Qualification"),
			},
		)
		stage = stream.choice(["Demo/Making", "Proposal/Quotation", "Negotiation"])
		if stage != "Demo/Making":
			warehouse = frappe.db.get_value(
				"Item Default", {"parent": product["code"], "company": masters["company"]}, "default_warehouse"
			)
			quotation = make_and_submit_quotation(
				deal,
				masters["company"],
				[{"item_code": product["code"], "qty": qty, "rate": product["price"], "warehouse": warehouse}],
				day,
				max(day + timedelta(days=30), getdate()),
				time=result.next_time(),
			)
			result.quotations.append(quotation)
		_advance_deal(deal, stage)
		result.leads.append(lead)
		result.deals.append(deal)


def _new_orders(sc, day, rng, masters, result):''',
		),
		(
			'''	for index in range(count):
		organization = f"{sc.raw['company']['abbr']} 场景客户 {day:%Y%m%d}-{index + 1:02d}"
		lead = create_lead({"first_name": "采购联系人", "organization": organization})
		deal = convert_lead_to_deal(
			lead,
			{
				"expected_deal_value": 1000,
				"expected_closure_date": day + timedelta(days=7),
				"probability": 60,
			},
		)
		result.leads.append(lead)
		result.deals.append(deal)
		product = choose_demand_product(sc, rng)
		qty_config = demand_quantity_config(sc, day)
		qty = max(
			qty_config["round"],
			round(rng.gauss(qty_config["mean"], qty_config["sd"]) / qty_config["round"])
			* qty_config["round"],
		)
		warehouse''',
			'''	customers = _customer_pool(sc)
	customer_stream = _stream(sc, day, "customers")
	for _index in range(count):
		# FD-007: orders come from the scenario customer pool; CRM's Sales Order hook then finds
		# the existing Customer by name (erpnext/crm/frappe_crm_api.py create_customer)
		organization = customer_stream.choice(customers)
		product = choose_demand_product(sc, rng)
		qty = _demand_qty(sc, day, rng, product)
		lead = create_lead({"first_name": "采购联系人", "organization": organization})
		deal = convert_lead_to_deal(
			lead,
			{
				"expected_deal_value": flt(qty * product["price"], 2),
				"expected_closure_date": day + timedelta(days=7),
				"probability": _status_probability("Qualification"),
			},
		)
		result.leads.append(lead)
		result.deals.append(deal)
		warehouse''',
		),
		(
			'''			time=result.next_time(),
		)
		order = make_and_submit_sales_order(
			quotation,
			day,
			time=result.next_time(),
			delivery_date=day + timedelta(days=rng.randint(*sc.raw["demand"]["lead_days"])),
		)
		result.quotations.append(quotation)
		result.sales_orders.append(order)
''',
			'''			time=result.next_time(),
		)
		_advance_deal(deal, "Proposal/Quotation")
		order = make_and_submit_sales_order(
			quotation,
			day,
			time=result.next_time(),
			delivery_date=day + timedelta(days=rng.randint(*sc.raw["demand"]["lead_days"])),
		)
		_advance_deal(
			deal,
			"Won",
			deal_value=frappe.db.get_value("Sales Order", order, "net_total"),
			closed_date=day,
		)
		result.quotations.append(quotation)
		result.sales_orders.append(order)
	_open_deals(sc, day, count, masters, result)
''',
		),
	],
)

edit(
	"scenario/params.py",
	[
		(
			'''	if "purchase" in raw:
		purchase = v.mapping(raw["purchase"], "purchase")''',
			'''	if "crm" in raw:
		crm = v.mapping(raw["crm"], "crm")
		v.numeric(crm.get("open_deal_ratio"), "crm.open_deal_ratio", maximum=1)
	if "purchase" in raw:
		purchase = v.mapping(raw["purchase"], "purchase")''',
		)
	],
)

edit(
	"data/scenario.yaml",
	[
		(
			"# IT-013: share of each received line rejected at inspection, drawn per receipt in [0, 2x].",
			"""# FD-007: extra deals per ordered deal that stay open (no sales order) at a mid stage.
crm:
  open_deal_ratio: 0.25
# IT-013: share of each received line rejected at inspection, drawn per receipt in [0, 2x].""",
		)
	],
)
print("ok")
