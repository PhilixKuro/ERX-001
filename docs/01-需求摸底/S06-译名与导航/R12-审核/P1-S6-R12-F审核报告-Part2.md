# P1-S6-R12 F 审核报告 · Part2（对象：代码 / 审核标准：B 需求文档 §4.2、§4.4、§4.12 ＋ R3 方案 Part2 经 R6 替换后）

**轮次**：P1-S6-R12｜**步骤**：F（plannedDev audit）分片 2｜**日期**：2026-10-13｜**执行者**：Claude（Opus 5.5，分片子 Agent，独立第三方视角）
**依据**：
- 意图层：[B 需求文档](../R02-需求文档/P1-S6-R2-B需求文档.md) §3.2 DEC-003／014／016／019、§4.2.2、§4.2.4、§4.2.6、§4.4、§4.12、§八 AC-003／AC-014；S3 术语标准草案 §1.1～§1.3（`S03-演示前置/R01-前置讨论/P1-S3-R1-A术语标准草案.md`）
- 要求层：[R3 总纲](../R03-开发方案/P1-S6-R3-C开发方案-总纲.md) A5、A11、HT-001～003、HT-010／011／013、§六；[R3 Part2](../R03-开发方案/P1-S6-R3-C开发方案-Part2.md) 全文（接口契约、SL-004～006、TS-006～009）
- 替换：[R6 方案](../R06-开发方案/P1-S6-R6-C开发方案.md) §六——TS-006 分段作废（A20）、无 context `Unpaid` 不写（DEC-036）、TS-007 整体由 R6 TS-021 取代（**归片 5，本片不核**）、TS-009 第 4 步 `Payment` → 收付款（DEC-035）；R6 TS-019／TS-020 归片 5
- 线索（不采信，逐条自核）：R4 D 回执-Part2、R4 D 方案补充三份、R5 E 确认报告、R5 SB 修复回执（IT-013）、R11 E 确认报告
- 规范：`docs/开发守则.md`、`docs/业务规则.md`

**被审范围**：`frappe-bench/apps/frappe_china/`，HEAD `d441e9f`，S6 改动面 `git diff 474cd1c..d441e9f`。本片：`public/js/invoice_list.js`（全文）、`public/js/desk_patches.js:238-243`（`formatters.Select` 替换段，其余段归别片）、`hooks.py:30-41`、`translations/zh.csv` 中点名用词与 DEC-002/003/014/016/019～022、035、036 相关行、`tests/test_named_terms.py`、`tests/translation_overrides.py` 中本片键、`README.md:69-75`。上游对照 frappe `c1f1e8e`（v16.34.0）、erpnext `12cd563`（v16.35.0）。

---

## 覆盖自证

**实际查了**：
- R3 Part2 接口契约 JS 部分（`wrap_indicator`、`wrap_status_filter`、`formatters.Select`）逐行对代码与上游调用链；Python 契约（`occupants`／`check`／`stratified_sample`）只核 `occupants` 现形（读 `Spike/P1S6R4-occupancy.py:18-26`），`stratified_sample` 随 TS-007 归片 5。
- SL-004 ②③⑤（点名用词、Timesheet 全族、覆盖清单）、SL-006 ①～⑤ 逐条；TS-006 第 2、3、5、6、8 步，TS-008 全部 7 步，TS-009 第 4 步（经 DEC-035 替换后）。
- 宿主自建合并字典（六 app 官方 `zh.po` ∪ csv，`Spike/P1S6R12-F/p2/merged.py`）比对 `NAMED_TERMS` 75 键与 Timesheet 29 条；vm 沙箱加载 `invoice_list.js`、`desk_patches.js` 实跑行为（`Spike/P1S6R12-F/p2/sl006-check.cjs`，输出 `sl006-check.out.txt`）；Node 全套 71 条实跑。
- 演示站 `erx.localhost` 只读 SELECT：`tabWorkstation`、`tabSalutation`、`tabTranslation`、`tabCRM Deal Status`、`tabCRM Lead Status`、`tabCRM Deal`。
- R5 SB `Spike/P1S6R5-SB/it013/patched/result.json` 读数复核。

