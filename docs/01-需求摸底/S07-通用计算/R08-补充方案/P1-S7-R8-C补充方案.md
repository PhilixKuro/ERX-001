# P1-S7 通用计算 —— 补充方案（R08）

**版本**：v1.2｜**日期**：2026-10-17｜**编写者**：Claude（Opus 5.5）
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
- 首道：只记录已提交卡自身的实际损耗；没有卡上损耗时为 0，不把未建卡数量视为损耗
- 非首道：本道累计损耗＝上道工序行的累计 `process_loss_qty`＋本道已提交卡自身的实际损耗
- 不从未建卡、取消卡或卡数量差额推导损耗；`completed_qty` 保持原生汇总的已提交卡实际完工量

**具体改动**（`production/operation_flow.py`）

```python
def sync_operation_loss(work_order: str) -> None:
    wo = frappe.get_doc("Work Order", work_order)
    if wo.track_semi_finished_goods:
        return  # 原生半成品口径按各道自身损耗求和
    previous_loss = 0
    for op in sorted(wo.operations, key=lambda row: row.idx):
        cards = _operation_cards(work_order, op.name)  # 排除取消、纠正卡
        if not cards or any(c.docstatus == 0 and c.for_quantity for c in cards):
            previous_loss = flt(op.process_loss_qty)
            continue  # 有正数量草稿时保留原生值，不从缺卡推算
        loss = previous_loss + sum(flt(c.process_loss_qty) for c in cards if c.docstatus == 1)
        # 按字段精度写入累计损耗；按 completed_qty + loss 与工单数量更新原生状态
        # completed_qty 是原生汇总的已提交卡实际完工量
        previous_loss = loss
```

**关键变化**：
1. 不再按"本道卡数量合计与工单数量的差"算损耗
2. 保留已提交卡的实际损耗，并累加上一道工序行的累计损耗
3. 未建卡和取消卡不贡献损耗

### 验证方式

补充 `tests/test_operation_flow.py` 中的测试用例：
- 探针 C 场景：首道只建 600 的卡且卡上无实际损耗，提交后首道累计损耗＝0
- 探针 E 场景：取消一张待重做的卡，损耗计算不受影响（基于已提交卡）
- 新增：三道工序，首道报 950、第二道报 900，第三道应按 900 为输入

---

## 四、任务 TS-019：修复取消后回填超拆分数量（对应 FD-005）

### 问题诊断

**当前问题**：拆成 `[250,250,200,0]` 后，取消前道，加回 300 到最后一张会超过拆分数量上限。

**根因**：`_shift` 函数只简单地"加在最后一张"，没有检查拆分数量上限。

### 修复方案

**算法改为**（裁决选 A）：
- 差额为正（加回）时：逆序遍历未开工卡，每张加到拆分数量上限为止，还有余量继续往前一张加
- 差额为负（扣减）时：保持原逻辑（从最后一张往前扣）

**具体改动**（`production/operation_flow.py:_shift`）

复用现有 `_set_card_qty(card, new_qty, work_order)` 同步数量、工时、原料需求量和排程；保留扣到0的草稿卡。

```python
def _shift(cards, diff, work_order, split_qty=None):
    # diff < 0：保留原有逆序扣减逻辑
    # diff > 0：按卡名逆序，每张最多加 split_qty - current
    # 无正上限：全部加给最后一张
    # 余量 > 0：frappe.log_error，既不新增卡，也不声称已完全对齐
    ...
```

**上限映射**：`realign` 仅在 Operation 勾选 `create_job_card_based_on_batch_size` 时使用上限，复用 `job_card_split._bom_operation_split_qty(wo, operation)`，与建卡入口一致。该函数按工序所属BOM及同名工序在该BOM中的第k次出现匹配，避免重复实现主BOM映射。未勾选或上限非正数，沿用不限额回填。

### 验证方式

补充 `tests/test_operation_flow.py`：
- FD-005 原场景：`[250,250,200,0]` → 取消前道、加回 300 → `[250,250,250,250]`
- 边界：拆分数量 100，三张卡 `[100,100,50]`，加回 200 → `[100,100,100]`，余 150 无处填，记日志且不新增卡

---

## 五、任务 TS-020：修复按订单规则仓库粘连（对应 FD-008）

### 问题诊断

**当前问题**：调用原生 `get_items_for_material_requests` 时，`for_warehouse=None` 会让上游改写外层变量，第一种原料的默认仓粘给其后所有原料。

**根因**：上游 `production_plan.py:1903` 在展开后的原料循环中让外层 `warehouse` 首次取值后持续复用，导致不同原料的默认仓互相粘连；`default_material_request_type` 是请购类型，不是仓库。

### 修复方案（裁决选①）

**先展开原料，再按原料公司默认仓分组，分别调用原生函数**：
- 第一轮：按销售订单/BOM 得到展开后的原料行
- 读取每个原料在该公司的 `Item Default.default_warehouse`
- 按仓库分组：`{仓库A: [原料1], 仓库B: [原料2], None: [原料3]}`
- 逐组调用原生函数；无默认仓的行按现有约定报告问题、不出建议

**具体改动**（`replenishment/rules.py`）

