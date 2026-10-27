# F 复核报告·片3（对象：R8 SB 修复 11 项＋用户裁决追加改动／审核标准：R08 F 审核报告各项判定标准与用户裁决、R05 开发方案、R04 需求文档）

**轮次**：P1-S8-R11（F 复核）片 3｜**日期**：2026-10-27｜**执行者**：Claude（Opus 5.5，片 3 子 Agent，未参与此前任何修复）｜**打tag**：否
**代码基线**：`frappe_debug` `3894c5a`（SB 起点 `1f9ba1c`）；`frappe_china` `f0ac818`（起点 `ffadacf`）；主仓库 `e20ea11` 的 `docker/` 改动。三处工作区与 HEAD 一致（`git status` 无改动）。
**依据**：F/SB/audit 三份规格；SB 修复回执全文；F 审核报告 11 项行与裁决列；片报告 Part1（P1-02）、Part2（P2-01～05）、Part3（P3-01、03、04、06、07）；P1-S8 概况 SH-P1S8021／022；需求 AC-019。

## 1. 覆盖自证

- **读全的代码（SB 差异全量）**：`frappe_debug` `git diff 1f9ba1c 3894c5a` 的全部非测试文件（`install.py`、`hooks.py`、`demo/progress.py`／`registry.py`／`switch.py`／`workspace.py`、`public/js/demo/runner.js`／`rehearsal.js`／`functions.js`、`scenario/day.py`／`masters.py`／`support.py`／`params.py`／`targets.py`／`monthly.py`／`quality.py`／`verify.py`／`rehearsal.py`／`runner.py`、`data/scenario.yaml`、`README.md` 差异）；`frappe_china` `git diff ffadacf f0ac818` 全部非测试文件与 `test_crm_status.py`；主仓库 `git show e20ea11 -- docker` 全部 7 个文件。另通读 `demo/snapshot.py`、`demo/switch.py`、`demo/registry.py`（1-200 行）、`demo/operation.py`、`transit.html`（34-130 行）、`docker/scripts/setup.sh` 第 3～6.2 段、`docker/lock-apps.sh` 写入段、`check_business_order.py`。
- **上游对照**：Frappe `desk/search.py:36-62,408-438`（`search_link`、`http_cache`、`build_for_autosuggest`）、`utils/caching.py:212-252`、`__init__.py` `override_whitelisted_method`／`get_attr`／`call`、`handler.py:65-86`、`installer.py:325-340`（`before_install` 调用点）、`installer.py:666-705`、`config.py` 全段、`utils/synchronization.py`；容器内 `filelock 3.20.4` 的 `_api.py`、`_unix.py`（`_acquire`／`_release`）；ERPNext `job_card.py:169-185,1368-1430`；CRM 前端 `__('New')` 出处。
- **实测（只读或无副作用）**：Node 单测两 app；`bash -n` 三个脚本；`apps.json` JSON 校验；容器 bash 5.2 模拟 `setup.sh` 的 `read` 解析；`erx` 只读 SQL（第 9 幕原始快照 `_a9_o`、工作库 `_work`、第 1／6 幕原始快照的 `Demo Progress`）；读 `erx`／`s8r9` 的 `site_config.json` 键是否存在（不读值）与登记表；读 web 日志 `frappe-bench/logs/s8-r8sb-web.log` 的 500 与 traceback；锁探针 `Spike/P1S8R11-F/p3/lock_unlink_probe.py`（只在自建临时目录建删 `probe.lock`，跑完自删目录，残留 0）。
- **只读码未实测**：`setup.sh` 第 6 段跳过分支（未建站，逐行读码＋解析模拟）；`frappe_china install.reorder_installed_apps` 在缺 `frappe_debug` 时的行为（只看了 `TAIL_APPS` 定义，采信回执）；`search_link` 覆盖的真实浏览器表现（采信 SB `fd002_labels.json`，本片读了该证据）；`runner.js` 焦点判定的真实浏览器行为（采信 SB 复核日志）。
- **跳过及原因**：Python 测试与 migrate（约束：主会话占用 `test.localhost`）；任何 `erx` 写操作、切库、浏览器演示（约束）；Ruff 只在容器内对 `frappe_debug` 跑了 `format --check`（73 文件已格式化），`check` 与 `frappe_china` 采信门禁日志。

## 2. 验证门（本片可跑部分）

| 门 | 声称值 | 实测值 | 一致否 |
|---|---|---|---|
| `frappe_debug` Node | 102/102 | `node --test` 102/102 通过（Node 24.13.1） | ✅ |
| `frappe_china` Node | 116/116 | 116/116 通过 | ✅ |
| `bash -n` | 三脚本通过 | `setup.sh`、`up.sh`、`configure-apps.sh` 通过 | ✅（但语法检查抓不到 P3-01） |
| `apps.json` | JSON 有效 | 有效 | ✅ |
| `frappe_debug` Ruff format | 格式化后 73 文件全过 | 容器内 HEAD `ruff format --check` 73 files already formatted；门禁日志 `s8-r8sb-ruff-frappe_debug.log` 记的是格式化前 2 文件待改，与回执说明一致 | ✅ |
| Python 194／486＋6＋4 | 见回执 | 未跑（约束）；门禁日志 `Ran 194 tests … OK`、`Ran 486 … OK`、`Ran 6 … OK`、`Ran 4 … OK` | 日志一致，未实测 |