**跳过及原因**：
- SL-004 ①④⑥⑦、SL-005 全部、TS-007、TS-009 第 1～3、5、6 步：被 R6 TS-019／020／021 替换或承接，归片 5；本片只在交界处留意（见集成点与 P2-08）。
- `bench run-tests`：按约束不跑（主会话在 test.localhost 全量回归）；`test_named_terms` 以宿主合并字典等价复算代替，见「验证门实跑结果」。
- 测试站界面实测：不做（站点数据在测试中）；SL-006 渲染结论采信 R5 SB IT-013 的 `result.json` 读数（文件已读、与代码行为推导一致），截图未逐张看。
- `desk_patches.js` 除 `:238-243` 外各段：归其它片（DEC-024／027、R9 各项、R5 SB IT-026）。

---

## 验证门实跑结果

| 门 | 声称值 | 实测值 | 与基线对比 | 一致否 |
|---|---|---|---|---|
| Node（`node --test frappe_china/tests/*.cjs`，宿主） | 71/71（R5 SB） | **71/71**，0 跳过 | 同 R5 SB 基线 71 | 一致 |
| `test_named_terms`（2 个用例） | 2/2（R4、R7、R10） | 未跑（约束）。宿主等价复算：`NAMED_TERMS` 75 键在合并字典中**全部命中**、0 不一致；Timesheet 官方含「工时表」条目 erpnext 22＋hrms 7＝29，`replace` 后**全部**与 csv 相等，csv 内含「工时表」的行 0 | — | 复算一致 |
| SL-006 行为（无对应自动测试） | R5 SB IT-013 五轮实页 | vm 沙箱：SI 徽标「未收款」、PI「未付款」、PI `on_hold`「临时冻结」、`onload` 委托返回值且重复下发只调原方法 1 次、筛选控件 `df.context` 被设、`last_options` 清空；Select formatter 按 `df.parent`／`doc.doctype` 取 context、无 context 回退「未付」 | — | 一致 |

---

## 逐项落地核查

