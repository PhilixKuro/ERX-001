# 审核报告·Part1（对象：P1-S8 Part1 代码，`frappe_china` `dd39b6a..75ceb04`、`frappe_debug` 骨架与装序、ERPNext fork `12cd563..a729571`、主仓库 `docker/` 的 S8 改动 / 审核标准：R04 需求文档 §4.5～4.8、§4.10～4.14、§4.16、§4.17、§4.21、§八 AC）

**轮次**：P1-S8-R8 F 片1（`plannedDev` audit 步）｜**日期**：2026-10-26｜**执行者**：Claude（Opus 5.5），独立子 Agent，未参与 C／D／E
**要求层**：[开发方案总纲](../R05-开发方案/P1-S8-R5-C开发方案-总纲.md)（A1～A20、§四偏离 19 条、§五契约、§六 HT、§七侵入度、§十纪律）＋[Part1](../R05-开发方案/P1-S8-R5-C开发方案-Part1.md)（TS-001～012、SL-001～010）
**意图层**：[R04 需求文档](../R04-需求文档/P1-S8-R4-B需求文档.md) §4.5～4.8、§4.10～4.14、§4.16、§4.17、§4.21、AC-001～017（总纲 §三覆盖表中落在 SL-001～010 的项）
**线索（不当结论）**：[D 回执 Part1](../R06-代码/P1-S8-R6-D回执-Part1.md)、[E 确认报告](../R07-确认/P1-S8-R7-E确认报告.md)
**探针**：`Spike/P1S8R8-F/p1/probe_normalize_partial.py`（输出 `probe_normalize_partial.out`）。纯 mock、不连库写入；其余取证为对 `s8verify.localhost`、`s8eoqformal.localhost` 的只读 SELECT。未碰 `erx.localhost`；未在 `test.localhost` 跑测试、migrate、清缓存（只读过一次其 `tabUOM`／`tabItem`）。

## 覆盖自证

**实际查了**：
- 依据：总纲全文、Part1 全文；需求 §4.5～4.8、§4.10～4.14、§4.16、§4.17、§4.21、§八 AC-001～029（逐条对过落在 SL-001～010 的 AC-001～017）；`docs/开发守则.md` 全文（含跨 Phase 契约表）、`docs/业务规则.md`；E 报告全文、D 回执 Part1 全文、D 讨论记录第 1～18 步标题与第 7、16 步正文。
- 代码（逐行读 diff）：`frappe_china` `dd39b6a..75ceb04` 的全部非测试文件——`hooks.py`、`install.py`、`accounting/{company,customer_tax,stock_entry_accounts}.py`、两个 `patches/s8_*`、`patches.txt`、`company_defaults.json`、科目表 json、`tax_setup.json`（只看规模）、`fixtures/custom_field.json`、`production/{bom_selection,operation_time,overproduction,piece_rate,process_loss}.py`、`replenishment/{daily,demand,reorder_level,rules,safety_stock,suggestion,types}.py`、`capacity_load.py`、`stock_plus` 三个 json 与策略对比报表四个文件、`production_plus` 计件两 json 与列表 js、`public/js/{bom,production_plan,work_order,desk_patches,independent_app_labels,replenishment_suggestion_list}.js`、`website_translation.py`、`zh.csv` 全部新增行、`translation_overrides.py` 新增行、`workspace_sidebar/business_flow.json`、README 覆盖登记。测试只读了 `test_install.py` diff、`test_overproduction.py` 头部与哈希守卫、`test_s8_accounting.py` 的用例名与断言词、`test_capacity_load.py` diff。
- `frappe_debug`（HEAD `d8614a5`）：`hooks.py`、`pyproject.toml`、`modules.txt`、`patches.txt`、`tests/test_smoke.py`、README、骨架提交 `616d897` 的文件清单、`scenario/masters.py` 的单位检查段、`data/demo.yaml` 第 1／4／6 幕相关步。
- ERPNext fork `12cd563..a729571` 全部 diff 与上下文（`stock_entry.py:865-899`）；主仓库 `adb3431^..87dac76` 的 `docker/apps.json` 与 `configure_apps.py`，`setup.sh` 第 6、6.2 段。
- 上游对照：`work_order.py:264-300,575-595,645-682,712-722,798-951`（并独立复算 `validate_work_order_against_so` 源码 sha256＝登记值）、`production_plan.py:137-197`、`stock_entry.py:905-952,1030-1185,3282-3305,4470-4523`、`bom.py:1360-1373,1755-1870`、`frappe_crm_api.py:128-165`、CRM `erpnext_crm_settings.py:616-720`、`erpnext_sales_order_customer.js`、frappe `installed_applications.py:109-136`、`defaults.py:149-273`、`cache_manager.py:281-321`、`success_action.js:1-90`、`utils/error.py:44-100`、`commands/utils.py:305-317`。
- 门：容器内 Ruff check／format（两 app）、8 个改动 js 的 `node --check`、`frappe_china` Node 全量。

**跳过及原因**：
- **Python 全量 `run-tests` 未跑**：主会话正在 `test.localhost` 跑全量验证门。验证门 Python 一项写「主会话跑」。
- 浏览器实点（SL-005 ⑥、SL-006 ①、SL-008 ②～⑥、SL-009 ④⑥、SL-010 ③）未做，只看了 D 留的截图与验收 json。
- `erx.localhost` 的数据一律未查；凡「演示站上怎样」的判断，取自 `s8verify`／`s8eoqformal`（同一生成器产出）与 `Spike/P1S8R6-D/acts/acceptance/` 下的彩排取证 json，见各条。
- Part2／Part3（`frappe_debug/scenario`、`builders`、`demo`、前端运行器）只在交接摘要登记依赖与共享状态，未审其实现。
- 测试文件（`test_process_loss`、`test_operation_time`、`test_replenishment_s8_*`、`test_strategy_comparison`、`test_customer_tax`、`test_s8_tax_migration` 等）未逐行读，测试质量只在 E 已点出的 IT-008／IT-010 处复核。

## 验证门实跑结果

