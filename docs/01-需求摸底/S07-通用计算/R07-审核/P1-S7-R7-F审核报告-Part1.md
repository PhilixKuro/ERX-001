# 审核报告·Part1（对象：P1-S7 通用计算代码，`frappe_china` `68233b9..acf97e6` 中本片范围 / 审核标准：R03 需求文档 §4.1～4.6、§4.10、§4.12、§4.13、§4.18、§八 AC）

**轮次**：P1-S7-R7 F 片1（`plannedDev` audit 步）｜**日期**：2026-10-16｜**执行者**：Claude（Opus 5.5），独立子 Agent，未参与 C／D／E
**要求层**：[开发方案总纲](../R04-开发方案/P1-S7-R4-C开发方案-总纲.md)（A1～A17、§四偏离、§五契约、§六 HT、§十纪律）＋[Part1](../R04-开发方案/P1-S7-R4-C开发方案-Part1.md)（TS-001～009、SL-001～005）
**意图层**：[R03 需求文档](../R03-需求文档/P1-S7-R3-B需求文档.md)
**线索（不当结论）**：[D 回执 Part1](../R05-代码/P1-S7-R5-D回执-Part1.md)、[E 确认报告](../R06-确认/P1-S7-R6-E确认报告.md)
**探针**：`Spike/P1S7R7-F/p1/`（脚本与输出同目录）。全部在 `test.localhost` 事务内跑、结束 `rollback`，残留核为 0；未触发 `log_error`；`erx.localhost` 未碰。

## 覆盖自证

**实际查了**：
- 依据：总纲全文、Part1 全文、需求 §4.1～4.6、§4.10、§4.12、§4.13、§4.17、§4.18、§八 AC-001～011／020～022；`docs/开发守则.md`（判据能区分、静默失败、探针三条纪律、改 app 级 json 调大 `modified`、§13 跨 Phase 契约表）、`docs/业务规则.md`。
- 代码（逐行读）：`replenishment/` 全部 9 个文件；`production/bom_selection.py`；`install.py` 的 S7 改动（`override_targets`、`_alert_recipients`、`after_migrate`、`order_ok` 判据）；`hooks.py` 中 `doctype_js`／`doctype_list_js`／`scheduler_events`／`after_migrate`／`doc_events`（Item、Work Order 选 BOM、Production Plan）／`fixtures` 过滤清单；`stock_plus/` 三个 DocType 的 json 与 py；`public/js/replenishment_suggestion*.js`、`work_order.js`；`fixtures/custom_field.json` 中 Company／Item／MR 共 18 条本片字段；`zh.csv` 本 Round 全部新增行（按本片源词逐条核）；`modules.txt`、两个侧栏 json；`.pre-commit-config.yaml`、`pyproject.toml`；主仓库 `docker/scripts/setup.sh` 6.1／6.2 段、`check_business_order.py`、`configure_apps.py:configure_stock`；测试 `test_after_migrate`、`test_install`（S7 相关段）、`test_bom_selection`、`test_replenishment_{params,levels,stock,rules,suggestion,daily,integration}`。
- 上游对照（锁定 erpnext `12cd563f`）：`production_plan.py:1441-1497,1655-1666,1687-1718,1745-1950`、`bom.py:466-479,992-1166`、`bin.py:78-88`、`work_order.py:2532-2582`、`get_item_details.py:1823-1837`、`reorder_item.py:40-70`、`sales_order.py:2085-2125`；frappe `migrate.py:200-203`、`utils/error.py:44-100`、`error_log.py:30-36`、`utils/fixtures.py`。
- Ruff 基线 `39b2cec`：`git show --stat`（64 文件＝63 `.py`＋`pyproject.toml`）；自写 AST 比对脚本 `ast_cmp.py`（排序 import 后比对 64 文件），7 个文件 AST 不同，逐个看 diff，全是 import 拆分、`zip(..., strict=False)`、`pairwise`、`_rows` 改名这四类等价修正。
- 门：容器内 `ruff check`／`format --check`、Node 全量、三个 js 的 `node --check` 自跑。
- 探针 6 个（见各发现）。

**跳过及原因**：
- **Python 全量 `run-tests` 未跑**：主会话正在 test.localhost 跑全量，按调度指示不跑、不 migrate、不清缓存。验证门 Python 一项沿用 E 的 349/349，不作本片实测值。
- SL-002 ① 的真实 migrate 挪位未重跑（同上，且 E 已实跑过）；只读码核 `after_migrate` 三处告警与吞异常。
- 前端提示与表单按钮未在浏览器实点，只读 js 与 `node --check`。
- `production/` 下除 `bom_selection.py` 外的文件、`production_plus/`、Part2／3 的 hooks 条目归片 2／3，只在交接摘要登记共享状态。

## 验证门实跑结果

