"""选 BOM 三条建单路径的真 DocType 用例（开发方案 Part1 TS-006 验证方式，SL-004 ③～⑥；R7 F FD-012 补）。

两份 BOM 原料单价相同，只差工作中心工价：原生默认 BOM 工价高、另一份工价低，
故三条路径都应改选非默认的那份（同时覆盖 FD-006「工价取工作中心现价」）。
"""

import json

import frappe
from erpnext.manufacturing.doctype.production_plan.production_plan import get_items_for_material_requests
from erpnext.manufacturing.doctype.work_order.work_order import get_item_details
from erpnext.selling.doctype.sales_order.sales_order import make_work_orders
from frappe.utils import add_days, today

from frappe_china.tests.utils import TEST_PREFIX, FrappeChinaTestCase

COMPANY = "_Test Company"
STORES = "Stores - _TC"
WIP = "Work In Progress - _TC"
FG = "Finished Goods - _TC"


class TestBomSelectionHooks(FrappeChinaTestCase):
	def setUp(self):
		super().setUp()
		capacity_planning = frappe.db.get_single_value("Manufacturing Settings", "disable_capacity_planning")
		self.addCleanup(
			frappe.db.set_single_value,
			"Manufacturing Settings",
			"disable_capacity_planning",
			capacity_planning,
		)
		frappe.db.set_single_value("Manufacturing Settings", "disable_capacity_planning", 1)
		self.suffix = frappe.generate_hash(length=6)
		self.fg = self._item("FG", cn_auto_select_bom=1)
		self.raw_default = self._item("RM Default")
		self.raw_cheap = self._item("RM Cheap")
		# 原生默认 BOM：工价 600／时；另一份 60／时。工时各 10 分钟，原料各 1 件、单价同为 1
		self.bom_default = self._bom(self.raw_default, hour_rate=600, is_default=1)
		self.bom_cheap = self._bom(self.raw_cheap, hour_rate=60, is_default=0)
		self.assertEqual(frappe.db.get_value("Item", self.fg, "default_bom"), self.bom_default)

	def test_work_order_form_path_switches_native_default(self):
		work_order = frappe.new_doc("Work Order")
		work_order.update(
			{
				"company": COMPANY,
				"production_item": self.fg,
				"qty": 10,
				"wip_warehouse": WIP,
				"fg_warehouse": FG,
				"source_warehouse": STORES,
				"skip_transfer": 1,
				"reserve_stock": 0,
			}
		)
		work_order.update(get_item_details(self.fg))
		self.assertEqual(work_order.bom_no, self.bom_default)
		work_order.get_items_and_operations_from_bom()
		work_order.insert()

		self._assert_uses_cheap_bom(work_order.name)
		comments = frappe.get_all(
			"Comment",
			filters={"reference_doctype": "Work Order", "reference_name": work_order.name},
			pluck="content",
		)
		self.assertEqual(len(comments), 1)
		self.assertIn(self.bom_cheap, comments[0])
		self.assertIn(self.bom_default, comments[0])
		self.assertIn("按成本自动选用", comments[0])

	def test_work_order_form_path_keeps_explicit_choice(self):
		self._bom(self.raw_default, hour_rate=900, is_default=0, name_hint="manual")
		manual = frappe.get_all(
			"BOM", filters={"item": self.fg, "docstatus": 1}, order_by="creation desc", pluck="name"
		)[0]
		work_order = frappe.get_doc(
			{
				"doctype": "Work Order",
				"company": COMPANY,
				"production_item": self.fg,
				"bom_no": manual,
				"qty": 10,
				"wip_warehouse": WIP,
				"fg_warehouse": FG,
				"skip_transfer": 1,
				"reserve_stock": 0,
			}
		)
		work_order.get_items_and_operations_from_bom()
		work_order.insert()

		self.assertEqual(work_order.bom_no, manual)
		comment = frappe.get_all(
			"Comment",
			filters={"reference_doctype": "Work Order", "reference_name": work_order.name},
			pluck="content",
		)[0]
		self.assertIn("人工指定", comment)
		self.assertIn(self.bom_cheap, comment)

	def test_work_order_confirmed_and_kept_sources_are_preserved(self):
		for source, bom, phrase in (
			("confirmed", self.bom_cheap, "按成本推荐、人已确认"),
			("kept", self.bom_default, "按成本推荐、人选择保留"),
			("manual", self.bom_default, "人工指定"),
		):
			with self.subTest(source=source):
				work_order = frappe.get_doc(
					{
						"doctype": "Work Order",
						"company": COMPANY,
						"production_item": self.fg,
						"bom_no": bom,
						"cn_bom_source": source,
						"qty": 10,
						"wip_warehouse": WIP,
						"fg_warehouse": FG,
						"skip_transfer": 1,
						"reserve_stock": 0,
					}
				)
				work_order.get_items_and_operations_from_bom()
				work_order.insert()
				work_order.reload()
				self.assertEqual((work_order.bom_no, work_order.cn_bom_source), (bom, source))
				self.assertEqual({row.bom for row in work_order.operations}, {bom})
				comment = frappe.get_all(
					"Comment",
					filters={
						"reference_doctype": "Work Order",
						"reference_name": work_order.name,
					},
					pluck="content",
				)
				self.assertEqual(len(comment), 1)
				self.assertIn(phrase, comment[0])
				self.assertIn(self.bom_default, comment[0])
				self.assertIn(self.bom_cheap, comment[0])

	def test_plan_kept_default_is_not_overwritten_when_creating_work_order(self):
		order = self._sales_order(30)
		plan = frappe.get_doc(
			{
				"doctype": "Production Plan",
				"company": COMPANY,
				"get_items_from": "Sales Order",
				"posting_date": today(),
				"sales_orders": [{"sales_order": order.name}],
			}
		)
		plan.get_items()
		plan.po_items[0].warehouse = FG
		plan.po_items[0].cn_bom_source = "kept"
		plan.save()
		plan.reload()
		self.assertEqual(
			(plan.po_items[0].bom_no, plan.po_items[0].cn_bom_source), (self.bom_default, "kept")
		)
		plan.submit()
		plan.make_work_order()
		names = frappe.get_all("Work Order", filters={"production_plan": plan.name}, pluck="name")
		self.assertEqual(len(names), 1)
		work_order = frappe.get_doc("Work Order", names[0])
		self.assertEqual(work_order.bom_no, self.bom_default)
		self.assertEqual({row.item_code for row in work_order.required_items}, {self.raw_default})
		comments = frappe.get_all(
			"Comment",
			filters={
				"reference_doctype": "Work Order",
				"reference_name": names[0],
			},
			pluck="content",
		)
		self.assertEqual(len(comments), 1)
		self.assertIn("由生产计划带入", comments[0])

	def test_sales_order_path(self):
		order = self._sales_order(20)
		names = make_work_orders(
			json.dumps(
				{
					"items": [
						{
							"item_code": self.fg,
							"bom": self.bom_default,
							"pending_qty": 20,
							"sales_order_item": order.items[0].name,
							"warehouse": FG,
							"description": self.fg,
						}
					]
				}
			),
			order.name,
			COMPANY,
		)
		self.assertEqual(len(names), 1)
		self._assert_uses_cheap_bom(names[0])
		comments = frappe.get_all(
			"Comment",
			filters={
				"reference_doctype": "Work Order",
				"reference_name": names[0],
			},
			pluck="content",
		)
		self.assertEqual(len(comments), 1)
		self.assertIn("按成本自动选用", comments[0])

	def test_production_plan_path(self):
		order = self._sales_order(30)
		plan = frappe.get_doc(
			{
				"doctype": "Production Plan",
				"company": COMPANY,
				"get_items_from": "Sales Order",
				"posting_date": today(),
				"sales_orders": [{"sales_order": order.name}],
			}
		)
		plan.get_items()
		self.assertEqual([row.bom_no for row in plan.po_items], [self.bom_default])
		for row in plan.po_items:
			row.warehouse = FG
		plan.save()
		self.assertEqual([row.bom_no for row in plan.po_items], [self.bom_cheap])

		materials = {row["item_code"] for row in get_items_for_material_requests(plan.as_dict())}
		self.assertIn(self.raw_cheap, materials)
		self.assertNotIn(self.raw_default, materials)

		plan.submit()
		plan.make_work_order()
		names = frappe.get_all("Work Order", filters={"production_plan": plan.name}, pluck="name")
		self.assertEqual(len(names), 1)
		self._assert_uses_cheap_bom(names[0])

	def _assert_uses_cheap_bom(self, work_order_name):
		work_order = frappe.get_doc("Work Order", work_order_name)
		self.assertEqual(work_order.bom_no, self.bom_cheap)
		self.assertEqual({row.bom for row in work_order.operations}, {self.bom_cheap})
		self.assertEqual({row.item_code for row in work_order.required_items}, {self.raw_cheap})

	def _item(self, code, **values):
		return (
			frappe.get_doc(
				{
					"doctype": "Item",
					"item_code": f"{TEST_PREFIX} BSH {code} {self.suffix}",
					"item_group": "Products",
					"stock_uom": "Nos",
					"is_stock_item": 1,
					"include_item_in_manufacturing": 1,
					"valuation_rate": 1,
					"item_defaults": [{"company": COMPANY, "default_warehouse": STORES}],
					**values,
				}
			)
			.insert()
			.name
		)

	def _bom(self, raw_material, *, hour_rate, is_default, name_hint="ws"):
		workstation = frappe.get_doc(
			{
				"doctype": "Workstation",
				"workstation_name": f"{TEST_PREFIX} BSH {name_hint} {hour_rate} {self.suffix}",
				"hour_rate": hour_rate,
				"production_capacity": 1,
				"working_hours": [{"start_time": "00:00:00", "end_time": "23:59:59"}],
			}
		).insert()
		operation = frappe.get_doc(
			{
				"doctype": "Operation",
				"name": f"{TEST_PREFIX} BSH OP {name_hint} {hour_rate} {self.suffix}",
				"workstation": workstation.name,
			}
		).insert()
		bom = frappe.get_doc(
			{
				"doctype": "BOM",
				"item": self.fg,
				"company": COMPANY,
				"quantity": 1,
				"currency": frappe.db.get_value("Company", COMPANY, "default_currency"),
				"rm_cost_as_per": "Valuation Rate",
				"with_operations": 1,
				"is_default": is_default,
				"items": [{"item_code": raw_material, "qty": 1, "rate": 1}],
				"operations": [
					{
						"operation": operation.name,
						"workstation": workstation.name,
						"time_in_mins": 10,
						"hour_rate": hour_rate,
					}
				],
			}
		).insert()
		bom.submit()
		return bom.name

	def _sales_order(self, qty):
		customer = frappe.get_doc(
			{
				"doctype": "Customer",
				"customer_name": f"{TEST_PREFIX} BSH Customer {qty} {self.suffix}",
				"customer_group": frappe.db.get_value("Customer Group", {"is_group": 0}),
				"territory": frappe.db.get_value("Territory", {"is_group": 0}),
			}
		).insert()
		order = frappe.get_doc(
			{
				"doctype": "Sales Order",
				"company": COMPANY,
				"customer": customer.name,
				"transaction_date": today(),
				"delivery_date": add_days(today(), 10),
				"currency": frappe.db.get_value("Company", COMPANY, "default_currency"),
				"selling_price_list": "Standard Selling",
				"items": [
					{
						"item_code": self.fg,
						"qty": qty,
						"rate": 10,
						"warehouse": FG,
						"delivery_date": add_days(today(), 10),
					}
				],
			}
		).insert()
		order.submit()
		return order
