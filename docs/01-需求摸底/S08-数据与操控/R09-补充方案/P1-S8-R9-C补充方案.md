# P1-S8 数据与操控 —— 补充方案（R09）

**版本**：v1.0｜**日期**：2026-10-26｜**编写者**：Claude（Opus 5.5）
**产出步骤**：P1-S8-R9 · `plannedDev` C 步（`build`），F 审核 `出方案修` 回 C
**来源依据**：[R08 F 审核报告](../R08-审核/P1-S8-R8-F审核报告.md) 的 2 项 `出方案修`（FD-001、FD-003）及其 2026-10-26 用户裁决；片报告 [Part1](../R08-审核/P1-S8-R8-F审核报告-Part1.md) P1-01、P1-03
**原方案**：[R05 C 开发方案总纲](../R05-开发方案/P1-S8-R5-C开发方案-总纲.md)（§5.1、A18）与 [Part1](../R05-开发方案/P1-S8-R5-C开发方案-Part1.md)（TS-002～004）；需求 [R04 B 需求文档](../R04-需求文档/P1-S8-R4-B需求文档.md) §4.6.1、§4.6.2、§4.7、AC-004

> **定位**：只覆盖两项修复，不是新方案。执行者先读原方案 TS-002～004 与总纲 §5.1 了解上下文。任务号接原方案（TS-027 起），切片号接 SL-018 起，假设号接 HT-024 起。

---

## 一、概述

**修复范围**：

1. **FD-001**：演示数据里「支」不是整数单位，取整逻辑走小数分支，第 4 幕计划数量为 5,259.299 支而不是 AC-004 的 5261。
2. **FD-003**：`normalize_fallback_operating_cost` 只在「全部报工完、一次入库」时对，分批完工时少记工序成本（工单 1000 分两批 500 入库，记 75，应为 100）。

**用户裁决**（2026-10-26，已填回审核报告）：

| 发现 | 裁决 |
|---|---|
| FD-001 | 选①：「支」改为整数单位。按件计的单位一并改：支、个、台、只、件、张、套、片、条（共 9 个）。箱、包、卷、批、次、打及全部度量单位不动 |
| FD-003 | 按累计实际工序成本分摊：本次应吸收＝(截至本次的累计实际工序成本 − 本工单已提交完工入库已吸收的部分) × 本次完工数 ÷ 已报工未入库数。口径并入 `SH-P1S8010`，演示后交会计复核，不阻塞本次修复 |

**完成标准**：

- 新站与已有站上，这 9 个单位都是 `must_be_whole_number=1`；测试不再临时改单位属性，AC-004 的 5264／5261 照样成立。
- 生成器在整数单位下生成的「支」数量全部为整数，`verify` 有对应检查并通过。
- 分批完工时，各批附加费用之和等于累计实际工序成本；整单一次入库的结果与现行实现相同。

---

## 二、调研结论（本步读码与只读查库，供执行者对照）

### 2.1 FD-001

