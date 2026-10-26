# 审核报告·片3（对象：`frappe_debug` @ `d8614a5` 的演示框架、`/crm` 驱动、快照与换库、彩排、九幕配置与客户说明／审核标准：R04 需求文档＋R05 开发方案）

**轮次**：P1-S8-R8 F 片3｜**日期**：2026-10-26｜**执行者**：Claude（Opus 5.5，片 3 子 Agent）｜**打tag**：否
**依据（要求层）**：[总纲](../R05-开发方案/P1-S8-R5-C开发方案-总纲.md)全文（A1～A20、§四、§5.3／5.4、§六、§十）、[Part3](../R05-开发方案/P1-S8-R5-C开发方案-Part3.md)全文（SL-012～017、TS-018～026）；R6 [彩排方案补充 A](../R06-代码/P1-S8-R6-D彩排方案补充建议.md)（用户已批准，视同方案补充）
**依据（意图层）**：[需求文档](../R04-需求文档/P1-S8-R4-B需求文档.md) §4.2、§4.3、§4.4 全节、§4.9.3、§4.15、§七、§八 AC-020～029；ADR-0008、ADR-0014；P1 概况契约一；`docs/开发守则.md`、`docs/业务规则.md`
**线索（不当结论）**：D 回执 Part3、D 讨论记录、D 待验表、R7 E 确认报告
**探针**：`Spike/P1S8R8-F/p3/`（`flock_probe.py`、`thread_lock_probe.py`、输出 `probes.log`）。只动临时锁文件，残留核 0。未连 `erx.localhost` 的库与接口，只读了它的 `site_config.json` 的 `db_name` 与 `private/frappe_debug/snapshots.json`；未在 `test.localhost` 跑测试、migrate 或清缓存；未建删任何库。

## 覆盖自证

- **读全的代码**：`hooks.py`；`demo/` 下 `config.py`、`progress.py`、`scene_date.py`、`crm_inject.py`、`dbops.py`、`registry.py`、`snapshot.py`、`switch.py`、`workspace.py`、`operation.py`、`functions.py`、`brochure.py`；`public/js/demo/runner.js`、`functions.js`、`rehearsal.js`；`public/demo/transit.html`；`templates/crm_demo.html`；`frappe_debug/page/demo_rehearsal/*`、`doctype/demo_progress/*.json`；`data/demo.yaml` 全文；`README.md`。
- **只读相关段**：`crm_driver.js`（存储键与回写进度段，主体 E 已核 10/10，不重复）；`scenario/runner.py` 的 `start_generate`／`_run_generate`／`generate_status`／`_read_status`；`scenario/rehearsal.py`；`scenario/targets.py:prepare_act4`；`scenario/monthly.py:finish_scenario_segment`；`scenario/support.py:clear_admin_list_filters`；`scenario/quality.py` 的白名单段；`docker/scripts/setup.sh` 的装 app 段。上游对照：`frappe/app.py`（after_response、`sync_database`）、`config.py`（站点配置缓存）、`redis_wrapper.py`（键前缀）、`model/document.py:1655`（doc_events 顺序）、`model/utils/user_settings.py`、`list_view.js:593-605`、`erpnext/manufacturing/doctype/bom/bom.py:1693`。
- **测试文件**：只看 `test_switch.py`、`test_registry.py`、`test_transit.cjs`、`test_rehearsal.cjs`、`test_rehearsal_page.cjs` 中与发现有关的用例，没逐条审测试断言。
- **跳过**：Python 测试未自跑（约束：不在 `test.localhost` 跑）；没做真实浏览器换库或整场预跑（约束；`s8dev.localhost` 已不在站点清单里）；E 已核的 IT-001／002 和 IT-008～016（片1／片2 范围）不重复；客户说明 PDF 只核页数与禁词（按指示），截图只看了 act1 一张。
- **分片**：本片 = Part3 全部九个任务＋总纲中 Part3 相关条目。Part1／Part2 范围只在集成点上读。

## 验证门实跑结果

| 门 | 声称值 | 实测值 | 与基线对比 | 一致否 |
|---|---|---|---|---|
| `node --check`（runner／functions／rehearsal／crm_driver／彩排页 js 共 5 个） | E：语法通过 | 5/5 OK | — | ✅ |
| `node --test tests/*.cjs`（frappe_debug） | E 修后 97/97 | 97/97 通过（1.2 秒） | R7 开工时 95 → 97，只增不减 | ✅ |
| `ruff check` ／ `format --check`（frappe_debug，容器内） | E：通过 | All checks passed；70 files already formatted | 与 E 的 70 文件一致 | ✅ |
| frappe_debug Python 全量 | E 修后 175～178 | 未跑（约束） | — | 未核 |
| 锁探针（9p 挂载跨进程 flock） | D：补库串行锁有效 | 持锁时另一进程 `Timeout`，释放后可取（`probes.log`） | — | ✅ |
| 锁探针（同进程另一线程，`timeout=0`） | 无声称 | 另一线程立即 `Timeout`（`probes.log`） | — | 支撑 P3-02 |
| 客户说明 PDF | 9 页 A4、无「今天」 | `pdfinfo` 9 页 595×842；`pdftotext` 含「今」字 0 次 | — | ✅ |

## 逐项落地核查

