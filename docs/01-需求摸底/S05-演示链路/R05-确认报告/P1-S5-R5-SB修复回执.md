# SB回执（对象：代码与站点 / 依据：[R5 E确认报告](P1-S5-R5-E确认报告.md) 裁为 `新Session修` 的 8 项 ＋ [R3 开发方案](../R03-开发方案/P1-S5-R3-C开发方案-总纲.md)）

**轮次**：P1-S5-R5（附属，不占 Round）｜**日期**：2026-10-06｜**执行者**：Claude（Opus 5.5）
**状态值**：`修复已落地`（裁为 `新Session修` 的 8 项全部完成并按报告判定标准复验通过；演示站三项 IT-005／018／026 于 2026-10-07 在第二个 Session 做完）

> 本 Session 先补完了 R7 D 步（见 [R7 D回执](../R07-D代码/P1-S5-R7-D回执.md)），再做本回执各项：IT-005 要带上 R6 的代码，IT-006 的测试要建在 R6 修法上（R6 方案 §九第 3 条）。

## 逐项执行结果

| 任务 | 报告项号 | 落地位置（文件:行） | 结果 | 完成时间 | 说明 |
|---|---|---|---|---|---|
| SL-002 测试补齐 | IT-006 | `frappe_china/tests/test_expense_claim.py`（新增，7 例对应 SL-002 ①～⑦）；`frappe_china/tests/test_scaffold.py` `test_hrms_is_optional`（⑧） | ✅完成 | 2026-10-06 | 建在 R6 修法上：「5 个类型」按 R6 方案读作「站上全部类型」，科目号按 `expense_claim_account_number` 断言 |
| 配置脚本拆分与补齐行为 | IT-013 | `docker/configure-apps.sh`（重写为宿主侧入口）；`docker/scripts/configure_apps.py`（新增，`configure_crm`／`configure_raven`／`ensure_bot_and_functions`）；`docker/README.md`「配置四个 App」 | ✅完成 | 2026-10-06 | 不含已并入 SH-P1S5006 的「`RAVEN_*` 不全时非密钥字段照写」：现行为是三个都不填时跳过连接字段并说明，`URL`／`KEY` 只填一个时报错 |
| 报表通道与工具描述 | IT-014 | `docker/scripts/configure_apps.py` `TOOLS`；`frappe_china/ai/queries.py` 删 `run_report` | ✅完成 | 2026-10-06 | 用户裁决：改用 Raven 原生 `Get Report Result` 类型，不追认自写包装。15 条描述改中文；`list_crm_deals` 去掉「submitted」 |
| CRM 链路重做 | IT-017 | `docs/01-需求摸底/Spike/P1-S5-R5-IT017-crm-chain.py`（新增）；输出留证 `…/Spike/P1-S5-R5-IT017-crm-chain.log` | ✅完成 | 2026-10-06 | 用户裁决：脚本化验证＋关键值留证，代替 `/crm` 界面截图。脚本调界面背后的同一批服务端方法（转商机、生成报价单的预填参数与明细预填、报价单转销售订单、看板两张图），只在测试站跑 |
| 本机连通基线 | IT-024（本机基线部分） | `frappe_china/realtime_check.py` `run()` 轮询处改 `use_local_cache=False`；`frappe_china/tests/test_realtime_check.py` 新增 `test_run_sees_ack_written_by_another_process`；`docs/01-需求摸底/Spike/P1-S5-R5-IT024-local-baseline.mjs`（新增）及其 `.log` | ✅完成 | 2026-10-07 | LG-007 上线前对照已并入 SH-P1S5007，不在本项。首跑暴露 `run()` 缺陷（见「偏离与暂停」），修后通过 |
| 演示站接入四个 App | IT-005 | `docker/backups/保留-S5装App前/20261007_003913-*`；`frappe-bench/logs/s5-sb-it005-up.log`；`frappe-bench/logs/s5-sb-it005-configure.log`；`docs/01-需求摸底/Spike/P1-S5-R5-IT005-demo-site-verify.py`（新增）及其 `.log`、`…-demo-site-config.log` | ✅完成 | 2026-10-07 | 用户 2026-10-07 准许按 R3 Part2 TS-007 第 1～6 步写演示站。按报告建议另在演示站跑 `configure-apps.sh` 与 `check_app_order`（TS-008 第 3 步）。代码、`apps.json` 均未改 |
| Insights 演示站验收 | IT-018 | `docs/01-需求摸底/Spike/P1-S5-R5-IT018-insights-demo.mjs`（新增）及其 `.log`；截图 `…/Spike/P1-S5-R5-IT018-insights-home.png`、`…-data-sources.png`、`…-query-tabCompany-count.png` | ✅完成 | 2026-10-07 | 按 TS-011 第 2～3 步在演示站做，不再以单测替代。宿主无头 Chrome 登录后开页面与截图；建查询与执行走界面背后的同一批接口（`frappe.client.insert`、`insights.api.run_doc_method` → `execute`），再在界面打开该查询页截图。验完删除工作簿（连带删查询） |
| 新基准点与常驻文件回写 | IT-026 | `docker/backups/保留-S5装App后/20261007_011313-*`；`docs/项目概况.md`；`docs/开发守则.md`；`docs/01-需求摸底/0-P1文档/路线文档.md`（v1.6 → v1.7）；`docs/01-需求摸底/Spike/P1-S5-R5-IT026-final-check.log` | ✅完成 | 2026-10-07 | 按 TS-016 第 2～5 步：先只读复核演示站，再出新空账基准点，自查方案外改动，载入常驻文件契约后回写。逐文件改动见「常驻文件改动清单」 |

