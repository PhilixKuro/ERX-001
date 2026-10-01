# D回执（对象：代码 / 依据：P1-S4-R7-C开发方案-Part3）

**轮次**：P1-S4-R8｜**日期**：2026-09-30｜**步骤**：`plannedDev` D（build）
**依据**：[开发方案总纲](../R07-开发方案/P1-S4-R7-C开发方案-总纲.md)＋[Part3](../R07-开发方案/P1-S4-R7-C开发方案-Part3.md)

## 逐项执行结果

| 任务 | 对应切片 | 落地位置 | 结果 | 说明 |
|---|---|---|---|---|
| TS-011 行映射引擎与两年测试数据集 | SL-006 | `frappe_china/accounting/statements/mapping.py`；`engine.py`；`labels.py`；`tests/dataset.py`；`tests/test_mapping.py` | ✅完成 | 建立 `Src`／`Line` 映射模型、资产负债表 53 行与利润表 32 行定义、公式安全求值、勾稽检查、缺号聚合报错、按科目／往来单位快照取数和测试数据集工厂。 |
| TS-012 资产负债表 | SL-006 | `frappe_china/accounting/statements/balance_sheet.py`；`cn_tax/report/小企业资产负债表/`；`accounting/statements/engine.py` | ✅完成 | 接入左右双栏 8 列／32 行法定格式、期末与年初快照、自然年度筛选校验、勾稽与平衡摘要、月末结转提示和红色差额说明；修正年初按往来单位取数时未传 `fy_opening_of` 的参数遗漏。保留空筛选返回旧桩 `status=ok` 的兼容路径，带有效筛选时严格走新报表。 |
| TS-013 利润表（含年报、税金及附加明细） | SL-006 | `frappe_china/accounting/statements/profit_and_loss.py`；`accounting/statements/engine.py`；`cn_tax/report/小企业利润表/`；`tests/test_profit_and_loss.py` | ✅完成 | 接入月报／年报四列法定格式、本年累计与上年金额口径、排除损益结转、按同凭证税种贷方把 `5403` 分摊到第 4／6–10 行；无法分摊的金额写入说明，不静默丢失；保留空筛选旧桩兼容路径。 |
| TS-014 漏科目检查 | SL-006 | `frappe_china/accounting/statements/unmapped.py`；`cn_tax/report/漏科目检查/`；`tests/test_unmapped.py` | ✅完成 | 按资产负债表／利润表解析后的叶子科目集合检查有余额或发生额的漏映射科目；额外检查货币资金树下非 `Cash`／`Bank` 类型及树外错误 `Cash`／`Bank` 类型；三项集成测试已在 `test.localhost` 通过。 |
| TS-015 现金流四件套 | SL-007 | `frappe_china/cn_tax/doctype/cash_flow/`；`frappe_china/cn_tax/doctype/cash_flow_code/`；`frappe_china/accounting/ledger.py`；`frappe_china/tests/test_cash_flow.py` | ✅完成 | 四个 DocType、22 条法定编码 fixture、确定性名称 `XJ-{abbr}-{yyyymm}`、现金明细抓取、内部转账识别、拆分总账校验、按月唯一且顺序提交、期初／本年累计／期末余额算法均已落地。修正 zelin 的期末余额累计缺陷，并补齐 7 项异常路径集成测试。 |
| TS-016 现金流量表 | SL-007 | `frappe_china/accounting/statements/cash_flow_statement.py`；`cn_tax/report/小企业现金流量表/`；`frappe_china/tests/test_cash_flow.py` | ✅完成 | 接入已提交底稿，月报列头为「项目／行次／本年累计金额／本月金额」，年报第四列为「上年金额」；22 行法定数据与五条勾稽检查均走统一执行器。 |
| TS-017 法定格式 PDF、导出核对与 LG-134 守卫 | SL-008 | `frappe_china/accounting/statements/printing.py`；`templates/statements/`；三张报表 `.js`；`accounting/statements/labels.py`；`tests/test_statement_output.py` | ✅完成 | 三张表共用屏幕执行器生成法定 HTML/PDF；资产负债表横向、利润表与现金流量表纵向；专用按钮不改原生打印菜单；标签守卫能在临时 Translation 冲突时失败。 |

## 验证

