# 审核报告·片3（对象：`frappe_china` @ `68233b9..acf97e6` 中负荷报表、SPC、收尾，及主仓库 S7 横切／审核标准：R03 需求文档＋R04 开发方案）

**轮次**：P1-S7-R7 F 片3｜**日期**：2026-10-16｜**执行者**：Claude（Opus 5.5，片 3 子 Agent）｜**打tag**：否
**依据**：[总纲](../R04-开发方案/P1-S7-R4-C开发方案-总纲.md)全文、[Part3](../R04-开发方案/P1-S7-R4-C开发方案-Part3.md)全文；[需求文档](../R03-需求文档/P1-S7-R3-B需求文档.md) §4.6、§4.11.1、§4.11.2、§4.13～4.18、§八 AC-012～015、AC-023
**线索（不当结论）**：[D 回执 Part3](../R05-代码/P1-S7-R5-D回执-Part3.md)、[E 确认报告](../R06-确认/P1-S7-R6-E确认报告.md)
**探针**：`Spike/P1S7R7-F/p3/`（`demo_readonly.py`＋`.log` 演示站只读；`spc_capacity_probe.py`＋`.log` 测试站只读、末尾 rollback；`translation_check.log` 两站译名自检）。未 migrate、未 run-tests、未 clear-cache，未写任何站点。

## 覆盖自证

- **查了**：`production/spc.py` 全文；`production_plus/report/capacity_load/*`、`report/spc_control_chart/*`、`page/spc_chart/*` 全文；`public/js/vendor/` 两文件（与 Insights 包逐字节比 sha256）；`workspace_sidebar/production_plus.json`／`stock_plus.json`、`modules.txt`、`.pre-commit-config.yaml`、`pyproject.toml` 的 diff；README 在本范围内的全部 diff；`zh.csv` 本范围 diff 全部新增行（片3 的约 40 行逐条看，其余只看排序与守卫）；`test_capacity_load.py`／`.cjs`、`test_spc.py`、`spc_data.py`、`test_spc_chart.cjs`、`test_translations.py` 与 `translation_whitelist.py` 的 diff；`install.py` 的 `after_migrate` 段与 `test_after_migrate.py`（IT-006 及 E 留给 F 的译名问题）。
- **横切查了**：主仓库 `bd4f91e..02771f5` 的 11 个 S7 提交逐个看 stat，`docker/` 下三处改动看 diff（`configure_apps.py` 另以 `-w` 比）；各提交里 `docker/apps.json` 的锁值；`开发守则.md`／`项目概况.md`／`业务规则.md`／`docs/README.md`／`CLAUDE.md` 在 S7 的改动；`Spike/P1S7R5-D`、`Spike/P1S7R6-E` 全部文件清单与编码；演示站只读快照与容器内长跑进程启动时刻、web 重载日志。
- **跳过**：没看截图像素内容（只核文件在、核 `ts016-ui-result.json` 记录的颜色与规则）；工作中心筛选只验 SQL 可执行，没有造带工位的 Job Card 检验单验结果（D 复核建议已说明未测）；Python 全量未自跑（主会话同时在跑，按要求不跑），全量数字引自主会话 `Spike/P1S7R7-F/python-full.log`，已读该日志核对；Part1／Part2 范围的代码（补货、拆单、级联、计件）只在集成点上读，不审。
- **片间**：本片消费片 2 的 Job Card 改写与片 1 的 `install.py` 自检；见文末交接摘要。

## 逐项落地核查

落地＝代码在；生效＝真被调用、未被绕过；根因＝原问题消失。

