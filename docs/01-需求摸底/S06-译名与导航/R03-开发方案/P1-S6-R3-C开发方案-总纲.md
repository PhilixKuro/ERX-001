# P1-S6 译名与导航 —— 开发方案·总纲

**来源需求**：[R2 B 需求文档](../R02-需求文档/P1-S6-R2-B需求文档.md) v1.0（需求 TS-001～013、AC-001～015）＋本轮 [C 讨论记录](P1-S6-R3-C讨论记录.md)（DEC-020～022）
**日期**：2026-10-09｜**编写者**：Claude（Opus 5.5）｜**执行者**：Claude（S6 概况的偏离：D 步执行者由 CodeX 改为 Claude）
**状态值与复核建议**：不在本文件——见 [P1-S6-R3-C回执](P1-S6-R3-C回执.md)

> **编号**：切片 `SL-`、任务 `TS-`、技术假设 `HT-` 为本方案内编号。**需求文档里也有 `TS-` 编号，二者不是一回事**，引用需求的任务一律写「需求 TS-00x」。决策 `DEC-`、遗留 `LG-`、被否决 `NV-` 沿用本 Stage 序号。
> **方案是只读依据**：执行进度只写 D 回执（每 Part 一份），不回写本方案。
> **路径**：凡写 `frappe_china/…` 均指 `frappe-bench/apps/frappe_china/frappe_china/…`（app 包目录）；`Spike/…` 指主仓库根下的 `Spike/`。

## 一、概述

**要做的事**：给 `frappe_china` 加一道译名自检并改造译名测试；把现金流量底稿改名为 `Cash Flow Worksheet`；修 S4 自有功能的四处小缺陷与分隔符；把六个 app 的界面缺口（约 5338 条）全部补成中文，演示线逐条定词、其余批量译后抽检；让两张发票的「未收款／未付款」在三处裸渲染点分得开；建「业务流程」首页图标与自有侧栏；修开账凭证跳总账显示全零；逐例复现「不刷新即不显示」；最后在演示站逐屏核、出新空账基准点。

**完成标准**（本方案的验收总口径）：

1. 各切片验收条件全部通过（§三索引，完整条件在各 Part）。
2. `frappe_china` 全量测试：S5 收口时 **215 条**全过，本方案新增测试另计，**只增不减**（AC-009）。
3. 需求文档 AC-001～AC-015 逐条有正向证据（截图、查询结果、脚本或测试输出），不以「没报错」代替。
4. 演示站最终状态：装序不变、`check_app_order` 为真；`HDTH` 科目 266；`Translation` 表 0 行；自检返回空清单；无测试数据残留；有一份本 Stage 收尾后的新空账基准点，`20261008_211805` 仍在。

## 二、Part 索引

| Part | 文件 | 内容 | 切片 | 任务 |
|---|---|---|---|---|
| 1 | [Part1](P1-S6-R3-C开发方案-Part1.md) | 译名基线脚本、译名自检与测试改造、底稿改名、S4 小缺陷与分隔符 | SL-001～003 | TS-001～005 |
| 2 | [Part2](P1-S6-R3-C开发方案-Part2.md) | 演示线档、批量档与抽检、裸渲染点、改数据按钮抽检 | SL-004～006 | TS-006～009 |
| 3 | [Part3](P1-S6-R3-C开发方案-Part3.md) | 业务流程图标与侧栏、树形点检、开账凭证跳转、不刷新六例 | SL-007～009 | TS-010～013 |
| 4 | [Part4](P1-S6-R3-C开发方案-Part4.md) | 演示站逐屏核与新基准点、全量回归与常驻文件 | SL-010 | TS-014～015 |

## 三、切片划分与验收（索引）

