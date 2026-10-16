# P1-S7-R5 D 代码讨论记录

**讨论主题**：TS-012 工序间数量传递的 Manufacture 数量口径
**日期**：2026-10-16
**参与者**：用户、Codex

## 演化过程

#### 第 1 步：裁决 TS-012 的验收口径

**提出者：** Codex
**背景：** 独立 SA 已证明工序间数量传递本身可按 950 继续，但原方案把 Manufacture 的 `fg_completed_qty=950` 与 `process_loss_qty=50` 同时作为验收输入。ERPNext 原生会将成品行算为 `950 - 50 = 900`，工单仍为 `In Process`，因此无法满足“成品 950、工单 Completed”的验收条件。若不裁决，TS-012 及其后续任务不能继续。
**选项：**

| 选项 | 描述 | 优点 | 缺点 |
|---|---|---|---|
| A（推荐） | 保持 ERPNext 原生语义，将 Manufacture 输入改为 `fg_completed_qty=1000`、`process_loss_qty=50`，得到成品 950、工单 Completed | 不改原生库存与工单语义，改动和风险最小 | 验收输入不再与原方案字面相同 |
| B | 保留 `950/50` 输入，接受成品 900、工单 In Process | 零生产语义改动 | 与演示要表达的 950 成品及原验收条件不一致 |
| C | 保留 `950/50` 输入，改造生产语义使成品 950 且工单 Completed | 保留原输入字面 | 需覆盖库存数量、工单状态及后续链路，范围和风险显著扩大 |

**用户回答：** 用户选择 A：改验收输入，保持原生语义，使用 `fg_completed_qty=1000`、`process_loss_qty=50`，使成品 950、工单 Completed。
**结论：** TS-012 按 A 继续；不改 ERPNext 原生生产语义。测试验收条件与 D 待验表、D 回执同步改写，随后先红后绿实现。
**产物快照：** TS-012 的 HT-012 验收输入为 `fg_completed_qty=1000`、`process_loss_qty=50`；预期 finished-good 数量 950，Work Order 状态 `Completed`。

#### 第 2 步：暂停 Manufacture 验收并保留原生失败证据

**提出者：** Codex
**背景：** 按第 1 步口径实现数量级联后，三项工序卡测试全部通过；但原生 Manufacture 校验出现新的事实冲突。级联后的第二、三道工序均为完工 950、损耗 0，`fg_completed_qty=1000` 的 Manufacture 在提交前会被 `check_if_operations_completed()` 拒绝，因为 `950 + 0 < 1000`。将输入降为 `950/0` 后，原生又会自动带入首道损耗 50，生成成品 900，工单保持 `In Process`。
**用户回答：** 保留原生语义：暂停 TS-012 Manufacture 验收，保留级联代码与失败证据，重新确定验收口径。
**结论：** TS-012 的工序数量级联实现保留；Manufacture 成品 950／工单 `Completed` 不再作为当前已确认验收结果。TS-012 暂停在 Manufacture 验收口径，TS-013～017 继续按任务顺序等待 TS-012 重新定口径。
**证据：** `bench --site test.localhost run-tests --module frappe_china.tests.test_operation_flow` 复跑 4/4（10.877s，退出 0），Manufacture 用例明确断言 `1000/50` 抛 `OperationsNotCompleteError`，以及原生 `950/0 → 成品行900、produced_qty=900、process_loss_qty=50、status=In Process`。固定证据说明见 `Spike/P1S7R5-D/ts012-native-evidence.md`，运行日志为 `frappe-bench/logs/s7-r5-ts012-native-evidence.log`；原始探针见 `Spike/P1S7R5-D/ht012-probe.log`。

## 决策汇总表

| 决策内容 | 最终选择 | 选择理由 | 提出者 | 失效条件 |
|---|---|---|---|---|
| TS-012 Manufacture 数量口径（第 1 步，已失效） | 当时选择 A：`fg_completed_qty=1000`、`process_loss_qty=50`，预期成品 950、工单 Completed；第 2 步已暂停该口径 | 当时仅按成品扣损耗与工单完成公式判断，后续原生工序校验否证该假设 | 用户裁决 | 已触发：当前下游工序 950＋0 无法通过 1000 的原生校验，以第 2 步裁决为准 |
| TS-012 当前处理 | 暂停 Manufacture 验收，保留原生语义与失败证据 | `1000/50` 在当前级联结果下被原生工序校验拒绝；`950/0` 只能得到成品 900、工单 In Process | 用户裁决 | 重新确定可同时满足工序级联与入库验收的口径 |

## 被否决方案汇总表

| 方案 | 否决理由 |
|---|---|
| B：保留 `950/50` 并接受成品 900、工单 In Process | 不满足原验收目标 |
| C：改造原生生产语义 | 改动范围和风险过大，且无必要 |

## 遗留问题

| 事项 | 状态（暂缓/待确认/待调研） | 触发条件（何时重新处理） |
|---|---|---|
| TS-012 Manufacture 验收口径 | 待确认 | 用户重新确定与原生工序校验一致的验收输入后，恢复 TS-012 收口；在此之前不进入 TS-013 |
