# P1-S8-R6 D 回执 · Part2

**日期**：2026-10-22｜**执行者**：Codex｜**打 tag**：否
**依据**：[R5 开发方案·Part2](../R05-开发方案/P1-S8-R5-C开发方案-Part2.md)及总纲。

## 逐项执行结果

| 任务 | 对应切片 | 落地位置（文件:行） | 结果 | 完成时间 | 说明 |
|---|---|---|---|---|---|
| TS-013 场景参数文件与加载校验 | SL-011 | `frappe_debug/scenario/params.py:293`、`frappe_debug/data/scenario.yaml:3`、`frappe_debug/tests/test_params.py:109` | ✅完成 | 2026-10-22 | 实现不可变 Scenario、YAML 安全加载、相对日期／工作日推导、日期分段及业务参数逐项汇总校验；缺省配置为 HDS。ATDD 先红 10/10（模块缺失），实现后 11/11（2.789 秒）；六类必需错误、合法日期样例、假日顺延、默认文件及不写入断言均通过。无新增工程约定。 |
| TS-014 建单辅助、主数据与期初 | SL-011 | `frappe_debug/builders/{common,selling,buying,manufacturing,accounts,crm,dates}.py`、`scenario/{masters,opening}.py`、`tests/{test_builders,test_builder_dates,test_builder_integration,test_masters}.py` | ✅完成 | 2026-10-22 | 公共日期流程、主数据幂等与期初 GL 通过。真实原生 mapper 集成测试3/3：CRM 转换返回 string、报价客户创建及订单子行交期；采购按供应商/场景日期取价、拒收收货 GL/SLE、非零发票与 1002 付款结清；草稿生产计划生成日期正确且已提交工单/工序卡。 |
| TS-015 每日全链 | SL-011 | `frappe_debug/scenario/slots.py`、`tests/test_slots.py` | ⚠️部分 | 2026-10-22 | 首段连续工作时间分配器已实现；已覆盖同工位占用、午休/日界、假日及禁用时段，目标测试3/3。库中占用查询按原生 Job Card `docstatus < 2` 读取。尚未实现 run_day／14 天全链，HT-020真实 12 卡工位验证未完成。 |
| TS-016 每月任务、缺料、第 6／9 幕前置 | SL-011 | — | ⬜未开始 | — | — |
| TS-017 生成器入口、后台任务与一年实跑 | SL-011 | — | ⬜未开始 | — | — |

## 方案要求的验证

| 任务 | 验证方式（方案原文） | 怎么跑的 | 实测结果 |
|---|---|---|---|
| TS-013 | `test_params.py`：SL-011 ① 六例；一例完整合法参数解析出的 S／D1／D2／E／segments 与写死值一致（以 E＝2026-10-20 为例：S＝2025-10-01）。 | `bench --site test.localhost run-tests --module frappe_debug.tests.test_params`；另对 `frappe_debug` 执行 Ruff check 与 format check。 | 11/11（2.789 秒）；写死日期与三段区间通过，默认 `scenario.yaml` 可载入；Ruff 与格式检查通过。 |
| TS-014 | `test_masters.py`：小参数在测试站事务内 `build_masters` 两次，第二次无新增；期初日记账 GL 借贷与参数一致。 | `bench --site test.localhost run-tests --app frappe_debug`；另先红后绿运行 `test_builders.py`。 | 21/21（27.397秒），退出0；15类主数据二次构建计数不变，2张已提交BOM；期初日记账已提交，GL借贷各1,000,000，1002银行借700,000、3001资本贷1,000,000；日期辅助5/5，建单公共流程2/2。Ruff check、22个文件格式检查均通过。 |
| TS-015 | `test_day.py`：测试站事务内 14 天小场景；断言单据类型计数、日期不减、GL／SLE 齐全、同工位不重叠；⑪ 在 TS-017 的后台任务里核。 | — | — |
| TS-016 | `test_monthly.py` 与 `test_shortage.py`：测试站逐月跑一年；核折旧、月末结转、现金流底稿、计件汇总；断料时第一张卡的首道工序被推迟，后续物料到货后恢复。 | — | — |
| TS-017 | SL-011 ③～⑫：在 `s8dev.localhost` 实跑全年，核单据／GL／SLE 数量、三规则分段、月末业务、供应商评分、工位排程、SPC、负荷、缺料、第 9 幕建议、后台补丁与分段续跑；记录总耗时及每日耗时分布。 | — | — |

## 全量验证

| 门 | 结果 |
|---|---|
| `frappe_china` 集成测试 | — |
| 旧类与未分类测试 | — |
| Node、Ruff 与格式检查 | 2026-10-22 `frappe_debug` Ruff check通过，22个Python文件format check通过；本次无Node文件。 |
| `frappe_debug` 测试 | 当前全量29/29（43.960秒），退出0；含 TS-014真实 mapper 集成3项、builders 4项、参数12项、日期5项、SlotAllocator 3项与 smoke 1项。 |

## 偏离与暂停

暂无。

## 新增约定

| 约定 | 类别 | 在哪个任务确立 |
|---|---|---|

## 未做项

| 项 | 为什么没做 |
|---|---|

## 状态值

执行中；TS-013、TS-014完成；TS-015部分实现时段分配器，尚未实现 run_day／14天全链；TS-016～017未开始。当前全量29/29通过；续跑锚点为实现并验证 TS-015 每日全链。HT-015 属于 TS-021 的前置验证，不阻塞当前任务；TS-017前不跑生成器整年实跑。当前无待用户裁决的阻塞。

## 复核建议

`test_builder_integration.py` 真实集成测试锁住 CRM 客户创建、采购价与拒收数量、Production Plan 草稿提交。日全链、所有业务单据逐类 GL/SLE 与真实同工位 12 卡排程仍须在后续 `test_day.py`／TS-017 实跑中验证。HT-015 按方案在 TS-021 前执行 SA 验证，不阻塞 TS-015～017。

## 2026-10-22 中途提交检查点

- 用户明确授权提交并推送当前进度。`frappe_china`的Part1实现已推送至`ee153b4591ce80419290a39ec430a0c99c0381a3`；`frappe_debug`的场景参数、日期辅助、主数据与期初实现已推送至`e2843633210688417b73303e3ee4cd50ee1865d4`。主仓库同步更新`docker/apps.json`。
- 本次是开发中途保存：TS-014仍为部分完成，TS-015～017未开始，不代表Part2全量验收或D步收口。续跑从TS-014的原生mapper建单辅助开始。
- 提交前未发现测试或场景生成任务；昨晚遗留的`purchase_receipt_ui.cjs`进程60268已结束。常驻Docker、web、worker与scheduler继续正常运行。