| 事实 | 依据 |
|---|---|
| 三站（`erx`、`s8verify`、`test`）上 9 个单位全是 `must_be_whole_number=0`，`Nos`／`Unit` 是 1 | 本步只读 SQL |
| `ensure_cn_uoms` 只建缺少的单位、不写整数属性；唯一调用点是 `after_install` | `frappe_china/accounting/install.py:55-64`；`frappe_china/install.py:228-234` |
| **新站上本次新加的补丁不会执行**：`install_app` 先 `set_all_patches_as_completed`，再跑 `after_install` | `frappe/installer.py:358-361` |
| 生成器里「支」数量出现小数的唯一来源是 `required_input_qty` 的非整数分支（`flt(q, 3)`）；整数单位下逐道 `ceil`，下游拆卡、工序数量传递、报工、完工入库、发货全部继承整数 | `process_loss.py:90-108`；生成器订单量按 500 取整（`day.py:114-118`）；报工损耗 `round()`（`day.py:407-408`）；第 6、7 幕数量为整数（`targets.py:159`、`demo.yaml`） |
| 原生整数校验：Work Order `qty`、Production Plan `planned_qty`、Stock Entry 行、BOM `process_loss_qty`、报价／订单／发货／发票行；Job Card 不校验 | `transaction_base.py:618-650`；`work_order.py:1636-1653`；`production_plan.py:142`；`stock_entry.py:291-292`；`bom.py:1365-1373` |
| 改整数后场景 BOM 整体损耗率按 A18 取：压簧 4.9303%→4.9%、拉簧 3.97%→3.9%（BOM 数量 1000）。工单数量按工序损耗率逐道算，不读整体值 | `process_loss.py:99-102`；`scenario.yaml:71-120` |
| 这 8 个单位（个、台、只、件、张、套、片、条）在两个自有 app 里只出现在 `CN_UOMS` 清单；两站物料的库存单位只有「支」与「千克」 | 子 Agent grep 与只读 SQL |
| `erx.localhost` 现有 3 张未开工的小数工单（`MFG-WO-2026-00062` 5259.299、`00074`／`00077` 4207.439），改整数后若在其上做完工入库会被原生拦下 | 只读 SQL。演示站要从清洁基库整场重跑（S8 概况既定），重跑后这些工单不再存在 |

### 2.2 FD-003

| 事实 | 依据 |
|---|---|
| 上游 fallback 行金额＝`remaining × fg_completed_qty`；已报工工序的 `remaining` 取**累计** `actual_operating_cost − consumed`，而 `consumed` 按 `operation_id` 查，fallback 行不写 `operation_id`，故恒为 0 | `stock_entry.py:4470-4519`；`bom.py:1827-1854` |
| 未报工工序（`completed_qty=0`）取 `planned ÷ 工单数`（单位额）；累计为 0 时退回 `BOM.operating_cost ÷ BOM.quantity`（单位额）；多层 BOM 子装配路径也是单位额。这三条乘 `fg` 后都不放大 | `stock_entry.py:4498-4525` |
| 有工位成本组件时上游按「累计实际 − 已吸收」再乘「本次 ÷ 剩余报工数」，并封顶在剩余成本——即用户裁决的口径 | `bom.py:1748-1817` |
| `check_if_operations_completed`：每道工序须满足 `fg + 工单 produced_qty ≤ completed_qty + process_loss_qty (+容差)`，故完工入库时每道工序都已有报工，「未报工」分支在非半成品跟踪工单上到不了 | `stock_entry.py:1168-1200`（`:1042` 仅非 `track_semi_finished_goods` 时调） |
| 工单工序行的 `process_loss_qty` 是**累计**损耗（S7 TS-018 口径），s8verify 852/852 道工序满足 `completed_qty + process_loss_qty = 工单 qty` | `operation_flow.py:47-78`；本步只读 SQL |
| 完工入库的 `fg_completed_qty` 含损耗；已提交入库的 `fg_completed_qty` 之和即「已入库数」，与上一行同一口径 | `stock_entry.py:878-900`、`:3282-3305` |
| fallback 行的可靠识别：`has_operating_cost=1` 且 `operation_id`、`operating_component` 都空。用户手加行、「Additional Operating Cost」行、非库存物料行、返修行都不满足 | `landed_cost_taxes_and_charges.json:83-89`；`bom.py:1856-1921` |
| Job Card 提交、取消都会重算并保存工单 `actual_operating_cost`（累计值） | `job_card.py:783-792,1052-1094`；`work_order.py:620-643` |
| 场景每张工单只有一张完工入库、工位无成本组件（s8verify 332/332），新旧口径结果相同；`erx.localhost` 已提交的 74 张完工入库各有一行 fallback，已提交单据不重算 | 本步只读 SQL；`day.py:428-433` |
| 生成器月末制造费用按 GL 上 `410199` 的净额记，不依赖修正公式，无须随动 | `frappe_debug/scenario/monthly.py:91-144` |

