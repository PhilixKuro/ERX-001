# P1-S7 通用计算 —— 开发方案·总纲

**版本**：v1.0｜**日期**：2026-10-15｜**编写者**：Claude（Opus 5.5）
**产出步骤**：P1-S7-R4 · `plannedDev` C 步（`build`）
**来源需求**：[R3 B 需求文档](../R03-需求文档/P1-S7-R3-B需求文档.md) v1.0（下称「需求」）
**状态值与复核建议**：不在本文件——见 [P1-S7-R4-C回执](P1-S7-R4-C回执.md)
**执行者**：Claude（S7 概况「偏离」：D 步不交 CodeX）

> **读法**：本方案是 D 步的唯一权威依据，也是 E 步的核对清单。总纲装跨 Part 的约定、接口契约、技术假设与执行纪律；各 Part 按「切片 → 任务」展开。**凡与需求字面不一致处，以本方案为准**，偏离逐条列在 §四。
> **编号**：切片 `SL-`、任务 `TS-`、技术假设 `HT-` 为本方案内编号。**需求文档里也有 `TS-`、`AC-` 编号**，引用时一律写「需求 TS-00x」「需求 AC-0xx」。
> **「读码」与「实测」**：本方案凡写「读码」的都未在站点上跑过；「探针」指本步在测试站以 `bench execute` 跑过的只读探针（已删除）。行号指 `docker/apps.json` 锁定的 commit。

---

## 一、概述

**做什么**：在 `frappe_china` 里补上弹簧厂演示要讲的计算层：每日按三种规则算出「何时该进多少料」、写成补货建议单交人采纳；按仓库自动维护安全库存与再订货点；新建工单与生产计划时按单位成本选 BOM；批次级单位换算；工时与拆单解耦；前道完工数自动传给后道；计件额汇总进工资；产能负荷报表与 SPC 控制图；迁移时自检自有覆盖是否生效。另做 Ruff 基线清零。

**完成标准**：十二个切片的验收条件全部通过（§三），需求 AC-001～AC-023 每条都落在某个切片的验收条件里（§三末「需求 AC 覆盖表」）。验收一律要有正向证据（测试输出、查询结果、截图），不能以「没报错」代替。

**Part 索引**

| Part | 文件 | 内容 | 切片 | 任务 |
|---|---|---|---|---|
| 1 | [Part1](P1-S7-R4-C开发方案-Part1.md) | Ruff 基线与模块骨架、覆盖自检、补货参数与安全库存／再订货点、按成本选 BOM、补货建议单与每日计算 | SL-001～SL-005 | TS-001～TS-009 |
| 2 | [Part2](P1-S7-R4-C开发方案-Part2.md) | 批次换算、拆单、工序间数量传递、计件工资 | SL-006～SL-009 | TS-010～TS-013 |
| 3 | [Part3](P1-S7-R4-C开发方案-Part3.md) | 产能负荷报表、SPC 报表与控制图页面、演示站落地与全量回归 | SL-010～SL-012 | TS-014～TS-017 |

**首个 Phase 方案的四条额外要求**：不适用。P1 的首个开发方案是 S4-R7，四条已在那里写成验收条件并经 E／F 核过（工程基础设施、端到端最简路径、契约任务、关键假设）。本 Stage 在既有基础设施上追加，只保留一个基础设施切片（SL-001，Ruff 基线与模块骨架），它本身就是需求 TS-001（`PH-P1019`）。

---

## 二、关键架构决策（本方案新定，C 步职责内）

