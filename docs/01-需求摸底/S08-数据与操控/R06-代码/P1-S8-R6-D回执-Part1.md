# P1-S8-R6 D 回执 · Part1

**日期**：2026-10-21｜**执行者**：Codex｜**打 tag**：否
**依据**：[R5 开发方案·Part1](../R05-开发方案/P1-S8-R5-C开发方案-Part1.md)及总纲。

## 逐项执行结果

| 任务 | 对应切片 | 落地位置（文件:行） | 结果 | 完成时间 | 说明 |
|---|---|---|---|---|---|
| TS-001 骨架、装序、after_commit | SL-001 | `frappe-bench/apps/frappe_debug/frappe_debug/tests/test_smoke.py:8`、`frappe-bench/apps/frappe_china/frappe_china/install.py:203` | ✅完成 | 2026-10-21 | 私有仓库已创建、本地骨架已建并安装到测试站；`frappe_debug` 冒烟 1/1 通过，装序检查 `ok: true`；after_commit 提交／回滚两条定向测试已分别通过，Ruff 检查通过。`frappe_debug` 已提交并推送，commit=`616d897`；`apps.json` 与锁文件仍待按方案登记锁定 commit |
| TS-002 账务修正与迁移 | SL-002 | `frappe-bench/apps/frappe_china/frappe_china/accounting/stock_entry_accounts.py:11`、`frappe-bench/apps/frappe_china/frappe_china/patches/s8_cn_accounting_defaults.py:7`、`frappe-bench/apps/frappe_china/frappe_china/tests/test_s8_accounting.py:11` | ✅完成 | 2026-10-21 | 新公司默认、迁移范围／幂等／自定义值保留、银行方式补齐与付款取科目、制造差异科目中式隔离均有测试；完工入库集成实测生成工序成本并只记 `1405`／`1409`／`410199`，无损益行及「Cost of Goods Sold」提示 |
| TS-003 损耗率字段与整体值 | SL-003 | `frappe-bench/apps/frappe_china/frappe_china/production/process_loss.py:29`、`frappe-bench/apps/frappe_china/frappe_china/public/js/bom.js:19`、`frappe-bench/apps/frappe_china/frappe_china/tests/test_process_loss.py:8`、`frappe-bench/apps/frappe_china/frappe_china/tests/test_bom_loss.cjs:18` | ✅完成 | 2026-10-21 | 原有 3/3 验证后发现重新读库全零覆盖手填值；用户选择 A（D 讨论第 2 步）后，先跑红（Python 8 条中 5 失败，前端 2/2 失败），前后端改为任一非零才启用工序模式。现损耗／计划 8/8、前端损耗 2/2 通过；全零重读重存保留 5%，混合零工序自动算；切片全量门随 TS-004 收尾 |
| TS-004 反算、超产、按订单放大 | SL-003 | `frappe-bench/apps/frappe_china/frappe_china/production/process_loss.py:99`、`frappe-bench/apps/frappe_china/frappe_china/production/overproduction.py:16`、`frappe-bench/apps/frappe_china/frappe_china/public/js/production_plan.js:1`、`frappe-bench/apps/frappe_china/frappe_china/replenishment/rules.py:193` | ✅完成 | 2026-10-21 | 损耗／计划 8/8、超产 5/5、补货规则 6/6、Node 92/92 通过。读库确认 5% 重存保留、5000 反算 5264；推荐提示截图已核、专用夹具 10 项清理完成。首次全量的科目表哈希、CSV 排序、工序损耗译名已修复；SL-004 全量集成 431/431、另 5/5＋4/4 通过，覆盖 SL-003 |
| TS-005 税模板沿用与改名 | SL-004 | `frappe-bench/apps/frappe_china/frappe_china/accounting/customer_tax.py:1`、`frappe-bench/apps/frappe_china/frappe_china/patches/s8_rename_tax_categories.py:1`、`frappe-bench/apps/frappe_china/frappe_china/cn_tax/data/tax_setup.json:1` | ✅完成 | 2026-10-21 | 客户税种沿用先红后绿 4/4；改名最新复验 2/2（86.931 秒），12 模板／13 规则的税率、科目、含税标志保持，含中式范围与快照守卫。并存新名按方案跳过，不合并。旧名引用仅余补丁映射。全量 431＋5＋4 全过，含既有税务、结转与最小闭环；无新工程约定 |
| TS-006 工时与 BOM 工序列 | SL-005 | `frappe-bench/apps/frappe_china/frappe_china/production/operation_time.py:9`、`:60`；`hooks.py:191`、`:200`；`tests/test_operation_time.py:1` | ✅完成 | 2026-10-21 | HT-007 回滚探针通过后先红后绿；新验收 10/10，拆卡 9/9、容量报表 2/2、工序流转 16/16，Node 92/92；切片全量 frappe_china 集成 441/441（2373.200 秒）、旧类 5/5、未分类 4/4，退出 0；frappe_debug 1/1、译名自检通过。Ruff 与 diff check 通过。无新增工程约定 |
| TS-007 换 BOM 人确认 | SL-006 | `frappe_china/production/bom_selection.py`、`hooks.py`、`fixtures/custom_field.json`、`public/js/production_plan.js`、`public/js/work_order.js`、`translations/zh.csv`、`tests/test_bom_confirmation.py`、`test_bom_confirmation.cjs` | ✅完成 | 2026-10-21 | 已实现并完成测试站迁移；来源定向 6/6、建单路径 6/6、前端专项 17/17，全 app Node 109/109。浏览器同一计划先 kept、再 confirmed、第三次保存无弹框，夹具 12 项已清理。修正旧评论断言后，全量 449/449（2392.615 秒）、旧类 5/5（0.258 秒）、未分类 4/4（0.006 秒）均通过；Node 109/109，debug 1/1、译名自检通过。首次全量失败为旧措辞与 SL-006②④ 不符，详见下表。TS-007 完成 |
| TS-008 补货口径与呈现 | SL-007 | `frappe_china/replenishment/demand.py:37`、`:64`；`safety_stock.py:39`；`reorder_level.py:22`；`rules.py:75`；`suggestion.py:6`；`daily.py:17`；`public/js/replenishment_suggestion_list.js:75`；`stock_plus/doctype/replenishment_suggestion/replenishment_suggestion.json:3` | ✅完成 | 2026-10-21 | 用户批准的 Company WIP 仓口径已实现；真实库存 3/3、明细契约 5/5，levels 9/9、rules 6/6、daily 5/5、integration 5/5。列表 title_field=item_code 和每公司单表已补；结果表契约 3/3、Node 109/109、Ruff 181 文件通过；真实浏览器核对列表、实际计算、两子表列与 23 项中文。译名 20/20、质量 13/13、自检、debug 1/1 通过。最终版本全量集成 457/457（2345.409 秒）、旧类 5/5（0.248 秒）、未分类 4/4（0.005 秒），退出码 0；见 `s8-ts008-full-final2.log`。 |
| TS-009 译名与显示 | SL-008 | frappe_china/public/js/desk_patches.js、independent_app_labels.js、tests/test_s8_labels.py、计件字段与列表 | ✅完成 | 2026-10-21 | 全量459/459＋5/5＋4/4、Node115/115、Ruff182文件及译名门通过；CRM真实下拉/看板、采购入库真实提交、工序/BOM保存重读、有数据SPC、计件姓名/来源及对账均实测；临时夹具已清理。 |
| TS-010 策略对比报表 | SL-009 | stock_plus/report/replenishment_strategy_comparison/replenishment_strategy_comparison.py:150、tests/test_strategy_comparison.py:15 | ✅完成 | 2026-10-21 | 先红6/6模块缺失，再绿6/6；真实中文报表/三段柱图已验。库存均值880/1050/900、采购2/1/0、总成本44.8219178082/25.7534246575/4.9315068493。切片全量465/465＋6/6＋4/4通过，退出0；整年性能按方案待TS-017的s8dev数据就绪补验。 |
| TS-011 侧栏入口 | SL-009 | workspace_sidebar/business_flow.json:3、tests/test_business_flow_navigation.py:15、README | ✅完成 | 2026-10-21 | 用户批准15项完整清单（D讨论第9步），14为方案计数笔误；7节66入口，静态6/6，15项逐一实点打开、中文标签及报价页sidebar_title=Business Flow通过；译名门、Node115/115、Ruff和切片全量均通过。 |
| TS-012 前置数据 | SL-010 | docker/scripts/configure_apps.py:237、Spike/P1S8R6-D/test_demo_prerequisites.py | ✅完成 | 2026-10-21 | 原生性别/称呼种子、批号开关、仅默认管理员姓名改中文已实现；Spike单测先红3条缺函数，后绿4/4。两次真实shell入口均退出0，第二次无改动；浏览器 Gender 7 项、批号开关及管理员中文显示通过。标准全量集成465/465（2434.073秒）、旧类6/6（0.312秒）、未分类4/4（0.004秒），退出码0；详见 s8-sl010-full.log。 |