| 意图层依据 | 要求层要求（方案任务） | 定位（文件:行） | 落地 | 生效否 | 偏差说明 |
|---|---|---|---|---|---|
| §4.4.2 配置开播前校验 | TS-018 ① `demo.yaml` 形态、`scene_date_fields`、`start_route` | `data/demo.yaml:1-19` | ✅ | ✅ `get_demo_config` 读它 | — |
| 同上 | TS-018 ② `get_demo_config`／`validate_config`，`D2-1` 形式 | `demo/config.py:51-56,135-210` | ✅ | ✅ 运行器 `start` 调用（`runner.js:483`） | 加了 `pause` 拒收（IT-006 用户裁决）、`rule_dates` 返回键；已登记 |
| §4.4.5 演示进度 | TS-018 ③ DocType `Demo Progress` 六字段、仅 System Manager | `doctype/demo_progress/demo_progress.json` | ✅ | ✅ | — |
| 同上 | TS-018 ④ `save_progress`／`get_progress`／`extend_bootinfo` | `demo/progress.py:14-83`、`hooks.py:10` | ✅ | ✅ boot 带进度，中转页读 `get_progress` | `get_progress` 改为白名单（中转页要用），合理 |
| §4.4.3 动作集 | TS-019 ② 十三个动作 | `runner.js:254-344` | ✅ | ✅ | `set` 后追加值高亮框（`f6e5faa`）、`open_list` 加 `sort_by`、`open_report` 加 `wait_for_results`，均为方案外小扩展，见 P3-08 |
| 同上 | TS-019 ① 只在激活或有模式时启动，否则只注册「开始演示」入口（彩排页里） | `runner.js:499-503`；`demo_rehearsal.js` 无该按钮 | ⚠️ 部分 | ❌ 入口不存在 | **见 P3-01**：从基库无法开播 |
| §4.3.2 第 2 条 | TS-019 ③ 前端场景日期 | `runner.js:345-360,488-493` | ✅ | ✅ | 另把 `posting_time` 固定为 23:00 起按幕／步递增（D 回执 2026-10-24 段已登记，为防跨午夜负库存） |
| 同上 | TS-019 ④ 服务端 `apply_scene_date` | `demo/scene_date.py`、`hooks.py:18` | ✅ | ✅ | 片1 问的 Job Card 排程见交接摘要：不受影响 |
| §4.4.6 推进与快捷键 | TS-019 ⑤ `right`、`alt+r`、`alt+h`、`alt+1～9`，撞键自查 | `runner.js:459-480` | ✅ | ✅ | 撞键时 throw 而非 `console.error`，效果同为不启动；需求写「空格或方向键」，方案取 `right`，README 却写「或空格」，见 P3-09 |
| 同上 | TS-019 ⑥ 浮窗 | `runner.js:361-371`、`public/css/demo.css` | ✅ | ✅ | 中文字面量（A10） |
| §4.4.7 `/crm` 驱动 | TS-020 注入、驱动、读回、兜底 | `demo/crm_inject.py`、`templates/crm_demo.html`、`crm_driver.js` | ✅ | ✅ | E 已核 10/10，本片只核了存储键两端一致 |
| §4.4.8 快照 | TS-021 ① `dbops`：库名白名单、`MYSQL_PWD`、`clone_sync`／`clone_detached`／`drop_db` | `demo/dbops.py` | ✅ | ✅ | 无注入面（库名正则、`shlex.quote`、端口 `int`）；`drop_db` 漏传端口，见 P3-10 |
| 同上 | TS-021 ② 登记表与 `filelock` | `demo/registry.py` | ✅ | ✅ | IT-003 后加 `claim_refill`／`act_availability`／`_clone_vanished` |
| 同上 | TS-021 ③ `take_snapshot`／`snapshot_status`／`drop_snapshots`／`replenish` | `demo/snapshot.py` | ✅ | ✅ | `snapshot_status` 没有鉴权，且会写登记表，见 P3-05；返回值键名与 §5.3 不同，见 P3-13 |
| 同上 | TS-021 ④ `_switch`、`switch_to_act` 选库表、权限 | `demo/switch.py:36-124` | ✅ | ✅ | 选库规则已按 IT-003 统一为「m 就绪用 m，否则 b」 |
| 同上 | TS-021 ⑤ `switch_status` 允许 Guest、只回 db 与 user | `switch.py:175-177` | ✅ | ✅ | — |
| §4.4.8 换库四步 | TS-022 ① 中转页 | `public/demo/transit.html` | ✅ | ✅ | csrf 走 sessionStorage 不走 URL（已登记）；IT-003 后加场景文案与 `quietStop` |
| 同上 | TS-022 ② 运行器侧快进／重来／跳幕 | `runner.js:397-441` | ✅ | ⚠️ | 单场主路径生效；多场与边界见 P3-01、P3-02、P3-03 |
| §4.4.8 演示结束 | TS-022 ③「回到演示前」「清理快照库」 | `demo_rehearsal.js:58-72`、`runner.js:450-458` | ✅ | ✅ | 回基库后补齐全部已用副本（IT-003） |
| §4.4.9 预跑 | TS-023 ① Page `demo-rehearsal` | `frappe_debug/page/demo_rehearsal/` | ✅ | ✅ | IT-003 加「就绪检查」「补齐快照」 |
| 同上 | TS-023 ② 预跑编排＋补充 A 工作库生命周期 | `rehearsal.js`、`demo/workspace.py` | ✅ | ✅ | E 读验收 json 确认（本片读了 `logs/s8-r7e-erx-rehearsal.json`：`done`、2885.784 秒、9 次快照） |
| 同上 | TS-023 ③④ 场景日期、耗时记录 | `rehearsal.js:172,187` | ✅ | ✅ | — |
| §4.2 九幕 | TS-024 ① 九幕配置 | `data/demo.yaml:20-456` | ✅ | ✅（E 整场预跑） | 第 4、5 幕首步暗改主数据，见 P3-06 |
| 同上 | TS-024 ② 命名函数，服务端「仅 Administrator」 | `functions.js`（25 个注册）、`demo/functions.py` | ⚠️ | ⚠️ | `demo/functions.py` 全部校验 Administrator；但第 4、5 幕调用的 `scenario/rehearsal.py` 两个白名单方法没有校验，见 P3-05 |
| §4.15 讲解词 | TS-024 ③ 不写「今天」、用最终译名 | `demo.yaml` 83 处 `say` | ⚠️ | — | 无「今天／今日」；但有五处向客户念出内部代号，见 P3-07 |
| §4.15 客户说明 | TS-025 九页 PDF | `demo/brochure.py`、`templates/brochure.html`、`0-P1-S8文档/客户说明.pdf` | ✅ | ✅ | 9 页、无禁词；截图早于 R7 数据重生成，见 P3-12 |
| §4.9.3-11 | （Part2 生成器，片2 转交）快照前清列表设置 | `scenario/monthly.py:276-277` | ⚠️ | ⚠️ | 九个快照点里只有三处主动清，见 P3-11 |
| TS-019 收尾 | TS-026 README、部署、`root_password`、正式库不装 | `README.md`；`docker/scripts/setup.sh:351-365` | ⚠️ | — | README 四处与实现不符（P3-09）；没有阻止装进正式库的守卫（P3-04）；口令足迹（P3-10） |
| ADR-0013／§4.4.8 末 | 换库方法只许 Administrator | `snapshot.py:9-12`、`switch.py:29-32`、`workspace.py`（引 `snapshot._authorized`） | ✅ | ✅ | `frappe.only_for` 对 Administrator 直接放行，实际判据就是 `user == "Administrator"`，符合要求 |

