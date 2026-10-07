# F 复核分片报告 · 片 3（对象：应用配置脚本、CRM／Raven 文档与登记 / 审核标准：R3 开发方案 Part3 SL-005～007、TS-009～012；R9 F 审核报告 FD-002／004／014～017／028／029；SB 回执 FD-017）

**轮次**：P1-S5-R10｜**步骤**：F 复核分片 3｜**日期**：2026-10-07｜**执行者**：Claude 子 Agent（只读）
**依据**：[R3 开发方案 Part3](../R03-开发方案/P1-S5-R3-C开发方案-Part3.md)（TS-009 第 1～5 条、SL-005 ①、SL-007 ①②）；[R9 F 审核报告](../R09-F审核/P1-S5-R9-F审核报告.md)（FD-002／004／014～017／028／029 行、当场修清单、收口）；[R9 Part3](../R09-F审核/P1-S5-R9-F审核报告-Part3.md)（全文）；[SB 回执](../R09-F审核/P1-S5-R9-SB修复回执.md)（全文）；[Stage 概况](../P1-S5-概况.md) 长效信息 #3／#4、登记册 SH-P1S5006
**被审范围**：主仓库 `git diff 2fb2641..d7b89d6` 中 `docker/scripts/configure_apps.py`、`docker/configure-apps.sh`、`docker/README.md`「配置四个 App」节、`docker/.env.example` Raven 段、`docs/项目概况.md` 两处、Stage 概况 #4 与 SH-P1S5006 行；SB 探针与改前副本；`frappe_china` 本轮未动本片文件（`git diff 4b21aae..9d53d39 -- frappe_china/ai frappe_china/tests/raven_dataset.py` 为空），只为核延迟项描述读了现状

> 问题编号 `P3-xx` 是片内编号，主会话收口时转成 `FD-`。

## 覆盖自证

**读全了的**：分片通用说明；SB 回执（全文）；R9 Part3（全文）；R9 收口报告中本片各项的行、当场修清单、延迟清单；`configure_apps.py` 现版 1–337（全文）；改前副本 `Spike/P1-S5-R9-SB-FD017-configure_apps.before.py`（与 `git show 2fb2641:docker/scripts/configure_apps.py` 比对，除行尾 CRLF 外逐字节一致）；SB 探针 `Spike/P1-S5-R9-SB-FD017-probe.py`（全文）；`configure-apps.sh` 1–34；README 231–259；`.env.example` 25–37；`tests/raven_dataset.py`（全文）。

**按需读的**：R3 方案 Part3 的 TS-009、SL-005／007、配置表；Stage 概况 #3／#4（:105-107）与登记册 SH-P1S5006（:120）；项目概况 :68、:103；R8 E 报告 IT-030 段；路线文档 §四 S7 第 14、15 条；开发守则 diff（本轮只动了 app 顺序与工具链两节，与本片无关）。

**对照的上游代码**（只读）：
- raven `e890308`：`raven/doctype/raven_settings/raven_settings.py` 58–87（validate）与 `.json` 中 `push_notification_service`（缺省 `Raven`）、`push_notification_server_url`（`mandatory_depends_on`）；`raven_bot.py` 57–135（validate／on_update／before_insert）；`raven_ai_function.py` 56–98、446–523；`ai/sdk_tools.py` 30–58；`ai/ai.py` 15–27；`notification.py`、`api/notification.py`、`boot.py` 中推送服务的读取点。
- crm：`erpnext_crm_settings.py` 15–30、54–100、594–715；`crm_product/reconcile_job.py` 11–18。
- erpnext：`crm/frappe_crm_api.py` 135–192；`crm/doctype/crm_settings/crm_settings.py` 35–66；`buying/report/purchase_analytics/purchase_analytics.js` 全部过滤器的 `reqd`／`default`。
- frappe：`database/database.py:451-458`（`sql_ddl` 先 commit）。

**只读查询**（两站各一遍，Git Bash `bench mariadb`）：
- `tabRaven AI Function` 按 `type` 分组计数与 `requires_write_permissions` 合计；总数；
- `tabRaven Bot` 的 `model_provider`／`model`／`debug_mode`／`openai_assistant_id`；`tabRaven Bot Functions` 行数；
- `tabSingles`：`CRM Settings.enable_frappe_crm_data_synchronization`、`enable_opportunity_creation_from_contact_us`，`Contact Us Settings.is_disabled`，`ERPNext CRM Settings` 的 enabled／erpnext_company／sync_products，`Raven Settings` 的连接字段与推送相关字段（密钥类只判空）；
- `tabFrappe CRM Allowed User` 计数；`tabCompany`；探针残留（`_fct_probe%`）。

