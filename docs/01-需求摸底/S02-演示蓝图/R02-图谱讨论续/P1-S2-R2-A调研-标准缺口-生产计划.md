# P1-S2-R2-A 调研：标准缺口 — 生产计划与排产

调研对象：ERPNext v16.35.0 / Frappe v16.34.0 本地源码。路径相对 `frappe-bench/apps/erpnext/erpnext/`。
标注约定：【码】＝读码所得（有行号）；【推】＝推断；【未查实】＝没查。**未实跑任何 bench 命令。**

## 一、问 1：ERPNext v16 实现了 MRP 的哪一层

**先说 v16 的变化**：v16 新增了三个此前没有的 DocType —— `Sales Forecast`、`Master Production Schedule`、`Item Lead Time`，以及 1427 行的 `Material Requirements Planning Report`。这批东西把 ERPNext 从"手工挑销售订单生成工单"推进到了一条真正的 需求→MPS→MRP 链。**但产能仍未参与计算。**

| 层 | v16 实现程度 | 依据 |
|---|---|---|
| **S&OP** | **无** | grep `rough_cut`/`RCCP`/`time_fence`/`planning_horizon`/`Capacity Plan` 全 erpnext 仅命中 Manufacturing Settings 的 "Capacity Planning For (Days)" 标签，无任何 S&OP DocType【码】 |
| **需求管理/预测** | **有（v16 新增，很薄）** | `manufacturing/doctype/sales_forecast/`：`Sales Forecast`（frequency=Weekly/Monthly，status=Planned/MPS Generated/Cancelled）+ `Sales Forecast Item`（item_code / delivery_date / demand_qty / warehouse）。`sales_forecast.py` 仅 92 行，无预测算法，是**人工录入独立需求的容器**。另有 `report/exponential_smoothing_forecasting/` 做指数平滑。相关需求由 MRP 报表 BOM 展开产生【码】 |
| **MPS** | **有（v16 新增），但无时界** | `Master Production Schedule`（480 行）。`get_actual_demand:50` 汇总 SO + Material Request → `get_item_wise_mps_data:262` 按 (item_code, delivery_date) 聚合 → `get_cumulative_lead_time:145` 递归 BOM 累加提前期 → `add_mps_data:286`：`order_release_date = delivery_date - cumulative_lead_time`。**demand/planning time fence 无**（grep `time_fence` 零命中）。算粗排 + 倒排释放日，不算能力校验【码】 |
| **MRP 运算** | **BOM展开✅ 净需求✅ 提前期倒排✅ 安全库存✅ 批量规则≈仅最小订购量** | 引擎是**报表**：`report/material_requirements_planning_report/`（1427 行）。逐层展开（indent/parent_bom/bom_no）；净需求 `get_item_wise_bin_details:126` + `update_mps_data_with_bin_details:168` 扣库存与在途；提前期来自 `Item Lead Time`；安全库存见 `production_plan.py:85,1658` 的 `include_safety_stock` 与报表 `:454`。**lot sizing 只有最小订购量补足**：`production_plan.py:1473,1500-1509,1555-1559`（`_quantity_in_purchase_uom` / min_order_qty 凑整）。**无 EOQ、无固定批量、无期间批量**（grep `lot_size`/`EOQ` 零命中）【码】 |
| **⭐ RCCP / CRP** | **无。有"产能"这个数字，没有产能负荷计算** | 见下节详述。要点：MRP 报表确有一列 Capacity，但取自 `Item Lead Time.capacity_per_day`（**物料级，与 Workstation / Routing 无关**），且 `capacity` 在 1427 行全文仅 8 处命中，全是取值/传值/列定义（`get_item_capacity:1285-1299`、`:407`、`:463-465`、`:809-811`、`:970`），**没有一处把需求与 capacity 相比较、告警或削峰**。`get_bucket_view_data:393-431` 把需求按时间桶累加，capacity 只是随 dict 带过去显示【码】 |
| **有限产能排产 FCS/APS** | **无。实为 FCFS 顺排 + 冲突递归顺延** | `job_card.py:544 schedule_time_logs` → `:558 validate_overlap_for_workstation` → `:364 get_overlap_for` → `:400-434 has_overlap`。冲突则把 `planned_start_time` 推到冲突单 `to_time + get_mins_between_operations()`（`:572-580`）后**递归重试**；`check_workstation_time:583-640` 按工时窗口切分、跨班次跨天拆分、跳假日。先建 Job Card 者先占槽，**不回头优化、无目标函数、无优先级、无换型**。超出 `capacity_planning_for_days`（默认 30）找不到槽即抛错（`work_order.py:1251`）【码】 |
| **闭环反馈** | **实绩有，闭环无** | Job Card time_logs 回写实际工时；实绩报表有 `BOM Variance Report`/`Production Analytics`/`Job Card Summary`/`Downtime Analysis`。但**无重排机制** —— grep 未见任何 reschedule / replan 调度器，实绩不回流进 MPS/MRP【码】 |