| # | 决策 | 理由 |
|---|---|---|
| A1 | **新增两个注册模块**：`Stock Plus`（库存增强，目录 `frappe_china/stock_plus/`，装补货建议单）与 `Production Plus`（生产增强，目录 `frappe_china/production_plus/`，装计件汇总单、两张报表、控制图页面）。业务逻辑放两个普通包：`frappe_china/replenishment/`（补货）与 `frappe_china/production/`（生产）。每个新模块配一份空 `Workspace Sidebar`（同 `cn_tax.json` 先例），压住模块自动侧栏 | 同 S4 A8「模块目录装 DocType／Report，普通包装计算」的分法；需求 §4.1 把补货模块留给 C 步，补货与生产分属库存、生产两域，按 ADR-0012 按域分 |
| A2 | **新字段一律 Custom Field＋fixtures，字段名加 `cn_` 前缀**（如 `Item-cn_rule_eoq`） | 与 `Company-cn_urban_construction_tax_rate` 同；免与上游将来新增字段撞名 |
| A3 | **公司默认参数放 Company 的 Custom Field**，不另建设置单 | 需求 §4.2.2 留 C 定；与 S4 城建税率同处，造数一处填 |
| A4 | **日需求按 SLE 白名单取**：`is_cancelled=0`、`actual_qty<0`，且 `voucher_type` 为 `Delivery Note`、`Sales Invoice`，或为 `Stock Entry` 且 `purpose` ∈ {`Material Issue`, `Manufacture`, `Material Consumption for Manufacture`}。仓间调拨、盘点、采购退货不算需求 | 需求 §4.2.3 留 C 定、要求与 σ 同口径。用白名单而非原生报表的「排除法」：排除法会把盘点、采购退货也算成消耗（`itemwise_recommended_reorder_level.py:95-122`），且该报表的发货一路有 `setdefault` 缺陷（`:156-157`，SI 被漏计） |
| A5 | **σ 取样本标准差**（`statistics.stdev`，分母 89）；**Z 取 `statistics.NormalDist().inv_cdf(服务水平/100)`** | 需求 §4.3 留 C 定。窗口是对未来需求的抽样估计，用样本标准差 |
| A6 | **`warehouse_group` 有值时，该行的需求与计划量都按组下全部仓库合计** | 原生 `reorder_item.py:56-61` 有组时用组的计划量判触发；再订货点按同一范围算，触发线与被比较量才是同一口径 |
| A7 | **补货建议单的「触发依据」用子表**（每行一个输入项：项目名取自固定的 Select 选项、数值、备注），不用一段 JSON 或拼接文本 | 人手算复核时一行一个数；项目名走 Select 选项故可译 |
| A8 | **采纳生成的 MR 以计算日期为 `transaction_date`**，经 Custom Field `Material Request-cn_replenishment_suggestion` 回指建议单 | S8 回放时采纳也按模拟日期出单；MR 原生无通用回指字段 |
| A9 | **按订单规则直接调原生 `get_items_for_material_requests`**，以 dict 传入（不建 Production Plan），`ignore_existing_ordered_qty=1` 使它扣减计划量；成品行的待展开量取销售订单行的 `qty − delivered_qty − work_order_qty`（换成库存单位） | 原生已扣的只有 `Bin.projected_qty`（`production_plan.py:1655-1666`），已提交 MR／PO 已含在计划量里，故「已覆盖的不重复建议」由它满足；已建工单的那部分，原料占用已进 `reserved_qty_for_production`，展开时再扣会重复，故只展开未建工单的部分 |
| A10 | **选 BOM 用内存算成本，不落库**：先把每道工序的 `hour_rate` 预置为工作中心 `hour_rate`，再调 `bom.calculate_cost(save_updates=False, update_hour_rate=False)` | `update_cost(save=False)` 在 `update_hour_rate=True` 时仍会 `row.db_update()`（`bom.py:1061-1062`），选一次 BOM 就改写全部候选 BOM 的工序行；预置后走 `update_hour_rate=False` 分支即不写库 |
| A11 | **工单选 BOM 挂 `before_insert`，评论在 `after_insert` 写**；生产计划挂 `validate` | 生产计划建工单时带 `ignore_validate`（`production_plan.py:945`），挂 `validate` 管不到这条路径；`insert()` 里 `before_insert` 早于 `run_before_save_methods`（`frappe/model/document.py:480`），不受 `ignore_validate` 影响。插入前没有单号，评论只能在插入后写 |
| A12 | **「BOM 未被人改过」的判据**：`bom_no` 为空，或等于原生两种默认 BOM 之一（工单 `get_item_details` 的默认与 `stock.get_item_details.get_default_bom`） | 原生三条建单路径各取各的默认（工单表单、销售订单、生产计划，见 HT-005 依据）；只认其中一种会把另一路的默认误判成人改 |
| A13 | **拆单用「模块属性替换」**：`work_order` 模块上的 `split_qty_based_on_batch_size` 换成自有函数，由幂等的 `ensure_patched()` 在 `before_request`、`before_job` 与 Work Order `before_submit` 三处调用。侵入度定 **L4**（跟方法体），另加一条测试比对上游原函数源码的哈希，上游一改即红 | 两个调用方都按模块全局名查找（探针：`WorkOrder.create_job_card` 与解包后的 `make_job_card` 的 `__globals__` 即模块字典），全 bench 无别处 import 它（HT-003）。补丁放 `hooks.py` 不可靠：钩子表有缓存，新进程未必 import `hooks.py`。哈希测试把「跟方法体」变成可执行的提醒 |
| A14 | **后道卡的数量经 `frappe.db.set_value` 直接改**：`for_quantity`、`time_required`（按原生建卡同式 `工序 time_in_mins ÷ 工单 qty × 新数量`，`work_order.py:2987`）、`scheduled_time_logs` 末行的时长与止时、`items` 子表的 `required_qty`（按新旧数量比例），一并改；不走 `save()` | 原生改 `for_quantity` 不重算 `time_required`（`job_card.py:169-184`），而 `before_save` 有排程时会按 `scheduled_time_logs` 把 `time_required` 改回原值（`:926-950`）；只改数量，负荷报表就照旧按整卡工时计。`save()` 还会跑 `validate_job_card_qty`（`:238-273`），中间态可能误报 |
| A17 | **工序间数量按「预计产出」逐道传递，并级联到其后所有工序**：首道的计划量＝工单数量；每道的预计产出＝已提交卡的完工数之和＋max(0, 该道计划量 − 已提交卡的 `for_quantity` 之和)；下一道的计划量＝上一道的预计产出 | 只按「已提交完工数」算，前道一取消就无卡可计，后道会被改成 0，回不到取消前（需求 AC-018 第 3 问）；按预计产出算，未提交部分仍按计划量计，即需求 §4.8「部分卡未提交时只按已提交部分滚动调整」。级联见 §四 偏离 3 |
| A15 | **控制图用 echarts 5.6.0**，把 Insights 前端依赖里的 `dist/echarts.min.js` 连同 LICENSE 原样放进 `frappe_china/public/js/vendor/`（文件名带版本号），页面经 `frappe.require` 加载 | frappe-charts 一条线只有一个颜色（`AxisChart.js:304`、`utils/draw.js:583-590`），做不到逐点着色（RS-004 取第二个库）；Insights 打包产物里的 echarts 并入了带哈希的 chunk、无全局导出，不能直接引用。放静态文件不需改 app 的构建，版本由文件本身锁定 |
| A16 | **界面文字一律用英文源词，经 `_()`／`__()` 翻译，中文进 `zh.csv`**。选源词前先查六个官方 app 的词典：官方已有该键且译文合用的，直接沿用、csv 不收；官方译文不合用的，**换一个官方没有的源词**，不覆盖官方 | 同 S4 A9「csv 只收官方词典里没有的键」。例：建议单状态要显示「待定」，官方 `Pending` 已译作别的词，就另取源词，不去改全站的 `Pending` |