| 切片 | 功能点（需求编号） | 验收条件摘要（完整版在所在 Part） |
|---|---|---|
| **SL-001** 译名守卫 | 需求 TS-002；DEC-010／013；`PH-P1030` | 自检四项各有反证报失败、正常时返回空；覆盖清单用例与「清单每键在 csv」用例通过；`labels.py` 只容「库未就绪」 |
| **SL-002** 底稿改名 | 需求 TS-006；DEC-015；`PH-P1060` | 测试站在有一条底稿时 migrate 成功、记录在新表可打开、子表 `parenttype` 已改；搜索「现金流量」三者各不同名；S4 现金流量测试全过 |
| **SL-003** S4 小缺陷与分隔符 | 需求 TS-010；`PH-P1035`／`1041`／`1042`／`1063`／`1052` | 四处各有前后对比证据；分隔符不占全局键、英文界面显示 `a; b` |
| **SL-004** 演示线译名 | 需求 TS-001／003／007；DEC-002／003／014／016／019～022；`PH-P1011`／`1062` | 演示线面无缺口；演示线撞名组零残留；§4.2.4 点名用词逐条命中；按钮抽检表 20–40 词全「一致」 |
| **SL-005** 全量无缺口 | 需求 TS-004；DEC-001／017；RW-05 | 基线脚本重跑缺口 0（除白名单）；分层抽检 100 条不可用 ≤ 10 |
| **SL-006** 裸渲染点 | 需求 TS-005；`PH-P1010` | 三条出路各有实测记录；落地处销售发票列表徽标、筛选下拉、只读 status 显示「未收款」，采购发票显示「未付款」，`On Hold` 徽标不变 |
| **SL-007** 业务流程导航 | 需求 TS-008／009；DEC-004～007／009／018／020／021 | 首页第一个图标「业务流程」；侧栏列全；原有图标与侧栏 `modified` 不变；五个树形或 `is_tree` DocType 点进不空白 |
| **SL-008** 开账凭证跳转 | 需求 TS-011；`PH-P1061` | 期初库存调账与期初日记账凭证跳总账显示分录；普通凭证行为不变 |
| **SL-009** 不刷新六例 | 需求 TS-012；`PH-P1002` | 六例每例有复现结论与处置 |
| **SL-010** 逐屏核与收尾 | 需求 TS-013；AC-001／002／015 | 屏清单每屏截图「通过」；每张侧栏分节无重名；演示站自检空、`Translation` 0 行；新基准点 |

**执行每个切片前，对照该切片验收条件检查方案覆盖性——如发现按方案写出的代码无法通过验收条件，暂停反馈，不硬写。**

## 四、关键架构决策（本方案新定，C 步职责内）

