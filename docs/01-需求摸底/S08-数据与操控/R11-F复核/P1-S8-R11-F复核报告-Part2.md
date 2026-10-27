# F 复核报告 · 片 2（对象：R10 D 代码 FD-001／FD-003 修复 / 审核标准：R09 C 补充方案 + 需求 §4.6、§4.7、AC-004 + BR-008）

**轮次**：P1-S8-R11｜**片**：2（`出方案修` 两项 FD-001、FD-003 的复核）｜**日期**：2026-10-27｜**执行者**：Claude（Opus 5.5），独立审查，未参与此前任何修复
**Spec**：[F-codeAudit-plannedDev-audit.md](../../../流程体系/workflows/plannedDev/F-codeAudit-plannedDev-audit.md)、[bricks/audit.md](../../../流程体系/bricks/audit.md)
**代码基线**：
- `frappe_china`：R10 提交 `751ae3b`、`ffadacf`（基线 `a8b495f`）；HEAD `f0ac818`（SB FD-002，未触及本片代码）
- `frappe_debug`：R10 提交 `dfc5ffb`、`1f9ba1c`（基线 `e1fdc14`）；HEAD `3894c5a`（SB 修复，改了 `verify.py` 的其它部分与生成器，`_integer_uom_checks` 函数与 `1f9ba1c` 逐字相同）

---

## 1. 覆盖自证

**读全的依据**：F spec、audit 积木；R08 F 审核报告 FD-001／FD-003 行及 Part1 P1-01／P1-03；R09 C 补充方案全文与 C 回执；R10 D 回执；R08 SB 修复回执中 `erx` 整场预跑相关段；需求 §4.6（4.6.1～4.6.4）、§4.7、AC-004；`业务规则.md` BR-008；总纲 A18 条。

**读码（逐行）**：
- `git diff a8b495f..ffadacf`：`accounting/install.py`、`accounting/stock_entry_accounts.py`、`install.py`、`patches.txt`、`patches/s8_whole_number_count_uoms.py`、`translations/zh.csv`、`tests/test_install.py`、`tests/test_process_loss.py`、`tests/test_replenishment_rules.py`、`tests/test_s8_accounting.py`。
- `git diff e1fdc14..1f9ba1c`：`scenario/verify.py`、`tests/test_scenario_support.py`；当前 HEAD 的 `verify.py:19-25,520-650`。
- `hooks.py:117,188-210`（`after_install` 与 Stock Entry `before_validate` 挂点）。
- 上游对照：`erpnext/stock/doctype/stock_entry/stock_entry.py:3282-3305,4470-4527`、`erpnext/manufacturing/doctype/bom/bom.py:1693,1827-1868`、`erpnext/utilities/transaction_base.py:618-650`、`frappe/installer.py:358-361`。
- SB 后续提交：`git diff ffadacf..f0ac818 --stat` 与 `git diff 1f9ba1c..3894c5a`，确认是否触及本片代码。

**演示站只读实测**：`erx.localhost` 登记表 `sites/erx.localhost/private/frappe_debug/snapshots.json`（基库 `_2bd5b09209543e8e`、工作库 `_2bd5b09209543e8e_work`、27 份快照全 ready）。对基库、`_a4_o`、`_a5_o`、`_a9_m`、工作库做 SELECT（见第 4 节）。未写库、未切库、未 set-config。

**跳过及原因**：
- **验证门未亲自实跑**（F spec 预设提示词 3 要求）：主会话正在 `test.localhost` 跑全量验证门，本片受约束不得在该站跑测试；验证门实测归主会话。故 D 回执的 9/9、25/25、184/184 等数字本片**未复核**，只读了测试代码本身判断断言是否测到要点。
- **对 FD-001 修前对照库的查询**：试图只读 s8verify 库（`_17bc759fb7a93ca2`）做修前对照，被 MariaDB 拒绝（erx 的库用户无跨站权限），未改权限，放弃。修前数值引用 R08 报告。
- **集成检查表**：本片只涉及一条跨模块数据流（工单工序成本 → 完工入库 fallback 行 → `410199` → 月末制造费用）与一条共享状态（UOM 整数属性），在第 3、7 节写；§13 跨 Phase 契约逐条登记归收口。

---

## 2. 逐项落地核查

三层：①代码在 → ②真被调用 → ③原问题真消失。