---

## 三、切片划分与验收（索引；各切片的完整验收条件在所在 Part）

| 切片 | 功能点（需求编号） | 验收条件要点 | Part |
|---|---|---|---|
| **SL-001** Ruff 基线与模块骨架（基础设施，豁免「用户可感知」） | 需求 TS-001、`PH-P1019`、DEC-020；A1 | 容器内锁版本 ruff 可跑；`ruff check`／`format --check` 0 告警；基线是独立一次提交、只含格式与 lint 修复；两个新模块与空侧栏 migrate 后存在、Desk 不多出自动侧栏；全量测试与基线相同 | 1 |
| **SL-002** 覆盖自检 | 需求 TS-002、IM-007、`PH-P1073`、DEC-010 | migrate 后自检自动跑；不过时三处告警、migrate 正常结束；断言覆盖 `override_whitelisted_methods` 全部条目（改坏 CRM 那条也报）；自检本身抛异常也告警不中断；无中式公司不告警；`setup.sh` 顺序比对不一致即非零退出 | 1 |
| **SL-003** 补货参数、安全库存、再订货点 | 需求 TS-003～005、IM-008／009、DEC-002／004／007～009 | 参数字段与回落；`auto_indent` 显式置 0；提前期同步；`safety_stock` 与再订货点按手算一致、按仓库不同；未勾物料不动；无 `Item Reorder` 行不建；提前期缺失、无出库等边界有明确结果 | 1 |
| **SL-004** 按成本选 BOM | 需求 TS-006、IM-018、DEC-018／019／023 | 三 BOM 选单位成本最低、手算一致；调价后选择改变；工单评论；人改过不覆盖只提示；销售订单、生产计划建工单也选；生产计划行 BOM 一致；未勾物料原样；选择不改写 BOM 库内数据 | 1 |
| **SL-005** 补货建议单与每日计算 | 需求 TS-007、IM-017、DEC-001／003／005／006／021／022；§4.12／4.13 | 三规则并列、去重、采纳生成已提交 MR 并回指、忽略不出单、批量采纳；三规则建议量手算一致；按某日计算的窗口与幂等；参数缺失与单物料出错不中断 | 1 |
| **SL-006** 批次级单位换算 | 需求 TS-008、IM-012、DEC-013 | 三类单据行选不同批次带出不同系数、等于展开长度×线密度（或倒数）；服务端复核；未填回落物料级；库存单位行不动 | 2 |
| **SL-007** 工时与拆单解耦 | 需求 TS-009、IM-013、DEC-014 | 10000 支、拆分数量空 → 1 张卡、4000 分；填 2500 → 4 张；两条建卡路径都生效；未勾工序照旧；上游函数一改测试即红 | 2 |
| **SL-008** 工序间数量传递 | 需求 TS-010、IM-015、DEC-016 | 950／50 → 后道 950；三道级联；已开工只提示；取消复原；拆单下扣最后一张；后道卡能按原生校验提交 | 2 |
| **SL-009** 计件工资 | 需求 TS-013、IM-016、DEC-017 | 计件额手算一致、单价回落；汇总单逐行列来源；已提交 `Additional Salary` 回指；重复跳过；取消联动；无单价行列出；员工无薪资结构时报清楚 | 2 |
| **SL-010** 产能负荷报表 | 需求 TS-011、IM-010、DEC-011 | 需求与产能两列非空、手算一致（部分完工、假日）；未排期一列；超载标红；柱状图；产能为 0 标注 | 3 |
| **SL-011** SPC 报表与控制图 | 需求 TS-012、IM-011、DEC-012 | 已知数据 Cpk／Ppk 手算一致；非数字剔除计数；样本不足；Nelson 8 条各一命中一不命中；页面判异点异色（截图） | 3 |
| **SL-012** 收尾：登记、全量回归、演示站落地 | 需求 TS-014、AC-023 | README 覆盖登记与接口约定成文；全量测试只增不减全过；译名自检过；演示站 migrate 后自检过、`auto_indent`＝0、业务数据仍为 0 | 3 |

