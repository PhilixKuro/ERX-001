# P1-S6 译名与导航 —— 开发方案（R9：R8 E 报告回流修补）

**来源**：[R8 E 确认报告](../R08-确认/P1-S6-R8-E确认报告.md)「交出去向」中的 `出方案修` 各项：IT-033～038、IT-041、IT-043、IT-048，清单外发现 5 条，以及演示站复核时补截 BOM／WO 普通取消框；本轮 [C 讨论记录](P1-S6-R9-C讨论记录.md) DEC-039～041。需求依据不变：[R2 B 需求文档](../R02-需求文档/P1-S6-R2-B需求文档.md) v1.0。
**日期**：2026-10-12｜**编写者**：Claude（Opus 5.5）｜**执行者**：Claude（S6 概况的偏离：D 步执行者由 CodeX 改为 Claude）
**状态值与复核建议**：不在本文件，见 [P1-S6-R9-C回执](P1-S6-R9-C回执.md)

> **与前两版方案的关系**：R3 方案（[总纲](../R03-开发方案/P1-S6-R3-C开发方案-总纲.md)＋Part1～4）是 S6 的主方案，[R6 方案](../R06-开发方案/P1-S6-R6-C开发方案.md)补改过一轮，两者都仍有效。本方案只**补**下列各节点名的部分，不替换其中任何验收条件。R3 总纲 §九的执行纪律对本方案同样适用（第 3 条的回执命名改为本方案 §八，第 4 条改为：TS-036 之前不得对 `erx.localhost` 做写操作，动演示站前先核 `20261012_163036` 那套备份仍在）。
> **编号**：接 R6 续编——切片从 `SL-016` 起，任务从 `TS-025` 起，技术假设从 `HT-021` 起，架构决策从 `A23` 起。E 报告的 `IT-` 编号照原样引用。
> **路径**：`frappe_china/…` 指 `frappe-bench/apps/frappe_china/frappe_china/…`；`Spike/…` 指主仓库根下的 `Spike/`；上游路径都相对 `frappe-bench/apps/`。

## 一、概述

**要做的事**：R8 E 实测发现，演示站 15 屏英文都能在 `frappe_china` 内修掉（IT-033～037）。此外还有一个分组按钮裸串（IT-038）、一个对话框撞名（IT-041）、Raven 个人状态被演示线定词波及（IT-048），以及清场取法的缺口（IT-043）和 5 条定词。本方案把这些落成：

1. **Desk 前端补丁**：列表筛选按钮与首列排序提示、分组按钮裸串、报表 DocType 名列、修改记录的 `null`、「选工时单」对话框的日期标签；
2. **独立前端补丁**：CRM 页 `lang`、翻页「of」、`Empty`、侧栏占位；Raven 页 `Available` 改取 context 行；
3. **csv 定词与取法**：`_app_source_strings()` 补「字面量按键取用」一类和 Workspace Sidebar／Desktop Icon 的 json；称呼 4 词（DEC-039）、Raven `Available`（DEC-040）、清单外 4 条（DEC-041）、`Inter Company Invoice`；
4. **演示站复核**：按 R3 总纲 A14 走一轮（备份 → 造数核屏 → 恢复 → 新基准点），顺带补截 BOM／WO 的普通取消确认框。

**完成标准**：

1. 本方案各切片验收条件全部通过；
2. `frappe_china` 全量测试只增不减（R8 当场修后 257 条为基线），Node 用例以 29 条为基线；
3. 演示站逐屏核**全部屏 `pass=true`**，包括 R7 未过的 15 屏——这是 S6 完成标志第 1 条的落点；
4. 演示站最终状态同 R3 总纲 §一第 4 条，基准点用本轮新出的那一份。

## 二、关键架构决策（本方案新定）

| # | 决策 | 理由 |
|---|---|---|
| **A23** | **R9 每处前端补丁统一形态**：包住上游原方法，完整委托（原 receiver、原参数、原返回值）；只在 `frappe.boot.lang === "zh"`（独立前端为 `config.lang`）时改动；在包装函数上打 `__frappe_china_*` 幂等标记，重复加载不叠加；上游类或方法不存在时 `console.warn("[frappe_china] …")` 后跳过，不抛异常。每处补丁当场在 README 登记一行（接入点／覆盖文件／上游依赖：文件:行与锁定 commit／失效症状／复验法），并配 Node 用例覆盖：中文生效、英文会话不变、重复加载不叠加、上游缺失只告警 | 沿用 ADR-0009 与 R3 总纲 A6 的做法；R5／R8 两轮都查出补丁漏登记、漏用例，这里把形态写成验收项 |
| **A24** | **报表 DocType 名列按（报表，字段）白名单翻译**，只改显示值，不开 `add_translate_data` | `add_translate_data` 会对整行字符串调 `_()`，波及科目名、备注等用户数据（R8 IT-034 建议）。白名单只碰装 DocType 名的列 |
| **A25** | **修改记录 `null` 用只作用于时间线的 MutationObserver 改写，并起草上游缺陷报告**（R8 E 代裁）。上游报告只写草稿，**向 GitHub 提交须用户另行许可** | 包 `frappe.utils.html2text` 属全局行为改动，副作用难验，上游修好后也不会自动退场；`format_content_for_timeline` 是模块内函数，包不到 |
| **A26** | **CRM 侧栏占位分两处修**：服务端用 `override_whitelisted_methods` 包 `get_sidepanel_sections`，只改上游自动生成的占位（`"Add " + label + "..."`、`"Select " + label + "..."`）与只读提示；User 型字段的占位由前端拼串（`SidePanelLayout.vue:157`，不读 `field.placeholder`），在 CRM 注入脚本里限定于侧栏改写 | 两处的生成点不同；只改自动生成的占位，用户自定义的占位保持原样 |
| **A27** | **独立前端的 context 映射表**：Raven 页内 `RAVEN_CONTEXT_KEYS = {"Available": "Raven User"}`，桥接字典时把无 context 键改为取 `键:context` 的译文；该 context 行不存在时保留原值并告警 | Raven 源码以无 context 的 `_("Available")` 取词（`Profile.tsx:28`、`useSetAvailability.ts:9`），而无 context 的 `Available` 已按演示线定为「工位可用」（R7 DJ-001）。映射只作用于 Raven 页，不动 Desk 工作站 |
| **A28** | **`_app_source_strings()` 的取法补三类**：① JS 里 `translate(` 别名的字面量调用；② **命名约定**：Python 模块级常量、JS 标识符，名字以 `SOURCE`／`SOURCES` 结尾（不区分大小写）的，其中的字符串字面量都算本 app 源词；③ `workspace_sidebar/*.json` 与 `desktop_icon/*.json` 的 `title`、`label` 及 `items[].label`。函数拆成「读文件」与「从文本取词」两层，后者是纯函数，可喂构造文本测试 | R7 偏离第 0 条：清场误删 15 行，根因是取法认不出按键取用的键（IT-043）。约定比逐个点名更稳，新增的取用点只要守约定就自动被认出 |