| # | 决策 | 理由 |
|---|---|---|
| **A1** | **自检函数放 `frappe_china/translation_check.py`**：`find_problems() -> list[str]`（纯查询）＋ `run() -> list[str]`（供 `bench execute`，打印并返回）。与 `realtime_check.py` 同层 | 译名是全 app 的事，不属 `cn_tax` 或 `accounting`；同层已有先例 |
| **A2** | **`.mo` 的检查位置改为两处**：app 包目录下任何 `.mo`，**加** `sites/assets/locale/*/LC_MESSAGES/frappe_china.mo` | 需求 §4.3 写「app 目录下无 `.mo`」，但 `bench build` 编出的 `.mo` 实际落在 `get_mo_path()` = `sites/assets/locale/{lang}/LC_MESSAGES/{app}.mo`（`frappe/gettext/translate.py:61-62`），只查 app 目录查不到真正生效的那个。见 §六 |
| **A3** | **覆盖清单是测试侧的一个数据模块** `frappe_china/tests/translation_overrides.py`：`OVERRIDES: dict[str, Override]`，键与 csv 键同形（两列行为源词，三列行为 `源词:context`） | 需求 §4.3 要求清单在测试侧、每条带依据；做成数据模块而非散在用例里，便于 review 与按依据计数 |
| **A4** | **csv 加两条结构用例**：无重复键（同键后行静默盖前行，`translate.py:207-212`）；每行 2 或 3 列 | 5000 余行时手工无法发现重复；重复键是「译名被静默盖掉」的第四种形态 |
| **A5** | **desk 前端补丁集中在两个文件**：`frappe_china/public/js/desk_patches.js`（`app_include_js`，类原型与全局函数的覆盖）与 `frappe_china/public/js/invoice_list.js`（`doctype_list_js`，两张发票的列表设置）。`app_include_js` 由字符串改为列表 | ADR-0009 要求每处覆盖登记；两个文件对应两种加载时机（全局早于表单脚本 / 随 DocType meta 下发），分开放才看得清时机 |
| **A6** | **ADR-0009 的覆盖登记表落在 `frappe_china/README.md` 新增一节「desk 前端覆盖登记」**，每处一行：文件:行／覆盖了什么（类.方法或全局函数）／依赖上游的什么行为（文件:行，锁定 commit）／失效症状／复验法 | ADR-0009 只说「每处登记」，没定在哪；README 随 app 仓库走、与补丁同提交，升级时就在手边。项目里此前没有这张表，本 Stage 是第一处登记 |
| **A7** | **自有侧栏条目 label 的取法**（DEC-020 的落地）：同一对象在 erpnext 原有侧栏里已有 label 的照抄（如 `Account` 取 `Chart of Accounts`、`UOM` 取 `Unit of Measure (UOM)`）；没有的取对象自身名（DocType 名／Report 名）。URL 项没有对象名：`/crm` 三项沿用 CRM 已有源词 `Leads`／`Deals`／`Dashboard`，`/raven` 新起 `AI Assistant`。分节标题新起两个源词 `Master Data`、`Finance`，其余沿用已有源词。新起的四个源词（`Master Data`／`Finance`／`AI Assistant`／`Business Flow`）原本都无译文 | 照抄原有侧栏用词，自有侧栏与原有侧栏同一对象同名；新起的源词原本无译文，加 csv 不波及他处 |
| **A8** | **首页排序用 `idx = -1`** | 现有顶层可见图标 `idx` 最小为 0 且有多个（演示站实查），同 `idx` 按 label 字母序（`desktop.js:686-691`）；`idx` 列为有符号整数，导入时保留（`import_file.py:229-238`、`base_document.py:609-610`） |
| **A9** | **侧栏与图标的 json 手写为主，开发站界面排布为辅**；每次改 json 必须把 `modified` 调大 | LG-003 已实测 `developer_mode` 下 `save()` 写回 `frappe_china`；但导入只比 `modified`（`import_file.py:123-142`），手写时不调大即静默不生效 |
| **A10** | **底稿改名补丁放 `[pre_model_sync]`** | 放 post 段时 `sync_all` 先按新 json 建出 `Cash Flow Worksheet` 与空表，随后改名撞「同名 DocType 已存在」与 `RENAME TABLE` 目标已存在（`rename_doc.py:351,367-368`）；erpnext 四个 DocType 改名先例都在 pre 段 |
| **A11** | **裸渲染点出路 1 的落法不用 `states`，改为在 `doctype_list_js` 里包一层 `get_indicator`**；出路 2 的落法不用 Property Setter，改为在同一文件的 `onload` 给筛选控件补 `df.context`。两条原定做法仍各实测一次留证据 | 读码：`states` 分支先于 `get_indicator`（`indicator.js:82-91`），配了会盖掉采购发票的 `On Hold`／`Temporarily on Hold` 徽标（`purchase_invoice_list.js:25-31`）；`DocField` 没有 `context` 字段，筛选控件的 df 是新建的、不复制任何附加属性（`base_list.js:1238-1247`）。见 §六 |
| **A12** | **分隔符走 context 行**：`_("{0}; {1}", context="Month End Closing Voucher")`，经一个本地辅助函数拼接 | 英文界面仍显示 `a; b`；不占全局键，他 app 同源词不受影响（需求 §4.2.4 要求）；改用本 app 专属源词会让英文界面露出后缀 |
| **A13** | **逐屏核用宿主无头 Chrome 走 DevTools 协议**（沿用 `Spike/V16-cdp-run.js` 的做法），自动抽取屏上可见文本找英文词，并截图 | 23 环节约 70 屏，人工逐屏截图不可复现；自动抽文本给出「无英文词」的正向证据，截图供人复核 |
| **A14** | **演示站逐屏核的数据在核完后整体撤回**：先备份（即新基准点候选）→ 造演示数据并逐屏核 → 再备份一份测试态留档 → 恢复第一份 | AC-015 要基准点干净；S5-R12 同一做法 |

## 五、技术假设