## 集成检查

| 集成点类型 | 具体落点 | 两端一致否 | 说明 |
|---|---|---|---|
| 事件/消息 | **跨 Phase 契约：`erx_demo_step` ／`{node, params?, seq}`／无状态**（开发守则 §13 唯一一行） | ✅（两端都没有实现，契约处于休眠） | `frappe_debug` 里 grep 不到 `erx_demo_step`、`publish_realtime`、`frappe.realtime`；`frappe_china` 只在 `realtime_check.py:5` 的注释里提到它（自检另用事件名）。符合 ADR-0014：S8 推进不经事件，协议本体留给 `SH-P1S8003`／S9。旁注：ADR-0008 落点表说 `frappe_china` 有「推送助手」，grep 不到，属文档漂移，不在本片范围，交收口判断 |
| 事件/消息 | sessionStorage 键：`frappe_debug_transit`／`_csrf`（runner 写 → transit 读）、`_pending`／`_result`／`_crm`（functions.js 写 → crm_driver 读写）、`_mode`（live／rehearsal）、`_rehearsal` | ✅ | 字段逐个对过：runner 写 `{act, purpose, route, scene_date, from_route, return_to_base, csrf}`（`runner.js:429-437`），transit 读同名键（`transit.html:60-68`）；`switch_db` 载荷的 `db`、`resume_act`、`resume_playback` 两端一致 |
| 接口契约 | 总纲 §5.3 服务端接口 | ⚠️ | `get_demo_config`、`save_progress`、`switch_to_db`、`switch_status`、`start_generate`、`generate_status` 签名一致；`switch_to_act` 不回 `route`（改由中转页从 sessionStorage 取路由并在目标库展开引用，已登记）；`take_snapshot` 回 `{act, db, seconds, status}`，方案是 `{orig, elapsed_s}`，未登记、无消费方读它（P3-13）。§5.3 以外新增 `prepare_work`、`restore_work`（补充 A 批准）、`refill_snapshots`（IT-003 批准） |
| 接口契约 | 总纲 §5.4 前端约定（注册表、ctx、模板展开、执行顺序） | ✅ | `ctx` 键齐全（`runner.js:176-180`）；执行顺序「say → 动作 → save_progress」一致；`pause` 已按 IT-006 废弃 |
| 接口契约 | frappe_china 报表与页面路由（片1 暴露） | ✅ | Capacity Load 筛选 `company/from_date/to_date/bucket`、策略对比 `company/period_1..3_from/to`、三张法定报表 `company/fiscal_year/month(/period_type)` 与 `demo.yaml`、`functions.js:289-341` 的键逐个对上；`spc-chart` 页的 `wrapper.spc_fields／spc_load` 存在（`spc_chart.js:80-81`）；`Use recommended BOM` 按钮文字与 `production_plan.js:69` 同源 |
| 接口契约 | 侧栏 `?sidebar=Business%20Flow`（HT-011） | ✅ | `frappe_china/workspace_sidebar/business_flow.json` 存在；九幕 `route` 与 `open_form` 都带该参数；E 已有浏览器证据 |
| 共享状态 | `snapshots.json` 登记表 | ✅ | 写方 `snapshot`／`switch`／`workspace`／`registry.refresh`，读方再加 `params.load_scenario`（`scenario_end`）、`progress.save_progress`、`dbops.drop_db`、彩排页，全部经 `filelock("frappe_debug_snapshots")`。只读核 `erx` 现状：`work_state=ready`、第 1 幕 m `used`、其余 26 份 `ready`、`db_name=_2bd5b09209543e8e_a1_m`，与 E 终态一致 |
| 共享状态 | 站点操作锁 `locks/frappe_debug_demo_operation.lock` | ⚠️ | 换库、快照、补库、工作库、生成器入队共用一把锁，`timeout=0`；补库循环在响应后逐份取锁，与下一次换库互斥，见 P3-02 |
| 共享状态 | `Demo Progress` 单例 | ✅ | runner／crm_driver 写，boot、中转页、`apply_scene_date` 读；每份快照里一条 |
| 共享状态 | 站点配置 `db_name` 与 Redis 前缀 | ✅ | `_switch` 改配置、清本进程配置缓存、删目标库前缀键；HT-015 已 go（在途任务仍写旧库，靠「生成期间不换库」规避，`start_generate` 以 `expected_db` 再拦一次） |
| 跨模块数据流 | 生成器 → 各幕前置（片2 暴露） | ✅（读码） | `find_act7_order` 认 `po_no=S8-ACT7`、`delivery_date=D2`；`find_eoq_suggestion` 认 `act9_eoq_item`、E、`Awaiting Decision`；`next_demo_lead` 要未转换线索；质检计划认 `quality-plan.json`。整场预跑 `done` 是这条链的正向证据 |
| 跨模块数据流 | 列表设置清空（§4.9.3-11） | ⚠️ | 见 P3-11 |