## 复验结果

| 报告项号 | 报告的判定标准 | 怎么复验的 | 实测结果 |
|---|---|---|---|
| IT-006 | 按 R3 Part1 TS-005 第 5 条补 ①～⑦（HRMS 不在时 `skipTest`）与 ⑧ | 测试站跑 `test_expense_claim`、`test_scaffold`、`test_hr`；变异：去掉 `build_cn_company` 末尾的预配（入口 1）、`after_app_install` 里的补配（入口 2），各跑一次后还原 | 7/7、4/4、3/3 通过；入口 1 变异 → ①③ 失败，入口 2 变异 → ② 失败；还原后 `git status` 无 `.bak` |
| IT-013 | 按 Part3 TS-009 拆成宿主入口＋容器内脚本；载入 `.env`、MSYS 防改写、`--site`／`--company`；第二次跑「无改动」；缺 DocType 打说明；公司零家或多家报错；SL-005 ①、SL-007 ② 字段逐个贴值 | 测试站建一家中式公司 `_FCT CRM 验证` 后连跑两次；另跑四条异常路径：无中式公司不传 `--company`、公司不存在、未知参数、只设 `RAVEN_LLM_URL`；临时建一条 `Delete Document` 类工具再跑、删后再跑 | 第一次逐字段列改动，第二次「无改动」；四条异常路径分别报「找到 0 家公司…请用 --company 指定」「公司…不存在」「未知参数」「须同时设置」，rc=1／1／2／1；有写类工具时报出其名、rc=1，删后「无改动」。字段值：`ERPNext CRM Settings` enabled=1、is_erpnext_in_different_site=0、sync_products=1、create_customer_on_status_change=0、erpnext_company=`_FCT CRM 验证`；`FCRM Settings.currency`=CNY；bot `is_ai_bot`=1、`model_provider`=Local LLM、`allow_bot_to_write_documents`=0、`bot_functions` 恰为 15 条且顺序同方案表；站上写类工具 0 条 |
| IT-014 | 追认偏离或改正；`params` 补描述（6 个报表名与过滤键）；工具描述改中文 | 查 `run_report` 记录；以 Administrator 调 `raven.ai.functions.get_report_result` 跑 `Purchase Receipt Trends`；查 `frappe_china.ai.queries` 已无 `run_report` | `type`=Get Report Result、`function_path` 空、`requires_write_permissions`=0，`params` 由 Raven 按类型生成；6 个报表名与各自过滤键写在 description（R3 方案的 `BOM Stock Report` 在 v16 已改名 `BOM Stock Analysis`，按站上实名写）；实跑返回 29 列；whitelisted 接口面减一 |
| IT-017 | 按 TS-010 第 1～8 步重做（Deal 金额 100000、概率 50、推进两档；报价单公司为中式公司、联系人非空；自动建客户从站上可证；⑥ 异常路径有证据；HT-005 记结论）；裁决改为脚本化＋关键值 | 测试站跑 `P1-S5-R5-IT017-crm-chain.py` 两遍（第一遍暴露两处脚本问题后修正，见「偏离与暂停」），第二遍输出原样存 `.log` | 29 条断言全过、`EXIT=0`。关键值：物料建出即同步出 `CRM Product`（`standard_rate`=2.5，取价目表价）；Lead 转 Deal 后 Lead 状态 `Qualified`、`converted`=1；Deal `currency`=CNY（**HT-005 成立**，不需加 Property Setter）、金额 100000、概率 50；推进到 `Proposal/Quotation` 后概率仍 50；生成报价单参数 `quotation_to`=CRM Deal、`party_name`=该 Deal、`company`=`_FCT CRM 验证`、`contact_person`=`_FCT 联系人`，明细预填 1 行；报价单提交后 `currency`=CNY、`conversion_rate`=1，此时站上无该 Deal 的客户；转销售订单保存后站上新增客户 `_FCT 客户 CRM`（`crm_deal` 指向该 Deal、联系人已挂），SO `customer` 即它（**LG-085：Quotation→SO 不需人工建客户**）；看板「预测收入」2026-10 为 50000.0，「转化」含 Demo/Making 与 Proposal/Quotation 各 1；`enabled`=0 时 `can_create_quotations` 为假（按钮不出）、`get_quotation_url` 报「ERPNext is not integrated with the CRM」，恢复后为 1；清理后 `_FCT` 前缀 10 类记录残留 0 |
| IT-024（本机基线） | SL-008 ①：本机浏览器开 `http://localhost:8000` 桌面页，确认 `realtime_check.js` 已加载，`bench --site erx.localhost execute frappe_china.realtime_check.run --kwargs "{'user': 'Administrator'}"` 报通过，输出原样贴进回执 | 宿主无头 Chrome 经 DevTools 协议登录、开 `/desk`，读网络面板与 socket 状态，宿主跑方案原命令；另做两条对照：页面未开、停 `realtime-proxy`。脚本 `Spike/P1-S5-R5-IT024-local-baseline.mjs`，输出原样存同名 `.log` | 修 `run()` 后全过（`EXIT=0`）。`realtime_check.js` 请求 `http://localhost:8000/assets/frappe_china/js/realtime_check.js` 200；实时连接走 `http://localhost:9100/socket.io/…`（宿主 9100＝realtime-proxy）；`run()` 输出「实时通道检查：通过（575.2 ms，回执用户 Administrator）」，页面弹「实时通道检查已收到：<本次 token>」。对照：页面未开 → 「失败（timeout: 页面未在 5 秒内回执——实时通道不通、或目标用户没有打开的桌面页）」；停 proxy → 同样失败；起 proxy 并刷新页面 → 「通过（584.2 ms…）」。修前同一流程：页面已弹提示、`ack` 200，`run()` 仍 30 秒超时 |
| IT-005 | 按 Part2 执行 TS-007（核 `005331` → 备份另存 → `up.sh` → 重启 → HDTH 验证），再在演示站跑 `configure-apps.sh` 与 `check_app_order`；判定按 SL-004 ①②③④⑥ | 第 1～2 步宿主 `ls`／`backup.sh`／`cp`；第 3 步 `up.sh` 输出存 log；第 4 步停掉旧 `bench start` 进程树后重起，`/api/method/ping` 回 `pong`；第 5～6 步与 TS-008 第 3 步用 `Spike/P1-S5-R5-IT005-demo-site-verify.py`（唯一写操作是方案要求的在 `zh` 下保存一次 HDTH）；`configure-apps.sh --site erx.localhost` 连跑两次，再以 `--no-save --config` 只读核其字段 | ① `20261004_005331` 4 个文件在根目录；新备份 `20261007_003913` 4 个文件已另存 `保留-S5装App前/`。② `up.sh` `EXIT=0`，七个 app 均「已在锁定的 commit」；HRMS 装完打印 `frappe_china expense claim account backfill: {'华东弹簧有限公司': ['Calls', 'Food', 'Medical', 'Others', 'Travel']}`；6.2 段 `changed: true`，`after` 为 `frappe, erpnext, crm, hrms, insights, raven, frappe_china`。③ HDTH 5 行 `Expense Claim Account`，科目号与 `expense_claim_account_number` 映射逐行一致（Calls 5602090／Food 5602040／Medical 5602010／Others 5602250／Travel 5602130），站上报销类型恰 5 个；保存前后均科目 266、自检 `ok=true`、`extra_accounts=[]`、无 `Expense Claims`。④ `check_app_order`：`ok`／`order_ok`／`overrides_ok`／`translation_ok`／`company_checks_ok` 均真，三个覆盖解析到 `frappe_china.accounting.chart.*`，`Formula` 实得「计算方式」＝期望，竞争者 `{hrms: 公式}`，`problems` 空。⑥ GL、SLE、客户、供应商、物料、销售／采购发票、日记账凭证均 0。配置：第一次逐字段列改动，第二次「无改动」，均 `EXIT=0`；`ERPNext CRM Settings` enabled=1、is_erpnext_in_different_site=0、sync_products=1、create_customer_on_status_change=0、erpnext_company=华东弹簧有限公司；`FCRM Settings.currency`=CNY；bot `is_ai_bot`=1、`model_provider`=Local LLM、`allow_bot_to_write_documents`=0、`bot_functions` 15 条；站上 `Raven AI Function` 15 条，类型只有 Get List／Get Document／Get Report Result；无 `_FCT` 公司。脚本两次共 37＋37 条断言全过 |
| IT-018 | 按 TS-011 第 2～3 步：演示站浏览器开 `/insights`、页面可用；数据源列表有 `Site DB`；建查询「`Site DB` · `tabCompany` · 计数」得 1，截图后删除该查询（SL-006 ②③） | `Spike/P1-S5-R5-IT018-insights-demo.mjs` 跑两遍（第一遍暴露两处脚本问题，见「偏离与暂停」），第二遍输出原样存 `.log`；之后查库核残留 | 21 条断言全过、`EXIT=0`。`/insights` 200，页面标题「Dashboards \| Insights」；数据源记录 `Site DB` `is_site_db=1`、`Active`，列表里那一行显示为主机名 `localhost`；查询执行 200，SQL 为 `SELECT COUNT(t1.name) AS count_of_rows FROM (SELECT * FROM tabCompany …)`，结果 `[{count_of_rows: 1}]`；查询页截图可见 `count_of_rows` 列为 1。删工作簿后 `Insights Workbook`／`Insights Query v3` 均 0；Insights 后台补写的 1 条 `Insights Query Reference`、第一遍失败留下的 1 条 `Insights Query Execution Log` 按名删掉。现余 1 条执行日志（`sig4mp22ku`，00:42 装 App 时 Insights 自建的连接测试，非本项所建，保留） |

