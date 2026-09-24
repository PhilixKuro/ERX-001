# P1-S2-R2-A 排查：采购与库存对照行业现行标准

排查对象：ERPNext 16.35.0 / Frappe 16.34.0 本机源码（只读）。
视角沿用生产/质量两块已证实的模式：**记录层 vs 计算层**。行号均为本机源码实际行号。

结论先行：**采购块是本次排查里"计算层"最完整的一块**——供应商评分卡、框架协议累计量控制、
提前期参与计划，三项都有真算法，与"到处只有记录层"的预设不符。缺口集中在**分级与批量决策**
（ABC / EOQ / 配额）。库存块相反：触发层（再订货自动建请购）有，**定量层（安全库存、ROP 数值怎么来）全靠手填**。

## ① 采购与供应商判定表

| 标准能力 | 有无 | 记录层 / 计算层 | 依据（文件:行号） | 对弹簧厂的影响 |
|---|---|---|---|---|
| 供应商评估（多维评分、周期性） | **有** | **计算层完整** | `buying/doctype/supplier_scorecard_period/supplier_scorecard_period.py:43-91`：`validate()` 依次跑 `validate_criteria_weights`（权重须合计 100）→`calculate_variables`→`calculate_criteria`（`frappe.safe_eval` 解析 `crit.formula`，钳制在 0~`max_score`）→`calculate_score`（按 `weight/100` 加权）。变量取值是 20+ 个真 SQL 函数：`supplier_scorecard_variable.py:110` 延迟发货金额、`:148` 累计延迟天数（PR 实收日 vs PO `schedule_date`）、`:311` 拒收金额、`:337` 拒收件数、`:596` RFQ 响应天数。定时任务 `hooks.py:468` `refresh_scorecards` 挂 `daily_maintenance` | 可直接用。评分公式与权重是配置项，不用二开 |
| 到货准时率 / 质量合格率统计 | **有（在评分卡内）** | 计算层 | 准时：`supplier_scorecard_variable.py:115-145`（`get_cost_of_on_time_shipments`）、`:195-225`（按件计准时数）；合格率：`:337`/`:389` 拒收/接收件数之比可组公式 | 不用另造。但**没有独立的"供应商 OTD%/PPM 趋势报表"**，数据只在评分卡周期单里；要看趋势需自建报表 |
| 询价比价（RFQ 多家横向对比） | **有** | 记录层 + 报表层 | 报表 `buying/report/supplier_quotation_comparison/supplier_quotation_comparison.py:35-60`：跨 `Supplier Quotation Item` 取 `base_rate`/`amount`/`lead_time_days`/`valid_till`，含汇率折算与图表 | 能横向看。**无"选优/授标"动作**——选哪家、为何选，靠人工判断后手工开 PO，无记录 |
| 框架协议 / 长期协议 | **有** | **计算层（累计量控制 + 价格锁定都真）** | 累计量：`manufacturing/doctype/blanket_order/blanket_order.py:229-260` `validate_against_blanket_order`，按 `remaining_qty = item.qty - item.ordered_qty` 校验，超量容差读 `Buying Settings.blanket_order_allowance`；`ordered_qty` 由 `controllers/stock_controller.py:1704-1707` `update_blanket_order()` 回写，PO submit/cancel 均触发（`purchase_order.py:476,501,542`）。价格锁定：`stock/get_item_details.py:1887-1897` `update_party_blanket_order` 取协议价覆盖 | 年度协议按批下单可直接用，含超量拦截。字段仅 `qty`/`rate`（`blanket_order_item.json:42,64`），**无阶梯价、无最低承诺量** |
| 采购提前期参与计划 | **有** | 计算层 | `Item Lead Time` 的 `purchase_time`+`buffer_time`（`stock/doctype/item_lead_time/item_lead_time.json`）被两处消费：`manufacturing/doctype/master_production_schedule/master_production_schedule.py:454-459`（`制造分钟/1440 + purchase_time + buffer_time` 合成总提前期）、`manufacturing/report/material_requirements_planning_report/material_requirements_planning_report.py:1215-1232`。另有旧字段 `Item.lead_time_days`，被 `stock/report/itemwise_recommended_reorder_level/...py:29` 用 | 可用。注意**两套提前期字段并存**（`Item Lead Time.purchase_time` 与 `Item.lead_time_days`），消费方不同，二开需统一口径，否则钢丝提前期两处填不一致 |
| ABC 分类（按金额/重要性分级） | **无** | — | grep `abc_class`/`abc_analysis`/`abc_category`/`xyz_class`/`abc classification`（`*.py`/`*.json`，全 erpnext 目录）零命中；`buying/report/` 与 `stock/report/` 目录清单内无对应报表 | 弹簧厂钢丝规格常数百项，无分级则全部同策略管理，采购精力摊平 |
| 经济订货批量 EOQ | **无** | — | grep `eoq`/`economic_order`/`economic order`（erpnext+frappe，`*.py`/`*.json`/`*.js`）零命中 | 钢丝按整盘/整捆起订，实际靠经验定批量。EOQ 缺失对中小厂影响有限（供应商起订量常是硬约束） |
| 供应商配额（同料按比例分配多供方） | **无** | — | `Item Supplier` 全部字段仅 `supplier`、`supplier_part_no`、一个 column break（`stock/doctype/item_supplier/item_supplier.json:14,22,31`），**无比例/优先级字段**；grep `quota_arrangement`/`supplier_quota`/`allocation_percent` 在 erpnext 业务代码零命中（命中项全是会计科目表里的葡/法文词与 node_modules） | 主/备供方无法表达"7:3 分单"。多家供同一规格钢丝时，分配靠人工 |