| 方案任务 | 要求层要求 | 定位 | 落地 | 生效否 | 偏差说明 |
|---|---|---|---|---|---|
| TS-014 | Report `Capacity Load`：Production Plus、Script Report、`ref_doctype` Job Card、三角色 | `capacity_load.json:2-5` | ✅ | ✅ 演示站 `tabReport`、`Has Role` 只读查到 | — |
| TS-014 | 英文源词报表名、中文进 csv | `zh.csv`「Capacity Load,产能负荷」 | ✅ | ✅ | — |
| TS-014 | company／from／to 必填；bucket ∈ Day/Week/Month 默认 Week；工作中心多选 | `capacity_load.py:27-36`；`.js:3-7` `MultiSelectList` | ✅ | ✅ | — |
| TS-014 | `_buckets`：周桶周一起、首尾截断 | `capacity_load.py:9-22` | ✅ | ✅ 探针三种桶真跑 `execute`：日 4 行、周标签 10-26／11-02、月 10-01／11-01 | 桶标签取自然周一／月一，首桶截断时标签早于筛选起日（P3-12） |
| TS-014 | `_demand`：company、docstatus≠2、status∉{Completed,Cancelled}、workstation in、非纠正卡、开工日在区间或为空 | `capacity_load.py:48-71` | ✅ | ✅ | — |
| TS-014 | remaining＝time_required×(1−完工/for_quantity)，for_quantity≤0 记 0，max(0,…) | `:72-77` | ✅ | ✅ 手算 (600＋480×0.5)/60＝14.00 与单测一致 | — |
| TS-014 | `_capacity`：Σhours×production_capacity，不看 enabled；假日表扣日；holiday_list 空不扣 | `:79-101` | ✅ | ✅ 手算 4 天×(4＋4)×2＝64 | 不读 `allow_production_on_holidays`（P3-12） |
| TS-014 | 行：工作中心×桶，外加需求非零的「未排期」行 | `:96-123` | ✅ | ✅ | — |
| TS-014 | 列六个（需求／产能 Float 2 位、负荷率 Percent、备注「无产能」「未排期」） | `:124-137` | ✅ | ✅ 探针 zh 列头：工站、时间桶、需求工时、产能工时、产能负荷率、备注 | — |
| TS-014 | chart bar，datasets＝[需求合计, 产能合计] | `:138-159` | ✅ | ✅ | 未排期需求不进图（方案未要求） |
| TS-014 | 标红：js formatter，>100 包 `text-danger` span，不写内联色 | `capacity_load.js:9-16` | ✅ | ✅ Node 1/1 | — |
| TS-014 验证 | 单测 ①②④～⑦；③ Node | `test_capacity_load.py`、`.cjs` | ✅ | ✅ 主会话全量内 2/2；Node 自跑 | ⑦ 只对 `_buckets` 断言，`execute` 的日／月桶未在单测里跑（本片探针补跑） |
| TS-015 | `D2` 表 n＝2…10、`MIN_SUBGROUPS`＝25 | `spc.py:10-11` | ✅ | ✅ 常数逐个对标准表无误 | — |
| TS-015 | `Subgroup`／`SpcResult` TypedDict 字段 | `spc.py:20-45` | ✅ | ✅ | — |
| TS-015 | `load_subgroups`：docstatus=1、物料、参数、可选日期／类型／工作中心（join Job Card）；按日期、单名排序；空白跳过、非数字计剔除；全空行不成组 | `spc.py:149-190` | ✅ | ✅ 单测 abc＋空白 → 剔除 1；探针工作中心筛选 SQL 可执行 | 工作中心有数据场景未测（D 已自述） |
| TS-015 | 规格限：0 视为未设；各行不一致取最后一组并记 note | `spc.py:188-190` | ✅ | ✅ 单测改末行上限 16 → (16,5)＋note | — |
| TS-015 | `compute`：X̿、R̄、σ组内＝mean(R/d₂(n))、σ总体＝stdev(全部读数含 n＝1) | `spc.py:102-107` | ✅ | ✅ 见下方手算例 | — |
| TS-015 | Cpk／Ppk 同式、单侧取单侧、两侧都无为 None 并记 note | `spc.py:111-124` | ✅ | ✅ 探针只给 USL 时 Cpk＝1.134791 与手算一致 | 单测的单侧用例判别力不足（P3-06） |
| TS-015 | z＝(X̄−X̿)/(σ/√n)，n＝1 组 z、rules 为空不进图；n＞10 不进 X̄-R 并记 note | `spc.py:102,109-110,126-130` | ✅ | ✅ | — |
| TS-015 | `nelson` 8 条及窗口、标末点 | `spc.py:48-81` | ✅ | ✅ 逐条对方案判式：1 `>3`；2 九点同号且≠0；3 六点严格单调；4 十四点相邻差乘积全负；5 三中二 `>2` 同侧；6 五中四 `>1` 同侧；7 十五点 `<1`；8 八点 `>1` | 规则 8 同侧也命中（照需求「两侧均可」，P3-09） |
| TS-015 | `signals`＝判异点数 | `spc.py:143` | ✅ | ✅ | — |
| TS-015 | README 写「窗口规则标末点」 | README 已知限制末条 | ✅ | — | — |
| TS-015 | Report `SPC Control Chart`：五筛选、摘要六项＋样本不足、表六列、line 图逐点 UCL/LCL | `spc_control_chart.py`、`.js:2-9` | ✅ | ✅ 单测摘要与接口同值 | — |
| TS-015 | 报表按钮「打开控制图」带筛选进 URL query | `spc_control_chart.js:10-12` | ✅ | ✅ `set_route` 的对象参数经 `router.js:461-463` 成 `route_options` 并拼进 query；`ts016-ui-result.json` 记录跳转后筛选值 | — |
| TS-015 验证 | 单测 ①～⑤、16 个 Nelson 用例、站上造检验单 | `test_spc.py` | ✅ | ✅ 主会话全量内 3＋1 条 | — |
| TS-016 | vendor：原样复制 echarts 5.6.0 与 LICENSE；README 写来源／版本／Apache-2.0；pre-commit 排除 | `public/js/vendor/`、README 许可节、`.pre-commit-config.yaml:1` | ✅ | ✅ 两文件 sha256 与 Insights 包相同 | NOTICE 与 LICENSE-d3 未带（P3-05） |
| TS-016 | Page `spc-chart`（Production Plus、标题源词、角色） | `spc_chart.json` | ✅ | ✅ 演示站 `tabPage`、`Has Role` 查到 | — |
| TS-016 | `get_chart_data` whitelist、QI read 权限、与报表同一函数 | `spc.py:193-201`；报表 `:9` | ✅ | ✅ 单测 Guest 被拒 | — |
| TS-016 | 前端：五筛选、`route_options` 取初值、`frappe.require` 加载、逐点着色、虚线 UCL/LCL、tooltip 含规则 | `spc_chart.js:3-91` | ✅ | ✅ Node 1/1；D 浏览器取证 ECharts 实例 28 点、两色 | — |
| TS-016 | 颜色取 CSS 变量、不写死；摘要区；文案 `__()` 进 csv | `spc_chart.js:4-6,57-62`；csv | ✅ | ✅ | — |
| TS-016 验证 | 28 子组含两处判异、截图两张；`get_chart_data` 与 `execute` 同值 | `Spike/P1S7R5-D/ts016-*` | ⚠️ | ✅ | 取证数据 21/28 点判异，不是「两处」（P3-10） |
| TS-017 ① | README：模块边界两模块两包及判据 | README `:17-21` | ✅ | — | — |
| TS-017 ① | README「后端覆盖登记」节（拆单一行） | README `:114-118` | ✅ | — | — |
| TS-017 ① | README「按某日计算」四条与两入口全名 | README `:228-237` | ✅ | — | 与总纲 §5.2 逐条一致 |
| TS-017 ① | README 已知限制七项 | README `:196-202` | ✅ | — | 七项齐 |
| TS-017 ② | 全量 Python／Node 只增不减全过；两条译名测试；两站 `translation_check.run` | 见验证门表 | ✅ | ✅ | — |
| TS-017 ③ | 演示站：`check_app_order` ok、未新增 Error Log、`auto_indent`＝0、计件工资、两空侧栏 | 本片只读快照 | ✅ | ✅ | migrate 实际产生过 47 条 Error Log，D 按清单正向删除并如实记录；其中 45 条源自 TS-010 写演示站（P3-01） |
| TS-017 ④ | 演示站业务数据与 `Translation` 为 0 | 本片只读快照 | ✅ | ✅ | — |
| TS-017 ⑤ | 365 天回放耗时 | D／E 回执 | ✅ | ⚠️ | 片 1 范围（E IT-005 已重跑），本片不复核 |
| TS-017 4.2 | 备份另存 `docker/backups/保留-S7上线前/` | 目录四件套在、`.gitignore:5` 不入库 | ✅ | — | — |
| TS-017 4.5 | `bench start` 日志仍写 `frappe-bench/logs/bench-start.log` | `ts017-bench-start.sh`；容器内文件在 | ✅ | ✅ | — |
| TS-017 5 | 常驻文件：工具链 Ruff 行；长效约定候选列进回执 | `开发守则.md` 工具链表 | ⚠️ | — | Ruff 行已改且与实测一致；回执「新增约定：无」，至少两条长效坑未列为候选（P3-01、P3-02），项目概况未改（P3-08） |
| SL-001 横切 | `modules.txt` 两模块；两空侧栏 json、`modified` 有值 | 各文件 | ✅ | ✅ 演示站 Module Def 两条、侧栏 0 项、无自动 Desktop Icon | — |
| SL-002 ①（IT-006） | 自检通过时 migrate 输出「通过」 | `install.py:152-155` | ✅ | ✅（读码）| 「无对象」那条通过时不打印（P3-04）；标题未译（P3-03） |