| 门 | 声称值 | 实测值 | 与基线对比 | 一致否 |
|---|---|---|---|---|
| Ruff check（容器 `env/bin/ruff` 0.14.10，`acf97e6`） | E：全过 | `All checks passed!`（`ruff.out`） | 基线 0 保持 | ✅ |
| Ruff format --check | E：161 文件 | `161 files already formatted` | — | ✅ |
| Node `node --test frappe_china/tests/*.cjs` | E：89/89 | 89 pass／0 fail／0 skip（`f1_bom_rate_and_node.log`） | 基线 86 → 89 | ✅ |
| 本片三个 js `node --check` | D：通过 | 三个均 ok | — | ✅ |
| Python 全量 | E：349/349 | **未跑**（见覆盖自证） | — | 未核 |
| 基线提交 `39b2cec` 只含格式与 lint | D／E：是 | stat 64 文件；AST 不同的 7 个均为等价修正（`ast_cmp.out`） | — | ✅ |

## 逐项落地核查

落地：✅完整／⚠️部分／❌缺失。生效：真被调用、未被绕过；根因：原问题真消失。

| 方案任务 | 要求层要求 | 定位（文件:行） | 落地 | 生效否 | 偏差说明 |
|---|---|---|---|---|---|
| TS-001 ① | `pyproject.toml` dev-dependencies 锁 `ruff==0.14.10`，与 pre-commit `rev` 同 | `pyproject.toml:20`；`.pre-commit-config.yaml:21` | ✅ | ✅ | — |
| TS-001 ① | `setup.sh` 装 ruff，版本读 `pyproject.toml`（tomllib） | 主仓库 `docker/scripts/setup.sh:378-391` | ✅ | ✅（D 摘段实跑） | — |
| TS-001 ③ | ignore 加 RUF001～003 各带注释 | `pyproject.toml:41-43` | ✅ | ✅ | — |
| TS-001 ④⑤ | `check --fix`、余项手修、行内 noqa 不扩大全局忽略；format | `39b2cec` | ✅ | ✅ | 无新增 noqa |
| TS-001 ⑦ | 独立一次提交，只含格式与 lint | `39b2cec` | ✅ | — | AST 比对确认 |
| TS-001 ⑧ | 开发守则工具链行 | `docs/开发守则.md:237` | ✅ | — | — |
| TS-002 | `modules.txt` 两行、两目录 | `modules.txt:2-3`；`stock_plus/`、`production_plus/` | ✅ | ✅ 探针 Module Def 两条、`app_name=frappe_china` | — |
| TS-002 | 两个空侧栏 json | `workspace_sidebar/stock_plus.json`、`production_plus.json` | ✅ | ✅ 探针 items＝0 | — |
| TS-002 | `replenishment/types.py` 放 §5.1 TypedDict | `replenishment/types.py:4-14` | ✅ | ✅ | — |
| TS-002 | 字段表 Company 7 条、Item 10 条、MR 1 条（本片） | `fixtures/custom_field.json` | ⚠️ | ⚠️ | Item `cn_service_level` 带 default 95（方案写「无 default」），见 **P1-04**；Company 节插入位置吞掉原生字段，见 **P1-05** |
| TS-002 | 字段名进 `hooks.py` fixtures 过滤清单 | `hooks.py:257-293` | ⚠️ | — | 缺 MR 那条，见 **P1-06** |
| TS-002 | 单测 `tests/test_s7_scaffold.py` | — | ❌ | — | 文件不存在，见 **P1-12** |
| TS-002 | label、Section 标题补 csv | `zh.csv` | ✅ | ✅ | — |
| TS-003 | `override_targets()` 读自身 hooks 模块 | `install.py:24-28` | ✅ | ✅ 4 条含 CRM（`hooks.py:249-255`） | — |
| TS-003 | 删 `WHITELIST_TARGETS` 常量，测试改用函数 | `install.py:31-32`；`tests/test_install.py:247-266` | ⚠️ | — | 常量保留为兼容别名，测试未改，见 **P1-10** |
| TS-003 | `after_migrate`：吞异常、打印、Error Log、通知、commit | `install.py:143-179` | ✅ | ✅（E 实跑 migrate） | 标题未进 csv，见 **P1-15** |
| TS-003 | `_alert_recipients`：启用 SM ＋ Administrator，去 Guest | `install.py:124-140` | ✅ | ✅ | — |
| TS-003 | `hooks.after_migrate` | `hooks.py:116` | ✅ | ✅ | 同列表前面挂了片 2 的 `ensure_component`，见交接摘要 |
| TS-003 | `check_business_order.py`（纯标准库、ast 解析） | 主仓库 `docker/scripts/check_business_order.py` | ✅ | ✅（E 实跑 0／1） | — |
| TS-003 | `setup.sh` 第 6 段 reorder 后调，非零即退 | `setup.sh:396-397`（`set -euo pipefail`，`:11`） | ✅ | ✅ | — |
| TS-003（方案外） | — | `install.py:58` `order_ok` 改为整序须等于 `target_app_order` | — | — | 夹带，见 **P1-11** |
| TS-004 | `get_item_params`，0 视为未填 | `replenishment/params.py:19-73` | ✅ | ✅ | 服务水平的回落被 P1-04 架空 |
| TS-004 | `sync_lead_time`，Item `on_update`，无记录不建 | `replenishment/lead_time.py:4-12`；`hooks.py:182` | ✅ | ✅ | — |
| TS-004 | `configure_stock` 置 `auto_indent`＝0，可重跑 | 主仓库 `configure_apps.py:223-235,422` | ✅ | ✅（D 两次实跑） | — |
| TS-004 | README 已知限制「物料上无法覆盖成 0」 | `README.md` 已知限制 | ✅ | — | — |
| TS-005 | `select_bom` 签名、过滤、排序（单位成本、原生默认、名称） | `production/bom_selection.py:102-125` | ✅ | ✅ | — |
| TS-005 | `_unit_cost`：工序 `hour_rate` **预置为工作中心价**再 `calculate_cost(False, False)` | `bom_selection.py:64-99` | ⚠️ | ❌ | 只在行上费率为 0 时才取工作中心价，提交过的 BOM 行恒非零，工作中心调价不影响选择，见 **P1-03** |
| TS-005 | 不调 `update_cost`／`save`／`db_update` | `bom_selection.py` 全文 | ✅ | ✅（E 实测 `modified` 不变；上游 `calculate_cost(save_updates=False)` 下各 `db_update` 均不触发，`bom.py:1062,1101,1119,1142`） | — |
| TS-005 | `_native_default`、`default_boms`、`recommend_bom` 权限 | `bom_selection.py:28-61,128-131` | ✅ | ✅ | `default_boms` 返回 list 而非 set，无影响 |
| TS-006 | `work_order_before_insert`／`after_insert` 评论 | `bom_selection.py:134-180`；`hooks.py:183-187` | ✅ | ✅（E 三路径实跑） | — |
| TS-006 | `production_plan_validate` | `bom_selection.py:183-192`；`hooks.py:195` | ✅ | ✅（E 实跑） | — |
| TS-006 | 前端：`bom_no` 变化且未保存时提示 | `public/js/work_order.js:1-28`；`hooks.py:47` | ✅ | 未实点 | — |
| TS-006 | 前端：**已保存工单 `refresh` 时同样提示一次** | — | ❌ | — | 见 **P1-13** |
| TS-006 | 单测 `tests/test_bom_selection_hooks.py`（三路径真单据） | — | ❌ | — | 仓库只有桩测试，见 **P1-12** |
| TS-007 | 白名单需求口径、90 天含 D−89（IT-003 修后） | `replenishment/demand.py:18-27,40-86` | ✅ | ✅ 集成测试 `test_replenishment_integration.py:38-57` | — |
| TS-007 | `mean_and_stdev` 样本标准差 | `demand.py:89-94` | ✅ | ✅ | — |
| TS-007 | `warehouses_of_row`（组 → 叶子仓） | `demand.py:97-110` | ✅ | ✅ 探针：原生把空组存成本仓（`f1_misc_probe.log`），`:101` 已处理 | — |
| TS-007 | `projected_qty` 取原生 `Bin.projected_qty` 之和（IT-002 修后） | `demand.py:113-126` | ✅ | ✅ | 构成项展示的副作用见 **P1-08** |
| TS-007 | `compute_safety_stock`、多公司跳过、提前期缺失写 0 | `replenishment/safety_stock.py:39-85` | ✅ | ✅ | problems 为英文，见 **P1-15** |
| TS-007 | `compute_reorder_levels`、提前期缺失不写本行 | `replenishment/reorder_level.py:22-61` | ✅ | ✅ | — |
| TS-008 | DocType 三张、字段、权限、列表色 | `stock_plus/doctype/*`；`replenishment_suggestion_list.js:1-14` | ✅ | ✅ | 状态源词用了官方已有的 `Pending`，见 **P1-07** |
| TS-008 | `eoq_proposals`／`periodic_proposals`（IT-001 修后） | `replenishment/rules.py:75-168` | ✅ | ✅ 集成测试 `:70-131` | — |
| TS-008 | `order_proposals`：仓库＝原生返回行仓库 | `rules.py:183-272` | ⚠️ | ❌ | 上游函数把首行仓库粘给后续全部原料，见 **P1-02** |
| TS-008 | `order_proposals`：MR 类型取 `default_material_request_type`，值域同 `Item Reorder` | `rules.py:253` | ⚠️ | ❌ | 未映射 `Material Transfer`／`Customer Provided`，建议单写不进，见 **P1-01** |
| TS-008 | 只留勾 `cn_rule_order` 的物料（IT-004 修后） | `rules.py:237-247` | ✅ | ✅ 集成测试 `:133-183` | — |
| TS-008 | `upsert` 去重、行锁读 | `replenishment/suggestion.py:6-32` | ✅ | ✅ | — |
| TS-008 | fixtures 过滤清单加 MR 字段 | `hooks.py` | ❌ | — | 见 **P1-06** |
| TS-009 | `run_daily` 次序、throw、不 commit、单物料隔离 | `replenishment/daily.py:15-65` | ✅ | ✅ | — |
| TS-009 | `run_now` 权限、commit | `daily.py:68-73` | ✅ | ✅（E 实测） | 无单测，见 **P1-12** |
| TS-009 | `scheduled_daily` 写 Error Log，标题＝固定文字 | `daily.py:76-81`；`hooks.py:54` | ⚠️ | ⚠️ | 参数位次反了，标题成了结果字典，见 **P1-09** |
| TS-009 | `adopt`／`ignore`／`bulk_action` | `replenishment_suggestion.py:14-86` | ✅ | ✅（E 实测） | — |
| TS-009 | 表单 js：采纳（可改量）、忽略 | `replenishment_suggestion.js:1-38` | ✅ | 未实点 | — |
| TS-009 | 表单 js：表头「立即计算」；`run_now` 结果**以对话框列出每公司三步条数与 problems** | `replenishment_suggestion_list.js:51-79` | ⚠️ | ❌ | 只在列表有按钮，回调只刷新列表、不展示结果，见 **P1-14** |
| TS-009 | 列表批量结果逐条 msgprint | `replenishment_suggestion_list.js:81-102` | ⚠️ | — | 只报失败项，计入 P1-14 |
| TS-009 | README 已知限制「MR 取消不回滚」 | `README.md` | ✅ | — | — |