| 方案任务 | 方案要求 | 定位（文件:行） | 落地 | 生效否 | 原问题消失 | 证据 |
|---|---|---|---|---|---|---|
| TS-027-1 | `WHOLE_NUMBER_UOMS` 9 项＋子集断言；`ensure_whole_number_uoms()` 只改已存在且为 0 的、不动 `enabled`、重复返回 `[]`；`ensure_cn_uoms` 新建时带属性 | `frappe_china/accounting/install.py:54-55,58-74,77-87` | ✅ | ✅ 补丁与 `after_install` 都调用 | ✅ | `erx` 基库 9 个单位均 `must_be_whole_number=1`、`enabled=1`；`箱／千克／米`＝0（第 4 节 Q1） |
| TS-027-2 | `after_install` 在 `ensure_cn_uoms()` 后调 `ensure_whole_number_uoms()`（HT-024） | `frappe_china/install.py:229-238`；`hooks.py:117` | ✅ | ✅ `hooks.after_install` 指向该函数；上游 `installer.py:358-361` 先标补丁已执行再跑 `after_install`，读码与 HT-024 一致 | ✅（新站路径） | 测试 `test_after_install_sets_whole_number_uoms_for_existing_records`（`test_install.py`）直接调 `after_install()` 后断言 1 |
| TS-027-3 | 新补丁登记在 `[post_model_sync]` 末尾；改属性后列在途小数单据（未完工工单、草稿 Job Card、草稿生产计划），`log_error` 用关键字参数并 print，不改单据 | `patches.txt:11`；`patches/s8_whole_number_count_uoms.py:7-59` | ✅ | ✅ `erx` 基库与快照库 `tabPatch Log` 均有 `frappe_china.patches.s8_whole_number_count_uoms` 一条 | ✅（`erx` 从清洁基库重跑，无在途小数单据，Error Log 0 条，符合预期） | 第 4 节 Q1、Q6；判式 `abs(cint(x)-flt(x,精度))>1e-7` 与原生 `transaction_base.py:640` 同 |
| TS-027-4 | 注释说明两条路 | `install.py:237` | ⚠️ 只在 `after_install` 一侧有一行注释，补丁文件无注释 | — | — | 不影响行为，不记发现 |
| TS-027 验证 | 4 条单位用例＋补丁 Error Log 用例 | `tests/test_install.py:223-290` | ✅ | — | — | 5 条用例都在：幂等且不启用、子集、新建带属性、`after_install`、补丁报小数工单并只删自己造的 Error Log。补丁的 Job Card／生产计划两支无用例（方案只要求工单一支） |
| TS-028-1 | 删 `test_process_loss.py:11,137`、`test_replenishment_rules.py:15` 三处临时设 1，改为断言＝1 并提示先 migrate；`kg` 设 0 保留 | `test_process_loss.py:11-16,188-192`；`test_replenishment_rules.py:15-19` | ✅ | ✅ | ✅ 测试与演示同条件（根因：P1-01 的「测试临时改环境」） | `grep must_be_whole_number tests/`：非 `get_value` 的写法只剩 `test_install.py` 自己造的前提与 `kg` 一行 |
| TS-028-3 | HT-028 探测：1000／3·1·1／2103 支、全零损耗后完工入库，记录实际行为、不修上游 | `test_process_loss.py:81-126` | ✅ | ✅ | ⚠️ 结果是**被拦**（`process_loss_qty`＝103.047，`UOMMustBeIntegerError`），用例以 `assertRaises` 固定现状 | 方案「不成立时」要求回执「未做项」写明、交用户裁决；D 回执「未做项」表为空，只在 TS-028 行提一句，未见用户裁决或延迟登记 → **P2-01** |
| TS-029-1 | `verify(sc)` 加 `integer_uom.<表>` 共 10 项（工单 3 字段、Job Card 3 字段、生产计划行、完工／转移入库、成品行 `transfer_qty`、场景 BOM `process_loss_qty`），SQL 聚合、`detail` 给条数与 ≤5 单名 | `frappe_debug/scenario/verify.py:24-25,520-650` | ✅ | ✅ `verify()` 开头即调用；`verify_current_scenario*` 走 `verify()` | ✅ | 第 4 节 Q5：在 `erx` 工作库按同一 WHERE 条件复跑，每项命中行数非零（工单 335、Job Card 2129、计划行 335、入库 667、成品行 333、BOM 5），判式对 5259.299 为真、对 5261 为假，故检查不是空查；全部 0 小数 |
| TS-029-1 验证 | verify 单测：小数工单不过、整数通过 | `tests/test_scenario_support.py:32-59` | ✅ | — | — | 用例 mock 了 `frappe.db.sql` 返回值，只测到结果拼装与通过判定，**没测到 SQL 本身**。本片以第 4 节 Q5 的真库复跑补足 |
| TS-029-2 | 生成器其余代码不改 | `git diff e1fdc14..1f9ba1c` 只动 `verify.py` 与测试 | ✅ | — | — | R10 无夹带。SB 提交 `3894c5a` 改了 `day.py`／`targets.py` 等，属 SB 线（FD-004～008 等），不在本片 |
| TS-029-3 | 隔离站 `s8r9` 第一段实跑 | D 回执 | 未复核（站点运行记录，非代码） | — | 被整场重跑覆盖 | `erx` 已在新代码上整场重跑（SB 回执，3248.2 秒），本片直接查整年数据，见第 4 节 |
| TS-030 纯函数 | `fallback_operating_cost_share` 按 §3.2 签名与伪代码 | `stock_entry_accounts.py:36-55` | ✅ | ✅ 由 `normalize` 调用（`:99-101`） | ✅ | 五组期望值与两组异常写死在 `test_s8_accounting.py:78-91`；本片手算：(50,0,500,0,500)→50；(100,50,1000,500,500)→50；(80,0,800,0,500)→50；(5235.11,0,69675.196,0,69675.196)→5235.11；(40,45,…)→(0,True)；(80,20,50,50,25)→60（`remaining_qty≤0` 取剩余成本） |
| TS-030 `normalize` | 挂点签名不变；带 `job_card`、无 fallback 行、多行、半成品跟踪、多层 BOM 子装配、无已报工或累计为 0 时不改；未报工工序保留单位额部分；已吸收按其它已提交入库去重；`reported_qty` 取各道 `completed+loss` 最小值；超吸收出提示；`get_doc` 不用缓存；删旧启发式 | `stock_entry_accounts.py:58-111`（已吸收查询 `:114-129`）；`hooks.py:206-210` | ✅ | ✅ 挂在 Stock Entry `before_validate` 第 3 位，与 R8 时相同 | ✅（读码＋集成用例） | 删旧启发式与 `get_cached_doc` ✓；跳过条件与上游 `get_remaining_operating_cost`（`stock_entry.py:4495-4505`）同式（设置与工单 `use_multi_level_bom` 两者都成立才跳）✓；已吸收查询 `docstatus=1 and se.name != 本单`、子行条件与 `rows` 同、按父单去重取 `fg` ✓ |
| TS-030 测试 | 三条 mock 改造、期望不变；集成两批；重复 save；取消重做 | `test_s8_accounting.py:93-248,275-330` | ✅ | — | ✅ | 见下「FD-003 分批用例核」 |
| TS-030-4 | 两句中文提示进 `zh.csv` | `translations/zh.csv`（2 行，带引号） | ✅ | ✅ `frappe._()` 包裹 | ✅ | HEAD 上两句仍在（`grep -c`＝2） |
| TS-030-3 | docstring 写口径与 `SH-P1S8010` 的关系 | `stock_entry_accounts.py:43-47` | ⚠️ | — | — | 写成「consistent with … the accounting review recorded in SH-P1S8010」，读起来像会计已复核；实际 `SH-P1S8010` 是演示后待交会计 → **P2-03** |
| TS-031-3 | README 若有对应节则更新 `normalize` 口径；无则 D 回执写明未改 | `frappe_china/README.md`（无 `normalize_fallback`／LG-001 条目） | ⚠️ | — | — | README 未改合规（无对应节），但 D 回执没写「未改」→ 并入 **P2-02** |
| TS-031 其它 | 全量回归、译名三件套 | D 回执 | 未复核（见覆盖自证） | — | — | 归主会话验证门 |

