# P1-S8 数据与操控 —— 开发方案·总纲

**版本**：v1.0｜**日期**：2026-10-20｜**编写者**：Claude（Opus 5.5）
**产出步骤**：P1-S8-R5 · `plannedDev` C 步（`build`）
**来源需求**：[R4 B 需求文档](../R04-需求文档/P1-S8-R4-B需求文档.md) v1.0（下称「需求」）
**状态值与复核建议**：不在本文件——见 [P1-S8-R5-C回执](P1-S8-R5-C回执.md)
**执行者**：Claude（S8 概况「偏离」：D 步不交 CodeX）

> **读法**：本方案是 D 步的唯一权威依据，也是 E 步的核对清单。总纲装跨 Part 的架构决策、偏离、接口契约、技术假设与执行纪律；各 Part 按「切片 → 任务」展开。**凡与需求字面不一致处，以本方案为准**，偏离逐条列在 §四。
> **编号**：切片 `SL-`、任务 `TS-`、技术假设 `HT-` 为本方案内编号。**需求里也有 `TS-`、`AC-`、`LG-` 编号**，引用时一律写「需求 TS-00x」「需求 AC-0xx」「需求 LG-0xx」。决策 `DEC-` 沿用本 Stage 序号。
> **「读码」「探针」「实测」**：「读码」未在站点上跑过；「探针」指本步在测试站以事务内回滚跑过的只读探针（`Spike/P1S8R5-C/`）；「实测」指 R3 SA（`Spike/P1S8R3-SA/`）。行号指 `docker/apps.json` 锁定的 commit。

---

## 一、概述

**做什么**：三块。① `frappe_china` 里修完演示画面上会出错或让数字不对的缺陷（账务、工艺损耗反算、税模板、工时、换 BOM 确认、补货口径与呈现、译名十余处），加一张策略对比报表与侧栏入口；② 新建 `frappe_debug` app，内有一年期场景生成器；③ 同一 app 内的演示框架：配置驱动的浏览器内运行器、场景日期、演示进度、`/crm` 驱动、快照与换库、彩排即预跑，以及九幕配置与客户说明。最后部署到演示站、整场预跑。

**完成标准**：十七个切片的验收条件全部通过（§三），需求 AC-001～AC-029 每条都落在某个切片的验收条件里（§三末覆盖表）。验收一律要有正向证据（测试输出、查询结果、截图、计时记录），不能以「没报错」代替。

**Part 索引**

| Part | 文件 | 内容 | 切片 | 任务 |
|---|---|---|---|---|
| 1 | [Part1](P1-S8-R5-C开发方案-Part1.md) | `frappe_debug` 骨架；`frappe_china` 的缺陷修复、策略对比报表、侧栏、演示站前置配置 | SL-001～SL-010 | TS-001～TS-012 |
| 2 | [Part2](P1-S8-R5-C开发方案-Part2.md) | 场景参数文件与一年期场景生成器 | SL-011 | TS-013～TS-017 |
| 3 | [Part3](P1-S8-R5-C开发方案-Part3.md) | 演示框架、`/crm` 驱动、快照与换库、彩排与预跑、九幕配置与客户说明、收尾 | SL-012～SL-017 | TS-018～TS-026 |

**首个 Phase 方案的四条额外要求**：不适用（P1 首个方案为 S4-R7）。本 Stage 新建了一个 app，故保留一个基础设施切片 SL-001（`frappe_debug` 骨架与装序），它就是需求 TS-001。

---

## 二、关键架构决策（本方案新定，C 步职责内）