---

## 三、接口契约

### 3.1 `frappe_china`：整数计数单位（新）

```python
# frappe_china/accounting/install.py
WHOLE_NUMBER_UOMS: Final[tuple[str, ...]] = ("支", "个", "台", "只", "件", "张", "套", "片", "条")

def ensure_whole_number_uoms() -> list[str]:
    """把 WHOLE_NUMBER_UOMS 中已存在且 must_be_whole_number=0 的单位改为 1，返回改了的单位名。
    不建单位、不动 enabled；重复调用返回 []。"""
```

`ensure_cn_uoms` 建这 9 个单位时直接带 `must_be_whole_number: 1`；其余单位照旧。

### 3.2 `frappe_china`：fallback 工序成本（改）

```python
# frappe_china/accounting/stock_entry_accounts.py
def fallback_operating_cost_share(
    cumulative_actual: float,   # 已报工工序的累计 actual_operating_cost 之和
    absorbed_amount: float,     # 本工单其它已提交完工入库的 fallback 行金额之和
    reported_qty: float,        # min(各工序 completed_qty + process_loss_qty)
    entered_qty: float,         # 本工单其它已提交完工入库的 fg_completed_qty 之和
    finished_qty: float,        # 本单 fg_completed_qty
) -> tuple[float, bool]:
    """纯函数。返回 (本次应吸收的已报工部分金额, 已吸收是否超过累计实际)。
    remaining_cost = max(cumulative_actual − absorbed_amount, 0)
    remaining_qty  = reported_qty − entered_qty
    remaining_qty ≤ 0 时取 remaining_cost；否则 min(remaining_cost × finished_qty ÷ remaining_qty, remaining_cost)"""

def normalize_fallback_operating_cost(doc, method=None) -> None:
    """挂点、签名不变（Stock Entry before_validate 第 3 位）。改为按库里状态直接算出并覆盖 fallback 行金额，
    二次执行自然幂等，删掉现行「除了更远就跳过」的启发式。"""
```

---

## 四、技术假设

| # | 假设内容 | 状态 | 验证方式 | 不成立时 |
|---|---|---|---|---|
| HT-024 | 新站 `install-app` 时本次新加的补丁被预先标为已执行，故整数属性必须由 `after_install` 写 | 已读码（`frappe/installer.py:358-361`） | TS-027 测试直接调 `after_install` 路径的函数 | — |
| HT-025 | 非半成品跟踪工单在完工入库时，`min(各工序 completed_qty + process_loss_qty)` 就是累计已报工数（含损耗），与 `fg_completed_qty` 同一口径 | 已验证（s8verify 852/852 道工序 `completed+loss=工单数`；`check_if_operations_completed` 同式） | TS-030 集成用例断言 | 暂停反馈 |
| HT-026 | `before_validate` 里用 `frappe.get_doc("Work Order")` 读到的 `actual_operating_cost` 已含本单之前提交的全部 Job Card | 读码（`job_card.py:783-792` 提交时 `wo.save()`） | TS-030 集成用例：两批之间提交第二张卡后再建第二张入库 | 暂停反馈 |
| HT-027 | 工序拆卡数量设为工单数的一半时，提交第一张卡即可对一半数量做完工入库（原生校验放行） | 读码（`stock_entry.py:1168-1200`） | TS-030 集成用例 | 改用两张手工建的卡，回执记偏离 |
| HT-028 | 整数单位下，若工单所有工序报工损耗都为 0，原生完工入库按 `fg × BOM 整体损耗率 ÷ 100` 回退取损耗数量（`stock_entry.py:3298-3301`），`fg` 不是 BOM 数量的整倍数时会得小数、被整数校验拦下 | 读码，未实跑 | TS-028 加一条探测用例，**只记录结果、不修** | 若确实被拦：不在本方案内修，回执「未做项」写明，交用户裁决（生成器不会遇到：首道损耗 `round(≥500 × ~3%) > 0`） |