### FD-003 分批用例核（`test_partial_manufacture_absorbs_cumulative_actual_operating_cost`，`test_s8_accounting.py:275-311`）

- 造法：一道工序、`cn_job_card_split_qty=5`、工单 10 支（单位「支」），先断言拆成 2 张卡；第一张 30 分钟（时薪 60 → 30）提交，断言工序 `completed+loss`＝5、工单 `actual_operating_cost`＝30；入库 5、连续 `save()` 两次后 fallback 行＝30；提交并核 GL；第二张 60 分钟提交，断言累计＝90；入库 5 → 行金额＝60；断言两张之和＝工单累计 `actual_operating_cost`（2 位）；取消第二张、重建提交仍＝60；每次都核 GL 只有 `1405／1409／410199` 且无损益类。
- **是否真测到「两批合计＝累计实际」**：是。两批工序成本不等（30／60），旧公式会得 30×5÷10＝15 与 90×5÷10＝45，合计 60≠90，新公式 30＋60＝90，断言能区分新旧口径。断言用的是工单 reload 后的真实 `actual_operating_cost`，不是写死值。
- **没覆盖的**：①一批入库数小于已报工未入库数（如报工 8、入库 5）只在纯函数 (80,0,800,0,500) 测到，集成没测；②多道工序完工数不等时 `reported_qty` 取最小值，只在读码层面成立，集成只有一道工序（C 回执复核建议 1 已点出）。

