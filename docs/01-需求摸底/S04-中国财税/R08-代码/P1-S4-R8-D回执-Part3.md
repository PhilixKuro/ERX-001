# D回执（对象：代码 / 依据：P1-S4-R7-C开发方案-Part3）

**轮次**：P1-S4-R8｜**日期**：2026-09-30｜**步骤**：`plannedDev` D（build）
**依据**：[开发方案总纲](../R07-开发方案/P1-S4-R7-C开发方案-总纲.md)＋[Part3](../R07-开发方案/P1-S4-R7-C开发方案-Part3.md)

## 逐项执行结果

| 任务 | 对应切片 | 落地位置 | 结果 | 说明 |
|---|---|---|---|---|
| TS-011 行映射引擎与两年测试数据集 | SL-006 | `frappe_china/accounting/statements/mapping.py`；`engine.py`；`labels.py`；`tests/dataset.py`；`tests/test_mapping.py` | ✅完成 | 建立 `Src`／`Line` 映射模型、资产负债表 53 行与利润表 32 行定义、公式安全求值、勾稽检查、缺号聚合报错、按科目／往来单位快照取数和测试数据集工厂。 |

## 验证

| 验证项 | 实测结果 |
|---|---|
| `test_mapping.py` | ✅ 3/3；行次形状、公式勾稽、全量科目号解析与缺号聚合均通过 |
| Python 导入与编译 | ✅ `compileall`／测试站实际导入通过 |
| 测试站 | ✅ `bench --site test.localhost run-tests --app frappe_china --module frappe_china.tests.test_mapping`，3/3 |
| 全量 app 回归 | ✅ `bench --site test.localhost run-tests --app frappe_china`，46/46 |

## 实现边界

- 两年数据集工厂已提供 2025-01 至 2026-03 的确定性月份骨架与独立期望值；发票、现金流底稿和报表执行留给后续 TS-012～015 按方案继续补齐。
- `Src.exclude` 用于税费组中已单独分列明细的排除，避免同一明细被重复计入。
- 资产负债表右栏补齐 32 行版式槽位，空槽不带行次，供 TS-012 左右栏逐位配对。

## 状态值

**TS-011 已完成。下一续跑点：TS-012 资产负债表。**

## 复核建议

1. TS-012 接入 `snapshot_balance` 时复核年初余额与会计年度期初凭证口径。
2. TS-013 接入税金及附加分摊前，补一笔无法按贷方税种分摊的 `5403` 凭证，验证说明行。