| # | 决策 | 理由 |
|---|---|---|
| A1 | **`frappe_debug` 的目录**：注册模块 `Frappe Debug`（目录 `frappe_debug/frappe_debug/`，装 DocType `Demo Progress`、`Scenario Event` 与 Page `demo-rehearsal`）；普通包 `builders/`（建单辅助，生成器与演示命名函数共用）、`scenario/`（生成器）、`demo/`（演示框架服务端）；数据文件 `data/scenario.yaml`（场景参数）与 `data/demo.yaml`（演示配置）；前端 `public/js/demo/`（运行器）与 `public/demo/transit.html`（换库中转页） | ADR-0013「`data/`／`nodes/`／`drivers/`」三层里，`nodes/` 已被 ADR-0014 的配置驱动取代；ADR-0010「共用建单辅助、不共用节点定义」落成 `builders/` 一个包。同 S7 A1「注册模块装 DocType／Page，计算放普通包」 |
| A2 | **两份数据文件都用 YAML**（`PyYAML` 6.0.3 已在 bench 环境，读码确认 `env/lib/.../site-packages/yaml`），加载时整份校验 | 需求 §4.4.1「两份同格式为宜」 |
| A3 | **生成器无内存状态，逐日从库里推导要做什么**：哪些销售订单该排产、哪些采购订单该到货、哪些工单料够可以开工，一律每天查库得出；生成器进程之间不传状态 | 生成器分三段跑，中间插着彩排的现场单据（如第 1 幕的 5000 支订单在第二段由生成器照常发货）；按库推导，三段与现场单据自然衔接，也让任一段可单独重跑 |
| A4 | **原始快照是第三个库**（`{基库}_a{幕}_o`），从不被 `db_name` 指向；换库函数拒绝任何以 `_o` 结尾的目标。主用库 `_m`、备用库 `_b` 都由原始快照克隆 | 需求 §4.4.8 留 C 定、要求「演示中永不被写入」；`.sql.gz` 形态补备用库要先解压再导入（约 31～34 秒，V-01②），第三个库直接 `mariadb-dump｜mariadb`（30～73 秒，V-09），两者相当，库形态少一种文件格式 |
| A5 | **「哪份库干净」的登记放站点私有目录的 JSON 文件**（`sites/{站}/private/frappe_debug/snapshots.json`），读写都在 `frappe.utils.synchronization.filelock("frappe_debug_snapshots")` 内 | 需求 §4.4.8 要求放在快照库之外；文件随站点目录、不进任何库，换库不影响它 |
| A6 | **克隆库用分离的子进程，不用 RQ**：`subprocess.Popen(["sh", "-c", 命令], start_new_session=True)`，完成时由命令自身 `touch` 一个就绪／失败标记文件，登记表读标记判状态 | 克隆是纯数据库命令，不需要 frappe 上下文；RQ worker 跨换库的行为未验（需求 LG-002），克隆不经 worker 就不受它影响 |
| A7 | **生成器以 RQ `long` 队列后台任务跑**，`timeout=10800`，进度与完成信号写站点私有目录的状态文件，前端轮询 | V-02 ③ 实测后台任务＋轮询 2／2；生成期间不换库，LG-002 不涉及；`frappe_china` 的 `before_job` 钩子 `ensure_patched` 在后台任务里打拆单补丁（`PH-P1092`） |
| A8 | **场景日期两层**：① 前端运行器：演示中凡新建表单（含经映射生成的新表单）一出现，即按单据类型填场景日期并勾 `set_posting_time`；② `frappe_debug` 的 `before_insert` 钩子：演示进度为激活态、且不在生成器内时，把服务端代建单据上等于系统今天的业务日期改为场景日期 | 需求 LG-008。子 Agent 读码：上游取「今天」的写法有一百多处 from-import 副本（`nowdate` 114 处、`now_datetime` 41 处），且 `bench serve` 多线程，全局补丁补不全还会串扰；而服务端代建的单据（生产计划建工单、工单提交建工序卡、物料需求转采购订单的服务端路径）都要经 `insert()`，在 `before_insert` 一处兜住即可。钩子是 `doc_events` 追加型（L3），不占覆盖位，符合 ADR-0013 |
| A9 | **演示的「现场／彩排」模式不存库，存浏览器 `sessionStorage`**；库里的演示进度只记幕、步、单据引用、场景日期 | 彩排时存下的快照，现场换过去时模式要是「现场」；模式若在库里，换库后还得改目标库。存浏览器则快照库里的进度与模式无关 |
| A10 | **演示框架的浮窗与遮罩文字写中文字面量，不进 `zh.csv`**（偏离 2） | `frappe_china` 的译名测试 `_app_source_strings()` 只认本 app 的源词，csv 里出现 `frappe_debug` 的键会被当成非本 app 源词、清场时删掉；为它让 `frappe_china` 扫 `frappe_debug` 的源码又违反 ADR-0013 的单向依赖。`frappe_debug` 只在中文演示站装、客户库不装，无多语言需求 |
| A11 | **补货需求口径：出库发生在哪个仓就计在哪个仓，在制品仓的出库不计**。库存凭证计 `Material Issue`、`Material Transfer for Manufacture`、`Manufacture`、`Material Consumption for Manufacture` 四种用途的出库行，但排除仓库属于「在制品仓集合」（生产设置默认在制品仓＋该公司工单用过的 `wip_warehouse`）的行；发货单、销售发票照旧 | 需求 LG-007。线材由发料（转到在制品仓）离开原料仓，计在原料仓——正是再订货点行的仓；完工入库从在制品仓扣料，排除后不重复计。不经在制品仓（`skip_transfer`）的工单直接从原料仓 `Manufacture`，照样计入。见偏离 7 |
| A12 | **安全库存与再订货点取同一套仓库范围**：物料有 `Item Reorder` 行时，安全库存的需求取这些行展开后仓库的并集；没有行时取该公司全部非在制品仓 | 需求 §4.11.2「同一套需求口径与仓库范围」。再订货点＝日均×提前期＋安全库存，日均＞0 时自然大于安全库存（需求 AC-011） |
| A13 | **换 BOM 的界面判据：前端写 `cn_bom_source`**。界面保存（生产计划、新建工单）时由前端弹框并把选择写进行上或单上的 `cn_bom_source`；服务端见到该字段有值就不再改 BOM，为空（程序建单：生成器、按订单补货、销售订单「建工单」）才照 S7 自动选 | 需求 §4.11.1 要分「界面」与「无界面」两路，服务端本身分不出请求来自哪个表单；由前端显式写一个字段，判据唯一 |
| A14 | **计划数量的「人改过」判据**：生产计划明细加三个只读 Custom Field——`cn_demand_qty`（订单待生产量）、`cn_recommended_qty`（上次推荐值）、`cn_recommended_bom`（算推荐值时的 BOM）。需求量或 BOM 与上次不同 → 重算并覆盖；都相同而计划数量≠推荐值 → 视为人改过、不覆盖 | 需求 DEC-037、§4.6.2 留 C 定。子 Agent 读码：原生 `set_pending_qty_in_row_without_reference`（`production_plan.py:185-192`）每次保存把 `pending_qty` 改成 `planned_qty`，不能当判据 |
| A15 | **超产校验用类属性替换**：`WorkOrder.validate_work_order_against_so` 换成自有函数，幂等的 `ensure_patched()` 挂在 `before_request`、`before_job` 与 Work Order `before_validate` 三处；上游源码哈希守卫测试。侵入度 **L4** | 需求 LG-004。子 Agent 读码：它是 `WorkOrder` 的类方法（`work_order.py:645-682`），在 `validate` 里调，保存与提交都走；`before_validate` 在 `ignore_validate` 判断之前（`frappe/model/document.py:1404-1405`），生产计划建工单的路径也经过。ADR-0004 禁的是 `override_doctype_class` 钩子（第 18 行），运行时替换类方法不在其列，但第 28、45 行要求「只能靠改类方法时登记」——登 README 后端覆盖登记，并在 ADR-0004 文末修订记录加一行（TS-004） |
| A16 | **工时口径（OB-048）在工单 `before_validate` 重算**：草稿工单每次保存，对 `bom == 工单 bom_no` 且非固定时间的工序行，`time_in_mins ＝ BOM 工序 time_in_mins × 工单数量 ÷ BOM 数量`，再调 `calculate_operating_cost()` | 需求 LG-004。`set_work_order_operations` 有三个调用方（`work_order.py:1714`、`:2704`、`frappe_china` 的选 BOM），都在保存前；`before_validate` 统一兜在保存时，`ignore_validate` 路径也经过。只跟字段名（L3），不替换方法体 |
| A17 | **工时口径（OB-050）在 Job Card `before_insert` 截短排程行**：有 `scheduled_time_logs` 且本卡数量小于工单数量时，把排程行截到「工序时间 ÷ 工单数量 × 本卡数量」 | 读码：`create_job_card` 的 `time_required` 本已按比例（`work_order.py:2985`），错在排程用整道工序时间排每张卡（`job_card.py:544-556`），随后 `before_save` 的 `set_expected_and_actual_time`（`:926-950`）把 `time_required` 改回排程合计。截短在 `before_insert`，早于 `before_save`；且 `prepare_data_for_job_card`（`work_order.py:1243-1245`）读的是同一个文档对象的末行，下一张卡从截短后的止时排起 |
| A18 | **损耗率的整数精度规则（需求 LG-003）**：库存单位须为整数时，整体损耗率取「按 9 位小数存下后、BOM 数量 × 它 ÷ 100 恰为整数」的最大值，从 `floor(数量 × 理论值 ÷ 100)` 起向下逐一试；试到 0 都不行则整体值置 0 并提示 | 探针（`Spike/P1S8R5-C/probe_lg003*.py`）：4.9303 与 4.93 在数量 1000 时被拒，4.9 能存；直接「向下取整回算」在数量 300、1234 时首次能存、重存被拒（库里按 9 位存），数量 3、1500 时首次就被拒（浮点）。故判据要按存库精度算、并用与原生同一个判式 `qty % 1 != 0` |
| A19 | **建单辅助函数的单据日期统一一个入口**：`builders.dates.dated(doc, day, time=None)` 按 meta 设 `set_posting_time`、`posting_date`、`posting_time` 或 `transaction_date` | V-04 已用的写法（`V04-day-generator.py:56-63`）；生成器与命名函数共用，日期写法只有一处 |
| A20 | **策略对比报表放 `Stock Plus` 模块**（`frappe_china/stock_plus/report/replenishment_strategy_comparison/`），带一张「库存相关总成本」柱状图 | 补货属库存域（S7 A1）；需求 §4.14 留「是否加图」，一张图让第 8 幕一眼看出总成本高低，图不另造数 |