---

## 3. 跨模块数据流与共享状态（本片）

| 集成点类型 | 具体落点 | 两端一致否 | 说明 |
|---|---|---|---|
| 共享状态 | UOM 整数属性：写端 `ensure_cn_uoms`／`ensure_whole_number_uoms`（补丁＋`after_install`）↔ 读端 `process_loss.py:71,97`、`replenishment/rules.py:36`、原生 `validate_uom_is_integer`、`verify._integer_uom_checks` | ✅ | R08 P1-01 的「写端不设、读端依赖」已拼上；`erx` 上 9 个单位为 1，读端取整分支实际触发（计划 5261、BOM 4.9／3.9） |
| 跨模块数据流 | 工单工序成本 → fallback 行（`normalize`）→ `410199` → 生成器月末制造费用（按 GL 净额） | ✅ | `erx` 工作库 333 张完工入库，各 1 行 fallback，行金额与工单 `actual_operating_cost` 逐单相等（差值最大 0）；GL 借 1405 796,666.60＝贷 1409 701,561.66＋贷 410199 95,104.94 |

---

## 4. 演示站实测（`erx.localhost`，只读 SELECT）

连接默认库 `SELECT DATABASE()`＝`_2bd5b09209543e8e`（基库）。各查询以 `库名`.`表名` 全限定。

**Q1 单位属性与补丁日志**

```sql
SELECT name, must_be_whole_number, enabled FROM _2bd5b09209543e8e.tabUOM WHERE name IN (...);
SELECT patch FROM <库>.`tabPatch Log` WHERE patch LIKE '%whole_number%';
```

| 库 | 结果 |
|---|---|
| 基库 | 支、个、台、只、件、张、套、片、条＝1（enabled 均 1）；Nos＝1；箱、千克、米＝0；补丁日志 1 条 |
| `_a4_o` | 同上 9 个＋原生 Box／Nos／Pair／Set／Unit 为 1；补丁日志 1 条 |

**Q2 第 4 幕生产计划（AC-004）**

第 4 幕的现场生产计划在第 4 幕开场快照 `_a4_o` 里还不存在（该库最新计划 `MFG-PP-2026-00077`，2026-01-05），在第 5 幕开场快照 `_a5_o`（即第 4 幕走完后）与工作库里出现：

| 库 | 计划 | 日期 | 物料 | 销售订单（数量） | BOM（工序损耗率） | `planned_qty` |
|---|---|---|---|---|---|---|
| `_a5_o` | `MFG-PP-2026-00078` | 2026-01-07 | SPR-C-3.0-23-50 | SAL-ORD-2026-00085（5000 支） | HDTH-C3-A（卷簧 3／回火 1／磨端 1） | **5261.000000000** |
| 工作库 | 同上 | 同上 | 同上 | 同上 | 同上 | **5261.000000000** |

与需求 §4.6.2 第二例逐道 ceil（5000→5051→5103→5261）一致，AC-004 的 5261 在演示数据上成立（R08 时为 5,259.299）。对应工单 `MFG-WO-2026-00078` qty 5261；卷簧 3 张卡合计 5261、最大 2000，回火／磨端各 3 张合计 5201，均无小数；第 5 幕开场时卷簧已报工 1940＋损耗 60。