## 3. 逐项三层核查

| FD | 回执所写位置 | 代码在 | 真被调用 | 原问题消失 | 证据 | 结论 |
|---|---|---|---|---|---|---|
| FD-002 | `zh.csv` 6 行改带 context；`translation_overrides.py` 删 6 条；`website_translation.py` `CRM_STATUS_CONTEXTS`；`independent_app_labels.js` `applyCRMStatusLabels`；`crm_status.py` `search_link`＋`hooks.py`；两处 list js `Created` 带 context；README 两行 | ✅ 全部在 HEAD | ✅ `hooks.py:279` 覆盖 `frappe.desk.search.search_link`，`handler.execute_cmd` 先取 `override_whitelisted_method`；`/crm` 页 `config.app==='crm'` 时调 `applyCRMStatusLabels`；本 app 内 `Created` 两处都已带 `Result Status`（grep 无裸 `Created`） | ✅ Desk 回到官方「新建／资质／已认证／已转换／未认证／创建」，`/crm` 下拉与看板 14 状态中文（`fd002_labels.json`） | 签名：形参表与上游 `search.py:39-50` 逐个一致（含仅关键字 `link_fieldname`）；上游有 `@http_cache`，覆盖未加，但覆盖经 `get_attr` 调的是带 `http_cache` 的上游函数，其判据是「`frappe.request.path` 含 `frappe.desk.search.search_link`」，请求路径仍是原方法名，故 GET 缓存头照常设置；非状态 DocType 原样返回；其它 app 无同名覆盖（grep 各 `hooks.py`）。上游 `build_for_autosuggest` 只对 translated doctype 译 label，覆盖只替换两状态 DocType 的 label，正确。**已知代价属实**：CRM 前端 8 个文件用无 context 的 `__('New')`（`ActivityHeader.vue:70` 与设置页 7 处），`/crm` 内这些按钮显示「新线索」，README 已登记，在裁决「收窄到 `/crm`」范围内 | **已落地** |
| FD-004 | `masters.py` `build_masters` 置 `bill_for_rejected_quantity_in_purchase_invoice=0`；`verify.py` `accounts.received_not_billed`；集成用例 | ✅ | ✅ `build_masters` 每次建主数据都写；`verify` 新检查在 43 项内 | ✅ 第 9 幕快照：开关值 0；拒收入库行 175、拒收 1928.44 千克，发票数量与合格数不符的 0 行；220202 全期余额 0.00、E 前 0.00 | 只读 SQL（`_a9_o`）；`erx-verify.json` 该项 balance 0.0 | **已落地** |
| FD-005 | `day.py` `workstation_crews`／`_crew_member`；`verify` 两项 | ✅ | ✅ `_run_job_cards` 每张卡取班组成员 | ⚠️ 基本消失：报工员工 1→9 人；生成器日内同员工重叠 0 对（全年仅 D1 现场 3 对，属 SH-P1S8022）。但 `卷簧机-2` 班组（EMP-00002／06／10）全年 0 条报工，见 P3-06 | `_a9_o` 按工位×员工分组；按日期统计重叠对 | **已落地**（附观察 P3-06） |
| FD-006 | `day.py` `_previous_operation_end`、`_last_report_end`、`time_after`；删 `validate_sequence_id` 绕过 | ✅ | ✅ `allocator.take(..., not_before=...)`；完工入库走 `time_after` | ✅ 生成器数据：334 个工单里只有 1 个（D1 现场工单 `MFG-WO-2026-00078`）按「工序号」聚合有先后交叠，逐卡看是分批流水（批 1 回火 11:20 接在批 1 卷簧 11:20 止之后），不是乱序；完工入库早于末道止时 0 行。`day.py` 绕过已删 | `_a9_o` 临时表 SQL | **生成器已落地**；但**另一处绕过仍在** `scenario/targets.py:217`（`prepare_act6`），未登记，见 P3-03 |
| FD-007 | `day.py` `_new_orders`／`_open_deals` 等；`params.py`；`scenario.yaml` `crm.open_deal_ratio: 0.25`；`verify` 两项 | ✅ | ✅ | ✅ 第 9 幕快照：Won 335（概率 100）、Negotiation 23（70）、Proposal/Quotation 25（50）、Demo/Making 27（25）、Qualification 1（第 1 幕现场商机）；预计金额为 1000 的 0 张；销售订单 338 张、客户 31 个（30 池＋第 1 幕现场客户） | `_a9_o` SQL | **已落地**（`0.25` 为 SB 自定缺省，回执已如实说明） |
| FD-008 | `scenario.yaml` 价格走势；`support.py` `scenario_standings`；`verify` `supplier.rotation` | ✅ | ✅ 新建与已有记分卡都写 `scenario_standings()` | ⚠️ 按裁决范围已消失：12 家全年都有采购单（4～88 张），`prevent_pos` 全 0、`warn_pos` 全 1。但 12 家评分全为 Very Poor（7.5～23.9），每家 12 期里 7～11 期 0 分，区分度意图未恢复，见 P3-05 | `_a9_o` Supplier／Scorecard／Period SQL | **按裁决落地**；区分度残留待裁决（P3-05） |
| FD-011 | `progress.py` `_refuse_clean_database`／`assert_can_start`，`save_progress` 先过关；`runner.js` `demo.start` 先调、`start_show`；彩排页按钮；README | ✅ | ✅ `demo.start()` 首行 `xcall assert_can_start`；`save_progress` 每步都调；彩排页 `add_inner_button("开始演示")` 调 `start_show` | ✅ 基库上服务端无条件拒绝（不看前端参数），主绕法已堵 | 读码；SB 两场连演从基库开播成功（日志） | **已落地**；有两条残余旁路（工作库判定信任前端 `mode`；清理快照后 `base_db` 为空即无守卫），见 P3-04 |
| FD-012 | `install.py` `before_install`＋`hooks.py`；`apps.json` `demo_only`；`setup.sh` `DEMO_SITE`；`up.sh`；`.env.example`；`configure_apps.py`／`configure-apps.sh` `--demo`；`docker/README.md` | ✅ | ✅ `installer.py:336` 在 `install_app` 内逐个调 `before_install`，`new-site --install-app` 与 `install-app` 同经此处；`up.sh` 以 `-e DEMO_SITE` 传入；`setup.sh:361-367` 跳过分支逻辑正确（`app_demo_only` 读到 `1`、`DEMO_SITE` 缺省 0 时 `continue`；为 1 时先 `set-config -p frappe_debug_allowed 1`，`-p` 解析为 int 1，守卫接受） | ⚠️ 守卫本身生效；但 **apps.json 多读一列破坏了第 4 段旧循环**：`setup.sh:272` 仍按 5 个变量读 6 列，`app_official` 读成 `"1\t0"`，官方 app 判定恒假，见 P3-01 | 容器 bash 5.2 模拟：`read` 5 变量时末变量为 `$'1\t0'`，`[ "$app_official" = "1" ]` 为假；第 3 段（`:160`）与第 6 段（`:355`）已补列，正确 | **部分落地**（P3-01 须修） |
| FD-013 | `fd013_two_shows.cjs`；`registry.py`／`switch.py`（中途不补库）；`runner.js`（`return_to_base` 自取配置、焦点）；README | ✅ | ✅ `switch_to_act` 传 `claim=False`；无副本时 `claim_refill(only_act=act)`；回基库 `switch_to_db` 与「补齐快照」仍全量认领 | ✅ 判定标准（两场连演含跳回再快进、记换库秒数与补库期间 desk 响应）有日志支撑：六次换库 4.003～4.35 秒，跳回后快进取 `a6_b` 4.201 秒；214 个样本中位 8 毫秒、最大 12268 毫秒（回基库后补库窗口） | `s8-r8sb-fd013.{log,json}`、`-focus.{log,json}` 逐条读 | **已落地**；回执把同期出现的 500 误判为配置读竞争、并称无 traceback，实际有，见 P3-02 |
| FD-020 | `targets.py` `prepare_production_masters`（`prepare_act1` 调）；`demo.yaml` 删两步；`functions.js` 删注册；`rehearsal.py` 删两方法 | ✅ | ✅ `prepare_act1` 首行调用，属 `finish_scenario_segment` 的 D1−1 段 | ✅ `demo.yaml` 已无 `prepare_act4_bom`／`prepare_act5_oper`；第 9 幕快照工位费率 45／65／60／35 与 `scenario.yaml` 一致；整场预跑第 4、5 幕走完 | grep；`_a9_o` Workstation SQL；`erx-rehearsal.log` PASS | **已落地**（被删的两个白名单方法在 SB 起点已带 `_require_administrator()`，删除不涉及鉴权回退） |
| FD-021 | `demo.yaml` 四处 `say`；`test_demo_config` 禁词 | ✅ | ✅ | ✅ 本片对全部 `say:` 行 grep `D1|D2|场景|原生|汉字间空格` 零命中；四处新文案在 292、303、322、428 行 | grep | **已落地** |