## 全量验证

| 门 | 结果 |
|---|---|
| 执行前 frappe_china Python 基线 | 未完成：长测于 33/约 400 测试中断；期间代码已变化，不能作基线 |
| 执行前 Node 基线 | 89/89 通过 |
| frappe_china TS-002 定向验证 | `test_company` 14/14 通过；迁移扩展、制造科目隔离、`test_s8_accounting` 完工入库、`frappe_debug` 冒烟各 1/1 通过 |
| `frappe_debug` | 冒烟 1/1；Ruff check 与 format check 通过 |
| TS-003／004 损耗与计划定向验证 | 集成测试 8/8 通过（`frappe-bench/logs/s8-zero-loss-green.log`，9.884 秒）；红态 `s8-zero-loss-red.log` 8 条中 5 失败；前端损耗 2/2 及推荐提示 1/1 通过 |
| TS-004 超产与补货 | `s8-zero-overproduction-green.log` 5/5，8.433 秒；`s8-zero-rules-green.log` 6/6，1.049 秒；按订单用例的全局 `get_all` mock 原误拦真实 BOM 元数据，已收窄至带 `cn_rule_order` 筛选的 Item 查询，不改验收值 |
| SL-003 Node | 92/92 通过（`s8-zero-node.log`），原基线 89，新增推荐提示 1 条、全零只读 2 条 |
| SL-003 浏览器与读库 | `Spike/P1S8R6-D/SL003-manual-recommendation.png`：计划 5300、推荐 5264、订单待产 5000，描述为「推荐 5264」；`quantity_ui_fixture.py cleanup` 清理 10 项；`s8-loss-readback-green.json` 确认全零读库仍为手填 5% |
| SL-003 全量首次结果 | `s8-sl003-full.log`：集成 425 条，3 失败；old category 5/5、未分类 4/4。失败为科目表旧哈希、CSV 排序、缺 `Process Loss % (Operation)` 译名；未误记为通过 |
| 译名修复 | CSV 按 `(source.casefold(), context)` 排序、补工序损耗译名；三件套均已通过，详见后续行 |
| TS-005 客户税种 | `test_customer_tax` 4/4，18.385 秒；含实际 CRM 建客户、报价转订单及重取客户税模板；先红为模块缺失和旧税种名错误 |
| TS-005 改名复验 | `test_s8_tax_migration` 最新 2/2，86.931 秒；含中式范围、快照守卫、新名已存在时跳过、二次执行不改名，日志 `s8-tax-migration-green.log` |
| 科目表守卫 | `s8-chart-guard-green.log` 1/1，0.062 秒；依批准的单处类型修改更新原始字节基准 |
| 译名三件套 | `test_translations` 20/20；`test_translation_quality` 13/13，0.194 秒；`translation_check.run` 输出「译名自检通过」，返回空问题列表 |
| SL-004 全量门 | `s8-ts005-full.log`：集成 **431/431**，2413.999 秒；old category **5/5**，0.275 秒；未分类 **4/4**，0.006 秒；进程退出 0。覆盖新客户／改名及既有税务、结转、最小闭环，运行期间 app 文件冻结 |
| TS-006 测试准备 | `Spike/P1S8R6-D/test_operation_time.py` 起草后于 SL-004 全量结束后加入 app。`tests/test_operation_time.py` 10 条验收测试先红后绿；覆盖三入口 250／90／180、拆卡 100／100／50、开启排程连续性与报表、固定／其它 BOM／重复工序／映射失败／重存及排程跨间隔截断 |
| HT-007 生命周期探针 | `operation_time_probe.py` 在 test.localhost 事务内注入 250／90／180，并临时挂 Job Card before_insert 截短。三张卷簧卡排程前为 250／280／270 分，截短为 100／100／50；起止依次 08:00～09:40、09:50～11:30、11:40～12:10。实际 insert/submit 生命周期后断言通过，退出 0，finally rollback；证据 `logs/s8-operation-time-probe.json`。前两次仅因相对日志路径失败，非断言失败，已修正重跑 |
| SL-004 Node | `s8-ts005-node.log` 92/92，224.9296 毫秒，退出 0 |
| TS-006 新验收 | `s8-operation-time-red.log`：10 条，5 失败＋4 错误（新模块尚不存在），10.444 秒；`s8-operation-time-green.log`：10/10，9.812 秒。三入口读库均 250／90／180，二次保存不复乘；开关容量计划均 100／100／50；开容量时排程和为卡工时、后卡不早于前卡止时，报表需求合计 250/60 小时；固定／其它 BOM／重复出现映射、短排程／缺排程／提交态不动等通过 |
| TS-006 相邻回归 | `s8-operation-split-green.log` 9/9（6.812 秒）；`s8-operation-capacity-green.log` 2/2（3.675 秒）；`s8-operation-flow-green.log` 16/16（23.535 秒）。Ruff lint 与 format check 178 文件通过，diff check 通过 |
| TS-006 Node | s8-ts006-node.log：92/92，155.0997 毫秒 |
| TS-007 前端暂存红绿 | 用户批准 A 后，Spike/test_bom_confirmation.cjs 对现 app 跑红：11 条全失败（before_save 缺失），80.6828 毫秒；仅在 Spike/bom-confirmation-draft 加实现后 11/11 通过，77.8519 毫秒。覆盖保留→再次保存换用、confirmed/manual 不重询、关闭中止、候选成本与转义、工单 setter／计划来源。尚未写入 app，不能据此认定集成验收完成 |
| TS-007 前端重存边界 | 补已保存草稿工单 kept 后再存场景，先 12 条中 1 失败（s8-bom-confirmation-node-saved-kept-red.log）；修正草稿条件后 12/12，93.4397 毫秒（s8-bom-confirmation-node-draft-green.log）。保留的草稿可再询，已提交单不询 |
| TS-007 后端无站点探针 | bom_confirmation_unit_probe.py 不连接数据库，仅复用暂存测试的 mock 契约；现实现 4 条有 9 失败＋4 错误，草稿 4/4（0.006 秒）。覆盖 source 非空保留、计划优先、空来源自动及五种评论；迁移元数据与真 DocType 测试尚未执行，未冒充已验收 |
| TS-006 切片全量门 | `s8-ts006-full.log`：frappe_china 集成 441/441，2373.200 秒；旧类 5/5，0.261 秒；未分类 4/4，0.006 秒，退出 0。Node 92/92，frappe_debug 1/1，`translation_check.run` 输出译名自检通过 |
| TS-007 当前 app 定向门 | `s8-bom-confirmation-integration-final-targeted.log` 来源 6/6（2.757 秒），`s8-bom-selection-hooks-green.log` 建单路径 6/6（8.692 秒）；`s8-bom-confirmation-node-green.log` 专项 17/17；完整 Node 重跑 109/109（174.084 毫秒），退出 0，含手工 BOM 恰好等于推荐项仍为 manual |
| TS-007 浏览器与清理 | `s8-bom-confirmation-ui.json`：test.localhost 同一计划首次 kept、再次 confirmed、第三次保存无弹框；截图 `Spike/P1S8R6-D/SL006-plan-*.png`。`s8-bom-confirmation-fixture-cleanup.log` 列出 12 项清理；迁移已自然完成，未操作演示站 |
| TS-007 译名门 | `s8-bom-confirmation-translations.log` 20/20，`s8-bom-confirmation-translation-quality.log` 13/13，`s8-bom-confirmation-translation-check.log` 自检通过；当前切片全量结束后补 debug 冒烟及译名自检 |