**Q3 BOM 整体损耗率（A18）**（`_a5_o`）：压簧 HDTH-C3-A／B、HDTH-C8-A／B＝4.9（损耗数量 49），拉簧 HDTH-T3-A／B＝3.9（39），与方案 §2.1「4.9303→4.9、3.97→3.9」一致。工作库全部已提交 BOM 中 `process_loss_qty` 非整数的 0 条。

**Q4 全年各单据的「支」数量是否有小数**（工作库；`_a9_m` 结果相同）

| 表.字段 | 行数 | 小数条数 |
|---|---|---|
| Work Order `qty`／`produced_qty`／`process_loss_qty`（草稿 0） | 335 | 0／0／0 |
| Job Card `for_quantity`／`total_completed_qty`／`process_loss_qty` | 2169 | 0／0／0 |
| Work Order Operation `completed_qty`／`process_loss_qty` | 837 | 0／0 |
| Production Plan Item `planned_qty` | 335 | 0 |
| Stock Entry（Manufacture）`fg_completed_qty`／`process_loss_qty` | 333 | 0／0 |
| Stock Entry Detail（Manufacture，支）`transfer_qty`／`qty` | 333 | 0／0 |
| Delivery Note Item `stock_qty` | 332 | 0 |
| Sales Order Item `stock_qty` | 338 | 0 |
| Sales Invoice Item `stock_qty` | 332 | 0 |
| Quotation Item `stock_qty` | 384 | 0 |
| Stock Ledger Entry `actual_qty`（支，未取消） | 665 | 0 |
| Error Log「S8 整数计数单位…」 | — | 0 条 |

另：完工入库 `process_loss_qty` 最小 44、为 0 的 0 张 → HT-028 的零损耗分支在演示数据上不会触发。

**Q5 verify 整数检查的非空性**：按 `_integer_uom_checks` 的同一 JOIN／WHERE（窗口 2025-10-01～2026-10-26）在工作库计数：工单 335、Job Card 2129、计划行 335、入库 667、成品行 333、BOM 5，均非零；`abs(truncate(5259.299,6)-truncate(5259.299,0))>1e-7`＝1，对 5261＝0。检查确实覆盖真实数据且判式能区分。

**Q6 FD-003 在演示数据上的表现**（工作库）

| 项 | 结果 |
|---|---|
| 每张工单的完工入库张数 | 333 张工单全部为 1 张 |
| 每张入库的 fallback 行数 | 333 张全部为 1 行 |
| fallback 行金额 vs 工单 `actual_operating_cost` | 333 对，差值 >0.01 的 0 对，最大差 0 |
| 已完工工单各道 `completed+loss`＝工单数 | 832／832 |
| 完工入库 GL 科目 | 仅 1405（Asset）、1409（Asset）、410199（Asset），借贷平 |
| `set_op_cost_and_secondary_items_from_sub_assemblies`／半成品跟踪工单／多层 BOM 工单 | 0／0／335（设置为 0，故不跳过，与上游同） |

结论：整单一次入库时新口径结果等于累计实际（完成标准第 3 条后半）；分批场景无演示数据，按第 2 节用例核。

---

## 5. 业务规则合规核

| 规则条款 | 本 Round 改动是否涉及 | 结论 | 备注 |
|---|---|---|---|
| BR-008 完工入库不产生损益类分录 | 是（TS-030 改 fallback 行金额） | 合规 | 演示数据 333 张完工入库只有 1405／1409／410199（均 Asset）；集成用例每批与取消重做后都断言科目集合＝{1405,1409,410199}、无 Income／Expense、无 400101 |
| 需求 §4.7 成本完整性（工序成本按实全部进成品） | 是 | 合规（整单）／用例层合规（分批） | 整单：333 对逐单相等；分批：集成用例 30＋60＝累计 90 |
| 需求 §4.6.1「支须为整数」、§4.6.2 逐道 ceil、AC-004、总纲 A18 | 是 | 合规 | 第 4 节 Q1～Q4 |
| 新增口径① 分批完工按「累计实际 − 已吸收」× 本次 ÷ 已报工未入库数分摊 | 是（新增） | **草案·待领域专家确认** | 用户 2026-10-26 裁决采用，但口径由 F 审核（AI）提出、会计未复核，已并入 `SH-P1S8010`；代码 docstring 的措辞见 P2-03 |
| 新增口径② 已报工数＝各道工序 `completed_qty + process_loss_qty` 的最小值 | 是（新增，C 方案定） | **草案·待领域专家确认** | AI 拟定；多道工序完工数不等时的分摊基准，C 回执复核建议 1 已请用户判断，未见答复 |
| 新增口径③ 支、个、台、只、件、张、套、片、条为整数计数单位 | 是（新增） | **草案·待领域专家确认** | 用户裁决的配置选择，未进 `业务规则.md`；是否作为领域不变量登记由用户定。改后的连带后果见 P2-01 |
| BR-001～BR-007（税、科目等） | 否 | — | 本片改动不涉及 |

