# P1-S2-R2-A 复核：Routing 工时模型（batch_size / fixed_time / 工序间数量）

源码：`frappe-bench/apps/erpnext`（ERPNext 16.35.0），纯读码，未实跑。

## ① 三条判定

| 记载 | 判定 | 一句话 |
|---|---|---|
| A：`Routing` 无基准量 | **不成立**（须改写） | `BOM Operation.batch_size`（默认 1，Float）就是工时基准量，且在 `work_order.py:1491-1497` 被真实消费——启用后 `time_in_mins ÷ batch_size` 得单件工时，"每 100 件耗时 X" 可直接表达；缺陷不在"没有基准量"，而在**它被 `Operation.create_job_card_based_on_batch_size` 这一个开关同时绑定了"任务单拆批"**。 |
| B：`fixed_time` 两档不能相加 | **部分成立** | "**单行内**固定与线性二选一、不相加"成立（`work_order.py:1550`）；但"表达不了 20 分换型 + 每支 0.05 分"**不成立**——Routing 拆两行（一行 `fixed_time=1, 20`，一行 `fixed_time=0, 0.05`）原生即为 20 + 0.05×qty。`setup_time` Custom Field 与改 `calculate_time()` **非必需**。 |
| LG-040：`for_quantity` 不从上道净产出算 | **成立** | `work_order.py:2969` `qty = row.job_card_qty or work_order.qty`，而 `job_card_qty` 仅由批量拆分决定（`:2902-2910`），与前道 `completed_qty` / `process_loss_qty` 无任何关联。 |

## ② batch_size 与工时计算的实际机制（读码所得）

**字段（`bom_operation.json:142-149`）**：
```json
{"default": "1", "fetch_from": "operation.batch_size", "fetch_if_empty": 1,
 "fieldname": "batch_size", "fieldtype": "Float", "label": "Batch Size", "non_negative": 1}
```
无 description；位于 `costing_section`（`field_order` 中紧随 `base_hour_rate`）。上游 `Operation.batch_size` 是 Int，且 `depends_on: create_job_card_based_on_batch_size`——**上游界面上默认不可见**。

**全部消费点**（`grep -rn batch_size erpnext/manufacturing/`，剔除同名局部变量 `bom_update_log.py:192`）：

1. `bom.py:1058-1059`　`row.cost_per_unit = row.operating_cost / (row.batch_size or 1.0)`
2. `bom.py:1022-1023`　仅当行上勾了 `set_cost_based_on_bom_qty`：`operating_cost = cost_per_unit × BOM.quantity`
3. `bom.py:1331-1332` / `work_order.py:1678-1679`　`batch_size <= 0` 时兜底为 1
4. **`work_order.py:1490-1497`（工时核心）**：
```python
if not d.fixed_time:
    if frappe.get_value("Operation", d.operation, "create_job_card_based_on_batch_size"):
        qty = d.batch_size            # ← 否则 qty = BOM.quantity（:1523）
    if exploded: d.time_in_mins *= flt(qty)
    else:        d.time_in_mins /= flt(qty)
```
5. `work_order.py:2902-2910` `split_qty_based_on_batch_size()`：定 `job_card_qty`，即任务单拆批

**完整公式**（BOM → Work Order）：
```
单件工时 = BOM.time_in_mins / B        B = batch_size（开关开）或 BOM.quantity（开关关）
WO 行工时 = 单件工时 × WO.qty          （calculate_time, work_order.py:1548-1551）
fixed_time=1 → 上面两步全跳过，time_in_mins 原样透传
成本 = hour_rate × time_in_mins / 60   （bom.py:1056；routing.py:38）
```
**测试佐证**：`test_work_order.py:712-757` `test_operation_time_with_batch_size`——`time_in_mins=40, batch_size=5`，WO qty=1 → 8.0，qty=5 → 40.0。即 `batch_size` **确为 MRP II 意义上的基准量**，不是子装配批量。