## 4. 追加改动核查

| 改动 | 用户裁决出处 | 是否在裁决范围内 | 是否放宽原标准、登记是否覆盖 | 结论 |
|---|---|---|---|---|
| SPC 判定口径 `quality.py` `RULE_WINDOWS`／`outside_window_signals`（筛选器与 `verify` 共用） | 回执「偏离与暂停」：2026-10-27「改判定口径，但加入到延迟需求中」 | ✅ | **是放宽**：AC-019「判异点只出现在场景设定的异常段」被改为「窗外信号若其规则回看窗内含窗内组，算窗内拖尾」。SH-P1S8021 已登记该口径与可选替代（缓冲日、调窗口参数），覆盖。**注意**：实现对 8 条规则一律按回看长度豁免（规则 4、7 回看 14、15 组），登记文字以规则 5、6 为例，未写明连规则 2／4／7 的窗后信号也可被豁免（见 P3-08）。`erx` 工作库按新口径窗外 0 组；按旧口径有几组被豁免，本片无法从 `verify.json` 还原（只存了按新口径的结果） | 在范围内；登记覆盖，表述宜补全（P3-08） |
| 第 9 幕保留期 `targets.py` `ACT9_HELD_RULES`／`act9_hold_start`／`assert_act9_eoq_ready`、`monthly.py` 调用 | 回执：2026-10-27 第 9 幕选 A「现在修」 | ✅ | 不放宽验收：E 日缺 EOQ 时改为生成器报错，比现场报错更严。场景构造的副作用：保留期 7→21 天且把定期复核也扣住，第 9 幕快照里目标线材最后 21 天内有 1 条 `Periodic Review` 与 1 条 `EOQ` 建议被置 Ignored；该窗口落在第 8 幕策略对比的第 3 段（定期复核段，`rules.periodic`～E−1）内，回执未提及对第 8 幕数字的影响（见 P3-07）。缺料：最后 21 天该线材负库存 0 行 | 在范围内；副作用未披露（P3-07） |
| SPC 计划预览站标记 `frappe_debug_quality_preview`（`quality.py` `is_quality_preview_site`、`workspace.py`、`runner.py`、`progress.py` boot、`rehearsal.js`） | 回执：SPC 计划来源选 A | ✅ | 不放宽演示站：标记在 `erx`／`s8dev` 上恒不成立（站点名单优先）；`erx` 站点配置无该键。`s8r9` 已撤回该键与 `root_password`（本片读键存在性：均不存在） | 通过 |
| 演示中途不补库 `registry.py` `claim`／`only_act`、`switch.py` | IT-003 第 6 条已同意的退路；FD-013 待裁决点答复 | ✅ | 不放宽：反而消除了 R8 P3-02「补库与换库抢锁」在演讲中途的触发面。代价是用掉的副本到回基库才补，单场内同一幕第三次取用要等该幕自修（等待页静默轮询，不报错） | 通过 |
| `return_to_base` 自取配置 | FD-013 判定范围内（实测发现） | ✅ | 不涉及标准 | 通过 |
| 右方向键焦点判定（输入过才挡） | 回执：2026-10-27「改运行器」 | ✅ | 是行为放宽（原「有焦点即不响应」→「在该框输入过才不响应」），由用户裁决；`runner.js` 内无合成 `input` 事件（grep `dispatchEvent` 无），`set` 动作不会误记为输入 | 通过 |
| `verify` 排除演示日 `act_scene_days` | 回执：现场单据与新检查，2026-10-27「按建议来」 | ✅ | **是放宽**：四项检查排除 D1、D2、E。本片核实按日期排除没有误伤生成器数据：生成段为 `S～D1−1`、`D1+1～D2−1`、`D2+1～E−1`，三天本无生成器单据（工作库 D2＝2026-04-01 当天订单、报工均 0；D1 只有第 1～5 幕现场单据）。SH-P1S8022 已登记这四项与第 1、4、5 幕现场动作，覆盖 | 在范围内；登记覆盖 |
| 主仓库 `docker/` 改动 | FD-012 裁决「两层都做＋`--demo`」 | ✅ 7 个文件全部服务于 FD-012；`apps.json` 另把两 app 的 `commit` 锁到 SB 提交（回执已写） | 无方案外夹带；但改动引入回归 P3-01 | 无夹带；有缺陷 |
| `frappe_debug/README.md`「重做 SPC 候选计划」改写 | SPC 计划来源裁决 A | ✅ | 不涉及 | 通过 |

