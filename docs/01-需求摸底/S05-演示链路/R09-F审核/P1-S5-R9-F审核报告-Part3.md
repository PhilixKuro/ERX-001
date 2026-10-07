# F 审核分片报告 · Part3（对象：应用配置脚本、CRM、Insights、Raven 与三问 / 审核标准：B 需求文档 §4.5～§4.7、AC-001／003／007）

**轮次**：P1-S5-R9｜**步骤**：F 分片 3｜**日期**：2026-10-07｜**执行者**：Claude 子 Agent（只读）
**依据**：[R3 开发方案 Part3](../R03-开发方案/P1-S5-R3-C开发方案-Part3.md)（SL-005～007、TS-009～012，全文逐条）＋[总纲](../R03-开发方案/P1-S5-R3-C开发方案-总纲.md)；[B 需求文档](../R02-需求文档/P1-S5-R2-B需求文档.md) §3.2 DEC-007～016／020、§4.5～§4.7、§4.10／4.11、§八、§十；[R4 D 回执 Part3](../R04-代码/P1-S5-R4-D回执-Part3.md)；[SB 回执](../R05-确认报告/P1-S5-R5-SB修复回执.md) IT-013／014／017／018；[Stage 概况](../P1-S5-概况.md)延迟需求登记册（SH-P1S5006）
**被审范围**：`docker/configure-apps.sh`、`docker/scripts/configure_apps.py`、`docker/.env.example`、`docker/README.md`「配置四个 App」节（`git diff c372a94..2fb2641 -- docker/` 中属本片的部分）；`frappe_china/ai/queries.py`、`frappe_china/tests/raven_dataset.py`（`git diff 03fde72..4b21aae` 中属本片的部分）；两站 CRM／Raven／Insights 相关记录（只读）；上游 raven `e890308`、crm `deedce7`、insights `5447f16` 对照

> 问题编号 `P3-xx` 是片内编号，主会话收口时转成 `FD-`。

## 覆盖自证

**读全了的文档**：F Spec、`bricks/audit.md`、`bricks/sharding.md`、流程规范 §2.2／§2.3、`docs/开发守则.md`、`docs/业务规则.md`、方案总纲（全文）、方案 Part3（全文）、B 需求文档 §一、§3.1～3.2、§4.5～§4.7、§4.10～§4.11、§八、§十、Stage 概况（全文）、D 回执 Part3（全文）、SB 回执（全文）。R5／R8 E 报告只按关键词查了「核过什么」的索引，没有采信它们的结论。

**逐行读的代码**：
- `docker/scripts/configure_apps.py` 1–322（全文）、`docker/configure-apps.sh` 1–34（全文）、`docker/.env.example`（全文与 diff）、`docker/README.md` 229–256；对照了 `docker/seed-demo.sh` 1–24 的骨架。
- `frappe_china/ai/queries.py`（全文）、`frappe_china/tests/raven_dataset.py`（全文）；grep 确认这两个文件在 `frappe_china` 内没有别处引用；`tests/utils.py` 的 `TEST_PREFIX`。
- `docs/01-需求摸底/Spike/P1-S5-R5-IT017-crm-chain.py` 41–80、186–287，以及它的 `.log`（29 条「通过」、清理后残留 0）；`frappe-bench/logs/s5-sb-it005-configure.log` 前 40 行。

**对照的上游代码**（只读）：
- raven：`ai/functions.py` 全部函数签名，以及 1–30、185–283 行；`ai/sdk_tools.py` 1–330、486–760（`create_raven_tools`、`create_function_tool`、`handle_get_list`、`handle_get_document`）；`ai/agents_integration.py` 40–200、340–800（Local LLM 走强制回退的直连路径）；`ai/ai.py` 14–86、356–380、495–530（路由）；`ai/handler.py` 1–30、180–330（旧版 Assistants 路径）；`raven_ai_function.py` 1–530；`raven_bot.py` 55–140、187–199；`raven_bot.json` 的字段缺省值；`raven_settings.py` 56–90；`raven_message.py` 的入队位置。
- frappe：`core/doctype/report/report.py` 180–330、500–511；`desk/query_report.py` 30–60、273–400、920–935；`model/delete_doc.py` 24–135；`model/base_document.py` 1349–1370；`model/document.py` 828–840、1588–1610；`__init__.py` 中的 `is_whitelisted`。
- erpnext：`crm/frappe_crm_api.py` 141–215；`crm/doctype/crm_settings/crm_settings.py` 40–100；六张报表的 `.js` 过滤器（含 `public/js/purchase_trends_filters.js`）、`purchase_analytics.py`、`sales_analytics.py` 10–35。
- crm：`erpnext_crm_settings.py` 54–100、640–720；`fcrm_settings.py` 213–247；`install.py` 546–550；前端里 `enable_forecasting` 只在 `DashboardSettings.vue:42` 出现（grep `frontend/src` 得出）。