## TS-009 实测证据与验收边界

| 验收 | 实测与证据 |
|---|---|
| ①／HT-010 | s8-ts009-display-acceptance.json：Operation数值0.004、BOM三行均0.004，保存重读控件0.0040。截图SL008-operation-rate-saved.png、SL008-bom-rate-saved.png。 |
| ② | crm_status_acceptance.cjs读取真实role=option及看板标题：线索/商机各7项中文、存值不改。证据s8-ts009-crm-acceptance.json及SL008-crm-{leads,deals}-{dropdown,kanban}.png；旧脚本期望数组不充作证据。 |
| ③／HT-008 | purchase_receipt_ui.cjs实际提交MAT-PRE-2026-00005，docstatus=1，提示已成功提交采购入库，截图SL008-submit-success-real.png。finally取消/删除单据及物料，复查items/receipts均空；原00002草稿未动。 |
| ④ | 实际对账0行、提示库存与账面金额无差异，截图SL008-reconciliation.png；有差异由Node委托契约覆盖。 |
| ⑤ | 质检context实测来料检验/出货检验/过程检验，无context电话仍呼入/呼出。 |
| ⑥／HT-009 | 28张已提交临时质检驱动SPC：六列中文，摘要子组26、读数106、剔除0、判异12，prepared_report=0。截图SL008-spc-populated.png。当前未复现R2英文，历史会话/缓存原因无证据，不能归因为缓存；未改SPC算法。 |
| ⑦ | Node契约覆盖已创建/已跳过/问题及空段“无”。 |
| ⑧⑨ | 列表employee_name、明细三类来源中文，截图SL008-piece-rate-list.png、SL008-piece-rate-sources.png。展示夹具mock collect_rows不作为工资计算证据；零数量由Python覆盖。 |
| ⑩ | test_capacity_load覆盖周三/月15日首桶，其余桶保持。 |