---

## 三、切片划分与验收（索引；完整验收条件在所在 Part）

| 切片 | 功能点（需求编号） | 验收条件要点 | Part |
|---|---|---|---|
| **SL-001** `frappe_debug` 骨架与装序（基础设施，豁免「用户可感知」） | 需求 TS-001、`PH-P1074`；A1 | 测试站装上后在末位、`check_app_order` 为真；全仓 grep `frappe_china` 无 `frappe_debug`；`reorder_installed_apps` 的清缓存挂 `after_commit`、回滚时不清 | 1 |
| **SL-002** 完工入库账务 | 需求 TS-002、DEC-015／016、BR-008 | 两公司 `410199`；完工入库 GL 无损益行、`400101` 相抵；`400101` 类型空；银行类收付款方式带 `1002`；迁移只补空值；非中式公司不动 | 1 |
| **SL-003** 工艺损耗反算 | 需求 TS-003、DEC-013／014／037 | 5264／5261；整体值只读、整数单位按 A18；超产 5264 能交、5265 被拦、第二张合计超被拦；人改不覆盖、需求量或 BOM 变了重算；按订单 45.7 kg；哈希守卫 | 1 |
| **SL-004** 税模板沿用与改名 | 需求 TS-004、DEC-018／019 | 报价单不含税→订单不含税；CRM 新建客户税种取报价单；9 税种 12 模板改名、税率科目规则不变；测试旧名全改 | 1 |
| **SL-005** 工时口径 | 需求 TS-005、OB-048／050／025 | 250／90／180；开产能计划时三张卷簧卡 100／100／50；负荷报表一致；BOM 工序表默认列 | 1 |
| **SL-006** 换 BOM 人确认 | 需求 TS-006、OB-046 | 界面保存弹框、不确认不换；评论四类来源；程序路径照 S7 自动 | 1 |
| **SL-007** 补货口径与呈现 | 需求 TS-007、OB-082／083／037／038 | 再订货点＞安全库存＞0 且同一序列；发料与完工不重复计；弹窗按物料列旧值→新值与原因；列表物料号；子表列与依据项中文 | 1 |
| **SL-008** 演示画面译名与显示 | 需求 TS-008、OB-024／029／039／042／059／068～071、`PH-P1097` | 逐项中文或按要求显示（含截图）；0.004 存得进；首桶标签取起算日 | 1 |
| **SL-009** 策略对比报表与侧栏入口 | 需求 TS-009／010、DEC-035、OB-009／067／031 | 三段四列与手算一致（含天数折算）；缺料判定；侧栏 14 个新入口；带 `sidebar` 参数落在业务流程 | 1 |
| **SL-010** 演示站前置数据 | 需求 TS-011、OB-005／016、DEC-024 | 性别称呼、批号开关、Administrator 中文名；脚本重跑「无改动」 | 1 |
| **SL-011** 一年期场景生成器 | 需求 TS-012、CR-012、DEC-011／012／026／038／039 | 参数校验；一年全单据提交、GL／SLE 相符；日期不减；三规则依次；结转、底稿、折旧月月有；评分补齐；无重叠无跨天；SPC 子组 ≥25；第 6、9 幕前置条件成立；耗时记录 | 2 |
| **SL-012** 演示框架核心 | 需求 TS-013、CR-008、`PH-P1003` | 配置校验开播前报错；通用动作各一例；场景日期不出 OB-075；`save_as` 跨刷新可用；快捷键与浮窗 | 3 |
| **SL-013** `/crm` 驱动 | 需求 TS-014、DEC-034 | 10 次彩排次次完成；读回不符时重填、再不符走接口；`frappe_china` 未改 | 3 |
| **SL-014** 快照与换库 | 需求 TS-015、DEC-005／007／031～033 | 快进 ≤10 秒、首请求即 Administrator、10 次全成；重来两次都干净；原始快照拒写；回到演示前、清理 | 3 |
| **SL-015** 彩排与整场预跑 | 需求 TS-016、DEC-008 | 无人干预跑完九幕、每幕三库；注入错误停下报幕与步；记录总耗时 | 3 |
| **SL-016** 九幕配置与客户说明 | 需求 TS-017／018、DEC-004／025 | 九幕按清单跑通；讲解词无「今天」；九页 PDF | 3 |
| **SL-017** 收尾 | 需求 TS-019 | 全量回归只增不减；演示站部署与新清洁基准；整场预跑验收；用户现场演一遍 20～30 分钟；LG-001 实测 | 3 |

执行每个切片前，对照该切片验收条件检查方案覆盖性——如发现按方案写出的代码无法通过验收条件，暂停反馈，不硬写。