**手算例（本片独立，`spc_capacity_probe.log` 对照）**：四组 [1,3]、[2,4,6]、[3,5,7,9]、[5]，只有 USL＝12。
- multi＝前三组；X̄＝2、4、6 → X̿＝4；R＝2、4、6 → R̄＝4。
- R/d₂＝2/1.128＝1.773050、4/1.693＝2.362670、6/2.059＝2.914036 → σ组内＝7.049756/3＝**2.349918**（实测 2.34991847）。
- 全部 10 个读数均值 4.5，离差平方和 52.5，/9＝5.833333 → σ总体＝**2.415229**（实测 2.41522946）。
- Cpk＝(12−4)/(3×2.349918)＝**1.134791**；Ppk＝8/(3×2.415229)＝**1.104105**（实测一致）。若下限缺失被当成 0，Cpk 会是 4/7.05＝0.567，实测排除了这种实现。
- z₁＝(2−4)/(2.349918/√2)＝**−1.203628**（实测一致）；n＝1 组 z 为空。
- 子组数 3＜25 → `insufficient` 真。

## 验证门实跑结果

| 门 | 声称值（E 修后） | 实测值 | 与基线对比 | 一致否 |
|---|---|---|---|---|
| Node `node --test frappe_china/tests/*.cjs`（宿主 Node v24.13.1，在 `apps/frappe_china` 下） | 89/89 | **89/89**，fail 0、skip 0，145.8ms | TS-001 基线 86 → 89 | ✅ |
| Ruff `env/bin/ruff check apps/frappe_china`（容器，0.14.10） | 全过 | **All checks passed!**，退出 0 | 基线 0 告警保持 | ✅ |
| Ruff `format --check apps/frappe_china` | 161 文件 | **161 files already formatted**，退出 0 | — | ✅ |
| Python 全量（主会话跑，本片只读日志 `Spike/P1S7R7-F/python-full.log`） | 349/349 | 341＋5＋3＝**349**，均 OK，`EXIT=0`；其中 `test_capacity_load` 2/2、`test_spc` 1＋3、`test_translations` 20/20、`test_translation_quality` 13/13 | TS-001 基线 283 只增不减 | ✅ |
| `translation_check.run` 两站 | 通过 | test、erx 均「译名自检通过」（`p3/translation_check.log`） | — | ✅ |
| 演示站 `check_app_order()` | ok | `ok`、`order_ok`、`overrides_ok`、`translation_ok`、`company_checks_ok` 全真，`problems` 空 | — | ✅ |