**只读实验**（1 个，在演示站，用完已删）：`.claude/r10-tmp/p3_raven_validate.py`。取 `Raven Settings` 单例，在内存里按 `configure_raven` 的目标值设四个字段和一个假密钥，只调 `validate()`，不 save，最后 `rollback`。目的是核「`configure_raven` 的 save 会不会在第一次写之后抛异常」。结果见 P3-01。

**跳过的部分及原因**：
- 没跑 `configure-apps.sh`，也没跑 SB 探针：两者都会写站，分片禁止。SB 探针的结论只靠读码判断。
- 没给 bot 发消息：LiteLLM 未接，属 SH-P1S5006。
- `--company 华东弹簧有限公司` 的中文参数是否原样到达容器：用 `docker compose exec … python -c` 打印 `sys.argv` 的十六进制核过，与宿主 UTF-8 一致。没有经 `configure_apps.py` 跑。

## R9 已修项复核

| R9 项 | 修于（当场／SB） | 定位（文件:行） | 落地 | 生效 | 原问题消失 | 说明 |
|---|---|---|---|---|---|---|
| FD-017 | SB | `configure_apps.py:8-9`（说明）、`:145-182`（`configure_crm` 收已解析公司）、`:193`（去掉只设一个的报错）、`:271-286`（`preflight`）、`:310-317`（`main` 先 preflight 再写） | ✅ | ✅ | ✅（就 R9 点名的情形）；⚠ 新约定不完全成立，见 P3-01 | 逐条核见表后「FD-017 逐条核」 |
| FD-015 | 当场 | `docker/README.md:252、254`；`docker/configure-apps.sh:6` | ✅ | ✅ | ✅ | 两处示例都改为 `--company 华东弹簧有限公司`，README 注明填全名、`HDTH` 是缩写。演示站 `tabCompany` 只有 `华东弹簧有限公司`（abbr `HDTH`），`resolve_company` 按 name 查（`:134`），示例成立。中文参数经 `configure-apps.sh` 的数组与 `docker compose exec` 原样到达容器（十六进制一致）。`docker/`、`docs/` 中除 R9／R10 报告外再无 `--company HDTH` |
| FD-016 | 当场 | `docker/README.md:256` | ✅ | — | ✅ | 说法与上游一致：`frappe_crm_api.py:141-142` 的 `create_customer` 首行调 `validate_frappe_crm_sync`，`:168-173` 开关为 0 时 `frappe.throw`；CRM 侧 `erpnext_crm_settings.py:682-692` 同站点时直接 import 调它，`:707-708` 对 `ValidationError` 原样上抛，所以是「报错」而不是静默。两站该开关为 1。`crm_settings.py:50-59` 的 `validate_allowed_users` 在 CRM 已装时要求 `allowed_users` 为空，两站 `tabFrappe CRM Allowed User` 为 0 行，脚本写这一项不会被拦 |
| FD-029 | 当场 | `docker/.env.example:33-34` | ✅ | — | ✅ | 改为中文，写明「三个须一起设：不设 MODEL 时 bot 取 Raven 缺省 gpt-4o」「密钥只放这里，不写进任何文档、日志」。与 README :245 的说法一致 |
| FD-004（b） | 当场 | `docs/项目概况.md:68、103`；Stage 概况 :120 SH-P1S5006「唤醒时另须处理」①～⑥ | ✅ | — | ✅ | 两站各 15 条：`Get List` 8、`Get Document` 6、`Get Report Result` 1，`requires_write_permissions` 全 0；bot 均为 `Local LLM`、`openai_assistant_id` 为 NULL。按 `ai.py:24` 走 Agents SDK 路径，`sdk_tools.py:42-56` 只认 Get List／Get Document／Update／Create／Delete（Custom 另判），其余 `continue`。「挂 15 条、实际可用 14 条」成立。登记里写的行号 `:42-55` 与实际 `continue` 所在 `:56` 差一行，不影响定位 |
| FD-002 | 当场 | Stage 概况 :107（长效信息 #4） | ✅ | — | ✅（Stage 概况层）；观察见 P3-03 | #4 已补「演示前把 `debug_mode` 置 0」。两站 `tabRaven Bot.debug_mode` 现值都是 1，与描述「两站现为 1」一致 |

**FD-017 逐条核**：