## 5. 自证复核

| 回执声称 | 实际复核结果 | 一致否 |
|---|---|---|
| `erx` 工作库 `verify` 43/43 | `s8-r8sb-erx-verify.json`：`ok: true`，43 项全 ok | ✅ |
| 换库六次 4.0～4.4 秒，跳回后快进 `a6_b` 4.20 秒 | 日志 4.241、4.295、4.350、4.238、4.201（`a6_b`）、4.003 | ✅ |
| 回基库补齐 161～247 秒，开播 3.8～3.9 秒 | 161.136、237.797、246.703；`start_seconds` 3.779、3.94 | ✅ |
| desk 接口 214 样本、中位 8 毫秒、最高 12.3 秒在补库窗口 | `fd013.json` 214 样本、0 错、中位 8、最大 12268 | ✅ |
| 不代移焦点复核「两次快进 4.19、3.95 秒」「98 步 127.5 秒」（09:49～09:52） | 现存 `-focus` 日志是 09:58～10:04 的重跑：4.194、4.100，121.9 秒，16 次焦点。09:49 那轮的原始日志已被覆盖，4.19／3.95／127.5 无从核对；复验表引用的 09:58 场与日志一致 | 部分（09:49 场证据已覆盖） |
| FD-013 两场连演「通过」 | 两场 98＋115 步均走完；但 `s8-r8sb-fd013.log` 末行 `exit=1`，即脚本在第二场后的回基库处因 500 中止 | 实质一致，日志状态为失败，回执未说明 |
| `snapshot_status` 500「server 侧没留下 traceback」「推测是换库改 `site_config.json` 与并发读配置的竞争」 | `s8-r8sb-web.log` 有完整 traceback（4659-4734、8009-8123 行）：`registry.refresh／get_registry` → `filelock("frappe_debug_snapshots")` → `filelock/_unix.py` `os.open`／`os.fchmod` 抛 `FileNotFoundError`。与 `site_config.json` 无关。同一原因另有 2 次 `get_demo_config` 500（08:37:58、09:50:14）回执未提 | ❌（见 P3-02） |
| 赢单 338、在途 48（谈判 23、报价 25）（`s8r9`） | `s8r9-verify.json`：Won 338、Negotiation 23、Proposal/Quotation 25 | ✅（`erx` 为 Won 335，生成日不同所致，非矛盾） |
| 报工员工 9 人 | `_a9_o` 9 人 | ✅ |
| 「12 名员工、4 个工位时每个工位 3 人轮班，计件汇总每月最多 12 张」 | `卷簧机-2` 全年无报工，其 3 人 0 条，实际上限 9 | ❌（P3-06） |
| FD-006「绕过已去掉」 | `day.py` 已去掉；`targets.py:217` 仍有同一绕过 | 部分（P3-03） |
| FD-012「`setup.sh` 跳过分支读码核对」 | 第 6 段逻辑正确；第 4 段未补列导致回归 | 部分（P3-01） |
| 整场预跑 3248.2 秒 | `s8-r8sb-erx-rehearsal.log` `total_seconds: 3248.224` | ✅ |
| Python 194／486＋6＋4 | 门禁日志一致（未实跑） | ✅（日志） |
| 本机 `.env` 加 `DEMO_SITE=1`（概况） | `docker/.env` 含 `DEMO_SITE=1` | ✅ |