## 全量验证

| 门 | 结果 |
|---|---|
| 全量 `bench --site test.localhost run-tests --app frappe_china`（`logs/s5-sb-regression.log`，2026-10-07） | **Ran 205、OK、`EXIT=0`**，耗时 904 秒。对比 R7 基线 196：只增不减（+7 `test_expense_claim`、+1 `test_scaffold.test_hrms_is_optional`、+1 `test_realtime_check.test_run_sees_ack_written_by_another_process`）。截至 IT-024，演示站三项未做 |
| 全量（同上，演示站三项做完后重跑；`frappe-bench/logs/s5-sb-final-regression.log`，2026-10-07） | **Ran 205、OK、`EXIT=0`**，耗时 948 秒，205 条全 ✔。与上一行同数：演示站三项不改代码，只增不减成立。收集条数 205 ≥ S4 收口的 160（SL-010 ④） |
| 专项 `test_realtime_check` | 6/6；去掉 `use_local_cache=False` 的变异 → 1 例失败，还原后 6/6 |

| IT-026 | 在 IT-005 之后按 TS-016 第 3、5 步做（先载入常驻文件契约）；判定按 SL-010 ⑤⑥ | 第 2 步：`demo-site-verify.py --no-save --config` 只读复核（输出存 `IT026-final-check.log`），另查库核 `_FCT`、商机、报价单、销售订单、`Translation` 计数；第 3 步 `backup.sh` 后另存；第 4 步主仓库与七个 app 逐个 `git status --short`；第 5 步载入 `docs/流程体系/常驻文件契约.md`，按判据定写哪个文件，写入时查同文件的逐出 | ⑤ 演示站 `check_app_order` `ok` 为真；SL-004 ⑥ 计数均 0；`_FCT` 前缀公司、物料 0；商机、Lead、报价单、销售订单 0；`Translation` 0；`Raven Settings` 与 bot `ERX 分析助手` 在；37 条断言全过。新基准点 `20261007_011313` 4 个文件已另存 `保留-S5装App后/`，`20261004_005331` 4 个文件仍在根目录，`restore.sh` 按修改时间取的最新一套即新基准点。第 4 步：七个 app `status` 均空、HEAD 与 `apps.json` 一致；SPS submodule 空；主仓库只有本回执、Spike 下本 Session 新增的验证脚本与留证、三份常驻／跨轮文件，均对得上 IT-005／018／026。⑥ 见「常驻文件改动清单」 |