**跑过的只读查询**（两站各一遍）：
- `tabSingles` 中 CRM／FCRM／ERPNext CRM／Raven Settings 的相关字段；
- `tabRaven Bot`、`tabRaven Bot Functions`、`tabRaven AI Function`；
- `tabCompany`、`tabProperty Setter`（CRM Deal／Quotation／Customer）、`tabCustom Field`（crm_deal／erpnext_customer）、`tabCRM Form Script`；
- 六张报表的 `report_type`／`prepared_report`／`ref_doctype`；
- 密钥字段只判空，没有读值；`tabCRM Deal Status`；`tabDefaultValue` 中的 currency／company；
- `tabInsights Data Source v3`（演示站）；`_FCT` 残留计数；四个 App 工作区 `git status`；`apps.json` 与 HEAD 的比对。

**跑过的只读函数**（都在 `frappe.db.rollback()` 之内）：
- 测试站上用 `create_raven_tools(bot)` 生成 bot 实际拿到的工具表，其中 `log_error` 换成了 print；
- 两站 meta 字段存在性；
- 测试站 `raven.ai.functions.get_report_result` 对六张报表各跑一次。

**⚠ 本片探针留下了两条无法回滚的记录**：测试站 `tabError Log` 的 `ruekosvjr2`（`Report execution failed for: Purchase Analytics`，10:56:18）和 `tiadsd1l5c`（`Report execution failed for: BOM Stock Analysis`，10:59:04）。`tabError Log` 是 MyISAM，rollback 撤不掉（开发守则「探针三条纪律」第 1 条）。本片按规定不写库，所以没有删。需要清理时**按这两个 name 正向删除**。这两条本身就是 P3-04 的实证。

**跳过的部分及原因**：
- Spec 要求的「验证门亲自实跑」没有做。分片任务禁止 `run-tests`，主会话正在跑全量回归。
- `configure-apps.sh` 没有实跑，因为它会写站。幂等性只读了代码，并核了两站现状。
- 没有给 bot 发消息，没有开浏览器。LiteLLM 未接，属 SH-P1S5006。
- Insights 只核了演示站 `Site DB` 记录，没有重跑 IT-018 脚本（会写演示站）。
- TS-010 只看了 IT-017 脚本与日志，没有重跑（会写测试站）。

## 逐项落地核查