## 三、技术假设

| 编号 | 假设内容 | 状态 | 验证方式 | 不成立时 |
|---|---|---|---|---|
| HT-021 | `frappe_china` 的 `app_include_js` 在 frappe 的 `list`／`form`／`report`／`desk`／`controls` 各 bundle 之后加载，故 `desk_patches.js` 执行时 `frappe.ui.FilterGroup`、`frappe.views.ListView`、`frappe.ui.Page`、`frappe.views.QueryReport`、`frappe.ui.Dialog` 都已定义 | 读码（`frappe/hooks.py:25-34` 的 bundle 次序在前，`www/desk.html:65` 逐个输出；现有 `ControlButton` 补丁已在用同一前提） | TS-035 测试站实页：控制台无 `[frappe_china] … unavailable` 告警，且各补丁的包装标记为真 | 暂停反馈 |
| HT-022 | CRM 页 `<html lang="en">` 改为 `lang="zh"` 后，ECharts 按 `document.documentElement.lang` 取中文 locale，且不影响样式 | 读码（`crm/frontend/node_modules/echarts/lib/core/locale.js:55-58`；CRM 构建产物 css 中 `:lang(`／`[lang` 选择器 0 处，C 步 grep 过） | TS-035：CRM 看板截图月份为中文，线索、商机列表与侧栏版式和改前截图一致 | 不暂停：撤掉 `lang` 改动，把月份缩写按 `Jan`～`Dec` 进 CRM 图表区的限定翻译，回执写明 |
| HT-023 | CRM 前端经 `/api/method/crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_sidepanel_sections` 调用时，走 `override_whitelisted_methods` | 读码（`frappe/__init__.py:1577-1580` 的 `override_whitelisted_method`，取最后一个覆盖；`crm/hooks.py` 未覆盖该方法） | TS-034 Python 用例：`frappe.override_whitelisted_method(原路径)` 返回本 app 路径；TS-035 实页看占位 | 暂停反馈 |
| HT-024 | Raven 页 `frappe.boot.__messages` 是 `get_all_translations("zh")` 的全量合并字典，含 csv 的 context 键 `Available:Raven User` | 读码（`frappe/boot.py:234`、`translate.py:129-132,203-211`） | TS-032 测试站：取 Raven 页 boot，断言该键存在 | 暂停反馈 |
| HT-025 | 注入脚本（经典脚本，位于 `</body>` 前）在 Raven 入口模块（`type="module"`，延后执行）求值 `STATUS_OPTIONS` 之前运行 | 读码（`raven/www/raven.html:169` 是 module 脚本；现有 `bridgeMessages` 靠的是同一前提，R5 已实测首屏为中文） | TS-035：Raven 设置 → 个人资料，状态下拉显示「有空」 | 不暂停：改为在注入脚本里对该下拉的选项文本做限定改写，回执写明 |
| HT-026 | 已提交但无已提交下游单据的 BOM、Work Order，点「取消」走 `frappe.confirm` 普通确认框，不走「取消所有单据」对话框 | 读码（R6 HT-020 所引 `form.js:1068-1071`；R8 截到 `_cancel_all` 是因为那两张单据有下游） | TS-036 第 6 步：截图 `dialog_kind=confirm`，截后 `docstatus` 不变 | 暂停反馈 |
| HT-027 | 分组按钮的 label 在渲染前过一次 `__()`，不会破坏上游按 label 查按钮：`remove_inner_button` 本就先翻译再查（`page.js:673-677`）；`change_inner_button_type` 带分组调用时按原 label 查（`page.js:686-693`） | 读码，**未穷举**带分组的裸串调用 | TS-028 第 1 步：grep `erpnext`、`hrms` 的 `add_custom_button(` 首参为字面量且带分组的全部调用，再逐个查有无以原英文 label 调 `change_custom_button_type`／`remove_custom_button` 带分组 | 不暂停：有冲突则把补丁收窄为白名单 `RAW_GROUP_LABELS = {"Inter Company Invoice"}`，回执写明 |

## 四、切片划分与验收