| 门 | 声称值 | 实测值 | 与基线对比 | 一致否 |
|---|---|---|---|---|
| Ruff check `frappe_china`（容器 `ruff 0.14.10`，`75ceb04`） | E：通过 | `All checks passed!` | 基线 0 保持 | ✅ |
| Ruff format --check `frappe_china` | E：185 文件 | `185 files already formatted` | — | ✅ |
| Ruff check／format `frappe_debug`（`d8614a5`） | E：70 文件 | `All checks passed!`／`70 files already formatted` | — | ✅ |
| `frappe_china` Node `node --test frappe_china/tests/*.cjs` | E：115/115 | 115 pass／0 fail／0 skip（166 ms） | D 基线 89 → 115 | ✅ |
| 本片 8 个改动 js 的 `node --check` | — | 全部 ok（`bom.js`、`production_plan.js`、`work_order.js`、`desk_patches.js`、`independent_app_labels.js`、`replenishment_suggestion_list.js`、`piece_rate_summary_list.js`、策略对比报表 js） | — | ✅ |
| 上游 `validate_work_order_against_so` 源码 sha256 | 方案／README：`dd34f079…b6a6` | 按 AST 行号 645-682 截取复算＝`dd34f0798ed5604f5ac1c1038ad6b6c18d643eebaceadbb6f93e49851959b6a6` | — | ✅ |
| Python 全量（`frappe_china`、`frappe_debug`） | E：471/471＋6＋4、178/178 | **主会话跑**（本片未跑） | — | 未核 |

## 逐项落地核查

落地：✅完整／⚠️部分／❌缺失。生效：真被调用、未被绕过；根因：原问题真消失。