| 意图层（源头要什么） | 要求层（方案逐条） | 定位（文件:行） | 落地 | 生效否 | 偏差说明 |
|---|---|---|---|---|---|
| §4.2.4 `Dr` → 借方（DEC-003／022） | TS-006 第 2 步 `Dr,借方`，进 OVERRIDES | `zh.csv:1611`；`translation_overrides.py:30`；`test_named_terms.py:13` | ✅ | 生效（合并字典「借方」） | 称谓侧代价已由 R11 提出、主会话处理，不另编；补证见业务规则节末 |
| §4.2.4 `Setup` 基础设置／`Setup:Workstation` 调机（DEC-019） | TS-006 第 2 步两行 | `zh.csv:4515-4516`；OVERRIDES `:103` | ⚠️ | 侧栏分节生效；工位表单下拉（`select.js:172-175`）与只读显示（本片 Select formatter）生效；**工位列表徽标不生效** | `workstation_list.js:13` 裸 `__(doc.status)`，状态为 `Setup` 的工位列表徽标显示「基础设置」→ P2-03 |
| §4.2.4 `Payment References`／`Payment Entry Reference` 核销明细（DEC-014） | TS-006 第 2 步 | `zh.csv:3467,3474`；OVERRIDES `:79,82` | ✅ | 生效 | — |
| §4.2.4 `Cash Flow Worksheet`／`Cash Flow` | 同上 | `NAMED_TERMS:18-19` | ✅ | 生效 | 底稿改名本体归片 1 |
| §4.2.4 `Item` → 物料、三个 DEC-021 词、`Business Flow` 等四个新源词 | TS-006 第 2 步 | `NAMED_TERMS:20-27` | ✅ | 生效 | `Closed Date` 只有 `crm_deal.json` 一处出处（`crm/locale/main.pot:1518`），无须 context 行，方案第 2 步子项满足 |
| §4.2.4 `Unpaid`／`Paid` 三套（PI／SI context、无 context） | TS-006 第 2 步；经 R6 DEC-036 替换为「无 context `Unpaid` 不写」 | `zh.csv:3422-3423,5236-5237`；无 context 两键 csv 无行 | ✅ | 生效（合并字典无 context `Unpaid`＝官方「未付」、`Paid`＝「已付款」） | 断言见 `NAMED_TERMS:40-43,65-66` |
| §4.2.4 收付款方向其余条目（照 S3 §1.1／§1.3） | TS-006 第 2 步（R6 TS-019 第 4 步承接） | `NAMED_TERMS:44-63` | ✅ | 生效（75 键全命中） | 逐条写 csv 归片 5；本片只核点名表断言覆盖与命中 |
| §4.2.4 `Timesheet` 全族「工时表」→「工时单」（DEC-016） | TS-006 第 3 步；SL-004 ③ | `test_named_terms.py:100-138`；OVERRIDES 依据 `DEC-016` | ✅ | 生效（29/29） | 用例在官方 po 读不到时空转通过 → P2-07 |
| §4.2.2 必改条目逐条 | TS-006 第 8 步 | 见右 | ⚠️ | — | `Accounts Setup`／`HR Setup`／`Is Sales Item`／`Create Quotation`／`View Customer`／`Add Row`／`Agents`／`Bot`／`Receivable`／`Opening & Closing` 均命中；**`默认成品仓(收料仓)` 括注未改、无处置记录** → P2-01；**CRM 商机阶段名**只有 `Qualification` 进了 SH-P1S6002，`Demo/Making` 等四个全无译文、无处置 → P2-02 |
| §4.2.2 规则 2／3、DEC-020 连带 | TS-006 第 5 步：`Stock Ledger` 另定；查 `Stock Balance`、`Stock Ledger Invariant Check` 同族是否连带改，D 回执记判定 | `zh.csv`（`Stock Ledger,库存台账`）；OVERRIDES `:104` | ⚠️ | `Stock Ledger` 生效 | 同族两词的判定在 R4／R7／R10 回执与附表中查无 → P2-08（与片 5 交界） |
| §4.2.2 规则 4 CRM 115 条覆盖 | TS-006 第 6 步 | — | ⚠️ | 无从核 | 回执与附表无该步记录 → P2-09（观察） |
| §4.2.5 第 5 条行序 | TS-006「csv 分段」→ R6 A20 全表排序 | `test_translations.py:270` `test_csv_sorted` | ✅（按替换后） | — | 用例本体归片 1／5 |
| §4.3 覆盖清单（本片写入的覆盖行） | SL-004 ⑤ | `translation_overrides.py` 本片键：`Dr`、`Setup`、`Payment References`、`Payment Entry Reference`、`Payment`、`Stock Ledger`、`Closed Date`、`Create Chart Of Accounts Based On`、Timesheet 族 | ✅ | 由 `test_translations` 交集用例守住（归片 1） | — |
| §4.4 按钮抽检 | TS-009 第 4 步经 DEC-035：`Payment` → 收付款 | `zh.csv:3464`；OVERRIDES `:77`；`NAMED_TERMS:75` | ✅ | 生效（徽标外的列表动作菜单 `sales_invoice_list.js:42`、`purchase_invoice_list.js:55` 裸 `__("Payment")` 吃无 context 行） | 抽检表重做归片 5 |
| §4.2.6 出路 1：列表徽标 | TS-008 第 2 步 `wrap_indicator`；契约「只改按 status 返回的那种」「幂等」 | `invoice_list.js:7-19` | ✅ | 生效：`meta.py:100,112` 先拼 erpnext `_list.js` 再拼本文件，`model.js:255-258` 同一 `new Function` 内执行，包装时 settings 已存在（HT-001 成立）；`indicator.js:89-91` 走 `settings.get_indicator`，表单表头徽标同样经此（IT-013 撤钩轮表头回到「未付」佐证） | 原定 `states` 做法已实测留证（IT-013 states 轮，采购 `on_hold` 被盖） |
| §4.2.6 出路 2：标准筛选下拉 | TS-008 第 3 步 `wrap_status_filter` | `invoice_list.js:21-36` | ✅ | 生效：`base_list.js:302-306` 建 FilterArea → `:1144` `make_standard_filters`（无 `custom_filter_configs` 时同步建控件）先于 `list_view.js:366` 的 `onload`；`select.js:61-82` 以 `df.context` 取译名（HT-002 成立）。报表视图 `report_view.js:88` 同样调 `onload`，一并生效 | Property Setter 原定做法已实测（IT-013：`meta` 有 context、控件无） |
| §4.2.6 出路 3：表单只读 `status` | TS-008 第 4 步替换 `formatters.Select` | `desk_patches.js:238-243` | ✅ | 生效：`sales_invoice.json` `status` `read_only=1` 走 `frappe.format` → `get_formatter("Select")`，无 `df.formatter`（HT-003 成立） | 与上游 `formatters.js:52-54` 等价，只多 context；无缺接点保护 → P2-05 |
| §4.2.6 出路 4：共享子表 | TS-008 第 5 步不做 | — | ✅ | — | 未见相关改动 |
| §4.2.6「不改 frappe 源码」 | 同上 | 六上游 app 本片无改动 | ✅ | — | — |
| SL-006 ③ `on_hold` 不被改 | — | `invoice_list.js:13` 只认第 3 项 `status,=,…` | ✅ | `purchase_invoice_list.js:27` 返回两元素数组，不被改 | — |
| SL-006 ④ 撤钩反证 | TS-008 第 7 步（预期值经 DEC-036 改「未付」） | R5 SB IT-013 `unhooked/` | ✅ | — | — |
| SL-006 ⑤ README 三行五栏 | TS-008 第 6 步、A6 | `README.md:69-75` | ✅ | — | 锁定 commit 两个、行号与函数名定位均对得上（R11 IT-054 已修第 3 行定位） |
| A5 两文件、`app_include_js` 改列表 | TS-008 第 2、4 步 | `hooks.py:30-41` | ✅ | — | `hooks.py` 本片外的新增（`doctype_js`、`update_website_context`、`override_whitelisted_methods` 一行）分属 Part3、DEC-026、R9，均有裁决来源 |
| 方案外夹带 | — | `invoice_list.js` 只有 `1779cf0` 一次提交；`desk_patches.js:238-243` 自 `1779cf0` 未改 | 无 | — | — |