```python
# order_proposals：保留原销售待生产量与 select_bom 逻辑
for source in po_items:
    details = get_exploded_items({}, company, source["bom_no"], 0,
                                 planned_qty=source["planned_qty"])
    for code, detail in details.items():
        # detail.default_warehouse 来自该公司 Item Default
        # 缺仓：加入 problems，不进入建议计算
        # 有仓：构造无BOM原料行（item_code、required_qty、sales_order、include_exploded_items=0）
        # required_qty 使用 detail.qty（库存单位），按默认仓分组
        ...
for warehouse, raw_rows in by_warehouse.items():
    rows = get_items_for_material_requests({
        "company": company, "po_items": raw_rows, "for_warehouse": warehouse,
        "ignore_existing_ordered_qty": 1, "include_non_stock_items": 0,
        "include_subcontracted_items": 1, "include_safety_stock": 0,
        "consider_minimum_order_qty": 0,
    })
    # 保留勾选过滤、数量×采购换算系数、建议汇总与销售来源归集
```

**关键变化**：先展开原料，再按原料公司默认仓分别显式传 `for_warehouse`；不向原生API传不存在的关键字参数。默认仓缺失时报告问题，不用成品仓、BOM来源仓或物料组仓兜底。原生函数仍负责采购单位换算与原有计算口径。

### 验证方式

补充 `tests/test_replenishment.py`（或新建）：
- 探针场景：两种原料，A 默认「原料仓」、B 默认「在制仓」，销售订单展开后建议单的仓库分别正确
- 边界：展开后的原料 C 无公司默认仓，报告问题且不出建议

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
```

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
class TestOperationFlow(FrappeChinaTestCase):
    # ... 现有测试 ...
    
    def test_capacity_planning_both_modes(self):
        """SL-008 ① 在有无排程两种模式下都通过。"""
        for disable_cp in [0, 1]:
            with self.subTest(disable_capacity_planning=disable_cp):
                frappe.db.set_single_value("Manufacturing Settings", "disable_capacity_planning", disable_cp)
                # ... 执行三道工序、950/50 损耗的场景 ...
                # 断言：第二、三道为 950，入库后工单 Completed（任务卡全部提交本身不等于工单完成）
        
        # 恢复原值
        frappe.db.rollback()
    
    def test_required_items_from_zero(self):
        """SL-008 ⑥ 原料需求量：从 0 加回时按工单原料口径重取。"""
        # 创建工单，后道拆成 4 张 [250,250,250,250]
        # 前道报 750，后道变 [250,250,250,0]
        # 断言：最后一张原料需求量为 0
        
        # 取消首道卡、释放其损耗，后道恢复 [250,250,250,250]
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
| VC-018-1 | 首道只建 600 的卡且卡上无实际损耗，提交后首道工序行累计 `process_loss_qty`＝0；未建卡数量不算损耗 |
| VC-018-2 | 取消一张待重做的卡，损耗计算不受影响（只基于已提交卡） |
| VC-018-3 | 1000→950→900→900 的三道工序，工序行累计损耗依次为 50、100、100；取消/未建卡不被推成损耗 |
| VC-019-1 | 拆分数量 250，四张 `[250,250,200,0]`，加回 300 → `[250,250,250,250]`（逆序填充至上限） |
| VC-019-2 | 拆分数量 100，三张 `[100,100,50]`，加回 200 → `[100,100,100]`，余 150 记日志且不新增卡 |
| VC-020-1 | 先展开原料；两种原料公司默认仓不同，按订单规则展开后各自建议单仓库正确（不粘连） |
| VC-020-2 | 展开后的原料无公司默认仓时，按现有约定报告问题、不出建议 |
| VC-021-1 | `frappe_china/README.md` 已知限制节有批次换算的限制描述与演示约定 |
| VC-022-1 | `test_operation_flow.py` 覆盖有无排程两种模式 |
| VC-022-2 | 测试覆盖从 0 加回原料需求量的重取逻辑 |
| VC-022-3 | 测试覆盖拆单下完整入库流程 |
| VC-022-4 | 测试覆盖取消重做往返 |

---

## 九、复核建议

按 Spec 要求写复核建议：

1. **算法正确性**：TS-018 的损耗计算保留卡上实际损耗并累加上道累计值，需复核：首道／中间道／末道三种情形下，损耗数值是否符合原生累计语义（不再把"未建卡"算成损耗）
2. **边界覆盖**：TS-019 的逆序回填，需复核：所有卡都满了、余量无处填的情形是否妥善处理（当前方案是记日志并丢弃余量）
3. **性能**：TS-020 按仓库分组后多次调用原生函数，需复核：物料数量较多时（如 100 种原料分布在 10 个仓库）的性能开销是否可接受
4. **文档完整性**：TS-021 的已知限制描述是否足够清晰，让用户理解"为什么只配 kg 与支"

---

## 十、执行纪律（给执行者）

1. **站点安全**：本补充方案只改测试站，不动演示站
2. **测试先行**：TS-018～TS-020 每个任务先补测试、测试红，再改代码、测试绿
3. **全量回归**：每个任务完成后跑一次全量测试，用例数只增不减
4. **R07 的23项修复已提交**：本轮基线 app `a091cd7`；新改动叠加在该基线上。D步不要求提交，提交/推送另需用户明确授权。

---

## 状态输出

- **`方案已产出`** —— 补充方案构建完成。交由 D 步执行 TS-018～TS-022，执行完回 E 步复核。

## R9修订说明

2026-10-17 用户选择A，授权修正并继续：TS-018 只累加卡实际损耗及前道累计损耗；TS-019 两个数量例与余量日志；TS-020 先展开原料再分仓。同步修正原生字段含义、API签名及伪代码与既有函数的衔接，不重做原设计裁决。详见R9讨论记录。