| 方案任务 | 要求层要求 | 定位（文件:行） | 落地 | 生效否 | 偏差说明 |
|---|---|---|---|---|---|
| TS-001 ① | 骨架：`pyproject`、`hooks`（`required_apps`、无 `override_*`／`regional_overrides`／译名 csv）、`modules.txt`、A1 目录、README 两句 | `frappe_debug/hooks.py:1-18`；`616d897` 17 文件 | ✅ | ✅ | `doc_events "*"`、`app_include_js` 等是 Part3 追加，均为追加型 |
| TS-001 ② | 冒烟测试：已装且 `frappe_china` 在前 | `frappe_debug/tests/test_smoke.py:6-10` | ✅ | ✅（E 实跑） | — |
| TS-001 ③ | `reorder_installed_apps` 的两次失效挂 `after_commit` | `install.py:221-224` | ✅ | ✅ | 读码：上游 `set_global`→`add_default`→`_clear_cache`（`defaults.py:191,273`）在提交前还会全清一次，但最后一次失效已在提交后，窗口内建出的旧缓存会被它清掉，PH-P1074 成立。调用方只有 `setup.sh:396`（经 `bench execute`，`commands/utils.py:316` 提交） |
| TS-001 ③ | 单测：提交前不调、提交后各一次、回滚不调 | `tests/test_install.py`（diff `+117~+149`） | ✅ | ✅ | — |
| TS-001 ④ | `apps.json` 按 `frappe_china` 同形加一条，排其后 | `docker/apps.json:47-52` | ✅ | ⚠️ | `setup.sh` 第 6 段对任何站都装 `apps.json` 全部条目，客户库「不装」无机制，见 **P1-07** |
| TS-001 ⑤ | `TAIL_APPS` 是 `frappe_china` 内唯一引用 | `install.py:6` | ✅ | — | grep 另命中 `test_install.py` 4 处（已登记偏离） |
| TS-002 ① | `company_defaults.json` 加 `410199` 与四种收付款方式 → `1002` | `company_defaults.json:+11,+28-33` | ✅ | ✅ | — |
| TS-002 ② | 科目表 `400101.account_type` 改空，父科目不动 | 科目表 json `:879` | ✅ | ✅ s8verify 实测 `400101` 类型为空 | — |
| TS-002 ③ | `set_cn_mode_of_payment_accounts`：存在才处理、有值不动 | `accounting/company.py:162-185`；`build_cn_company:134` | ✅ | ✅ | IT-009 后只在缺行／空值时 `save` |
| TS-002 ④ | `unify_difference_account`：Manufacture／Repack、中式科目表、全部行改 `400101`；取不到 `log_error` 不抛；挂 `before_validate` 第二位 | `stock_entry_accounts.py:138-159`；`hooks.py:257-262` | ✅ | ✅ s8verify 332 张完工入库 GL 只有 `1405`／`1409` | 附加费用空科目补 `410199` 是 HT-001 退路（E 已补登） |
| TS-002 ⑤ | 迁移补丁：只补空、只改 `Cost of Goods Sold`、缺科目 `log_error`＋`print` 不抛 | `patches/s8_cn_accounting_defaults.py:7-33`；`patches.txt:9` | ✅ | ✅ | IT-009 修后合规 |
| TS-002（E 新增 IT-001／018） | `normalize_fallback_operating_cost`：除回原生放大的工序成本，二次执行为空操作 | `stock_entry_accounts.py:162-194`；`hooks.py:261` | ⚠️ | ⚠️ | 单张整单入库对；**分批完工入库少计**，见 **P1-03** |
| TS-003 ① | Custom Field `BOM Operation-cn_process_loss_percentage`（Percent，`insert_after: time_in_mins`，`in_list_view`） | `custom_field.json:+257-267`；`hooks.py:314` | ✅ | ✅ | — |
| TS-003 ② | §5.1 四个函数 | `production/process_loss.py:17-108` | ✅ | ⚠️ | `operation_loss_rates` 无调用方，见 **P1-10**；全零视为未启用（用户批准） |
| TS-003 ③ | `bom_process_loss` 挂 `before_validate`；整数单位走 A18；提示两句 | `process_loss.py:65-86`；`hooks.py:189` | ✅ | ⚠️ | 演示数据里「支」不是整数单位，A18 从不触发，见 **P1-01** |
| TS-003 ④ | 前端：任一行非零即整体值只读 | `public/js/bom.js:1-24`；`hooks.py:45` | ✅ | 未实点 | — |
| TS-003 ⑤ | 标签、提示两句进 csv | `zh.csv`（`Process Loss % (Operation)`、两句提示） | ✅ | — | — |
| TS-004 ① | `Production Plan Item` 三字段（`cn_recommended_bom` hidden） | `custom_field.json:+300-333` | ✅ | ✅ | — |
| TS-004 ② | `production_plan_planned_qty` 排在 `production_plan_validate` 后；人改判据；合并来源按引用求和 | `process_loss.py:124-147`；`hooks.py:266-271` | ✅ | ✅ | 演示数据计划数量为 `5259.299` 而非 5261，见 **P1-01** |
| TS-004 ③ | 前端「推荐 {0}」 | `public/js/production_plan.js:153-167` | ✅ | 未实点（D 截图） | — |
| TS-004 ④ | 超产替换：照抄原生、只改上限；`ensure_patched` 三入口；哈希守卫；README、ADR-0004 | `overproduction.py:15-59`；`hooks.py:243,346-359`；README 后端覆盖登记；ADR-0004:49 | ✅ | ✅ | 与上游 `work_order.py:645-682` 逐行比对，只改了 `allowed_qty` 一行；报错消息里仍是订单数量（原生契约），无影响 |
| TS-004 ⑤ | 按订单补货 `planned_qty` 改反算，来源仍记未交数 | `replenishment/rules.py:241` | ✅ | ✅ | — |
| TS-005 ① | `customer_tax_category_from_quotation`（Customer `before_insert`） | `accounting/customer_tax.py:4-25`；`hooks.py:236-238` | ✅ | ✅ | 读码确认 CRM 建客户经 `frappe_crm_api.create_customer:150-156`，`crm_deal` 在白名单（`:136`），插入前已赋值（HT-013） |
| TS-005 ②③ | `tax_setup.json` 改名；补丁 `OLD_TO_NEW`、`rename_doc`、前后比对、幂等 | `cn_tax/data/tax_setup.json`；`patches/s8_rename_tax_categories.py:7-64` | ✅ | ✅ s8verify 销项 5 模板新名，税率与 `included_in_print_rate` 合理 | 比对不一致时的 `log_error` 位次反，见 **P1-08** |
| TS-005 ④ | 测试旧名全改；旧名只留补丁 | grep `.py`／`.json` 只命中补丁 `:8-16` | ✅ | — | — |
| TS-006 ① | `work_order_operation_time`（WO `before_validate`，排在 `ensure_patched` 后） | `production/operation_time.py:9-55`；`hooks.py:242-245` | ✅ | ✅ | — |
| TS-006 ② | `job_card_scheduled_time`（Job Card `before_insert`） | `operation_time.py:58-94`；`hooks.py:251` | ✅ | ✅（D 探针、E 读码） | — |
| TS-006 ③ | BOM 工序表默认列 Property Setter（只补缺） | — | ✅（无须改） | ✅ | 原生三列已 `in_list_view`，D 未加 fixtures，合方案「只补缺」 |
| TS-007 ① | `cn_bom_source` 两字段（Select、hidden） | `custom_field.json:+335-359` | ✅ | ✅ | — |
| TS-007 ② | 服务端来源判定与五种措辞；有值不改 | `bom_selection.py:136-172,203-206` | ✅ | ✅ | — |
| TS-007 ③ | 前端 `before_save` 弹框（计划逐行、工单单个） | `production_plan.js:1-151,169-201`；`work_order.js:1-34,73-105` | ✅ | 未实点（D 截图四张） | `kept` 再询为用户批准的补充（D 讨论第 4 步） |
| TS-008 ① | `Material Transfer for Manufacture` 入口径；`wip_warehouses`；SQL 只在 Stock Entry 分支排 WIP；调用方传 `company` | `demand.py:13,37-62,75-100`；`safety_stock.py:89`；`reorder_level.py:68`；`rules.py:99,169` | ✅ | ✅ | 默认 WIP 仓改读 `Company.default_wip_warehouse`（用户批准）；`frappe.local` 缓存在长任务中不刷新，见 **P1-09** |
| TS-008 ② | 安全库存逐物料取 `Item Reorder` 仓并集、无行取非 WIP 仓 | `safety_stock.py:76-89` | ✅ | ✅ | — |
| TS-008 ③ | `changes` 明细三步 append；未触发写原因 | `safety_stock.py`、`reorder_level.py`、`rules.py`、`suggestion.py:35-47`、`daily.py:44-86`；`types.py:4-19` | ✅ | ✅ | — |
| TS-008 ④ | 弹窗按公司成表、物料可点 | `replenishment_suggestion_list.js:63-94` | ✅ | 未实点（D 浏览器 json） | — |
| TS-008 ⑤ | 列表首列物料号；两子表默认列；依据项 23 项中文 | 三个 json（`title_field=item_code`、`in_list_view`、`modified` 调大）；`zh.csv` `Replenishment Projected Qty` | ✅ | ✅ | 存值改名无迁移补丁：本片查 s8verify／s8eoqformal 旧值行均 0（见自证复核） |
| TS-009 OB-024 | 两个 `cn_piece_rate` 加 `precision: 4`、调大 `modified` | `custom_field.json:+285-286,+296-297` | ✅ | ✅ s8verify Custom Field `precision=4` | 计件汇总单明细的「计件单价」列仍按 2 位显示，见 **P1-04** |
| TS-009 OB-029 | CRM 14 状态加译不改名；撞名登记 | `zh.csv`（14 行）；`translation_overrides.py`（5 条）；`website_translation.py:36-50`；看板 DOM 补丁 `independent_app_labels.js:8-15,164-168` | ✅ | ⚠️ | 无 context 覆盖波及 Desk 提交成功提示等，见 **P1-02** |
| TS-009 OB-039 | 提交成功提示中文（HT-008 不成立后改前端包装并登记） | `desk_patches.js:7-23`；README Desk 前端覆盖登记 | ✅ | ✅ 彩排取证 `act3-step14.json` 含「已成功提交采购入库」 | 同一取证里旁边的按钮显示「新线索」，见 P1-02 |
| TS-009 OB-042 | 包装 `get_no_result_message`、登记、Node 测试 | `desk_patches.js:170-177`；README | ✅ | ✅ | — |
| TS-009 OB-059 | 质检三项 context 键 | `zh.csv`（`Incoming`／`Outgoing`／`In Process` 带 `Quality Inspection`） | ✅ | ✅ | — |
| TS-009 OB-068 | HT-009 先复现再修 | — | ✅（未复现、未改） | — | 如实记录，不立项 |
| TS-009 OB-069／070／071 | 计件弹窗三段；员工姓名列；单价来源 context 键；0 数量行跳过 | `piece_rate_summary_list.js:10-18`；`piece_rate_summary.json:+43`；`zh.csv`；`piece_rate.py:87-88` | ✅ | ✅ | — |
| TS-009 PH-P1097 | 首桶标签取 `max(key, start)` | `capacity_load.py:20` | ✅ | ✅ | 周三用例已补（IT-010） |
| TS-010 | 策略对比报表：筛选、四指标、缺料判定、报错、默认物料、图表、中文列 | `stock_plus/report/replenishment_strategy_comparison/*.py:1-216` | ✅ | ✅ | 缺料加回本工单发料（`88e3cc1`，D 讨论第 16 步，口径未改）；整年计时 2.383 秒（E IT-011） |
| TS-011 | 业务流程侧栏补入口、`modified` 调大、README 数字随改 | `business_flow.json`（73 项＝7 节＋66 链接，`modified 2026-10-21 21:51`）；README:21 | ✅ | ✅ | 15 项为用户批准（方案「14」笔误） |
| TS-011（HT-011） | `sidebar=Business Flow` 落业务流程侧栏 | — | ✅（D 浏览器探针） | 采信截图 | — |
| TS-012 | `configure_demo_prerequisites`：原生性别／称呼、批号开关、仅默认名时改「演示管理员」；排在 `configure_stock` 后；重跑无改动 | 主仓库 `docker/scripts/configure_apps.py:237-266,455-456` | ✅ | ✅（D 两次实跑日志） | 演示专属设置落在通用配置脚本，见 P1-07 |
| 方案外（E IT-002） | ERPNext fork `validate_fg_completed_qty` 和按精度归一 | erpnext `stock_entry.py:892-895`（`a729571`） | ✅ | ✅ | L5 源码改动，提交信息与侵入度登记缺项，见 **P1-06** |