| 切片 | 功能点 | 验收条件 |
|---|---|---|
| **SL-016** Desk 列表与分组按钮 | IT-033、IT-038；A23 | ① 中文会话下，列表筛选按钮的 `title`：1 个条件为「已应用 1 个筛选条件」，3 个为「已应用 3 个筛选条件」，0 个为「已应用 0 个筛选条件」（上游 0 个时也写 title），文字取自 csv 键 `{0} Filter Applied`／`{0} Filters Applied`；按钮正文、`btn-primary-light` 类与上游一致。② 列表首列（Subject 列）表头 `title` 为 `__("Click to sort by {0}", [__(label, null, doctype)])`，如工单列表为「点击按成品排序」；`get_header_html()` 返回的其余部分与原方法逐字相同（Node 用例对比）。异常路径：原返回值里找不到上游那段错误 title 时原样返回，不抛异常。③ `add_inner_button` 带分组时，下拉项的文字与 `data-label` 都是 `__(label)`；label 本已是中文、或不带分组的按钮，结果与上游逐字相同；移动端菜单项 `分组 > 按钮` 同样是中文。采购发票「创建」下显示「公司间销售发票」。④ 英文会话三处都不变；`FilterGroup`、`ListView`、`Page` 任一缺失只告警、其余补丁照常生效；重复加载不叠加 |
| **SL-017** 报表 DocType 名列 | IT-034；A24 | ① `REPORT_DOCTYPE_COLUMNS = {"General Ledger": ["voucher_type", "against_voucher_type", "party_type"], "Stock Ledger": ["voucher_type"]}` 内的列，单元格显示 `__(value)`，如「采购入库」「日记账凭证」；`title` 属性跟随显示值。② 底层数据不变：`frappe.query_report.data[i].voucher_type` 仍是英文 DocType 名；`voucher_no` 链接的路由仍指 `/desk/purchase-receipt/…`。③ 白名单外的报表与字段，单元格显示与上游逐字相同（Node 用例拿非白名单报表与非白名单字段各验一次）；空值、`null` 原样经原 formatter；Stock Ledger 自带的 `report_settings.formatter`（红绿数量）照常生效。④ 英文会话不变；`QueryReport` 缺失只告警 |
| **SL-018** 修改记录 `null` | IT-035；A25 | ① 表单时间线里修改记录的 `<b>null</b>`、`<b>undefined</b>` 显示为「（空）」（csv 键 `(Empty)`，本 app 自有源词）；只匹配 `.new-timeline .timeline-content` 内、`textContent` 恰为 `null` 或 `undefined` 的 `<b>`。② 时间线外的 `<b>null</b>`（Node 用例构造一个在表单字段区的）不变；时间线内 `textContent` 为 `null value` 之类的 `<b>` 不变。③ Observer 只建一个（重复加载不叠加）；英文会话不改。④ `Spike/P1S6R9/upstream-it035.md` 有上游缺陷报告草稿：复现步骤、`version_timeline_content_builder.js:411-418` 与 `utils.js:269-273` 的根因、建议修法（`html2text` 对 `null`／`undefined` 返回空串，或 `format_content_for_timeline` 先判空）；草稿**未外发**，回执写明待用户许可 |
| **SL-019** CRM 独立前端 | IT-036、IT-037；A26 | ① 渲染出的 CRM 页 html 恰含一处 `<html class="h-full" lang="zh">`、不含 `lang="en"`；上游模板里找不到 `<html class="h-full" lang="en">` 时，`test_website_translation` 的新用例失败并在消息里写明「上游 crm.html 的 html 标签已变」（异常路径：上游改了模板，测试当场发现）。② CRM 看板月份为中文（HT-022）；图表区的 `Empty` 显示「空」，带百分比的 `Empty (12.5%)` 显示「空 (12.5%)」。③ 列表翻页处：前后都是数字的「of」显示「/」，同一容器内的 `Load More` 显示「加载更多」；不夹在两个数字之间的「of」（Node 用例构造一条记录文本）不变。④ 侧栏：`override` 返回值里，上游自动生成的占位改为 `_("Add {0}...").format(_(label))`／`_("Select {0}...").format(_(label))`，只读提示改为 `_()` 译文；字段原本就设了 `placeholder` 的保持原样；该 DocType 无侧栏布局时返回 `[]`；英文会话下返回值与上游逐字相同（Python 用例逐项对比）。⑤ User 型字段占位「单选 Lead Owner...」在侧栏内显示为 `Select {0}...` 的译文套 CRM 运行时 `__(label)`；侧栏外同形文本不变 |
| **SL-020** 对话框与 Raven 限定改词 | IT-041、IT-048；DEC-040；A27 | ① 销售发票「获取物料 → 工时单」打开的「选工时单」对话框：`from_time`、`to_time` 两个标签分别显示 `From Date`、`To Date` 的译文（现为「起始日期」「截止日期」）。标题不是该对话框、或字段名不符的对话框不变（Node 用例构造一个带 `from_time` 的其它对话框）。② Raven 页 `frappe._messages["Available"]` 等于 csv 的 `Available:Raven User`（「有空」），设置 → 个人资料与用户菜单的状态选项显示「有空」；Desk 中 `Raven User` 表单的 `availability_status` 下拉与只读显示也是「有空」；Desk 工作站状态的 `Available` 仍是「工位可用」。③ 该 context 行不存在时，Raven 页保留无 context 译文并告警一次（Node 用例）；已有运行时词条照旧不被覆盖（沿用 `bridgeMessages` 现有用例） |
| **SL-021** csv 定词与取法 | IT-043、清单外 5 条；DEC-039、041；A28 | ① `_app_source_strings()` 的结果包含 R8 `Spike/P1S6R8-E/sl012/literal_keys.json` 所列 25 键、`CN Tax`，以及本方案新增的全部自有键（`{0} Filter Applied`、`{0} Filters Applied`、`(Empty)`、`Add {0}...`、`Select {0}...`）。② 纯函数 `_source_strings_from_text(name, text)` 的判别力用例：构造 Python 片段 `FOO_SOURCES = ("A", "B")`、`BAR_SOURCE: Final[str] = "C"`、`OTHER = ("D",)`，断言取到 A、B、C，取不到 D；构造 JS 片段 `translate('E')`、`const sources = {x: new Set(['F'])}`、`translateLabel('G')`，断言取到 E、F，取不到 G；构造 Workspace Sidebar json，断言取到 `title` 与 `items[].label`。③ 合并字典（测试站 `clear-cache` 后）：`Mrs` 太太、`Miss` 小姐、`Madam` 夫人、`Master` 少爷、`Mr` 先生、`Ms` 女士；`JAN` 为 `JAN`；`To:UOM Conversion Factor` 目标单位；`Manufacturing Setup` 生产初始化；`CN Tax` 中国财税；`Available:Raven User` 有空；`Inter Company Invoice` 公司间销售发票——全部进 `NAMED_TERMS`，`test_named_terms` 通过。④ 覆盖官方的（称呼 4 词、`JAN`）进 `OVERRIDES`，依据分别为 `DEC-039`、`DEC-041`；`JAN` 另进 `UNTRANSLATED`，写理由「条码类型代号，原样」。每个新词的候选在占用脚本里报可用，输出贴回执。四道质量守卫、覆盖清单两个差集、`test_csv_sorted` 全过。⑤ 测试站联系人表单的称呼下拉截图：先生、女士、太太、小姐、夫人、少爷、借方、教授、`Mx` 九项，其中无重名 |
| **SL-022** 演示站复核与新基准点 | R8 交出去向「演示站复核」；IT-039 余项；HT-026；R3 总纲 A14 | ① `screens.json` 在 R7 的 139 屏之外新增：「选工时单」对话框、Raven 个人资料状态下拉、BOM 与 WO 普通取消确认框各一屏（称呼下拉不进：演示站 `tabSalutation` 为 0 条，下拉是空的，只在测试站截，见 TS-035 第 8 屏）；回执附新增屏表（id／环节／状态／为何新增）。采购发票「公司间销售发票」需要内部供应商，演示站无此数据时只在测试站截图，回执写明。② 演示站逐屏核 `result.json` **每屏 `pass=true`**（英文、繁体、`title` 三类都为空）；R7 未过的 15 屏逐屏列出复跑结果。③ BOM、WO 各造一张无下游的已提交单，截普通取消框，`dialog_kind=confirm`，截后 `docstatus` 仍为 1。④ 新基准点按 A14：备份 A → 造数核屏 → 测试态备份另存 `保留-S6R9测试态/` → 恢复 A（显式时间戳）→ 期间改过 csv 或代码则 `migrate` 后另出基准点备份 → 另存 `保留-S6收尾/`（旧的 `20261012_163036` 一套移入 `保留-S6收尾/R7/`，不删）。恢复后 `Translation` 0 行、造数前缀查无记录、`check_app_order` 为真、科目 266、`find_problems()` 为 `[]` |
| **SL-023** 全量回归与回写 | R3 SL-010 ⑦ | ① `frappe_china` 全量测试通过，条数 ≥ 257＋本方案新增，通过、跳过分开报；Node 用例 ≥ 29＋本方案新增，全过。② 测试站与演示站 `translation_check.run` 均返回 `[]`。③ README「Desk 前端覆盖登记」与「独立前端覆盖」两表，本方案每处补丁各有一行（接入点逐个对上 TS-027～034）；Node 与 Python 用例文件名写在复验法列。④ 常驻文件按实况回写（写前载入常驻文件契约）：项目概况的演示站基准点与已知限制；开发守则补 A28 的命名约定（「按键取用的译名键，常量名以 `SOURCE`／`SOURCES` 结尾」）。⑤ `git status` 逐个文件对上本方案任务；六个上游 app 的 `status` 为空 |