---

## 业务规则合规核

| 规则条款 | 本片改动是否涉及 | 结论 | 备注 |
|---|---|---|---|
| BR-001 小企业会计准则 | 否 | 合规 | 本片只动译名与显示层 |
| BR-002 法定报表构成 | 间接：法定列头不得被 csv 翻译 | 合规（归片 1 守卫） | `test_translations.py:218` 对 `NAMED_TERMS` 键**豁免**法定列头检查——本片名单直接决定片 1 守卫的豁免面，登记为集成点 |
| BR-003～BR-007 | 否 | 合规 | — |
| 收付款方向用词（S3 术语标准 §1.1～§1.3、DEC-064／080、本 Stage DEC-036） | 是 | 合规；另有超出点名范围的方向词缺口 → P2-04 | 不是 BR 条款，是术语标准；`Unpaid`／`Paid` 两张发票三处渲染点按方向分开，`Is Paid`、`Paid Amount` 四个 context、`Received Amount`、`Payment Type`、`Type of Payment`、`Mode of Payment` 族、`Outstanding Amount`、`Outward`／`Inward` 全命中 |
| 规则新增／变更检出 | 本片无 | — | 未引入新的领域不变量 |

**`Dr` 补证**（不另编号）：`Dr` 同一无 context 键另有会计义调用点 `erpnext/accounts/doctype/account/account_tree.js:63`（`__("Dr")`／`__("Cr")` 科目树余额方向）、`bank_clearance.py:84`（`_("Dr")`），这两处「借方」才对；称谓侧来自 `frappe/desk/page/setup_wizard/install_fixtures.py:46` 的 `_("Dr")`，同为无 context 调用，**csv 层分不开两义**。演示站 `tabSalutation` 0 行、`tabTranslation` 0 行（本次只读查询）。另定称谓词须先解决「同键不可分」，不是改一行 csv 能做到的。

---

## 集成点登记（交接摘要）

