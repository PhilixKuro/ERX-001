"""P1-S8-R8 F 片1 探针：不连库，只用 mock 复算 normalize_fallback_operating_cost
在「同一工单两张部分完工入库」与「部分工序已报工」两种情形下的金额。
上游 fallback 公式照 erpnext bom.py:1844-1858 与 stock_entry.py:4494-4523 手写。"""
from types import SimpleNamespace as NS
from unittest.mock import patch

import frappe
from frappe_china.accounting import stock_entry_accounts as sea


def upstream_fallback(ops, wo_qty, fg_qty, consumed):
    # stock_entry.get_remaining_operating_cost：已报工工序取「实际总额−已消耗」（总额），
    # 未报工工序取「计划额÷工单数量」（单位额）；bom.add_operations_cost 再 × fg_completed_qty
    remaining = 0.0
    for op in ops:
        if op["completed_qty"]:
            remaining += op["actual"] - consumed.get(op["name"], 0)
        else:
            remaining += op["planned"] / wo_qty
    return remaining * fg_qty


def run(ops, wo_qty, fg_qty, consumed):
    amount = upstream_fallback(ops, wo_qty, fg_qty, consumed)
    row = NS(has_operating_cost=1, operation_id=None, operating_component=None, amount=amount, base_amount=amount)
    doc = NS(purpose="Manufacture", work_order="WO", fg_completed_qty=fg_qty)
    doc.get = lambda key: {"work_order": "WO", "additional_costs": [row]}.get(key)
    wo = NS(qty=wo_qty, operations=[NS(actual_operating_cost=o["actual"], planned_operating_cost=o["planned"]) for o in ops])
    wo.get = lambda key: wo.operations if key == "operations" else None
    def _flt(v, precision=None):
        v = float(v or 0)
        return round(v, precision) if precision is not None else v

    with patch.object(frappe, "get_cached_doc", return_value=wo), patch.object(frappe, "get_precision", return_value=2), patch.object(sea, "flt", _flt):
        sea.normalize_fallback_operating_cost(doc)
        first = row.amount
        sea.normalize_fallback_operating_cost(doc)  # submit 时再跑一次
    return amount, first, row.amount


ops_done = [{"name": "op1", "completed_qty": 1000, "actual": 100.0, "planned": 100.0}]
print("case A 单张全量入库 1000/1000:", run(ops_done, 1000, 1000, {}))
print("case B1 第一张部分入库 500/1000:", run(ops_done, 1000, 500, {}))
print("case B2 第二张部分入库 500/1000（fallback 行无 operation_id，consumed 恒为 0）:", run(ops_done, 1000, 500, {}), "应记 50")
ops_mixed = [
    {"name": "op1", "completed_qty": 1000, "actual": 100.0, "planned": 100.0},
    {"name": "op2", "completed_qty": 0, "actual": 0.0, "planned": 60.0},
]
print("case C 一道已报工、一道未报工 1000/1000:", run(ops_mixed, 1000, 1000, {}), "应记 160")

# 现实的分批完工：工单 1000，先报工 500（实际工序成本 50）入库 500；再报工 500（累计 100）入库 500。
# 上游 check_if_operations_completed（stock_entry.py:1168-1185）只要求已报工数 ≥ 本次+已入库，两张都放行。
first = run([{"name": "op1", "completed_qty": 500, "actual": 50.0, "planned": 100.0}], 1000, 500, {})
second = run([{"name": "op1", "completed_qty": 1000, "actual": 100.0, "planned": 100.0}], 1000, 500, {})
print("case D 分批完工：第一张", first, "第二张", second, "合计", first[2] + second[2], "实际工序成本 100")