| 意图层依据 | 要求层要求（方案任务／验收条款逐条） | 定位（文件:行） | 落地 | 生效否 | 偏差说明 |
|---|---|---|---|---|---|
| 总纲 A6 | TS-009-1 宿主侧入口 `configure-apps.sh`，按 `seed-demo.sh` 的骨架写：载入 `.env`、MSYS 防改写、`--site` 缺省取 `SITE_NAME` | `configure-apps.sh:11-34` | ✅ | ✅ | 只用 `-e` 传变量名，密钥不进进程参数（`:30-32`），比方案更稳 |
| A6 | TS-009-1 容器内 `configure_apps.py`：init／connect → 三个函数 → commit → destroy | `configure_apps.py:289-318` | ✅ | ✅ | 签名多了 `notes` 参数，`configure_crm` 的参数名改为 `company_arg`。不影响契约用途 |
| A6 | TS-009-1 某 App 没装（缺 DocType）时跳过该段并打说明 | `:145-147`、`:186-188`、`:217-219` | ✅ | ✅ | — |
| A6 | TS-009-1 `--company` 缺省取唯一一家「小企业会计准则(2024)」公司，零家或多家报错 | `:128-140` | ✅ | ✅ | 文案经 SB 实测。**README／脚本头的示例 `--company HDTH` 跑不通**，见 P3-06 |
| A6／开发守则「不静默」 | 幂等：已是目标值不写；第二次跑输出「无改动」 | `:113-121`、`:306-311` | ⚠ | ✅（常规路径） | 常规路径成立：两站现状与目标值一致，SB／R8 记有「无改动」。首跑出错时，DDL 的隐式提交使整体回滚不成立，且已提交的改动不会打印，见 P3-08（读码） |
| §4.5／DEC-008／LG-004 | TS-009-2 `FCRM Settings.currency=CNY`，已是 CNY 则不写 | `:149-154` | ✅ | ✅ | 两站 `currency=CNY` |
| §4.5 | TS-009-2 `ERPNext CRM Settings`：enabled=1／different_site=0／sync_products=1／create_customer_on_status_change=0／erpnext_company＝该站中式公司 | `:156-171` | ✅ | ✅ | 测试站 `_FCT CRM 验证`（CNY、中式）；**演示站 `华东弹簧有限公司`（HDTH，CNY）** ✅ |
| §4.5／HT-014 | TS-009-2 `enable_forecasting` 不改（保持 0） | 脚本不写它 | ✅ | ✅ | 两站均为 0。前端 grep 只在设置页出现，看板图不受它门控，HT-014 读码成立 |
| §4.5 LG-004／HT-005 | TS-009-2 HT-005 不成立时才加 `CRM Deal.currency` 属性默认值 | 未加 | ✅ | ✅ | 两站 CRM Deal 的 Property Setter 为 0 条。IT-017 日志记 Deal `currency=CNY`，HT-005 成立 |
| （方案外） | — | `:173-180` | ⚠ | ✅ | **夹带**：`CRM Settings.enable_frappe_crm_data_synchronization=1`。它是 LG-085 自动建客户的必要前提（`frappe_crm_api.py:142,168-173`），但方案、SB 回执、README 都没有申报，见 P3-07 |
| §4.6.1／DEC-011 | TS-009-3 `Raven Settings` 四个字段＋密钥（Password，经 save 加密） | `:184-212` | ⚠ | ⏸ | 方案要求「密钥未设时非密钥字段照写、只告警」；实现是两项都未设时整段跳过，只设一项时报错。SB 已申报，说「并入 SH-P1S5006」，但登记册描述没写这一条，见 P3-09。两站现在 `enable_ai_integration=0`、密钥空，是延迟状态 |
| §4.6.1「不进任何文档、日志」 | TS-009-3 输出只报密钥「已设／未设」 | `:208`、`:283-286` | ✅ | ✅ | 改动行写成「（密钥）→（密钥，已改）」。`Raven Settings` 开了 `track_changes`，但 `_save_passwords` 先把字段掩成 `*`（`base_document.py:1364-1369`），Version 里不会留明文。`.env` 已被 gitignore（`.gitignore:4`）。两份 configure 日志里没有密钥字样 |
| §4.6.2／DEC-009 | TS-009-4 bot `ERX 分析助手`：is_ai_bot=1、Local LLM、model=$RAVEN_LLM_MODEL、写／代码解释器／文件搜索=0、debug_mode=1；instruction 原文 | `:19-24`、`:250-274` | ✅ | ✅ | instruction 与方案逐字一致。`model` 未设时取 `gpt-4o`（演示站），测试站为空串。IT-029 已处理 |
| 方案 TS-009-4「`debug_mode=1`……演示前由 S7 关掉，**记进 S7 输入**」 | 同上 | 路线文档／Stage 概况长效信息／项目概况 | ❌ | — | grep `debug_mode` 在三处都为零命中，见 P3-03 |
| DEC-009 | TS-009-4 15 条工具，名字／类型／DocType 同表、中文描述、按表序写进 `bot_functions` | `:28-87`、`:221-241`、`:269-271` | ⚠ | ❌（第 15 条） | 两站 15 条记录、顺序与类型核对一致（#15 依 IT-014 裁决改为 `Get Report Result`）。**但 bot 在 Local LLM 路径实际只拿到 14 个工具，`run_report` 被上游静默丢掉**（实测 `create_raven_tools` → 14），见 P3-01 |
| §4.6.2 LG-009 | TS-009-4 Get List 描述列出可用字段 | `:33-73` | ✅ | ✅ | 两站 meta 核过：描述里列的字段全部存在。`CRM Deal Status.type` 的选项与描述一致。CRM Deal 不可提交，描述已写明 |
| §4.6.3 | TS-009-4 #15 `params` 列出可用报表名与过滤键 | `:75-86` | ⚠ | ❌ | 报表名与过滤键写在 description 里，六张报表在两站都存在。**Purchase Analytics 缺必填键 `doc_type` 等**，按描述传参会报 `AttributeError`（实测），见 P3-05。工具本身也不可达（P3-01） |
| DEC-009「不建写类」 | TS-009-4 站上有非 15 条、且属写类型的工具时报错退出、不删 | `:89-102`、`:243-248` | ✅ | ✅ | `WRITE_TYPES` 覆盖上游全部写类型。两站 `requires_write_permissions` 全为 0 |
| A6 | TS-009-5 `.env.example` 加三个键名（无值）与注释 | `.env.example:32-35` | ✅ | — | 注释是英文、只有一行，没提「三个须一起设」，见 P3-11 |
| A6 | TS-009-5 README「配置四个 App」节：何时跑、填哪三个值、跑两次安全 | `README.md:229-256` | ✅ | — | 内容齐全。示例 `--company HDTH` 不成立（P3-06） |
| DEC-007／AC-001 | TS-010 / SL-005 ②～⑦ CRM 实点 | IT-017 脚本与日志 | ✅ | ✅ | 用户裁决改为「脚本化＋关键值」。日志：Deal 100000／50、推进两档、报价单公司＝中式公司、联系人非空、`quotation_to=CRM Deal`、CNY／汇率 1、转 SO 后自动建客户（`crm_deal` 指回）、预测收入 50000、关集成后报错原文对、残留 0。看板只核了后端函数，未经界面 |
| DEC-016／AC-007 | TS-011 / SL-006 ①～③ | 演示站 `Insights Data Source v3` | ✅ | ✅（部分复核） | 两站 `installed_apps` 都含 insights；演示站 `Site DB` `is_site_db=1`、`Active`。查询结果 1 来自 SB 截图，本片未重跑 |
| DEC-010～014／020、SH-P1S5006 | TS-012 ③④⑥ 连通、报表通道、三问 | — | ⏸ | — | 已延迟。**延迟后剩下的代码不完全诚实**：P3-01（报表通道配置是死的）、P3-02（现成工具路径对问 2／问 3 走不通）都没进登记册 |
| A7 | TS-012-1 `raven_dataset.py` 契约 §2 | `tests/raven_dataset.py:1-36` | ❌（已延迟 IT-019） | — | 文件头注明不可用。核实情：`teardown` 不删 Company，R8 IT-030 的风险描述与代码不符；`build` 会挑中 `_FCT CRM 验证` 来建；防误用只靠注释。见 P3-10 |
| A8 | 契约 §3 退路函数「触发哪一问才写哪一个」 | `ai/queries.py:1-28` | ❌（已延迟 IT-015） | 死代码 | 四个 whitelisted 函数，零引用。用的是 `get_list`（带权限），不扩大攻击面。已登记延迟，但登记册描述没写（P3-09） |
| LG-091 | `Get List` 绕过权限，上生产前处置 | 上游 `sdk_tools.py:570`（`frappe.get_all`） | ✅（登记属实） | — | Local LLM 路径确实走 `handle_get_list` → `get_all`。`Get Document` 走 `check_permission`（`:732-733`）。项目概况 :163 的登记与实情一致 |