**需求 AC（本片）**：AC-001～003、005、007～010、012、014（入口部分）、015、016、017 有正向证据（E／D 实跑＋本片读码与只读 SQL）。**AC-004** 在测试站（测试内临时把「支」设为整数）成立；在演示数据上计划数量是 `5259.299` 支，不是 5261（P1-01）。**AC-006** 成立。**AC-011** 中「同一序列、发料计入」成立；「再订货点＞安全库存＞0」的场景数据由片 2 核。**AC-013** 中 OB-039 的提示本身是中文，但同一提示框的「新建」按钮被改成「新线索」（P1-02）。

## 集成检查

| 集成点类型 | 具体落点 | 两端一致否 | 说明 |
|---|---|---|---|
| 事件／消息 | 本片不发不收 realtime 事件；告警走 Error Log | ✅ | 新增 Error Log 标题见交接摘要；`s8_rename_tax_categories` 一处标题／正文位次反（P1-08） |
| 接口契约 | 总纲 §5.1 损耗反算四函数 | ⚠️ | 签名一致；`required_input_qty` 被计划（`process_loss.py:136`）、超产（`overproduction.py:38`）、按订单补货（`rules.py:241`）三处共用，判据唯一；`operation_loss_rates` 无调用方（P1-10）；「整数单位才 ceil」的分支依赖 UOM 数据（P1-01） |
| 接口契约 | 总纲 §5.2 `ChangeRow`／`StepResult.changes` | ✅ | `types.py:4-19` 与写端（三步＋`upsert`＋`daily` 失败行）、读端（`replenishment_suggestion_list.js:75-86`）键名一致，`field`／`outcome` 取值在前端都有标签 |
| 接口契约 | 总纲 §5.3／5.4（`frappe_debug` 演示框架） | 不涉及 | 归片 3 |
| 接口契约 | `docs/开发守则.md` 跨 Phase 契约表：「演示操控的事件协议」（`erx_demo_step`） | 不涉及 | 本片代码不发、不收；`realtime_check.py:5` 明写不复用 |
| 共享状态 | `hooks.py` `doc_events`：Stock Entry `before_validate` 顺序 `apply_batch_factor → unify_difference_account → normalize_fallback_operating_cost`；Work Order `before_validate` 顺序 `ensure_patched → operation_time`；Production Plan `validate` 顺序 `bom_selection → planned_qty` | ✅ | 与方案要求的顺序一致；`frappe_debug` 的 `"*"` `before_insert`（场景日期）因后装而晚于 `frappe_china` 各 `before_insert` 执行 |
| 共享状态 | `before_request`／`before_job` 两个 `ensure_patched`（拆单、超产） | ✅ | 生成器同步调用路径另显式调（E IT-016） |
| 共享状态 | `fixtures/custom_field.json` 与 `hooks.py` fixtures 过滤清单 | ✅ | 本片新增 6 条全部进清单（`hooks.py:314-319`）；两条 `cn_piece_rate` 改 `precision` 并调大 `modified` |
| 共享状态 | `zh.csv` 无 context 覆盖键 `New`／`Qualified`／`Converted`／`Unqualified`／`Qualification`／`Created` | ❌ | 全站生效，波及 Desk、CRM 其它按钮、HRMS 前端（P1-02） |
| 共享状态 | `translation_overrides.py` 与官方同文的 7 条登记 | ⚠️ | P1-05 |
| 共享状态 | UOM「支」的 `must_be_whole_number`（`ensure_cn_uoms` 写端未设，A18／反算读端依赖） | ❌ | P1-01 |
| 共享状态 | `docker/apps.json` 第 9 条 `frappe_debug`；ERPNext 锁 `a729571` | ⚠️ | P1-06、P1-07 |
| 跨模块数据流 | 损耗率 → 计划数量 → 工单 → 超产校验 | ✅ | 同一函数；哈希守卫与上游一致 |
| 跨模块数据流 | 工单工序成本 → 完工入库附加费用（`normalize`）→ `410199` → 生成器月末制造费用凭证（片 2 `monthly._create_overhead_entry`） | ⚠️ | 单张整单入库口径一致；分批完工时附加费用少计，月末凭证按 `410199` 净额同步少记，账平但产品成本偏低（P1-03） |
| 跨模块数据流 | 报价单税模板 → 客户税种 → 订单 `get_party_details` | ✅ | 读码 CRM 订单表单 `refresh` 只在 `customer` 为空时调 `check_customer_for_quotation`，建客户时 `crm_deal` 已在 `before_insert` 前赋值 |
| 跨模块数据流 | 补货需求 → 安全库存 → 再订货点 → 规则建议（同一事务读刚写值） | ✅ | `reorder_level.py:70`、`rules.py:170` 现读 `Item.safety_stock` |