---

## 五、切片划分与验收

| 切片 | 功能点 | 验收条件 |
|---|---|---|
| **SL-018** 整数计数单位 | FD-001；需求 §4.6.1、§4.6.2、AC-004；总纲 A18 | ① `test.localhost` migrate 后 9 个单位均为 1，`箱`、`千克`、`米` 等仍为 0；再 migrate 一次补丁不再执行、`ensure_whole_number_uoms()` 返回 `[]`；② 新建单位走 `ensure_cn_uoms` 即为 1；已停用的「支」整数属性改为 1、`enabled` 仍为 0；③ 测试代码里不再有 `set_value("UOM", "支", "must_be_whole_number", 1)`，AC-004 的 5264／5261 与 A18 的 4.9／4.8／4.0／4.92／0／0 照样通过；④ 隔离站从清洁基准生成第一段（S→D1−1）后，`verify` 新增的「整数单位数量」检查通过，且工单、Job Card、完工入库、生产计划、BOM 损耗数量中「支」非整数条数为 0；⑤ 异常：补丁遇到在途的小数单据（未完工工单、草稿 Job Card、草稿生产计划）时仍改属性，并把清单写进 Error Log 与输出，不静默；⑥ HT-028 探测结果记进回执 |
| **SL-019** 分批工序成本 | FD-003；需求 §4.7；E IT-018 | ① 纯函数：(50,0,500,0,500)→50；(100,50,1000,500,500)→50；先多报工 (80,0,800,0,500)→50、(100,50,1000,500,500)→50；整单 (5235.11,0,69675.196,0,69675.196)→5235.11；② 异常：已吸收超过累计实际时金额为 0 且返回标志为真，`normalize` 出黄色提示；`remaining_qty ≤ 0` 时取剩余成本；③ 集成：真实工单 10 支、拆两张卡，第一张提交后入库 5、第二张提交后入库 5，两张入库的 fallback 行金额之和＝工单累计 `actual_operating_cost`（误差 ≤0.01），GL 只涉及存货类与 `410199`；取消第二张入库再重做，金额与取消前相同；④ 整单一次入库、组件行、Repack、半成品跟踪工单、多层 BOM 子装配路径、累计实际为 0 时：行金额不被本函数改动或与现行实现结果相同；⑤ 同一单 `before_validate` 跑两次结果不变 |

**执行每个切片前，对照该切片验收条件检查方案覆盖性——如发现按方案写出的代码无法通过验收条件，暂停反馈，不硬写。**

---

## 六、并行开发说明

SL-018（TS-027～029）与 SL-019（TS-030）改的文件不相交（前者 `accounting/install.py`、`patches/`、`install.py`、`tests/test_process_loss.py`、`tests/test_replenishment_rules.py`、`tests/test_install.py`、`frappe_debug/scenario/verify.py`；后者 `accounting/stock_entry_accounts.py`、`tests/test_s8_accounting.py`），可并行。同一执行者按序号串行即可。

## 七、任务清单

| 任务 | 对应切片 | 可并行否 |
|---|---|---|
| TS-027 整数计数单位：建单位、补丁、新站路径 | SL-018 | 与 TS-030 可并行 |
| TS-028 测试改为与演示同条件，加 HT-028 探测 | SL-018 | 依赖 TS-027 |
| TS-029 生成器整数检查与第一段实跑 | SL-018 | 依赖 TS-027 |
| TS-030 fallback 工序成本按累计实际分摊 | SL-019 | 与 TS-027～029 可并行 |
| TS-031 全量回归与登记 | 全部 | 最后 |

---

## 任务 TS-027：整数计数单位（对应切片 SL-018）

### 目标

新站与已有站上 9 个按件计的单位都是整数单位。

### 具体改动