**需求 AC（本片）**：AC-001～003、005、007～011、020、022 落地且有正向证据（E 实跑＋本片探针／读码）。AC-004「按订单抽一个物料手算一致」在单仓、`Purchase` 类型下成立，在 P1-01／P1-02 的条件下不成立。AC-006 成立（集成测试）。AC-021「表单出推荐提示」只在新建编辑时成立（P1-13）。

## 自证复核

| 被审产物声称 | 实际复核结果 | 一致否 |
|---|---|---|
| D TS-001：`39b2cec` 只含 63 个 `.py` 与 `pyproject.toml`，AST 归一后无其他差异 | stat 64 文件属实；本片独立 AST 比对 7 个文件不同，逐个看 diff 均为 import 拆分、`zip(strict=False)`、`pairwise`、`_rows` 四类，与 D 列举一致 | ✅ |
| D TS-002：「22 custom fields synchronized」 | fixtures 共 27 条（含 S4～S6 旧 4 条、MR 1 条、片 2 的 Batch／BOM Operation／Operation 等）；本片 18 条均在测试站 meta 中 | 数字口径不明，不另立项 |
| D TS-002 验证方式：`tests/test_s7_scaffold.py` 单测 | 文件不存在 | ❌（P1-12） |
| D TS-005/006：「test.localhost 真实验收覆盖四条路径」「8/8 定向测试」 | 仓库内 `test_bom_selection.py` 全用 `BomStub`／mock；E 用真 BOM 补了探针，但未留成测试；方案要求的 `test_bom_selection_hooks.py` 不存在 | ❌（P1-12） |
| E IT-001～004、006 修复 | 读码 `rules.py:37-73,237-247`、`demand.py:18-27,40-58,113-126`、`install.py:153-155`；集成测试 4 条不 mock，断言能区分修前修后（修前 `basis` 写不进、窗口合计 4、计划量 93、未勾物料出建议） | ✅ 修得对；修出的副作用见 P1-08 |
| E TS-005：「把原料估价调到 50 后改选 B2」证明「调价后选择改变」 | 只证明原料价会刷新；工价一侧未被覆盖，本片探针：工作中心费率 0→600，单位成本不变 | ⚠️（P1-03） |
| E：「`frappe_china override self-check failed` 只给管理员看，留 F 判」 | 不在 csv、不在官方词典；本片判为低（P1-15） | — |