## 业务规则合规核

（以下规则均「未经专家确认」，见 `业务规则.md` 顶部警示。）

| 规则条款 | 本 Round 改动是否涉及 | 结论 | 备注 |
|---|---|---|---|
| BR-001 小企业会计准则 | 是（科目表 `400101` 类型） | 合规 | 只改 `account_type`，科目号、名称、层级不变；`400101` 属成本类，清掉「销售成本」类型与准则分类一致 |
| BR-002 报表构成 | 否 | 合规 | 本片不改三张报表 |
| BR-003 增值税税率 | 是（税种、模板改名） | 合规 | 改名补丁只改名，前后比对税率与科目；s8verify 销项 5 模板税率 0／13／13／3／3 |
| BR-004 未交增值税结转 | 否 | 合规 | — |
| BR-005 城建税与附加 | 否 | 合规 | — |
| BR-006 资产负债表平衡 | 间接（完工入库分录） | 合规 | E 在第 7／8 幕快照实测平衡；本片未独立复算 |
| BR-007 价税分离 | 是（模板改名） | 合规 | `included_in_print_rate` 随模板保持，含税／不含税两套并存 |
| BR-008 完工入库不产生损益类分录 | 是（`unify_difference_account`、`normalize_fallback_operating_cost`、`400101` 类型） | 合规 | s8verify 332 张完工入库 GL 只有 `1405` 借 1,214,318.19／`1409` 贷 1,214,318.19，无 Income／Expense 行；`410199` 在本科目表继承 `root_type=Asset`（成本类），不是损益类 |
| 规则新增／变更检出 ① | 完工入库工序成本＝工单工序成本×完工数÷工单数（`normalize` 的「正确值」） | **草案·待领域专家确认** | AI 推断的成本分摊口径，已并入 `SH-P1S8010`；分批完工下它本身不对，见 P1-03 |
| 规则新增／变更检出 ② | 投料＝逐道 ceil(产出÷合格率)；损耗率整数精度取法（A18） | 非领域不变量 | 与需求 §4.17「计划口径的选择，不登记」一致 |
| 规则新增／变更检出 ③ | 银行类收付款方式挂 `1002` | 非领域不变量 | 建账默认，已进 `SH-P1S8005` |

## 自证复核

| 被审产物声称 | 实际复核结果 | 一致否 |
|---|---|---|
| D TS-003／004、E TS-003：「1000→4.9…」「5264／5261」 | 测试 `setUp` 把「支」临时设为整数（`test_process_loss.py:11,137`）；s8verify／s8eoqformal／test.localhost 的「支」`must_be_whole_number=0`；生成的 BOM 整体值 4.9303、计划 `3644.695` 等小数；彩排取证 `act4-step6.json` 里第 4 幕计划数量 `5259.299` 支 | ❌（P1-01） |
| D TS-009：「CRM 无 context 撞名覆盖影响面：New→新线索（公共'新建'类文字）…」 | 影响面列了类别，没指出 Desk 提交成功提示的「新建」按钮（`success_action.js:77`）；彩排取证 `act3-step14.json` 实为「已成功提交采购入库／新线索／打印／邮件」 | ❌（P1-02） |
| D TS-009 ①／HT-010：「0.004 存得进、表单显示 0.0040」 | 工序与 BOM 工序属实；同一份 `s8-ts009-display-acceptance.json` 的计件明细文本里「计件单价」列是「¥ 0.00」 | 部分（P1-04） |
| E IT-001／018：「`normalize_fallback_operating_cost` 幂等，工序成本按实计入」 | 读码与 mock 探针：单张整单入库 100→100、二次执行不变，属实；分批完工（先报工 500 入库 500、再报工 500 入库 500）合计 75，应为 100（`probe_normalize_partial.out` case D） | 部分（P1-03） |
| E IT-002：「`stock_entry.py:892` 和按库存精度归一」 | `a729571` 只改此一处，`flt(flt(a,p)+flt(b,p),p)`，语义与项目概况:173 登记一致 | ✅ |
| E 拿不准处：`Projected Qty` 存值改名无迁移补丁 | s8verify、s8eoqformal `tabReplenishment Basis Item` 中 `basis='Projected Qty'` 均为 0 行；演示站清洁基准 GL／SLE 为 0、无建议单（项目概况:69）。暂无数据受影响，不立项 | ✅ |
| D TS-001：「验收 grep 只额外命中测试源码」 | 复跑 grep：`install.py:6` 一处＋`test_install.py` 4 处 | ✅ |
| E TS-004：「上游哈希复算一致」 | 本片独立复算一致 | ✅ |
| D TS-012：「两次运行，第二次无改动」 | 读码：四项都有「已是目标值不写」判断；`Administrator` 只在 `first_name=='Administrator'` 时改 | ✅ |

## 问题清单