**需求 AC 覆盖表**（E 步据此核「需求验收无遗漏」）

| 需求 AC | 落在 | 需求 AC | 落在 | 需求 AC | 落在 |
|---|---|---|---|---|---|
| AC-001 | SL-002 ①② | AC-011 | SL-007 ①～④ | AC-021 | SL-012 ③④⑤ |
| AC-002 | SL-002 ③ | AC-012 | SL-008 ① | AC-022 | SL-014 ①～③ |
| AC-003 | SL-002 ④ | AC-013 | SL-008 ②～⑩ | AC-023 | SL-014 ④⑤ |
| AC-004 | SL-003 ①～③ | AC-014 | SL-009 ⑤⑥、SL-016 ③ | AC-024 | SL-013 ① |
| AC-005 | SL-003 ④ | AC-015 | SL-010 ①～③、SL-002 ⑤ | AC-025 | SL-015 ①～③ |
| AC-006 | SL-003 ⑤ | AC-016 | SL-001 ①～③ | AC-026 | SL-017 ④ |
| AC-007 | SL-003 ⑥ | AC-017 | SL-009 ①～④ | AC-027 | SL-016 ④ |
| AC-008 | SL-004 ①～③ | AC-018 | SL-011 ②③④ | AC-028 | SL-017 ⑤ |
| AC-009 | SL-005 ①～③ | AC-019 | SL-011 ⑤～⑨ | AC-029 | SL-017 ① |
| AC-010 | SL-006 ①② | AC-020 | SL-012 ① | | |

---

## 四、相对需求文档的偏离与补定

需求里写「C 步定」的各处，本方案的取法见 §二与各任务；下表只列**改了需求字面**或**需求没提、本方案补上**的。

| # | 需求原文 | 本方案 | 理由 |
|---|---|---|---|
| 1 | §4.4.8「九幕约 18 个库，每份约 0.1 GB，合计约 2 GB」 | 每幕三个库（原始、主用、备用），**九幕 27 个库，约 2.7 GB** | A4：原始快照取第三个库的形态。演示机 D 盘余 150 GB |
| 2 | §4.4.6「浮窗与提示文字进 `zh.csv`」；§3.1 ADR-0006「演示框架的浮窗文字也是」 | `frappe_debug` 的浮窗、遮罩、中转页文字写**中文字面量** | A10 |
| 3 | §4.8「`frappe_china/tests` 里按旧名断言的用例（5 个文件 13 处）」 | **5 个文件 32 行**：`tests/dataset.py` 291／333／339，`test_closing.py` 143／155，`test_e2e_minimal.py` 29／47／64／200，`test_taxes.py` 14-18／21-27／75／80，`tests/utils.py` 14-22 | 子 Agent grep 实数；行号以 D 步执行时为准 |
| 4 | §4.8 销项 5、进项 7 个模板「改为好懂的名字」 | 模板 `title` 与税种同名规则：销项「13% 专票 含税价」等、进项同名；记录名随 `title - 缩写` 改（`rename_doc`） | 需求只给税种名；模板 `title` 原本就等于税种名（子 Agent 读 `tax_setup.json`），沿用同一对应 |
| 5 | §4.11.1「无界面路径照 S7 自动选用」 | 销售订单「建工单」（`make_work_orders`）也归无界面路径，照 S7 自动选、评论记「按成本自动选用」 | A13。该按钮由服务端一次建多张工单，无表单可弹框；演示走生产计划，不经这条路 |
| 6 | §4.6.1「处置手段 C 步实测后定」 | A18；**试到 0 仍不合格时整体值置 0、保存时出黄色提示**「整数单位下无法表示该损耗率，请调整 BOM 数量」；计划数量反算仍按工序损耗率算，不受影响 | 数量 1234、7 这类按 9 位精度取不到大于 0 的合格值（探针）。置 0 只影响完工入库的原生损耗、BOM 成本与选 BOM 三处，列进回执拿不准处 |
| 7 | §4.11.2「原料需求按生产消耗计」「消耗如何归属到再订货点行的仓库，C 步定」 | A11：按出库发生仓计、在制品仓出库不计；即线材的需求日是**发料日**而非完工日 | 需求要的是「生产消耗」；发料比完工早一两天，日需求序列整体前移，对 90 天均值与标准差影响可忽略；换来的是归属天然落在原料仓、不重复计 |
| 8 | §4.14 缺料次数「其所需原料在发料仓的结存不足」 | 只看**所选物料**中的所需原料；另加一张「库存相关总成本」柱状图（A20） | 报表按物料筛选，缺料也按同一物料集判，口径一致；生成器的推迟判定也只看补货物料（Part2 TS-016） |
| 9 | §4.4.5 演示进度「至少记：当前幕、当前步、引用表、本幕场景日期」 | 照需求；**不记现场／彩排模式**（A9） | A9 |
| 10 | §4.4.8「改 `db_name` 与抄会话行」由同一套换库方法 | 抄会话行用**站点数据库用户**连目标库（克隆时已授权）；只有建库、授权、删库用 root | 换库在演示现场频繁调用，root 只留给建删库；root 口令从站点配置 `root_password` 读（只在演示站与开发临时站设，不进 git） |
| 11 | §4.3.2 第 2 条「服务端代建的单据也须取场景日期，手段 C 步定」 | A8 两层；服务端那层**只改等于系统今天的日期字段**，显式传了日期的不动 | 生成器与人显式给的日期不能被冲掉；生成器内另有标志直接跳过 |
| 12 | §4.9.2「供应商评分：`creation` 改到场景起点后建按月记分卡」 | 记分卡在**第三段生成的末尾**建 | 原生只补「期末日 ≤ 系统今天」的期（`supplier_scorecard.py:214`）；预跑当天＝E，早建会补出场景里尚未发生的月份。第 9 幕在 E，记分卡在 E 前建好即可 |
| 13 | §4.9.2 每月折旧普通凭证（科目未写） | 借 `5602070 管理费用_资产折旧摊销费`、贷 `1602020 累计折旧`；期初借 `1002`／固定资产明细、贷 `3001 实收资本` | 与 `frappe_china` README「已知限制」生产设备折旧暂落 `5602070` 同口径；进会计复核 `SH-P1S8005` |
| 14 | §4.12 OB-031「若演示配置从业务流程侧栏进入即可避开，则只在配置里处理」 | 第 1 幕不点 CRM 的「创建报价单」（它开新标签页，RS-008）；由命名函数在**同一标签页**打开同一个地址（`/desk/quotation/new?…&crm_deal=…`），并带 `sidebar=Business Flow` 参数（HT-011） | 读码：CRM 按钮由 CRM 写进库的表单脚本 `window.open(url,'_blank')`（`erpnext_crm_settings.py:751`），改它要占 CRM 的覆盖位或改它的记录。非演示场景下的 OB-031 未修，并入 `SH-P1S8007` |
| 15 | §4.4.8「两份都用过且后台未补完时，遮罩等补完（约 30～73 秒）」 | 照需求；补库由 A6 的子进程做，不经 RQ | A6 |
| 16 | 需求 LG-009「第 7 幕交付的是第 1 幕的订单还是另一张」 | **另一张**：生成器保证有一张交货日＝D2、成品已入库的订单，第 7 幕交它；第 1 幕的订单由生成器在第二段按交货日照常发货 | A3；第 1 幕订单在第 5 幕已完工，第二段若不发货，账上会挂着一张三个月不交的单 |
| 17 | 需求 LG-009「第 9 幕看历史价与评分用哪个原生视图」 | 历史价：物料价格（`Item Price`）列表按物料、采购价目表筛选、按 `valid_from` 降序；评分：供应商评分（`Supplier Scorecard`）列表 | 两者原生列表即有供应商、价格／分数、日期列；侧栏补「供应商评分」入口（业务流程侧栏现无，子 Agent 核过） |
| 18 | §4.4.3 动作集合 | 不加新动作；表单保存时出现的确认框与选 BOM 弹框，由 `save`／`submit` 的 `on_dialog` 参数指明怎么答 | 弹框出现在保存的 Promise 里，另起一步答不到；由同一步并发处理，配置里仍是一步 |
| 19 | §4.3.2 第 3 条「第 6 幕的计件汇总由框架以本幕场景日期调 `make_piece_rate_summaries`」 | 第 6 幕以 **D2 的前一天**（上月末）调用 | D2 是月初第一个工作日，按 D2 调得到的是当月、几乎无报工；老板要看的是上个月的计件。上月末早于 D2，满足「不晚于今天」与按时序调用的约定 |