执行每个切片前，对照该切片验收条件检查方案覆盖性——如发现按方案写出的代码无法通过验收条件，暂停反馈，不硬写。

**需求 AC 覆盖表**（E 步据此核「需求验收无遗漏」）

| 需求 AC | 落在 | 需求 AC | 落在 | 需求 AC | 落在 |
|---|---|---|---|---|---|
| AC-001 | SL-005 ① | AC-009 | SL-003 ③ | AC-017 | SL-007 ①② |
| AC-002 | SL-005 ② | AC-010 | SL-002 ①～④ | AC-018 | SL-008 ①～④ |
| AC-003 | SL-005 ③ | AC-011 | SL-002 ⑥ | AC-019 | SL-009 ①～④ |
| AC-004 | SL-005 ⑤～⑦ | AC-012 | SL-010 ①～④ | AC-020 | SL-004 ①～③ |
| AC-005 | SL-003 ② | AC-013 | SL-011 ①～③ | AC-021 | SL-004 ④～⑥、SL-005 ⑦ |
| AC-006 | SL-005 ⑧ | AC-014 | SL-011 ④ | AC-022 | SL-001 ②③ |
| AC-007 | SL-003 ④⑤ | AC-015 | SL-011 ⑥ | AC-023 | SL-012 ② |
| AC-008 | SL-003 ⑥⑦ | AC-016 | SL-006 ①～③ | | |

---

## 四、相对需求文档的偏离与补定

需求里写「C 步定」的各处，本方案的取法见 §二与各任务；下表只列**改了需求字面**或**需求没提、本方案补上**的。

| # | 需求原文 | 本方案 | 理由 |
|---|---|---|---|
| 1 | §4.10 第 1 条：工单 `before_insert`／`validate`（新建时）选 BOM | 只挂 `before_insert`（A11） | 生产计划建工单带 `ignore_validate`，`validate` 不跑；`before_insert` 三条路径都跑 |
| 2 | §4.10 第 3 条：生产计划带 BOM「`get_item_details` 路径；挂法 C 步定」 | 挂 Production Plan 的 `validate`（`doc_events`，L3），改写 `po_items.bom_no`；另在前端「取物料请求明细」按钮之前不另做处理（原生按钮读表单上的 `po_items`，保存后即是改过的值） | 读码：`po_items.bom_no` 只在 `add_items`（`production_plan.py:504-551`）与前端 `get_item_data`（`:2041`）两处写入，服务端无处重置（`validate` 不碰它，`:137-145`）；下游缺料计算、建工单都读行上的值（`:1815`、`:750`）。`add_items` 在 Python 内直接调 `get_item_details`，`override_whitelisted_methods` 管不到，故不走 L4。**RS-002 由此关闭** |
| 3 | §4.8：只对齐「下一道」工序 | 对齐本道之后的**全部**工序，逐道按预计产出级联（A17） | 前道少 50，第三道照旧是原数，操作工在第三道又要手填差额，需求要消除的正是这一步；三工序例（需求 AC-018）只核第二道，按字面做会留下第三道 |
| 4 | §4.8：差额从最后一张未开工卡扣，扣到 0 的「保留 0 还是取消」 | 扣到 0 的卡**保留、`for_quantity`＝0**，不取消；加回时也先加在最后一张 | 草稿卡没有可取消的状态，删除不可逆；0 数量的草稿卡不进负荷（需求侧按未完成比例计，`for_quantity`＝0 按 0 计，需求 §4.11.1） |
| 5 | §4.8：「开工」判据 C 步定 | **已开工**＝`time_logs` 有任一行带 `from_time`，或 `status` 不是 `Open` | 原生只要有 `time_logs` 即置 WIP（`job_card.py:1254-1297`）；`status` 由转料等也会离开 `Open`，转过料的卡改数量会与已转料数矛盾，同样视为已开工 |
| 6 | §4.8：工序顺序取 `idx` 或 `sequence_id` | 取 `Work Order Operation` 的 `idx` | 原生的前后序校验用 `sequence_id`，但 `sequence_id` 为空时整个跳过（`job_card.py:1368-1430`），演示 BOM 多数不填；`idx` 恒有、就是 BOM 工序表的顺序 |
| 7 | §4.9：时间行按 `from_time` 日期归期间 | 照需求；**无 `from_time` 的行归该卡的 `posting_date`** | 原生非 `enforce_time_logs` 时允许不填时间（`job_card.py:894-905`） |
| 8 | §4.9：期间＝D 所在月 | 期间＝D 所在**自然月**的 1 日至月末；`payroll_date`＝**期间末日**；需求 §4.13 表中「`payroll_date`＝D」改为「＝期间末日」 | 需求 §4.9 与 §4.13 两处不一致：前者写期间末日，后者写 D。期间末日让同月任一日调用都得到同一张单，幂等才成立 |
| 9 | §4.9：月末自动触发是否挂 scheduler | **不挂**；入口只有手动按钮与 S8 调用的函数 | 演示站 scheduler 本就关；自动月结会在演示中途意外生成单据 |
| 10 | §4.2.1：列表批量采纳／忽略可定为不做 | **做**：列表两个批量动作，逐条调同一采纳／忽略方法、逐条报结果 | 演示三条并列时一次处理；实现只是循环 |
| 11 | §4.2.1：不再触发时可加「已过时」标注 | **不加** | 需求说可选；加了要多一个字段与判定，演示不讲 |
| 12 | §4.2.1：来源单据「子表或文本」 | 子表「来源销售订单」（销售订单、行、待展开量） | 可点开核对 |
| 13 | §4.2.3：覆盖 N 天的仓库来源可放宽 | **不放宽**，只算有 `Item Reorder` 行的 物料×仓库 | 与 EOQ 同口径；造数时给要演示的物料建行即可 |
| 14 | §4.2.3：按订单规则的仓库与 MR 类型 | 仓库＝原生函数返回的行仓库（物料默认仓库或物料组默认仓库）；MR 类型取该物料 `default_material_request_type`，为空取 `Purchase`。返回的数量是采购单位，按其 `conversion_factor` 换回库存单位再写建议量 | 需求 §4.2.1 写「无该行的按订单建议取采购」，原生函数已带出物料的默认请购类型，取它更贴近物料设定；为空时回落即需求原意 |
| 15 | §4.2.3：按订单的待展开量 | 销售订单行 `qty − delivered_qty − work_order_qty`（库存单位），**不扣成品库存** | A9。成品库存也会被这张销售订单消耗，扣成品要另判哪些已被别的订单预留，超出本 Stage；演示时成品期初为 0，两者相同。列入回执拿不准处 |
| 16 | §4.6 第 3 条「给每个启用的 System Manager 发站内通知」 | 收件人＝启用的、`Has Role` 含 System Manager 的用户，**并上 `Administrator`**（去重，不含 `Guest`） | Administrator 是演示与开发时实际登录的账号，它的角色表里未必列 System Manager，按角色查会漏掉它 |
| 17 | §5.2：无中式公司时的「无对象」提示不当告警 | `after_migrate` 只在 `ok` 为假时告警；`ok` 在无中式公司时本为真，「无对象」那条只打印、不写 `Error Log`、不发通知 | 测试站常态无中式公司 |
| 18 | §4.11.3：至少覆盖三类单据行 | 覆盖 `Purchase Receipt Item`、`Stock Entry Detail`、`Delivery Note Item` 三类；`Sales Invoice Item`（`update_stock=1`）与 `Purchase Invoice Item` **不做** | 需求下限即三类；发票直接出入库在演示链上不用 |

