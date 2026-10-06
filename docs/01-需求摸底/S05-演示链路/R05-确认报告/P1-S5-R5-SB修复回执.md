# SB回执（对象：代码与站点 / 依据：[R5 E确认报告](P1-S5-R5-E确认报告.md) 裁为 `新Session修` 的 8 项 ＋ [R3 开发方案](../R03-开发方案/P1-S5-R3-C开发方案-总纲.md)）

**轮次**：P1-S5-R5（附属，不占 Round）｜**日期**：2026-10-06｜**执行者**：Claude（Opus 5.5）
**状态值**：（进行中）

> 本 Session 先补完了 R7 D 步（见 [R7 D回执](../R07-D代码/P1-S5-R7-D回执.md)），再做本回执各项：IT-005 要带上 R6 的代码，IT-006 的测试要建在 R6 修法上（R6 方案 §九第 3 条）。

## 逐项执行结果

| 任务 | 报告项号 | 落地位置（文件:行） | 结果 | 完成时间 | 说明 |
|---|---|---|---|---|---|
| SL-002 测试补齐 | IT-006 | `frappe_china/tests/test_expense_claim.py`（新增，7 例对应 SL-002 ①～⑦）；`frappe_china/tests/test_scaffold.py` `test_hrms_is_optional`（⑧） | ✅完成 | 2026-10-06 | 建在 R6 修法上：「5 个类型」按 R6 方案读作「站上全部类型」，科目号按 `expense_claim_account_number` 断言 |
| 配置脚本拆分与补齐行为 | IT-013 | `docker/configure-apps.sh`（重写为宿主侧入口）；`docker/scripts/configure_apps.py`（新增，`configure_crm`／`configure_raven`／`ensure_bot_and_functions`）；`docker/README.md`「配置四个 App」 | ✅完成 | 2026-10-06 | 不含已并入 SH-P1S5006 的「`RAVEN_*` 不全时非密钥字段照写」：现行为是三个都不填时跳过连接字段并说明，`URL`／`KEY` 只填一个时报错 |
| 报表通道与工具描述 | IT-014 | `docker/scripts/configure_apps.py` `TOOLS`；`frappe_china/ai/queries.py` 删 `run_report` | ✅完成 | 2026-10-06 | 用户裁决：改用 Raven 原生 `Get Report Result` 类型，不追认自写包装。15 条描述改中文；`list_crm_deals` 去掉「submitted」 |
| CRM 链路重做 | IT-017 | `docs/01-需求摸底/Spike/P1-S5-R5-IT017-crm-chain.py`（新增）；输出留证 `…/Spike/P1-S5-R5-IT017-crm-chain.log` | ✅完成 | 2026-10-06 | 用户裁决：脚本化验证＋关键值留证，代替 `/crm` 界面截图。脚本调界面背后的同一批服务端方法（转商机、生成报价单的预填参数与明细预填、报价单转销售订单、看板两张图），只在测试站跑 |
| 本机连通基线 | IT-024（本机基线部分） | `frappe_china/realtime_check.py` `run()` 轮询处改 `use_local_cache=False`；`frappe_china/tests/test_realtime_check.py` 新增 `test_run_sees_ack_written_by_another_process`；`docs/01-需求摸底/Spike/P1-S5-R5-IT024-local-baseline.mjs`（新增）及其 `.log` | ✅完成 | 2026-10-07 | LG-007 上线前对照已并入 SH-P1S5007，不在本项。首跑暴露 `run()` 缺陷（见「偏离与暂停」），修后通过 |
| 演示站接入四个 App | IT-005 | — | ⬜未开始 | — | **用户 2026-10-07 已准许按 R3 Part2 TS-007 第 1～6 步写演示站**，并裁定本 Session 先提交推送、演示站相关三项（IT-005／018／026）由下一个 Session 做。续跑从本行起 |
| Insights 演示站验收 | IT-018 | — | ⬜未开始 | — | 依赖 IT-005 |
| 新基准点与常驻文件回写 | IT-026 | — | ⬜未开始 | — | 依赖 IT-005 |

## 复验结果