最终门：Python459/459（2422.628秒）、旧类5/5（0.257秒）、未分类4/4（0.005秒），退出0；Node115/115（219.087毫秒）；Ruff check/format182文件及译名自检通过。全量后未改app实现。夹具清理cleaned=40、remaining=[]，manifest已删除。JSON在frappe-bench/logs，截图/脚本在Spike/P1S8R6-D。

CRM无context撞名覆盖影响面：New→新线索（公共“新建”类文字）、Converted→已转化（其它转换状态）、Qualified→合格、Unqualified→不合格（其它资格/质量状态）、Qualification→需求确认（其它资质文字）。CRM调用无context，按方案覆盖并逐条登记translation_overrides.py。无新增工程约定，前端包装已登记README；HT-009历史原因无法追溯如实作为复核限制。

## TS-008 验证证据与既有用例调整

- 库存红绿证据：`s8-replenishment-stock-red.log`／`s8-replenishment-stock-green.log`，真实库存 3/3；90 天需求仅 6 次原料发料，总量 126；手算安全库存 25.682311、再订货点 35.482311；skip_transfer 的原料完工扣料计入，无补货行时仅非 WIP 仓计入。明细契约 `s8-replenishment-details-green4.log` 5/5。
- 首次全量唯一失败是旧 mock 未为新增旧建议量读取提供返回值；补足 mock 后该模块 4/4。随后 `s8-ts008-full-final.log` 集成 457/457（2371.217 秒）、旧类 5/5（0.271 秒）、未分类 4/4（0.005 秒），退出 0。此全量发生在最后两处 UI 修正之前；最终版本另跑 `s8-ts008-full-final2.log`，已完成457/457（2345.409秒）、旧类5/5、未分类4/4，退出0。
- 真实浏览器发现列表首列仍为 name；补 `title_field=item_code` 后，`replenishment_result_ui.cjs` 断言首列 item_code、item_name 另列。公司级单表契约 `s8-ts008-company-table-red.log` 3 条中 1 失败（3 张而非 1 张），修正后 `s8-ts008-result-contract-final.log` 3/3。
- `s8-ts008-browser.json` 是真实列表按钮→日期对话框→实际 run_now 响应：一家公司一张表，安全库存 2→0、再订货点 5→0；包含站点原有 17 张按订单建议的未变化明细。它不是手工注入 HTML。列表／实际弹窗截图为 `SL007-suggestion-list.png`、`SL007-calculation-actual.png`；旧的 `SL007-calculation-changes/noChanges/problems.png` 仅为代表性 HTML 探针，不能充当实际渲染验收。
- `replenishment_columns_ui.cjs` 在测试站未保存新表单验证 basis/value/note 与 sales_order/item_code/pending_qty 三列；23 依据选项全中文，截图 `SL007-suggestion-details.png`。临时物料 `_FCT SL007 UI 8b69d2a` 及该物料建议已删、公司开关恢复 0，临时清理模块已移除；未删除站点原有建议。
- 测试站最终迁移 `s8-ts008-migrate-final.log` 在 orphan 阶段长等待后自然退出 0，覆盖自检通过；未重启容器、未操作演示站。最终 Node 109/109（222.5824 毫秒），结果契约 3/3（95.5004 毫秒）；Ruff check 与 format check 181 文件、diff check 通过。UI 修正后译名 20/20（11.296 秒）、质量 13/13（0.183 秒）、translation_check 自检通过、debug 1/1（0.054 秒）。

