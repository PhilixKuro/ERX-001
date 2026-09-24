# P1-S2-R2-A 排查：需求预测与计划 / 工程变更与主数据

排查对象：ERPNext 16.35.0、Frappe 16.34.0（只读源码）。路径基准 `frappe-bench/apps/`。

> **本次推翻两条既有判定**（均为范围缩小方向，与项目既往教训同型）：
> ① 预测算法**不是完全没有**——`exponential_smoothing_forecasting` 报表在；
> ② 变体属性**支持数值**——`Item Attribute` 有 `numeric_values`/`from_range`/`to_range`/`increment`。

## ① 预测与计划判定表

| 标准能力 | 有无 | 记录/计算层 | 依据（读码所得） | 对弹簧厂影响 |
|---|---|---|---|---|
| 指数平滑预测 | **有**（报表） | 计算层，但**不落库** | `erpnext/manufacturing/report/exponential_smoothing_forecasting/exponential_smoothing_forecasting.py` 264 行。`ExponentialSmoothingForecast.forecast_future_data()` 第 19-41 行实现一次指数平滑：`value[forecast_key] = prev_forecast + smoothing_constant * (prev_actual - prev_forecast)`。滤器含 `smoothing_constant`/`periodicity`/`no_of_years`/`based_on_document`/`based_on_field`(Qty 或 Amount) | 可看趋势，但结果**只在屏幕上**（grep `insert()`/`save()`/`new_doc` = 0 命中），要转成 `Sales Forecast` 须人工再录一遍 |
| 移动平均 / 季节性分解 | **无** | — | grep `moving_average` 全部命中是**存货计价**的 Moving Average（`stock/stock_ledger.py`、`stock_ageing`），与预测无关；grep `seasonal` 仅命中 `Monthly Distribution`（会计分摊用，非预测季节因子）。一次指数平滑**不含趋势项与季节项**（无 Holt / Holt-Winters） | 弹簧厂常有淡旺季（如汽配、家电配套），季节性要自己算 |
| 预测误差 / 准确率（MAPE、bias） | **无** | — | grep `mape`/`accuracy` 在该报表 0 命中；全 `manufacturing/` 无误差跟踪表或字段。报表只出「实际 vs 预测」两行值，**不算偏差指标** | 预测准不准无从度量，平滑常数 α 只能凭感觉调 |
| **预测消耗**（forecast consumption） | **有** | **计算层** | `material_requirements_planning_report.py:449-450`：`row.demand_qty = max(flt(row.planned_qty), flt(row.sales_forecast_qty))`，`planned_qty` 同式取大。即标准「**greater-of**」取大规则——实际订单超过预测即以订单为准，不重复计需求。取数见 `get_sales_forecast_data()` (1148 行起)，只取 `docstatus == 1` 的 `Sales Forecast` | **这条是好消息**，MRP 不会把预测和实单双算 |
| 时界（demand / planning time fence） | **无** | — | 全 `erpnext/` grep `time_fence`/`planning_horizon`/`frozen_period` 唯一命中是 `accounts/report/cash_flow/cash_flow.py`（无关）。MPS 与 MRP 均无冻结窗口字段 | 近期已排产的单子会被每次重算冲掉，车间拿到的计划不稳定 |
| 净变式 MRP（net change） | **无，全量重算** | — | MRP 是 Query Report（`material_requirements_planning_report.py` 1427 行），**每次打开报表即整体重算**，无增量表、无 `net_change` 标志、无变更日志驱动。触发方式＝人工带滤器跑报表（可选 `mps` 滤器串到某张 MPS） | 料号多时每次全量跑，且无「上次跑完后哪些变了」的线索 |
| 计划订单（planned order） | **有，可转换** | 计算层 | **此前"只是报表"的担心不成立**：`make_order()` (1303 行) 分派到 `make_purchase_orders()` (1347) 与 `make_work_orders()` (1391)，分别 `frappe.new_doc("Purchase Order").insert()` (1375-1383) 与 `frappe.new_doc("Work Order").insert()` (1401-1413)；报表列含 `Planned Work Order` (1051)。另有独立的 `Production Plan` (2401 行) 走 `make_work_order()` (773) / `make_material_request()` (962) / `make_subcontracted_purchase_order()` (864) | MRP 结果能直接驱动执行，勾选行→建单 |
| 多工厂 / 多仓库计划 | **有（按仓库）**；调拨建议**未查实** | 计算层 | `Production Plan` 有 `for_warehouse` 字段，`get_bin_details()` (1687) 按 `for_warehouse or source_warehouse or default_warehouse` 取数；`get_items_for_material_requests()` (1745) 处理仓库列表与父仓库汇总 (1922)，`ignore_existing_ordered_qty` 控制是否计已有在途 | 单厂多仓可用；**仓间调拨建议我没查实**，标为待验 |
| MPS 提交仍然坏 | 坏（沿用既有结论） | — | 既有结论不改：`master_production_schedule.py:445` 调 `make_mrp`，全仓无定义；json 无 `is_submittable` | 但 MRP 报表可独立跑（`mps` 滤器可选），不经 MPS 也能用 |