1. **写类工具检查的集合是否同一个。** 改前用 `set(names)`，`names` 在 `ensure_bot_and_functions` 的循环里**每条都** append（`before.py` 中 `names.append(name)` 在 `if changed` 之外），循环跑完就是 `TOOLS` 全部 15 个名字，与是否写过无关。现在用 `{name for name, *_rest in TOOLS}`。`TOOLS` 每项都是 4 元组 `(name, kind, reference_doctype, description)`，`name, *_rest` 解包正确。两者是同一集合。
   - 差别一：改前是先 upsert 再查，现在是先查再 upsert。对「15 条中某条被人改成写类」的情形，两者都不报（都在排除集合里），随后 upsert 改回只读类型。结果相同。
   - 差别二：改前只在 `Raven AI Function` 与 `Raven Bot` 都在时查，现在只看 `Raven AI Function`。两者同属 raven，实际不会只装一个，可忽略。
2. **CRM 判定。** `preflight` 的条件是 `_has("FCRM Settings") and _has("ERPNext CRM Settings")`，`configure_crm` 的跳过条件是 `not _has(...) or not _has(...)`，两者互为补集，一致。CRM 没装时 `company=None`，`configure_crm` 在 `:147-149` 先返回，用不到 `company`，安全。CRM 已装时，`resolve_company` 要么返回字符串，要么抛 `ConfigureError`，不会出现 `None` 写进 `erpnext_company`。
3. **Raven 判定。** `preflight` 用 `_has("Raven Settings") and (url or key) and not (url and key)`。`configure_raven` 依次是：`not _has("Raven Settings")` 时跳过，`not (url or key)` 时跳过。能走到写字段这一步的，只有「Raven Settings 在、且至少设了一个」，而其中只设一个的已被 preflight 拦下。两边判据一致，不存在「preflight 放过、configure_raven 写到一半才报只设一个」的情形。`Raven Settings` 不在、但设了一个值时：preflight 不报，`configure_raven` 打「Raven 未安装」说明后跳过，与改前行为相同（改前也是先判未安装）。
4. **`ConfigureError` 的抛出点。** 全文只有 `resolve_company`（`:135`、`:139`）与 `preflight`（`:277`、`:285`）。`resolve_company` 只被 `preflight` 调用。所以脚本自己的 `ConfigureError` 已全部排在第一次写之前，`main` 里 `except ConfigureError` 的 `rollback()` 现在是空操作，无害。
5. **第一次写之后仍可能抛异常的点**（都不是 `ConfigureError`）。逐个函数找过：
   - `configure_raven` 的 `settings.save()`（`:210`）：**上游 `Raven Settings.validate` 必抛**，见 P3-01。这是唯一一个可预知、且在正常使用路径上必然触发的。
   - `configure_crm`：`ERPNext CRM Settings.save` 的 validate 里 `create_custom_fields`（会走 DDL，正是 FD-017 的起因）、`enqueue_reconciliation`（Redis 不通时抛）；`CRM Settings.save` 的 `validate_enable_opportunity_creation_from_contact_us`（两站该开关为 0，不触发）、`validate_allowed_users`（见上，不触发）。都依赖环境，不是脚本能预检的。
   - `ensure_bot_and_functions`：`frappe.get_doc` 只在 `exists` 为真时调用，不会抛 `DoesNotExistError`。新建或改 `Raven AI Function` 时，上游 validate 会核 `reference_doctype`，Raven 在而 CRM 不在时，前三条工具指向 `CRM Deal`／`CRM Deal Status`，会抛错（读码，现实中四个 App 一起装，不触发）。`model` 为空时不写 `model`：新建 bot 取缺省 `gpt-4o`，已有 bot 保持原值。`Raven Bot.validate` 只要求有 instruction、工具不需写权限，脚本两项都满足。`on_update` 对 `Local LLM` 不调 OpenAI。没有找到会抛错的点。
   - `main`：`commit()` 之后的 `frappe.clear_cache()` 若因 Redis 失败而抛错，改动已提交但不打印（环境类，极少见）。
   - 这些非 `ConfigureError` 异常，`main` 都不捕获：进程打 traceback、rc=1，`finally` 里 `destroy()` 关连接，未提交的写被 MariaDB 丢弃。DDL 之前的写已被 `sql_ddl` 的隐式 commit 提交，丢不掉。退出码对宿主 `set -e` 仍是失败，可以接受。