| 既有用例 | 调整 | 原因与保留断言 |
|---|---|---|
| test_replenishment_levels 的日需求与安全库存用例 | 为 WIP 集合增加独立 mock；按 DocType 区分 Item／Item Reorder 的返回 | 新仓库查询不能复用旧的字符串 Item 列表；原需求总量、窗口、写值、跨公司保护断言保留，另断言完整 SQL 参数序列 |
| test_replenishment_daily.test_order_is_fixed_and_same_day_upsert_is_idempotent | 三规则与 upsert mock 接受 changes 参数 | 新明细列表是追加参数；原调用顺序及幂等断言保留 |
| test_replenishment_integration.test_run_daily_writes_eoq_and_periodic_suggestions_with_basis | Projected Qty → Replenishment Projected Qty | 按方案 A16 避免覆盖原生译名，Select 存值与写入同步；EOQ 手算与实际建议断言保留 |
| test_replenishment_suggestion.test_pending_suggestion_is_updated_and_completed_one_is_not_reused | db.get_value 返回由 [RS-1, None] 改为 [RS-1, 5, None] | 新读取旧建议量供 changes 比较；另断言更新 suggested_qty=9，不改变复用待定、完成后新建的期望 |

## TS-007 既有用例期望变动

| 用例 | 旧期望 | 新期望 | 依据与复验 |
|---|---|---|---|
| `test_bom_selection.TestBomSelection.test_work_order_preserves_manual_bom_and_comments` | 评论含「手动指定」 | 评论含「人工指定」 | SL-006②明定人工指定，④要求同步 S7 旧断言；仍保留 BOM-MANUAL、不自动替换且列出 BOM-CHEAP 两项断言。首次全量唯一失败后修正，模块 8/8（2.503 秒） |

TS-007 首次全量：449 条，2407.397 秒，唯一失败为旧措辞断言；旧类 5/5（0.285 秒）、未分类 4/4（0.005 秒），退出 1。改为验收明确的「人工指定」后，模块 8/8 且切片全量重跑 `frappe-bench/logs/s8-ts007-full-final.log` 通过：449/449、5/5、4/4。随后 Node 109/109、debug 1/1、`translation_check.run` 通过。

## TS-006 既有用例期望变动

`test_job_card_split.py` 的夹具 BOM quantity=1、工序 time_in_mins=40、WO qty=10000，工序 batch_size=100 只管批量，不再作时间分母（A16）。先实跑旧期望，9 条测试中出现四个失败断言（同一参数化测试三处＋端点一处），再按验收公式更新：

| 用例／拆分 | 旧分钟 | 新分钟 | 理由 |
|---|---|---|---|
| `test_work_order_submit_uses_bom_split_quantity_and_preserves_job_card_time`，split=0 | 4000 | 400000 | 40 × 10000 ÷ 1 |
| 同用例，split=2500 | 每卡 1000 | 每卡 100000 | 40 × 2500 ÷ 1 |
| 同用例，split=3000 | 1200／1200／1200／400 | 120000／120000／120000／40000 | 各卡 40 × 本卡数量 ÷ 1 |
| `test_make_job_card_endpoint_uses_the_same_bom_split_quantity` | 每卡 1000 | 每卡 100000 | 与自动建卡同口径 |

未勾批量的单卡原期望 400000 不变；拆卡数量、batch_size、原生函数哈希与映射断言不变。`test_capacity_load.py` 为报表专用数据行，暂无期望变更。
| SL-005 BOM 列现状 | `Spike/P1S8R6-D/operation_time_ui.cjs` 已断言 `frappe.boot.sitename=test.localhost`，新建未保存 BOM 截图 `SL005-bom-operation-columns.png` 实证工序／工站／工序时间／工序损耗率四列默认可见；原生前三列 `in_list_view=1`，不重复添加 Property Setter。截图尚未涉及工时实现 |

## TS-005 税种与模板改名映射

以下九项同时用于 Tax Category、十二个销售／采购模板 title 及十三条 Tax Rule 引用；模板 name 附 ` - {公司缩写}`。正式补丁尚未 migrate 到演示站；测试站仅以测试事务验证。

| 旧名 | 新名 |
|---|---|
| P13专票含税 | 13% 专票 含税价 |
| P13专票未税 | 13% 专票 不含税价 |
| P9专票含税 | 9% 专票 含税价 |
| P6专票含税 | 6% 专票 含税价 |
| P3专票含税 | 3% 专票 含税价 |
| P3专票未税 | 3% 专票 不含税价 |
| P1专票含税 | 1% 专票 含税价 |
| P1专票未税 | 1% 专票 不含税价 |
| P0无税 | 0% 无税 |

## 方案要求的验证