## 业务规则合规核

| 规则条款 | 本片改动是否涉及 | 结论 | 备注 |
|---|---|---|---|
| BR-001 小企业会计准则 | 间接涉及：`resolve_company` 按 `CN_CHART_NAME` 认中式公司 | 合规（未经专家确认） | 只用来选 CRM 报价的公司，不改科目 |
| BR-002 报表构成 | 否 | — | 本片不碰财务报表 |
| BR-003 增值税税率 | 否 | — | 三问数据方案定为「不含税」，有意绕开税率 |
| BR-004 增值税结转 | 否 | — | — |
| BR-005 附加税 | 否 | — | — |
| BR-006 资产负债恒等 | 否 | — | — |
| BR-007 价税分离 | 否 | — | 同 BR-003 |
| 本片是否新增或变更规则 | 无产品语义不变量的改动 | — | 三问口径（加权金额、拒收率、单位利润，以及方案拟定的「拒收率不超过 5% 取最便宜」）是测试问法，不是领域不变量，不进 `业务规则.md`。其中 5% 阈值是 AI 在 C 步拟的，S7 若把它当客户口径用，须标「草案·待领域专家确认」 |

## 集成点登记（交接摘要）

**本片发出的事件**：自有代码不发任何实时事件。上游会被触发的有：CRM 的 `crm_customer_created`（建客户时）；Raven 的 `ai_event`／`ai_event_clear`（发私信给 bot 时）。都与契约一 `erx_demo_step` 无关。