## 常驻文件改动清单

| 文件 | 改了什么 | 依据 |
|---|---|---|
| `docs/项目概况.md` | 技术栈加「官方业务 App」一行；模块结构加四个官方 App 的目录行、`frappe_china` 行改写为现有各块（`hr.py`／`install.py`／`realtime_check.py`）；装载顺序的守护由「`after_migrate` 自检」改为 `reorder_installed_apps`＋`check_app_order`（`frappe_china` 无 `after_migrate` 钩子，原句失真）；版本记录句补 tag 与「官方 App 不改不推」；能力节加 S5 四项；UI 路由加三个独立前端；演示站当前状态改写为 S5 装 App 后；备份基准点：`20261004_005331` 降为 S4 基准、新增 `20261007_003913` 与 `20261007_011313`（当前空账基准点）；端口一条改写为经 `realtime-proxy` 转发、补检查工具与断开须刷新；已知限制「hrms app 未安装」改写为「HRMS 已装但未配人事数据」，另加 Raven 只读工具绕过权限（LG-091） | 判据 A：均为现状、改写原句不追加；TS-016 第 5 步清单 |
| `docs/开发守则.md` | 三层仓库表加官方 App 一行、remote 节加「官方 App 用官方仓库＋锁 commit，不 fork」；版本锁定节补条目按装序、`tag`／`branch` 二选一；新增五节：装完新 app 后归位并验、依赖可选 app 按 DocType 存在分支、删公司子表行由 `Company.on_trash` 兜住且不带 `force`、认科目看科目号、轮询别的进程写进缓存时跳过本地副本 | 判据 B：均无期限限定；来源为 R4 D 回执 Part1／Part2、R7 D 回执、本回执的「新增约定」节，与 Stage 概况长效信息 #1 |
| `docs/01-需求摸底/0-P1文档/路线文档.md` v1.6 → v1.7 | §四 S6 清单第 2 条补 `.mo` 覆盖 `.csv` 的出处、新增第 11 条（`/crm` 独立前端，译名覆盖两套）；§四 S7 清单新增第 14 条（演示操控驱动两套界面）、第 15 条（三问口径对 CR-012 数据的三项要求）；版本行与头部版本号 | Stage 概况长效信息 #2～#4，按 TS-016 第 5 步第 3 点落进路线文档对应 Stage 的清单 |