## 业务规则合规核

> 业务规则八条全部「未经专家确认」。本片改动多为演示操控，涉及产品语义的只有第 1、5、7 幕调用 `frappe_china` 的那几处。

| 规则条款 | 本 Round 改动是否涉及 | 结论 | 备注 |
|---|---|---|---|
| BR-001 小企业会计准则 | 否 | 合规 | 本片不碰科目表 |
| BR-002 报表至少三张、月报 | 是（第 7 幕开三张法定报表） | 合规 | `open_previous_month_statement` 取上月月报；出数靠 frappe_china，E 有只读回读 |
| BR-003 税率 | 是（第 1 幕税模板 `13% 专票 含税价 - HDTH`） | 合规 | 销售货物 13% |
| BR-004 应交增值税月末转出 | 是（第 7 幕 `close_previous_month` → `generate_month_end_closing`） | 合规（实现在 frappe_china，本片未复核分录） | — |
| BR-005 附加税 | 同上 | 合规（同上） | — |
| BR-006 资产负债表平衡 | 是（第 7 幕） | 合规（采信 E `s8-r7e-run2-act7-readback.json`，本片未复跑） | — |
| BR-007 价税分离 | 否（计算在 frappe_china） | 合规 | — |
| BR-008 完工入库无损益行 | 是（第 5 幕完工入库） | 合规（采信 E） | `prepare_act5_operating_cost_account` 只在公司 `default_operating_cost_account` 为空时补成 `expenses_added_to_stock_account`（410199），不引入损益科目；但它是方案外的现场写入，见 P3-06 |
| 规则新增／变更 | 否 | — | 本片未检出新领域不变量。`posting_time` 固定 23:00 起递增是演示实现约定，不是业务规则 |

## 自证复核

| 被审产物声称 | 实际复核结果 | 一致否 |
|---|---|---|
| E：IT-003 已修，`select_snapshot` 统一、主动补库、静默自修 | 代码在（`registry.py:205-273`、`switch.py:93-124`），单测在；**修复后没有真实浏览器的多场复测**，SL-014 ① 十次计时证据早于修复（P3-03） | 部分 |
| E：IT-003 第 6 条「实测补库对界面速度的影响」照做 | `logs/`、`Spike/P1S8R7-E/` 都找不到相关记录 | ❌ |
| E 疑问：SL-015 ①「27 份全部就绪」与「停在第 1 幕主用库」矛盾 | 实现取 26 ready＋1 used，彩排页文字注明「当前所在库计为已用，属正常」（`demo_rehearsal.js:21`）；README:45 仍写「均为就绪」 | 实现已化解，文档没跟上（P3-09） |
| E 疑问：SL-014 ⑤「未演过的幕」没有定义 | IT-003 后按状态选库，不再区分「演过」：m 就绪用 m，否则 b。等价于「取干净那份」，需求表的意图成立 | ✅（定义被状态取代） |
| D README：「每按一次右方向键或空格走一步」 | 只绑了 `right`（`runner.js:464-465`） | ❌（P3-09） |
| D README：「本 app 不注册覆盖钩子」 | 后端不注册；前端包装了全局 `frappe.get_indicator`（`runner.js:10-28`） | ❌（P3-08） |
| D README：「开讲前看就绪检查，全部就绪再开始」 | 停在第 1 幕主用库时最多 17/18；能全绿的状态（基库）却开不了播 | ❌（P3-01） |
| D 回执：快照接口只许 Administrator | 换库、快照、工作库接口成立；`snapshot_status` 与第 4、5 幕两个服务端方法例外 | 部分（P3-05） |
| D 回执 TS-025：缩略图检查无遮挡 | act1 截图右下有四个已提交提示框叠在表单上 | 观察（P3-12） |
| E：讲解词无「今天」 | 83 处 `say` 无「今天／今日」，PDF 无「今」字 | ✅ |
| E：Node 97/97、Ruff 通过 | 自跑一致 | ✅ |

## 问题清单