**执行每个切片前，对照该切片验收条件检查方案覆盖性——如发现按方案写出的代码无法通过验收条件，暂停反馈，不硬写。**

## 五、任务清单

| 任务 | 对应切片 | 可并行否 |
|---|---|---|
| TS-025 取法补字面量按键一类与侧栏 json | SL-021 | 否（后续任务新增的自有键靠它认出） |
| TS-026 csv 定词 | SL-021 | 否 |
| TS-027 列表筛选按钮与首列排序提示 | SL-016 | 与 TS-029～031 同改 `desk_patches.js`，不并行 |
| TS-028 分组按钮裸串 | SL-016 | 同上 |
| TS-029 报表 DocType 名列 | SL-017 | 同上 |
| TS-030 修改记录 `null` 与上游报告草稿 | SL-018 | 同上；草稿可并行写 |
| TS-031 「选工时单」对话框标签 | SL-020 | 同上 |
| TS-032 Raven `Available` 限定改取 | SL-020 | 可与 TS-027～031 并行（只改 `independent_app_labels.js` 的 Raven 段） |
| TS-033 CRM 页 `lang`、翻页与 `Empty` | SL-019 | 与 TS-032、034 同改 `independent_app_labels.js`，串行 |
| TS-034 CRM 侧栏占位 | SL-019 | 服务端部分可并行；前端部分在 TS-033 之后 |
| TS-035 测试站实页核 | SL-016～021 | 否 |
| TS-036 演示站复核与新基准点 | SL-022 | 否 |
| TS-037 全量回归、README、常驻文件 | SL-023 | 否 |

---

## 任务 TS-025：取法补字面量按键一类与侧栏 json（对应 SL-021）

### 目标
清场与「自有源词必有译文」两处判据都认得出按键取用的键（IT-043），也认得出侧栏 json 的标题（`CN Tax`）。

### 具体改动
1. **`frappe_china/tests/test_translations.py`**：把 `_app_source_strings()` 拆成两层。
   ```python
   def _source_strings_from_text(name: str, text: str) -> set[str]:
       # name 为相对 app 根的路径（判文件类型），text 为文件内容；纯函数，不读盘、不 import frappe
       # .py：
       #   ① 现有 _()／__() 字面量调用（含 context= 的拼 "源词:context"）
       #   ② ast 解析，模块级 Assign／AnnAssign，目标名 re.search(r"SOURCES?$", name, re.I)
       #      → 值为 str 常量，或 tuple／list／set 里的 str 常量
       # .js：
       #   ① 现有 _／__ 字面量调用，正则前缀扩为 (?<![A-Za-z_.$])(?:_{1,2}|translate)\(
       #      （translateLabel( 因紧跟 Label 不匹配）
       #   ② 赋给名字以 sources／SOURCES 结尾的标识符的字面量里的字符串：
       #      取 `(?:const|let|var)\s+(\w*sources)\s*=` 之后到配对的 `;` 或语句结束之间，
       #      其中 new Set([...]) 与 [...] 内的引号字符串
       # .json（DocType／Report／custom_field 照旧）；另：doctype 为 "Workspace Sidebar"／"Desktop Icon"
       #   → title、label、items[].label
       # 返回前去掉含汉字的串（同现有末行）

   def _app_source_strings() -> set[str]:
       # 遍历同现有（跳过 tests／fixtures 规则不变，json 另收 workspace_sidebar／desktop_icon），
       # 逐文件调 _source_strings_from_text 取并集
   ```
   `Spike/P1S6R6-csv-prune.py` 用 `exec` 取同名函数的源码。拆分后脚本须把 `_source_strings_from_text` 一并取出（按名字列表取 FunctionDef），否则脚本报 `NameError`。两个函数都在**函数体内** import `ast`／`json`／`re`／`Path`（同现状），因为脚本只 exec FunctionDef，取不到模块级 import。