---

## 6. 新发现

| # | 严重程度 | 定位 | 问题描述 | 违背的标准 | 建议 | 建议档位 | 待裁决点 | 状态 |
|---|---|---|---|---|---|---|---|---|
| P2-01 | 中 | 上游 `erpnext/stock/doctype/stock_entry/stock_entry.py:3294-3301`；固定现状的用例 `frappe_china/tests/test_process_loss.py:81-126`；D 回执「未做项」表（空） | **整数单位改动在客户库上新暴露了一个阻断路径，且没有去向。** 9 个单位改为整数后，凡工单所有工序报工损耗都为 0、BOM 整体损耗率非 0、完工数不是 BOM 数量的整倍数时，原生完工入库按 `fg × 整体损耗率 ÷ 100` 回退算出小数损耗（实测 2103 支 → 103.047），被 `UOMMustBeIntegerError` 拦下。改前「支」是小数单位，这条路能提交；改后不能，属本次改动引入的行为变化。演示数据不触发（完工入库最小损耗 44，0 损耗 0 张），但 `frappe_china` 要装客户正式库，「整单无损耗」在实际报工中并不罕见；用户可手填整数损耗绕过，但报错文案是原生的「数量不能为小数」，不提示该怎么办。方案 HT-028「不成立时」要求回执「未做项」写明并交用户裁决；D 回执只在 TS-028 行写「按方案只记录、不修」，「未做项」为空，延迟需求登记册无条目，用户未见裁决 | R09 方案 HT-028「不成立时」与执行纪律 7；开发守则「静默失败」精神（用户看不懂的拦截） | 交用户裁决去向：(a) 登记延迟需求，写明触发条件、绕过办法（手填整数损耗）、正式库上线前须处理；(b) 追加修复，例如 `before_validate` 中在 Job Card 报工损耗合计为 0 时显式置 `process_loss_qty=0` 并跳过 BOM 回退，或按 A18 同口径把回退值取整并出提示（须另出方案，因为会改原生损耗语义） | 延迟或不修（登记延迟需求） | ① 登记延迟还是本 Stage 修；② 若修，零报工损耗时损耗取 0（以报工为准）还是取整后的 BOM 回退值 | 待裁决 |
| P2-02 | 低 | `docs/01-需求摸底/S08-数据与操控/R10-代码/P1-S8-R10-D回执.md`「未做项」节、TS-031 行 | D 回执漏写两处方案明确要求的登记：① HT-028 被拦，方案要求进「未做项」（同 P2-01）；② TS-031 第 3 条要求「README 无对应节则在 D 回执写明未改」，README 确无 `normalize_fallback_operating_cost`／LG-001 条目，回执未写 | R09 方案 TS-031-3、HT-028；`bricks/receipt.md` 未做项登记 | 补回执两行（文档补记，不改代码） | 本Session修 | 是否由收口会话顺手补回执，还是随 P2-01 的裁决一并补 | 待裁决 |
| P2-03 | 观察 | `frappe_china/accounting/stock_entry_accounts.py:43-47`（`fallback_operating_cost_share` docstring） | docstring 写「consistent with the component-cost path and the accounting review recorded in SH-P1S8010」，读者会理解为会计已复核该口径。实际 `SH-P1S8010` 是「演示后交会计、不阻塞」的待办，口径仍是草案 | R09 方案 TS-030 要点 3（写明口径与 `SH-P1S8010` 的关系）；F spec 预设提示词 6（AI 拟定的规则不得当作已生效） | 改为「pending accounting review, tracked in SH-P1S8010」一类措辞；可在下一次碰该文件时顺手改 | 延迟或不修 | 是否值得单独改 | 待裁决 |