1. `frappe_china/accounting/install.py`：加 `WHOLE_NUMBER_UOMS` 与 `ensure_whole_number_uoms()`（§3.1）。`ensure_cn_uoms` 插入时 `must_be_whole_number = 1 if name in WHOLE_NUMBER_UOMS else 0`。`WHOLE_NUMBER_UOMS` 的每一项都须在 `CN_UOMS` 里（加一条模块级断言或测试）。
2. `frappe_china/install.py` 的 `after_install`：在 `ensure_cn_uoms()` 之后调 `ensure_whole_number_uoms()`（HT-024：单位若在装 app 前已存在，新站只有这一条路）。
3. 新补丁 `frappe_china/patches/s8_whole_number_count_uoms.py`，登记在 `patches.txt` 的 `[post_model_sync]` 末尾：

```python
def execute():
    changed = ensure_whole_number_uoms()
    if not changed:
        return
    open_docs = 在途小数单据(changed)
    # 未完工工单：status not in (Completed, Closed, Cancelled) 且 docstatus<2、qty 有小数，production_item 的 stock_uom 在 changed
    # 草稿 Job Card：docstatus=0、for_quantity 有小数，production_item 的 stock_uom 在 changed
    # 草稿生产计划：docstatus=0、po_items.planned_qty 有小数，item 的 stock_uom 在 changed
    # 「有小数」判式与原生同：abs(cint(x) − flt(x, 精度)) > 1e-7
    if open_docs:
        frappe.log_error(title="S8 整数计数单位：在途单据仍为小数", message=清单)   # 关键字参数（FD-019 教训）
        print(清单)
```

   不改在途单据本身（单据数量是业务数据，交人处理）；属性照改。
4. 注释说明为何要两条路（补丁管已有站、`after_install` 管新站）。

### 验证方式

`tests/test_install.py`：
- 新增：先把「支」「个」设 0、「箱」设 0，调 `ensure_whole_number_uoms()` → 返回含「支」「个」、不含「箱」；再调一次返回 `[]`。
- 新增：停用的「支」经 `ensure_whole_number_uoms()` 后 `must_be_whole_number=1`、`enabled=0`。
- 既有 `test_existing_disabled_cn_uom_stays_disabled` 不改、仍过。
- 补丁：建一张未完工、`qty` 为小数的工单（产品单位「支」，先把「支」设 0），跑 `execute()` → 「支」为 1，Error Log 有一条该标题且内容含工单名；测试清理只删自己造的 Error Log。

在 `test.localhost` 跑 `bench --site test.localhost migrate`，回执贴补丁输出与 9 个单位的只读 SQL 结果；再 migrate 一次，确认 Patch Log 不重复。

---

## 任务 TS-028：测试与演示同条件（对应切片 SL-018）

### 目标

去掉测试里「临时把支设为整数」的写法，让测试在与演示站相同的单位属性下通过（审核报告 FD-001 建议②后半，裁决①时同样适用：根因是测试与演示条件不同）。

### 具体改动

1. 删除以下三处临时设定，改为在 `setUpClass`（或用例开头）断言 `frappe.db.get_value("UOM", "支", "must_be_whole_number") == 1`，不成立时报「先 migrate 使 s8_whole_number_count_uoms 生效」：
   - `tests/test_process_loss.py:11`（`TestProcessLoss.setUp`）
   - `tests/test_process_loss.py:137`（`TestProcessLossPlan._setup_loss_fixture`）
   - `tests/test_replenishment_rules.py:15`
   
   `test_process_loss.py:12` 把 `kg` 设 0 的那行保留（`kg` 不在本次范围，属测试自身前提）。