### 结论：ERPNext v16 落在 **MRP**，够不上 **MRP II**

判据就是产能那一维有没有参与计算，答案是**没有**：

1. MPS → MRP 报表这条计划链上**完全无产能约束**。唯一的 Capacity 列是物料级展示值，代码里不参与任何比较。
2. 唯一真正检查产能的地方是 Job Card 排产时的工作中心时段占用避让（`has_overlap`），但那是**执行层的防重叠**，不是计划层的 CRP：它发生在工单已经下达之后，是 FCFS 顺延而非产能平衡，且不反馈给计划。
3. 无重排、无计划/实绩闭环 —— MRP II 的"闭环"这一半也不成立。

准确说法：**v16 是一个较完整的 MRP（含 MPS 与预测容器、净需求、提前期倒排、安全库存），外加物料级粗产能的"显示"，没有能力需求计划。**

### 顺带发现一处疑似缺陷（重要，但未实跑验证）

`master_production_schedule.py:443-449`：`on_submit` → `enqueue_doc("Master Production Schedule", self.name, "make_mrp", queue="long")`。但 **`def make_mrp` 在 erpnext 与 frappe 两个 app 内均无定义**（grep 确认，唯一同名命中是测试里的辅助函数 `make_mrp_plan`）。该报表自身的测试文件也留了注释：`test_material_requirements_planning_report.py:232` "left in draft: on_submit enqueues MRP Log creation in a background job"，而 **`MRP Log` 这个 DocType 在整个仓库不存在**（find 零命中）。
【推】提交 MPS 会导致后台任务 AttributeError，MRP 结果不落库，只能靠报表即时算。**这条须实跑确认**，不排除由别处注入。

## 二、问 2：Workstation / Workstation Type 产能模型查证

`Workstation`（`manufacturing/doctype/workstation/workstation.json`）字段：`working_hours`(Table→Workstation Working Hour)、`holiday_list`、**`production_capacity`(Int)**、`total_working_hours`(Float)、`hour_rate`、`workstation_type`、`plant_floor`、`status`、`warehouse`、`workstation_costs`、`disabled`。
`Workstation Working Hour` 子表字段：`start_time` / `end_time` / `enabled` / `hours`。

- **"每天可用几小时"能表达** ✅ —— `working_hours` 多时段子表 + `holiday_list`；`workstation.py:97-104 set_total_working_hours` 汇总；`job_card.py:583-640` 排产时真按这些时段切分并跳假日【码】
- **"同时能开几台"能表达** ✅ —— `production_capacity` 是**并行槽位数**，`job_card.py:412-434` 用 `alloted_capacity` dict 装并行 Job Card，键数 ≥ production_capacity 才判为满载【码】
- **排产是否检查工作中心占满** ✅ —— `get_overlap_for:364-398` 查该工作中心已有 Job Card 的时间重叠，`has_overlap:400-434` 按并行容量判定【码】
- **产能负荷报表** ❌ —— `manufacturing/report/` 下 22 个报表已逐个列出，无一是产能/负荷（最接近的 `production_planning_report`、`production_plan_summary` 都是数量口径）；`manufacturing/dashboard_chart/` 8 个图也无负荷图【码】
- **`Workstation Type` 无任何产能字段**（仅 workstation_type / hour_rate / description / workstation_costs）。按 type 排产时 `job_card.py:565-567` 取 `get_workstations()` 的**第一个**工作中心，不做负载均衡【码】

**小结**：单个工作中心的日历与并行度**建得起来**，冲突也真会避让。缺的是把这些汇总成"某周某工作中心负荷 X 小时 / 可用 Y 小时"的计划层视图 —— 即 RCCP/CRP 那一层，以及优先级、换型、跨工作中心均衡。

**另记**：v16 新增 `stock/doctype/item_lead_time/`，字段 `capacity_per_day`、`no_of_workstations`、`no_of_shift`、`shift_time_in_hours`、`daily_yield`、`total_workstation_time`、`manufacturing_time_in_mins`、`purchase_time`、`buffer_time`。这是一套**物料级的产能/良率参数**，与 Workstation 实体解耦。其中只有 `capacity_per_day` 被 `get_item_capacity:1285` 消费；`daily_yield` / `no_of_workstations` 的消费点**未查实**。

## 三、问 3：开源候选（GitHub API 实测，2026-09-23）