## 集成检查

| 集成点类型 | 具体落点 | 两端一致否 | 说明 |
|---|---|---|---|
| 跨模块数据流 | 片2 拆单／级联改写 Job Card `for_quantity`、`time_required`、`scheduled_time_logs` → 负荷报表需求侧 | ✅ | 报表只读 `time_required`、`for_quantity`、`total_completed_qty`、`expected_start_date`；A14 同时改时长与排程末行，`for_quantity`＝0 的卡需求记 0（`capacity_load.py:72-76`），与总纲偏离 4 一致。`expected_start_date` 来自原生 `set_expected_and_actual_time`（`job_card.py:926-950`），只在开了产能排程时有值（P3-12） |
| 跨模块数据流 | Quality Inspection（`docstatus=1`、`readings`、`reference_type`＝Job Card）→ SPC | ✅ | 读端字段与 `quality_inspection.json` 一致；`inspection_type` 选项与原生相同 |
| 接口契约 | 报表 `execute` 与页面 `get_chart_data` 共用一函数 | ✅ | `spc_control_chart.py:9` 直接调 `get_chart_data`；单测断言 Cpk、Ppk、判异点数相同 |
| 接口契约 | 报表 → 页面的筛选传递（`route_options`） | ✅ | 写端 `set_route("spc-chart", 对象)`，读端 `on_page_show` 取 `frappe.route_options` 后置空 |
| 共享状态 | `zh.csv`、`translation_whitelist.py`、`hooks.py.after_migrate` | ✅ | csv 按 casefold 排序、无重复键（测试过）；`after_migrate` 顺序见 P3-11 |
| 共享状态 | `docker/apps.json` 锁 | ✅ | 现锁 `acf97e6`＝`frappe_china` HEAD＝`origin/main`；历史滞后一次见 P3-13 |
| 事件／消息 | 不涉及 | — | 本片无 SSE、realtime 事件 |
| 跨 Phase 契约（开发守则 §13 唯一一条：演示操控事件协议） | 不涉及 | — | S7 未改 `erx_demo_step` 推送侧 |

## 业务规则合规核

| 规则条款 | 本 Round 改动是否涉及 | 结论 | 备注 |
|---|---|---|---|
| BR-001～BR-007（会计准则、报表、税率、价税分离、结转、附加税） | 否 | 合规（未触及） | 负荷与 SPC 不产生会计分录；需求 §4.17 已判本 Stage 不新增不变量 |
| 新增／变更规则检出 | 否 | — | Cpk／Ppk、Nelson、负荷口径是算法口径（需求 §4.17），本片未发现被写成领域不变量 |

## 自证复核

| 被审产物声称 | 实际复核结果 | 一致否 |
|---|---|---|
| D：TS-014 需求 14h、产能 64h、负荷 21.875% | 手算一致；单测在全量内 | ✅ |
| D：TS-015 X̿＝10、σ组内＝1.450512682、Cpk＝1.149019024 | 按 13×(2/1.693)＋13×(4/2.326) 均值复算一致；但该数据测不出 X̿ 定义与单侧处理（P3-06），本片另做非对称手算例 | ✅（判别力弱） |
| D：ECharts 与 LICENSE 字节一致 | sha256 两项与 Insights 包相同 | ✅ |
| D：28 子组、两种颜色、规则 1／2 | `ts016-ui-result.json` 两色、28 点，但 21 点判异 | ⚠️（P3-10） |
| D Part2：TS-010「浏览器临时数据、6787 服务及 hosts 标记已清」 | 演示站曾留 `_FCT_TS010_UI_1792088513074` 与两批次（Part3 才清），45 条 Error Log 的 referrer 为 `test.localhost:8000` | ❌（P3-01） |
| D：首次 migrate 因模块映射旧缓存未注册新 DocType | 读码成立（`frappe/__init__.py:225` 在 `in_migrate` 置位前按 `app_modules` 缓存建表，`model/sync.py:116` 用它） | ✅（但未进守则，P3-02） |
| D：「新增约定：无」 | 至少 P3-01、P3-02 两条是长效坑 | ❌ |
| E：IT-006 修后通过时打印 | 读码：`install.py:152-155` 在 `ok` 为真时打印 `PASS_MESSAGE`；单测断言 | ✅（「无对象」提示不打印，P3-04） |
| E：修复已上演示站长跑进程 | `bench start` 于 10:27 UTC 起；E 改 `rules.py`／`install.py`／`demand.py` 于 11:43～11:57，`bench-start.log` 记 web 进程 11:42～11:57 五次检测到改动重载，末次 11:57:38 晚于最后一次源码改动 11:57:08；`acf97e6` 无 json／js 改动，不需 migrate、build。worker 按 rq fork 子进程现取代码（读码推断，未实证）；演示站 scheduler 关 | ✅（worker 为推断） |
| TS-017：演示站业务数据 0、`Translation` 0、`auto_indent`＝0、计件工资、两空侧栏 | 本片只读快照全部成立；`Error Log` 自 D 最终快照后新增 0；无自检告警通知 | ✅ |