2. 其余用 `Nos` 的测试（`test_job_card_split`、`test_operation_flow`、`test_e2e_minimal`）不动。
3. **HT-028 探测用例**（新增于 `tests/test_process_loss.py`）：产品单位「支」、BOM 数量 1000、工序 3／1／1（整体值取 4.9）、工单 2103 支，全部 Job Card 报工损耗为 0 后做完工入库。断言写成「记录实际结果」：
   - 能提交 → 断言提交成功，并断言 `process_loss_qty` 为整数；
   - 被整数校验拦下 → 用 `@unittest.expectedFailure` 或 `assertRaises(UOMMustBeIntegerError)` 固定住现状，用例 docstring 写明「已知缺口，见 R09 回执未做项」。
   
   执行者先跑一次看实际行为再定写法，**不修上游行为**。

### 验证方式

`bench --site test.localhost run-tests --app frappe_china --module frappe_china.tests.test_process_loss`、`…test_replenishment_rules`、`…test_install` 全过；`grep -rn 'must_be_whole_number", 1' frappe_china/tests` 只剩 TS-027 的单位用例自己造的前提（如有），不再出现在 `test_process_loss.py`、`test_replenishment_rules.py`。回执写 HT-028 的实际结果。

---

## 任务 TS-029：生成器整数检查与第一段实跑（对应切片 SL-018）

### 目标

证明整数单位下生成器全链的「支」数量都是整数，并让 `verify` 以后能自动看出这类问题。

### 具体改动

1. `frappe_debug/scenario/verify.py` 的 `verify(sc)` 加一组检查 `integer_uom.<表>`：对场景公司、`posting_date` 或单据日期在场景窗口内的已提交单据，统计库存单位 `must_be_whole_number=1` 的数量字段里非整数的条数，期望 0。表与字段：
   - `Work Order.qty`、`Work Order.produced_qty`、`Work Order.process_loss_qty`
   - `Job Card.for_quantity`、`Job Card.total_completed_qty`、`Job Card.process_loss_qty`
   - `Stock Entry.fg_completed_qty`（Manufacture、Material Transfer for Manufacture）、`Stock Entry Detail.transfer_qty`（成品行）
   - `Production Plan Item.planned_qty`
   - `BOM.process_loss_qty`（场景 BOM）
   
   判式与原生同（`abs(cint(x) − flt(x, 精度)) > 1e-7`）；`detail` 给条数与最多 5 个单据名。用 SQL 聚合，不逐条 `get_doc`。
2. 生成器其余代码**不改**（§2.1：小数唯一来源在 `required_input_qty`）。若第 3 条实跑出现非整数，暂停反馈，不就地改生成器公式。

### 验证方式

1. `frappe_debug/tests/test_verify.py`（或现有 verify 用例文件）加一条：造一张小数 `qty` 的工单（单位「支」）→ `integer_uom.Work Order` 不通过、`detail` 含该单名；整数时通过。
2. **第一段实跑**（隔离站，不碰 `erx.localhost`）：按 R6 建 `s8dev` 的做法从清洁基准 `20261024_111641` 恢复一座临时站 `s8r9.localhost`，装同版本 app 并 migrate（补丁生效），scheduler 关；按 README「重做 SPC 候选计划」第 1 步以 `quality_preview: 1` 建工作库并切入，`runner.generate(S, D1−1, preview_quality_schedule=True)`。生成完：
   - 跑 `verify_current_scenario_summary()`，贴结果；`integer_uom.*` 全部通过；与本段无关、因只生成一段而不满足的检查（如全年计数、第 6／9 幕前置）如实列出，不算本任务失败；
   - 只读 SQL 复核：工单、Job Card、完工入库「支」非整数条数为 0；任取压簧、拉簧各一张工单，手算其 `qty` 等于对应订单待生产量的逐道 ceil 结果（压簧 3／1／1：5000→5051→5103→5261；拉簧 3／1：两道），写进回执；
   - 记生成耗时，与 R7 第一段（约 376～411 秒）对比。
3. 用完删除临时站的工作库与快照登记，撤回 `root_password`；临时站本身留不留，回执写明并交用户定。

---

## 任务 TS-030：fallback 工序成本按累计实际分摊（对应切片 SL-019）

### 目标