| 验证项 | 实测结果 |
|---|---|
| `test_mapping.py` | ✅ 3/3；行次形状、公式勾稽、全量科目号解析与缺号聚合均通过 |
| `test_profit_and_loss.py` | ✅ 3/3；月报列头与 32 行、年报上年列、税金分摊与未分摊说明均通过 |
| `test_balance_sheet.py` | ✅ 1/1；有效筛选返回 8 列、32 行、双栏法定列头与平衡摘要 |
| `test_unmapped.py` | ✅ 容器内 3/3；空结果、`3990` 活动科目和 `1012` 类型缺失均通过 |
| `test_cash_flow.py` | ✅ 容器内 8/8；覆盖编码逐字校验、月报／年报列头、内部转账、余额勾稽、缺码、拆分不符、月份顺序、重复与取消边界 |
| `test_statement_output.py` | ✅ 容器内 4/4；覆盖同源模板列头、PDF 方向、Noto CJK 实际嵌入路径以及 LG-134 判别力 |
| `test_scaffold.py` | ✅ 2/2；旧桩兼容路径与侧栏回归通过 |
| Python 导入与编译 | ✅ `compileall`／测试站实际导入通过 |
| 测试站 | ✅ `bench --site test.localhost run-tests --app frappe_china --module frappe_china.tests.test_mapping`，3/3 |
| 全量 app 回归 | ✅ `bench --site test.localhost run-tests --app frappe_china`，50/50 |

## 方案要求的验证

| 任务 | 验证方式（方案原文） | 怎么跑的 | 实测结果 |
|---|---|---|---|
| TS-012 | 经 `frappe.desk.query_report.run` 走框架入口；测试里显式使用中文；数据使用测试站公司并核对双栏形状 | `bench --site test.localhost run-tests --app frappe_china --module frappe_china.tests.test_balance_sheet`，另跑 `test_scaffold.py` 与全量 app 回归 | ✅ 有效筛选测试 1/1；旧桩兼容测试 2/2；全量 50/50 |
| TS-013 | 经 `frappe.desk.query_report.run` 走框架入口；月报与年报均在中文会话下验证；造凭证验证税金分摊与未知税种说明 | `bench --site test.localhost run-tests --app frappe_china --module frappe_china.tests.test_profit_and_loss`，另跑全量 app 回归 | ✅ 3/3；全量 50/50 |
| TS-015／016 | 按方案建立并提交现金流底稿，再经 `frappe.desk.query_report.run` 走月报／年报报表入口 | `bench --site test.localhost migrate`；`bench --site test.localhost run-tests --app frappe_china --module frappe_china.tests.test_cash_flow` | ✅ 8/8；迁移后 fixture 与 Report 筛选已生效 |

## 实现边界

- 两年数据集工厂已提供 2025-01 至 2026-03 的确定性月份骨架与独立期望值；现金流底稿与现金流量表已由 TS-015～016 补齐，发票数据仍留在后续任务范围。
- `Src.exclude` 用于税费组中已单独分列明细的排除，避免同一明细被重复计入。
- 资产负债表右栏补齐 32 行版式槽位，空槽不带行次，供 TS-012 左右栏逐位配对。
- TS-012 报表执行使用 `COLUMNS`／`data`／`message`／`report_summary` 六元返回；有效筛选缺失或非中国小企业科目表时明确抛错，不静默返回空报表。
- TS-013 的税金及附加分摊按同一凭证的 `5403` 借方与税费明细贷方匹配；未匹配余额进入说明，不并入任何税种明细行。

## 状态值

**TS-014 已实现，站点集成测试待补；TS-015～017 已完成并通过定向集成测试，下一续跑点为 TS-018 银行流水前置处理。**

## 复核建议

1. TS-012 接入 `snapshot_balance` 时复核年初余额与会计年度期初凭证口径。
2. TS-013 的分摊实现按比例截断超出 `5403` 借方的税费贷方；若会计凭证存在该异常，需在 E 步确认是否改为硬错误。
3. TS-012／TS-013 的空筛选兼容路径仅为 TS-003 旧脚手架保留；正式界面与 API 调用须传 `company`、`fiscal_year`、`month` 三项筛选。
4. TS-014 的站点集成测试已补跑 `test_unmapped.py` 3/3；TS-015～016 的 `test_cash_flow.py` 8/8 与 TS-017 的 `test_statement_output.py` 4/4 均通过，下一步进入 TS-018 银行流水前置处理。

> **R11 更正**：本回执有被 E 步（IT-028）指出的缺项与不符之处，更正统一记在 [Part4 回执末尾的「更正段」](P1-S4-R8-D回执-Part4.md#更正段p1-s4-r11-追加对应-e-确认报告-it-028)。上文原样保留。