## 问题清单

| # | 严重程度 | 定位 | 问题描述 | 违背的标准/意图 | 建议 | 建议档位 | 待裁决点 | 状态 | 用户裁决 |
|---|---|---|---|---|---|---|---|---|---|
| P1-01 | 中 | `replenishment/rules.py:253`；`replenishment_suggestion.json` `material_request_type` 选项 | 按订单规则把原生返回的 `material_request_type`（即 `Item.default_material_request_type`，取值 `Purchase/Material Transfer/Material Issue/Manufacture/Customer Provided`）原样写进建议单，而建议单该字段只有 `Purchase/Transfer/Material Issue/Manufacture`。默认请购类型为「调拨」或「客户提供」的原料，`upsert` 报 Select 校验错，该物料不出建议、只进 problems。探针 `f1_misc_probe.log`：`order_props [('Material Transfer', 6.0)]` → `upsert_fail ValidationError 物料需求类型不能为“Material Transfer”` | 方案 TS-008「`material_request_type` 取值域与 Item Reorder 一致」、偏离 14；需求 AC-004 | 在 `order_proposals` 把 `Material Transfer` 映射为 `Transfer`（与 `adopt` 的反向映射对称）；`Customer Provided` 无对应项，建议回落 `Purchase` 并在 basis 备注写原值；补一条用例 | 本Session修 | `Customer Provided` 回落 `Purchase`，还是给建议单加该选项（`adopt` 已能原样透传） | 待裁决 | |
| P1-02 | 中 | `rules.py:219-230` 调上游 `production_plan.py:1806,1903` | `for_warehouse=None` 时，上游循环里 `warehouse = warehouse or details.get("source_warehouse") or details.get("default_warehouse")` 改写的是外层变量，**第一种原料的默认仓会粘给其后所有原料**，净缺料也拿那个仓的 Bin 扣。探针 `f1_order_wh_probe.log`：原料 B 默认仓 `Work In Progress - _TC`，建议单仓库却是 `Stores - _TC` | 方案偏离 14「仓库＝原生函数返回的行仓库（物料默认仓库或物料组默认仓库）」——该前提在上游实现下不成立；需求 §4.2.1 仓库取供料仓 | 两种改法：① 每种成品／原料组合按物料默认仓分组、分别调一次原生函数；② 只用原生函数取展开量，仓库与 Bin 自己按物料默认仓重取再扣。演示数据若所有原料同一默认仓则不暴露，可写进已知限制 | 出方案修 | 取 ① ② 还是接受原生行为、写进 README 已知限制 | 待裁决 | |
| P1-03 | 中 | `production/bom_selection.py:68-74` | 方案 A10 要求「先把每道工序的 `hour_rate` **预置为工作中心 `hour_rate`**」再走 `update_hour_rate=False`；代码反过来，只在行上费率为 0 时才取工作中心价。提交过的 BOM 行费率恒非零（测试站 3／3 行非零），工作中心调价对选择**完全无效**。探针 `f1_hour_rate_probe.log`：工作中心 0→600，单位成本 12.25→12.25。E 的「调价后选择改变」只调了原料价，分辨不出这一点 | 方案 A10、TS-005 伪代码；需求 §4.10「工价取工作中心 `hour_rate`」 | 改为：有 workstation 取 Workstation 价，否则取 Workstation Type 价，两者都无才保留行值；补一条「只调工作中心费率、选择改变」的真 BOM 测试 | 本Session修 | — | 待裁决 | |
| P1-04 | 中 | `fixtures/custom_field.json:215-222`（`Item-cn_service_level` `"default": "95"`） | 方案字段表写明 Item 的 `cn_service_level`「无 default」。带了默认后，新建物料的服务水平一律是 95（探针：`new_doc` 得 95.0、列默认 `95.000000000`、测试站 2 个物料全为 95），`get_item_params` 永远取物料值，**公司默认服务水平对新物料从不生效** | 需求 §4.2.2「物料覆盖为空即取公司默认」；方案 TS-002 字段表 | 删掉该条 `default`、调大 `modified`，migrate 后核列默认已去掉；测试站／演示站已有物料的 95 按需清空（演示站业务数据为 0，无存量） | 本Session修 | 是否清空测试站已有物料上的 95 | 待裁决 | |
| P1-05 | 中 | `fixtures/custom_field.json:61`（`Company-cn_replenishment_section` `insert_after: default_currency`） | 节分隔插在原生「details」节中间，其后的原生字段 国家、是否集团、默认假日表、默认信头、税号、城建税率、域、成立日期、母公司、报表货币 全部被划进「补货参数」节。探针 `f1_meta_probe.log` 的 Company 段逐字段列出节归属 | 方案 TS-002「`insert_after` 由执行者按表单位置定」；演示屏单 | `insert_after` 改为 details 节末字段 `reporting_currency`（`company.json` 中其后即 `company_info` 节），调大 `modified`；浏览器看一眼公司表单 | 本Session修 | — | 待裁决 | |
| P1-06 | 低 | `hooks.py:257-293` | fixtures 过滤清单缺 `Material Request-cn_replenishment_suggestion`（json 里有、`hooks_fixture_has_mr => False`）。导入不受影响，但下次 `bench export-fixtures` 会把它从 json 里删掉，字段随之丢失 | 方案 TS-008「`hooks.py` fixtures：本任务加 TS-002 留下的 MR 字段」 | 清单补一行 | 本Session修 | — | 待裁决 | |
| P1-07 | 低 | `replenishment_suggestion.json` `status`／`rule` 选项 | 状态源词用了 `Pending`，官方 frappe／crm／insights 已译「待处理」，界面显示「待处理」而非需求的「待定」；规则 `Against Sales Order` 取到 erpnext 的「销售订单」，三条规则并列时显示为「经济订货量／定期复核／销售订单」 | 总纲 A16（官方译文不合用就换官方没有的源词，例子正是 `Pending`）；方案 TS-008 | 改源词（如 `Awaiting Decision`、`By Sales Order`）并进 csv；涉及 json、`suggestion.py`、`replenishment_suggestion.py`、两个 js、测试 | 新Session修 | 接受「待处理」「销售订单」，还是按 A16 改源词 | 待裁决 | |
| P1-08 | 低 | `rules.py:44-47,65-72`；`replenishment_basis_item.json` | IT-001 的修法把生产、委外、生产计划三项预留都映射到 `Reserved Qty`，而它的官方译文是「销售预留数量」：触发依据里会出现四行「销售预留数量」，区分只靠备注里的英文字段名。官方另有「生产预留数量」「委外预留数量」「生产计划预留数量」（探针 `tr` 段） | 需求 §4.2.1「足以让人手算复核」；A7「项目名走 Select 选项故可译」 | `basis` 选项补三项官方源词，`BASIS_OPTIONS` 一一对应，调大 json `modified` | 本Session修 | — | 待裁决 | |
| P1-09 | 低 | `replenishment/daily.py:80` | `frappe.log_error(str(result), "Daily …")` 位次反了：上游签名 `log_error(title, message)`（`frappe/utils/error.py:44`），且 `str(dict)` 不含换行、触发不了上游的互换启发式。Error Log 标题成了截断到 140 字的结果字典，固定标题落进正文；也没经 `_()` | 方案 TS-009 `log_error(title=_("Daily replenishment calculation has problems"), message=…)` | 改为关键字参数，标题经 `_()` 并进 csv | 本Session修 | — | 待裁决 | |
| P1-10 | 低 | `install.py:31-32`；`tests/test_install.py:247-266` | `WHITELIST_TARGETS` 未删，改成导入时求值的别名；测试仍用它。将来测试 patch `hooks` 后别名不跟着变，两处取值可分叉 | 方案 TS-003「常量删除；测试同步改为 `override_targets()`」 | 删别名，测试改调函数 | 本Session修 | — | 待裁决 | |
| P1-11 | 低 | `install.py:58`（`d39a6c5` 引入） | **方案外夹带**：`order_ok` 判据由「frappe_china 之后只许尾部 app」改成「整序须等于 `target_app_order`」，把业务 app 之间的相对顺序也纳入断言。方向与 `PH-P1073` 一致，但未经方案或用户裁决；失败提示文字仍是旧判据（「frappe_china 之后只能是 …」），业务 app 互换时提示与原因对不上 | 审法第 7 条；开发守则「判据必须能区分」 | 保留则补进方案偏离并改提示文字；或回退 | 本Session修 | 保留新判据还是回退 | 待裁决 | |
| P1-12 | 中 | `tests/`（缺 `test_s7_scaffold.py`、`test_bom_selection_hooks.py`）；`tests/test_bom_selection.py` 全为桩 | 方案点名的两个测试文件不存在。SL-001 ④（模块、侧栏、字段 meta）、SL-004 ①～⑥（三张真 BOM 手算、三条建单路径、评论、生产计划展开）、SL-005 ⑩（`run_now` 权限）在仓库里没有回归保护，现有证据只在 E 与本片的一次性探针里。P1-03 正是桩测试漏掉的 | 方案 TS-002／005／006／009「验证方式」；总纲纪律 5「手算值写成常量」 | 按方案补两个测试文件（E 的 `it-bom-probe` 可直接改写）＋ `run_now` 权限用例 | 新Session修 | — | 待裁决 | |
| P1-13 | 低 | `public/js/work_order.js:1-28` | 只有 `bom_no` 字段事件、且 `frm.is_new()` 才提示；方案要求的「已保存工单 `refresh` 时同样提示一次（取评论里的那次选择）」没做 | 方案 TS-006 前端提示；需求 AC-021 | 加 `refresh` 分支 | 本Session修 | — | 待裁决 | |
| P1-14 | 中 | `public/js/replenishment_suggestion_list.js:70-75`；`replenishment_suggestion.js` | 「立即计算」回调 `.then(() => listview.refresh())` 丢掉了返回的 `DailyResult`：参数缺失、提前期缺失、多公司出库等 problems 在界面上**一条都看不到**，没出建议时用户分不清是不触发还是出错（静默失败）。方案要求对话框列出每公司三步条数与 problems，且按钮在表单表头 | 方案 TS-009；需求 §4.12「返回…问题清单，供演示查看」；开发守则「静默失败」 | 回调里按公司列出三步 processed／skipped／problems；表单也挂按钮；批量结果按方案逐条列 | 本Session修 | — | 待裁决 | |
| P1-15 | 低 | `safety_stock.py:62,68,73`、`reorder_level.py:47`、`rules.py:89,130,249`、`daily.py:80`；`install.py:8` | problems 全是英文短语（`lead time missing` 等），方案 §5.1 写明「中文」；`ALERT_TITLE` 与每日告警标题既不在 csv 也不在官方词典（探针：`_()` 原样返回英文） | 总纲 §5.1 `StepResult.problems` 注释；A16 | problems 改为经 `_()` 的英文源词＋csv，或直接中文；两个标题进 csv | 本Session修 | — | 待裁决 | |