2. 新增用例 `test_source_strings_literal_key_forms`（SL-021 ② 的构造片段）与 `test_literal_keys_are_app_sources`：把 R8 `literal_keys.json` 的 25 键写成用例内常量（测试不读 `Spike/`），断言它们 ⊆ `_app_source_strings()`。
3. 先跑 `test_translations`：新取法会多认出侧栏 `items[].label` 等键，其中合并字典无中文的会使现有用例 `test_every_app_source_string_has_chinese` 失败——逐键处置：补 csv（先查占用），或进 `UNTRANSLATED` 写理由。处置表进回执。
4. `python -I Spike/P1S6R6-csv-prune.py --dry-run` 能跑（只看不报错，不比行数：csv 现含 R7 批量档，脚本的保留规则不认它们）。另写 `Spike/P1S6R9/own-keys.py`，断言 25 键与 `CN Tax` ∈ `keep_keys()["own"]`。

### 验证方式
SL-021 ①②；`run-tests --module frappe_china.tests.test_translations` 全过。

---

## 任务 TS-026：csv 定词（对应 SL-021）

### 目标
DEC-039～041 与 `Inter Company Invoice` 写进 csv 与守卫表。

### 具体改动
1. 先跑占用脚本（`python -I Spike/P1S6R4-occupancy.py <源词> <候选>`），逐个贴输出：太太、小姐、夫人、少爷、目标单位、生产初始化、中国财税、有空、公司间销售发票。有被占用的，暂停反馈（定词已由用户裁决，不自行换词）。
2. **`frappe_china/translations/zh.csv`** 按 A20 排序位置写入：

   | 源词 | 译文 | context | 依据 |
   |---|---|---|---|
   | `Mrs` | 太太 | — | DEC-039 |
   | `Miss` | 小姐 | — | DEC-039 |
   | `Madam` | 夫人 | — | DEC-039 |
   | `Master` | 少爷 | — | DEC-039 |
   | `JAN` | JAN | — | DEC-041 |
   | `To` | 目标单位 | `UOM Conversion Factor` | DEC-041 |
   | `Manufacturing Setup` | 生产初始化（改现有行） | — | DEC-041 |
   | `CN Tax` | 中国财税 | — | DEC-041 |
   | `Available` | 有空 | `Raven User` | DEC-040 |
   | `Inter Company Invoice` | 公司间销售发票 | — | R7 按钮抽检定稿（附表第 106 行） |

3. **`tests/test_named_terms.py`** `NAMED_TERMS` 加上表全部键（含 `Mr` 先生、`Ms` 女士，标注「保留官方」）。
4. **`tests/translation_overrides.py`**：称呼 4 词与 `JAN` 各加一条 `Override(官方, ours, 依据)`，官方值从测试站合并字典取（不手抄）。
5. **`tests/translation_whitelist.py`** `UNTRANSLATED` 加 `"JAN": "条码类型代号，原样"`（基线脚本把「译文等于源词」计为缺口，`gaps()` 第 125 行）。
6. 测试站 `clear-cache`，跑 `test_translations`、`test_named_terms`、`test_translation_quality`、`translation_check.run`。

### 验证方式
SL-021 ③④。称呼下拉截图（⑤）放在 TS-035 一并截。

---

## 任务 TS-027：列表筛选按钮与首列排序提示（对应 SL-016）

### 目标
修 IT-033 的 4 屏。

### 具体改动
**`frappe_china/public/js/desk_patches.js`** 加两段（A23 形态）：
```javascript
// 1) FilterGroup.update_filter_button —— frappe/public/js/frappe/ui/filters/filter_list.js:130-145
//    原方法委托后：if zh && this.filter_button?.attr
//       n = this.filters.length
//       this.filter_button.attr("title", __(n > 1 ? "{0} Filters Applied" : "{0} Filter Applied", [n]))
//    （上游 n>1 才加 s，0 与 1 都走单数；本补丁沿用同一分支）
// 2) ListView.get_header_html —— frappe/public/js/frappe/list/list_view.js:752-814
//    html = 原方法(...)；if !zh || !html || !this.columns?.[0]?.df → return html
//    df = this.columns[0].df
//    wrong = `title="${__("Click to sort by {0}", [df.label])}"`
//    right = `title="${__("Click to sort by {0}", [__(df.label, null, df.parent || this.doctype)])}"`
//    return wrong === right ? html : html.replace(wrong, right)   // 只替换第一处；找不到即原样
```
csv 加 `{0} Filter Applied`、`{0} Filters Applied` 两行，都译「已应用 {0} 个筛选条件」（两键在补丁里以 `__("…")` 字面量出现，TS-025 的取法会认出）。新建 **`frappe_china/tests/test_desk_patches.cjs`**，沿用 `test_desk_titles.cjs` 的 vm 写法，桩出 `frappe.ui.FilterGroup`、`frappe.views.ListView`，覆盖 SL-016 ①②④。现有四个 `.cjs` 的桩上下文没有这些类，补丁必须用可选链守卫，现有用例不改也应全过。

### 验证方式
SL-016 ①②④；`node --test frappe_china/tests/*.cjs`。

---

## 任务 TS-028：分组按钮裸串（对应 SL-016）

### 目标
修 IT-038。

### 具体改动
1. **先验 HT-027**：grep `erpnext/erpnext`、`hrms/hrms` 的 `.js`，找出 `add_custom_button(` 首参为字面量字符串（不是 `__(`）且有第三参（分组）的全部调用；对每个 label，再 grep 是否有以同一英文字面量调用 `change_custom_button_type`／`remove_custom_button` 并带分组的。结果表进回执。
2. **`desk_patches.js`** 包 `frappe.ui.Page.prototype.add_inner_button(label, action, group, type, align_right)`（`frappe/public/js/frappe/ui/page.js:622-662`）：
   ```javascript
   // if zh && group && typeof label === "string" → label = __(label)
   // 然后以 (label, action, group, type, align_right) 委托原方法、返回原返回值
   // HT-027 有冲突时：条件再加 RAW_GROUP_LABELS.has(label)
   ```
   `form.add_custom_button` 以原 label 记 `custom_buttons[label]`（`form.js:1540-1548`），不受影响。
3. Node 用例：带分组的英文 label 被翻译、`data-label` 跟随；中文 label 不变；不带分组不变；英文会话不变。