| 编号 | 假设内容 | 状态 | 验证方式 | 不成立时 |
|---|---|---|---|---|
| HT-001 | `frappe_china` 的 `doctype_list_js` 拼在 erpnext 自带 `*_list.js` 之后执行，执行时 `frappe.listview_settings["Sales Invoice"]` 已存在，可包装其 `get_indicator` | 读码（`desk/form/meta.py:100,112,284-299`；`model.js:255-258`） | Part2 TS-008 第 2 步 | 暂停反馈 |
| HT-002 | 列表 `onload` 时标准筛选控件已建好、在 `page.fields_dict` 里；改 `df.context` 并清 `last_options` 后重设选项即带 context | 读码（`list_view.js:366`；`base_list.js:31-32,288,305`；`page.js:889`；`select.js:69,82`） | Part2 TS-008 第 3 步 | 不暂停：该渲染点保留官方原译（DEC-080 对该点继续有效），记不可行 |
| HT-003 | 运行期替换 `frappe.form.formatters.Select` 对销售发票只读 `status` 生效（`status` 字段无 `df.formatter`） | 读码（`formatters.js:52-54,421-445`；`base_input.js:177-178`） | Part2 TS-008 第 4 步 | 不暂停：同上 |
| HT-004 | 在 `app_include_js` 里改 `erpnext.stock.StockController.prototype.show_general_ledger`，库存凭证、库存调账打开时生效（子类无同名方法，erpnext bundle 先于本 app 脚本加载） | 读码（`stock_controller.js:114-134`；`stock_reconciliation.js:341`；子类 grep 无覆盖） | Part3 TS-012 | 暂停反馈 |
| HT-005 | `frappe_china` 经 `doctype_js` 注册的 `Journal Entry`／`Payment Entry` `refresh` 在 erpnext 的 `refresh` 之后跑，可先 `remove_custom_button` 再加带开账参数的按钮 | 读码（`script_manager.js:122-138,161-175`；`journal_entry.js:79-96`；`payment_entry.js:423-441`） | Part3 TS-012 | 不暂停：该单据记不可行，库存类照做 |
| HT-006 | `rename_doc("DocType", …, force=True)` 在补丁中改表名、改子表 `parenttype`、改 Link `options`，`reload_doc` 载入新 json；全新装站把补丁记为已跑、直接建新表 | 读码（`rename_doc.py:170,396-412,616-645`；`doctype.py:685-692`；`installer.py:357-358`） | Part1 TS-004 | 暂停反馈 |
| HT-007 | 两站都没有 `Desktop Layout` 快照，新图标会出现在首页 | **已验证**（两站 `tabDesktop Layout` 0 行，本轮实查） | — | — |
| HT-008 | 从自有侧栏进入的单据，经「创建 → 下游单据」或报表跳转时侧栏保持（`resolve_sidebar()` 第 1 条） | 读码（`sidebar.js:709-744`） | Part4 TS-014 逐屏记 | 不暂停：记下换走的屏与路径，屏清单结论里写明；修法另报用户 |
| HT-009 | 首页图标的 svg 能匹配上：容器内 Python 拼出的资源路径是正斜杠（`boot.py:538-540` 用 `os.path.join`） | 读码；bench 跑在 Linux 容器内 | Part3 TS-010 第 5 步 | 暂停反馈 |
| HT-010 | csv 三列行对 Python `_()` 与 JS `__()` 都生效，键为 `源词:context` | **已验证**读码（`translate.py:207-211`；`utils/translations.py:4,38-44`；`translate.js:5-18`） | — | — |
| HT-011 | `/crm`、`/raven` 前端取的是全站合并字典，csv 对它们同样生效 | **已验证**读码（`crm/api/__init__.py:13-19`；`raven/apps/web/src/main.tsx:24` 取 boot 的 `__messages`，即 `get_all_translations`） | — | — |
| HT-012 | 自有侧栏与图标在 `developer_mode=1` 下 `save()` 写回 `frappe_china` 的 json（LG-003） | **已验证**（测试站实测：`insert()` 后 `workspace_sidebar/lg003_probe_sidebar.json` 与 `desktop_icon/lg003_probe_icon.json` 写出；删除后两文件随之删除；探针已清） | — | — |
| HT-013 | 批量档可用率 ≥ 90%（RW-05） | 未验证 | Part2 TS-007 抽检 | 按 DEC-017：> 10 条不可用停下报用户 |
| HT-014 | 侧栏 URL 项（`/crm/…`、`/raven`）对非 Administrator 用户可见 | 未验证（`desk_views.py:68-` 对 Administrator 恒真，对 URL 类型的判定未读完） | 不在本 Stage 验（演示用户归 S7） | 不暂停：写进 D 回执交 S7 |
| HT-015 | `show_opening_entries=1` 时总账把 `is_opening=Yes` 的行列进明细 | 读码（`general_ledger.py:564-568`） | Part3 TS-012 | 暂停反馈 |