---

## 五、接口契约

只列跨任务、跨模块或跨前后端的接口；模块内私有函数由执行者定。

### 5.1 `frappe_china`：损耗反算（三处共用）

```python
# frappe_china/production/process_loss.py
def operation_loss_rates(bom_no: str) -> list[float]:
    """按 BOM Operation.idx 升序返回各道 cn_process_loss_percentage（百分数，空记 0）。"""

def overall_loss_percentage(bom_no_or_doc) -> float | None:
    """1 − ∏(1 − p_i/100)，×100 返回；全部工序为空返回 None（整体值照旧手填）。"""

def whole_number_loss_percentage(quantity: float, theoretical: float) -> tuple[float, bool]:
    """A18。返回 (可存的整体值, 是否被迫置 0)。判式与 bom.py:1371 相同：flt(quantity) * p / 100 % 1 == 0，
    p 先 flt(p, 9)。从 floor(quantity*theoretical/100 + 1e-9) 起向下试，到 0 为止。"""

def required_input_qty(bom_no: str, output_qty: float) -> float:
    """需求 §4.6.2：有工序损耗率时从末道往前逐道 ceil(产出 ÷ (1 − p_i/100))；全空时
    ceil(需求 ÷ (1 − 整体/100))。产品库存单位非整数单位时 ceil 改为 flt(x, 数量精度)。
    ceil 前减 1e-9，防 5000.0000001 被取成 5001。"""
```

### 5.2 `frappe_china`：补货结果的逐物料明细（OB-083）

```python
# frappe_china/replenishment/types.py（追加；StepResult 原有键不变）
class ChangeRow(TypedDict):
    item_code: str
    warehouse: str | None    # 安全库存为 None
    field: str              # "safety_stock" | "warehouse_reorder_level" | "suggested_qty"
    old: float | None
    new: float | None
    outcome: str            # "updated" | "unchanged" | "created" | "not_triggered" | "skipped"
    reason: str             # 中文一句，如「计划量 30 高于再订货点 19.909，不出建议」

class StepResult(TypedDict):     # 新增可选键
    ...
    changes: list[ChangeRow]
```

### 5.3 `frappe_debug`：演示框架的服务端接口

```python
# frappe_debug/demo/config.py
ACTIONS: Final = ("open_new", "open_doc", "open_list", "open_report", "open_page",
                  "set", "add_row", "click", "save", "submit", "wait", "highlight", "call")

@frappe.whitelist()
def get_demo_config() -> dict:
    """读 data/demo.yaml 与 data/scenario.yaml，校验后返回
    {"acts": [...], "dates": {"S":…, "D1":…, "D2":…, "E":…}, "segments": [...], "scene_date_fields": {...}}。
    校验失败 frappe.throw，消息逐条列「第 N 幕第 M 步：原因」。仅 Administrator。"""

def validate_config(cfg: dict, dates: dict) -> list[str]:
    """纯函数：未知动作、缺必填键、日期引用不存在、save_as 先用后定义、同名 save_as 重复。
    命名函数名不在服务端校验（在前端注册表），前端开播前再校一次。"""

# frappe_debug/demo/progress.py
@frappe.whitelist()
def save_progress(act: int, step: int, refs: str | dict | None = None, scene_date: str | None = None) -> None:
    """写 Single DocType「Demo Progress」并 commit。仅 Administrator。"""

def get_progress() -> dict:     # extend_bootinfo 钩子用：{"active", "act", "step", "refs", "scene_date"}

# frappe_debug/demo/switch.py
@frappe.whitelist(methods=["POST"])
def switch_to_act(act: int, purpose: str) -> dict:
    """purpose ∈ {"forward", "restart", "jump"}。按 §4.4.8「何时换库」表选目标库：
    返回 {"status": "switched", "db": 目标库, "route": 该幕起始路由} 或 {"status": "waiting"}（两份都用过、补库中）。
    仅 Administrator；目标以 _o 结尾即 throw。"""

@frappe.whitelist(methods=["POST"])
def switch_to_db(db_name: str) -> dict:      # 预跑开始切到工作库、「回到演示前」用；同样拒 _o

@frappe.whitelist()
def switch_status() -> dict:     # 中转页轮询：{"db": 当前连接库, "user": session user}

# frappe_debug/demo/snapshot.py
@frappe.whitelist(methods=["POST"])
def take_snapshot(act: int) -> dict:
    """先 commit，再同步克隆当前库 → {基库}_a{act}_o（等完成），再分离子进程克隆 _o → _m、_o → _b。
    登记表写三份及状态。返回 {"orig": …, "elapsed_s": …}。"""

@frappe.whitelist()
def snapshot_status() -> dict:   # 全部幕三份库的状态，预跑末尾等全部就绪用

@frappe.whitelist(methods=["POST"])
def drop_snapshots() -> dict:    # 「清理快照库」：当前 db_name 不在其中才删

# frappe_debug/scenario/runner.py
@frappe.whitelist(methods=["POST"])
def start_generate(from_date: str, to_date: str) -> dict:
    """enqueue(queue="long", timeout=10800) 生成 [from_date, to_date]；返回 {"job_id"}。仅 Administrator。"""

@frappe.whitelist()
def generate_status(job_id: str) -> dict:   # {"state": "running"|"done"|"failed", "day": 已造到哪天, "error": …}

def generate(from_date, to_date, scenario: "Scenario | None" = None, commit: bool = True) -> "GenerateResult":
    """逐日造单（Part2）。commit=False 供测试在事务内跑。"""
```