（严重程度：高=阻断/根因偏离 · 中=需修 · 低=技术债 · 观察=可容许偏差记录。下游引用时由收口报告统一换成 `FD-` 编号。）

## 集成检查

| 集成点类型 | 具体落点 | 两端一致否 | 说明 |
|---|---|---|---|
| 事件／消息 | 本片无 SSE／`publish_realtime`；`after_migrate` 打印、Error Log、Notification Log | ✅ | 三处告警的写端在 `install.py:157-179`，读端是 migrate 输出与 Desk 通知 |
| 接口契约 | 总纲 §5.1 `StepResult`／`DailyResult` | ✅ | `types.py` 与 `daily.py` 一致；`problems` 语言不符见 P1-15 |
| 接口契约 | 总纲 §5.2 `run_daily(as_of_date, company)` | ✅ | docstring 原样含四条约定；不 commit；未来日期 throw（`daily.py:27-28`）。README「按某日计算」节同文 |
| 接口契约 | 总纲 §5.2 `run_now`／`scheduled_daily` | ⚠️ | `run_now` 多一个 `company` 参数（向后兼容）；`scheduled_daily` 告警位次反（P1-09） |
| 接口契约 | 总纲 §5.3 `select_bom`／`default_boms`／`recommend_bom` | ⚠️ | `BomCandidate` 多 `is_default`、`note` 两键，`default_boms` 返回 list；调用方（`rules.py:192`、`bom_selection.py:138,187`、`work_order.js`）只用 `bom`／`auto`／`candidates[].unit_cost`，拼得上。工价口径偏离见 P1-03 |
| 接口契约 | 总纲 §5.4 `override_targets`／`after_migrate` | ✅ | — |
| 接口契约 | `docs/开发守则.md` §13 登记的跨 Phase 契约：「演示操控的事件协议」一条 | 不涉及 | 本片代码未发、未收 `erx_demo_step` |
| 共享状态 | `hooks.py`、`fixtures/custom_field.json`、`zh.csv` | ⚠️ | 见交接摘要；本片发现 P1-04／05／06 落在共享文件 |
| 跨模块数据流 | 选 BOM → 按订单展开（`rules.py:192-196` → 原生 `get_items_for_material_requests`） | ✅ | 同一 `select_bom`；E 已用原料集合佐证 |
| 跨模块数据流 | 安全库存 → 再订货点 → 规则（同一事务内读刚写的 `Item.safety_stock`） | ✅ | `reorder_level.py:52`、`rules.py:140` 都现读库值 |
| 跨模块数据流 | 建议单 → MR（`adopt`）→ MR 回指字段 | ✅ | `Transfer`→`Material Transfer` 映射在 `adopt`；反向（原生 → 建议单）缺失即 P1-01 |
| 跨模块数据流 | 按订单原料仓 ← 原生函数 | ❌ | P1-02 |