| 集成点类型 | 具体落点 | 本片暴露／依赖 | 两端一致否 | 说明 |
|---|---|---|---|---|
| 共享状态（全局函数替换） | `frappe.form.formatters.Select`（`desk_patches.js:239`） | **暴露**：全 Desk 的 Select 显示值改为 `__(v, null, df.parent ‖ doc.doctype)` | 一致 | 消费方不止 SL-006：R9 DEC-040 `Available:Raven User` 的 Desk 侧靠它；csv 全部 `源词:DocType` context 行（SH-P1S6003 所述 178 行）在只读字段、列表 Select 列（`list_view.js:953`）、报表视图里从此生效。上游 `formatters.js:52-54` 若改签名或改为带 context，本替换应撤 |
| 共享状态（加载序） | `desk_patches.js` 单个 IIFE，Select 替换是**最后一条语句** | **依赖**：同文件前面各片补丁都不抛错 | 现状一致 | 前面任一段未加保护地抛错，出路 3 静默不装；现各段均有可选链或告警（读 `:7-236`）。本段自身无保护（P2-05） |
| 接口契约（上游列表设置） | `frappe.listview_settings["Sales Invoice"/"Purchase Invoice"]` 的 `get_indicator`、`onload` | **暴露**：包装标记 `__frappe_china_wrapped`、`__frappe_china_filter_wrapped`；**依赖**：erpnext `sales_invoice_list.js:30`、`purchase_invoice_list.js:22,43` 返回形状、`onload` 存在 | 一致 | 表单表头徽标经 `frappe.get_indicator` 也走此包装 |
| 接口契约（加载机制） | `hooks.py` `doctype_list_js` → `meta.py:100,112` 拼接、`model.js:255-258` 执行 | 依赖 | 一致 | 两 DocType 共用一文件、各自 meta 下发各跑一次，幂等标记挂在 settings 对象上 |
| 跨模块数据流 | 筛选控件 `page.fields_dict.status.df.context` 被改写 | 暴露 | 一致 | `select.js:82` 消费；`page.js` 其它读 `fields_dict` 的地方不读 `context` |
| 共享状态（译名） | csv 行 `Unpaid/Paid:Sales Invoice`、`…:Purchase Invoice`（`zh.csv:3422-3423,5236-5237`）；无 context `Unpaid` 不写（DEC-036） | **依赖**（行由 TS-006／R6 TS-019 写，后者归片 5） | 一致 | 片 5 若改这四行或补无 context `Unpaid`，SL-006 撤钩预期与 `NAMED_TERMS:66` 随之变 |
| 测试数据模块 | `NAMED_TERMS`（`test_named_terms.py:12`） | **暴露**给片 1：`test_translations.py:15` import、`:218` 用作法定列头检查豁免名单；给 `Spike/P1S6R6-csv-prune.py:58` 作 csv 保留键 | 一致 | 往 `NAMED_TERMS` 加键会同时扩大片 1 守卫的豁免面 |
| 测试数据模块 | `OVERRIDES` 本片键的 `basis` | 依赖片 1 `test_override_basis_forms` 的依据形态 | 一致 | `Payment` 的依据「按钮抽检 IT-010（DEC-035）」 |
| 缓存 | 合并字典 `MERGED_TRANSLATION_KEY`（`translate.py:162`） | 依赖 | — | 改 csv 后须 `clear-cache`；`test_named_terms` 自行 `clear_cache()` |
| 跨 Phase 契约（开发守则 §13） | — | — | — | 守则中无本片相关的跨 Phase 契约登记 |

---

## 自证复核

| 被审产物声称 | 实际复核结果 | 一致否 |
|---|---|---|
| R4 Part2：Timesheet 29 条全部改为「工时单」 | 官方含「工时表」条目 erpnext 22＋hrms 7＝29，逐条 `replace` 后与 csv 相等；csv 无残留「工时表」 | 一致 |
| R4 Part2 新增约定：Select formatter 只对有 `df.parent` 或 `doc.doctype` 的字段传 context | `desk_patches.js:241-242` 如此；沙箱实跑：无 context 回退「未付」 | 一致 |
| R5 SB IT-013：接钩轮销售四处「未收款」、采购四处「未付款」、`on_hold`「临时冻结」 | `it013/patched/result.json` 读数逐项如此；与代码推导一致 | 一致 |
| R5 SB IT-013：撤钩轮表单只读 status 仍为「未收款」，属设计 | 出路 3 在 `app_include_js` 的 `desk_patches.js`，不随 `doctype_list_js` 撤掉；判定成立 | 一致 |
| R3 Part2 TS-006 第 8 步「必改条目逐条核」已做（R4 回执 TS-006 ✅） | `默认成品仓(收料仓)` 合并字典仍为官方原文；CRM 四个商机阶段名无译文；两处均无处置记录 | **不一致**（P2-01、P2-02） |
| HT-001～003（读码假设） | 逐条读上游链路，均成立（见逐项表） | 一致 |
| README SL-006 三行五栏齐全 | `README.md:73-75` 五栏齐全，锁定 commit 两个与 `docker/apps.json` 所锁版本号一致（frappe v16.34.0 `c1f1e8e`、erpnext v16.35.0 `12cd563`） | 一致 |