| 19 | §4.9：薪资项「计件工资」名称中文、英文源词进 csv | 记录名直接取中文 `计件工资`（缩写 `JJGZ`）。它是数据记录名，不经 `_()`，csv 不收 | 记录名不是界面字符串，进 csv 也不会被取用；与中文计量单位（S4）同理 |
| 20 | §4.4：再订货点的 safety_stock「取 §4.3 刚写入的物料级值」 | 照需求；物料勾了「自动计算补货参数」但当次安全库存因提前期缺失记 0 时，再订货点照算（＝d̄_仓×0＋0＝0）并在结果里记「提前期缺失」，**不写**该行 | 写 0 会让 EOQ 从此每天都触发（计划量≤0 恒真），比不写更糟 |
| 21 | §4.12：「每家启用了补货的公司」 | Company 加勾选 `cn_replenishment_enabled`；物料级的安全库存按**当次处理的公司**的仓库合计算。一个物料在两家启用公司都有出库时，安全库存一步跳过该物料并记问题 | `Item.safety_stock` 是全站单值，两家公司各算一次会互相覆盖；演示站只有一家，跳过并报出比静默覆盖好 |

---

## 五、接口契约

只列跨任务、跨模块或供 S8 调用的接口；模块内私有函数由执行者定。签名里的 `TypedDict` 定义在所列文件。

### 5.1 公共结果形态

```python
# frappe_china/replenishment/types.py
class StepResult(TypedDict):
    step: str               # "safety_stock" | "reorder_level" | "suggestions"
    processed: int          # 写入或更新的条数
    skipped: int
    problems: list[str]     # 每条形如「物料 X／仓库 Y：原因」，中文；不 raise

class DailyResult(TypedDict):
    as_of_date: str         # ISO 日期
    companies: dict[str, list[StepResult]]   # 公司名 → 依次三步的结果
    ok: bool                # 全部 problems 为空
```

### 5.2 供 S8 与演示调用的入口（需求 §4.13 接口约定）

