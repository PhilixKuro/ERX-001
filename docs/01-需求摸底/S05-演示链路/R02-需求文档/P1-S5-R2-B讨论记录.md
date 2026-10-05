# P1-S5-R2 B 步中途讨论记录（plannedDev B 步·需求文档）

**讨论主题**：B 步写需求文档时冒出的、A 步已裁决但前提读码不成立的事项
**日期**：2026-10-05
**参与者**：用户、Claude（Opus 5.5）
**性质**：`play-build` 契约纪律 3「冒真判断 → 按需引用讨论契约、就地新开一份讨论记录」。**本文件不带状态值**——B 步的状态值在本 Round 回执里（规范 §11.1「中途讨论记录」条）。
**依据**：[R1 A 需求讨论](../R01-需求讨论/P1-S5-R1-A需求讨论.md)（第 1–9 步）
**承接说明**：本文件是 B 步的中途讨论记录，与 A 步讨论记录不是同一产物。步号自第 1 步起（同 S4-R6 先例）。

> **落档开关未开**：本记录只有一个议题，提出与裁决都在同一个对话轮内完成（取裁用选项工具，不另占对话轮），写下第 1 步时讨论已结束。开关的作用是逐轮核步号，此处没有第二轮可核，故未开（讨论契约 §5「谁开」「谁关」由载入方定时点）。

---

## 演化过程

#### 第 1 步：B 步开工；问 1「找单子」的加权金额须由 AI 自己算

**① 读盘定位**

**提出者：** 用户（「继续开发项目」，随后两次「继续」）

**背景：** 按流程中枢第 1–2 步读盘：项目概况 → P1（进行中）→ S5 演示链路（`plannedDev`）。S5 概况「当前进度」：R1 的 A 步状态值 `已收敛`，下一步 B 步、由用户在新 Session 开——本 Session 即那个新 Session。判为情形 A，按出口路由「A shape · 已收敛 → B」驱动 B 步。

**结论：** 本 Round 为 **R2，跑 B 步（build，需求文档）**。Spec：[B-requirement-plannedDev-build.md](../../../流程体系/workflows/plannedDev/B-requirement-plannedDev-build.md)。`打tag=否`。预设执行者 Claude。依据为 R1 A 需求讨论全文（唯一一份 A 步实例）。

**② 问 1 的口径：`expected_deal_value` 不是加权金额**

**提出者：** Claude

**背景：** DEC-012 定「进行中的商机按 `expected_deal_value` 排序取前几名」，并注明「＝金额 × 概率」是按字段名推断、计算式未读，留 C 步核。写需求文档时读了 CRM `main`（分支头 `deedce73`），推断不成立：

| # | 事实 | 出处 |
|---|---|---|
| 1 | `expected_deal_value` 是一个独立的 `Currency` 字段（label「Expected Deal Value」），语义是「预计成交金额」 | `crm/fcrm/doctype/crm_deal/crm_deal.json` |
| 2 | 它不由概率算出。唯一自动改写它的地方是：开了 `auto_update_expected_deal_value` 且 Deal 有明细合计时，用 `net_total or total` 覆盖它 | `crm/fcrm/doctype/crm_deal/crm_deal.py:240-249` |
| 3 | `probability` 是 `Percent` 字段，按百分数存（50 表示 50%）；Deal 状态带默认概率（10／25／50／70／90／100／0） | `crm_deal.json`；`crm/install.py` 的 `add_default_deal_statuses` |
| 4 | CRM 自己的「预测收入」看板是**查询时**算 `expected_deal_value × probability ÷ 100 × 汇率` | `crm/api/dashboard.py:677-683` |
| 5 | Raven 的 `Get List` 只能按单个已有字段排序，无表达式（A 步第 4 步事实 3）；走 LiteLLM 时无代码解释器（A 步第 4 步事实 5） | `raven/ai/sdk_tools.py:486-600`、`agents_integration.py` |

可复现：`curl https://raw.githubusercontent.com/frappe/crm/main/crm/fcrm/doctype/crm_deal/crm_deal.py`，看 `update_expected_deal_value`；同仓 `crm/api/dashboard.py` 搜 `probability`。

⇒ 若照字面实现 DEC-012，「按加权金额排」就成了「按预计金额排」，漏斗概率不参与。要保留用户选的口径，乘法要么由 AI 做，要么由一个自写函数做。

**选项：**

| 选项 | 描述 | 优点 | 缺点 |
|---|---|---|---|
| **AI 自己乘**（推荐） | 口径不变；bot 用 `Get List` 取进行中商机的金额与概率两个字段，自己算完再排序。测试数据把各单的加权金额拉开差距；3 次全对才算答得出；答不出再改用自写函数 | 零开发；仍是「现成工具就能答」 | 依赖模型算术；最小数据下算得对不保证 S7 的 100 条下也对 |
| 自写查询函数 | 口径不变；另写一个 `Custom Function` 直接返回按加权金额排好的商机 | 最稳，不靠模型算数 | 多 0.25–0.5 人日；问 1 不再是「现成工具就能答」 |
| 改成不加权 | 只按 `expected_deal_value` 排 | 零开发、零算术 | 不是用户选的「金额 × 概率」，概率不再参与排序 |

**用户回答：** 取「AI 自己乘」（选项工具作答）。

**结论：** **DEC-020**：问 1 的口径维持「金额 × 概率」，**由 bot 自取 `expected_deal_value` 与 `probability` 两字段自行计算排序**，`probability` 按百分数除以 100。三问实测时问 1 若 3 次未全对，改走自写 `Custom Function`（即上表第二项，作为显式退路）。**更正 DEC-012 的计算式推断**（「`expected_deal_value` ＝ 金额 × 概率」不成立）。连带两条约束由 Claude 补、写进需求文档 §4.6：① 问 1 的测试数据须使「按加权金额排」与「只按金额排」得出**不同**的前几名，否则测不出 AI 有没有真的乘（开发守则「判据必须能区分它要区分的两种情形」）；② 「前几名」取前 3 名（A 步未定数目）。

---

## 决策汇总表

| 编号 | 决策内容 | 最终选择 | 选择理由 | 提出者 | 失效条件 |
|---|---|---|---|---|---|
| **DEC-020** | 问 1 加权金额由谁算（更正 DEC-012 的计算式推断） | **bot 自取金额与概率两字段自行计算排序**；3 次未全对则改走自写 `Custom Function` | 保住用户选的口径且零开发；退路明确 | Claude（第 1 步），用户确认（第 1 步）；两条测试约束由 Claude 补 | 实测 3 次未全对；或用户换模型（同 DEC-011） |

## 被否决方案汇总表

| 编号 | 方案 | 否决理由 |
|---|---|---|
| **NV-003** | 问 1 改为只按 `expected_deal_value` 排序 | 不是用户选的口径，漏斗概率不再参与（第 1 步） |

（「自写查询函数」未被否决，降为 DEC-020 的退路。）

## 遗留问题

无新增（问 1 的退路已写进 DEC-020）。