| # | 严重程度 | 定位 | 问题描述 | 违背的标准/意图 | 建议 | 建议档位 | 待裁决点 | 状态 | 用户裁决 |
|---|---|---|---|---|---|---|---|---|---|
| P1-01 | 中 | `frappe_china/accounting/install.py:6-64`（`ensure_cn_uoms` 建「支」不设 `must_be_whole_number`）；`process_loss.py:71-76,97-106` | 需求 §4.6.1 明写「库存单位『支』须为整数」，A18、需求 §4.6.2 的逐道 ceil、AC-004 的 5261 都以此为前提。实际 s8verify、s8eoqformal、test.localhost 三站的「支」都是 `must_be_whole_number=0`（只读 SQL），测试只在 `setUp` 里临时设 1。于是生成数据中 BOM 整体值存 4.9303、A18 从不触发，`required_input_qty` 走 `flt(x, 精度)` 分支：计划与工单数量是 `3644.695`、`2629.651` 支等小数（s8verify 332 张工单全为小数），彩排取证 `Spike/P1S8R6-D/acts/acceptance/act4-step6.json` 第 4 幕画面上计划数量为「5,259.299 支」，不是需求例子的 5261。测试与验收都通过，是因为测试数据与演示数据的单位属性不同 | 需求 §4.6.1、§4.6.2、AC-004；总纲 A18、§5.1；开发守则「判据必须能区分」 | 两条路：① 「支」改为整数单位（`ensure_cn_uoms` 对「支」等计数单位设 `must_be_whole_number=1`，补迁移补丁），再核生成器全链（工单、拆卡、完工入库、损耗数量都要整数）并整场重跑；② 接受小数，更正需求 AC-004 与第 4 幕讲解口径，并删掉测试里临时改单位的写法，让测试与演示同条件。未查演示站，以 s8verify 与彩排取证推断 | 出方案修 | 「支」是否改为整数单位（①）还是接受小数支（②）；选①时其它计数单位（个、件、只…）是否一并改 | 待裁决 | |
| P1-02 | 中 | `translations/zh.csv` 无 context 行 `New,新线索`、`Qualified,合格`、`Converted,已转化`、`Unqualified,不合格`、`Qualification,需求确认`；`tests/translation_overrides.py:28-33` | 为让 CRM 下拉显示中文，覆盖了 5 个无 context 的公共源词，全站生效。实测波及：① Desk 提交成功提示的「新建」按钮（`frappe/.../success_action.js:77` `__("New")`）显示为「新线索」——彩排取证 `act3-step14.json` 里就是「已成功提交采购入库／新线索／打印／邮件」，演示中报价单、订单、发货、发票、采购入库、采购发票六类单据每次提交都会出现；② 树视图主按钮 `treeview.js:491`；③ CRM 自身多处「New」按钮（`ActivityHeader.vue:70`、设置页 7 处）、HRMS 前端列表 `ListView.vue:34`；④ `Qualification` 也是 HRMS 员工「教育经历」子表列名（`employee_education.json:28`）与 ERPNext 线索分节名，现显示「需求确认」。D 回执列了影响类别，漏了 ①。另 `Created` 由官方「创建」改成「已创建」，同样全站生效 | 需求 OB-029「CRM 状态显示中文」只针对 CRM；开发守则「覆盖官方词典的键须逐条写真实依据」；项目概况:212「改无 context 行前须查六个 app 的全部出处」 | 把 CRM 状态译名收窄到 `/crm`：zh.csv 改用带 context 的键（或只在 `website_translation.py` 给 `/crm` 页注入的词典里放这 14 个状态），下拉与看板由本 app 已有的 `/crm` 注入与看板 DOM 补丁取译；全局撤掉 5 条（及 `Created` 视需要）覆盖与登记。至少须修 ① | 新Session修 | 收窄到 `/crm`，还是保留全局覆盖、只另补 Desk 提交提示按钮 | 待裁决 | |
| P1-03 | 中 | `accounting/stock_entry_accounts.py:162-194` | `normalize_fallback_operating_cost` 以「工单工序总成本×本次完工数÷工单数」为正确值。上游 fallback（`stock_entry.py:4510-4515`＋`bom.py:1844-1858`）对已报工工序加的是**累计实际总额**、再乘本次完工数，所以修正的前提只在「全部报工完再一次入库」时成立。分批完工（上游 `check_if_operations_completed`，`stock_entry.py:1168-1185`，只要求累计报工数不小于累计入库数）时：先报工 500（实际 50）入库 500、再报工 500（累计 100）入库 500，两张合计记 75，少记 25%（mock 探针 case D，`Spike/P1S8R8-F/p1/probe_normalize_partial.out`）。演示数据每张工单只有一张完工入库（s8verify 332／332、s8eoqformal 331／331），不暴露；但 `frappe_china` 装客户正式库，分批完工在实际使用中常见 | 需求 §4.7「完工入库后的分录只剩借库存商品／贷在产品／贷 410199」的成本完整性；E IT-018 修法 1「工序成本按实计入」 | 把正确值改为「截至本次的累计实际工序成本 − 本工单已提交完工入库已吸收的 fallback 工序成本」，按本次完工数在剩余未入库数中的占比分摊；补分批完工的回归用例（先红后绿）。口径牵动 `SH-P1S8010`，先写方案 | 出方案修 | 分摊口径（按累计实际成本还是按计划单位成本）须定；是否与 `SH-P1S8010` 一起交会计 | 待裁决 | |
| P1-04 | 低 | `production_plus/doctype/piece_rate_summary_item/piece_rate_summary_item.json:50-54`（`rate` Currency，无 `precision`） | OB-024 只改了工序与 BOM 工序两个 `cn_piece_rate`。计件汇总单明细的「计件单价」列仍按币种 2 位显示：库里存 0.002～0.005（s8verify 1806 行全部 <0.01），界面显示「¥ 0.00」——D 自己的验收文本 `s8-ts009-display-acceptance.json` `rateSources.text` 即为「…1100¥ 0.00BOM 工序¥ 0.40」。第 6 幕打开计件汇总单时可见 | 需求 OB-024（第 6 幕）「计件单价至少存 4 位小数」、AC-012 的意图 | `rate` 加 `"precision": "4"`，调大 `modified`，migrate 后看一张汇总单 | 本Session修 | — | 待裁决 | |
| P1-05 | 低 | `tests/translation_overrides.py`（`Field`、`New Value`、`Reason`、`Result`、`Skipped`、`Updated`、`Warehouse` 七条）；`zh.csv` 对应七行 | 七条的「我们的译文」与官方完全相同（如 `Warehouse` 仓库→仓库），csv 里加了这七行，只因与官方词典有交集就登记成覆盖，依据写「本 app 自有源词（SL-007…）」。官方已给同一译文，csv 行不必要；同一 Round 的 TS-010 对「公司不存在」就是删掉重复行、不登记 | 开发守则「译名自检时机」：不得为让交集断言通过而整批登记 | 删这七行 csv 与七条登记，跑译名三件套确认仍过 | 本Session修 | — | 待裁决 | |
| P1-06 | 低 | ERPNext fork `a729571`；总纲 §七；`docs/项目概况.md:173` | ERPNext 源码改动（L5）不在方案任务与 §七侵入度表里（由 E IT-002 引入，用户批准提交）。开发守则「确须改源码时两条义务」：① 提交信息应注明为何 hook 不可行——`a729571` 只写了浮点原因，没写为何不用类方法替换（L4，同 `overproduction.py` 的做法）；② 已知限制要写「能否将来上游化」——概况:173 只写了升级时复核。这是上游真缺陷，可上游化 | 开发守则「扩展 ERPNext 优先用 hook」与两条义务；总纲 §七 | 概况:173 补「为何不用 L4、可上游化」，并考虑向 `frappe/erpnext` 提 PR；提交信息不改写历史，补在概况即可 | 本Session修 | 是否向上游提 PR | 待裁决 | |
| P1-07 | 低 | 主仓库 `docker/apps.json:47-52`、`docker/scripts/setup.sh:352-365`；`configure_apps.py:237-266,455-456` | 需求 §4.5 与开发守则「客户正式库从空站新建、不装 `frappe_debug`」，但 `frappe_debug` 进了 `apps.json` 后，`setup.sh` 第 6 段对任何站都按 `apps.json` 全装，没有「演示专用」开关；`configure_apps.py` 是通用配置脚本，跑它就会把 `Administrator` 改名「演示管理员」、开批号全局开关。按方案 TS-001 第 4 步与 TS-012 字面合规，但两者合起来，客户库目前没有「不装、不配」的路径 | 需求 §4.5 末条；DEC-024 只对演示账号；开发守则「客户正式库从空站新建」 | `apps.json` 条目加 `"demo_only": true`、`setup.sh` 按参数跳过；`configure_demo_prerequisites` 改为显式参数（如 `--demo`）才跑。客户库建站流程尚未立项，可登记延迟 | 延迟或不修 | 本轮修，还是登记到客户上线前（与 `SH-P1S8009` 同期） | 待裁决 | |
| P1-08 | 低 | `patches/s8_rename_tax_categories.py:431-434`（`frappe.log_error(f"Tax data changed…", "S8 tax template rename mismatch")`） | 位次反：上游签名 `log_error(title, message)`（`frappe/utils/error.py:44`），长串无换行不触发互换，Error Log 标题成了截到 140 字的前后快照，固定标题落进正文。只在改名前后数据不一致时触发 | 开发守则「静默失败」（告警要可读）；同 S7 F 片1 P1-09 同类 | 改关键字参数 `title=…, message=…` | 本Session修 | — | 待裁决 | |
| P1-09 | 观察 | `replenishment/demand.py:37-62` | `wip_warehouses` 按 `frappe.local` 缓存，方案说「按请求缓存」。生成器在一个 RQ 长任务里逐日跑一年，`frappe.local` 不重置，期间新出现的工单 WIP 仓不会进集合。演示数据只有一个 WIP 仓（s8verify 332 张工单全为「进行中 - HDTH」＝公司默认），不暴露 | 方案 TS-008「结果按请求缓存」 | 生成器每日开头清 `frappe.local.cn_wip_warehouses`，或按 `as_of` 作键 | 延迟或不修 | — | 待裁决 | |
| P1-10 | 观察 | `production/process_loss.py:17-24` | §5.1 契约里的 `operation_loss_rates` 实现了但无任何调用方（两 app grep 只命中定义）；`overall_loss_percentage`、`required_input_qty` 各自另查工序表 | 审法第 2 层「排除死代码」 | 删掉，或让另两处改用它 | 延迟或不修 | — | 待裁决 | |