| 任务 | 验证方式（方案原文） | 怎么跑的 | 实测结果 |
|---|---|---|---|
| TS-001 | SL-001 ①②④ 贴命令输出；③ 单测 test_install.py 加两条；记两套测试用例数基线 | `Spike/P1S8R6-D/install_cache_probe.py`；测试站 `check_app_order`、`frappe_debug.tests.test_smoke`；after_commit 定向测试 | 安装后 `check_app_order` 返回 `ok: true`；冒烟 1/1 通过；提交后清缓存／回滚不清缓存均通过。验收 grep 的测试源码额外命中已记偏离 |
| TS-002 | SL-002 ①～⑥；迁移测试二次运行无改动；账务单据 GL 与提示 | `test_company`、`test_s8_accounting`（test.localhost） | 新公司 `410199`、四种银行方式 `1002`；迁移补缺不覆盖自定义值、非中式不动且重复运行通过；付款默认函数返回 `1002`；完工凭证只含 `1405`／`1409`／`410199`，无 Income／Expense 行，`400101` 无余额，保存无 COGS 提示；通过 |
| TS-003 | `test_process_loss.py`：六个数量各存两次、手填保持、非整数单位精度 | 测试站 `test_process_loss`；Node `test_bom_loss.cjs` | 8/8 集成中的损耗 5 条通过；1000→4.9、1500→4.8、300→4、2500→4.92、1234/7→0；kg 为 4.9303；全零与未填落库后整体手填 5 保持。前端全零可编辑、混合非零只读与清零恢复均通过 |
| TS-004 | SL-003 ②③⑤ 计划；④ 超产与哈希守卫；⑥ 按订单补货；⑤ 前端截图 | `test_process_loss`、`test_overproduction`、`test_replenishment_rules`；`Spike/P1S8R6-D/quantity_ui.cjs` | 5264／5261；手改 5300 保留；换 BOM 重算、需求 6000→6316、合并来源通过；计划建 5264 工单提交成功、第二张 1 被拦、5265 与 5000+265 被拦；原生源码哈希守卫通过；原料 45.69152 kg、来源未交 5000；截图显示「推荐 5264」 |
| TS-005 | SL-004 ① CRM 建客户与订单重取税模板；② 九税种十二模板改名；③ grep 与全量 | `test_customer_tax`、`test_s8_tax_migration`；源码 `rg` 旧名仅命中补丁映射；`s8-ts005-full.log` | 客户 4/4、改名最新 2/2，切片全量 431＋5＋4 全过；十二模板与十三规则非名称字段经独立 JSON 比对未变 |
| TS-006 | SL-005 ①三路径②③开关产能④负荷⑤固定与多级范围⑥列截图 | 先 HT-007 回滚探针，再 `test_operation_time` 红绿与 `test_job_card_split`／`test_capacity_load`／`test_operation_flow`；截图脚本 `operation_time_ui.cjs` | 新验收 10/10、相邻 9＋2＋16 全过；四列默认可见；切片全量集成 441/441、旧类 5/5、未分类 4/4；Node 92/92；debug 1/1；译名自检通过 |
| TS-007 | SL-006 ①浏览器保留后换用；②五类来源；③来源有值不改；④旧断言按新口径更新 | `test_bom_confirmation`、`test_bom_selection_hooks`、Node 专项及全量；`bom_confirmation_ui.cjs`；切片全量 | 来源 6/6、路径 6/6、专项 17/17、Node 109/109；浏览器 kept→confirmed→不重询通过。首次全量唯一失败为旧评论措辞断言，按 SL-006②④ 更新后模块 8/8；重跑全量 449/449、5/5、4/4 全过 |
| TS-008 | SL-007 补货需求、库存范围、说明与实际建议写入 | `test_replenishment_levels`、`test_replenishment_rules`、`test_replenishment_daily`、`test_replenishment_integration`、`test_replenishment_s8_stock`、`test_replenishment_s8_details`；Node 结果表格；Ruff | 旧模块 9/9、6/6、5/5、5/5；新真实库存 3/3、明细契约 5/5；Node 109/109、表格契约 3/3；Ruff check 与 format check 181 文件通过。最终全量 457/457＋5/5＋4/4，退出 0；译名 20/20、质量 13/13、自检、debug 1/1 通过 |
| TS-009 | SL-008演示画面译名与显示 | Python/Node、译名门、三个浏览器验收脚本 | 全量459/459＋5/5＋4/4、Node115/115；CRM下拉/看板、真实提交、精度、计件姓名/来源、有数据SPC及对账通过；见实测证据节 |
| TS-010 | SL-009①～④手算、缺料、日期校验及中文图表 | test_strategy_comparison、strategy_sidebar_ui.cjs及全量 | 定向6/6；三段四项指标与独立手算一致，缺料三工单只计1；截图经人工核对，prepared_report=0；切片全量465/465＋6/6＋4/4通过 |
| TS-011 | SL-009⑤15入口逐一可开、⑥报价页业务侧栏 | test_business_flow_navigation、strategy_sidebar_ui.cjs | 静态6/6、逐入口15/15，HT-011成立；用户批准的15项全部补齐，方案14为计数笔误 |
| TS-012 | SL-010原生性别/称呼、批号开关、管理员显示及第二次无改动 | Git Bash执行docker/configure-apps.sh两次，显式site=test.localhost与原CRM公司_FCT CRM 验证；demo_prerequisites_probe.py、demo_prerequisites_ui.cjs | 首次仅改批号0→1及默认姓名；第二次无改动，两次退出0。Gender7条、Salutation9条，存值英文；真实员工下拉7项中文；批号1，姓名与会话/侧栏均为演示管理员。SL-010全量待终态 |

## 偏离与暂停