6. **SB 探针结论是否成立。** 成立。
   - setup：建一条 `Delete Document` 工具，把 `sync_products` 置 0，并提交。这样 CRM 段有一个待写字段，并且必然触发写类工具报错。
   - 钩子：`Document.save` 与 `Database.sql_ddl` 都钩在类上，脚本的写全部走 `.save`，钩得住。
   - 判定：`rc == 1`、`save` 为 0 次、teardown 时 `sync_products` 仍为 0。改前版本按读码会 save 一次 `ERPNext CRM Settings` 再报错，判「不通过」；现版本在 preflight 就报错，判「通过」。两者对得上回执的数字。
   - 局限，SB 已自述：站上三个自定义字段已存在，探针触发不了 DDL。「公司不存在」「只设 URL」两条异常路径是直接跑 `configure-apps.sh` 看报错文字，没有放进计数框架。按读码，两者现在都在 preflight 里抛，结论不受影响。
   - 现状核对：两站无 `_fct_probe%` 残留，测试站 `sync_products=1`。
7. **说明与 README 是否一致。** README :245「`URL` 与 `KEY` 只填一个时报错退出」、:258「已有写类工具时报错退出」仍对：报错文字与退出码没变，只是时机提前。模块说明 :8-9「会报错退出的检查都在写任何东西之前做完」，就脚本**自己**的检查而言成立。但它容易被读成「脚本报错时什么都没写」，与 P3-01 的实情不符。README 没写「两个都填时」会怎样，见 P3-01。

## 延迟／不做项登记核对

| R9 项 | 裁决去向 | 登记位置 | 描述与实情一致否 | 说明 |
|---|---|---|---|---|
| FD-014 | 延迟，并入 SH-P1S5006 ③ | Stage 概况 :120 ③ | ✅ | `configure_apps.py:83` 的 Purchase Analytics 描述只列 company、from_date、to_date、tree_type、range。上游 `purchase_analytics.js` 里 `reqd: 1` 的有 tree_type、doc_type、value_quantity、from_date、to_date、company、range、curves。漏的正是 `doc_type`／`value_quantity`／`curves`，与登记一致。行号从 R9 时的 `:81` 移到 `:83`（SB 在说明里加了两行），登记没写行号，不受影响 |
| FD-028 | 延迟，并入 SH-P1S5006 ④ | Stage 概况 :120 ④ | ✅ | `raven_dataset.py:20` 用 `like "_FCT%"` 取第一家公司，测试站唯一的 `_FCT` 公司就是 `_FCT CRM 验证`；`:33-36` 的 teardown 对 CRM Deal／Item／Supplier／Purchase Receipt／Sales Order／BOM 以 `force=True` 删 `_FCT` 前缀记录，不含 Company。登记写「会挑中 `_FCT CRM 验证`」「`force=True` 删 `_FCT` 前缀的物料等（不删公司）」，与代码一致。R8 E 报告 IT-030 里的旧说法（会删掉该公司）没改。那是历史报告，以登记册为准，不算问题 |

## 业务规则合规核

| 规则条款 | 本轮改动是否涉及 | 结论 | 备注 |
|---|---|---|---|
| BR-001 小企业会计准则 | 间接涉及：`resolve_company` 仍按 `CN_CHART_NAME` 认中式公司，只是调用位置移进 preflight | 合规（语义未变） | 只用来选 CRM 报价的公司，不碰科目 |
| BR-002 报表构成 | 否 | — | — |
| BR-003 增值税税率 | 否 | — | — |
| BR-004 增值税结转 | 否 | — | — |
| BR-005 附加税 | 否 | — | — |
| BR-006 资产负债恒等 | 否 | — | — |
| BR-007 价税分离 | 否 | — | — |
| 本轮是否新增或变更规则 | 否 | — | SB「新增约定」（配置类脚本先预检再写）属工程约定，不是领域不变量，不进 `业务规则.md` |

## 集成点登记（交接摘要）

**本片依赖**（需要别片确认）：
- 片 1／2：`frappe_china.accounting.chart.CN_CHART_NAME` 未变名（`preflight` → `resolve_company` 在第一行 import 它）。本轮 FD-008 去掉了 `hr.py` 对它的再导出，`configure_apps.py` 从 `chart` 直接导入，不受影响（读码）。
- 主会话：SB 回执的新约定「会报错退出的检查全部放在第一次写之前」若要进 `docs/开发守则.md`，措辞须按 P3-01／P3-02 收窄成「脚本自己的检查」，或者先把 Raven Settings 那一处补上。

