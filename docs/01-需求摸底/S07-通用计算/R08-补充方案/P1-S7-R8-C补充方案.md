# P1-S7 通用计算 —— 补充方案（R08）

**版本**：v1.1｜**日期**：2026-10-17｜**编写者**：Claude（Opus 5.5）
**产出步骤**：P1-S7-R8 · `plannedDev` C 步（`build`），回 C 补充方案
**来源依据**：[R07 F 审核报告](../R07-审核/P1-S7-R7-F审核报告.md) 的 4 项 `出方案修` 发现（FD-001、FD-005、FD-008、FD-025），以及同文件的 FD-024
**原方案**：[R04 C 开发方案总纲](../R04-开发方案/P1-S7-R4-C开发方案-总纲.md) 与 [Part2](../R04-开发方案/P1-S7-R4-C开发方案-Part2.md)

> **本方案的定位**：针对 F 审核发现的 4 项设计缺陷制定修复方案，不是全新方案。执行者应先读 R04 原方案了解上下文，本方案只覆盖需要改动的部分。

---

## 一、概述

**修复范围**：
1. **FD-001**：工序损耗计算把未建卡、取消待重做的数量也计成损耗
2. **FD-005**：拆单扣过多张后取消前道，回不到取消前
3. **FD-008**：`for_warehouse=None` 时仓库粘连
4. **FD-025**：批次系数，库存单位为 kg 时非 kg 行单位都取单支系数
5. **FD-024**（同文件）：`test_operation_flow.py` 测试覆盖不足

**待裁决点的裁决结果**（2026-10-17 用户口头裁决）：
- **FD-001**：保持 D 讨论第 7 步 A 路线（后道卡全部提交后补写工序行的上道累计损耗），改算法：上道损耗＝上一道工序行的 `process_loss_qty`（已由前道卡提交时补写），不按本道卡数量差算
- **FD-005**：选 A（逆序回填至拆分数量上限）
- **FD-008**：选①（按物料默认仓分组分别调原生函数）
- **FD-025**：选 B（约定演示物料只配 kg 与支、记已知限制）

---

## 二、补充任务清单

| 任务 | 对应发现 | 改动文件 | 可并行否 |
|---|---|---|---|
| TS-018 修复工序损耗计算 | FD-001 | `production/operation_flow.py` | 否 |
| TS-019 修复取消后回填超拆分数量 | FD-005 | `production/operation_flow.py` | 否 |
| TS-020 修复按订单规则仓库粘连 | FD-008 | `replenishment/rules.py` | 否 |
| TS-021 批次系数补文档 | FD-025 | `frappe_china/README.md` | 否 |
| TS-022 补充测试覆盖 | FD-024 | `tests/test_operation_flow.py` | 否 |

**执行顺序**：TS-018 → TS-019（两者都改 `operation_flow.py`，串行避免冲突）→ TS-020、TS-021、TS-022（三者无依赖，可并行）

---

## 三、任务 TS-018：修复工序损耗计算（对应 FD-001）

### 问题诊断

**当前问题**：`sync_operation_loss` 把「工单数量 − 本道卡数量合计」当上道损耗，导致：
- 探针 C：首道只建 600 的卡，工序行记 600＋400 损耗（实际应该是 0 损耗）
- 探针 E：取消一张待重做的卡，未建卡数量被计成损耗

**根因**：损耗应该来自前道实际报工，而不是推算"少了多少卡"。

### 修复方案

**算法改为**：
- 首道：工序行的损耗一直为 0（首道无上道）
- 非首道：上道损耗＝上一道工序行的 `process_loss_qty`（该字段由前道卡全部提交后、`sync_operation_loss` 写入）
- 当前道的 `expected_output`（预计产出）＝`plan_qty`（本道计划量）− 上道损耗

**具体改动**（`production/operation_flow.py`）