### 验证方式
SL-016 ③④。

---

## 任务 TS-029：报表 DocType 名列（对应 SL-017）

### 目标
修 IT-034 的 3 屏（总账、库存台账、开账跳转）。

### 具体改动
**`desk_patches.js`** 包 `frappe.views.QueryReport.prototype.prepare_columns(columns)`（`frappe/public/js/frappe/views/reports/query_report.js:1379-1452`）：
```javascript
const REPORT_DOCTYPE_COLUMNS = {
  "General Ledger": ["voucher_type", "against_voucher_type", "party_type"],
  "Stock Ledger": ["voucher_type"],
};
// result = 原方法(columns)
// if !zh → return result
// fields = REPORT_DOCTYPE_COLUMNS[this.report_name]; if !fields → return result
// for col of result where fields.includes(col.fieldname):
//    const format = col.format
//    col.format = (value, row, column, data, filter) =>
//        format(typeof value === "string" && value ? __(value) : value, row, column, data, filter)
// return result
```
只改传给 formatter 的显示值，`data` 对象不动，故 `Dynamic Link` 的 `voucher_no` 仍按 `data.voucher_type` 建路由。`against_voucher_type`、`party_type` 两列 E 未点名，但同样装的是 DocType 名、也在同一张报表上，一并纳入（理由写进 README 登记行）。已知代价：datatable 列内筛选按原始值匹配，用户输中文搜不到——回执写明，不处理。

### 验证方式
SL-017 ①～④（Node 用例桩 `QueryReport.prototype.prepare_columns` 返回带 `format` 的列）。

---

## 任务 TS-030：修改记录 `null` 与上游报告草稿（对应 SL-018）

### 目标
修 IT-035 的 4 屏（工单、工序卡、完工入库、销售订单状态菜单的修改记录）。

### 具体改动
1. **`desk_patches.js`**：
   ```javascript
   // const fix_timeline_nulls = (root) => {
   //   if (!isZh()) return;
   //   root.querySelectorAll?.(".new-timeline .timeline-content b").forEach((b) => {
   //     if (b.textContent === "null" || b.textContent === "undefined") b.textContent = __("(Empty)");
   //   });
   // };
   // 幂等标记 document.__frappe_china_timeline_nulls；
   // MutationObserver(document.body, {subtree: true, childList: true}) → fix_timeline_nulls(document)
   ```
   与现有 datatable title 的 Observer 分开建，各自一个标记。csv 加 `(Empty)` → 「（空）」。
2. **`Spike/P1S6R9/upstream-it035.md`**：上游缺陷报告草稿（英文，SL-018 ④ 所列内容），附 frappe 锁定 commit `c1f1e8ec3708750d7254f7f99d869ffb9886f19f`。**不外发**。
3. Node 用例：SL-018 ①～③。

### 验证方式
SL-018 ①～④。

---

## 任务 TS-031：「选工时单」对话框标签（对应 SL-020）

### 目标
修 IT-041（`From` 显示「发件人」）。

### 具体改动
**`desk_patches.js`** 包 `frappe.ui.Dialog.prototype.make`（`frappe/public/js/frappe/ui/dialog.js:33`；构造函数先 `$.extend(this, opts)` 再调 `make()`，故此时 `this.title`、`this.fields` 已就位）：
```javascript
const DIALOG_FIELD_LABELS = {
  "Fetch Timesheet": {from_time: "From Date", to_time: "To Date"},  // erpnext sales_invoice.js:305-337
};
// make 前：if zh：
//   for [title, labels] of entries(DIALOG_FIELD_LABELS):
//     if this.title === __(title):
//       for f of this.fields || []: if labels[f.fieldname] && f.fieldtype === "Date" → f.label = __(labels[f.fieldname])
// 然后委托原 make
```
不替换 `frappe.ui.Dialog` 类本身（会破坏 `instanceof` 与已定义的子类）。Node 用例：命中的对话框改标签；标题不同、字段名不同或字段类型不是 Date 的都不变；英文会话不变。

### 验证方式
SL-020 ①。

---

## 任务 TS-032：Raven `Available` 限定改取（对应 SL-020）

### 目标
修 IT-048 的 Raven 一处（DEC-040）。

### 具体改动
1. **`frappe_china/public/js/independent_app_labels.js`**：
   ```javascript
   const RAVEN_CONTEXT_KEYS = {"Available": "Raven User"};
   function applyContextKeys(frappe, table, warn = () => {}) {
     // 对 table 每个 [key, context]：v = frappe._messages[`${key}:${context}`]
     //   v 存在 → frappe._messages[key] = v；不存在 → warn(key) 且不改
     // 返回改了几条
   }
   // Raven 分支：bridgeMessages 成功后调 applyContextKeys(root.frappe, RAVEN_CONTEXT_KEYS, missing)
   // module.exports 加 applyContextKeys、RAVEN_CONTEXT_KEYS
   ```
   放在 `bridgeMessages` 之后，因为 `bridgeMessages` 保留已有运行时词条，而这里要覆盖的是 boot 字典带进来的无 context 值。
2. 先验 HT-024：测试站取 Raven 页 boot 的 `__messages["Available:Raven User"]`。
3. Node 用例（`test_independent_app_labels.cjs`）：映射生效、context 行缺失时告警且不改、重复调用结果相同。

### 验证方式
SL-020 ②③。

---

## 任务 TS-033：CRM 页 `lang`、翻页与 `Empty`（对应 SL-019）

### 目标
修 IT-036 的 3 屏（线索列表、商机列表、看板）。

### 具体改动
1. **`frappe_china/templates/independent_apps/crm.html`**：在现有 `replace('</body>', …)` 上再链一个 `replace('<html class="h-full" lang="en">', '<html class="h-full" lang="zh">')`。
2. **`frappe_china/website_translation.py`** `SOURCES` 加 `of`、`Load More`、`Empty`。
3. **`independent_app_labels.js`**：
   - `sources.chart` 加 `Empty`；`category` 正则的分组扩为 `(stage|source|Empty)`；
   - 新增翻页处理（只在 CRM）：
     ```javascript
     // function processListFooter(element):
     //   找 element 内（含自身）textContent.trim() === "of" 的 div，
     //   且 previousElementSibling、nextElementSibling 的 textContent.trim() 都匹配 /^[\d,]+$/
     //   → 该 div 文本 = messages["of"]（缺词即 missing 并跳过）
     //   → container = 该 div 的 parentElement.parentElement；
     //     container 内文字恰为 "Load More" 的 button 的文本节点 → messages["Load More"]
     // 在 processElement 里对 CRM 调用
     ```
   - 导出 `processListFooter` 的纯判定部分（如 `isPagerOf(prevText, text, nextText)`）供 Node 测。