**找过但未成发现的方向**：
- 补丁对已有小数单据：只改属性、列清单进 Error Log 与输出，不改单据，符合方案；`erx` 从清洁基库重跑，无在途小数单据，Error Log 0 条。补丁只列草稿 Job Card／草稿计划／未完工工单，不列草稿完工入库、草稿发货等（方案范围如此），记在复核建议。
- 整数单位对生成器其他环节：第 4 节 Q4 覆盖工单、拆卡、工序、计划、完工入库、发货、订单、发票、报价、库存流水，全年 0 小数；「支」物料无其它换算单位，发货单位全为「支」。
- BOM 损耗率：4.9／3.9 符合 A18，`process_loss_qty` 整数。
- 已吸收查询：取消的入库（docstatus=2）不计入，取消重做用例证实；按父单去重 `fg` 正确；`bom_no` 未过滤，与 fallback 行本身无 `operation_id` 的情况相符，不构成问题。
- 改前已提交、按旧公式少记的分批入库：新算法以「累计实际 − 已吸收」为剩余，下一批会自动补齐差额，不会重复计；多记的情况走超吸收提示。
- 方案外夹带：R10 两个 app 的 diff 只含方案列出的文件；SB 后续提交未触及本片函数。

---

## 7. 交接摘要（回传收口）

**本片依赖**：
- 主会话的验证门实跑结果（`test_install`、`test_process_loss`、`test_replenishment_rules`、`test_s8_accounting`、`test_scenario_support` 及全量），本片未跑。
- SB 回执所述 `erx` 整场预跑（2026-10-27，3248.2 秒）确实在 HEAD 代码上进行：本片只从数据侧印证（补丁日志在、计划创建时间 2026-10-27 15:15～15:55、数值整数），未核对预跑时容器内代码版本。

**本片暴露**：
- 共享状态：9 个计数单位在 `erx` 基库、全部快照库、工作库上 `must_be_whole_number=1`；HT-028 的零损耗阻断（P2-01）对任何以这些单位为库存单位的物料都成立，若别片涉及客户库上线条件或延迟登记册，需交叉。
- 契约：`normalize_fallback_operating_cost` 挂点不变（Stock Entry `before_validate` 第 3 位）；新纯函数 `fallback_operating_cost_share` 签名与方案 §3.2 一致；`verify()` 新增 10 项 `integer_uom.*` 检查，排在所有检查之前（SB 回执 `verify` 43/43 应已含这 10 项，本片未核计数）。
- 跨模块数据流：fallback 行 → `410199` → 月末制造费用，演示数据上逐单相等，月末凭证不受影响。

---

## 8. 复核建议

1. **严重程度在边界上的**：P2-01 定「中」。理由是改动把一条原本能走通的完工路径变成原生报错，且落在要装客户库的 app 上；若用户认为客户上线前必有一轮专门的生产配置核对、且手填损耗可绕过，可改判「低」。P2-02 在「低／观察」之间，是回执完整性问题，不影响代码。
2. **查得最浅处**：FD-003 的多道工序、完工数不等场景只读了码，没有真实数据或集成用例；`reported_qty` 取最小值这一口径本身是 AI 定的（草案②）。查法：读 `stock_entry_accounts.py:96-99` 与 C 方案 §3.2，判断报工不齐时按最慢工序算剩余数是否符合你对分批入库的理解。
3. **开放找漏的盲区**：①没跑任何测试（约束所限）；②没核 `erx` 预跑时容器代码版本与 HEAD 一致，只从数据侧推断；③补丁的 Job Card／生产计划两支没有用例，也没有真实小数数据可验；④没看「箱、包、卷、批、次、打」保持小数后在发货打包、批量单位换算（`batch_uom.apply_batch_factor`）里有没有与整数「支」换算出小数的情况——`erx` 上「支」物料没有其它换算单位，故演示数据不暴露，客户库可能遇到；⑤超吸收判定 `absorbed > cumulative` 没有容差，浮点误差可能让「刚好吸收完」时出一次多余的黄色提示（金额本就为 0，不影响账），未实测。
4. **拿不准处**：P2-01 算「由本次改动引入的新问题」还是「方案已知并接受的限制」。方案把它列为已知、只探测；但方案同时要求被拦时交用户裁决，而这一步没有发生，所以本片按「去向未定」记为发现。