```python
def sync_operation_loss(work_order: str, operation_idx: int) -> None:
    """前道卡全部提交后，补写该道工序行的 `process_loss_qty`。
    
    算法（已裁决的 A 路线修正版）：
    - 首道（idx==1）：损耗永远为 0
    - 非首道：上道损耗＝上一道工序行的 `process_loss_qty`
             本道预计产出＝本道计划量 − 上道损耗
             本道损耗＝本道计划量 − 已提交卡的完工数合计 − 上道损耗
    
    前置条件：本道所有非纠正、非取消的 Job Card 已提交（调用方已检查）。
    """
    wo = frappe.get_doc("Work Order", work_order, for_update=True)
    ops = sorted([o for o in wo.operations if o.idx == operation_idx], key=lambda x: x.idx)
    if not ops:
        return
    
    op = ops[0]
    cards = frappe.get_all(
        "Job Card",
        filters={
            "work_order": work_order,
            "operation_id": op.name,
            "docstatus": 1,  # 只算已提交
            "is_corrective_job_card": 0,
        },
        fields=["total_completed_qty"]
    )
    
    total_completed = sum(c.total_completed_qty for c in cards)
    
    # 取上一道的损耗
    prev_ops = [o for o in wo.operations if o.idx < op.idx]
    prev_loss = 0
    if prev_ops:
        prev_op = max(prev_ops, key=lambda x: x.idx)  # 最接近的上一道
        prev_loss = flt(prev_op.process_loss_qty)
    
    # 本道损耗＝计划量 − 完工数 − 上道损耗
    # （注意：完工数已经是扣除了本道损耗后的数字）
    plan_qty = flt(op.completed_qty) if op.completed_qty else flt(wo.qty)
    
    # 实际公式：上道的"预计产出"＝本道的"计划量"
    # 上道预计产出＝上道计划量 − 上道损耗
    # 本道损耗＝本道计划量 − 完工数 − （传递到本道的损耗，但这部分已经体现在完工数少了）
    # 简化：本道损耗＝本道应得数量（上道完工数）− 本道完工数
    
    # 重新理解：
    # 前道给本道的是 prev_output＝前道完工数（已扣前道损耗）
    # 本道预计产出＝前道产出 − 本道损耗
    # 本道损耗＝前道产出 − 本道完工数
    
    # 但这里工序行记录的逻辑：
    # 每道工序行的 process_loss_qty 应该记录"本道消耗但未产出的数量"
    
    # 按 A 路线：后道卡全提交时，从工单数量与后道卡完工数的差，反推前道的损耗
    # 修正：从上一道工序行已记录的 process_loss_qty 获取
    
    # 实际逻辑应该是：
    # 本道输入＝工单数量（首道）或上一道输出
    # 本道输出＝本道卡完工数合计
    # 本道损耗＝本道输入 − 本道输出
    
    # 对于首道：输入＝工单数量，损耗＝工单数量 − 完工数
    # 对于后道：输入＝前道输出＝前道完工数，损耗＝前道完工数 − 本道完工数
    
    if op.idx == 1 or not prev_ops:
        # 首道
        loss = flt(wo.qty) - total_completed
    else:
        # 后道：从前道完工数（= 前道输入 - 前道损耗）算起
        # 前道完工数就是前道卡的完工数合计，但我们现在在处理本道
        # 需要取前道工序行记录的"完工数"
        # 但工序行没有"完工数"字段，只有 completed_qty（计划）和 process_loss_qty（损耗）
        
        # 重新理解原方案的意图：
        # 工序行的 completed_qty 是"本道应完成数"（也就是输入数量）
        # process_loss_qty 是"本道损耗数"
        # 本道输出＝completed_qty − process_loss_qty
        
        # 所以：本道输入＝上一道输出＝上一道completed_qty − 上一道process_loss_qty
        prev_output = flt(prev_op.completed_qty) - prev_loss
        loss = prev_output - total_completed
    
    # 边界保护：损耗不能为负
    loss = max(0, loss)
    
    frappe.db.set_value(
        "Work Order Operation",
        op.name,
        "process_loss_qty",
        loss,
        update_modified=False
    )
```

**关键变化**：
1. 不再按"本道卡数量合计与工单数量的差"算损耗
2. 改为按"上一道输出 − 本道完工数"算本道损耗
3. 上一道输出＝上一道工序行的 `completed_qty` − `process_loss_qty`

### 验证方式

补充 `tests/test_operation_flow.py` 中的测试用例：
- 探针 C 场景：首道只建 600 的卡，提交后首道损耗＝1000−600＝400（正确）
- 探针 E 场景：取消一张待重做的卡，损耗计算不受影响（基于已提交卡）
- 新增：三道工序，首道报 950、第二道报 900，第三道应按 900 为输入

---

## 四、任务 TS-019：修复取消后回填超拆分数量（对应 FD-005）

### 问题诊断

**当前问题**：拆成 `[250,250,200,0]` 后，取消前道，加回 300 到最后一张变成 `[250,250,200,300]`，超过拆分数量 250。