### 5.4 `frappe_debug`：前端运行器的约定

```js
// frappe_debug/public/js/demo/runner.js（app_include_js）
frappe.provide("frappe_debug.demo");
frappe_debug.demo.functions = {};          // 命名函数注册表：name → async (ctx, args) => any
frappe_debug.demo.register = (name, fn) => {...};
// ctx = { act, step, refs, dates, scene_date, frm: () => cur_frm, call: frappe.xcall, wait_for(pred, ms) }
// 模板展开：步骤里的字符串值支持 "${ref.po1}"、"${date.D1}"、"${scene_date}"。
// 步骤执行顺序：显示 say → 执行动作 → save_progress(act, step+1, refs) → pause: presenter 时等推进键（彩排不等）。
```

---

## 六、技术假设

需求 §十 LG-003／004／005／007／008 在本步已调研，结论分别进 A18、A15／A16／A17、HT-012、A11、A8。

| 编号 | 假设内容 | 状态 | 验证方式 | 不成立时 |
|---|---|---|---|---|
| HT-001 | 完工入库的「附加费用」行（`additional_costs`）的费用科目，原生按 Company `expenses_added_to_stock_account` 带出；设好 `410199` 后不再要手填 | 读码（A 步依据；`stock_controller.py:929-965` 有读取方，带出到附加费用行的那一处未定位） | TS-002 测试：建一张有工序成本的完工入库、不填附加费用科目、提交成功且 GL 有贷 `410199` | 在 Stock Entry `before_validate` 给空的附加费用行补 `410199`，回执记偏离 |
| HT-002 | Stock Entry `before_validate` 把 Manufacture／Repack 全部行 `expense_account` 改为 `400101` 后，原生不再改回（只在为空时填，`stock_entry.py:849-851`、`stock_controller.py:1001-1002`），GL 里 `400101` 借贷相抵 | 读码 | TS-002 测试断言 GL 行 | 暂停反馈 |
| HT-003 | A18 算出的整体值在首次保存与重新保存时都过原生校验 | 读码＋探针（探针只验了单点，算法本身未跑） | TS-003 测试：数量 1000／1500／300／2500／1234／7 各存两次 | 暂停反馈 |
| HT-004 | 给 `WorkOrder` 类赋值 `validate_work_order_against_so` 后，已建实例与新实例都走新函数；在 Work Order `before_validate` 里调 `ensure_patched` 能赶在本次 `validate` 之前 | 读码（子 Agent；当前上游源码 sha256 `dd34f0798ed5604f5ac1c1038ad6b6c18d643eebaceadbb6f93e49851959b6a6`） | TS-004 三路径测试（表单、生产计划建工单后提交、`run-tests` 进程） | 暂停反馈 |
| HT-005 | 生产计划从销售订单带出的明细行有 `sales_order_item`，可按原生同式（`production_plan.py:397-399`）算出订单待生产量 | 读码 | TS-004 测试 | 暂停反馈 |
| HT-006 | frappe 表单脚本的 `before_save` 处理器返回 Promise 时，保存会等它 resolve；reject 或 `frappe.validated=false` 时中止保存 | 读码已确认（`form.js:866-880` 以 `run_serially` 依次跑 `validate`、`before_save`，之后才查 `frappe.validated`；`script_manager.js:114-115` 处理器返回 Promise 即返回它） | TS-007 测试站表单上实点一次 | 改为在「取物料」与 BOM 变化时弹框（不在保存时），回执记偏离 |
| HT-007 | 开产能计划时，Job Card `before_insert` 截短 `scheduled_time_logs` 后：`time_required`＝截短后合计；同一工序的下一张卡从截短后的止时排起 | 读码（A17） | TS-006 测试（测试站临时开 `disable_capacity_planning=0`，测试内还原） | 暂停反馈 |
| HT-008 | frappe v16 的 `extend_bootinfo` 钩子在 `bootinfo.success_action` 写好之后执行，可就地改其 `message` | 读码已确认（`sessions.py:146` 调 `get_bootinfo`，其中 `boot.py:111` 写 `success_action`；`sessions.py:169-170` 之后才跑 `extend_bootinfo`，且在读 redis 缓存之后、每次请求 boot 都跑） | TS-009 测试 | 改为前端在 `desk_patches.js` 包装 `SuccessAction.prototype.show_alert` 翻译 message，并登记前端覆盖 |
| HT-009 | OB-068 SPC 报表列名英文的原因：`zh.csv` 已有这 6 个列名与摘要标签的键（本步读 csv 核过），R2 看到英文另有原因（缓存、会话语言或报表经 prepared report） | 未验证 | TS-009 先在测试站以中文会话跑报表复现，定位原因后修 | 原因在上游、本 app 改不了时暂停反馈 |
| HT-010 | Currency 型 Custom Field 设 `precision: "4"` 后存 0.004 不被舍入、界面显示 4 位 | 读码（frappe 取 `df.precision` 优先） | TS-009 测试 | 改为 Float 型、`precision: "4"`，迁移旧值 |
| HT-011 | 地址带 `sidebar=Business Flow` 时 desk 选用该侧栏（`sidebar.js:327-329` 读 `frappe.route_options.sidebar`，`router.js` 把查询参数写进 `route_options`） | 读码（子 Agent，未实测） | TS-011 浏览器探针 | 命名函数在新表单打开后调 `frappe.app.sidebar.setup("Business Flow")`（若有该接口），否则记入回执、第 1 幕侧栏不换 |
| HT-012 | `frappe_debug` 的 `update_website_context` 在 `frappe_china` 之后执行（按装序，`base_template_page.py:69-75`），能读到 `frappe_china` 改过的 `context.template`；Jinja `{% include 变量 %}` 可引入前一层模板 | 读码 | TS-020 测试：中文会话与英文会话各取一次 `/crm` 页面源码，含运行器脚本 | 暂停反馈（需求 LG-005 的备选：`frappe_china` 加通用钩子名，要改 `frappe_china`） |
| HT-013 | CRM 建客户经 `erpnext/crm/frappe_crm_api.py:141` 的 `create_customer`，插入前 `crm_deal` 已赋值（白名单含它，`:128-137`），故 Customer `before_insert` 能据此找到报价单 | 读码 | TS-005 测试直接调该函数 | 暂停反馈 |
| HT-014 | 草稿 Job Card 只写 `scheduled_time_logs`（无 `time_logs`）保存时不做工位重叠校验、状态仍为 Open，`expected_start_date` 与 `time_required` 由排程行得出 | 读码（`job_card.py:926-950`；重叠校验只在 `validate_time_logs`） | TS-016 测试 | 第 6 幕的超载改由「工单计划开工日」承载，负荷报表另行处理，暂停反馈 |
| HT-015 | 换库后 RQ worker 与 scheduler 的行为（需求 LG-002）：worker 按进程缓存站点配置 60 秒（`frappe/config.py:149`），换库后 60 秒内入队的任务可能写进旧库 | 未验证 | **D 待验表**，TS-021 开写前由 SA 验 | DEC-031 失效条件：无法规避时暂停反馈 |
| HT-016 | 克隆出的库给站点数据库用户授权后，用站点用户连目标库抄会话行可行 | 读码（frappe 授权写法 `db_manager.py:33-44`；V-01② 抄会话用的是 root） | TS-021 测试 | 改用 root 抄会话，回执记偏离 |
| HT-017 | 运行器用的快捷键 `right`、`alt+r`、`alt+h`、`alt+1`～`alt+9` 在 desk 里无既有绑定 | 读码（子 Agent：列表页占 up／down／enter／space，全局占 escape／enter／ctrl+up／down，未见 left／right／alt+数字） | 运行器启动时自查 `frappe.ui.keys` 的已注册表，撞键即控制台报错并停 | 换键，回执记偏离 |
| HT-018 | `/assets/frappe_debug/demo/transit.html` 由 `SharedDataMiddleware`（`frappe/app.py:572`）直出、不跑 frappe 脚本，页内带 csrf 头的 POST 能调 whitelisted 方法 | 读码；V-01② 用的是 `/api/method/…status_file` 页，不是 `/assets` | TS-022 浏览器探针 | 中转页改用 frappe_debug 的一个 whitelisted 方法返回纯 HTML（同 V-01② 做法） |
| HT-019 | 一年场景（每月约 400～500 张单据，含结转、补货计算、计件、CRM、物料需求）在 90 分钟内造完 | 未验证（V-04 单链 21.4 分钟是下限） | TS-017 实跑计时 | 超过 2 小时：先查最慢的单据类型；仍超则暂停反馈（RS-005） |
| HT-020 | 生成器关产能计划（`disable_capacity_planning=1`，V-04 同）并用「工位空闲时段分配器」排报工时间，可避开 `OverlapError` | V-04 实测（关产能计划仍报重叠，因而需要分配器）；分配器本身未验证 | TS-015 测试：同工位同日 12 张卡 | 暂停反馈 |
| HT-021 | `frappe.utils.pdf.get_pdf` 在容器内渲染中文无乱码 | 已验证（S4 法定报表 PDF 同一条路，`statements/printing.py`） | — | — |
| HT-022 | 客户的 `tax_category` 有值时，原生 `get_party_details`（`accounts/party.py:163-176`）按税规则取到报价单那个模板 | 读码 | TS-005 测试 | 暂停反馈 |