---

## 问题清单

| # | 严重程度 | 定位 | 问题描述 | 违背的标准/意图 | 建议 | 建议档位 | 待裁决点 | 状态 |
|---|---|---|---|---|---|---|---|---|
| P2-01 | 中 | `zh.csv`（无 `Default Finished Goods Warehouse` 行）；源词在 `erpnext/locale/zh.po:16080-16081`（`Company.default_fg_warehouse`） | 需求「已知的必改条目」中的 `默认成品仓(收料仓)` 括注至今未改：合并字典仍是官方「默认成品仓(收料仓)」（`Spike/P1S6R12-F/p2/out1.txt:12`）。R4／R7／R10 回执与附表查不到对它的处置记录（全目录 grep `括注`／`Default Finished Goods Warehouse` 只命中需求与方案原文）。R6 的「演示面无官方译文的键」流程按定义扫不到它（它有官方译文、不在撞名组），所以 R6 之后也无人接住 | 需求 §4.2.2 必改条目表第 8 行；R3 Part2 TS-006 第 8 步「定位其源词后改」（未被 R6 §六替换） | 定词（如去掉括注，或改成说明其作用的括注），写 csv、进 OVERRIDES 与 `NAMED_TERMS` | 新Session修 | 定什么词（用户此前未裁）；或裁为「括注其实可用、保留官方」并补记录 | 待裁决 |
| P2-02 | 中 | 演示站 `tabCRM Deal Status`：`Qualification`／`Demo/Making`／`Proposal/Quotation`／`Negotiation`／`Ready to Close`／`Won`／`Lost`（只读查询）；`crm/frontend/src/pages/Deal.vue:988-990` 在 `isTranslatable('CRM Deal Status')` 时 `__(status)`；`crm_deal_status.json:109` `translated_doctype=1` | 需求点名的「CRM 商机阶段名（`Qualification` 等）无译文」只处理了一半：`Qualification` 被 R8 IT-042 当默认数据登进 `SH-P1S6002`（且官方「资质」本身义不对），而 `Demo/Making`、`Proposal/Quotation`、`Negotiation`、`Ready to Close` 四个合并字典里**全无译文**（`out1.txt:2-5`），也不在任何延迟需求里。因为它们是安装数据（`crm/install.py:97-115`）、不在 `main.pot`，基线缺口脚本按定义看不见。另外 CRM 把该 DocType 标为可翻译、前端会调 `__()`，所以写 csv 是有效的；DEC-033「默认数据不改 csv」管不管得到这里，没有人裁过。线索状态 `Contacted`／`Nurture`／`Junk` 情况相同 | 需求 §4.2.2 必改条目第 4 行；R3 Part2 TS-006 第 8 步 | 二选一：① 写 csv（无 context 行，先跑占用核查），进 `NAMED_TERMS`；② 认定属 DEC-033 默认数据，把这四个阶段名与三个线索状态补进 `SH-P1S6002` | 新Session修 | DEC-033 是否覆盖「`translated_doctype=1` 的 CRM 状态记录」；选 ① 还是 ② | 待裁决 |
| P2-03 | 低 | `erpnext/manufacturing/doctype/workstation/workstation_list.js:13`（裸 `__(doc.status)`）；`zh.csv:4515-4516` | DEC-019 要工位状态 `Setup` 显示「调机」，只在带 context 的渲染点生效（表单下拉 `select.js:172-175`、本片 Select formatter 的只读显示）。工位**列表徽标**不带 context，吃无 context 行，显示「基础设置」（侧栏分节义），与表单上的「调机」不一致。沙箱实跑：`Workstation Setup badge => 基础设置`。同类裸渲染点还有工厂车间可视化 `visual_plant.js:183` 的 `.text(data.status)`（原样英文）。演示站现有工位 0 条，`Setup` 不是默认值，演示中只有手选该状态才会出现 | 需求 DEC-019「渲染点可分」的前提只核了 `boot.py:465` 与 `select.js`，漏了列表徽标 | 照 SL-006 出路 1 的做法，给 `Workstation` 补一个 `get_indicator` 包装（按 ADR-0009 登记），或接受并记进延迟需求 | 延迟或不修 | 演示脚本会不会用到工位 `Setup` 状态；修还是登记 | 待裁决 |
| P2-04 | 低 | 合并字典：`Partly Paid`→部分付款、`Unpaid and Discounted`→已贴现未付、`Partly Paid and Discounted`→已贴现部分付款（`out1.txt:9-10`；`p2/out3.txt`）；`zh.csv` 无对应 `:Sales Invoice` 行 | 销售发票的其余状态值仍然是「付」的方向：客户部分回款的销售发票，列表徽标、筛选下拉、只读 status 都显示「部分付款」。SL-006 已经让这三处带上 `Sales Invoice` context，**只缺 csv context 行**，补了即可生效。这超出了点名表（S3 §1.1 只列 `Unpaid`／`Paid`），但与 DEC-064「收付款方向按 DocType 拆 context」是同一意图 | S3 DEC-064 意图；需求 §4.2.4 方案丙销售侧 | 补 `Partly Paid,部分收款,Sales Invoice` 等三行（先跑占用核查），进 `NAMED_TERMS` | 新Session修 | 列入本 Stage，还是作为点名表外的项登记延期 | 待裁决 |
| P2-05 | 低 | `desk_patches.js:238-243` | Select 替换段没有缺接点保护：`frappe.form` 不存在时整段抛 `TypeError`（沙箱实跑：`desk_patches.js without frappe.form => THROW TypeError: Cannot read properties of undefined (reading 'formatters')`），也不告警。它与同文件 R9 A23 的「缺接点告警并跳过」写法不一致。R11 E 报告第 77 行把它记为「并入 IT-054 一起改，或留给 F」，IT-054 的修复范围只动了 README，这处仍在。现实中 `app_include_js` 只在 Desk 加载，`frappe.form` 在，所以影响面小 | 开发守则「静默失败」；R9 A23 写法约定 | 改成 `const data = frappe.form?.formatters?.Data; if (typeof data !== "function") { console.warn(...); } else {...}`，补一条 Node 缺接点用例 | 新Session修 | 是否接受「Desk 内必然存在」不改 | 待裁决 |
| P2-06 | 低 | `tests/*.cjs` 中没有任何用例加载 `invoice_list.js`；`desk_patches.js` 的 Node 用例都用 `formatters: { Data: (x) => x }` 桩，却没有断言 Select 行为（grep `invoice_list`、`formatters.Select` 0 命中） | SL-006 三条出路**零自动回归**：去掉 `invoice_list.js:13` 的条件、`:29` 的 `df.context` 赋值，或把 `desk_patches.js:241` 改成不传 context，现有 71 条 Node 用例与 Python 用例都不会变红；唯一证据是 R5 SB IT-013 的一次性实页取证。上游升级后只能按 README 复验法手工核。本片沙箱脚本 `Spike/P1S6R12-F/p2/sl006-check.cjs` 已经证明这些行为可以在 vm 桩里断言 | 开发守则「判据须有判别力」；方案没要求单测，属技术债 | 把沙箱脚本改成正式 Node 用例（包装文字、`on_hold` 不改、幂等、`onload` 委托、Select 取 context 与回退） | 新Session修 | 是否值得为 SL-006 补自动用例 | 待裁决 |
| P2-07 | 低 | `test_named_terms.py:104-106,116-117` | `test_timesheet_family_uses_gong_shi_dan` 在 `zh.po` 路径不存在时 `continue`，结果为空时 for 循环一次断言都不跑，**空转通过**；也没有断言条数（应为 29）。路径由 `parents[4]` 推算，换目录布局（比如 app 以符号链接装）就会悄悄失效 | 开发守则「静默失败」与判别力；SL-004 ③「逐条比对」 | 加 `self.assertGreaterEqual(len(terms), 29)`，或至少断言非空；路径改用 `frappe.get_app_path(app, "locale", "zh.po")` | 新Session修 | — | 待裁决 |
| P2-08 | 低 | R3 Part2 TS-006 第 5 步；合并字典 `Stock Balance`→库存余额(收发存汇总表)、`Stock Ledger Invariant Check`→物料凭证与会计凭证差异表（`out1.txt:15`、`out3.txt`） | 方案要求查 `Stock Balance`、`Stock Ledger Invariant Check` 是否随 `Stock Ledger` 改名连带要改，**并在 D 回执记判定**。R4／R7／R10 回执与附表都查不到这两词的判定。`Stock Ledger Invariant Check` 现在名中的「物料凭证」只指 `Stock Ledger Entry`（分录），语义上说得通，但「已判过」没有记录。与片 5（R6 TS-019 撞名 191 组）交界：若片 5 在撞名表中判过，本条可关 | R3 Part2 TS-006 第 5 步（R6 §六未替换此子项） | 收口时与片 5 比对；查无判定则补一行判定记录 | 新Session修 | 是否已被 R6 TS-019 撞名表吸收 | 待裁决 |
| P2-09 | 观察 | R3 Part2 TS-006 第 6 步；`Spike/P1S6R1-crm-overrides.py` | 「CRM 115 条覆盖默认接受，只处理与 S3 相抵或造成新撞名的」这一步，回执里没有执行记录（没有核过多少条、改了哪几条）。规则是默认接受，所以缺记录本身不一定代表有错，但「这步做没做」无从核验。部分可能已被 R6 TS-019 撞名逐组判覆盖（片 5） | 需求 §4.2.2 规则 4 | 收口时与片 5 撞名表比对；若无覆盖，补一次脚本跑数入档即可 | 延迟或不修 | — | 待裁决 |
| P2-10 | 观察 | 合并字典 `On Hold`→临时冻结（frappe 官方）、`Temporarily on Hold`→已暂挂（csv，OVERRIDES `:107` 依据 S3 §2.3.4） | 采购发票 `on_hold=1` 时：**没有**解冻日的（无限期）显示「临时冻结」，**有**解冻日的（确属临时）显示「已暂挂」（`purchase_invoice_list.js:26-29`）。两个词的「临时」义正好与条件颠倒。它照 S3 术语标准原样落地（`On Hold` 保留），不违反依据，只记录 | S3 术语标准草案 §2.3.4（`:291`） | 交领域确认时一并看；如改，`On Hold` 在 frappe 全站通用，须带 context | 延迟或不修 | — | 待裁决 |