| # | 严重程度 | 定位 | 问题描述 | 违背的标准/意图 | 建议 | 建议档位 | 待裁决点 | 状态 | 用户裁决 |
|---|---|---|---|---|---|---|---|---|---|
| P3-01 | 中 | `runner.js:499-503`（只在 `progress.active` 或 sessionStorage 有模式时启动）；`transit.html:107`（回基库时删 `frappe_debug_mode`）；`demo_rehearsal.js` 全文（无开播按钮）；README:50-55；清洁基准备份里 `Demo Progress.active=0` | **按 README 走完一场、点「回到演示前」之后，下一场开不了播。**回基库后基库的进度是未激活，sessionStorage 的模式也被删掉，运行器不启动，快捷键不注册，`Alt+1` 没有反应；彩排页也没有方案 TS-019 ① 要求的「开始演示」入口。README 要求「就绪检查全绿再开讲」，而能全绿的恰好就是这个基库状态（停在第 1 幕主用库时最多 17/18）。若有人在基库上从控制台调 `frappe_debug.demo.start()`，`begin_act(1)` 不换库，第 1 幕会直接写进清洁基库。现在能用的绕法是：上一场结束不回基库，直接按 `Alt+1`（跳幕也会触发补库）。用户已说明「之后会对不同客户做多次演示」 | 方案 TS-019 具体改动 1「否则只注册『开始演示』入口（彩排页里）」；需求 §4.4.9 第 1 条「不动清洁基准本身」；§七 演示者流程 | ① 彩排页加「开始演示」按钮：调 `switch_to_act(1, "jump")` 经中转页进第 1 幕，置 `frappe_debug_mode=live`；② `demo.start()` 在当前库是登记表的 `base_db` 或 `work_db` 时拒绝开播；③ README 现场演示节改成「回基库 → 就绪全绿 → 点开始演示」 | `新Session修` | 下一场的标准流程定哪种：A 每场结束都回基库，再用新按钮开播；B 不回基库，场间按 `Alt+1`（README 照此改，「回到演示前」只在彻底收尾时用） | 待裁决 | |
| P3-02 | 中 | `demo/operation.py:14`（`FileLock(timeout=0)`）；`snapshot.py:59-71`（`replenish` 套 `@site_operation`）；`switch.py:156-172`（补库在响应后的回调里逐份调 `replenish`）；`transit.html:34,55,129`；探针 `Spike/P1S8R8-F/p3/probes.log` | **换库后的后台补库和下一次换库抢同一把非阻塞锁，抢输的一方当场报错。**每次换库或回基库后，web 进程在响应后的回调里逐份补库，每份都取站点操作锁再删库（`DROP DATABASE` 走子进程）。这时演示者若按 `→`、`Alt+R` 或 `Alt+数字`，`switch_to_act` 立即拿到「已有演示数据库操作正在进行，请稍后重试」，中转页走 `fail()`，向观众显示「切换未完成」和这句报错。回基库后一次要补十几份时，窗口最长。反过来，补库那份抢输时会被标成 `failed`，下次换库会再认领，能自愈，不丢数据。探针证实同进程另一线程在 `timeout=0` 下立即超时；没做端到端复现（不碰 erx） | IT-003 用户要求「不在客户面前报错」（E 报告 IT-003 建议第 4 条，2026-10-25 裁决「全部照做」） | ① 中转页把「操作正在进行」当作 waiting，静默每 2 秒重试；② 或补库只在登记表锁内认领，删库与启动克隆放到锁外；③ 补一条测试：持锁时调 `switch_to_act`，中转页不显示错误 | `本Session修` | — | 待裁决 | |
| P3-03 | 中 | E 当场修清单 #3（只有单测）；D 回执 Part3 第 66-76 行（计时证据为修复前代码）；`logs/`、`Spike/P1S8R7-E/` 无补库耗时记录 | **IT-003 的「原问题真消失」只有单测支撑。**修复后的整场预跑只覆盖到「预跑结束跳回第 1 幕」，没有任何真实浏览器的多场复测：「第二场第 5→6 幕按 `→`」「单场内跳回后再快进」两种卡死路径都没有实测；SL-014 ①（十次快进≤10 秒）、④（连续两次重来）的证据都是修复前代码的。IT-003 第 6 条（演讲中途补库对界面速度的影响，变慢就退到「只在回基库后与开场前补」）用户已同意照做，但找不到任何测量记录。现在每次换库都会在演示途中启动其余已用副本的 `mariadb-dump｜mariadb` | 审核纪律 9 第三层；E 报告 IT-003 第 6 条与用户裁决 | 在 `s8ts023preview` 或新建的临时站（不在 erx）按「第一场全程 → `Alt+1` 或回基库 → 第二场全程，含一次跳回再快进」跑一遍，记各次换库秒数与补库期间 desk 操作的响应时间；结果写进回执 | `新Session修` | 若补库明显拖慢界面，是否按已同意的退路把补库限定在回基库后与开场前 | 待裁决 | |
| P3-04 | 中 | `docker/scripts/setup.sh:351-365`（按 `apps.json` 逐条 `install-app`，不区分 app）；`docker/apps.json:49-53`；`frappe_debug/hooks.py`（没有 `before_install`）；`rehearsal.js:6` 与 `scenario/quality.py:19-21`（只有这两处按站点名限制） | **没有任何机制阻止 `frappe_debug` 装进客户正式库。**`setup.sh` 用 `SITE_NAME` 建站后，把 `apps.json` 的每个 app 都装上，`frappe_debug` 在其中。开发守则要求客户正式库从空站新建，而 `setup.sh` 是唯一的建站装 app 脚本，用它建客户站就会装上 `frappe_debug`。装上后：全站每次插入都多一次 `Demo Progress` 查询；`switch_status` 对匿名访问开放；P3-05 的两个越权写方法也随之暴露。现在换库与快照能被拦住，只是因为客户站不会配 `root_password`、也不会有登记表，是间接保护，不是设计出来的守卫 | ADR-0013「客户正式库不装 `frappe_debug`」；需求 §4.4.8 末；本 Spec 特查项 2 | ① `frappe_debug` 加 `before_install`：站点配置没有显式标记（如 `frappe_debug_allowed: 1`）就拒装；② `setup.sh` 只在演示站或开发站装 `frappe_debug`（`apps.json` 加一个标记字段，或按站点名单） | `新Session修` | 守卫放在哪一层：app 自身的 `before_install`，还是 `setup.sh`／`apps.json`，或两层都做 | 待裁决 | |
| P3-05 | 中 | `scenario/rehearsal.py:13-37`（`prepare_act4_bom_recommendation`、`prepare_act5_operating_cost_account`：`@frappe.whitelist()`，没有 Administrator 校验）；`snapshot.py:54-56`（`snapshot_status` 无鉴权，且调 `registry.refresh()` 写登记表文件）；`demo/functions.py` 各写库方法用 `@frappe.whitelist()`，默认也接受 GET | **白名单方法的鉴权不一致，有两个现场写库方法任何登录用户都能调。**`prepare_act4` 用 `db.set_value` 改工位费率，并以 `ignore_permissions` 把另一份 BOM 设成默认；`prepare_act5` 用 `db.set_value` 改公司的 `default_operating_cost_account`。两者都绕过权限、不校验用户。`snapshot_status` 任何登录用户可读全部库名，每次调用还会改写登记表（cloning→ready／failed）。`make_quotation_for_deal`、`close_previous_month`、`prepare_cash_flow_worksheet` 等写库方法虽然校验 Administrator，但不限 POST：Administrator 登录时，一个顶层 GET 跳转就能触发结转（GET 不验 csrf）。演示站通常只有 Administrator，实际风险取决于 P3-04 | 方案 TS-024 第 2 条「服务端需要的查询……whitelisted，仅 Administrator」；需求 §4.4.8 末；本 Spec 特查项 2 | ① `scenario/rehearsal.py` 两个方法补 `_require_administrator()`；② `snapshot_status` 补 `_authorized()`；③ 凡写库的白名单方法改 `methods=["POST"]`（运行器经 `frappe.call`，默认 POST，不受影响）；④ 补一条非 Administrator 被拒的测试 | `本Session修` | — | 待裁决 | |
| P3-06 | 低 | `demo.yaml:181-183`（第 4 幕首步）、`:245-247`（第 5 幕首步）；`scenario/targets.py:34-58`；`scenario/rehearsal.py:13-37` | **第 4、5 幕现场第一步悄悄改主数据，方案没有这两步，讲解词也没说。**第 4 幕首步在观众面前把工位费率重写成场景值，并在默认 BOM 与成本推荐相同时，把另一份 BOM 设为默认，好让随后的「换用推荐」弹框一定出现；讲解词是「按场景工位费率核算 BOM，并保留原生推荐确认」。第 5 幕首步给公司补 `default_operating_cost_account`，讲解词是「完工费用按公司的存货结转科目自动入账」。生成器建主数据时已设过这个科目（`masters.py:56`），所以现场通常是空操作；但它让第 5 幕「费用科目自动带出」不完全依赖 frappe_china 的 HT-001 退路，演示证据因此打了折扣。方案 TS-024 的第 4 幕从「`set` 公司」开始，第 5 幕从「余下工序卡报工」开始 | 审核 Spec 预设 7（方案外夹带）；需求 §4.2 第 4 幕「生产计划推荐更便宜的 BOM 并请人确认」（推荐应来自场景数据，而不是现场改默认） | ① 两步挪进生成器 `finish_scenario_segment` 的 D1−1 段（`prepare_act1` 旁），现场配置删掉这两步；② 或保留，但在 D 回执补登偏离，并把讲解词改成不涉及内部动作的说法 | `新Session修` | 挪进生成器（要重跑预跑），还是保留并补登偏离 | 待裁决 | |
| P3-07 | 低 | `demo.yaml:183`「按场景工位费率核算 BOM，并保留原生推荐确认」、`:298`「打开 过程控制图并载入场景窗口」、`:309`「按 D2 所在月份的上月汇总计件工资」、`:328`「打开交货日为 D2 的场景订单」、`:434`「按场景终点执行每日计算」 | **五处讲解词向客户念出内部代号**：「D2」「场景终点」「场景窗口」「原生推荐」「场景工位费率」（第 298 行还多一个空格）。E 只查了禁词「今天」，没查这一类 | 需求 §4.15「用最终译名」；DEC-038「日期讲『这一天』『月初』」 | 改成观众能懂的说法，如「按上个月汇总计件工资」「打开这一天要交货的订单」「按这一天执行每日计算」；顺手 grep `D1|D2|场景|原生` 防复发（可加进 `test_demo_config`）。改讲解词按 RS-006 要重跑预跑 | `新Session修` | — | 待裁决 | |
| P3-08 | 低 | `runner.js:10-28`（`install_temporal_indicators` 包装全局 `frappe.get_indicator`，提交 `ae536a3`）；`README.md:15`；`frappe_china/README.md` 覆盖登记节 | **运行器替换了 desk 全局函数 `frappe.get_indicator`，方案里没有，也没有登记。**演示激活时，销售订单列表的逾期判定改成按场景日期算。行为合理，但开发守则要求替换或包装上游全局函数时逐处登记（覆盖位置、依赖的上游行为、失效症状、复验法），而 `frappe_debug` README 第 15 行写的是「本 app 不注册覆盖钩子」 | 开发守则「desk 与独立前端的覆盖逐处登记」；审核 Spec 预设 7 | `frappe_debug/README.md` 加一节「前端覆盖登记」：记 `get_indicator` 包装（依赖 `erpnext/selling/doctype/sales_order/sales_order_list.js:27` 用 `get_diff(delivery_date)` 判逾期），并改正第 15 行 | `本Session修` | — | 待裁决 | |
| P3-09 | 低 | `README.md:45`「九幕主用／备用／原始快照均为就绪状态」；`:50`「全部就绪再开始」；`:52`「右方向键或空格」；`:15`（同 P3-08） | **README 有三处与实现不符**：① 预跑结束时实际是 26 ready＋1 used（彩排页对此有说明）；② 停在第 1 幕主用库时就绪检查不可能全绿（与 P3-01 相连）；③ 空格键没有绑定，只绑了右方向键 | 需求 §七 预期使用流程；回执如实 | 跟 P3-01 的裁决一起改 README；空格键是补绑还是删掉这句，按用户习惯定 | `本Session修` | 空格键补绑，还是 README 删掉「或空格」 | 待裁决 | |
| P3-10 | 低 | `docker/backups/20261024_111641-…site_config_backup.json`、`保留-S8清洁基准/` 同名文件、`保留-S8R6-TS023前/…s8dev…json`（共三份含 `root_password`）；`sites/s8ts023preview.localhost/site_config.json`（仍有 `root_password`）；`dbops.py:126-143`（`drop_db` 不传 `-P` 端口） | **MariaDB root 口令的落点比方案说的多。**方案要求「口令不写进任何受管文件」：这三份备份在 `.gitignore` 内，不违规，但会随备份目录拷来拷去；隔离预跑站 `s8ts023preview` 用完没有撤回口令（D 在 s8dev 上每次都撤回）。这个口令是整个 MariaDB 容器的 root，演示站上任何 Administrator 会话里的代码都能借它操作 `test`、`s8verify` 等全部库。另：`drop_db` 不像 `clone_cmd`／`database_exists` 那样传端口，站点配了非默认 `db_port` 时会连错端口（现配置未设端口，无实际影响） | 总纲 §十 纪律 4「口令不写进任何受管文件」；README:37、62 | ① `s8ts023preview` 用 `bench set-config root_password None` 撤回（或整站删除，由用户定）；② README 注明 `backup.sh` 产出的 site_config 备份含 root 口令、勿外传；③ `drop_db` 补端口参数 | `本Session修` | `s8ts023preview` 是撤口令还是整站删除 | 待裁决 | |
| P3-11 | 观察 | `scenario/monthly.py:276-277`（只在 D1−1、D2−1、E−1 调 `clear_admin_list_filters`）；`runner.js:273-283`；frappe `list_view.js:593-605`；`model/utils/user_settings.py:30-61`；`hooks.py:264`（`sync_user_settings` 在 `hourly_maintenance`） | **快照前清列表设置，九个快照点里只有三处主动做**（片2 转交）。第 2～5、7、9 幕的快照是在前几幕彩排之后拍的，彩排里 `open_list` 设的筛选只写进 Redis 的 `_user_settings`，要等每小时的 `sync_user_settings` 才落库；演示期间 scheduler 关，所以没落进快照库；换库时又删了目标库前缀的缓存，现场看不到旧筛选。结论成立，但靠的是「scheduler 关」这条运行约束，不是代码保证。另：`open_list` 传 `filters: {}`（第 9 幕供应商评分）时，上游判 `filters.length === 0` 不清旧筛选，若库里有残留筛选会原样显示 | 需求 §4.9.3 第 11 条（OB-073） | 记录即可；若要代码保证：`take_snapshot` 克隆前调一次 `clear_admin_list_filters()`，`open_list` 在 `filters` 为空时显式清筛选 | `延迟或不修` | — | 待裁决 | |
| P3-12 | 观察 | `0-P1-S8文档/客户说明.pdf`（修改时间 2026-10-24 10:37）；`data/brochure_images/act*.png`（2026-10-24 01:43～02:17）；`act1.png` 右下 | 客户说明 9 页、无禁词，符合 SL-016 ④。但：① 截图早于 R7 的数据重生成（IT-012～014 改了供应商分布、拒收和期末需求），第 9 幕截图里的供应商价格与评分不是现在快照里的数；E 写的是「若截图有变再重生成 PDF」，没有做；② act1 截图右下四个「已提交」提示框叠在表单上，D 回执说缩略图无遮挡；③ PDF 文字层把部分汉字编成康熙部首码位（`pdftotext` 抽出「⼈」「⼀」「⽣」「客⼾」），屏幕上显示正常，客户复制文字会得到异体码 | 需求 §4.15；DEC-025 | 下次重跑预跑后重截第 6～9 幕并重生成 PDF；码位问题记作已知限制（属 wkhtmltopdf 字体映射，非本 app 逻辑） | `延迟或不修` | — | 待裁决 | |
| P3-13 | 观察 | `snapshot.py:51`（回 `{act, db, seconds, status}`）对总纲 §5.3（`{orig, elapsed_s}`）；`switch.py:124`（回值无 `route`） | §5.3 返回值形状漂移。`switch_to_act` 不回 `route` 已在 D 回执登记；`take_snapshot` 的键名改动没有登记，目前也没有消费方读它（`rehearsal.js:178` 只 await 不取值） | 总纲 §5.3 接口契约 | 在 D 回执偏离节补一行 | `延迟或不修` | — | 待裁决 | |