---

## 七、接入点与侵入度（需求 §4.21 落定）

| 接入点 | 用什么 | 级 | 登记 |
|---|---|---|---|
| 策略对比报表 | 自有 Report | L2 | — |
| BOM 工序损耗率、计件单价精度、生产计划明细三字段、`cn_bom_source` 两处 | Custom Field＋fixtures | L1 | — |
| BOM 工序表默认列（OB-025） | Property Setter＋fixtures | L1 | — |
| 整体损耗率、计划数量反算、差异科目统一、客户税种、工时重算、排程截短、换 BOM 来源 | `doc_events`（`before_validate`／`validate`／`before_insert`） | L3 | — |
| 生产计划与工单的换 BOM 弹框、计划数量推荐提示、补货弹窗、计件弹窗 | `doctype_js`／`doctype_list_js` 追加 | L3 | 只追加不改上游行为，回执写明 |
| Success Action 译名 | `extend_bootinfo`（HT-008 不成立时改前端包装） | L3 | 改前端时登 Desk 前端覆盖 |
| 对账报表无差异提示（OB-042） | `desk_patches.js` 包装 `QueryReport.prototype.get_no_result_message` | 前端覆盖 | README「Desk 前端覆盖登记」一行 |
| 超产校验 | 类属性替换（A15） | **L4** | README「后端覆盖登记」一行＋哈希守卫；ADR-0004 修订记录一行 |
| 建账默认、`400101` 类型、银行科目、税种改名 | 数据文件＋迁移补丁 | L0～L1 | — |
| `frappe_debug` 全部 | 自有 app（客户库不装）；`update_website_context`、`extend_bootinfo`、`doc_events`、`app_include_js` 都是追加型 | 不计入客户库侵入度 | — |