## 业务规则合规核

| 规则条款 | 本 Round 改动是否涉及 | 结论 | 备注 |
|---|---|---|---|
| BR-001 小企业会计准则 | 否 | 合规 | 本片不碰科目、报表 |
| BR-002 报表构成 | 否 | 合规 | — |
| BR-003 增值税税率 | 否 | 合规 | — |
| BR-004 未交增值税结转 | 否 | 合规 | — |
| BR-005 城建税与附加 | 否 | 合规 | `install.py` 的建账自检保持原样（`check_all_cn_companies` 随同一入口跑） |
| BR-006 资产负债表平衡 | 否 | 合规 | — |
| BR-007 价税分离 | 否 | 合规 | 采纳生成 MR 不带价 |
| 规则新增／变更检出 | 本片算法口径（EOQ、σ、Z、白名单需求、窗口含 D−89） | 非领域不变量 | 与需求 §4.17 判断一致：通用算法的口径选择，不进 `业务规则.md`，无送审项 |

## 跨片一致性（交接摘要）

**本片发出／消费的事件**：不发不收 realtime 事件。`after_migrate` 发 Error Log（标题 `frappe_china override self-check failed`）与 `Notification Log`（type `Alert`）；`scheduled_daily` 发 Error Log（标题见 P1-09）；各计算函数单物料异常发 Error Log（标题 `Safety stock calculation`、`Reorder level calculation`、`EOQ replenishment proposal`、`Periodic replenishment proposal`、`Sales order replenishment proposal`、`Sales order material calculation`、`Daily replenishment calculation`、`Daily replenishment proposals`、`Replenishment suggestion`）。