- SL-003／TS-003 原“全部为空”无法在 Frappe Percent 落库后区分空值与零；用户在 [D 讨论记录第 2 步](P1-S8-R6-D讨论记录.md) 批准补充为“全零视为未启用，任一非零才自动算”，无需新增字段；后端 `overall_loss_percentage` 与前端只读判据同步修正，不改 5264／5261 验收值。
- 全量发现 S6 科目表字节守卫未随 R5 TS-002 的 `400101.account_type` 清空同步。已从原始 blob `474cd1c` 验证差异：只有批准的类型调整及多余末尾 CRLF；去掉多余 CRLF，以原始 blob 单处替换计算新 SHA256 `b6890ab453742273e338efee2cb1a4559dfff8224ba0b8a47b6455e3d9c841e2`，守卫按批准的变化更新，未对现文件盲取哈希放行。
- TS-005 映射表未在首轮迁移测试前写入回执，属于执行顺序缺口；现已补齐全表。后续不以此补录声称满足“先贴表”的时序要求。
- TS-007 方案内部口径冲突：SL-006① 同一计划「先保留、再次保存再换用」无法由前端只处理空 source 的伪代码完成。用户已在 D 讨论第 4 步批准 A：kept 且推荐不同则重询，confirmed／manual 不重询。按此补充实现判据，保留原验收；TS-006 回归继续。
- TS-008／A11 的默认在制品仓字段按用户批准改从 `Company.default_wip_warehouse` 读取（D 讨论第 6 步），与该公司已提交工单仓取并集；当前 v16 的 Manufacturing Settings 已无旧字段。SQL 仅在 Stock Entry 分支排除 WIP，发货单与销售发票分支不变。
- TS-008 的依据项 `Projected Qty` 与官方公共词条碰撞，按方案既定的独立源词办法使用 Select 存值 `Replenishment Projected Qty`，译为「补货预计可用量」，`rules.py` 写入处和测试同步。其余 22 项沿用原存值；碰撞清单探针见 `Spike/P1S8R6-D/replenishment_translation_probe.py`。未覆盖原生公共译名。
- TS-008 列表仅将 item_code 设为 in_list_view 仍不能替代 Frappe 默认 name 首列，真实浏览器验证后补 title_field=item_code；结果表改为汇总同公司所有步骤的一张表，遵循方案原要求。
- TS-009：真实页面显示的 CRM 状态列名绕过 CRM `__()`；用户批准在 `independent_app_labels.js` 限定看板标题区域翻译已知状态，底层状态存值不改（讨论记录第 7 步）。原生 `success_action` 在 `extend_bootinfo` hook 执行后才由 `frappe.boot` 写入，后端 hook 无法改到真实对象；改在 `desk_patches.js` 包装 `SuccessAction.show_alert`，只翻译与默认原生句完全匹配的提示，用户自定义消息和英文会话不变。已实际提交临时Purchase Receipt并见中文提示，随后取消删除及核查清理。
- TS-009单价：Operation与BOM工序保存重读均为0.004，表单显示0.0040，符合HT-010明定的precision=4、界面四位要求。此前将尾零列为阻塞是验收解读错误，现纠正，不增加格式补丁。
- 概况原预设执行者 Claude，本次按用户“继续开发项目”由 Codex 接续。
- 全量 Python 基线启动后才确认运行时间超过预期，且后续编辑导致它不再是干净基线；已在约 33 个测试处中止。仅以定向测试验证改动。
- 验收 grep 会命中 `test_install.py` 的装序测试中预期值；保留可读的测试断言，因此相比方案声称的「只命中 install.py 与 README」有测试源码额外命中。
- TS-003 开发期间测试站 migrate 与 web 进程进入不可中断的 Docker `p9_client_rpc` 文件系统等待，超 6 分钟未退出；未重启容器，以免影响现有站点状态。该环境阻塞不代表 TS-003 测试通过。

## 新增约定

| 约定 | 类别 | 在哪个任务确立 |
|---|---|---|
| frappe_debug 普通包 builders／scenario／demo，注册模块目录装 DocType／Page，配置在 data；依赖单向指向 frappe_china | 位置／跨层调用 | TS-001（方案 A1） |

TS-004 未另定工程约定：后端替换沿用 A15 三入口幂等安装，已登记 README、ADR-0004 与哈希守卫；前端推荐描述用 `doctype_js` 追加事件和当前行 `set_field_property`，不替换原生类或方法，故不作前端覆盖登记。

TS-006 无新增工程约定：工时与排程均用既有 doc_events 生命周期追加；不替换原生方法、不更改 BOM 工时／batch_size 的含义，不需新增前后端覆盖登记。

TS-007 无新增工程约定：确认弹窗与来源标记为 doctype_js／doc_events 追加，不替换原生类或方法；沿用现有 Select 存值与翻译纪律。

TS-008 无新增工程约定：沿用已有补货模块、frappe.local 请求内缓存和 Select 独立源词约定；列表脚本追加结果展示，不替换上游类或方法，无需新增覆盖登记。

## 未做项

| 项 | 为什么没做 |
|---|---|
| apps.json 版本锁（已补齐） | 用户2026-10-22授权中途提交推送；`frappe_china`已推送`ee153b4591ce80419290a39ec430a0c99c0381a3`，`frappe_debug`已推送`e2843633210688417b73303e3ee4cd50ee1865d4`，本次主仓库检查点同步锁定两者。 |
| TS-010整年性能计时 | 按方案待TS-017的s8dev一年场景就绪后补验；当前小数据查询数不按天增长、报表运行约0.013秒，不替代整年性能证据 |

## 状态值

执行中，尚未满足“代码已落地”。TS-001～012已完成；SL-010全量465/465＋6/6＋4/4、Node115/115及译名门通过，TS-012真实配置入口、界面验收和切片全量已完成。下一步TS-013场景参数文件与加载校验；整年性能待TS-017的s8dev数据就绪。

## 复核建议