**本片暴露的接口**：
- 宿主命令 `docker/configure-apps.sh [--site S] [--company C]`：rc 0 表示成功或「无改动」；1 表示 ConfigureError；2 表示未知参数。
- whitelisted 端点 `frappe_china.ai.queries.{list_crm_deals, list_purchase_receipts, list_sales_orders, list_boms}`：死代码，零引用，已延迟。
- `frappe_china.tests.raven_dataset.{PREFIX, expected, verify_built, build, teardown}`：不可用。

**本片依赖的接口**：
- `frappe_china.accounting.chart.CN_CHART_NAME="小企业会计准则(2024)"`，片 1／片 2 的建账代码定义。脚本 import 它，要求容器里 `frappe_china` 可导入。
- 上游 `create_raven_tools`（raven `e890308`）只认 Custom／Get List／Get Document／Update／Create／Delete 六种类型。
- CRM `get_quotation_url` 读 `erpnext_company`。
- ERPNext `frappe_crm_api.create_customer` 要求 `CRM Settings.enable_frappe_crm_data_synchronization=1`。

**本片依赖或写入的跨片共享状态**：
- `installed_apps`：两站均为 `frappe, erpnext, crm, hrms, insights, raven, frappe_china`。本片只读不改，但要求 crm／raven 在场。
- `apps.json` 锁定：crm `deedce7`、insights tag `v3.14.2`／`5447f16`、raven `e890308`、frappe_china `4b21aae`，与 HEAD 一致。
- 站点 Singles：`ERPNext CRM Settings.erpnext_company`（测试站 `_FCT CRM 验证`／演示站 `华东弹簧有限公司`）、`FCRM Settings.currency=CNY`、`CRM Settings.enable_frappe_crm_data_synchronization=1`、`Raven Settings`（未开）。
- Raven 记录：两站各 15 条 `Raven AI Function`、bot `ERX 分析助手`（`debug_mode=1`，演示站 `model=gpt-4o`）、一个 Bot 类 `Raven User`。
- 全局默认值 `currency=CNY`（演示站另有 `company=华东弹簧有限公司`），HT-005 依赖它。
- 测试站夹具公司 `_FCT CRM 验证`：IT-017 脚本依赖它；`raven_dataset.build` 也会挑中它。
- 前缀 `_FCT`：`raven_dataset.PREFIX` 与 `tests/utils.TEST_PREFIX` 共用。
- `.env` 键：`RAVEN_LLM_URL`／`KEY`／`MODEL`、`SITE_NAME`、`BENCH_NAME`。
- 本片不读写 `company_defaults.json`。

**开发守则 §13 跨 Phase 契约**：契约一 `erx_demo_step`。本片不发、不消费，不涉及。

## 自证复核