| 报告项号 | 报告的判定标准 | 怎么复验的 | 实测结果 |
|---|---|---|---|
| IT-006 | 按 R3 Part1 TS-005 第 5 条补 ①～⑦（HRMS 不在时 `skipTest`）与 ⑧ | 测试站跑 `test_expense_claim`、`test_scaffold`、`test_hr`；变异：去掉 `build_cn_company` 末尾的预配（入口 1）、`after_app_install` 里的补配（入口 2），各跑一次后还原 | 7/7、4/4、3/3 通过；入口 1 变异 → ①③ 失败，入口 2 变异 → ② 失败；还原后 `git status` 无 `.bak` |
| IT-013 | 按 Part3 TS-009 拆成宿主入口＋容器内脚本；载入 `.env`、MSYS 防改写、`--site`／`--company`；第二次跑「无改动」；缺 DocType 打说明；公司零家或多家报错；SL-005 ①、SL-007 ② 字段逐个贴值 | 测试站建一家中式公司 `_FCT CRM 验证` 后连跑两次；另跑四条异常路径：无中式公司不传 `--company`、公司不存在、未知参数、只设 `RAVEN_LLM_URL`；临时建一条 `Delete Document` 类工具再跑、删后再跑 | 第一次逐字段列改动，第二次「无改动」；四条异常路径分别报「找到 0 家公司…请用 --company 指定」「公司…不存在」「未知参数」「须同时设置」，rc=1／1／2／1；有写类工具时报出其名、rc=1，删后「无改动」。字段值：`ERPNext CRM Settings` enabled=1、is_erpnext_in_different_site=0、sync_products=1、create_customer_on_status_change=0、erpnext_company=`_FCT CRM 验证`；`FCRM Settings.currency`=CNY；bot `is_ai_bot`=1、`model_provider`=Local LLM、`allow_bot_to_write_documents`=0、`bot_functions` 恰为 15 条且顺序同方案表；站上写类工具 0 条 |
| IT-014 | 追认偏离或改正；`params` 补描述（6 个报表名与过滤键）；工具描述改中文 | 查 `run_report` 记录；以 Administrator 调 `raven.ai.functions.get_report_result` 跑 `Purchase Receipt Trends`；查 `frappe_china.ai.queries` 已无 `run_report` | `type`=Get Report Result、`function_path` 空、`requires_write_permissions`=0，`params` 由 Raven 按类型生成；6 个报表名与各自过滤键写在 description（R3 方案的 `BOM Stock Report` 在 v16 已改名 `BOM Stock Analysis`，按站上实名写）；实跑返回 29 列；whitelisted 接口面减一 |
| IT-017 | 按 TS-010 第 1～8 步重做（Deal 金额 100000、概率 50、推进两档；报价单公司为中式公司、联系人非空；自动建客户从站上可证；⑥ 异常路径有证据；HT-005 记结论）；裁决改为脚本化＋关键值 | 测试站跑 `P1-S5-R5-IT017-crm-chain.py` 两遍（第一遍暴露两处脚本问题后修正，见「偏离与暂停」），第二遍输出原样存 `.log` | 29 条断言全过、`EXIT=0`。关键值：物料建出即同步出 `CRM Product`（`standard_rate`=2.5，取价目表价）；Lead 转 Deal 后 Lead 状态 `Qualified`、`converted`=1；Deal `currency`=CNY（**HT-005 成立**，不需加 Property Setter）、金额 100000、概率 50；推进到 `Proposal/Quotation` 后概率仍 50；生成报价单参数 `quotation_to`=CRM Deal、`party_name`=该 Deal、`company`=`_FCT CRM 验证`、`contact_person`=`_FCT 联系人`，明细预填 1 行；报价单提交后 `currency`=CNY、`conversion_rate`=1，此时站上无该 Deal 的客户；转销售订单保存后站上新增客户 `_FCT 客户 CRM`（`crm_deal` 指向该 Deal、联系人已挂），SO `customer` 即它（**LG-085：Quotation→SO 不需人工建客户**）；看板「预测收入」2026-10 为 50000.0，「转化」含 Demo/Making 与 Proposal/Quotation 各 1；`enabled`=0 时 `can_create_quotations` 为假（按钮不出）、`get_quotation_url` 报「ERPNext is not integrated with the CRM」，恢复后为 1；清理后 `_FCT` 前缀 10 类记录残留 0 |
| IT-024（本机基线） | SL-008 ①：本机浏览器开 `http://localhost:8000` 桌面页，确认 `realtime_check.js` 已加载，`bench --site erx.localhost execute frappe_china.realtime_check.run --kwargs "{'user': 'Administrator'}"` 报通过，输出原样贴进回执 | 宿主无头 Chrome 经 DevTools 协议登录、开 `/desk`，读网络面板与 socket 状态，宿主跑方案原命令；另做两条对照：页面未开、停 `realtime-proxy`。脚本 `Spike/P1-S5-R5-IT024-local-baseline.mjs`，输出原样存同名 `.log` | 修 `run()` 后全过（`EXIT=0`）。`realtime_check.js` 请求 `http://localhost:8000/assets/frappe_china/js/realtime_check.js` 200；实时连接走 `http://localhost:9100/socket.io/…`（宿主 9100＝realtime-proxy）；`run()` 输出「实时通道检查：通过（575.2 ms，回执用户 Administrator）」，页面弹「实时通道检查已收到：<本次 token>」。对照：页面未开 → 「失败（timeout: 页面未在 5 秒内回执——实时通道不通、或目标用户没有打开的桌面页）」；停 proxy → 同样失败；起 proxy 并刷新页面 → 「通过（584.2 ms…）」。修前同一流程：页面已弹提示、`ack` 200，`run()` 仍 30 秒超时 |

