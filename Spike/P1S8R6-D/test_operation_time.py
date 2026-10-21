"""SL-005: BOM quantity is the operation-time basis on every creation path."""

import json
from unittest.mock import Mock, patch

import frappe
from frappe.utils import get_datetime, today

from frappe_china.tests.utils import TEST_PREFIX, FrappeChinaTestCase


class TestOperationTime(FrappeChinaTestCase):
    def setUp(self):
        super().setUp()
        self.settings = {
            field: frappe.db.get_single_value("Manufacturing Settings", field)
            for field in ("disable_capacity_planning", "allow_overtime")
        }
        frappe.db.set_single_value(
            "Manufacturing Settings", "disable_capacity_planning", 1
        )
        self.suffix = frappe.generate_hash(length=8)
        self.fg = self._item("FG")
        material = self._item("RM")
        self.bom = frappe.get_doc(
            {
                "doctype": "BOM",
                "item": self.fg,
                "company": "_Test Company",
                "quantity": 1000,
                "currency": frappe.db.get_value(
                    "Company", "_Test Company", "default_currency"
                ),
                "with_operations": 1,
                "items": [
                    {"item_code": material, "qty": 1, "uom": "Nos", "stock_uom": "Nos"}
                ],
            }
        )
        for index, (label, minutes) in enumerate(
            (("Coiling", 50), ("Temper", 18), ("Grinding", 36))
        ):
            station = frappe.get_doc(
                {
                    "doctype": "Workstation",
                    "workstation_name": f"{TEST_PREFIX} Time {label} {self.suffix}",
                    "production_capacity": 1,
                }
            ).insert()
            operation = frappe.get_doc(
                {
                    "doctype": "Operation",
                    "name": f"{TEST_PREFIX} Time {label} {self.suffix}",
                    "workstation": station.name,
                    "create_job_card_based_on_batch_size": int(index == 0),
                    "batch_size": 2500 if index == 0 else 1,
                }
            ).insert()
            self.bom.append(
                "operations",
                {
                    "operation": operation.name,
                    "workstation": station.name,
                    "time_in_mins": minutes,
                    "batch_size": 2500 if index == 0 else 1,
                    "cn_job_card_split_qty": 2000 if index == 0 else 0,
                },
            )
        self.bom.insert()
        self.bom.submit()

    def tearDown(self):
        try:
            for field, value in self.settings.items():
                frappe.db.set_single_value("Manufacturing Settings", field, value)
        finally:
            super().tearDown()

    def _item(self, label):
        return (
            frappe.get_doc(
                {
                    "doctype": "Item",
                    "item_code": f"{TEST_PREFIX} Time {label} {self.suffix}",
                    "item_group": "Products",
                    "stock_uom": "Nos",
                    "is_stock_item": 1,
                    "include_item_in_manufacturing": 1,
                }
            )
            .insert()
            .name
        )

    def _work_order(self):
        wo = frappe.get_doc(
            {
                "doctype": "Work Order",
                "company": "_Test Company",
                "production_item": self.fg,
                "bom_no": self.bom.name,
                "qty": 5000,
                "stock_uom": "Nos",
                "source_warehouse": "Stores - _TC",
                "fg_warehouse": "Finished Goods - _TC",
                "wip_warehouse": "Work In Progress - _TC",
                "skip_transfer": 1,
                "reserve_stock": 0,
                "planned_start_date": f"{today()} 08:00:00",
            }
        )
        wo.get_items_and_operations_from_bom()
        return wo.insert()

    def _assert_times(self, wo):
        wo.reload()
        self.assertEqual([row.time_in_mins for row in wo.operations], [250, 90, 180])
        self.assertEqual(wo.operations[0].batch_size, 2500)

    def _sales_order(self):
        from frappe_china.tests.test_bom_selection_hooks import TestBomSelectionHooks

        return TestBomSelectionHooks._sales_order(self, 5000)

    def _cards(self, wo):
        return [
            frappe.get_doc("Job Card", name)
            for name in frappe.get_all(
                "Job Card",
                filters={
                    "work_order": wo.name,
                    "operation": self.bom.operations[0].operation,
                },
                pluck="name",
                order_by="creation, name",
            )
        ]

    def test_form_save_recomputes_and_does_not_compound_on_resave(self):
        wo = self._work_order()
        self._assert_times(wo)
        wo.save()
        self._assert_times(wo)

    def test_sales_order_creation_uses_bom_quantity(self):
        from erpnext.selling.doctype.sales_order.sales_order import make_work_orders

        order = self._sales_order()
        names = make_work_orders(
            json.dumps(
                {
                    "items": [
                        {
                            "item_code": self.fg,
                            "bom": self.bom.name,
                            "pending_qty": 5000,
                            "sales_order_item": order.items[0].name,
                            "warehouse": "Finished Goods - _TC",
                            "description": self.fg,
                        }
                    ]
                }
            ),
            order.name,
            "_Test Company",
        )
        self.assertEqual(len(names), 1)
        self._assert_times(frappe.get_doc("Work Order", names[0]))

    def test_production_plan_creation_uses_bom_quantity(self):
        order = self._sales_order()
        plan = frappe.get_doc(
            {
                "doctype": "Production Plan",
                "company": "_Test Company",
                "get_items_from": "Sales Order",
                "posting_date": today(),
                "sales_orders": [{"sales_order": order.name}],
            }
        )
        plan.get_items()
        for row in plan.po_items:
            row.warehouse = "Finished Goods - _TC"
        plan.insert()
        plan.submit()
        plan.make_work_order()
        names = frappe.get_all(
            "Work Order", filters={"production_plan": plan.name}, pluck="name"
        )
        self.assertEqual(len(names), 1)
        self._assert_times(frappe.get_doc("Work Order", names[0]))

    def test_split_cards_without_capacity_planning(self):
        wo = self._work_order()
        wo.submit()
        cards = self._cards(wo)
        self.assertEqual([card.for_quantity for card in cards], [2000, 2000, 1000])
        self.assertEqual([card.time_required for card in cards], [100, 100, 50])

    def test_capacity_schedules_and_report_use_each_card_quantity(self):
        from frappe_china.production_plus.report.capacity_load.capacity_load import (
            execute,
        )

        frappe.db.set_single_value(
            "Manufacturing Settings", "disable_capacity_planning", 0
        )
        frappe.db.set_single_value("Manufacturing Settings", "allow_overtime", 1)
        wo = self._work_order()
        wo.submit()
        cards = self._cards(wo)
        self.assertEqual([card.time_required for card in cards], [100, 100, 50])
        for card in cards:
            self.assertAlmostEqual(
                sum(row.time_in_mins for row in card.scheduled_time_logs),
                card.time_required,
            )
        for previous, following in zip(cards, cards[1:]):
            self.assertGreaterEqual(
                get_datetime(following.expected_start_date),
                get_datetime(previous.expected_end_date),
            )
        _, data, _, _ = execute(
            {
                "company": wo.company,
                "from_date": today(),
                "to_date": today(),
                "bucket": "Week",
                "workstations": [self.bom.operations[0].workstation],
            }
        )
        self.assertAlmostEqual(sum(row["demand_hours"] for row in data), 250 / 60)

    def test_fixed_and_other_bom_rows_are_preserved_and_occurrences_match(self):
        from frappe_china.production.operation_time import work_order_operation_time

        rows = [
            frappe._dict(
                bom=self.bom.name, operation="Cut", time_in_mins=999, fixed_time=1
            ),
            frappe._dict(bom="Other BOM", operation="Cut", time_in_mins=777),
            frappe._dict(bom=self.bom.name, operation="Cut", time_in_mins=888),
        ]
        doc = frappe._dict(
            docstatus=0,
            bom_no=self.bom.name,
            qty=5000,
            operations=rows,
            calculate_operating_cost=Mock(),
        )
        ops = [
            frappe._dict(operation="Cut", time_in_mins=10, fixed_time=1),
            frappe._dict(operation="Cut", time_in_mins=18),
        ]
        with patch(
            "frappe_china.production.operation_time.frappe.get_all", return_value=ops
        ):
            work_order_operation_time(doc)
        self.assertEqual([row.time_in_mins for row in rows], [999, 777, 90])
        doc.calculate_operating_cost.assert_called_once()

    def test_schedule_trim_keeps_prefix_across_working_time_gaps(self):
        from frappe_china.production.operation_time import job_card_scheduled_time

        wo = self._work_order()
        card = frappe.get_doc(
            {
                "doctype": "Job Card",
                "work_order": wo.name,
                "operation_id": wo.operations[0].name,
                "for_quantity": 2000,
                "time_required": 250,
                "scheduled_time_logs": [
                    {
                        "from_time": f"{today()} 08:00:00",
                        "to_time": f"{today()} 09:00:00",
                        "time_in_mins": 60,
                    },
                    {
                        "from_time": f"{today()} 13:00:00",
                        "to_time": f"{today()} 15:00:00",
                        "time_in_mins": 120,
                    },
                    {
                        "from_time": f"{today()} 16:00:00",
                        "to_time": f"{today()} 17:10:00",
                        "time_in_mins": 70,
                    },
                ],
            }
        )
        job_card_scheduled_time(card)
        self.assertEqual(card.time_required, 100)
        self.assertEqual(
            [row.time_in_mins for row in card.scheduled_time_logs], [60, 40]
        )
        self.assertEqual(
            get_datetime(card.scheduled_time_logs[-1].to_time),
            get_datetime(f"{today()} 13:40:00"),
        )
        before = card.as_dict()
        job_card_scheduled_time(card)
        self.assertEqual(card.as_dict(), before)

    def test_bom_grid_metadata_contains_required_columns(self):
        meta = frappe.get_meta("BOM Operation")
        for name in (
            "operation",
            "workstation",
            "time_in_mins",
            "cn_process_loss_percentage",
        ):
            self.assertEqual(meta.get_field(name).in_list_view, 1, name)

    def test_unmapped_operation_keeps_time_and_reports_failure(self):
        from frappe_china.production.operation_time import work_order_operation_time

        row = frappe._dict(bom=self.bom.name, operation="Missing", time_in_mins=777)
        doc = frappe._dict(
            docstatus=0,
            bom_no=self.bom.name,
            qty=5000,
            operations=[row],
            calculate_operating_cost=Mock(),
        )
        with (
            patch(
                "frappe_china.production.operation_time.frappe.log_error"
            ) as log_error,
        ):
            work_order_operation_time(doc)
        self.assertEqual(row.time_in_mins, 777)
        log_error.assert_called_once()
        doc.calculate_operating_cost.assert_not_called()

    def test_submitted_work_order_and_short_or_absent_schedule_stay_unchanged(self):
        from frappe_china.production.operation_time import (
            job_card_scheduled_time,
            work_order_operation_time,
        )

        wo = self._work_order()
        with patch("frappe_china.production.operation_time.frappe.get_all") as get_all:
            wo.docstatus = 1
            work_order_operation_time(wo)
        get_all.assert_not_called()
        card = frappe.get_doc(
            {
                "doctype": "Job Card",
                "work_order": wo.name,
                "operation_id": wo.operations[0].name,
                "for_quantity": 2000,
                "time_required": 80,
                "scheduled_time_logs": [
                    {
                        "from_time": f"{today()} 08:00:00",
                        "to_time": f"{today()} 09:20:00",
                        "time_in_mins": 80,
                    }
                ],
            }
        )
        before = card.as_dict()
        job_card_scheduled_time(card)
        self.assertEqual(card.as_dict(), before)
        card.set("scheduled_time_logs", [])
        with patch(
            "frappe_china.production.operation_time.frappe.db.get_value"
        ) as get_value:
            job_card_scheduled_time(card)
        get_value.assert_not_called()