## 交接摘要

**本片依赖什么**

- **片2（生成器）**：各幕前置都要存在且唯一——`po_no=S8-ACT7`、`delivery_date=D2`、已提交的第 7 幕订单；E 当天 `act9_eoq_item`（`WIRE-65MN-3.0`）的 `EOQ` 建议处于 `Awaiting Decision`；至少一条未转换、没有商机的 CRM 线索；第 6 幕某工位 D2 后数周负荷超过 100%（`.text-danger` 格要存在）；`quality-plan.json` 覆盖第 7 幕出货检验的 `inspection_key`。`generate.json` 形状 `{job_id, state, day, error}` 及 IT-017 的重试读；`finish_scenario_segment` 在 D1−1／D2−1／E−1 清列表筛选（P3-11）；`frappe.flags.in_scenario_generator` 由 runner 置位（`scene_date.py` 据此跳过）；`load_scenario()` 在有工作库时取登记表的 `scenario_end` 冻结 E。`masters.py:56` 预设 `default_operating_cost_account`（P3-06 的第 5 幕首步因此通常是空操作）。
- **片1（frappe_china）**：报表名与筛选键——`Capacity Load`（`company/from_date/to_date/bucket`）、`Replenishment Strategy Comparison`（`company/period_1..3_from/to`，图表容器 `.chart-wrapper`）、`小企业资产负债表`（`company/fiscal_year/month`）、`小企业利润表`／`小企业现金流量表`（再加 `period_type`）；`spc-chart` 页的 `wrapper.spc_fields`／`wrapper.spc_load` 与 `.spc-summary` 里的 `Cpk:` 文字；侧栏 `Business Flow`（`workspace_sidebar/business_flow.json`）与 `?sidebar=Business%20Flow`（HT-011）；`production_plan.js` 弹框主按钮源词 `Use recommended BOM`；白名单 `replenishment.daily.run_now`、`replenishment_suggestion.adopt`、`piece_rate.make_for_period`（均为 `only_for` 角色）；`closing.generate_month_end_closing`；`Cash Flow Worksheet.get_cash_flow_items`；`website_translation` 的模板路径 `frappe_china/templates/independent_apps/crm.html`（`crm_inject.py:6` 硬认）；`install.TAIL_APPS` 含 `frappe_debug`；`stock_entry_accounts.unify_difference_account` 给空附加费用科目补 410199（第 5 幕「自动带出」的真正来源）。