| 候选 | 许可证 | 活跃度（实测 pushed_at） | v16 兼容 | 集成形态 | 能补哪一层 |
|---|---|---|---|---|---|
| **frePPLe**（frePPLe/frepple） | Community MIT；仓库 license 字段 NOASSERTION → **双许可，Enterprise 专有**（v8 起 forecast 模块从 AGPL 转 MIT） | **2026-09-23（今天）**，747★，未归档 —— 极活跃 | **未查实**（见下） | 独立服务（C++ 核心 + Django），REST 对接 | **正是 RCCP/CRP + 有限产能排产 + 预测**，即 ERPNext 缺的那两层 |
| msf4-0/ERPNext-Frepple-Integration | GPL-3.0 | **2022-02-21，停更 4 年半**，30★ | **不兼容**【推：2022 年对应 v13/14 时代】 | Frappe app | 不可用 |
| **Timefold Solver**（OptaPlanner 继任） | Apache-2.0 | **2026-09-23（今天）**，1791★ | 与 ERPNext **无现成集成** | Java 库/独立服务，需自写适配层 | 求解器内核：能承载优先级、换型矩阵、多约束 FCS。但排产模型、数据同步、UI 全要自建 |

**frePPLe 与 ERPNext 集成的现实可行性**：官方文档存在 ERPNext connector 页（`frepple.com/docs/current/erp-integration/erpnext-connector.html`，当前文档版本 9.19.0），说明**官方在维护一个 ERPNext 连接器**，这比社区那个停更仓库可靠得多。但**是否 Enterprise Edition 限定、支持到 ERPNext 哪个版本（v16?）、Community 版能否用，本次未查实** —— 这是选型前必须先确认的一条。
社区侧还有 msf4-0 的三个衍生仓库（Enhanced-Integration / Version-1.3 / IRPS-Enhanced），最新可见时间 2023-12，**未逐个核实活跃度与兼容性**。

**Frappe 生态内的 APS app**：**未查实** —— 没做 Frappe Cloud marketplace 与 GitHub topic 检索。按已知情况【推】生态内无成熟的产能计划/APS app。

## 四、只能自研的部分

即便引入 frePPLe，下列属于弹簧行业特化或 ERPNext 侧改造，外部项目补不了：

1. **Work Order / Sales Order 优先级字段**（已实测零命中）—— 任何 APS 都要读优先级，ERPNext 侧得先有这个字段才喂得出去。
2. **换型/调机时间矩阵** —— 弹簧厂按线径、材质、卷簧方向切换，是**工序对工序的矩阵**，不是单值 `setup_time`。frePPLe 有 setup matrix 能力【推，未核实其数据模型细节】，但 ERPNext 侧的录入与同步要自建。
3. **工艺损耗反算投料量** —— 已实测 `production_plan.py` 中 `process_loss` 零引用。`Item Lead Time.daily_yield` 存在但消费点未查实。这是 SO 必然短交的直接原因，须自研（或在 MRP 侧接管）。
4. **Routing 基准量**（每 100 件耗时 X）—— 已实测缺失，弹簧工时高度依赖基准量表达。
5. **工作中心级 CRP 负荷报表** —— 物料级 `capacity_per_day` 不够用，要按 Routing → Workstation 汇总负荷并与 `working_hours × production_capacity` 对比。
6. **MPS 时界（demand / planning time fence）** —— v16 完全没有。
7. **`make_mrp` 缺失的绕行** —— 若要 MRP 结果落库（而非每次看报表即时算），须自研持久化。

## 五、拿不准 / 未查实

- **`make_mrp` / `MRP Log` 缺失是否真会报错** —— 只做了静态 grep，未实跑提交 MPS。这条影响"MPS 能不能用"的判断，优先级最高。
- **frePPLe ERPNext connector 的 Edition 限定与 ERPNext 版本支持** —— 只确认官方文档页存在，未读内容。选型前必查。
- **Frappe marketplace / GitHub topic 内是否有产能计划或 APS app** —— 未检索。
- **msf4-0 三个衍生仓库**（Enhanced-Integration 系列）的实际活跃度与兼容性 —— 未逐个查 API。
- **`Item Lead Time.daily_yield` / `no_of_workstations` / `no_of_shift` 的消费点** —— 只确认 `capacity_per_day` 被 `get_item_capacity` 用，其余字段是否参与计算未追。
- **rounding multiple / 采购倍数** 是否在 stock 或 buying 模块另有实现 —— 只在 `production_plan.py` 与 MRP 报表内查过 lot sizing。
- **`Delivery Schedule Item`**（`master_production_schedule.py:250` 引用，v16 新的交付排程子表）未展开查，可能与 MPS 的需求口径有关。