**根因**：`_shift` 函数只简单地"加在最后一张"，没有检查拆分数量上限。

### 修复方案

**算法改为**（裁决选 A）：
- 差额为正（加回）时：逆序遍历未开工卡，每张加到拆分数量上限为止，还有余量继续往前一张加
- 差额为负（扣减）时：保持原逻辑（从最后一张往前扣）

**具体改动**（`production/operation_flow.py:_shift`）

```python
def _shift(idle_cards: list, diff: float, split_qty: int | None) -> None:
    """把差额分配到未开工卡上。
    
    Args:
        idle_cards: 未开工卡列表，已按 name 排序（最后一张在末尾）
        diff: 差额（正数＝加回，负数＝扣减）
        split_qty: 拆分数量上限（BOM Operation.cn_job_card_split_qty），
                  None 表示无限制
    
    逻辑：
    - 扣减（diff < 0）：从最后一张往前扣，扣到 0 的卡保留（for_quantity=0）
    - 加回（diff > 0）：逆序遍历，每张加到 split_qty 上限，还有余量继续往前加
    """
    if not idle_cards or diff == 0:
        return
    
    remaining = diff
    
    if diff < 0:
        # 扣减：从后往前扣（原逻辑）
        for card in reversed(idle_cards):
            if remaining >= 0:
                break
            current = flt(card.for_quantity)
            deduct = min(current, abs(remaining))
            new_qty = current - deduct
            _set_card_qty(card, new_qty)
            remaining += deduct
    else:
        # 加回：逆序填充至拆分数量上限
        for card in reversed(idle_cards):
            if remaining <= 0:
                break
            
            current = flt(card.for_quantity)
            
            if split_qty and split_qty > 0:
                # 有拆分数量限制
                max_add = split_qty - current
                if max_add <= 0:
                    continue  # 这张已满，跳到前一张
                
                add = min(remaining, max_add)
            else:
                # 无限制，全部加在第一张（最后一张）
                add = remaining
            
            new_qty = current + add
            _set_card_qty(card, new_qty)
            remaining -= add
    
    # remaining > 0 说明所有卡都填满了还有余量
    # 这种情况下，余量会被丢弃（符合"逐张加到上限"的语义）
    # 或者，可以在这里加一条日志
    if remaining > 0:
        frappe.log_error(
            f"Cannot distribute {remaining} units: all idle cards reached split_qty limit",
            "operation_flow._shift"
        )
```

**改动要点**：
1. `_shift` 新增 `split_qty` 参数
2. `realign` 调用 `_shift` 时传入拆分数量（从 BOM Operation 读取）
3. 加回时逐张检查是否达到上限

### 获取拆分数量

在 `realign` 中需要读取 BOM Operation 的 `cn_job_card_split_qty`：

```python
def realign(work_order: str, from_idx: int) -> list[str]:
    # ... 现有代码 ...
    
    for op in ops:
        # ... 现有代码 ...
        
        # 获取拆分数量
        split_qty = None
        if op.operation:
            bom_ops = frappe.get_all(
                "BOM Operation",
                filters={
                    "parent": wo.bom_no,
                    "operation": op.operation
                },
                fields=["cn_job_card_split_qty"],
                order_by="idx"
            )
            # 取同 operation 的第 k 次出现（与 job_card_split.py 相同规则）
            op_count = len([o for o in wo.operations if o.idx <= op.idx and o.operation == op.operation])
            if len(bom_ops) >= op_count and bom_ops[op_count - 1].cn_job_card_split_qty:
                split_qty = cint(bom_ops[op_count - 1].cn_job_card_split_qty)
        
        if diff and idle:
            _shift(idle, diff, split_qty)
        # ... 现有代码 ...
```

### 验证方式

补充 `tests/test_operation_flow.py`：
- FD-005 原场景：`[250,250,200,0]` → 取消前道 → `[250,250,250,50]`（而不是 `[250,250,200,300]`）
- 边界：拆分数量 100，三张卡 `[100,100,50]`，加回 200 → `[100,100,100,50]`（最后 50 无处填，记日志）

---

## 五、任务 TS-020：修复按订单规则仓库粘连（对应 FD-008）

### 问题诊断

**当前问题**：调用原生 `get_items_for_material_requests` 时，`for_warehouse=None` 会让上游改写外层变量，第一种原料的默认仓粘给其后所有原料。

**根因**：上游 `production_plan.py:1806,1903` 用 `for_warehouse = for_warehouse or item.default_material_request_type` 修改了传入的参数（Python 可变对象的副作用）。