| 被审产物声称 | 实际复核 | 一致否 |
|---|---|---|
| D 回执 Part3「TS-009 configure-apps.sh 幂等……已验证」 | R5 已判偏离（IT-013），SB 重写。本片读码：常规路径幂等成立，首跑出错路径不成立（P3-08） | 否（已由 IT-013 处理；残余见 P3-08） |
| D 回执「TS-010 ……已验证」 | R5 判证据不足（IT-017），SB 重做。本片读日志：29/29 通过、残留 0 | 原声称否；SB 后一致 |
| SB IT-013「字段逐个贴值……`bot_functions` 恰为 15 条且顺序同方案表」 | 两站 SELECT 一致 | 一致 |
| SB IT-013 字段清单（未提 `CRM Settings`） | configure 日志与两站 Singles 都有 `CRM Settings.enable_frappe_crm_data_synchronization: 0→1` | 不一致（漏报，P3-07） |
| SB IT-014「改用 Raven 原生 `Get Report Result`……实跑返回 29 列」 | 29 列是直接调用 `get_report_result` 得到的，没有经过 bot 的工具路径。经 bot 路径时 `create_raven_tools` 不认这个类型，工具数为 14（实测） | **不一致：实跑只证明函数可用，不证明 bot 能调到（P3-01）** |
| R8 IT-014「两站 15 条……类型只有 Get List 8／Get Document 6／Get Report Result 1」 ✅ | 记录数一致；生效的工具是 14 个 | 记录层一致，生效层不一致 |
| 项目概况 :103「Raven 只读 bot，15 条只读工具（列表、取单据、跑报表）」 | 跑报表那条不可达 | 不一致（P3-01） |
| SB IT-017「LG-085：Quotation→SO 不需人工建客户」 | 日志 :40 新增客户、`crm_deal` 指回 | 一致 |
| SB IT-018「`Site DB` `is_site_db=1`、Active」 | 演示站 SELECT 一致 | 一致 |
| R8 IT-030「`raven_dataset.py` 按前缀强删……重写前若被调用会删掉它（`_FCT CRM 验证`）」 | `teardown` 只删 CRM Deal／Item／Supplier／Purchase Receipt／Sales Order／BOM（`raven_dataset.py:34`），不含 Company | 不一致（P3-10） |
| `raven_dataset.py` 文件头「teardown 会按 _FCT 前缀误删别的测试数据」 | 属实：`force=True`，覆盖六类 DocType | 一致 |
| 概况 SH-P1S5006 描述 | 没写 IT-015／IT-019、`configure_raven` 行为偏离、报表通道不可达、单轮工具调用限制 | 不一致（P3-09、P3-02） |

## 问题清单