---

## 八、并行开发说明

不标并行。理由：Part1 几乎每个任务都改 `frappe_china` 的 `hooks.py`、`fixtures/custom_field.json`、`translations/zh.csv`；Part2、Part3 都改 `frappe_debug/hooks.py`；D 步执行者只有一个。

---

## 九、执行顺序

```
TS-001 frappe_debug 骨架与装序
  └─ TS-002 账务 ─ TS-003 损耗率 ─ TS-004 反算与超产 ─ TS-005 税模板 ─ TS-006 工时
       ─ TS-007 换 BOM 确认 ─ TS-008 补货口径 ─ TS-009 译名 ─ TS-010 对比报表 ─ TS-011 侧栏
       ─ TS-012 前置数据                                   （硬次序②：以上全部早于生成器）
  └─ TS-013 场景参数 ─ TS-014 主数据与期初 ─ TS-015 每日全链 ─ TS-016 每月与缺料
       ─ TS-017 生成器入口与一年实跑（s8dev 站）
  └─ TS-018 演示配置与进度 ─ TS-019 desk 运行器 ─ TS-020 /crm 驱动
       ─ [D 待验表：HT-015／LG-002] ─ TS-021 快照与换库服务端 ─ TS-022 换库前端
       ─ TS-023 彩排与预跑 ─ TS-024 九幕配置 ─ TS-025 客户说明 ─ TS-026 收尾与演示站
```

按任务序号顺序执行即满足全部依赖（需求硬次序②由 TS-013 起排在 TS-002～TS-012 之后保证；需求 TS-013 框架只依赖 TS-001，排在生成器之后不违反依赖，只是串行）。

---

## 十、执行纪律（给执行者，随方案走）

1. **切片前反查**：执行每个切片前，对照该切片验收条件检查方案覆盖性——如发现按方案写出的代码无法通过验收条件，暂停反馈，不硬写。
2. **假设先验**：任务依赖 §六 中「未验证」或「读码」的假设时，先验掉再写；不成立按该行「不成立时」处理，写「暂停反馈」的就停下来报用户。**HT-015 必须走 D 待验表转 SA**（新 Session 做），拿到填回再写 TS-021；不阻塞的 TS-018～TS-020 可先做。
3. **中断续跑**：开工即建 D 回执（每个 Part 一份，按 `bricks/receipt.md`），全部任务预填 `⬜未开始`；每个任务做完当场回写。中断后从第一个非 ✅ 行续。执行进度**不回写本方案**。
4. **站点安全**：
   - 单测一律在 `test.localhost`。不得对 `erx.localhost` 做任何写操作（含 migrate、装 app、改站点配置），直到 TS-026。
   - **生成器整年实跑、演示框架端到端（换库、彩排）在临时站 `s8dev.localhost`**：TS-017 开头由演示站清洁基准备份建起（同 R3 SA 建 `sa.localhost` 的做法），容器内以单进程 `bench serve --port 6787` 服务（`compose.yaml:59` 已映射 6787）；用完不删，留到 TS-026 结束后由用户定。浏览器探针写之前先断言 `frappe.boot.sitename` 是目标站（开发守则）。
   - `root_password` 只用 `bench --site s8dev.localhost set-config root_password …` 写进该站 `site_config.json`（`frappe-bench/` 不进 git），口令不写进任何受管文件、回执只写「已设」。
   - D 步期间不得跑 `docker/up.sh`。确需重建容器时先报用户。
   - TS-026 在演示站动手前先 `docker/backup.sh`，另存到 `docker/backups/保留-S8上线前/`。
5. **测试纪律**：
   - `frappe_china` 测试继承 `frappe_china/tests/utils.py` 的 `FrappeChinaTestCase`；`frappe_debug` 测试同样继承它（`frappe_debug` 依赖 `frappe_china`，可 import）；不得 import `erpnext.tests.utils`。
   - 测试数据名带 `TEST_PREFIX`（`_FCT`）；会触发 `frappe.log_error` 的测试，清理只删能证明是自己造的行。
   - 手算复核的算例写成测试里的常量期望值。
   - 每个任务做完跑本任务测试；每个切片做完跑一次 `frappe_china` 全量（`bench --site test.localhost run-tests --app frappe_china`）与 Node 测试，与 TS-001 记下的基线比，用例数只增不减、全过。`frappe_debug` 自 TS-001 起另有一套，同样只增不减。
   - S4／S7 既有用例因本 Stage 改行为而须改的（税种名、选 BOM 静默替换、补货口径），在同一任务内改，并在 D 回执逐条列出「改了哪条、为什么」。
6. **译名**：`frappe_china` 新增与改译的界面文字，每加一处同一任务内补 `zh.csv`；覆盖官方键的登记 `translation_overrides.py` 并写依据；每个切片结束跑 `test_translation_quality`、`test_translations` 与 `translation_check.run`。`frappe_debug` 的界面文字按 A10 写中文字面量。
7. **json 的 `modified`**：自有 DocType／Report／Page／Workspace Sidebar json 与 fixtures 条目每改一次调大 `modified`。新增模块后先 `clear-cache` 再 migrate（开发守则）。
8. **覆盖登记**：TS-004 的超产替换登 README「后端覆盖登记」；TS-009 的 `get_no_result_message` 包装登「Desk 前端覆盖登记」；前端追加脚本在 D 回执写明为何判为追加。
9. **版本管理**：不 commit、不 push、不打 tag，除非用户在对话里显式允许（CLAUDE.md「版本管理操作规则」）。**TS-001 建 `frappe_debug` 的远程仓库属对外动作，执行前停下来问用户**仓库名与可见性；未获答复时先只在本地 `git init`，`apps.json` 条目留到获准后补。
10. **不静默**：凡「查不到、算不出、对不上」一律进返回值的问题清单或报错，不得输出 0 或空列表了事（开发守则「静默失败」）。
11. **约定显式化**：每个任务标完成前自问是否确立了新约定（命名、文件位置、错误处理、依赖、跨层调用），有则记进 D 回执「新增约定」节。本方案已知会产生的候选：`frappe_debug` 目录分层（A1）、`root_password` 只放站点配置、生成器无内存状态（A3）。
12. **最后一个任务（TS-026）做全量回归**并复核演示站最终状态。