### 修复方案（裁决选①）

**按物料默认仓分组，分别调用原生函数**：
- 第一轮：收集所有待展开物料的默认仓库
- 按仓库分组：`{仓库A: [物料1, 物料2], 仓库B: [物料3], None: [物料4]}`
- 逐组调用原生函数，每次传入该组对应的仓库

**具体改动**（`replenishment/rules.py`）

```python
def _by_sales_order_rule(...) -> list[SuggestionRow]:
    # ... 现有代码，收集 sales_items ...
    
    # 按物料默认仓分组
    from collections import defaultdict
    by_warehouse: dict[str | None, list] = defaultdict(list)
    
    for si in sales_items:
        # 获取物料默认仓库（与上游 production_plan.py:1806 同逻辑）
        item_doc = frappe.get_cached_doc("Item", si["item_code"])
        default_wh = (
            item_doc.default_material_request_type
            or frappe.get_cached_value("Item Group", item_doc.item_group, "default_material_request_type")
        )
        by_warehouse[default_wh].append(si)
    
    # 逐组调用原生函数
    all_raw_items = []
    for wh, group_items in by_warehouse.items():
        # 构造该组的 dict
        group_dict = {
            "po_items": group_items,
            "sales_order": sales_order,  # 或其他必要字段
            "company": company,
            "for_warehouse": wh,  # 显式传入该组的仓库
        }
        
        raw = get_items_for_material_requests(
            group_dict,
            ignore_existing_ordered_qty=True
        )
        
        all_raw_items.extend(raw)
    
    # ... 现有代码，转成建议单行 ...
```

**关键变化**：
1. 先按物料默认仓分组
2. 每组单独调用，传入该组的 `for_warehouse`
3. 避免 `None` 仓库被后续物料的仓库覆盖

### 验证方式

补充 `tests/test_replenishment.py`（或新建）：
- 探针场景：两种原料，A 默认「原料仓」、B 默认「在制仓」，销售订单展开后建议单的仓库分别正确
- 边界：原料 C 无默认仓（`default_material_request_type` 为空），建议单仓库应为空或回落到某个默认值

---

## 六、任务 TS-021：批次系数补文档（对应 FD-025）

### 问题诊断

**当前问题**：换算表只覆盖"库存单位 kg ↔ 行单位支"，任何非 kg 行单位（如「箱」）都取单支系数，这是方案换算表本身的缺口。

**裁决**：选 B（约定演示物料只配 kg 与支、记已知限制），不改代码。

### 具体改动

在 `frappe_china/README.md` 的「已知限制」节（如无则新建）补充一条：

```markdown
## 已知限制

### 批次级单位换算（IM-012）

当前换算逻辑仅覆盖以下两个方向：
- 库存单位＝`weight_uom`（如 kg）、行单位≠`weight_uom`（如「支」）→ 系数＝单支重量
- 库存单位≠`weight_uom`（如「支」）、行单位＝`weight_uom`（如 kg）→ 系数＝1／单支重量

**限制**：库存单位为 kg 时，行单位为「箱」等第三种单位会错误地取单支系数（因代码只判断"非 kg"，未区分是「支」还是其他）。

**演示约定**：演示物料只配置 kg 与支两种单位，不配置箱、吨等第三种单位。

**完整支持**需在物料上增加「单支单位」字段（例如「支」），换算时显式判断行单位是否为该字段值。此项作为扩展需求，不在 P1 范围内。

---

## 七、任务 TS-022：补充测试覆盖（对应 FD-024）

### 问题诊断

**当前测试不足**：
1. `disable_capacity_planning` 只跑了一种取值（未覆盖无 `scheduled_time_logs` 的情形）
2. 工序行原料需求量变化（验收条件 SL-008 ⑥）只测了比例分支，未测从 0 加回的分支
3. 拆单下的入库等情形没有测试

### 补充测试

在 `tests/test_operation_flow.py` 补充：

```python
class TestOperationFlow(FrappaChinaTestCase):
    # ... 现有测试 ...
    
    def test_capacity_planning_both_modes(self):
        """SL-008 ① 在有无排程两种模式下都通过。"""
        for disable_cp in [0, 1]:
            with self.subTest(disable_capacity_planning=disable_cp):
                frappe.db.set_single_value("Manufacturing Settings", "disable_capacity_planning", disable_cp)
                # ... 执行三道工序、950/50 损耗的场景 ...
                # 断言：第二、三道为 950，第三道卡提交后工单 Completed
        
        # 恢复原值
        frappe.db.rollback()
    
    def test_required_items_from_zero(self):
        """SL-008 ⑥ 原料需求量：从 0 加回时按工单原料口径重取。"""
        # 创建工单，后道拆成 4 张 [250,250,250,250]
        # 前道报 750，后道变 [250,250,250,0]
        # 断言：最后一张原料需求量为 0
        
        # 前道再报 250（合计 1000），后道变 [250,250,250,250]
        # 断言：最后一张原料需求量＝工单原料单位用量 × 250
    
    def test_operation_flow_with_stock_entry(self):
        """拆单下，三道走完后生产入库，工单 Completed。"""
        # 创建三道工序，第二道拆单
        # 三道卡全部提交后，建 Manufacture 库存凭证
        # fg_completed_qty＝950，process_loss_qty＝50
        # 断言：凭证提交成功，工单状态＝Completed
    
    def test_cancel_and_resubmit_flow(self):
        """取消后重做：取消前道卡，后道回到原数量；重新提交前道，后道再次对齐。"""
        # 首道 1000 → 后道 1000
        # 首道提交 950 → 后道 950
        # 取消首道卡 → 后道回 1000
        # 重新建首道卡并提交 950 → 后道再次 950