| # | 严重程度 | 定位 | 问题描述 | 违背的标准/意图 | 建议 | 建议档位 | 待裁决点 | 状态 |
|---|---|---|---|---|---|---|---|---|
| P3-01 | 高 | `docker/scripts/configure_apps.py:75-86`；上游 `raven/ai/sdk_tools.py:37-56`、`raven/ai/ai.py:24` | **报表通道 `run_report` 对 bot 不可达。** 记录在，bot 调不到。bot 是 `Local LLM`、无 `openai_assistant_id`，按 `ai.py:24` 走 Agents SDK 路径。该路径的 `create_raven_tools` 只认 Custom／Get List／Get Document／Update／Create／Delete，其余类型直接 `continue`，不打日志。只有旧版 Assistants 路径（`handler.py:306`）认 `Get Report Result`。实测测试站 `create_raven_tools(bot)` 返回 14 个工具，不含 `run_report`。IT-014 当时的裁决依据是「上游函数无 whitelist、Custom Function 存不进去」，没覆盖这一层。项目概况和 SB 都写成「15 条只读工具含跑报表」，会误导 SH-P1S5006 与 S7 | DEC-009（报表通道是 bot 的工具之一）；AC-003；三层落地第 2 层「真被调用」 | 改回 `Custom Function`，指向 `frappe_china` 里一个 whitelisted 包装：内部调 `frappe.desk.query_report.run`，并带 `report` 权限检查。或者维持现状，在 SH-P1S5006 与项目概况里写明「报表通道当前不可达」 | 新Session修 | IT-014 裁决的是「用原生类型、不追认包装」，现在要推翻：(a) 恢复自写包装（Custom Function），本轮修；(b) 维持原生类型，只改登记册与项目概况，留 SH-P1S5006 唤醒时处理 | 待裁决 |
| P3-02 | 中 | 上游 `raven/ai/agents_integration.py:514-515、586-590、643-649` | **Local LLM 路径一轮只执行一批工具调用。** 第二次请求不再带 `tools`，模型没法「先列单号、再逐张取单据」。而方案 TS-009 #4／#5、需求 §4.6.2 LG-009 把问 2、问 3 的现成工具路径定为「主表 Get List 列单号 → 逐张 Get Document」。按读码，这条路在当前上游结构上走不通，只有第一轮就能并行发全部调用的情形例外，而此时模型还不知道单号。读码结论，未实测 | 需求 §4.6.2、§4.6.5（三问可测）；拼装不上 | 在 SH-P1S5006 登记描述里补这条读码结论与出处，唤醒时先用一次实测确认；成立就直接按 §4.6.4 走 A8 退路（Custom Function 在该路径可用，`sdk_tools.py:38-41`） | 延迟或不修 | — | 待裁决 |
| P3-03 | 中 | 方案 Part3 TS-009-4；路线文档 §四 S7、Stage 概况长效信息、项目概况（均无） | 两站 bot `debug_mode=1`。方案要求「演示前由 S7 关掉，记进 S7 输入」，但三处 grep `debug_mode` 全部零命中。开着时，报错回复会把错误原因发进聊天（`ai.py:516-520`），旧路径甚至发完整 traceback（`handler.py:325-328`），演示现场可能当着客户露出来 | 方案明确要求的交接项遗漏；RW-04「AI 在现场答错比不演示代价更大」 | 在路线文档 §四 S7 清单或 Stage 概况长效信息 #4 补一句「演示前把 bot `debug_mode` 置 0」 | 本Session修 | — | 待裁决 |
| P3-04 | 低 | `configure_apps.py:75-86`（#15 描述「运行一张只读报表」）；上游 `report.py:186-198、507-511`，`query_report.py:318`，`raven_ai_function.py:349`、`handler.py:308-313` | 报表通道「只读」不完全成立（P3-01 修复后才会生效）：① 报表执行失败时 `log_error` 写进 MyISAM 的 Error Log，rollback 撤不掉；本片探针实际留下两条，见覆盖自证。② 跑满 15 秒，上游另开连接把 `Report.prepared_report` 置 1 并提交，此后同一报表只读已完成的 Prepared Report，没有就返回空，不报错。③ 上游 schema 暴露 `user` 参数，AI 可以指定按哪个用户的匹配过滤跑（`get_filtered_data`）。`has_permission` 仍按会话用户判，所以是放宽可见范围，不是越权 | 开发守则「探针三条纪律」第 1、3 条；「不静默」；DEC-009「只读」 | 修 P3-01 时一并处理：包装函数固定 `user=frappe.session.user`、关掉 prepared 自动化或给执行时长设上限，描述里注明失败会留日志 | 延迟或不修 | 是否随 P3-01(a) 一起做 | 待裁决 |
| P3-05 | 低 | `configure_apps.py:81` | `Purchase Analytics` 的过滤键描述只写了 company、from_date、to_date、tree_type、range，漏了必填的 `doc_type`、`value_quantity`、`curves`（`purchase_analytics.js:35-99`）。按描述传参，实测 `AttributeError: 'NoneType' object has no attribute 'startswith'`。其余五张按描述传参能跑：BOM Stock Analysis 缺 warehouse 时报错，与描述「须传」一致 | TS-009-4「描述写明各报表常用过滤键」 | 补齐三个必填键及可选值；或者从清单里去掉这张，问 2 用不到它的维度 | 本Session修 | — | 待裁决 |
| P3-06 | 低 | `docker/README.md:250`、`docker/configure-apps.sh:6` | 示例 `--company HDTH` 不成立。演示站公司名是 `华东弹簧有限公司`（`HDTH` 是缩写），`resolve_company` 按 name 查（`configure_apps.py:132`），会报「公司 HDTH 不存在」，rc=1。不会静默出错，但照文档敲会失败 | TS-009-5 README 可照做 | 示例改为 `--company 华东弹簧有限公司`，或者让 `resolve_company` 也认 `abbr` | 本Session修 | 改文档，还是让脚本认缩写 | 待裁决 |
| P3-07 | 低 | `configure_apps.py:173-180` | 方案外夹带：写 `CRM Settings.enable_frappe_crm_data_synchronization=1`。它是 CRM 由 Deal 自动建客户的必要前提（不开时 `validate_frappe_crm_sync` 抛错），属合理补漏，但方案的配置表、SL-005 ①、SB 回执的逐字段贴值、README 都没提。日后有人照方案手工配，或排查「建不出客户」，查不到这一项 | F Spec 预设提示词 7（方案外夹带须申报） | 在 README「配置四个 App」节与 SL-005 记录里补这一字段及原因 | 本Session修 | 追认夹带（只补文档） | 待裁决 |
| P3-08 | 低 | `configure_apps.py:168-171、243-248、313-316` | 首跑时 `ERPNext CRM Settings.save` 会在 `validate` 里建自定义字段，DDL 走 `sql_ddl`，先 `commit()`（`database.py:451-457`）。之后的 `ensure_bot_and_functions` 若因「已有写类工具」抛 ConfigureError，`rollback()` 只能撤到 DDL 之后。CRM 段已经落库，输出却只有错误、不列已提交的改动；第二次跑 CRM 段又显示「无改动」。读码推断，未实测 | 开发守则「不静默」；TS-009「输出改动清单」 | 每段写完立刻打印该段改动；或者把写类工具检查挪到最前面（只读预检），再开始写 | 新Session修 | — | 待裁决 |
| P3-09 | 低 | `P1-S5-概况.md` 延迟需求登记册 SH-P1S5006 行 | 登记描述与实情不符。概况进度段说 IT-015／IT-019 并入了 SH-P1S5006，但该行描述只写 LiteLLM、报表通道、三问与 MODEL，没写：① `raven_dataset.py` 须整份重写＋`test_raven_dataset.py`；② `ai/queries.py` 四个死函数要删；③ `configure_raven` 只填一项就报错、而方案要求非密钥字段照写（SB 申报的偏离）；④ P3-01、P3-02。唤醒者只读登记册，会漏掉这些 | 流程规范 §12（登记册是唤醒时的唯一入口）；任务说明「登记描述与实情不符则报」 | 补全该行描述 | 本Session修 | — | 待裁决 |
| P3-10 | 观察 | `frappe_china/tests/raven_dataset.py:1-4、19-22、33-36`；R8 E 报告 IT-030 | ① 防误用只靠文件头注释。方案 Part3 TS-012 写的原命令 `bench execute frappe_china.tests.raven_dataset.build`／`teardown` 现在照样能执行。② `build` 用 `like "_FCT%"` 取公司，会挑中测试站夹具 `_FCT CRM 验证`，在它下面建乱码商机。③ R8 IT-030 说「teardown 会删掉 `_FCT CRM 验证`」与代码不符：teardown 不含 Company。真正的风险是 `force=True` 删 `_FCT` 前缀的 Item／BOM／Supplier 等，跳过链接校验，可能留下悬空引用 | 自证复核；开发守则「删记录不带 force」的精神 | 在 `build`／`teardown` 开头直接 `raise NotImplementedError(...)`；IT-030 的风险描述在收口时更正 | 延迟或不修 | — | 待裁决 |
| P3-11 | 观察 | `docker/.env.example:32-35` | 新增注释是英文单行「Raven local LLM (required only for Raven configuration)」，全文件其余注释都是中文；也没提 README 写明的「三个须一起设、不设 MODEL 取 gpt-4o」 | TS-009-5「加注释」；IT-029 的提示应在填值处可见 | 改成中文，补一句「三个须一起设；密钥不进任何文档」 | 本Session修 | — | 待裁决 |