（严重程度：高=阻断/根因偏离 · 中=需修 · 低=技术债 · 观察=可容许偏差记录。编号为片内临时号，收口时统一改 `FD-`。）

## 跨片一致性（交接摘要）

**本片发出／消费的事件**：不发不收 realtime 事件。新增 Error Log 标题：`frappe_china manufacturing difference account missing`、`frappe_china s8_cn_accounting_defaults`、`S8 tax template rename mismatch`（位次反，P1-08）、`Work Order Operation Time Mapping`、`Job Card Scheduled Time Mapping`；补货沿用 S7 标题。

**本片暴露的接口**：
- `frappe_china.production.process_loss.required_input_qty(bom_no, output_qty)`、`overall_loss_percentage`、`whole_number_loss_percentage`、`production_plan_planned_qty`；整数单位才 ceil（P1-01）。片 2 生成器、片 3 第 4 幕都消费其结果。
- `frappe_china.production.overproduction.ensure_patched`（`before_request`／`before_job`／WO `before_validate`）；生成器同步路径须自行调（E IT-016 已做）。
- `frappe_china.accounting.stock_entry_accounts.unify_difference_account`、`normalize_fallback_operating_cost`（Stock Entry `before_validate` 第 2、3 位）；后者靠「插入、提交各跑一次、第二次空操作」的幂等，片 2 `insert_and_submit` 依赖它；它的正确值口径即 `SH-P1S8010`，片 2 `monthly._create_overhead_entry` 按 `410199` 净额记月末制造费用，二者须同口径（P1-03）。
- `frappe_china.production.bom_selection`：`cn_bom_source` 取值 `confirmed/kept/manual`（字段）与 `doc.flags.cn_bom_choice["source"]` 的 `plan/auto`（内存）；生成器建单留空即自动选。
- `frappe_china.replenishment.types.ChangeRow`、`StepResult.changes`；`run_daily` 结果多出 `changes`，片 2／3 若展示或断言需按新键。
- `frappe_china.replenishment.demand.wip_warehouses(company)`（`frappe.local` 缓存，P1-09）。
- `Replenishment Basis Item.basis` 存值 `Projected Qty` 改为 `Replenishment Projected Qty`。
- 报表 `Replenishment Strategy Comparison`（筛选键 `company`、`items`、`period_{1,2,3}_{from,to}`；返回 `message` 非空时图表为 None），片 3 第 8 幕消费。
- Customer `before_insert` 税种沿用；税种与模板新名（`13% 专票 含税价 - {缩写}` 等），片 3 `demo.yaml:54` 直接引用该名。
- `docker/scripts/configure_apps.py:configure_demo_prerequisites`；`frappe_china.install.TAIL_APPS=("frappe_china","frappe_debug")`。
- ERPNext fork `a729571`（HT-023 归一），片 2 第 7 幕用例依赖。