## 问题清单

片内编号 `P3-`，收口时改编 `FD-`。

| # | 严重程度 | 定位 | 问题描述 | 违背的标准/意图 | 建议 | 建议档位 | 待裁决点 | 状态 | 用户裁决 |
|---|---|---|---|---|---|---|---|---|---|
| P3-01 | 中 | `Spike/P1S7R5-D/s7-erx.localhost-before.json:8`；`ts017-deferred-errors.json`（45 条 referrer 为 `http://test.localhost:8000/desk…`）；`ts017-clean-demo.py:5`；D 回执 Part2 第 36 行 | TS-010 的浏览器取证首版连的是 `test.localhost:8000`，而 8000 上的 `bench serve` 按 `default_site` 只服务演示站。结果在 `erx.localhost` 建了物料 `_FCT_TS010_UI_1792088513074`（时间戳 2026-10-15 18:21 UTC）与两个批次，并留下 45 条请求失败（缺 `cn_unit_length_m` 列等），首次演示站 migrate 时才从 deferred 队列刷进 Error Log。Part2 回执写「浏览器临时数据…已清」，没提写过演示站；Part3 才清掉物料、正向删 47 条日志。演示站现已干净（本片只读快照：物料 0、批次 0、自 D 最终快照后新增日志 0）。`ts016-ui.cjs:10`、`ts017-demo-ui.cjs:9` 已加 `frappe.boot.sitename` 断言，`ts010-ui.cjs` 现版本仍没有 | 总纲纪律 4「TS-001～016 不得对 `erx.localhost` 做任何写操作」；开发守则「静默失败」与回执如实 | ① 开发守则补一条长效约定：浏览器探针连上后、任何写之前先断言 `frappe.boot.sitename`（auto-memory 里已有「8000 只服务演示站」，但守则没有）；② Part2 回执 TS-010 行补一句更正，指向 Part3 第 47 行 | `本Session修` | — | 待裁决 | |
| P3-02 | 中 | D 回执 Part3 第 34 行；`frappe/__init__.py:225`、`frappe/model/sync.py:116` | 改了 `modules.txt` 后的第一次 `bench migrate` 退出 0，却不同步新模块的 DocType／Report／Page：`frappe.init` 按 Redis 里旧的 `app_modules` 建模块表（此时 `in_migrate` 还没置位），`sync_for` 只遍历这张表；`Migrate.setUp` 的 `clear_cache` 晚于此。D 靠先 `clear-cache` 再 migrate 解决，没写进守则，`check_app_order` 也测不出。客户正式库首装 S7 时会照样踩：migrate 成功、报表与单据不存在 | 开发守则「断言机制可用前写入端与读取端两侧都要查」；TS-017 第 5 条「长效约定列为候选」 | ① 开发守则补一条：改 `modules.txt` 后先 `bench --site <站> clear-cache` 再 migrate，并以 `Module Def`／`tabDocType` 计数验注册；② 可选：`docker/scripts/setup.sh` 在 migrate 前加一次 `clear-cache` | `本Session修` | 只写守则，还是另改 `setup.sh` 与（或）在 `check_app_order` 加「`modules.txt` 每个模块在 `Module Def` 里有」一项（后者会改片1 的自检，宜 `出方案修`） | 待裁决 | |
| P3-03 | 低 | `install.py:8,161,172` | E 留给 F 的那条：`ALERT_TITLE`「frappe_china override self-check failed」既不在 csv、也不在官方词典，Error Log 标题与站内通知显示英文。另两处使它即使进 csv 也不生效：① 常量名不以 `SOURCE` 结尾，`_app_source_strings()` 收不到，译名守卫查不出缺译（开发守则「译名自检时机」第 3 段）；② migrate 进程 `frappe.local.lang` 是 `en`（`frappe/__init__.py:201`，站点未配 `lang`），`_()` 不带 `lang="zh"` 时取英文。方案原写「经 `_()`」，目的就是可译。通知正文（problems）是中文，标题英文，同一条通知中英混排 | 总纲 A16；开发守则「站点自检函数的形态」（结论与语言有关须显式按 `zh` 取） | 常量改名 `ALERT_TITLE_SOURCE`、进 csv（如「frappe_china 覆盖自检未通过」），两处调用改 `_(…, lang="zh")`；`PASS_MESSAGE` 同理或登记进白名单说明只给终端看 | `本Session修` | 要不要译：该串只给管理员看、不在演示屏单内。选「译」按上条改；选「不译」则登记进 `translation_whitelist.py` 写明理由，并把 `_()` 去掉免得误导 | 待裁决 | |
| P3-04 | 低 | `install.py:152-155`；总纲偏离 17 | 站上无中式公司时 `ok` 为真，`after_migrate` 只打印 `passed`，`problems` 里那条「站上没有中式公司，建账自检无对象」不打印。偏离 17 写「『无对象』那条只打印、不写 Error Log、不发通知」 | 总纲 §四 偏离 17 | 通过分支在打印 `PASS_MESSAGE` 之后逐条打印 `problems`（此时只可能是提示类） | `本Session修` | — | 待裁决 | |
| P3-05 | 低 | `public/js/vendor/`；README 许可节 | 只带了 echarts 的 `LICENSE`。同包另有 `NOTICE`（Apache-2.0 第 4(d) 款要求再分发时保留）与 `licenses/LICENSE-d3`（`LICENSE` 第 216-221 行指向它，d3 部分为 BSD-3）。方案只要求带 `LICENSE`，执行照方案做了，缺口在方案 | Apache-2.0 §4(d)；需求 §4.11.2「引入新前端依赖须锁版本」的许可面 | 把 `NOTICE` 与 `LICENSE-d3` 原样复制进 `vendor/`（建议名 `ECHARTS-NOTICE`、`ECHARTS-LICENSE-d3`），README 许可节补一句 | `本Session修` | 是否在方案外补这两份文件（不补则对外交付前的法务复核须覆盖，README 已有该提示） | 待裁决 | |
| P3-06 | 低 | `tests/test_spc.py:203-241` | SPC 常量算例的 26 个子组均值都是 10、规格 5／15 对称，三处口径都分辨不出：① X̿ 取「组均值之均值」还是「全部读数均值」（n 不等时两者不同）；② 单侧用例 `compute(groups, 15, None)` 与双侧得数相同，把缺失下限当 0 的错误实现也会通过；③ Ppk 中心用 X̿ 还是总体均值。实现本身是对的（本片非对称手算例逐式一致），缺的是测试判别力 | 开发守则「判据必须能区分它要区分的两种情形」 | 把本报告的手算例（[1,3]、[2,4,6]、[3,5,7,9]、[5]，USL＝12）写成常量用例：X̿＝4、σ组内＝2.349918、σ总体＝2.415229、Cpk＝1.134791、Ppk＝1.104105、z₁＝−1.203628 | `本Session修` | — | 待裁决 | |
| P3-07 | 低 | 主仓库 `a3e39f2` 的 `docker/scripts/configure_apps.py` | 这次 feat 提交顺手把整份 `configure_apps.py` 从 Tab 缩进改成 4 空格并按行宽重排（全量 diff 660 行，`-w` 后只剩 102 行，真正的改动是新增 `configure_stock` 与一处调用）。方案的格式基线只覆盖 `frappe_china` 仓库（DEC-020 要求基线独立提交），主仓库脚本的格式化不在方案内，且和功能改动混在一个提交里，`git blame` 失真 | 审法纪律 7（方案外夹带）；DEC-020 的「格式与功能分开」精神 | 不回退（已推送，回退代价更大）；在本报告留档即可。今后主仓库脚本格式化另起提交 | `延迟或不修` | — | 待裁决 | |
| P3-08 | 低 | `docs/项目概况.md:68`；同文件自有 app 一行 | 「演示站当前状态」仍是 S6 收口（2026-10-14）：没写 S7 上线后的两个新模块、两张报表与控制图页面、`计件工资` 组件、`auto_indent`＝0、新清洁基准 `docker/backups/保留-S7上线前/20261016_162704`（及其含 TS-010 残留、恢复后须再清这一注意事项）。自有 app 一行的「现有」也没有 S7 的块。按方案 TS-017 第 5 条与 Workflow，这属 Stage 收口步要做的，F 时点尚未到期 | 常驻文件契约（演示站状态以项目概况为准，TS-017 前后基线核对引的就是这一段） | Stage 收口时按常驻文件契约更新这两处 | `延迟或不修` | — | 待裁决 | |
| P3-09 | 观察 | `production/spc.py:78-80` | Nelson 规则 8 照需求「两侧均可」实现，8 点全在 +1σ 外的同侧序列也命中（探针 `[1.5]*8` → `[6, 8]`）。经典定义（Nelson 1984）是 8 点都不在 ±1σ 内**且两侧都有**，用来抓混合分布；同侧情形已由规则 2／6 覆盖。照字面做的后果是同侧偏移会被 6、8 双重标出 | 需求 §4.11.2 第 8 条字面 vs 规则原意 | 维持现状并在 README 已知限制写一句；或改为「两侧都有」 | `延迟或不修` | 保留需求字面，还是改回经典定义（改则要同步需求与测试） | 待裁决 | |
| P3-10 | 观察 | `Spike/P1S7R5-D/ts016-site-data.py:9-11`；`ts016-ui-result.json` | 方案要求取证数据「含两处判异：一点越 3σ、一段连续 9 点同侧」，实际组内极差 0.2 使 σ 很小，28 点里 21 点判异（规则 1、5、6、8 大面积命中）。SL-011 ⑥ 只要求异色与悬停显示规则，已满足；但截图看不出「少数异常点被挑出来」的演示效果，演示造数（S8）会碰到同样问题 | Part3 TS-016 验证方式 | 不重拍；S8 造 SPC 演示数据时组内波动与组间偏移按 σ 比例设计 | `延迟或不修` | — | 待裁决 | |
| P3-11 | 观察 | `hooks.py:116`；`production/piece_rate.py:23-35` | `after_migrate` 先跑 `piece_rate.ensure_component` 再跑自检；`ensure_component` 没有 try，若 `Salary Component` 插入抛错（如 HRMS 校验变化），migrate 在自检之前中断，自检「不中断 migrate」的设计被它绕过。现两站都已有该组件，走的是 `exists` 早退 | 需求 §4.6 第 3 条「不 raise、不中断 migrate」（针对自检；此处是相邻钩子） | 对调两项顺序，或给 `ensure_component` 的 after_migrate 入口包一层只告警的 try | `延迟或不修` | — | 待裁决 | |
| P3-12 | 观察 | `capacity_load.py:13-21,66`；`job_card.py:926-950` | 三处口径记录：① 首尾桶截断时桶标签取自然周一／月一（如筛选 10-30 起、周桶标 10-26），不是筛选起日；② 未排期行的桶键是英文 `Unscheduled`，只在前端 formatter 里换中文，导出 Excel 时显示英文；③ `expected_start_date` 只在开了产能排程时由原生写入，测试站 `disable_capacity_planning`＝1、演示站为 0，关排程的站点所有卡都进「未排期」；④ 产能侧不读 `Manufacturing Settings.allow_production_on_holidays`（原生 `workstation.py:204-213` 开了它就不跳假日），两站该项均为 0，现无差异 | 需求 §4.11.1 | ①② 维持；③ 写进 README 已知限制一句，S8 造数前核演示站该开关 | `延迟或不修` | — | 待裁决 | |
| P3-13 | 观察 | 主仓库 `fea1737`（锁仍 `874d3d1`）→ `6a82ea4` | 提交卫生：① D 回执 Part3 说 app 提交 `e1b5621` 已推送、主仓库同步提交，但 `fea1737` 没改 `docker/apps.json`，锁滞后到下一次提交 `6a82ea4` 才跳到 `61e94cf`，`e1b5621` 从未被锁过；期间按锁重建会拿不到 TS-013～016。② `frappe_china` 的 `39b2cec`～`e1b5621` 由 Codex 执行、无 `Co-Authored-By`，`61e94cf`、`acf97e6` 由 Claude 执行、带该行；作者都是 `PhilixKuro`，与用户账号一致，执行者在各回执头部写明，归属可追。③ 各提交信息与内容相符；其余 7 次锁与提交说明一致。现锁 `acf97e6` 与 app HEAD、`origin/main` 一致 | CLAUDE.md 版本管理；总纲纪律 9 | 不补救（已被后续提交覆盖），留档 | `延迟或不修` | — | 待裁决 | |
| P3-14 | 观察 | `Spike/P1S7R5-D/` | 受管目录卫生：无长跑进程日志写进 Spike（`ts016-server.sh`、`ts017-bench-start.sh` 均写 `frappe-bench/logs/`），无 `__pycache__`、无大体积可重生成产物（最大 json 36 KB，是删日志用的身份清单，须留）。两点记录：① `ht011-probe.log`、`ht012-probe.log` 是 UTF-16 LE（PowerShell 重定向），git 当二进制存，不可 diff；② `ts014-016-check.sh`、`ts017-full-check.sh` 名为 check，实际先跑 `ruff check --fix` 与 `ruff format`（会改 app 文件），`update-s7-translations.py` 直接改写 `zh.csv`。`Spike/P1S7R6-E/` 全为脚本与依赖当时站点状态的输出，无应删项 | 开发守则「长跑进程的日志不写进受管目录」；auto-memory「提交前删可重生成产物」 | 不改；今后取证日志用 UTF-8 写 | `延迟或不修` | — | 待裁决 | |

