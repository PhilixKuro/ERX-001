"""365 daily calculations with real dated stock issues, always rolled back."""
import json
import time
from datetime import timedelta
from pathlib import Path

import frappe
from frappe.utils import getdate, today
from frappe_china.replenishment.daily import run_daily

assert frappe.local.site == "test.localhost"
company = "_Test Company"
prefix = "_FCT S7 Replay " + frappe.generate_hash(length=8)
start = getdate(today()) - timedelta(days=364)
warehouses = ("Stores - _TC", "Finished Goods - _TC")
error_names = []
setting_fields = ["cn_replenishment_enabled", "cn_order_cost", "cn_holding_rate", "cn_review_days", "cn_review_start_date", "cn_service_level"]
settings_before = frappe.db.get_value("Company", company, setting_fields, as_dict=True)
ledger_before = frappe.db.count("Stock Ledger Entry", {"company": company})
errors_before = set(frappe.get_all("Error Log", filters={"method": ["like", "%Daily replenishment%"]}, pluck="name"))
result = {"days": 0, "items": 30, "warehouse_rows": 60, "rules_enabled": 3, "total_seconds": 0, "max_day_seconds": 0, "ok": False}
try:
    for year in {start.year, getdate(today()).year}:
        if not frappe.db.exists("Fiscal Year", str(year)):
            frappe.get_doc({"doctype": "Fiscal Year", "year": str(year), "year_start_date": f"{year}-01-01",
                            "year_end_date": f"{year}-12-31"}).insert()
    frappe.db.set_value("Company", company, {"cn_replenishment_enabled": 1, "cn_order_cost": 20,
        "cn_holding_rate": 20, "cn_review_days": 30, "cn_review_start_date": start, "cn_service_level": 95})
    items = []
    for index in range(30):
        item = frappe.get_doc({"doctype": "Item", "item_code": f"{prefix} {index:02d}", "item_group": "Products",
            "stock_uom": "Nos", "is_stock_item": 1, "valuation_rate": 2, "lead_time_days": 7,
            "cn_auto_replenishment_params": 1, "cn_rule_eoq": 1, "cn_rule_periodic": 1, "cn_rule_order": 1})
        for warehouse in warehouses:
            item.append("reorder_levels", {"warehouse": warehouse, "warehouse_reorder_level": 5, "warehouse_reorder_qty": 1,
                                          "material_request_type": "Purchase"})
        item.insert()
        items.append(item.name)
    receipt = frappe.get_doc({"doctype": "Stock Entry", "company": company, "stock_entry_type": "Material Receipt",
                             "set_posting_time": 1, "posting_date": start, "posting_time": "08:00:00"})
    for item in items:
        for warehouse in warehouses:
            receipt.append("items", {"item_code": item, "qty": 10, "t_warehouse": warehouse, "basic_rate": 2})
    receipt.insert().submit()
    opening_rows = frappe.db.count("Stock Ledger Entry", {"item_code": ["in", items]})
    durations = []
    for day in range(365):
        date = start + timedelta(days=day)
        issue = frappe.get_doc({"doctype": "Stock Entry", "company": company, "stock_entry_type": "Material Issue",
                               "set_posting_time": 1, "posting_date": date, "posting_time": "09:00:00"})
        issue.append("items", {"item_code": items[day % 30], "qty": 1, "s_warehouse": warehouses[(day // 30) % 2]})
        issue.insert().submit()
        before = time.perf_counter()
        output = run_daily(date, company)
        duration = time.perf_counter() - before
        if not output["ok"]:
            raise RuntimeError(json.dumps(output, ensure_ascii=False, default=str))
        durations.append(duration)
        if (day + 1) % 30 == 0:
            print(json.dumps({"day": day+1, "calculation_seconds": sum(durations), "max_seconds": max(durations)}), flush=True)
    ledger_rows = frappe.db.count("Stock Ledger Entry", {"item_code": ["in", items]})
    expected_rows = opening_rows + 365
    assert ledger_rows == expected_rows, (ledger_rows, expected_rows)
    result.update(days=365, total_seconds=sum(durations), max_day_seconds=max(durations), ledger_rows=ledger_rows, ok=True)
finally:
    # Error Log is nontransactional: only exact records whose message contains this unique prefix.
    error_names = [name for name in frappe.get_all("Error Log", filters={"method": ["like", "%Daily replenishment%"]}, pluck="name") if name not in errors_before]
    frappe.db.rollback()
    for name in error_names:
        frappe.delete_doc("Error Log", name, ignore_permissions=True)
    result["error_logs_removed"] = error_names
    result["rolled_back_item_count"] = frappe.db.count("Item", {"item_code": ["like", prefix + "%"]})
    result["settings_restored"] = settings_before == frappe.db.get_value("Company", company, setting_fields, as_dict=True)
    result["ledger_restored"] = ledger_before == frappe.db.count("Stock Ledger Entry", {"company": company})
    Path("/workspace/Spike/P1S7R5-D/ts017-replay-result.json").write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False), flush=True)
    assert result["rolled_back_item_count"] == 0 and result["settings_restored"] and result["ledger_restored"]