```python
# frappe_china/replenishment/daily.py
def run_daily(as_of_date: str | date | None = None, company: str | None = None) -> DailyResult:
    """每日补货计算：依次 安全库存 → 再订货点 → 三规则建议。

    as_of_date 为空取今天。company 为空时处理全部勾了 cn_replenishment_enabled 的公司。
    接口约定（需求 §4.13，S8 生成器须遵守）：
    1. 调用方按日期先后逐日调，且调用时库内单据只到 as_of_date 为止；
       计划量、已订、已请购取调用当下的 Bin，不按日期还原。
    2. 同一 as_of_date 重复调用幂等：建议单按 物料×仓库×规则 更新待定那条，不新增。
    3. as_of_date 晚于今天时 frappe.throw。
    4. 不支持事后单独补算过去某日。
    单个物料出错只进 problems，不中断其它物料；不 commit（由调用方或 scheduler 提交）。"""

@frappe.whitelist()
def run_now(as_of_date: str | None = None) -> DailyResult:
    """表单／列表按钮用。仅 System Manager、Stock Manager；内部调 run_daily。"""

def scheduled_daily() -> None:
    """scheduler_events daily 挂这个；调 run_daily()，结果有 problems 时写一条 Error Log。"""

# frappe_china/production/piece_rate.py
def make_piece_rate_summaries(company: str, as_of_date: str | date) -> SummaryResult:
    """S8 调用：期间＝as_of_date 所在自然月；为期间内每个有计件的员工建并提交一张计件汇总单。
    同员工同期间已有已提交单的跳过并报出。接口约定同 run_daily 的 1～4 条（第 2 条换成「已有即跳过」）。"""

class SummaryResult(TypedDict):
    period: tuple[str, str]
    created: list[str]      # 计件汇总单名
    skipped: list[str]      # 「员工 X：已有 Y」
    problems: list[str]     # 「员工 X：无薪资结构分配」等
```

### 5.3 选 BOM（三处共用，需求 DEC-019）

```python
# frappe_china/production/bom_selection.py
class BomCandidate(TypedDict):
    bom: str
    raw_material_cost: float
    operating_cost: float
    quantity: float
    process_loss_percentage: float
    unit_cost: float        # (raw_material_cost + operating_cost) / quantity / (1 - loss/100)

class BomChoice(TypedDict):
    bom: str | None         # 选中的 BOM；物料无有效 BOM 时为 None
    auto: bool              # 物料勾了 cn_auto_select_bom 才为真；为假时 bom 即原生默认、candidates 为空
    candidates: list[BomCandidate]   # 按 unit_cost 升序

def select_bom(item_code: str, company: str | None = None) -> BomChoice: ...

def default_boms(item_code: str) -> set[str]:
    """原生两种默认 BOM 的并集（A12）。"""

@frappe.whitelist()
def recommend_bom(item_code: str, company: str | None = None) -> BomChoice:
    """前端提示用；读权限：BOM read。"""
```

### 5.4 自检

```python
# frappe_china/install.py
def override_targets() -> tuple[str, ...]:
    """frappe_china.hooks.override_whitelisted_methods 的全部键（取代 WHITELIST_TARGETS 常量）。"""

def after_migrate() -> None:
    """hooks.after_migrate。调 check_app_order()；ok 为假或 check 抛异常时三处告警
    （打印、Error Log、站内通知），不 raise。"""
```

---

## 六、技术假设

需求 §十 LG-001／002／003／005 在本步已调研，结论分别进 HT-003、HT-005、HT-013、HT-008。