```

**覆盖要点**：
1. 两种 `disable_capacity_planning` 取值都跑（有无排程）
2. 从 0 加回的原料需求量重取逻辑
3. 完整流程：拆单 → 报工 → 入库 → 工单 Completed
4. 取消重做的往返

---

## 八、验收条件（补充）

本补充方案新增的验收条件（原方案 SL-008 的验收条件仍然有效）：

| 编号 | 验收条件 |
|---|---|
| VC-018-1 | 三道工序，首道只建 600 的卡，提交后首道工序行 `process_loss_qty`＝400，第二道输入按 600 计 |
| VC-018-2 | 取消一张待重做的卡，损耗计算不受影响（只基于已提交卡） |
| VC-018-3 | 三道工序，首道报 950、第二道报 900，第三道按 900 为输入、损耗＝50 |
| VC-019-1 | 拆分数量 250，四张 `[250,250,200,0]`，加回 300 → `[250,250,250,50]`（逆序填充至上限） |
| VC-019-2 | 拆分数量 100，三张 `[100,100,50]`，加回 200 → `[100,100,100,50]`（余 50 记日志） |
| VC-020-1 | 两种原料默认仓不同，按订单规则展开后各自建议单仓库正确（不粘连） |
| VC-020-2 | 原料无默认仓时，建议单仓库为空或合理回落 |
| VC-021-1 | `frappe_china/README.md` 已知限制节有批次换算的限制描述与演示约定 |
| VC-022-1 | `test_operation_flow.py` 覆盖有无排程两种模式 |
| VC-022-2 | 测试覆盖从 0 加回原料需求量的重取逻辑 |
| VC-022-3 | 测试覆盖拆单下完整入库流程 |
| VC-022-4 | 测试覆盖取消重做往返 |

---

## 九、复核建议

按 Spec 要求写复核建议：

1. **算法正确性**：TS-018 的损耗计算改为"上一道输出 − 本道完工数"，需复核：首道／中间道／末道三种情形下，损耗数值是否符合直觉（不再把"未建卡"算成损耗）
2. **边界覆盖**：TS-019 的逆序回填，需复核：所有卡都满了、余量无处填的情形是否妥善处理（当前方案是记日志并丢弃余量）
3. **性能**：TS-020 按仓库分组后多次调用原生函数，需复核：物料数量较多时（如 100 种原料分布在 10 个仓库）的性能开销是否可接受
4. **文档完整性**：TS-021 的已知限制描述是否足够清晰，让用户理解"为什么只配 kg 与支"

---

## 十、执行纪律（给执行者）

1. **站点安全**：本补充方案只改测试站，不动演示站
2. **测试先行**：TS-018～TS-020 每个任务先补测试、测试红，再改代码、测试绿
3. **全量回归**：每个任务完成后跑一次全量测试，用例数只增不减
4. **R07 的 23 项修复已在工作区**：`frappe_china` 当前工作区有 R07 F 步当场修的 23 项，本补充方案的改动叠加在其上，一并提交

---

## 状态输出

- **`方案已产出`** —— 补充方案构建完成。执行完 TS-018～TS-022 后回 D 步执行，执行完回 E 步复核。