## 6. 集成检查

| 集成点类型 | 落点 | 两端一致否 | 说明 |
|---|---|---|---|
| 接口契约 | `override_whitelisted_methods` `frappe.desk.search.search_link` → `frappe_china.crm_status.search_link` | ✅ | 形参表一致、有用例守；Desk `link.js:475`、CRM `Link.vue` 两个消费方都走同名方法；返回结构 `{value, description, label}` 不变 |
| 接口契约 | `zh.csv` context 键 ↔ `website_translation.py` `"{source}:{context}"` ↔ `applyCRMStatusLabels` | ✅ | 键格式与 `translate.py:231-232` 一致；`crmBoot` 取到「新线索」「需求确认」 |
| 接口契约 | `apps.json` `demo_only` ↔ `setup.sh` 三处 `read` ↔ `before_install` 的 `frappe_debug_allowed` ↔ `lock-apps.sh` | ⚠️ | `setup.sh:272` 未补列（P3-01）；`lock-apps.sh` 用 `entry.update` 保留未知键，`demo_only` 不会被锁定脚本抹掉；`check_business_order.py` 只读 `app_name`，不受影响 |
| 接口契约 | `assert_can_start(mode)` ↔ `runner.js` `mode()`（sessionStorage） | ⚠️ | 工作库判定依赖前端传入的 `mode`（P3-04） |
| 共享状态 | 登记表锁 `locks/frappe_debug_snapshots.lock`（`get_registry`／`refresh`／`update_copy`／`claim_refill`） | ❌ | 9p 挂载上并发取锁偶发 `FileNotFoundError`（P3-02）；`save_progress` 因 FD-011 每步取这把锁 2 次（原 1 次） |
| 共享状态 | 站点操作锁 `frappe_debug_demo_operation.lock` 与补库 | ✅ | 演示中途不再补库，换库与补库争锁只剩回基库后的窗口；该锁同为 filelock（释放即删文件），理论上同受 P3-02 影响，日志未见实例 |
| 共享状态 | `Demo Progress.base_db`、登记表 `base_db` ↔ FD-011 守卫 | ⚠️ | `drop_snapshots` 把登记表重置为 `base_db: None` 后守卫失效（P3-04） |
| 共享状态 | 站点配置 `frappe_debug_quality_preview` ↔ boot ↔ `rehearsal.js`／`workspace.py`／`runner.py` | ✅ | 演示站名单优先；`erx`、`s8r9` 均无该键 |
| 跨模块数据流 | 生成器 D1−1 段 `prepare_production_masters` → 第 4 幕 BOM 推荐、第 5 幕费用科目 | ✅ | 快照费率与参数一致，预跑通过 |
| 跨模块数据流 | 第 9 幕保留期 → 第 8 幕策略对比第 3 段 | ⚠️ | 最后 21 天 1 条定期复核建议被忽略，落在第 3 段内（P3-07） |
| 跨模块数据流 | 生成器 → `verify`（新 8 项）→ SH-P1S8022 | ✅ | 按日期排除不误伤生成器数据（见第 4 节） |
| 跨模块数据流 | 供应商评分 → 第 9 幕「对照评分确认供应商」 | ⚠️ | 不再禁采，但 12 家全 Very Poor（P3-05） |
| 事件/消息 | `erx_demo_step` | ✅（休眠） | 两 app 的 SB 差异均不含 `publish_realtime`／`erx_demo_step` |
| 事件/消息 | sessionStorage `frappe_debug_mode`／`_transit`：`start_show` 写 `live` → 中转页 → 运行器自启 | ✅ | `transit.html:120` 回基库时删 `mode`，`start_show` 重新写入，两端一致 |