| 编号 | 假设内容 | 状态 | 验证方式 | 不成立时 |
|---|---|---|---|---|
| HT-001 | `env/bin/pip install ruff==0.14.10` 能在容器内装上并以 `env/bin/ruff` 运行；`bench setup requirements` 不卸载它 | 未验证（容器内现无 ruff，A 步实测；pip 26.2.1 在） | TS-001 第 1 步实装；再跑一次 `bench setup requirements --python` 后复查 | 暂停反馈 |
| HT-002 | `after_migrate` 钩子在 `bench migrate` 末尾逐 app 执行，抛异常会中断 migrate（故须自吞） | 读码已确认（`frappe/migrate.py:200-203`） | TS-003 测试 | — |
| HT-003 | 替换 `work_order` 模块属性 `split_qty_based_on_batch_size` 后，工单提交建卡（`:1228`）与 `make_job_card`（`:2853`）都用新函数 | **探针已确认**：`WorkOrder.create_job_card` 与解包后的 `make_job_card` 的 `__globals__` 均为该模块字典；全 bench 无别处 import 该名（只读核查） | TS-011 两条路径各一测试 | 暂停反馈（LG-001 退回用户） |
| HT-004 | `before_request` 与 `before_job` 钩子在每个 web 请求、每个后台任务开始时执行，可承载幂等补丁 | 读码已确认（`frappe/app.py:244-245`、`utils/background_jobs.py:269-270`）；`bench execute` 与 `run-tests` 不经这两处，故另在 Work Order `before_submit` 调一次 | TS-011 测试在 `run-tests` 进程里跑，覆盖 `before_submit` 那处 | 暂停反馈 |
| HT-005 | Production Plan `validate`（`doc_events`）里改写 `po_items.bom_no`，保存后保留，下游缺料计算与建工单读到改后的值 | 读码已确认（见 §四 偏离 2） | TS-006 测试 | 暂停反馈（RS-002 退回用户：可退为只管工单与按订单两处） |
| HT-006 | 工单 `before_insert` 对三条建单路径都执行：表单新建、`sales_order.make_work_orders`（`.insert()`）、`production_plan.create_work_order`（`ignore_validate` 下 `insert()`） | 读码已确认（`frappe/model/document.py:480` 在 `run_before_save_methods` 之前） | TS-006 三路径测试 | 暂停反馈 |
| HT-007 | `before_insert` 里改 `bom_no` 后，须重调 `set_work_order_operations()` 与 `set_required_items()`，工序与原料才对应新 BOM；生产计划路径在插入前已按旧 BOM 调过这两个方法（`production_plan.py:939-940`），重调即覆盖 | 读码已确认（两方法都先清表再按 `self.bom_no` 重建，`work_order.py:1456-1530`、`:1726-1738`） | TS-006 测试断言工序行的 `bom` 与原料行属新 BOM | 暂停反馈 |
| HT-008 | 演示站与测试站 `Stock Settings.use_serial_batch_fields`＝1，三类单据行上可直接填 `batch_no` | **探针已确认**两站均为 1（默认值也是 1，`stock_settings.json:426-430`） | — | — |
| HT-009 | 单据 `before_validate`（`doc_events`）改行的 `conversion_factor` 后，原生 validate 用新值重算 `stock_qty`／`transfer_qty`；仅 `uom == stock_uom` 时被重置为 1 | 读码已确认（`stock_controller.py:169-180`、`buying_controller.py:750-757`、`stock_entry.py:760-771`、`document.py:1404-1415`） | TS-010 测试断言派生量 | 暂停反馈 |
| HT-010 | 预置工序行 `hour_rate` 后调 `bom.calculate_cost(save_updates=False, update_hour_rate=False)`，只在内存里得出 `raw_material_cost`／`operating_cost`，不写库；原料价按 `rm_cost_as_per` 现取 | 读码已确认（`bom.py:992-1062、1064-1105`） | TS-005 测试：选择前后各候选 BOM 的库内 `modified` 与成本字段不变 | 暂停反馈 |
| HT-011 | 后道卡经 `db.set_value` 把 `for_quantity` 改小后，操作工按改后数量报工能通过原生提交校验（`job_card.py:907-923`）与前后序校验（`:1368-1430`） | 读码推断，未实跑 | TS-012 测试 | 暂停反馈 |
| HT-012 | 前道 950 完工＋50 损耗、后道按 950 完工后：① 生产入库 950 能过原生校验（`stock_entry.py:1165-1190` 按每道 完工＋损耗 ≥ 入库量判）；② 入库单带 `process_loss_qty`＝50 时，工单 `produced_qty＋process_loss_qty ≥ qty` 即 Completed（`work_order.py:716-719`） | 读码已确认两处判式；**未核**：后道工序行的状态按 完工＋损耗 对比 `Work Order.qty` 判（`:1577-1595`），950＋0 < 1000 会停在 `Work in Progress`，这是否让工单状态被拉回 `In Process`（`:728-730` 只在非 Completed 时看工序状态，读码判为不会） | TS-012 测试走到入库并查工单与工序状态 | 工单能 Completed、只是工序行停在进行中 → 记进 D 回执、不暂停；工单到不了 Completed → **暂停反馈** |
| HT-013 | echarts 5.6.0 的折线图可按数据项设 `itemStyle.color` 实现逐点着色；`dist/echarts.min.js` 以 `frappe.require` 加载后挂出全局 `echarts` | 成熟做法（echarts 文档的 data item 级 `itemStyle`）；frappe-charts 不可行已读码确认（A15） | TS-016 截图 | 暂停反馈（RS-004：改 AC-015） |
| HT-014 | HRMS `Additional Salary` 提交要求员工在 `payroll_date` 前有已提交的 `Salary Structure Assignment`，否则 throw；`currency` 必填须显式传 | 读码已确认（`additional_salary.py:43-78`、json `:171-178`） | TS-013 测试 | — |
| HT-015 | `Workstation Working Hour.hours` 由保存时按起止时刻算出（`workstation.py:97-104`），可直接求和 | 读码已确认。另：`enabled` 字段原生**无任何读取方**（`manufacturing/` 下零处），`total_working_hours` 也不看它；本方案**照原生不看 `enabled`**，与 `workstation.py` 同口径，在 README 已知限制写一句 | TS-014 测试 | — |

---

## 七、接入点与侵入度（需求 §4.18 落定）

| 接入点 | 用什么 | 级 | 登记 |
|---|---|---|---|
| 补货建议单、计件汇总单、两张报表、控制图页面 | 自有 DocType／Report／Page | L2 | — |
| 各新字段 | Custom Field＋fixtures | L1 | — |
| `run_daily`、`after_migrate` | `scheduler_events`／`after_migrate` | L3 | — |
| 提前期同步、选 BOM（工单、生产计划）、工序数量传递、计件取消联动、批次系数复核 | `doc_events` | L3 | — |
| 拆单 | 模块属性替换（A13） | **L4** | README「后端覆盖登记」新节一行＋源码哈希测试 |
| 工单表单的推荐提示、批次系数前端带出、建议单列表批量动作 | `doctype_js`／`doctype_list_js` 追加 | L3 | 只追加、不改上游行为，不登记，回执写明理由 |
| `auto_indent` 置 0 | 配置脚本 | L0 | — |