**本片暴露什么**

- **`apply_scene_date`（回片1）**：`doc_events {"*": before_insert}`。上游 `document.py:1655` 先跑本 DocType 的钩子、再跑 `"*"`，所以它在 `job_card_scheduled_time` 之后执行；它只改 `scene_date_fields` 列出的**顶层**字段（Job Card 只列了 `posting_date`），而且只在字段值等于系统今天时才改，**不碰 `scheduled_time_logs` 子表的起止时间**；Job Card 没有 `set_posting_time` 字段，那一句不生效。排程行由工单 `planned_start_date` 推出：现场工单由 `create_work_orders_from_plan` 显式写 `场景日 08:30`；服务端代建的工单，`planned_start_date`（Datetime）在本钩子里只换日期、保留时分。片1 关心的排程截短不受影响。
- **前端场景时间**：新单 `posting_time` 固定为 `23:00:00 + (幕×60 + 步) 秒`（`runner.js:355-359`），同一场景日内按幕／步递增，跨午夜与刷新后不变。
- `Demo Progress` 单例（`act/step/refs/scene_date/active/base_db`），每份快照库一条；`active=1` 时 `apply_scene_date` 生效。注意：未迁移出这张表的站（如 `s8verify`）上，受场景日期管的单据 insert 会报 DocType 不存在，写入型探针要避开。
- 登记表 `private/frappe_debug/snapshots.json`；站点操作锁 `locks/frappe_debug_demo_operation.lock`（片2 的 `start_generate`／`_run_generate` 也取这把锁，`_run_generate` 等 10 秒）；补库串行锁 `locks/frappe_debug_refill.lock`（`flock` 命令，9p 挂载上跨进程有效，已探针）。
- 换库语义：改站点 `db_name`、清本进程站点配置缓存、删 Redis 目标库前缀键、把会话行抄进目标库；之后其它进程 60 秒内的行为以 HT-015 为准。
- 前端全局包装 `frappe.get_indicator`（P3-08）：演示激活时影响销售订单列表的状态标识。
- 事件协议 `erx_demo_step` 本片既不发也不收。