4. Python 用例（`test_website_translation.py`）：渲染后恰一处 `lang="zh"`、无 `lang="en"`；上游模板缺该标签时失败，消息写明（用 `assertIn` 在渲染前对原模板文本断言）。
5. Node 用例：SL-019 ②③。

### 验证方式
SL-019 ①～③；HT-022 在 TS-035 截图验。

---

## 任务 TS-034：CRM 侧栏占位（对应 SL-019）

### 目标
修 IT-037 的 2 屏（线索、商机详情侧栏）。

### 具体改动
1. 新文件 **`frappe_china/crm_sidepanel.py`**：
   ```python
   ORIGINAL = "crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_sidepanel_sections"

   @frappe.whitelist()
   def get_sidepanel_sections(doctype: str) -> list:
       # sections = frappe.get_attr(ORIGINAL)(doctype)（原方法自带权限与存在性判断，照原样委托）
       # if frappe.local.lang != "zh": return sections
       # 逐 section → columns → fields（field 为 dict，原方法已转成 get_field_obj 的结果）：
       #   label = field.get("label") or ""
       #   if field.get("placeholder") == f"Add {label}...":    → _("Add {0}...").format(_(label))
       #   elif field.get("placeholder") == f"Select {label}...": → _("Select {0}...").format(_(label))
       #   if field.get("tooltip") == "This field is read only and cannot be edited." → _(该串)
       # return sections
   ```
   label 用无 context 的 `_(label)`，与 CRM 前端 `__(field.label)` 取同一个词。
2. **`hooks.py`** `override_whitelisted_methods` 加 `ORIGINAL → "frappe_china.crm_sidepanel.get_sidepanel_sections"`。
3. csv 加 `Add {0}...` → 「添加{0}……」、`Select {0}...` → 「选择{0}……」（与现有 `Add Organization...,添加组织……` 同形）；只读提示若合并字典无中文，补一行。
4. **`independent_app_labels.js`**（CRM，TS-033 之后）：侧栏区（`.sections.flex.flex-col.overflow-y-auto`）内，`placeholder` 属性或文本恰为 `${messages["Select"]} (.+)\.\.\.` 的，改为 `format(messages["Select {0}..."], [root.__ ? root.__(label) : label])`；`website_translation.SOURCES` 加 `Select`、`Select {0}...`。
5. 新文件 **`frappe_china/tests/test_crm_sidepanel.py`**：HT-023 断言；对 `CRM Lead` 的中文与英文会话各取一次，SL-019 ④ 逐项断言；构造一个带自定义 placeholder 的字段（patch 原方法返回值），断言原样保留；无布局的 DocType 返回 `[]`。
6. Node 用例：侧栏内 User 型占位改写、侧栏外同形文本不变。

### 验证方式
SL-019 ④⑤。

---

## 任务 TS-035：测试站实页核（对应 SL-016～021）

### 目标
在浏览器里看到 TS-026～034 的效果，验 HT-021、022、025。

### 具体改动
1. 测试站 `bench build --app frappe_china`、`clear-cache`；容器内另起 `--site test.localhost serve --port 6787`（R3 总纲 §九第 4 条），用完停掉。
2. 写 `Spike/P1S6R9/test-site-check.cjs`（基于 `Spike/P1S6R6-screen-check.js` 的登录与截图），逐项截图存 `Spike/P1S6R9/test-site/`，每张配一行读数（选择器取到的文字或属性）：

   | # | 屏 | 看什么 |
   |---|---|---|
   | 1 | 工单列表（加 1 个筛选） | 筛选按钮 title、首列表头 title |
   | 2 | 采购发票（内部供应商，已提交） | 「创建」下拉项（测试站临时建内部供应商与单据，用后删） |
   | 3 | 总账、库存台账 | 凭证类型列 |
   | 4 | 任一有字段从空改为有值的修改记录 | 「（空）」 |
   | 5 | 销售发票「获取物料 → 工时单」 | 两个日期标签 |
   | 6 | Raven 设置 → 个人资料 | 状态下拉；Desk `Raven User` 表单同一字段 |
   | 7 | CRM 看板、线索列表、线索详情 | 月份、`Empty`、翻页、侧栏占位 |
   | 8 | 联系人表单 | 称呼下拉（SL-021 ⑤） |
   | 9 | 工作站表单 | 状态 `Available` 仍为「工位可用」 |

3. 控制台日志里无 `[frappe_china]` 告警（HT-021）；CRM 版式与改前截图对比（HT-022，改前图用 R7 `Spike/P1S6R6-screens/` 里同屏）。
4. **撤钩反证**：临时把 `hooks.py` 的 `app_include_js` 去掉 `desk_patches.js`，`build`、`clear-cache` 后重截第 1、3、5 屏，应回到英文或「发件人」；随即恢复，核 `git -C frappe-bench/apps/frappe_china status --short` 与反证前一致。
5. 测试站造的数据用后删除，回执列出删了什么。
6. 称呼下拉里的 `Mx` 官方原样、本方案不改（无通行中译），截图里出现属预期，回执写明。

### 验证方式
SL-016～021 中写「截图」的各条；HT-021、022、025 的验证。

---

## 任务 TS-036：演示站复核与新基准点（对应 SL-022）