**README 新增「后端覆盖登记」节**：格式同既有「Desk 前端覆盖登记」（接入点／覆盖文件／作用／依赖上游的什么及锁定 commit／失效症状／复验法）。本 Stage 只有拆单一行。

---

## 八、并行开发说明

不标并行。理由：几乎每个任务都改 `hooks.py`、`fixtures/custom_field.json` 与 `translations/zh.csv` 这三个共享文件；D 步执行者只有一个（Claude）。

---

## 九、执行顺序

```
TS-001 Ruff 基线（单独提交，须用户许可）
  └─ TS-002 模块骨架与字段 fixtures 框架
       ├─ TS-003 覆盖自检 ─────────────────────────────┐
       ├─ TS-004 补货参数 → TS-005 选 BOM → TS-006 三处接入 │
       │        └─ TS-007 安全库存与再订货点             │
       │              └─ TS-008 建议单 → TS-009 每日计算 │
       ├─ TS-010 批次换算                               │
       ├─ TS-011 拆单 → TS-012 工序数量传递             ├─ TS-017 收尾与演示站
       │        └─ TS-013 计件工资                      │
       └─ TS-014 负荷报表 → TS-015 SPC 计算 → TS-016 控制图页面 ┘
```

按任务序号顺序执行即满足全部依赖。

---

## 十、执行纪律（给执行者，随方案走）

1. **切片前反查**：执行每个切片前，对照该切片验收条件检查方案覆盖性——如发现按方案写出的代码无法通过验收条件，暂停反馈，不硬写。
2. **假设先验**：任务依赖 §六 中「未验证」或「读码推断」的假设时，先在测试站验掉再写；不成立按该行「不成立时」处理，写「暂停反馈」的就停下来报用户，不绕路。
3. **中断续跑**：开工即建 D 回执（每个 Part 一份，按 `bricks/receipt.md`），全部任务预填 `⬜未开始`；每个任务做完当场回写。中断后从第一个非 ✅ 行续。执行进度**不回写本方案**。
4. **站点安全**：
   - TS-001～TS-016 **只动 `test.localhost`**，不得对 `erx.localhost` 做任何写操作（含 migrate）。
   - D 步期间不得跑 `docker/up.sh`（`setup.sh` 第 6 段会装到演示站）。确需重建容器时先报用户。
   - 演示站基线（S6 收口态，项目概况「演示站当前状态」）：业务数据全为 0、`Translation` 为 0、科目 266、装序 7 个 app。TS-017 前后各核一次。
   - TS-017 在演示站 migrate 之前先 `docker/backup.sh`，并另存一份到 `docker/backups/保留-S7上线前/`。
5. **测试纪律**：
   - 测试继承 `frappe_china/tests/utils.py` 的 `FrappeChinaTestCase`；不得 import `erpnext.tests.utils`。
   - 测试数据名一律带 `TEST_PREFIX`（`_FCT`），随测试事务回滚；会触发 `frappe.log_error` 的测试，清理只删能证明是自己造的行（开发守则「探针三条纪律」第 1 条）。
   - 手算复核的算例写成测试里的常量期望值（不在测试里用被测函数算期望值）。
   - 每个任务做完跑本任务的测试；每个切片做完跑一次全量 `bench --site test.localhost run-tests --app frappe_china`，与 TS-001 记下的基线比，用例数只增不减、全过。
6. **译名**：新增的 DocType、字段、Select 选项、报表列、页面文案、提示，每加一处同一任务内补 `zh.csv`（A16）；每个切片结束跑 `test_translation_quality`、`test_translations` 与 `translation_check.run`（开发守则「译名自检时机」）。
7. **json 的 `modified`**：自有 DocType／Report／Page／Workspace Sidebar json 每改一次调大 `modified`（开发守则）；Custom Field 走 fixtures，同理调大 fixtures 里该条的 `modified`。
8. **覆盖登记**：TS-011 在同一次改动里登 README「后端覆盖登记」；前端追加脚本在 D 回执写明为何判为追加。
9. **版本管理**：不 commit、不 push、不打 tag，除非用户在对话里显式允许（CLAUDE.md「版本管理操作规则」）。**TS-001 做完即停下来请求提交许可**——它必须先于一切功能改动单独提交（需求 DEC-020）；未获许可不开 TS-002。获许可后 `frappe_china` 仓库提交一次，提交信息只写格式与 lint 修复。其后功能改动全部只写不提交，D 步收尾时整体报给用户裁决。
10. **不静默**：凡「查不到、算不出、对不上」一律进 `problems` 或报错，不得输出 0 或空列表了事（开发守则「静默失败」）。计算类入口不 raise 单物料错误，但每一条都要进返回值。
11. **约定显式化**：每个任务标完成前自问是否确立了新约定（命名、文件位置、错误处理、依赖、跨层调用），有则记进 D 回执「新增约定」节（`bricks/receipt.md` 纪律 6）。
12. **最后一个任务（TS-017）做全量回归**并复核演示站最终状态。
