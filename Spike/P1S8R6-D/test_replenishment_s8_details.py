"""SL-007 ④⑤: scope, company cache, outcome details and untouched counters."""
from datetime import date
from unittest.mock import patch

import frappe

from frappe_china.replenishment import demand, rules, safety_stock, suggestion
from frappe_china.tests.utils import FrappeChinaTestCase


class TestS8ReplenishmentDetails(FrappeChinaTestCase):
    def setUp(self):
        super().setUp()
        frappe.local.cn_wip_warehouses = {}
        self.addCleanup(lambda: setattr(frappe.local, "cn_wip_warehouses", {}))
        self.day = date(2026, 10, 15)

    def test_wip_union_is_cached_by_company_and_uses_submitted_orders(self):
        def get_all(doctype, **kwargs):
            if doctype == "Company":
                return ["DEFAULT"]
            self.assertEqual(doctype, "Work Order")
            self.assertEqual(kwargs["filters"]["docstatus"], 1)
            self.assertEqual(kwargs["filters"]["company"], "CO")
            return ["DEFAULT", "CUSTOM", None, ""]
        with patch("frappe.get_all", side_effect=get_all) as query:
            self.assertEqual(demand.wip_warehouses("CO"), {"DEFAULT", "CUSTOM"})
            self.assertEqual(demand.wip_warehouses("CO"), {"DEFAULT", "CUSTOM"})
            self.assertEqual(query.call_count, 2)
        with patch("frappe.get_all", return_value=["OTHER"]) as query:
            self.assertEqual(demand.wip_warehouses("OTHER CO"), {"OTHER"})
            self.assertEqual(query.call_count, 2)

    def test_safety_union_expands_reorder_rows_and_filters_other_companies(self):
        row1 = frappe._dict(warehouse="RAW", warehouse_group="GROUP")
        row2 = frappe._dict(warehouse="RAW")
        def get_all(doctype, **kwargs):
            if doctype == "Item":
                return ["WIRE"]
            if doctype == "Item Reorder":
                return [row1, row2]
            self.fail(f"unexpected query: {doctype}")
        with (
            patch("frappe.get_all", side_effect=get_all),
            patch.object(safety_stock, "_company_warehouses", return_value=["RAW", "RAW2", "WIP"]),
            patch.object(safety_stock, "_enabled_companies", return_value=[]),
            patch.object(safety_stock, "warehouses_of_row", side_effect=[["RAW", "RAW2", "FOREIGN"], ["RAW"]]),
            patch.object(safety_stock, "wip_warehouses", return_value={"WIP"}),
            patch.object(safety_stock, "daily_demand", return_value={"WIRE": [0]*89+[9]}) as history,
            patch.object(safety_stock, "get_item_params", return_value={"lead_time_days": 7, "service_level": 95}),
            patch.object(safety_stock, "_precision", return_value=6),
            patch("frappe.db.get_value", return_value=2),
            patch("frappe.db.set_value"),
        ):
            result = safety_stock.compute_safety_stock("CO", self.day)
        self.assertEqual(set(history.call_args.args[1]), {"RAW", "RAW2"})
        self.assertEqual(history.call_args.args[3], "CO")
        self.assertEqual(result["changes"][0], {
            "item_code": "WIRE", "warehouse": None, "field": "safety_stock",
            "old": 2.0, "new": 4.12855, "outcome": "updated",
            "reason": result["changes"][0]["reason"],
        })
        self.assertTrue(result["changes"][0]["reason"])

    def test_three_rules_explain_untriggered_conditions(self):
        row = frappe._dict(parent="WIRE", warehouse="RAW", warehouse_reorder_level=20)
        params = {"review_days": 7, "review_start": date(2026, 10, 1), "lead_time_days": 3}
        changes = []
        with (patch.object(rules, "_reorder_rows", return_value=[row]),
              patch.object(rules, "warehouses_of_row", return_value=["RAW"]),
              patch.object(rules, "projected_qty", return_value=(30, {})),
              patch.object(rules, "get_item_params", return_value=params)):
            self.assertEqual(rules.eoq_proposals("CO", self.day, [], changes), [])
            self.assertEqual(rules.periodic_proposals("CO", date(2026, 10, 14), [], changes), [])
            with patch.object(rules, "daily_demand", return_value={"WIRE": [1]*90}), patch("frappe.db.get_value", return_value=0):
                self.assertEqual(rules.periodic_proposals("CO", self.day, [], changes), [])
            with patch.object(rules, "_sales_order_rows", return_value=[]):
                self.assertEqual(rules.order_proposals("CO", self.day, [], changes), [])
        self.assertEqual(len(changes), 4)
        self.assertEqual({row["outcome"] for row in changes}, {"not_triggered"})
        self.assertTrue(all(row["field"] == "suggested_qty" and row["item_code"] == "WIRE" for row in changes))
        self.assertIn("30", changes[0]["reason"])
        self.assertIn("20", changes[0]["reason"])
        self.assertIn("非盘点日", changes[1]["reason"])
        self.assertIn("10", changes[2]["reason"])
        self.assertIn("无净缺料", changes[3]["reason"])

    def test_upsert_records_created_updated_and_unchanged_quantities(self):
        from unittest.mock import Mock
        proposal = {"item_code": "WIRE", "warehouse": "RAW", "rule": "EOQ", "qty": 12}
        for current, qty, expected, old in ((False, None, "created", None), (True, 9, "updated", 9), (True, 12, "unchanged", 12)):
            with self.subTest(expected=expected):
                changes = []
                doc = Mock(name="RS", suggested_qty=qty)
                doc.name = "RS"
                with patch("frappe.db.get_value", return_value="RS" if current else None), patch("frappe.get_doc", return_value=doc):
                    suggestion.upsert("CO", self.day, proposal, changes)
                change = changes[0]
                self.assertEqual((change["field"], change["old"], change["new"], change["outcome"]), ("suggested_qty", old, 12, expected))
                self.assertTrue(change["reason"])

    def test_daily_keeps_changes_on_every_step_and_reports_skipped_writes(self):
        from frappe_china.replenishment.daily import run_daily
        safety = {"step": "safety_stock", "processed": 1, "skipped": 0, "problems": [], "changes": []}
        reorder = {"step": "reorder_level", "processed": 1, "skipped": 0, "problems": [], "changes": []}
        proposal = {"item_code": "WIRE", "warehouse": "RAW", "rule": "EOQ", "qty": 12}
        not_triggered = {"item_code": "SPRING", "warehouse": "FG", "field": "suggested_qty", "old": None, "new": None, "outcome": "not_triggered", "reason": "无净缺料"}
        def periodic(company, day, problems, changes):
            changes.append(not_triggered)
            return []
        for failure in (False, True):
            with self.subTest(failure=failure):
                def upsert(company, day, proposal, changes):
                    if failure:
                        raise ValueError("write failed")
                    changes.append({"item_code": "WIRE", "warehouse": "RAW", "field": "suggested_qty", "old": None, "new": 12, "outcome": "created", "reason": "EOQ"})
                    return "RS"
                with (patch("frappe_china.replenishment.daily.compute_safety_stock", return_value=safety),
                      patch("frappe_china.replenishment.daily.compute_reorder_levels", return_value=reorder),
                      patch("frappe_china.replenishment.daily.eoq_proposals", return_value=[proposal]),
                      patch("frappe_china.replenishment.daily.periodic_proposals", side_effect=periodic),
                      patch("frappe_china.replenishment.daily.order_proposals", return_value=[]),
                      patch("frappe_china.replenishment.daily.upsert", side_effect=upsert),
                      patch("frappe.log_error")):
                    result = run_daily(self.day, "CO")
                steps = result["companies"]["CO"]
                self.assertTrue(all("changes" in step for step in steps))
                suggestions = steps[2]
                self.assertEqual((suggestions["processed"], suggestions["skipped"]), (0, 1) if failure else (1, 0))
                self.assertIn(not_triggered, suggestions["changes"])
                row = next(row for row in suggestions["changes"] if row["item_code"] == "WIRE")
                self.assertEqual(row["outcome"], "skipped" if failure else "created")
                self.assertEqual(result["ok"], not failure)