**E 留给 F 判的那条**（`frappe_china override self-check failed` 不在 csv、显示英文）：判为发现 P3-03，低。理由是方案明写「经 `_()`」，意图可译；但它同时有守卫盲区与 migrate 进程语言两个问题，单补 csv 不会生效。

**IT-006 修复**（读码判，未 migrate）：成立。`install.py:152-155` 在 `ok` 为真时打印 `frappe_china override self-check passed` 后返回，`test_after_migrate.py:31-40` 断言只打印这一行、不写 Error Log。剩余偏差见 P3-04。

## 交接摘要

**本片消费（依赖别片）**

| 来源 | 消费什么 | 读端定位 | 依赖的不变量 |
|---|---|---|---|
| 片2 TS-011 拆单 | 每张 Job Card 的 `for_quantity`、`time_required`（上游按 `time_in_mins ÷ 工单 qty × 卡数量` 算） | `capacity_load.py:57-77` | 拆单后各卡 `time_required` 之和＝整单工时 |
| 片2 TS-012 级联 | `_set_card_qty` 经 `db.set_value` 同改的 `for_quantity`、`time_required`、`scheduled_time_logs` 末行 | 同上 | 级联后 `time_required` 与新数量同比例；扣到 0 的草稿卡 `for_quantity`＝0 留在库里（偏离 4），本表按 0 计 |
| 原生排程 | `expected_start_date`（`job_card.py:926-950` 由 `scheduled_time_logs` 汇出） | `capacity_load.py:66-71` | 开了产能排程才有值（P3-12 ③）；级联只改排程末行的止时，不动 `expected_start_date` |
| 原生质检 | Quality Inspection `docstatus=1`、`readings.reading_1..10`、`min_value`／`max_value`、`reference_type`＝Job Card 时的 `workstation` | `spc.py:153-171` | — |
| 片1 TS-003 | `check_app_order()` 与 `after_migrate`（本片判 IT-006 与 P3-03／04） | `install.py:47-177` | — |
| 片1 TS-002 | `modules.txt` 的 `Production Plus` 模块注册 | 两张报表、页面的 json `module` | 见 P3-02 的首次 migrate 缺口 |