**本片暴露**（别片会用到）：
- `configure-apps.sh` 退出码语义不变：0 成功或「无改动」；1 是 `ConfigureError`（现在全部在写之前发生）**或**上游 validate 抛错（traceback，可能在写之后）；2 是未知参数。
- **两站 `Raven Settings.push_notification_service` 为缺省值 `Raven`，推送服务器地址、密钥都为空。在这个状态下，任何走 `doc.save()` 的 Raven Settings 写入都会被上游拦下**（P3-01）。片 4／S7 若要改 Raven Settings，同样会撞上。
- 两站 bot `debug_mode=1`，S7 演示前须置 0（Stage 概况 #4）。

## 自证复核

| 被审产物声称（R9 报告／SB 回执／文档） | 实际复核 | 一致否 |
|---|---|---|
| SB 回执 FD-017「三项会报错的检查都放进了 `preflight`」 | 脚本自己的三项 `ConfigureError` 全在 preflight（见逐条核第 4 条） | 一致 |
| SB 回执「报错文字和退出码都没变」 | 三条报错字符串与改前副本逐字相同；`except ConfigureError` 仍返回 1 | 一致 |
| SB 回执新增约定「会报错退出的检查全部放在第一次写之前……不要写到一半再报错」 | 脚本自身成立；`configure_raven` 的 save 在两站必被上游 validate 拦，且排在 CRM 段写之后（P3-01） | 部分一致 |
| 模块说明 `configure_apps.py:8-9`「会报错退出的检查都在写任何东西之前做完」 | 同上 | 部分一致（P3-02） |
| SB 回执「改动前的副本留证」 | 与 `2fb2641` 版逐字节一致（只差 CRLF） | 一致 |
| SB 回执「`configure_crm`／`configure_raven` 只有 `main` 调用」 | grep `docker/`、`frappe_china`、`Spike/`：除改前副本外无其它调用 | 一致 |
| SB 回执复验「探针结束后写类工具已删、`sync_products` 恢复 1」 | 两站无 `_fct_probe%`；测试站 `sync_products=1` | 一致 |
| R9 当场修 FD-015／016／029 | 见上表 | 一致 |
| R9 当场修 FD-004「挂 15 条、实际可用 14 条」 | 两站 SELECT 与上游 `sdk_tools.py` 一致 | 一致 |
| R9 当场修 FD-002「两站现为 1」 | 两站 `debug_mode=1` | 一致 |
| README :245「三个值都不填也能跑……只填一个时报错退出」 | 两项都对；但没说两个都填时，按现状必定报错（P3-01） | 一致（有遗漏） |
| SH-P1S5006 ⑥「`URL`／`KEY` 只填一个时报错」 | 成立（现在在 preflight 抛） | 一致 |

## 问题清单