## 本片盲区自述

- **没往这些方向找**：Raven 前端 `/raven` 的工具展示与手动调用；Insights 的权限层（需求 §4.7 已注明「直连 MariaDB 绕过权限」，不进演示，本片没展开）；CRM 前端 Form Script（`Create Quotation from CRM Deal`）内容是否随 CRM 升级漂移；Raven 写类型以外、可能有副作用的 `Custom Function`（站上现在没有）。
- **把握最低的是 P3-02**。它完全基于读 `agents_integration.py` 的回退路径，前提是「Local LLM 永远走强制回退」（`:514-515`）。如果用户的 LiteLLM 模型在第一轮就并行发出多个调用，或者上游后续改了这段，结论会变。第一次实测前，它只能当高风险假设。
- **P3-01 的定级**：判「高」，是因为报表通道是 DEC-009 明定的工具，且被三份产物当成已可用。若认为「Raven 还没接 LiteLLM，现在不影响任何功能」，也可降为「中」。修法（a）会推翻用户对 IT-014 的裁决，所以列了待裁决点。
- **P3-08 未实测**：DDL 是否在这里发生，取决于站上是否已有那三个自定义字段。两站都已有，常规重跑不会触发。
- **探针副作用**：本片在测试站留下两条 Error Log（name 见覆盖自证）。另外 `get_report_result` 在 `frappe.cache` 写了 `report_execution_time` 哈希（只是缓存）。几次运行都远短于 15 秒，六张报表的 `prepared_report` 已复查，仍为 0。
- 没有交叉核对 S4 及更早的历史行为。业务规则合规核只对照了 BR-001～007。