分批完工时各批附加费用之和等于累计实际工序成本；整单一次入库结果不变（需求 §4.7 成本完整性；用户裁决口径）。

### 具体改动

`frappe_china/accounting/stock_entry_accounts.py`：

```python
def fallback_operating_cost_share(...):   # §3.2，纯函数

def normalize_fallback_operating_cost(doc, method=None) -> None:
    if doc.purpose != "Manufacture" or not doc.work_order or doc.get("job_card"):
        return                                   # 上游带 job_card 时不加 fallback 行（bom.py:1842）
    rows = [r for r in doc.additional_costs if r.has_operating_cost and not r.operation_id and not r.operating_component]
    if not rows:
        return
    if len(rows) > 1:
        msgprint(黄色, "多于一行工序成本行，未按累计实际校正")；return   # 上游只加一行
    wo = frappe.get_doc("Work Order", doc.work_order)            # 不用 get_cached_doc（HT-026）
    if wo.track_semi_finished_goods:
        return                                   # 本方案不覆盖半成品跟踪口径
    if 多层 BOM 子装配路径（Manufacturing Settings.set_op_cost_and_secondary_items_from_sub_assemblies 且 wo.use_multi_level_bom）:
        return                                   # 上游为单位额，未放大（stock_entry.py:4498-4505）
    reported_ops = [op for op in wo.operations if flt(op.completed_qty)]
    cumulative_actual = Σ flt(op.actual_operating_cost) for op in reported_ops
    if not reported_ops or not cumulative_actual:
        return                                   # 上游走单位额分支（未报工 planned÷qty、BOM 退路），未放大
    planned_part = Σ flt(op.planned_operating_cost) / flt(wo.qty) × flt(doc.fg_completed_qty)
                   for op in wo.operations if not flt(op.completed_qty)          # 与上游同式，保留
    absorbed_amount, entered_qty = 本工单其它已提交 Manufacture 入库（docstatus=1、name != doc.name）上
                   fallback 行 Σamount 与表头 Σfg_completed_qty（一条 SQL：Stock Entry join Landed Cost Taxes and Charges，
                   parentfield='additional_costs'，子行条件同 rows；fg 之和按父单去重另取）
    reported_qty = min(flt(op.completed_qty) + flt(op.process_loss_qty) for op in reported_ops)   # HT-025
    share, over_absorbed = fallback_operating_cost_share(cumulative_actual, absorbed_amount, reported_qty, entered_qty, flt(doc.fg_completed_qty))
    if over_absorbed:
        msgprint(黄色, "本工单此前完工入库已记工序成本 {0}，超过累计实际 {1}，本次记 0；请核对历史入库单")   # 不静默
    row.amount = row.base_amount = flt(share + planned_part, precision)
```

要点：

1. 删掉现行「`divided` 比 `amount` 更接近就除」的启发式与 `get_cached_doc`；新算法只读库里状态，插入、提交两次 `before_validate` 结果相同。
2. 混合工序（部分已报工、部分未报工）只在半成品跟踪或绕过原生校验时出现，按上式保留上游的单位额部分，不另设计。
3. docstring 写明口径与 `SH-P1S8010` 的关系；注释说明为什么用 `completed_qty + process_loss_qty`（累计损耗口径，S7 TS-018）。
4. 新增中文提示两句进 `zh.csv`（源词英文、按开发守则），跑译名三件套。

### 验证方式

`tests/test_s8_accounting.py`：