**本片暴露（供别片与 S8）**

- `frappe_china.production.spc.get_chart_data(filters)`（whitelist，QI read）、`load_subgroups`、`compute`、`nelson`；`SpcResult` 结构。报表与页面共用。
- Report `Capacity Load`（`execute(filters)` 返回四元组，含 bar 图）、Report `SPC Control Chart`（五元组，含 `report_summary`）、Page `spc-chart`（经 `frappe.route_options` 收筛选）。
- 静态资源 `/assets/frappe_china/js/vendor/echarts-5.6.0.min.js`。
- README「按某日计算」四条（S8 生成器须遵守）与「后端覆盖登记」节。

**依赖的共享文件条目**

- `translations/zh.csv`：本片新增约 40 行（Capacity／SPC／控制图相关），按 casefold 排序。
- `tests/test_translations.py:204-206`：`_app_source_strings()` 跳过 `public/js/vendor/`，否则 minified echarts 的 `__` 片段被当源词。别片若在 `vendor/` 下放自有文件，会被一并跳过。
- `hooks.py:116` `after_migrate` 顺序（P3-11）。
- `.pre-commit-config.yaml:1` 排除 `frappe_china/public/js/vendor/`。
- `docker/apps.json` 锁 `acf97e6`。

## 总体判断

本片范围对源头意图满足：负荷报表与 SPC 的公式、Nelson 判式、页面逐点着色、报表跳转都落地并生效，本片独立手算例逐式一致；演示站只读核实上线状态成立且干净，E 的修复已被演示站 web 进程重载。关键缺口不在本片代码，而在过程与留档：P3-01（D 期间写过演示站，回执未如实报）与 P3-02（新模块首次 migrate 静默漏注册）两条长效坑没进守则。

## 复核建议

1. **定级在边界上的**：P3-01 定「中」，理由是它违反了站点安全纪律、回执当时报得不全；反方理由是演示站已清干净、无业务数据损失，可降「低」。P3-02 定「中」，理由是客户正式库首装会 migrate 成功却缺单据；若认为装机流程总会先 `clear-cache`（`setup.sh:425` 是在 migrate 之后），可降「低」。P3-03 在「低／观察」之间：只给管理员看。
2. **查得最浅的**：工作中心筛选（`spc.py:158`、`:167` 的 join）只验了 SQL 可执行与空结果，没造「Job Card 关联检验单」验命中；`capacity_load.py` 的多工作中心与跨公司混合场景没单独造数。
3. **没往哪找**：没审 Part1／Part2 代码本身；没看截图像素；没复核 365 天回放（片1）；Python 全量用的是主会话日志，不是本片自跑；worker 进程是否已加载 E 修复只做了读码推断（演示站 scheduler 关、worker 平时不跑 S7 任务）。
4. **拿不准处**：P3-07（主仓库脚本整体格式化）算不算方案外夹带——它不改行为，但方案没要求；P3-09 规则 8 的定义取需求字面还是经典定义，属需求层取舍。