## 7. 新发现

| # | 严重程度 | 定位 | 问题描述 | 违背的标准 | 建议 | 建议档位 | 待裁决点 | 状态 |
|---|---|---|---|---|---|---|---|---|
| P3-01 | 中 | `docker/scripts/setup.sh:272`（第 4 段 `while IFS=$'\t' read -r app_url app_ref app_commit app_name app_official; do`）；`:154` 新增第 6 列 | **FD-012 给 apps.json 多读一列后，第 4 段「remote 归位」仍按 5 个变量读 6 列**，bash 把剩余部分并进末变量：`app_official` 变成 `"1\t0"`／`"0\t0"`，`[ "$app_official" = "1" ]` 对 crm、hrms、insights、raven 恒假。四个官方 app 于是走「自有 fork」分支：没有 origin 时把 bench 建的 upstream（官方仓库 URL）当成 fork，加成**可推送的 origin＝官方仓库**——这正是 P1-S5-R9 FD-010 用 `official` 标记防住的情形。容器 bash 5.2 模拟已复现（`printf %q` 得 `$'1\t0'`）。第 3、6 段已补列，只漏了这一处；`bash -n` 抓不到。用户本机 `.env` 已设 `DEMO_SITE=1`，下次跑 `up.sh` 即触发 | FD-012 回执「解析 apps.json 多读一列」不破坏旧行；`setup.sh` 第 4 段的 FD-010 约定 | `:272` 的 `read` 末尾补一个占位变量（如 `_app_demo_only`），与 `:160` 同写法；可顺带加一处断言或测试，确保各段 `read` 变量数与解析列数一致 | `本Session修` | — | 待裁决 |
| P3-02 | 中 | `demo/registry.py:127,151`（`filelock("frappe_debug_snapshots")`）；Frappe `utils/synchronization.py:40`；`filelock 3.20.4` `_unix.py` `_release`（释放时 `unlink` 锁文件）；`demo/progress.py:56,94`；日志 `logs/s8-r8sb-web.log:4659-4734,8009-8123`；探针 `Spike/P1S8R11-F/p3/lock_unlink_probe.py` | **回执记为观察项的 `snapshot_status` 偶发 500，根因是登记表锁文件在 9p 挂载上的竞争，不是改 `site_config.json`。**filelock 3.20 释放锁时删除锁文件；另一进程恰在此时 `os.open(O_CREAT)`／`fchmod` 同一路径，在 Docker Desktop 的 9p（drvfs）挂载上拿到 `ENOENT`，filelock 不重试、Frappe 只捕 `Timeout`，直接 500。探针：4 进程各取锁 300 次，9p 目录 216/1200 次 `FileNotFoundError`，容器本地 `/tmp` 0 次。web 日志 5 次实例：`snapshot_status` 3 次、`get_demo_config` 2 次（经 `load_scenario→get_registry`，08:37:58 与 09:50:14，后者在演示步骤进行中），traceback 都在，回执称「server 侧无 traceback」不符。**影响面比回执说的大**：凡取这把锁的接口都会偶发 500，包括 `save_progress`（每步都调，FD-011 后每步取锁 2 次）、`switch_to_act`、`get_demo_config`、`start_show`。并发来源是彩排页每 5 秒轮询、回基库后的补库线程 `update_copy`、中转页轮询；单人讲演中途并发少，发生率应低于测试驱动下，但一旦落在 `save_progress` 上，运行器会在浮窗里向观众显示报错 | IT-003 用户要求「不在客户面前报错」；开发守则 §12「Windows 文件锁」高风险点；审核纪律「不信自证」 | 选一：① 登记表锁改用不删文件的锁（如对常驻文件 `fcntl.flock`，与补库串行锁同法）；② 在 `registry.py` 包一层对 `FileNotFoundError` 的有限重试；③ 把锁目录放到容器本地文件系统。修后用本片探针在 9p 目录复跑应为 0；并把回执该观察项的根因改正 | `新Session修` | 修法选 ①②③ 哪种；是否连同 `operation.py` 的站点操作锁（同为 filelock、同样释放即删）一起改 | 待裁决 |
| P3-03 | 低 | `frappe_debug/scenario/targets.py:5,217`（`prepare_act6`：`with patch.object(JobCard, "validate_sequence_id", lambda _card: None): card.save(...)`，来自 `e5a9e6c`） | FD-006 原问题 ③「绕过原生工序顺序校验、方案没写、未登记」在生成器另一处仍在：第 6 幕负荷目标给草稿工序卡写排程行时，用同样的空函数绕过 `validate_sequence_id`（草稿卡非新建时 `validate` 会跑它，前道未完工即抛错，所以这里确实需要）。README 与回执均未登记；回执写「绕过已去掉」只对 `day.py` 成立 | FD-006 裁决「去不掉则保留并登记理由」；开发守则覆盖登记 | 登记理由（第 6 幕只排计划、不报工，前道必然未完工），或改为直接插入 `scheduled_time_logs` 子表行而不走整单 `validate` | `本Session修` | 登记保留，还是改写去掉 | 待裁决 |
| P3-04 | 低 | `demo/progress.py:52-62`（`_refuse_clean_database`）、`:85`（`save_progress` 固定传 `"rehearsal"`）；`runner.js:99,507`（`mode()` 取 sessionStorage）；`snapshot.py:94`（`drop_snapshots` 把登记表置 `base_db: None`） | FD-011 的服务端守卫有两条旁路：① 工作库：`assert_can_start` 只在前端传 `mode != "rehearsal"` 时拒绝，`save_progress` 永远按彩排放行，所以在工作库控制台把 sessionStorage 改成 `rehearsal` 再调 `demo.start()` 即可把第 1 幕写进预跑工作库；② 清理快照库后登记表 `base_db` 为空，守卫整个失效，此时在清洁基库调 `demo.start()` 或 `save_progress` 会写进基库。两者都要控制台误操作，正常按钮流程不会触发 | 裁决「基库、工作库上拒绝开播」；需求 §4.4.9「不动清洁基准」 | ① 工作库判定改在服务端认「当前是否有进行中的彩排」（如登记表 `work_state` 与生成状态），不信前端参数；② `drop_snapshots` 后保留一个「清洁基库」标记（或 `Demo Progress.base_db`）供守卫判断 | `延迟或不修` | 是否接受「只防按钮流程、不防控制台」 | 待裁决 |
| P3-05 | 低 | 第 9 幕快照 `tabSupplier Scorecard`：12 家 `supplier_score` 7.5～23.9、全部 `Very Poor`；`tabSupplier Scorecard Period` 每家 12 期里 7～11 期 0 分；`demo.yaml:440-442`（第 9 幕打开供应商评分卡并讲「价格与履约表现一并参考」） | FD-008 按裁决修完后，禁采没了，但评分仍无区分度：每家只在约 3 个月当最低价，其余月份无单得 0 分，加权平均后 12 家全被原生判 Very Poor（列表全红，且每家都带 `warn_pos`）。原报告意图是 AC-019「无空分」背后的区分度与第 9 幕能「看评分确认供应商」；现在观众看到的是十二家全部「很差」 | FD-008 原问题描述「评分失去区分度」；AC-019 意图 | 若要恢复区分度，只能动评分口径（无单月份不计分或用原生缺省标准），这超出裁决「不改评分公式」，需用户改判；或接受现状、讲解词避开等级 | `出方案修` | 接受全 Very Poor，还是改判允许调整评分口径 | 待裁决 |
| P3-06 | 观察 | `scenario/day.py` `workstation_crews`（按员工序号对**全部场景工位**取模）；`data/scenario.yaml:127-130`；第 9 幕快照：`卷簧机-2` 0 条报工；`verify.py` `staff.reporting_employees` 门槛 `min(employees, workstations)` | 班组按 4 个工位分，`卷簧机-2` 全年没有排到工序卡，其班组 EMP-00002／06／10 全年 0 条报工，计件汇总每月最多 9 人，不是回执说的 12。`verify` 门槛只要求 4 人，退回到 4 人也会通过 | 回执自述「每月最多 12 张」；FD-005 意图（12 名员工都参与） | 班组只按实际有工序的工位分，或门槛改为在职员工数；记录即可 | `延迟或不修` | — | 待裁决 |
| P3-07 | 观察 | `scenario/targets.py` `act9_hold_start`（E−21 起扣 EOQ 与定期复核）；`functions.js:281-288`（第 8 幕第 3 段＝`rules.periodic`～E−1）；第 9 幕快照目标线材 E−21 起 `Periodic Review` Ignored 1、`EOQ` Ignored 1 | 第 9 幕保留期扩到 21 天并扣住定期复核后，第 8 幕「三种补货策略对比」的第 3 段（定期复核段）末尾有一次定期复核补货被人为跳过，该段的库存占用、采购次数、总成本因此偏低。回执「修得最勉强」一节提到是在造场景，但没提对第 8 幕数字的影响 | 第 8 幕对比的公平性（需求 §4.2 第 8 幕）；回执如实 | 记录即可；若在意，第 8 幕第 3 段终点改为 `act9_hold_start − 1` | `延迟或不修` | — | 待裁决 |
| P3-08 | 观察 | `scenario/quality.py` `RULE_WINDOWS`／`outside_window_signals`；概况 SH-P1S8021 | 豁免逻辑对 8 条规则一律按回看长度判（规则 2、4、7 回看 9、14、15 组），只要回看段里有一个窗内组就豁免，不要求该窗内组参与触发。登记文字以规则 5、6 为例，读者会以为只豁免短窗口规则 | SH-P1S8021 的登记完整性 | 在 SH-P1S8021 补一句「适用全部 8 条规则，回看最长 15 组」；或把豁免限定在规则 5、6 | `延迟或不修` | — | 待裁决 |