写入即查逐出（契约 §4）：`项目概况.md` 的失真句已就地改写（`after_migrate`、hrms 未安装、S4 时点的演示站状态、「两侧同号」）；`开发守则.md` 未见因本次改动失效的存量条目。`CLAUDE.md`、`docs/README.md`、`docs/业务规则.md` 本次未写；`业务规则.md` 本 Stage 无领域不变量变更。Stage 收口时的全量逐出由 Stage 收口那一步做，不在本项。

## 偏离与暂停

- IT-017 首跑两处中断，都是脚本问题、不是 CRM 链路问题，已在脚本里改正并注释：① 销售订单保存报 `WarehouseRequired`——临时物料是库存物料，测试公司无默认出库仓，界面实点时同样要手选仓库；脚本改为填该公司的「成品」仓（TS-010 第 5 步原文没写这一项）。② 清理时删客户报 `LinkExistsError`——删客户会连带删只挂它的联系人，而联系人还被 Deal 引用；清理顺序改为先删 Deal 再删客户，并改为按名字前缀找回（加 `--cleanup-only` 供中断后单独清）。首跑中断后已用 `--cleanup-only` 清干净，再完整跑一遍留证。
- **IT-024 做本机基线时发现 R4 的 `realtime_check.run()` 在真实环境下必然报失败**：页面收到事件、弹出提示、`ack` 请求返回 200，`run()` 仍超时。原因是 `run()` 用 `frappe.cache.set_value` 写 pending 时框架同时留了一份 `frappe.local.cache` 副本（`frappe/utils/redis_wrapper.py:74`），轮询 `get_value` 先读本地副本（`:91`），永远看不到 web 进程写进 Redis 的 `acked`。R4／R5 的单测在同一进程里调 `ack`，本地副本跟着被改，故测不出来。修法一行：轮询改 `get_value(key, use_local_cache=False)`。这是 SL-008 ① 判定标准本身的前提（工具不修，本机基线无从通过），故在本项内修，未另开项；新增单测在回执后把本进程本地副本还原，模拟「别的进程写的回执」，去掉修法即失败（变异：6 例中 1 例失败，还原后 6/6）。
- IT-024 的反证段多做了一步：停 `realtime-proxy` 约 10 秒再起后，页面 socket 未自动重连（frappe 前端 `socketio_client.js:56` 只重连 3 次），刷新页面后才通。与方案 TS-013 第 6 步「必要时刷新」一致，记在此供 S7 演示参考：演示中实时通道断开超过几秒，终端须刷新页面。