**本片暴露的接口**：
- `frappe_china.replenishment.daily.run_daily(as_of_date=None, company=None) -> DailyResult`（S8、片 3 TS-017 回放调用）；`run_now`（whitelisted，SM／Stock Manager）；`scheduled_daily`（scheduler daily）。
- `frappe_china.replenishment.types.StepResult`／`DailyResult`。
- `frappe_china.production.bom_selection.select_bom`／`default_boms`／`recommend_bom`／`work_order_before_insert`／`work_order_after_insert`／`production_plan_validate`。
- `frappe_china.install.override_targets`／`after_migrate`／`check_app_order`／`target_app_order`／`BUSINESS_APP_ORDER`（被 `docker/scripts/check_business_order.py` 以 ast 读取）。
- DocType `Replenishment Suggestion`（`status` 值 `Pending/Adopted/Ignored`，`rule` 值 `EOQ/Periodic Review/Against Sales Order`）、`Replenishment Basis Item`、`Replenishment Source Order`；Custom Field `Material Request-cn_replenishment_suggestion`。

**本片依赖的接口**：
- 片 2 `frappe_china.production.piece_rate.ensure_component`：挂在 `hooks.after_migrate` 列表**第一位**、早于本片 `install.after_migrate`，且不在本片的吞异常范围内。它抛错会中断 migrate、自检不跑（HT-002）。请片 2 核它是否自吞异常。`install.after_install`／`after_app_install` 也调它（`install.py:223,238`）。
- 片 2 `frappe_china.production.job_card_split.before_submit_work_order` 与本片 `work_order_before_insert` 同挂 Work Order `doc_events`（`hooks.py:183-187`），互不依赖。
- 上游 `get_items_for_material_requests`（erpnext `production_plan.py:1745`）的仓库与请购类型行为（P1-01、P1-02）。