| # | 严重程度 | 定位 | 问题描述 | 违背的标准／意图 | 建议 | 建议档位 | 待裁决点 | 状态 |
|---|---|---|---|---|---|---|---|---|
| P3-01 | 中 | `docker/scripts/configure_apps.py:195-211`（`configure_raven` 的 `settings.save`）；上游 `raven/raven/doctype/raven_settings/raven_settings.py:68-70`、`raven_settings.json:212`（`push_notification_service` 缺省 `Raven`）与 `:224`；Stage 概况 SH-P1S5006 | **一旦填了 `RAVEN_LLM_URL` 和 `RAVEN_LLM_KEY`，`configure_raven` 在两站都必定报错**。原因：上游 `Raven Settings.validate` 在 `push_notification_service == "Raven"` 且 `push_notification_server_url` 为空时 `frappe.throw("Please enter the Push Notification Server URL")`；两站该字段都是缺省值 `Raven`，地址与推送密钥都为空。**实测**（演示站，内存设值、只调 `validate()`、rollback）：抛 `frappe.exceptions.ValidationError: Please enter the Push Notification Server URL`。`doc_events` 里没有别的 app 挂 `Raven Settings`。后果有三：① SH-P1S5006 唤醒时第一步「接 LiteLLM」就跑不通，登记册没写这一条；② 这个错排在 CRM 段写入**之后**，又不是 `ConfigureError`，正是 FD-017 要消除的「写到一半再报错」，只是换了一处——首跑若 CRM 段要建自定义字段，DDL 已隐式提交、撤不回，输出只有一段英文 traceback；③ 两站 `Raven Settings` 从没被保存过（`enable_ai_integration=0`），所以 R4～R9 都没撞上，SB 的复验也只跑了「都不填」「只填 URL」两条路径。这个问题不是本轮引入的，但本轮立的新约定「会报错的检查全部放在第一次写之前」在这里不成立 | SB 新约定（FD-017）；开发守则「不静默」；TS-009-3 要求 Raven Settings 能写成；流程规范 §12（登记册是唤醒入口） | (a) `configure_raven` 的目标值里加 `push_notification_service: "Frappe Cloud"`。Frappe Cloud 模式下推送由 `Push Notification Settings.enable_push_notification_relay` 控制，缺省关，等于不推送，与现状一致。或者 (b) `preflight` 里先判这一条，抛 `ConfigureError`，提示去 Raven 设置页改推送服务。无论取哪种，都在 SH-P1S5006 补一条⑦。另：README「配置四个 App」节补一句「两个都填时会顺带把推送服务改为 Frappe Cloud」（取 a）或「须先改推送服务」（取 b） | 本Session修 | 取 (a) 自动改推送服务（改了一个用户没要求的设置），还是取 (b) 预检报错、交人处理；或只登记、留到 SH-P1S5006 唤醒时改 | 待裁决 |
| P3-02 | 观察 | `configure_apps.py:8-9`（模块说明）；SB 回执「新增约定」 | 说明写「会报错退出的检查都在写任何东西之前做完」。就脚本自己的 `ConfigureError` 而言成立，但上游 validate 仍可能在写之后抛错：P3-01 是必然触发的；`ERPNext CRM Settings` 的 `enqueue_reconciliation`（Redis 不通）、Raven 在而 CRM 不在时工具指向 `CRM Deal` 的链接校验、commit 后的 `clear_cache` 是环境类或现实中不触发的。`main` 只捕获 `ConfigureError`，其余异常是 traceback、rc=1，未提交的写随断开连接丢弃，DDL 撤不回。读的人容易把说明理解为「报错就什么都没写」。若 SB 约定要进开发守则，原话也有同样问题 | 开发守则「判据必须能区分」的精神（说法要与实情相符） | 说明改为「本脚本自己的检查（公司、URL／KEY、写类工具）都在写之前做完；上游 validate 仍可能在写之后报错，此时已建的自定义字段不会回滚」。约定入守则时用同样的限定 | 本Session修 | — | 待裁决 |
| P3-03 | 观察 | Stage 概况 :105-107（长效信息 #3／#4）；路线文档 §四 S7 第 14、15 条（:232-233） | R9 当场修给长效信息 #3（CRM 覆盖 Contact／Email Template、`/crm` 实时没验）与 #4（`debug_mode` 置 0）各补了一句。但路线文档 §四 S7 第 14、15 条是 v1.7 时从 #3／#4 同步过去的，这次没有跟上。R9 收口第 4 条已判「本步可以改 Stage 概况、不必回写路线文档」，这本身不违规。风险在于：S7 开工若只读路线文档 §四清单，会漏掉 `debug_mode`。Stage 收口时的长效信息移交是否会再同步一次，本片没有核 | 方案 TS-009-4「记进 S7 输入」；长效信息移交 | Stage 收口做长效信息移交时，把 #3／#4 的 R9 增补同步进路线文档 §四 S6／S7 清单；或现在就在第 15 条末尾补一句 | 延迟或不修 | 收口时同步，还是现在补 | 待裁决 |

## 本片盲区自述

- **P3-01 只实测到 `validate()` 这一层。** 没有真跑 `configure-apps.sh` 并填上 URL／KEY，因为会写站。`save()` 在 validate 之前还有 `before_validate` 等钩子，按读码 `Raven Settings` 没有别的钩子能把 `push_notification_service` 改掉。修法 (a) 的「Frappe Cloud 模式下等于不推送」也是读码结论（`api/notification.py:11-18`、`notification.py:33-40`），没有实测。
- **非 `ConfigureError` 异常的清单**是逐个函数读码列出的，没有覆盖上游 `save()` 链上所有可能的 `frappe.throw`（例如权限、链接校验的每个分支）。只列了按两站现值可能触发的。
- **SB 探针**没有复跑，结论只按读码判为成立。DDL 路径（首跑建自定义字段）自始至终没有被实测过，R9 与 SB 都是读码。
- 没有核 `configure_apps.py` 之外的 `docker/` 改动（`setup.sh`、`lock-apps.sh`、compose、realtime-proxy），那些分在别片。
- FD-004 只核了「记录与类型分布」和上游跳过逻辑，没有在本轮重跑 `create_raven_tools(bot)`。R9 片 3 已实测得 14，本轮 raven 版本没变（`e890308`）。