1. 新增纯函数用例：SL-019 ① 的五组与 ② 的两种异常，期望值写死。
2. 既有三条 mock 用例（`…scaled_once_for_high_quantity_work_order`、`…not_divided_again_on_submit`、`…leaves_component_rows_and_other_purposes`）改为给 `work_order` 补 `completed_qty`、`process_loss_qty`、`track_semi_finished_goods`、`use_multi_level_bom`，并 patch 已吸收查询返回 `(0, 0)`、`frappe.get_doc` 返回该工单；期望值不变（5235.11、237.56、组件行与 Repack 不动）。回执逐条列「改了哪条、为什么」。
3. 新增集成用例 `test_partial_manufacture_absorbs_cumulative_actual_operating_cost`：沿用 `test_manufacture_capitalizes_operation_cost_without_profit_and_loss_entries` 的公司、物料、工位造法；BOM 一道工序、`cn_job_card_split_qty=5`，工单 10 支（HT-027）；提交第一张卡（时间行 30 分钟）→ 建并提交入库 5 → 提交第二张卡（60 分钟）→ 建并提交入库 5。断言：两张入库 fallback 行之和＝工单 `actual_operating_cost`（≤0.01）；第一张＝第一张卡的实际成本；GL 科目只在存货类与 `410199`。再取消第二张入库、重建提交，金额与取消前相同。
4. 新增：同一张草稿入库连续 `save()` 两次，金额不变。

`bench --site test.localhost run-tests --app frappe_china --module frappe_china.tests.test_s8_accounting` 全过。

---

## 任务 TS-031：全量回归与登记（对应全部切片）

### 具体改动

1. 全量：基线取 R8 修后回归（审核报告「修后回归」表）——`frappe_china` Python 471/471＋6＋4、`frappe_debug` Python 183/183、Node `frappe_debug` 98／`frappe_china` 115、两 app Ruff check／format、`bench build --app frappe_china --app frappe_debug`。用例数只增不减、全过。
2. 译名：`test_translation_quality`、`test_translations`、`translation_check.run` 两站。
3. `frappe_china/README.md`：「后端覆盖登记」或「LG-001」相关处（若有）更新 `normalize_fallback_operating_cost` 的口径说明；无对应节则在 D 回执写明未改。
4. 不在 `erx.localhost` 做任何写操作（含 migrate）。演示站 migrate 与整场预跑留到 SB 修完后一次做（审核报告「修复的连带面」、RS-006）。

### 验证方式

D 回执「全量验证」表贴各门实测数与基线对比。

---

## 八、执行顺序

```
TS-027 整数计数单位 ─ TS-028 测试同条件（含 HT-028 探测） ─ TS-029 verify 检查与第一段实跑
TS-030 fallback 工序成本（可与上一行并行）
                                   └──────────────┬──────────────┘
                                         TS-031 全量回归与登记
```

## 九、执行纪律（给执行者，随方案走）

1. **切片前反查**：见第五节表下指令。
2. **假设先验**：HT-025～027 在 TS-030 写实现前用集成用例先验；不成立按表中「不成立时」处理。HT-028 只探测不修。
3. **中断续跑**：开工即建 D 回执（按 `bricks/receipt.md`），TS-027～031 预填 `⬜未开始`，每个任务做完当场回写。执行进度不回写本方案。
4. **站点安全**：单测在 `test.localhost`；第一段实跑只在临时站 `s8r9.localhost`；不碰 `erx.localhost`。`root_password` 只用 `set-config` 写进临时站 `site_config.json`，用完撤回，回执只写「已设／已撤回」。
5. **测试纪律**：同原方案总纲 §十 第 5 条（`FrappeChinaTestCase`、`_FCT` 前缀、只删自己造的 Error Log、手算期望值写死）。
6. **不静默**：补丁的在途小数单据、已吸收超过累计实际，都要有输出或提示（开发守则「静默失败」）。
7. **不夹带**：生成器公式、`required_input_qty`、A18 规则都不改；第一段实跑若发现非整数或其它问题，暂停反馈。顺手发现的问题记进回执「未做项」或建议登记延迟需求。
8. **约定显式化**：「需要新站也生效的数据修正，补丁与 `after_install` 两条路都调同一个幂等函数」若被采用，记进 D 回执「新增约定」，由 Workflow 移交 `docs/开发守则.md`。
9. **版本管理**：不 commit、不 push、不打 tag，除非用户在对话里显式允许。