**找过但无发现的方向**：`search_link` 覆盖的签名、缓存头与其它 app 冲突；FD-012 第 6 段跳过分支与 `set-config -p` 的值类型；`before_install` 能否被 `new-site --install-app`／`install-app --force` 绕过（同一调用点，不能）；FD-006 生成器内是否另有对 `JobCard` 的 patch（只有 P3-03 一处）；`frappe_china` 是否 patch `validate_sequence_id`（无）；`verify` 按日期排除是否误伤生成器单据（无）；预览站标记能否在演示站成立（不能）；`docker/` 改动有无方案外夹带（无）；SB 差异有无新增事件。

## 8. 交接摘要

**本片依赖什么**
- 片 1／片 2 对 `frappe_china` 业务改动（FD-002 之外）与生成器其它项的复核结论；本片只核了 FD-002 的译名链路。
- `frappe_china.install.reorder_installed_apps` 在站点未装 `frappe_debug` 时照常（`TAIL_APPS` 含它，回执称只排已装 app，本片未读实现）。
- SB 的浏览器证据（`fd002_labels.json`、FD-013 日志）作为真实浏览器层的唯一来源。

**本片暴露什么**
- P3-01：`setup.sh:272` 回归，修前不要对本机重跑 `up.sh`（会把四个官方 app 的 origin 设成官方仓库）。
- P3-02：登记表锁在 9p 上偶发 `FileNotFoundError`，影响 `save_progress`、`switch_to_act`、`get_demo_config`、`snapshot_status`；若别的片也看到 `filelock` 相关 500，根因相同。
- 登记表锁、站点操作锁都是 filelock 3.20（释放即删文件）；补库串行锁 `frappe_debug_refill.lock` 是 `flock` 命令、常驻文件（目录里现只有它）。
- 第 9 幕快照数据画像（供收口与片 2 对照）：报工员工 9／12；赢单 335、在途 75（其中 Demo/Making 27 无报价）；订单客户 31；12 家供应商都有单、全 Very Poor；220202 余额 0.00。