**本片依赖的接口**：
- 片 3 `frappe_debug.demo.scene_date.apply_scene_date`（`doc_events "*"` `before_insert`）在本片全部 `before_insert`（Customer 税种、Work Order 选 BOM、Job Card 排程截短）之后执行；它只改「等于系统今天」的日期字段，本片钩子不读这些字段，未见冲突，请片 3 确认它不改 Job Card `scheduled_time_logs` 的起止时间。
- 片 2 生成器对 UOM「支」的使用（`masters.py:594-596` 只检查存在、不设整数），决定 P1-01 在演示数据上的表现。
- 片 3 第 3 幕取证显示的提交成功提示按钮（P1-02）、第 4 幕计划数量（P1-01）、第 6 幕计件汇总单（P1-04）。

**本片依赖的跨片共享状态**：
- `frappe_china/hooks.py`：本片新增 `doctype_js` BOM／Production Plan；`doc_events` Customer、BOM、Work Order `before_validate`、Job Card `before_insert`、Stock Entry 三项列表、Production Plan 两项列表；`fixtures` 清单 6 条；`before_request`／`before_job` 各加一条。
- `fixtures/custom_field.json`：本片新增 6 条（BOM Operation 损耗率、Production Plan Item 4 条、Work Order 1 条），改 2 条精度。
- `zh.csv`：本片新增约 110 行（含 14 个 CRM 状态、质检三个 context 键、策略对比报表列名、换 BOM 弹框、补货明细列名）；**无 context 的 `New`／`Qualified`／`Converted`／`Unqualified`／`Qualification`／`Created` 覆盖全站生效**（P1-02），请收口核片 2／3 有无依赖这些键的界面文字。
- `translation_overrides.py` 新增 14 条（P1-05 涉及其中 7 条）。
- `workspace_sidebar/business_flow.json` 66 入口；片 3 演示配置的路由带 `sidebar=Business%20Flow`。
- `docker/apps.json`：ERPNext `a729571`、`frappe_china` `75ceb04`、`frappe_debug` `d8614a5`（第 9 条，P1-07）。
- UOM「支」`must_be_whole_number=0`（P1-01）。

## 总体判断

部分满足。账务修正、超产替换、税模板沿用与改名、工时口径、换 BOM 确认、补货口径与明细、策略对比报表、侧栏、前置数据都已落地且生效，E 修过的 IT-001／002／008～011 本片复核修得对（IT-018 修法见下）。关键缺口：① 演示数据的「支」不是整数单位，需求与方案围绕整数单位设计的 A18 与逐道取整在演示上不生效，第 4 幕显示 5259.299 支（P1-01）；② 为 CRM 状态做的全局无 context 覆盖，使 Desk 每次提交成功提示里的「新建」按钮显示「新线索」（P1-02）；③ LG-001 修复在分批完工入库时少计工序成本，客户正式库会遇到（P1-03）。

## 复核建议

1. **定级在边界上的**：P1-01 在「中／高」之间——数字错在演示核心画面（第 4 幕），但账务与流程都不坏、AC-004 在测试站成立，故定中；若用户认为 5261 是第 4 幕必须讲出来的数，应升高。P1-02 在「中／低」之间——只是文字，但六类单据每次提交都出现、且误导（按钮实为「新建」），定中。P1-04 在「低／中」之间——第 6 幕若打开汇总单明细就会看到「¥ 0.00」单价，取决于讲解是否点开。
2. **查得最浅的**：前端交互（`production_plan.js`／`work_order.js` 的 `before_save` 弹框、`bom.js` 只读切换、补货结果弹窗）只读码与 `node --check`，没在浏览器实点；Python 全量没跑。查法：测试站开一张生产计划，取销售订单后保存，看弹框、`cn_bom_source` 与「推荐 {0}」描述；开补货建议列表点「立即计算」。
3. **没往哪找**：没核 `production_plan_planned_qty` 在生产计划**提交后**由原生 `update_after_submit` 或工单回写触发 `validate` 时是否会改已提交行的 `planned_qty`；没核 `job_card_scheduled_time` 与片 3 场景日期钩子在开产能计划时的时间叠加；没核多公司同时启用补货时的 `wip_warehouses("*")` 组合；没在真实站点上实跑 P1-03 的分批完工路径（只用 mock 复算上游公式，公式取自读码）。
4. **拿不准处**：P1-01 的根因究竟是「`ensure_cn_uoms` 应设整数」还是「R2 时演示站的『支』被人工设过整数、清洁基准重建后丢了」——R2 实操记录 OB-027 显示当时「支」是整数，现三站都不是，期间谁改的查不到（未查演示站）。P1-07 按方案字面合规，算不算发现取决于是否把「客户库不装」当成本 Stage 要兑现的约束。
