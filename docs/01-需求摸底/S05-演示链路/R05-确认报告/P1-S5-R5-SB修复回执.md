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
| CRM 链路重做 | IT-017 | — | ⬜未开始 | — | 用户裁决：脚本化验证＋关键值留证，代替 `/crm` 界面截图 |
| 本机连通基线 | IT-024（本机基线部分） | — | ⬜未开始 | — | LG-007 上线前对照已并入 SH-P1S5007，不在本项 |
| 演示站接入四个 App | IT-005 | — | ⬜未开始 | — | 写演示站前停下等用户确认 |
| Insights 演示站验收 | IT-018 | — | ⬜未开始 | — | 依赖 IT-005 |
| 新基准点与常驻文件回写 | IT-026 | — | ⬜未开始 | — | 依赖 IT-005 |

## 复验结果

| 报告项号 | 报告的判定标准 | 怎么复验的 | 实测结果 |
|---|---|---|---|
| IT-006 | 按 R3 Part1 TS-005 第 5 条补 ①～⑦（HRMS 不在时 `skipTest`）与 ⑧ | 测试站跑 `test_expense_claim`、`test_scaffold`、`test_hr`；变异：去掉 `build_cn_company` 末尾的预配（入口 1）、`after_app_install` 里的补配（入口 2），各跑一次后还原 | 7/7、4/4、3/3 通过；入口 1 变异 → ①③ 失败，入口 2 变异 → ② 失败；还原后 `git status` 无 `.bak` |
| IT-013 | 按 Part3 TS-009 拆成宿主入口＋容器内脚本；载入 `.env`、MSYS 防改写、`--site`／`--company`；第二次跑「无改动」；缺 DocType 打说明；公司零家或多家报错；SL-005 ①、SL-007 ② 字段逐个贴值 | 测试站建一家中式公司 `_FCT CRM 验证` 后连跑两次；另跑四条异常路径：无中式公司不传 `--company`、公司不存在、未知参数、只设 `RAVEN_LLM_URL`；临时建一条 `Delete Document` 类工具再跑、删后再跑 | 第一次逐字段列改动，第二次「无改动」；四条异常路径分别报「找到 0 家公司…请用 --company 指定」「公司…不存在」「未知参数」「须同时设置」，rc=1／1／2／1；有写类工具时报出其名、rc=1，删后「无改动」。字段值：`ERPNext CRM Settings` enabled=1、is_erpnext_in_different_site=0、sync_products=1、create_customer_on_status_change=0、erpnext_company=`_FCT CRM 验证`；`FCRM Settings.currency`=CNY；bot `is_ai_bot`=1、`model_provider`=Local LLM、`allow_bot_to_write_documents`=0、`bot_functions` 恰为 15 条且顺序同方案表；站上写类工具 0 条 |
| IT-014 | 追认偏离或改正；`params` 补描述（6 个报表名与过滤键）；工具描述改中文 | 查 `run_report` 记录；以 Administrator 调 `raven.ai.functions.get_report_result` 跑 `Purchase Receipt Trends`；查 `frappe_china.ai.queries` 已无 `run_report` | `type`=Get Report Result、`function_path` 空、`requires_write_permissions`=0，`params` 由 Raven 按类型生成；6 个报表名与各自过滤键写在 description（R3 方案的 `BOM Stock Report` 在 v16 已改名 `BOM Stock Analysis`，按站上实名写）；实跑返回 29 列；whitelisted 接口面减一 |

## 全量验证

| 门 | 结果 |
|---|---|

## 偏离与暂停

## 新增约定

| 约定 | 类别 | 在哪个任务确立 |
|---|---|---|

## 未做项

| 项 | 为什么没做 |
|---|---|

## 复核建议