## 9. 复核建议（本片特有）

1. **定级在边界上的**：P3-01 定「中」，理由是会把官方仓库配成可推送 origin，且用户已设 `DEMO_SITE=1` 随时会跑；推送需凭据，若认为风险只是 remote 名错乱可降「低」，但修法只有一行，建议当场修。P3-02 在「中／低」之间：讲演中途并发少、发生率应低，但它出在每步都调的 `save_progress` 上，且根因被回执误判，定「中」。P3-05 在「低／观察」之间：取决于第 9 幕是否会让观众看清评分等级。
2. **查得最浅的部分**：`setup.sh` 第 6 段跳过分支与 `reorder_installed_apps` 的组合没有实跑，只读码＋解析模拟；FD-002、FD-013 的真实浏览器层全部采信 SB 证据；Python 测试一条没跑。查法：在可丢弃的空站上 `DEMO_SITE=0` 跑一次 `setup.sh`，看 `frappe_debug` 是否跳过、6.2 归位与 `check_business_order.py` 是否通过、四个官方 app 的 remote 是否正确（后者可直接验证 P3-01）。
3. **开放找漏的盲区**：没查 `frappe_china` `zh.csv` 改动以外的 csv 行是否因删 6 条覆盖登记而失去「覆盖依据」测试的守护；没核 SPC 新口径下 `erx` 实际被豁免了几组（`verify.json` 只存新口径结果）；没查 P3-02 在 Windows 原生或 Linux 本地盘部署时是否存在（探针显示容器本地盘为 0，客户正式部署不在 9p 上时可能不复现）；没查多标签页同时开 desk 时 `typed_in` 焦点判定的行为。
4. **拿不准处**：P3-05 是否算问题——裁决明确「不改评分公式」，全 Very Poor 是该裁决的直接结果，可读为「用户已接受」；我按 FD-008 原问题里的「区分度」意图列为待裁决。