## ② 工程变更与主数据判定表

| 标准能力 | 有无 | 记录/计算层 | 依据 | 对弹簧厂影响 |
|---|---|---|---|---|
| **⭐ ECN / ECO 工程变更** | **无专用 DocType** | 连记录层都没有 | 对 `erpnext/` 与 `frappe/` 两个 app 同时 grep `engineering_change`/`engineering change`/`\bECO\b`/`change_request`（`--include=*.py --include=*.json`）＝**0 命中**；`manufacturing/doctype/` 下 52 个目录全列过，无变更申请类表。**已按纪律排除"被 Workflow 覆盖"**：Frappe 内置 `Workflow` 只做单据状态流转，它能给 BOM 加审批环节，但**不提供变更单实体**（无变更号、变更原因、受影响清单、生效批次），也**不带影响分析** | **本块最大缺口**。客户改图纸是常态，变更凭什么记、谁批、影响哪些在制单，全靠线下 |
| BOM 生效日期 | **无日期字段** | — | `bom.json` 全部 `fieldname` 已逐个列出（约 88 个），**只有 `is_active` / `is_default`**，无 `valid_from`/`valid_upto`/`effective_date`。切换＝人工翻 `is_default` 旗标，是**瞬时生效**，无「按日期自动切版」 | 新旧版切换时点靠人盯 |
| 切换时在制工单怎么处理 | 旧版**留存**（非追溯） | 记录层 | `Work Order` 建单时把 `bom_no` 写死在单上（`work_order.py:2611-2615` 取 variant BOM 时也是落字段），故已下达工单继续用旧版——**这点符合制造业预期**，不是缺口 | 在制不被打乱，但反过来说「哪些在制单还在用旧版」要自己查 |
| BOM 变更影响分析（where used） | **半有** | 记录层 | **正向展开有**：`report/bom_explorer/`（`get_exploded_items()` 递归 `BOM Item` 按 `parent` 下钻）、`bom_explosion_item` 子表、`bom_stock_analysis`。**反向追溯有一张**：`stock/report/item_where_used/`（grep `where_used` 命中 `.py/.js/.json` 三件套）。**但**：它是「某料用在哪」的静态清单，**不是变更影响分析**——不联动在制工单、不算受影响数量、不出变更波及面 | 能查到父件清单，但「改这个料会打乱哪几张在跑的工单」要人工交叉比对 |
| 图纸 / 程序文件版本 | **无版本能力** | 记录层 | `frappe/core/doctype/file/file.json` 全部 `fieldname` 已列：有 `content_hash`、`attached_to_doctype/name/field`、`folder`，**无 `version`/`revision`/`supersedes` 字段，无父子版本链**。`core/doctype/version/version.py` 的 `get_diff()` 只比对**文档字段**，不管附件二进制。既有结论（`drive` 补不上）成立 | A 类图纸、B 类成型程序的受控版本**必须二开**。上传同名文件只能靠 `content_hash` 察觉不同，拿不到「A 版→B 版」谱系 |
| 物料编码规则 | **有基础，无按属性生成** | — | `item.py:164-172`：`item_naming_by == "Naming Series"` 时走 `set_name_by_naming_series()`；默认序列 `STO-ITEM-.YYYY.-`（`item.json`），`validate_naming_series()` 在 469 行。**但**按属性拼码（线径+长度+材质→编码）**未查到**：grep `make_variant_item_code` 在 `item.py` 与 `item_variant_settings` 均 0 命中 | 弹簧「按属性拼码」的规则要二开；分类码可用 `Item Group` 凑，但不进编码串 |
| 变体自动生成 BOM | **有** | 计算层 | `manufacturing/doctype/bom/bom.py:2036` `make_variant_bom(source_name, bom_no, item, variant_items, target_doc)`，测试见 `test_bom.py:355 test_generated_variant_bom` / 380。`Production Plan` 亦能认变体 BOM（`test_production_plan.py:1450-1466`），`work_order.py:2611` 下单时自动挑变体 BOM | 派生规格可从模板 BOM 生成，省事 |
| **变体属性能否参与公式**（推翻既有判定） | 属性**支持数值**；公式**仍不支持** | 记录层 | **`item_attribute.json` 有 `numeric_values`(Check)、`from_range`、`to_range`、`increment` 四字段**；`item_attribute.py:86-87` 在 `numeric_values` 为真时调 `validate_is_incremental()`，94-105 行校验 `from_range < to_range` 且 `increment` 必填。**故"属性值只是字符串不可计算"这条既有判定不准**——数值型属性是原生能力，能约束步进与上下限（如线径 0.5~5.0 步进 0.1）。**但**：没有「由属性值代入公式算出用料量/工时」的机制，属性只做取值域校验，**不参与 BOM 数量计算** | 规格可结构化建模（好过预期），但「线径×圈数×中径→料长」这类公式仍须二开 |
| 主数据审批流 | **有（框架自带）** | — | Frappe 内置 `Workflow` DocType，**按要求不判为缺口**。可给 Item / BOM 配「新建→审批→生效」状态流 | 够用，不必二开 |