**本片依赖的跨片共享状态**：
- `hooks.py`：`doctype_js` 中 Work Order／Replenishment Suggestion 归本片，Purchase Receipt／Stock Entry／Delivery Note 归片 2；`doc_events` Item、Work Order 的 before／after_insert、Production Plan 归本片，Job Card、三类单据 before_validate、Work Order before_submit 归片 2；`before_request`／`before_job` 归片 2；`scheduler_events` 只有本片一条；`after_migrate` 两条见上。
- `fixtures/custom_field.json` 与 `hooks.py` fixtures 清单：本片 18 条（Company 7、Item 10、MR 1）；Item `cn_unit_length_m`、`Batch-cn_linear_density`、BOM Operation 两条、`Operation-cn_piece_rate` 归片 2。清单缺 MR 一条（P1-06），请收口核片 2 的字段是否都在清单里。`Batch-cn_linear_density` 的 `modified` 已调大（`8da1fb0`）。
- `zh.csv`：本片新增约 45 行（补货参数、规则、建议单、选 BOM 评论、计算对话框文案）。本 Round 对 csv 还有 9 行「删一行再加回同文」（如 `Edit field`、`ends with`、`Mode of Payment`），是重排序，内容未变，请收口确认没有被当作改译。
- `.pre-commit-config.yaml` 排除 `public/js/vendor/`（`e1b5621`，片 3 echarts）。

## 总体判断

部分满足。补货与选 BOM 的主链（安全库存、再订货点、EOQ、定期复核、去重、采纳、自检、Ruff 基线）落地并生效，E 修的 IT-001～006 修得对，未见修出新的功能问题（只有 P1-08 的展示副作用）。关键缺口：按订单规则在原料默认请购类型非采购、或原料默认仓不同时出错或出错仓（P1-01、P1-02）；选 BOM 的工价一侧不随工作中心变（P1-03）；公司默认服务水平对新物料失效（P1-04）；公司表单节划分被打乱（P1-05）；计算结果在界面上不可见（P1-14）；方案点名的两份测试缺失（P1-12）。

## 复核建议

1. **定级在边界上的**：P1-01 与 P1-02 在「中／高」之间——演示数据若全是采购件、同一默认仓就不暴露，故定中；若演示要讲「调拨补货」或原料分仓，应升高。P1-14 在「中／低」之间——它不改数据，但让 problems 在演示时无处可见，按开发守则「静默失败」定中。P1-07 在「低／中」之间——「待定」显示成「待处理」不影响功能，但 A16 原文就拿 `Pending` 当反例。
2. **查得最浅的**：前端三个 js 只读码、没在浏览器实点；Python 全量未跑。查法：Desk 打开补货建议列表点「立即计算」与批量采纳；打开工单新建页改 BOM。
3. **没往哪找**：没核 `run_daily` 在多家启用公司时的组合行为（只读码）；没核 `upsert` 在并发（scheduler 与手动同时跑）下的重复；没核子装配（方案已列不做）；没交叉核 S4～S6 既有行为是否被 `install.py` 的 `order_ok` 新判据影响（只看了 `test_install.py` 的两个用例）。
4. **拿不准处**：P1-11 是否算「方案外夹带」——它出现在 TS-003 同一提交，可视为 TS-003「比对业务 app 顺序」的延伸；但方案只要求 `setup.sh` 比对，没要求改运行时自检。P1-02 是上游行为，算不算本 app 的问题取决于方案偏离 14 的前提是否当作承诺。