## ② 库存与仓储判定表

| 标准能力 | 有无 | 记录层 / 计算层 | 依据（文件:行号） | 对弹簧厂的影响 |
|---|---|---|---|---|
| ABC / XYZ 库存分级 | **无** | — | 同上 grep，零命中 | 盘点频率、安全库存策略无法差异化 |
| 周期盘点（按分类定频次） | **无** | 仅有结果录入 | grep `cycle_count`/`cycle counting`/`count_frequency`/`physical_inventory` 零命中。`stock/doctype/` 下只有 `stock_reconciliation`（+`stock_reconciliation_item`），是**盘点结果录入单**，无"盘点计划/任务/频率"DocType，无盘点差异审批流 | 只能年度全盘或人工排表。弹簧厂料多件小，全盘成本高 |
| ⭐ 安全库存 | **有字段，无算法** | **记录层**（手填） | `Item.safety_stock` 为普通输入字段。被两处**消费**：`manufacturing/doctype/production_plan/production_plan.py:1658-1664`（`safety_stock = flt(row["safety_stock"]) if include_safety_stock else 0`；`required_qty = max(0, qty - (available_qty - safety_stock))`）、`stock/report/itemwise_recommended_reorder_level/itemwise_recommended_reorder_level.py:29`。全库 grep `safety_stock` 的 30 处命中**无一处是写入/计算**——没有标准差、没有服务水平系数、没有 √提前期 | **典型"有记录没算法"**。标准做法 `安全库存 = Z × σ需求 × √提前期` 完全缺失。钢丝提前期长、客户插单多，手填值必然偏高或偏低 |
| 再订货点 ROP | **触发有，定量无** | 触发=计算层；定量=记录层 | 子表 `Item Reorder` 字段仅 `warehouse_group`/`warehouse`/`warehouse_reorder_level`/`warehouse_reorder_qty`/`material_request_type`（`stock/doctype/item_reorder/item_reorder.json:20-57`），**全是固定值**。触发真有：`stock/reorder_item.py` 挂 `hooks.py:485` daily，`reorder_item()` 受 `Stock Settings.auto_indent` 开关控制，`:63-68` 按 `projected_qty <= reorder_level` 算 `deficiency` 并取 `max(deficiency, reorder_qty)` 自动建 Material Request。**推荐值只在报表里算、不回写**：`itemwise_recommended_reorder_level.py:29` `reorder_level = 平均日出库 × lead_time_days + safety_stock`（注意它把安全库存当输入而非输出） | 自动补货流程可用。但"补到多少"要人工把报表数字抄进 `Item Reorder`，无回写。这是**可低成本二开的一处**（把报表算法做成定时回写） |
| 批次有效期预警 | **有字段有报表，无预警机制** | 记录层 + 报表层 | `Batch.expiry_date`（`batch.json:95`），可由 `Item.shelf_life_in_days` 自动推算（`batch.py:195-213`，`expiry_date = manufacturing_date + shelf_life_in_days`）。报表 `stock/report/batch_item_expiry_status/batch_item_expiry_status.py:30-38` 输出"Expiry (In Days)"。发料端会避开过期批次：`pick_list.py:301-302`、`serial_and_batch_bundle.py:3210`（`expiry_date >= today() or isnull`），FEFO 排序 `:3052` | **`hooks.py` 里没有任何 expiry 相关定时任务**——无主动提醒，得有人去开报表。弹簧厂本身多为金属件无保质期，但表面处理剂/油品需要；优先级不高 |
| 库龄分析 | **有** | 计算层，分桶可配 | `stock/report/stock_ageing/stock_ageing.py:37`（`filters.ranges = get_age_ranges(filters.range)`）、`:48-49` 逗号分隔自定义分桶、`:137-169` 基于 FIFO 队列逐 slot 归桶，同时出数量与金额 | 可直接用识别呆滞钢丝。分桶按天数自定义 |
| 多级 BOM 真实可用量 | **部分** | 计算层（单层） | `Bin` 数量字段：`actual_qty`、`ordered_qty`（在途 PO）、`indented_qty`、`planned_qty`（已计划 WO）、`reserved_qty`、`reserved_qty_for_production`、`reserved_qty_for_sub_contract`、`reserved_qty_for_production_plan`、`reserved_stock`（`bin.json:65-193`）。公式 `bin.py:78-88`：`projected_qty = actual + ordered + indented + planned − reserved − reserved_for_production − reserved_for_sub_contract − reserved_for_production_plan` | 在途、已分配、已计划都算进去了，**单层可用量够用**。但这是**单物料单仓的净值**，不是"按多级 BOM 向下展开的可承诺量（ATP/CTP）"——要判断"这批弹簧能不能接"，仍需人工逐层看 |
| 库位管理（货位级） | **无原生货位模型，有扩展点** | — | `Warehouse` 是树（`parent_warehouse`/`lft`/`rgt`，`warehouse.json:201-223`），业界常见做法是"叶子仓库当库位"。`Putaway Rule` 只是**容量约束**：`item_code`+`warehouse`+`capacity`/`stock_capacity`/`priority`（`putaway_rule.json:24-105`），不是储位坐标。真扩展点是 `Inventory Dimension`（`inventory_dimension.json`），可把自定义维度（如货架/料架）注入并参与结存 | 无"排-列-层"原生模型。弹簧厂钢丝按盘立放、成品按箱，若要货位级，走 `Inventory Dimension` 二开，不必造新表 |
| 计量单位换算 | **有，单步固定系数** | 计算层（受限） | `UOM Conversion Detail` 仅 `uom`+`conversion_factor` 两个实字段（`uom_conversion_detail.json:15,25`），另有全局 `UOM Conversion Factor` 与 `UOM Category` | 采购 kg / 库存 kg / 销售 pcs 能配。**限制：系数是物料级固定 float**，而弹簧"kg↔pcs"随线径与圈数变，且同规格不同批次钢丝线密度有差。无批次级或公式级换算 → 这是弹簧行业的实打实缺口 |