## ③ 缺「计算层」的清单（按重要性排序）

1. **ECN/ECO 工程变更全缺**——连记录层都没有（本块唯一「记录层也没有」的项）。弹簧厂改图纸是常态，变更单、评审、生效控制、受影响在制单清单，四件全须二开。**优先级最高**。
2. **图纸与成型程序的受控版本**——`File` 无版本链，`Version` 不看附件。质量追溯与客户审厂都要这个。
3. **变更影响分析**——`item_where_used` 只给静态父件清单，缺「波及哪些在制工单/未清采购」的联动计算。与第 1 条同批做才划算。
4. **时界（time fence）**——零实现。没有它，每次重算都可能推翻车间已接的近期计划，MRP 输出不可信，是**已有计算层但缺约束层**的典型。
5. **预测误差跟踪（MAPE/bias）**——有预测算法却不度量准确率，α 无法标定，预测层等于开环。
6. **季节性与趋势预测**——只有一次指数平滑，淡旺季与增长趋势算不出。
7. **净变式 MRP**——全量重算，料号规模上去后既慢又无变更线索。
8. **按属性生成物料编码 / 属性参与用料公式**——数值属性已有（好于预期），差的是「代入公式算量」这一步。
9. **预测报表结果落库**——指数平滑算完不写回 `Sales Forecast`，人工转录是白工，改造量小、性价比高。

> 与既有模式一致：**本次仍是「记录层有、计算层缺」为主**，但出现两个例外——ECN 是**记录层也缺**（比模式更糟），而计划订单转换与预测消耗是**计算层实际齐备**（比模式更好，此前担心不成立）。

## ④ 拿不准 / 未查实的

- **仓间调拨建议**：`Production Plan` 能按 `for_warehouse` 分仓计划已读实，但「MRP 是否给出 A 仓调 B 仓的建议」**未查实**（未读 `material_request_plan_item` 与 `production_plan_material_request_warehouse` 细节）。
- **`item_where_used` 的实际查询深度**：只确认三件套文件存在与命名，**未读其 SQL**，不确定是单层父件还是递归全层。
- **`Production Plan` 与 MRP 报表两条路径的关系**：两者都能建工单，何为主线、是否重复，未通读 2401 行判定。
- **`is_phantom_bom`（虚拟件）**：`bom.json` 有此字段，对弹簧多工序半成品可能有用，本次未展开。
- **指数平滑报表的取数范围**：`based_on_document` 可选哪些单据类型（Sales Order / Delivery Note 等）未逐一列举。
- **推断而非读码所得**：第 ③ 节各条的「二开工作量」与优先级排序含我的判断，非源码事实。