**`time_in_mins` 语义**：BOM/Routing 上存的是"**做 B 件的总时间**"（B 见上），不是单件时间；`Work Order Operation.time_in_mins` 才是整批时间。`Job Card.time_required = time_in_mins / WO.qty × job_card_qty`（`work_order.py:2987`）。

**`Routing` 结构**：`routing.json` 仅三字段 `routing_name` / `disabled` / `operations`（Table → `BOM Operation`），**Routing 自身确无 quantity 字段**。`routing.py:34-40 calculate_operating_cost()` 只算 `hour_rate × time_in_mins / 60`，**完全不看 `batch_size`**——Routing 层的成本预览按"整批"口径，不除基准量。

## ③ 记载 A 当初为何判错（推断，标注依据）

三个叠加原因，都指向"字段在界面上等于不存在"：

1. **上游 `Operation.batch_size` 带 `depends_on: create_job_card_based_on_batch_size`**（`operation.json:70`），不勾开关根本不显示；
2. **`BOM Operation.batch_size` 落在 `costing_section`（成本节），不在 `time_in_mins` 旁边**，且 label 只叫 "Batch Size"、**无 description**——从工时视角看不出它是工时基准；
3. **工时路径上它被 `create_job_card_based_on_batch_size` 门控**（`work_order.py:1491`）：开关名字讲的是"任务单"，讲的不是工时。不勾则基准量退回 `BOM.quantity`——这正是"全厂共用同一 BOM 基准量"那个观察的来源，**该观察对默认路径是对的，错在把它当成了唯一路径**。

记载 A 应改写为：`batch_size` 存在且有效，真缺口是**"工时基准量"与"任务单拆批粒度"共用一个开关，不能只要前者**（每 100 件 X 分 → 被迫每 100 支开一张任务单）。这是耦合缺陷，不是能力缺失，量级远小于原判。符合 LG-021 的"范围缩小"方向。

## ④ 拿不准 / 未实跑

- **未实跑**：全部结论来自读码＋单测代码，未起 bench、未在 UI 上验证 `batch_size` 是否真的可编辑（`BOM Operation` 侧无 `depends_on`，读码上应可见于成本节网格，但网格默认列由 `in_list_view` 定，`batch_size` **无** `in_list_view`，须展开行编辑才看得到）。
- **记载 B 的两行方案未实跑**：`bom.py:1340` 要求每行 `time_in_mins > 0`、`:1334` 要求有 workstation，两行都满足即可；但"两行 ⇒ 两张 Job Card"的车间可用性（可用同 `sequence_id` 并行，`bom_operation.json:152` 有说明）未验证，也未验证换型行 `fixed_time` 在 `exploded`（多级 BOM）路径下是否仍原样透传——`work_order.py:1519` 的 exploded 分支同样受 `if not d.fixed_time` 保护，读码上应透传。
- **`setup_time`**：`grep -rn "setup_time\|setup_mins" erpnext/` **零命中**，原生确无此字段——记载 B 这半句成立。
- **`process_loss_qty` 数据流**（记载"字段有但链不通"，**成立**，但有一处需修正）：字段在 `BOM`、`BOM Secondary Item`、`Job Card`、`Work Order`、`Work Order Operation` 上均存在（`BOM Operation` 上**没有**）。流向：`Job Card.process_loss_qty` → `job_card.py:1073` 写入 `WO Operation.process_loss_qty` → `work_order.py:938-940` 汇总为 `WO.process_loss_qty`（仅 `track_semi_finished_goods=1` 时按工序汇总，否则从 Stock Entry 汇总）。**修正**：在 `track_semi_finished_goods` 下，半成品入库数量 **确实**扣了损耗（`job_card.py:1742` `get_qty_to_produce() - manufactured_qty - consumed_process_loss`），即**库存层通了**；不通的是**计划层**——`create_job_card` 仍给每道工序发 `WO.qty`，下游任务单的 `for_quantity` 不随上游损耗缩减。故 LG-040 与本条是同一个缺口的两面。
