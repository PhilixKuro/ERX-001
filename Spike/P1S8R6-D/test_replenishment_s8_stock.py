"""SL-007 ①～④: six issues count once; constants are hand calculations."""
from datetime import timedelta

import frappe
from erpnext.manufacturing.doctype.work_order.work_order import make_stock_entry
from erpnext.stock.doctype.stock_entry.stock_entry_utils import make_stock_entry as stock_entry
from frappe.utils import getdate, today

from frappe_china.replenishment.demand import daily_demand
from frappe_china.replenishment.reorder_level import compute_reorder_levels
from frappe_china.replenishment.safety_stock import compute_safety_stock
from frappe_china.tests.utils import TEST_PREFIX, FrappeChinaTestCase


class TestS8ReplenishmentStock(FrappeChinaTestCase):
    def setUp(self):
        super().setUp()
        frappe.local.cn_wip_warehouses = {}
        self.addCleanup(lambda: setattr(frappe.local, "cn_wip_warehouses", {}))
        self.day = getdate(today()) - timedelta(days=2)
        self.company = "_Test Company"
        self.stores = "Stores - _TC"
        self.wip = "Work In Progress - _TC"
        self.fg_wh = "Finished Goods - _TC"
        self.suffix = frappe.generate_hash(length=7)
        self.raw = self.item("Wire", cn_auto_replenishment_params=1, lead_time_days=7, cn_service_level=95)
        self.finished = self.item("Spring")
        frappe.db.set_value("Company", self.company, {"cn_replenishment_enabled": 1, "default_wip_warehouse": self.wip})
        self.raw.append("reorder_levels", {"warehouse": self.stores, "warehouse_reorder_level": 0})
        self.raw.save()
        self.bom = frappe.get_doc({
            "doctype": "BOM", "company": self.company, "item": self.finished.name,
            "quantity": 1, "currency": frappe.db.get_value("Company", self.company, "default_currency"),
            "items": [{"item_code": self.raw.name, "qty": 1, "rate": 10}],
        }).insert()
        self.bom.submit()
        stock_entry(item_code=self.raw.name, qty=500, to_warehouse=self.stores, rate=10,
                    company=self.company, posting_date=self.day-timedelta(days=89))

    def item(self, label, **values):
        return frappe.get_doc({
            "doctype": "Item", "item_code": f"{TEST_PREFIX} S8 Demand {label} {self.suffix}",
            "item_group": "Products", "stock_uom": "Nos", "is_stock_item": 1,
            "include_item_in_manufacturing": 1, "valuation_rate": 10, **values,
        }).insert()

    def work_order(self, qty, *, skip_transfer=0):
        wo = frappe.get_doc({
            "doctype": "Work Order", "company": self.company, "production_item": self.finished.name,
            "bom_no": self.bom.name, "qty": qty, "source_warehouse": self.stores,
            "wip_warehouse": self.wip, "fg_warehouse": self.fg_wh,
            "skip_transfer": skip_transfer, "reserve_stock": 0,
        })
        wo.get_items_and_operations_from_bom()
        wo.insert()
        wo.submit()
        return wo

    def movement(self, wo, purpose, qty, day):
        doc = frappe.get_doc(make_stock_entry(wo.name, purpose, qty))
        doc.set_posting_time = 1
        doc.posting_date = day
        doc.posting_time = "12:00:00" if purpose == "Manufacture" else "08:00:00"
        doc.insert()
        doc.submit()
        return doc

    def test_six_transfers_are_raw_demand_and_finished_wip_consumption_is_not_counted_twice(self):
        for index, qty in enumerate((6, 12, 18, 24, 30, 36)):
            day = self.day - timedelta(days=60-index*10)
            wo = self.work_order(qty)
            self.movement(wo, "Material Transfer for Manufacture", qty, day)
            self.movement(wo, "Manufacture", qty, day)
        stock_entry(item_code=self.raw.name, qty=50, from_warehouse=self.stores,
                    to_warehouse=self.fg_wh, company=self.company, posting_date=self.day)
        series = daily_demand([self.raw.name], [self.stores, self.wip, self.fg_wh], self.day, self.company)[self.raw.name]
        self.assertEqual([qty for qty in series if qty], [6, 12, 18, 24, 30, 36])
        self.assertEqual(sum(series), 126)
        self.assertEqual(sum(daily_demand([self.raw.name], [self.wip], self.day, self.company)[self.raw.name]), 0)
        self.assertEqual(series, daily_demand([self.raw.name], [self.stores], self.day, self.company)[self.raw.name])
        # 90 days: sum=126, sum of squares=3276, sample variance=(3276-126²/90)/89.
        # 95% Z=1.64485362695147, LT=7 => safety=25.68231093075; mean*7=9.8.
        safety = compute_safety_stock(self.company, self.day)
        reorder = compute_reorder_levels(self.company, self.day)
        self.assertFalse([p for result in (safety, reorder) for p in result["problems"] if self.raw.name in p])
        actual_safety = frappe.db.get_value("Item", self.raw.name, "safety_stock")
        level = frappe.db.get_value("Item Reorder", self.raw.reorder_levels[0].name, "warehouse_reorder_level")
        self.assertAlmostEqual(actual_safety, 25.682311, places=6)
        self.assertAlmostEqual(level, 35.482311, places=6)
        self.assertGreater(level, actual_safety)
        self.assertGreater(actual_safety, 0)

    def test_skip_transfer_counts_manufacture_from_raw_warehouse(self):
        wo = self.work_order(12, skip_transfer=1)
        self.movement(wo, "Manufacture", 12, self.day)
        series = daily_demand([self.raw.name], [self.stores, self.wip], self.day, self.company)[self.raw.name]
        self.assertEqual(series[-1], 12)
        self.assertEqual(sum(series), 12)

    def test_without_reorder_rows_safety_uses_non_wip_warehouses_only(self):
        self.raw.set("reorder_levels", [])
        self.raw.save()
        stock_entry(item_code=self.raw.name, qty=100, to_warehouse=self.wip, rate=10,
                    company=self.company, posting_date=self.day-timedelta(days=2))
        stock_entry(item_code=self.raw.name, qty=9, from_warehouse=self.stores,
                    company=self.company, posting_date=self.day)
        stock_entry(item_code=self.raw.name, qty=70, from_warehouse=self.wip,
                    company=self.company, posting_date=self.day)
        result = compute_safety_stock(self.company, self.day)
        self.assertFalse([p for p in result["problems"] if self.raw.name in p])
        # One raw day=9, 89 zeros; sigma=9/sqrt(90), LT=7. WIP's 70 must not inflate it.
        self.assertAlmostEqual(frappe.db.get_value("Item", self.raw.name, "safety_stock"), 4.128550, places=6)