**留给收口比对的点**：ADR-0008 落点表说 `frappe_china` 有推送助手，grep 不到（片1 范围）；P3-04 的守卫若放进 `setup.sh`，与片1 的装序归位（6.2 段）相邻，要一起看。

## 总体判断

- **结果是否真满足源头意图**：部分满足。单场演示主路径（九幕、快照、快进、重来、跳幕、回基库、清理）落地且有整场预跑证据；关键缺口在多场演示：从基库无法开播（P3-01）、补库与换库抢锁会当着观众报错（P3-02）、IT-003 修复没有真实浏览器复测（P3-03）。安全面上，换库与快照接口本身守得住，但缺少「不进正式库」的设计性守卫（P3-04），另有两个写库方法没有鉴权（P3-05）。
- **状态值**：`有发现`

## 片内复核建议

1. **最该先看 P3-01 与 P3-02（代价最大）**。查法：读 `runner.js:499-503` 与 `transit.html:107`，确认回基库后运行器不再启动；再读 `operation.py:14` 与 `switch.py:156-172`，对照 `Spike/P1S8R8-F/p3/probes.log` 第二段（同进程另一线程 `timeout=0` 立即超时）。两条都没做端到端复现（不能碰 erx，s8dev 已不在）；若要实证，在 `s8ts023preview` 上「回基库后立即 `Alt+1`」各试一次即可。
2. **定级在边界上的**：P3-05 我定「中」，理由是越权写主数据；若确认演示站永远只有 Administrator 一个用户，且 P3-04 已加守卫，可降为「低」。P3-06 在「低／中」之间：它不让演示失败，但第 4 幕「推荐更便宜的 BOM」的效果部分是现场改默认 BOM 造出来的，严格读需求可升「中」。P3-11 定「观察」，前提是演示期间 scheduler 一直关；这条约束一旦破，就该升「低」。
3. **查得最浅的部分**：`crm_driver.js` 的主体与 `restore_work` 的分步失败恢复（D 自己也说主要靠单测）只读了相关段；Python 测试没跑，也没逐条审断言；客户说明只看了一张截图。
4. **开放找漏的盲区**：没往这些方向找——补库期间磁盘余量（10-25 曾磁盘写满致登记表卡在 cloning，`Spike/P1S8R7-E/reset_registry.py` 的注释提到）；容器重启后 `_clone_vanished` 的 pid 复用误判；多个浏览器标签同时开着 desk 时的换库（需求只要求单标签）；`bench serve` 多线程下 `frappe.conf.db_name` 在补库回调里被改写是否影响并发请求（读码看是请求本地 `frappe.local.conf`，未实测）。
5. **拿不准处**：P3-01 是不是「问题」取决于用户打算怎么开第二场——如果用户本来就打算场间不回基库、直接 `Alt+1`，那它只是 README 写错（降为低）；我按 README 现文、并结合方案 TS-019 ① 明文要求的入口缺失，定为中。P3-06 是否算「方案外夹带」：D 讨论记录与回执都没登记这两步，我判为夹带；但它们服务于已批准的第 4 幕剧情，也可读为「命名函数的实现细节」。