## ③ 缺计算层的清单（按对弹簧厂重要性排序）

1. **安全库存无统计算法**（`Item.safety_stock` 纯手填，全库无写入逻辑）。钢丝提前期长＋插单频繁，手填必偏。标准公式 `Z × σ × √LT` 需完全自建。**最高优先**。
2. **kg↔pcs 换算不随线径/批次变**（`conversion_factor` 为物料级固定 float）。弹簧厂按 kg 买、按 pcs 卖，这是日常算错账的源头。需批次级或公式化换算。
3. **再订货点数值不回写**（算法已在 `itemwise_recommended_reorder_level.py:29`，但只出报表）。改造成本低、收益直接——把报表算法做成定时任务写回 `Item Reorder`。
4. **ABC / XYZ 分级全缺**（字段、报表、逻辑都无）。数百钢丝规格无法分层管理，且它是第 5、6 项的前置。
5. **周期盘点无计划层**（只有 `Stock Reconciliation` 录结果）。需盘点计划 + 频率 + 差异审批。
6. **供应商配额无法表达**（`Item Supplier` 只有两个实字段）。多供方分单比例靠人工。
7. **比价无授标动作**（`supplier_quotation_comparison` 只出对比表）。选供方的理由无留痕，客户审厂时说不清。
8. **无独立供应商 OTD%/PPM 趋势报表**（数据在评分卡周期单内，没有跨期趋势视图）。
9. **多级 BOM ATP/CTP 缺失**（`Bin.projected_qty` 是单层单仓净值）。接单能力判断仍靠人工。
10. **批次临期无主动预警**（`hooks.py` 无 expiry 定时任务）。弹簧厂影响面小，排末位。
11. **EOQ 缺失**。供应商起订量常是硬约束，实际价值不高，可不做。

## ④ 拿不准 / 未查实的

- **`Supplier Scorecard` 的默认评分标准是否随安装自带 fixtures**：只读到 `calculate_*` 与变量函数实现，未查 `Supplier Scorecard Criteria`/`Variable` 的预置数据文件。若不自带，公式与权重要从零配。考虑到 S1 已应验过"fixtures 缺口"这类坑，**此项须实机验证**，不宜按"自带"推定。
- **`Inventory Dimension` 做货位的实际边界**：只读了 DocType 字段（`validate_negative_stock`、`condition`、`fetch_from_parent` 等），未追它在 `stock_ledger` 结存与报表侧的完整表现（能否按维度出结存报表、能否与 `Putaway Rule` 联动）。断言"可做货位"是**推断**，未验证。
- **`planned_qty` 是否含在制未完工量**：读到 `bin.py:78-88` 的公式，但未追 Work Order 各状态如何增减 `planned_qty`，故"在制品不计入可用量"是推断而非读码所得。
- **`Blanket Order` 与 PO 之外单据的联动**（如直接开 Purchase Invoice 是否也扣协议累计量）：只查实了 PO 路径（`purchase_order.py:476,501,542`）与 `accounts_controller.py:4390` 一处调用，未逐单据核。
- **质量合格率与 `Quality Inspection` 的串联深度**：评分卡用的是 `Purchase Receipt Item.rejected_qty`，未查实 `Quality Inspection` 的判定结果是否自动写回该字段。若不自动，合格率数据依赖收货员手填拒收数。