- IT-005 的 `up.sh` 只装 App、不重启进程；按 TS-007 第 4 步停掉上一 Session 起的 `bench start` 进程树后重起（`docker exec -d … bench start`），`/api/method/ping` 回 `pong` 后才做验证。
- IT-018 首跑两处失败，都是脚本问题、不是 Insights 问题，已在脚本里改正并注释：① 按「Site DB」字样找列表行找不到——前端把 `is_site_db` 且标题为 `Site DB` 的数据源改显为 `window.location.hostname`（`insights/frontend/src2/data_source/data_source.ts:17`），改为按记录核、按主机名核界面。② 执行查询回 500——`run_doc_method` 用请求体里的文档构造对象、不重读库（`insights/api/__init__.py:300-313`），只传 `name` 时 `operations` 为空；改为与查询页一样传整份文档。首跑建的工作簿 `1` 已在 `finally` 里删掉。
- IT-026 第 2 步复核前顺手把本 Session 建在主仓库根的 `logs/`（`up.sh` 与 `configure-apps.sh` 两份输出）挪进 `frappe-bench/logs/`，与此前各 Session 的日志放一处；主仓库不再多一个未忽略的目录。
- IT-018 的清理比方案字面多两步：删工作簿只连带删查询，`on_update` 入队补写的 `Insights Query Reference`（在删除之后才落库）和第一遍失败的执行日志会留下，按名删掉。另有两处无法撤回、留在演示站：`Deleted Document` 里两个工作簿、两个查询共 4 条删除记录；`tabSeries` 里 `Insights Workbook` 计数为 2（下一个工作簿编号 3）。都不是业务数据，也不影响 SL-004 ⑥ 的计数。

## 新增约定

| 约定 | 类别 | 在哪个任务确立 |
|---|---|---|
| 轮询别的进程写进 `frappe.cache` 的值，读时一律带 `use_local_cache=False`：本进程 `set_value` 过的键会在 `frappe.local.cache` 留副本，不跳过就读不到别的进程的更新。单测要模拟「别的进程写」，不能在同一进程里直接调写方 | 跨层调用 | IT-024 |

## 未做项

| 项 | 为什么没做 |
|---|---|

## 状态值

- **`修复已落地`**：IT-005／006／013／014／017／018／024（本机基线）／026 八项全部 ✅，各按报告判定标准复验通过；全量 205/205；七个 app 工作区干净、HEAD 与 `apps.json` 一致。按出口路由交回唤起方 E 复核（与 R7 D 步合并复核，Stage 概况已定）。

## 复核建议

1. **修得最勉强的那项：IT-018。** 方案字面是「浏览器建查询」，实做是用界面背后的同一批接口建查询与执行、再在界面打开该查询页截图——没有逐个点 Insights 的查询编辑器。理由：与 IT-017 用户裁决的「脚本化＋关键值」同一路数，且判定值（`count_of_rows=1`）来自 Insights 自己的 `execute`。查法：看 `Spike/P1-S5-R5-IT018-query-tabCompany-count.png`（页面右侧两步操作与中间结果 1），对照 `.mjs` 里 `operations` 的两段。若要求界面逐点，此项须重做。
2. **修复引入的连带影响：演示站多了几条非业务痕迹，已在新基准点里。** IT-018 留下 4 条 `Deleted Document`、`Insights Workbook` 计数器为 2；IT-005 在 `zh` 下保存过一次 HDTH（`modified` 2026-10-07 00:51）。都发生在 `20261007_011313` 备份之前。查法：`bench --site erx.localhost mariadb -e "select deleted_doctype, deleted_name from \`tabDeleted Document\` where creation > '2026-10-07'"`。
3. **拿不准处：`项目概况.md` 的装序守护那句。** 原文写「守护靠 `after_migrate` 自检」，`frappe_china/hooks.py` 里没有 `after_migrate`（路线文档 v1.5 已注明接线归 S8G-S1），故改写为现行做法。若用户想保留「S8G-S1 将接 `after_migrate`」这一去向，应写在 P1 概况而非项目概况（判据 A：未实现的不是现状）。另：演示站 `RAVEN_*` 三值未设，bot 的 `model` 为空——这是 SH-P1S5006 的范围，不是本回执的缺口，但 S7 准备 AI 演示时须先补。