## 全量验证

| 门 | 结果 |
|---|---|
| 全量 `bench --site test.localhost run-tests --app frappe_china`（`logs/s5-sb-regression.log`，2026-10-07） | **Ran 205、OK、`EXIT=0`**，耗时 904 秒。对比 R7 基线 196：只增不减（+7 `test_expense_claim`、+1 `test_scaffold.test_hrms_is_optional`、+1 `test_realtime_check.test_run_sees_ack_written_by_another_process`）。截至 IT-024，演示站三项未做 |
| 专项 `test_realtime_check` | 6/6；去掉 `use_local_cache=False` 的变异 → 1 例失败，还原后 6/6 |

## 偏离与暂停

- IT-017 首跑两处中断，都是脚本问题、不是 CRM 链路问题，已在脚本里改正并注释：① 销售订单保存报 `WarehouseRequired`——临时物料是库存物料，测试公司无默认出库仓，界面实点时同样要手选仓库；脚本改为填该公司的「成品」仓（TS-010 第 5 步原文没写这一项）。② 清理时删客户报 `LinkExistsError`——删客户会连带删只挂它的联系人，而联系人还被 Deal 引用；清理顺序改为先删 Deal 再删客户，并改为按名字前缀找回（加 `--cleanup-only` 供中断后单独清）。首跑中断后已用 `--cleanup-only` 清干净，再完整跑一遍留证。
- **IT-024 做本机基线时发现 R4 的 `realtime_check.run()` 在真实环境下必然报失败**：页面收到事件、弹出提示、`ack` 请求返回 200，`run()` 仍超时。原因是 `run()` 用 `frappe.cache.set_value` 写 pending 时框架同时留了一份 `frappe.local.cache` 副本（`frappe/utils/redis_wrapper.py:74`），轮询 `get_value` 先读本地副本（`:91`），永远看不到 web 进程写进 Redis 的 `acked`。R4／R5 的单测在同一进程里调 `ack`，本地副本跟着被改，故测不出来。修法一行：轮询改 `get_value(key, use_local_cache=False)`。这是 SL-008 ① 判定标准本身的前提（工具不修，本机基线无从通过），故在本项内修，未另开项；新增单测在回执后把本进程本地副本还原，模拟「别的进程写的回执」，去掉修法即失败（变异：6 例中 1 例失败，还原后 6/6）。
- IT-024 的反证段多做了一步：停 `realtime-proxy` 约 10 秒再起后，页面 socket 未自动重连（frappe 前端 `socketio_client.js:56` 只重连 3 次），刷新页面后才通。与方案 TS-013 第 6 步「必要时刷新」一致，记在此供 S7 演示参考：演示中实时通道断开超过几秒，终端须刷新页面。

## 新增约定

| 约定 | 类别 | 在哪个任务确立 |
|---|---|---|
| 轮询别的进程写进 `frappe.cache` 的值，读时一律带 `use_local_cache=False`：本进程 `set_value` 过的键会在 `frappe.local.cache` 留副本，不跳过就读不到别的进程的更新。单测要模拟「别的进程写」，不能在同一进程里直接调写方 | 跨层调用 | IT-024 |

## 未做项

| 项 | 为什么没做 |
|---|---|

## 复核建议
