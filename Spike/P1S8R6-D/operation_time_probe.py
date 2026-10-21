"""HT-007 rollback probe: exercise real Job Card insert lifecycle on test.localhost."""
import json
import runpy
from pathlib import Path
from unittest.mock import patch

import frappe
from frappe.utils import add_to_date, flt, get_datetime

frappe.init(site="test.localhost", sites_path="/workspace/frappe-bench/sites")
frappe.connect()
try:
    assert frappe.local.site == "test.localhost"
    frappe.set_user("Administrator")
    frappe.local.lang = "zh"
    from erpnext.manufacturing.doctype.job_card.job_card import JobCard

    fixture_class = runpy.run_path("/workspace/Spike/P1S8R6-D/test_operation_time.py")["TestOperationTime"]
    fixture = fixture_class(methodName="runTest")
    fixture.setUp()
    try:
        frappe.db.set_single_value("Manufacturing Settings", "disable_capacity_planning", 0)
        frappe.db.set_single_value("Manufacturing Settings", "allow_overtime", 1)
        wo = fixture._work_order()
        # Inject the approved BOM-quantity times for the scheduling-only experiment.
        for row, minutes in zip(wo.operations, (250, 90, 180), strict=True):
            row.time_in_mins = minutes
        wo.save()
        observations = []

        def trim_on_insert(card):
            qty = flt(frappe.db.get_value("Work Order", card.work_order, "qty"))
            minutes = flt(frappe.db.get_value("Work Order Operation", card.operation_id, "time_in_mins"))
            want = minutes / qty * card.for_quantity
            before = sum(flt(row.time_in_mins) for row in card.scheduled_time_logs)
            if before > want + 1e-6:
                remaining, kept = want, []
                for row in card.scheduled_time_logs:
                    if remaining <= 0:
                        break
                    duration = flt(row.time_in_mins)
                    if duration > remaining:
                        row.time_in_mins = remaining
                        row.to_time = add_to_date(row.from_time, minutes=remaining)
                        duration = remaining
                    kept.append(row)
                    remaining -= duration
                card.set("scheduled_time_logs", kept)
                card.time_required = want
            observations.append({"quantity": card.for_quantity, "before": before, "want": want,
                                 "after": sum(flt(row.time_in_mins) for row in card.scheduled_time_logs)})

        with patch.object(JobCard, "before_insert", trim_on_insert, create=True):
            wo.submit()
        cards = fixture._cards(wo)
        assert [card.time_required for card in cards] == [100, 100, 50]
        assert all(sum(row.time_in_mins for row in card.scheduled_time_logs) == card.time_required for card in cards)
        assert all(get_datetime(following.expected_start_date) >= get_datetime(previous.expected_end_date)
                   for previous, following in zip(cards, cards[1:]))
        result = {"site": frappe.local.site, "observations": observations,
                  "cards": [{"quantity": card.for_quantity, "minutes": card.time_required,
                             "start": str(card.expected_start_date), "end": str(card.expected_end_date)} for card in cards],
                  "ht007": "go", "committed": False}
        Path("/workspace/frappe-bench/logs/s8-operation-time-probe.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(result, ensure_ascii=False))
    finally:
        fixture.tearDown()
        fixture.doCleanups()
finally:
    frappe.db.rollback()
    frappe.destroy()