（严重程度：高=阻断/根因偏离 · 中=需修 · 低=技术债 · 观察=可容许偏差记录；跨文件引用时前缀改 `FD-`，由收口统一编号）

---

## 自证复核（本片自查）

- R3 Part2 四个任务各有行：TS-006（第 2、3、5、6、8 步）、TS-008（全部）、TS-009 第 4 步（经替换）在逐项表；TS-007 全部与 TS-009 其余步骤写明归片 5。
- 三层落地：两个 JS 文件都追到了上游调用链（真被调用），R5 IT-013 实页读数与本片沙箱实跑两条独立证据证明原问题消失。
- 验证门自跑：Node 71/71；Python 用例未跑（约束），用宿主等价复算替代，已写明。
- 方案外夹带：`invoice_list.js` 与 Select 替换段自首次提交未改，无夹带。
- 业务规则：逐条留行。

---

## 本片盲区自述

1. **没有看测试站或演示站界面**。SL-006 的渲染结论来自 R5 SB `result.json` 与读码、沙箱推导，截图没逐张打开。手机端（`frappe.is_mobile()` 分支，标准筛选折叠）没核。
2. **Select formatter 的全局副作用只读码推断，没逐个核**：它让 csv 里所有 `X:DocType` context 行在只读字段、列表 Select 列、报表视图里同时生效。具体哪些屏的显示因此变了，没有清点（与 SH-P1S6003 同源，归片 5 逐屏核兜底）。
3. **列表侧栏「分组」**（`list_sidebar_group_by.js:174` 裸 `__(field.name)`）若用户把 `status` 加进分组字段，显示的仍是无 context 译名。这不在方案范围内，没有列为发现。
4. **没往「定词质量」方向找**：`NAMED_TERMS` 75 个键只核了「合并字典等于表中值」，没有逐个判断译得好不好（如 `Master`→少爷、`Agents`→智能体），那是 DEC 已裁的事。
5. **最拿不准的是 P2-02 的定性**：CRM 商机阶段名属于「需求点名的必改条目」还是 DEC-033 所说的「默认数据」，两个依据都说得通。我按「需求点名在先、DEC-033 没明说覆盖它」把它定为中。如果用户认为 DEC-033 已经覆盖，它就降为「补登延迟需求」的低级项。