### 具体改动
1. **核旧基准点**：`docker/backups/` 根目录与 `保留-S6收尾/` 下 `20261012_163036` 的 4 个文件都在。
2. **上线**：演示站 `migrate`、`bench build --app frappe_china`、`clear-cache`，重启 `bench start` 进程；跑 `translation_check.run` 与 `check_app_order`。
3. **备份 A**：`docker/backup.sh`，记时间戳 `{A}`。
4. **造数**：沿用 `Spike/P1S6R6-closed-loop.py`，前缀改 `_S6R9`。另造 BOM、WO 各一张无下游的已提交单（WO 选无工序的 BOM，提交时不生成工序卡）。
5. **屏清单**：`Spike/P1S6R6-screens.json` 另存为 `Spike/P1S6R9-screens.json`，按 SL-022 ① 新增屏（BOM、WO 普通取消框是新增的两屏，原来截到 `_cancel_all` 的两屏保留，标 `kind_expected: "cancel_all"`）。
6. **逐屏核**：`node Spike/P1S6R6-screen-check.js http://localhost:8000 Spike/P1S6R9-screens.json Spike/P1S6R9-screens/`。有不过的屏：属 csv 能修的，补 csv（先在测试站验，再同步到演示站并 `clear-cache`）后复跑该屏；属本方案补丁没覆盖到的，**暂停反馈**，不在本步加新补丁。
7. **测试态备份**：`docker/backup.sh`，4 个文件另存 `docker/backups/保留-S6R9测试态/`。
8. **恢复 A**：`docker/restore.sh {A}`（显式写时间戳；停服务与恢复分两条命令），然后 `migrate`、`clear-cache`；查 `Translation` 0 行、`_S6R9` 前缀记录 0、`tabCash Flow Worksheet` 0 行、科目 266、`find_problems()` 为 `[]`。
9. **新基准点**：第 6 步改过 csv 或代码的，A 已过时，`migrate`、`clear-cache` 后另出备份 C；4 个文件另存 `保留-S6收尾/`，原 `20261012_163036` 一套移入 `保留-S6收尾/R7/`。回执写明最终基准点时间戳，并确认根目录最新一套就是它。

### 验证方式
SL-022 ①～④。截图与 `result.json` 放 `Spike/P1S6R9-screens/`。

---

## 任务 TS-037：全量回归、README、常驻文件（对应 SL-023）

### 具体改动
1. 测试站全量 `run-tests --app frappe_china`，报收集、通过、跳过的条数；宿主 `node --test frappe_china/tests/*.cjs`。
2. **README**：「Desk 前端覆盖登记」表加 TS-027～031 的 5 行；「独立前端覆盖」表的 CRM、Raven 两行补本方案的改动（`lang`、翻页、`Empty`、侧栏、`RAVEN_CONTEXT_KEYS`）；`override_whitelisted_methods` 的 CRM 侧栏覆盖加一行（上游 `crm_fields_layout.py:113-146,179-191`，锁定 commit 取 `docker/apps.json`）。
3. 常驻文件——**先载入 `docs/流程体系/常驻文件契约.md`**：
   - `docs/项目概况.md`：演示站备份基准点（新基准点、`保留-S6R9测试态/`）；「已知限制」里译名一条按本轮结果改写（不宣称 Stage 完成）；
   - `docs/开发守则.md`：A28 的命名约定。
4. `git status --short`（主仓库与 `frappe_china`）逐个文件对上本方案任务；六个上游 app 目录的 `status` 为空。

### 验证方式
SL-023 ①～⑤。

## 六、E 报告各项的落点

| E 项 | 本方案 |
|---|---|
| IT-033（4 屏） | SL-016 ①②、TS-027 |
| IT-034（3 屏） | SL-017、TS-029 |
| IT-035（4 屏） | SL-018、TS-030 |
| IT-036（3 屏） | SL-019 ①～③、TS-033 |
| IT-037（2 屏） | SL-019 ④⑤、TS-034 |
| IT-038 | SL-016 ③、TS-028；csv 行在 TS-026 |
| IT-041 | SL-020 ①、TS-031 |
| IT-043 | SL-021 ①②、TS-025 |
| IT-048（Raven 一处） | SL-020 ②③、TS-032；csv 行在 TS-026 |
| 清单外：`JAN`、`To` 单位、`Manufacturing Setup`、`CN Tax` | SL-021 ③④、TS-026（`CN Tax` 的取法在 TS-025） |
| 清单外：称呼词 | DEC-039；SL-021 ③～⑤、TS-026 |
| 演示站复核、BOM／WO 普通取消框 | SL-022、TS-036 |

## 七、并行开发说明

| 可并行组 | 任务 | 各自写入范围 |
|---|---|---|
| ① | TS-030 第 2 步（上游报告草稿） | 只写 `Spike/P1S6R9/upstream-it035.md` |
| ② | TS-034 第 1、2、5 步（服务端覆盖与 Python 用例） | `crm_sidepanel.py`、`hooks.py`、`tests/test_crm_sidepanel.py`；与 `desk_patches.js` 系列互不相交 |
| ③ | TS-032 与 TS-027～031 | TS-032 只改 `independent_app_labels.js` 的 Raven 段与其 Node 用例；TS-027～031 只改 `desk_patches.js` 与 `test_desk_patches.cjs` |

**csv（`zh.csv`）、`test_named_terms.py`、`translation_overrides.py` 只由主 Session 串行写。**

**SB（附属 R5）余项不得与本方案 D 并行**：IT-026 改 `desk_patches.js` 的 datatable 段，与 TS-027～031 写同一文件。SB 排在本方案 D 之前或 E（R11）之后，由用户定。

## 八、执行顺序与回执

```
TS-025 取法 ─→ TS-026 csv 定词 ─→ TS-027 筛选／排序 ─→ TS-028 分组按钮 ─→ TS-029 报表列 ─→ TS-030 时间线 null ─→ TS-031 对话框
                                   │                                                               (草稿并行)
                                   ├─→ TS-032 Raven ─→ TS-033 CRM lang／翻页 ─→ TS-034 CRM 侧栏（服务端可并行）
                                   └──────────────────────────────────────────────────────────────┐
                                                                                                  └─→ TS-035 测试站实页 ─→ TS-036 演示站 ─→ TS-037 收尾
```

D 步为 **R10**，回执为 `R10-代码/P1-S6-R10-D回执.md`（不拆 Part），开工即建，预填 TS-025～037，每个任务做完当场回写（`bricks/receipt.md`）。D 完成后回 E 复核（R11）。E 的复核范围为本方案全部切片，加 SB 余项（若 SB 已在 R10 之前做完）。