## 六、相对需求文档的偏离与更正

| 需求原文 | 本方案 | 依据 |
|---|---|---|
| §4.6.2 侧栏表「条目（中文）」列 13 项（发货单、采购收货、库存凭证、工单等） | 沿用对象现行官方译名，不为侧栏覆盖、不另起源词；演示线撞名组照 DEC-002 定词 | DEC-020；A7 |
| §4.3 自检第 2 项「app 目录下无 `.mo`」 | app 包目录 ＋ `sites/assets/locale/*/LC_MESSAGES/frappe_china.mo` 两处 | A2 |
| §4.2.6 出路 1「给两个 DocType 配 `states`」 | 实测一次留证据；落法改为包 `get_indicator` | A11（读码判 `states` 会盖掉 `On Hold`） |
| §4.2.6 出路 2「Property Setter 给该字段设 `df.context`」 | 实测一次留证据；落法改为列表 `onload` 里补 `df.context` | A11（`DocField` 无 `context` 字段、筛选控件不复制附加属性） |
| §4.2.6 出路 3「能否以前端补丁做到」 | 能：替换 `frappe.form.formatters.Select`，不改 frappe 源码 | HT-003；读码 |
| §4.2.4 `Dr`「落地前先查 `tabSalutation`」 | 已查：演示站 0 条、测试站含英文 `Dr`；照落 | DEC-022 |
| §4.6.1「显示名『业务流程』（候选）」 | 定为 `Business Flow` → 业务流程 | DEC-021 |
| §4.2.4 三个「Claude 定」的词 | 用户认可，照落 | DEC-021 |
| §4.8.1 `PH-P1063`「二选一留 C 步」 | 取「报错时告诉正确做法」，且只在明细为空且余额不符时出这句 | Part1 TS-005；改动最小、不改校验语义 |
| §4.8.2「候选做法跳转时带 `show_opening_entries=1`」 | 库存类单据覆盖 `StockController.show_general_ledger`；日记账凭证与收付款凭证（二者都有 `is_opening` 字段）经 `doctype_js` 换按钮 | Part3 TS-012；见回执拿不准处 |
| §4.6.3「从顶部搜索直接进单据时第 2 条可能把侧栏换走」 | 读码更正：第 2 条在中文界面基本不命中（`sidebar_item_map` 以译后 label 为键、查时用英文 DocType 名，`sidebar.js:720,789-798`）；真正换走侧栏的是第 3 条「按 DocType 所属 app 过滤」——从搜索直接进 erpnext 的单据时会落回 erpnext 的侧栏 | 读码；演示全程经侧栏与「创建」按钮走，屏清单不受影响（HT-008） |
| §4.5「引用」7 个文件 | 实为 8 个（另有 `README.md:96-112` 的目录路径） | 子 Agent grep |
| §4.6.4 LG-074「`icon_html` 有写无读」 | 读码更正：当前源码 `menu.js:94-97` 读 `icon_html`；`sidebar_header.js:359-362` 在 item 无 `icon` 与 `icon_url` 时输出 `src="undefined"`，但它挂的 `.sidebar-header-menu` 在模板里不存在，疑为死代码。自有图标照放 svg，结论不变 | 读码 |

## 七、并行开发说明

本 Stage 的任务多数改同一份 `zh.csv` 或同一个测试站，**原则上不标并行**。两处可并行：

| 可并行组 | 任务 | 各自写入范围 |
|---|---|---|
| ① | Part2 TS-007 的批量翻译 | 分块各写 `Spike/P1S6R4-batch/part-{nn}.csv`（每块一个文件、互不相交），**合并进 `zh.csv` 只由主 Session 做一次**；可派子 Agent 分块并行译，每块带同一份术语表 |
| ② | Part1 TS-004（底稿改名）与 Part2 TS-009（按钮抽检） | 前者写 `cn_tax/doctype/`、`patches/`、`tests/`；后者只读 erpnext 源码、产物是 D 回执里的抽检表 |

## 八、执行顺序

