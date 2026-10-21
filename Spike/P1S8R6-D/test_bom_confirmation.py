"""SL-006 acceptance tests, staged while SL-005 full regression is running."""

from unittest.mock import Mock, patch

import frappe

from frappe_china.tests.utils import FrappeChinaTestCase


class TestBomConfirmation(FrappeChinaTestCase):
	def test_plan_rows_with_any_recorded_source_keep_their_bom(self):
		from frappe_china.production.bom_selection import production_plan_validate

		for source in ("confirmed", "kept", "manual"):
			with self.subTest(source=source):
				row = frappe._dict(item_code="_FCT Item", bom_no="BOM-DEFAULT", cn_bom_source=source)
				doc = frappe._dict(company="_Test Company", po_items=[row])
				with patch(
					"frappe_china.production.bom_selection.select_bom",
					return_value={"auto": True, "bom": "BOM-CHEAP", "candidates": []},
				):
					production_plan_validate(doc)
				self.assertEqual(row.bom_no, "BOM-DEFAULT")

	def test_work_order_sources_keep_choice_and_are_recorded(self):
		from frappe_china.production.bom_selection import work_order_before_insert

		for plan, source, expected in (
			("_FCT Plan", "", "plan"),
			("_FCT Plan", "confirmed", "plan"),
			("_FCT Plan", "kept", "plan"),
			(None, "confirmed", "confirmed"),
			(None, "kept", "kept"),
			(None, "manual", "manual"),
		):
			with self.subTest(source=expected):
				doc = frappe._dict(
					production_item="_FCT Item",
					company="_Test Company",
					bom_no="BOM-DEFAULT",
					production_plan=plan,
					cn_bom_source=source,
					flags=frappe._dict(),
					set_work_order_operations=Mock(),
					set_required_items=Mock(),
				)
				with (
					patch(
						"frappe_china.production.bom_selection.select_bom",
						return_value={"auto": True, "bom": "BOM-CHEAP", "candidates": []},
					),
					patch("frappe_china.production.bom_selection.default_boms", return_value=["BOM-DEFAULT"]),
				):
					work_order_before_insert(doc)
				self.assertEqual(doc.bom_no, "BOM-DEFAULT")
				self.assertEqual(doc.flags.cn_bom_choice["source"], expected)
				doc.set_work_order_operations.assert_not_called()
				doc.set_required_items.assert_not_called()

	def test_empty_source_still_selects_automatically(self):
		from frappe_china.production.bom_selection import work_order_before_insert

		doc = frappe._dict(
			production_item="_FCT Item",
			company="_Test Company",
			bom_no="BOM-DEFAULT",
			flags=frappe._dict(),
			set_work_order_operations=Mock(),
			set_required_items=Mock(),
		)
		with (
			patch(
				"frappe_china.production.bom_selection.select_bom",
				return_value={"auto": True, "bom": "BOM-CHEAP", "candidates": []},
			),
			patch("frappe_china.production.bom_selection.default_boms", return_value=["BOM-DEFAULT"]),
		):
			work_order_before_insert(doc)
		self.assertEqual(doc.bom_no, "BOM-CHEAP")
		self.assertEqual(doc.flags.cn_bom_choice["source"], "auto")
		doc.set_work_order_operations.assert_called_once()
		doc.set_required_items.assert_called_once()

	def test_comment_uses_all_five_source_phrases_and_keeps_candidates(self):
		from frappe_china.production.bom_selection import _format_choice

		candidate = {
			"bom": "BOM-CHEAP",
			"unit_cost": 5,
			"raw_material_cost": 4,
			"operating_cost": 1,
			"quantity": 1,
			"process_loss_percentage": 0,
		}
		for source, expected in (
			("plan", "由生产计划带入"),
			("confirmed", "按成本推荐、人已确认"),
			("kept", "按成本推荐、人选择保留"),
			("manual", "人工指定"),
			("auto", "按成本自动选用"),
		):
			with self.subTest(source=source):
				html = _format_choice(
					{"bom": "BOM-CHEAP", "auto": True, "source": source, "candidates": [candidate]}
				)
				self.assertIn(expected, html)
				self.assertIn("BOM-CHEAP", html)
				self.assertIn("5.000000", html)

	def test_hidden_source_fields_match_frozen_plan(self):
		for doctype in ("Production Plan Item", "Work Order"):
			field = frappe.get_meta(doctype).get_field("cn_bom_source")
			self.assertIsNotNone(field)
			self.assertEqual(field.fieldtype, "Select")
			self.assertEqual(field.options, "\nconfirmed\nkept\nmanual")
			self.assertEqual((field.read_only, field.hidden), (1, 1))
