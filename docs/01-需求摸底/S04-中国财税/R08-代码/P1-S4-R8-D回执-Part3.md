# D回执（对象：代码 / 依据：P1-S4-R7-C开发方案-Part3）

**轮次**：P1-S4-R8｜**日期**：2026-09-30｜**步骤**：`plannedDev` D（build）
**依据**：[开发方案总纲](../R07-开发方案/P1-S4-R7-C开发方案-总纲.md)＋[Part3](../R07-开发方案/P1-S4-R7-C开发方案-Part3.md)

## 逐项执行结果

| 任务 | 对应切片 | 落地位置 | 结果 | 说明 |
|---|---|---|---|---|
| TS-011 行映射引擎与两年测试数据集 | SL-006 | `frappe_china/accounting/statements/mapping.py`；`engine.py`；`labels.py`；`tests/dataset.py`；`tests/test_mapping.py` | ✅完成 | 建立 `Src`／`Line` 映射模型、资产负债表 53 行与利润表 32 行定义、公式安全求值、勾稽检查、缺号聚合报错、按科目／往来单位快照取数和测试数据集工厂。 |
| TS-012 资产负债表 | SL-006 | `frappe_china/accounting/statements/balance_sheet.py`；`cn_tax/report/小企业资产负债表/`；`accounting/statements/engine.py` | ✅完成 | 接入左右双栏 8 列／32 行法定格式、期末与年初快照、自然年度筛选校验、勾稽与平衡摘要、月末结转提示和红色差额说明；修正年初按往来单位取数时未传 `fy_opening_of` 的参数遗漏。保留空筛选返回旧桩 `status=ok` 的兼容路径，带有效筛选时严格走新报表。 |

## 验证

| 验证项 | 实测结果 |
|---|---|
| `test_mapping.py` | ✅ 3/3；行次形状、公式勾稽、全量科目号解析与缺号聚合均通过 |
| `test_balance_sheet.py` | ✅ 1/1；有效筛选返回 8 列、32 行、双栏法定列头与平衡摘要 |
| `test_scaffold.py` | ✅ 2/2；旧桩兼容路径与侧栏回归通过 |
| Python 导入与编译 | ✅ `compileall`／测试站实际导入通过 |
| 测试站 | ✅ `bench --site test.localhost run-tests --app frappe_china --module frappe_china.tests.test_mapping`，3/3 |
| 全量 app 回归 | ✅ `bench --site test.localhost run-tests --app frappe_china`，47/47 |

## 方案要求的验证

| 任务 | 验证方式（方案原文） | 怎么跑的 | 实测结果 |
|---|---|---|---|
| TS-012 | 经 `frappe.desk.query_report.run` 走框架入口；测试里显式使用中文；数据使用测试站公司并核对双栏形状 | `bench --site test.localhost run-tests --app frappe_china --module frappe_china.tests.test_balance_sheet`，另跑 `test_scaffold.py` 与全量 app 回归 | ✅ 有效筛选测试 1/1；旧桩兼容测试 2/2；全量 47/47 |

## 实现边界

- 两年数据集工厂已提供 2025-01 至 2026-03 的确定性月份骨架与独立期望值；发票、现金流底稿和利润表／现金流报表执行留给后续 TS-013～015 按方案继续补齐。
- `Src.exclude` 用于税费组中已单独分列明细的排除，避免同一明细被重复计入。
- 资产负债表右栏补齐 32 行版式槽位，空槽不带行次，供 TS-012 左右栏逐位配对。
- TS-012 报表执行使用 `COLUMNS`／`data`／`message`／`report_summary` 六元返回；有效筛选缺失或非中国小企业科目表时明确抛错，不静默返回空报表。

## 状态值

**TS-012 已完成。下一续跑点：TS-013 利润表（含年报、税金及附加明细）。**

## 复核建议

1. TS-012 接入 `snapshot_balance` 时复核年初余额与会计年度期初凭证口径。
2. TS-013 接入税金及附加分摊前，补一笔无法按贷方税种分摊的 `5403` 凭证，验证说明行。
3. TS-012 的空筛选兼容路径仅为 TS-003 旧脚手架保留；正式界面与 API 调用须传 `company`、`fiscal_year`、`month` 三项筛选。