本步进行中。TS-006 已完成指定门。复核建议：`operation_time.work_order_operation_time` 的固定行仍计入出现次数、其它 BOM 不计入；`job_card_scheduled_time` 保留休息间隔，只截短末行并同步止时。SL-005 多级范围目前用模拟行覆盖，尚无真实多级 BOM 树的新增验收。TS-004 可核 `production_plan_planned_qty` 的人改判据／合并来源与 `overproduction` 原生聚合契约；TS-005 可核新名存在时跳过、中式公司模板范围。TS-007 前后端确认边界可核 production_plan.js／work_order.js；来源与真实建单路径各 6/6，浏览器同一计划 kept→confirmed→第三次保存无弹框；全量 449/449、旧类 5/5、未分类 4/4 已过。TS-008 可核 `demand.daily_demand` 的 WIP 排除只位于 Stock Entry 分支、逐物料 reorder 仓集合与 title_field 的必要性；真实浏览器覆盖安全库存／再订货点变更、既有建议 unchanged、两子表默认列与 23 项中文，其他 outcome 由契约测试覆盖。TS-009重点核SuccessAction默认句精确匹配、英文/自定义委托与CRM看板DOM范围。HT-009当前未复现历史英文，根因不能追溯，未改SPC算法。


## TS-010／011 续做证据

- TS-010先跑红6条均为缺模块，1.451秒；实现后测试站6/6，14.334秒。真实单据：4笔库存收发、3张提交采购订单（每单两行验证distinct），另外草稿及无关物料订单排除；缺料三工单只计1。日期段1/4、倒置、首尾同日重叠、缺日期报错，默认三规则并集、缺参数总成本为空且提示。取消SLE不计，10天与365天查询数相同且不超过2。
- 浏览器SL009-strategy-comparison.png：八列中文、三段数据及实际SVG柱图，prepared_report=0；报价页SL009-quotation-business-flow.png，sidebar_title实测Business Flow，HT-011成立，无需fallback。
- TS-011先红：侧栏缺15项、报表未注册两个失败；json及测试站迁移后静态6/6。方案14为计数笔误，用户第9步批准按15项补齐，总入口66；其余7节及已有51项保持。
- 首次译名门20条中2失败：SPC Chart缺译及一个公司不存在公共词条未登记。新增SPC Chart独立源词；公司不存在直接沿用官方译文，删除重复CSV覆盖，不为过门制造覆盖依据。后续复验为准。
- 最终定向复验：39/39集成（策略6＋译名20＋质量13）、导航旧类6/6、debug1/1，日志s8-sl009-targeted-verified.log，退出0；translation_check.run输出“译名自检通过”，退出0。前一轮所有测试虽OK但进程退出1，Spike聚合脚本改以整数退出码并打印各套件成功标志后复验已消除该矛盾，未修改官方runner。
- 测试站migrate曾停在p9_client_rpc文件系统等待，后自然完成退出0，override self-check passed；未重启容器。15项入口真实点击证据logs/s8-strategy-sidebar-ui.json，Single设置按完整实际路由验证。
- 视觉复核发现最初报表截图仍停首页，不能作证。脚本改为直接导航目标页，断言中文页标题、可见SVG及表头并等待渲染，再重跑退出0；SL009-strategy-comparison.png现已人工查看，八列中文、三柱及三行手算数据同时可见。报价侧栏截图亦已人工核对。
- 临时夹具8项全部取消删除，remaining=[]；原生同步重估后清理本夹具唯一物料的4条重估记录及8条已取消SLE，GL为0；Company两项成本参数由20/20恢复0/0，manifest删除。证据logs/s8-strategy-ui-cleanup.json。清理按manifest单据和唯一物料正向限定，无force删除或全站流水清理。
- SL-009标准全量命令已启动：bench --site test.localhost run-tests --app frappe_china，日志s8-sl009-full.log；运行期间app源码冻结，不以启动成功替代通过。
- SL-009标准全量已取得终态：集成465/465，2447.546秒；旧类6/6，0.301秒；未分类4/4，0.005秒；进程退出0（s8-sl009-full.exit）。相较SL-008的459＋5＋4，仅新增策略6条及导航1条，无删减。Node115/115，259.556毫秒；两个自有app Ruff lint与format检查193文件通过。TS-010/011无新增工程约定，沿用Script Report及侧栏数据层；未增加上游覆盖。

## TS-012 续做证据

- 三条ATDD先红：均为configure_demo_prerequisites缺失；实现后3/3，增加main调用次序与同一Stock Settings字段回执合并检查后4/4（0.839秒）。脚本沿用原生update_genders/update_salutations及_apply，不覆盖管理员自定义姓名；无新增工程约定。
- 经Git Bash实际调用docker/configure-apps.sh --site test.localhost --company '_FCT CRM 验证'两次（保留测试站原CRM公司，站内两家中式公司故显式指定）。首轮输出批号开关0→1、Administrator→演示管理员；第二轮输出“无改动”。两次均退出0，日志s8-ts012-config-first.log、s8-ts012-config-second.log；未调用演示站。
- 只读查询s8-demo-prerequisites-data.json：Gender7、Salutation9，批号1，User.first_name/full_name均为演示管理员；英文原始记录名保持。真实员工性别下拉七项全中文；用户表单、会话姓名及侧栏可见演示管理员，截图SL010-employee-gender.png、SL010-batch-setting.png、SL010-administrator-name.png。首轮浏览器脚本错误读取boot.user.full_name为undefined，已按原生侧栏真实读取端改为frappe.session.user_fullname，重跑退出0，未改产品实现。
- SL-010标准全量已完成：集成465/465（2434.073秒）、旧类6/6（0.312秒）、未分类4/4（0.004秒），退出码0；日志s8-sl010-full.log与s8-sl010-full.exit。运行期间app源码冻结。