```
Part1  TS-001 基线脚本重跑 ─→ TS-002 自检函数 ─→ TS-003 测试改造与覆盖清单
                                      └─→ TS-004 底稿改名（先造一条底稿，再改代码、migrate）
                                                └─→ TS-005 S4 四处小缺陷与分隔符
          │
Part2  TS-006 演示线档（含点名用词、Dr、Timesheet、撞名定词）
          └─→ TS-007 批量档、分层抽检 ──(不可用 > 10 即停)
          └─→ TS-008 裸渲染点三条出路
       TS-009 按钮抽检（只读，可与 TS-004 起任意时点并行；定稿译名在 TS-006 之后写进 csv）
          │
Part3  TS-010 业务流程图标与侧栏 ─→ TS-011 树形点检
       TS-012 开账凭证跳转
       TS-013 不刷新六例（TS-010 之后；例 1、5 并入 TS-011）
          │
Part4  TS-014 演示站：migrate → 自检 → 备份 → 造数逐屏核 → 测试态备份 → 恢复 → 新基准点
          └─→ TS-015 全量回归、开发守则、README 覆盖登记、项目概况回写
```

## 九、执行纪律（给执行者，随方案走）

1. **切片前反查**：执行每个切片前，对照该切片验收条件检查方案覆盖性——如发现按方案写出的代码无法通过验收条件，暂停反馈，不硬写。
2. **假设先验**：任务依赖 §五中「未验证」或「读码」的假设时，先验掉再写；不成立按该行「不成立时」处理，写「暂停反馈」的就停下来报用户。
3. **中断续跑**：开工即建 D 回执（每个 Part 一份，命名 `P1-S6-R4-D回执-Part{N}.md`），预填全部任务为「未开始」；每做完一个任务当场回写。中断后从第一个未完成的任务续做，**不回写本方案**。
4. **站点安全**：
   - **Part4 TS-014 之前不得对 `erx.localhost` 做任何写操作**（只读查询、截图可以）；全部实测、造数在 `test.localhost` 上做。
   - 动演示站前**先核 `20261008_211805` 那套备份仍在 `docker/backups/` 根目录与 `保留-S5R12后/`**，再备份。
   - 看测试站界面须在容器内另起 `--site test.localhost serve --port 6787`，用完停掉；**停服务与恢复备份分两条命令跑**。
   - 重启 `bench start` 的进程、`bench build`、`bench clear-cache` 属本地可逆操作，可直接做，在回执里记一笔。
5. **测试纪律**（沿用 S4／S5）：自有测试不 import `erpnext.tests.utils`；涉及语言的断言显式设 `frappe.local.lang = "zh"`；会触发 `frappe.log_error` 的测试，清理只删能证明是自己造的行；在 app 目录或 `sites/assets` 下临时放文件的反证用例，`try/finally` 删掉，并断言删干净。**回执里分开报「通过」与「跳过」的条数**。
6. **译名纪律**：
   - **一切译名只写 `frappe_china/translations/zh.csv`**；开发期可在界面上用 `Translation` 记录试词，**用完即删**，每个任务收尾跑一次自检确认 `Translation` 为 0 行。
   - 覆盖官方译名的每一行，同一提交里进覆盖清单（A3），写依据。
   - 改 csv 后 `bench --site test.localhost clear-cache` 再看效果（合并字典有缓存，`translate.py:162`）。
7. **前端补丁纪律**：每加一处覆盖，当场在 README「desk 前端覆盖登记」节登一行（A6）；追加型改动（新增按钮、新增监听）不必登记，但须在 D 回执说明为何判为追加。
8. **改 json 必调 `modified`**：自有侧栏、图标、DocType 的 json 每次改动都把 `modified` 调大（A9），否则 `bench migrate` 静默不导入。
9. **版本管理**：主仓库与 `frappe_china` 仓库的改动都只写不提交；提交、推送、打 tag 均须用户许可（CLAUDE.md「版本管理操作规则」）。erpnext、frappe 与四个官方 App 的目录不做任何改动。
10. **不静默**：查不到、算不出、对不上一律报错或告警，不输出空列表了事（开发守则「静默失败」）。
11. **最后一个任务（TS-015）做全量回归**，并复核演示站最终状态（§一完成标准第 4 条）。
