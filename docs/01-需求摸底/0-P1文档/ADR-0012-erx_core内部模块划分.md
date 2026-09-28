# ADR-0012: 自有 app 内部模块最少——`frappe_china` 的 `modules.txt` 现只列 1 个

- 状态：accepted（**2026-09-28 修订**，随 [ADR-0013](ADR-0013-自有app按域分为frappe_china与frappe_debug.md)：6 个单位改分到两个 app；代码组织改采官方 app 的普通包分层；「模块数是界面成本」的判据补三条限定与一条前提；拆分信号更正。**「模块最少」这个结论不变。** 原标题「`erx_core` 内部模块最少」，文件名保留原样以免断链。见文末「修订记录」）
- 日期：2026-09-25 / 决策者：用户裁决（C 步第 15 步①），Claude 提选项；2026-09-28 修订出自 P1-S4-R1 A 步第 5–8 步（用户于第 6 步确认组织取向、第 8 步裁决 app 划分）
- 对应决策：DEC-063；修订对应 DEC-108／DEC-109／DEC-112

## 上下文

Frappe 的「模块」（`modules.txt` + `Module Def`）不只是代码组织单位。C 步查出一条机制（发现十五）：

`get_module_list` → `add_module_defs` → `auto_generate_sidebar_from_module()`，**每个 `Module Def` 自动生成一个 hammer 侧栏进 boot**（`__init__.py:899`、`installer.py:749-755`、`workspace_sidebar.py:239-252`）。

⇒ **模块划分是界面决策，不只是代码决策。** 而 CR-010 的方向正是「折叠无关入口」。

**2026-09-28 补：该判据须带三条限定与一条前提**（P1-S4-R1 G2 调查，A 步核实），每条都削弱「界面成本」的量级：

1. **官方的规避办法是发同名 fixture，而不是不声明模块**：`workspace_sidebar.py:243` 的守卫是 `frappe.db.exists("Workspace Sidebar", {"name": module, "for_user": None})`，站上已有与模块同名的侧栏即不自动生成。
2. **没有可见条目的侧栏被整条丢弃**：`boot.py:500-504` 对每条侧栏判「是否至少有一个非 Section Break 的条目」，没有则 `continue`。故纯代码模块（无 DocType／Report／Workspace／Dashboard／Page）本就不产侧栏。
3. **`hammer` 是死值**：`workspace_sidebar.py:250` 写入 `header_icon = "hammer"`，但前端不认它（G2：`sidebar_header.js:310-311` 下一行即覆盖为首字母字母块）。
4. **前提：「`modules.txt` 可随时追加」只在一定条件下成立**。`add_module_defs` 的唯一调用点是 `installer.py:345`（在 `install_app` 内），`migrate.py` 不调它 ⇒ 往已装的 app 追加 `modules.txt` 项，`bench migrate` **不经这条路**建 `Module Def`。**但另有一条补建路**（B 步读码补查，**未实测**）：DocType 同步时 `DocType.on_update` 调 `make_module_and_roles`（`core/doctype/doctype/doctype.py:543`、`:1975-1985`），模块缺 `Module Def` 即补建 ⇒ **新模块含 DocType 时 migrate 很可能能补上；只含 Report 的新模块补不上**。

**正确表述**：每多一个模块，**且它至少有一个 DocType／Report／Workspace／Dashboard／Page、且站上无同名 `Workspace Sidebar`**，才多一条侧栏。

## 决策

**现行（2026-09-28 修订）**

**一、模块**：`frappe_china` 的 `modules.txt` 只列 **1 个**模块：**`cn_tax`**（中国财税，承载本 Stage 的 DocType 与 Report）。`frappe_debug` 是否需要模块，按同一判据由 S7 的开发方案定（它若只有代码与数据文件，则不需要）。

**二、`cn_tax` 自动侧栏的压制**：`cn_tax` 有 DocType 与 Report，过得了上文限定 2 ⇒ 不处理会实打实多出一条侧栏。**须发一份与该模块同名的 `Workspace Sidebar` fixture**（名字与 `modules.txt` 那一行逐字相同）压住它。架构文档 §3.5 那份自有 title 的业务流侧栏**名字不同，压不住**。

**三、代码组织：采官方 app 的普通包分层**（DEC-108）。覆盖实现、whitelisted 接口、工具函数放**普通 python 包**，不采原决策「中国财税的逻辑全在模块内」。判据（G2 查实）：6 个官方 app 全部有普通包层且命名收敛（`api/`／`utils/`／`overrides/`）；hrms／crm／helpdesk 三家都把覆盖实现放普通包；`modules.txt` 与目录可完全解耦（hrms 声明 10 个模块、只 2 个装 DocType）。**保留原决策的一半**：`hooks.py` 与安装入口只做接线、不写业务逻辑。

**四、单位的归属**

| 单位 | 归属 | 性质 | 备注 |
|---|---|---|---|
| `cn_tax/` | `frappe_china` | 模块（`modules.txt` 1 项） | DocType、Report、科目表 JSON |
| 中国财税的覆盖实现、接口、工具 | `frappe_china` | 普通包 | 包名留 S4 的 C 步 |
| `i18n/` | `frappe_china` | 普通包 | 译名 csv 与自检（S6） |
| `patches_mfg/` | `frappe_china` | 普通包 | 生产模块修正（DEC-111，S7） |
| 推送助手 | `frappe_china` | 普通包 | 事件协议推送侧（ADR-0008，DEC-110） |
| `workspace_sidebar/`、`desktop_icon/` | `frappe_china` | app 级 json 目录（`sync.py:120`） | 含上条「二」的同名侧栏 fixture |
| `data/`、`nodes/`、`drivers/{desk,spa}` | `frappe_debug` | 普通包 | 造数据与建单辅助／23 节点定义／Cypress 与 Playwright 驱动（DEC-112，S7） |

**判据须写进各 app 的 README**：需要 `Module Def` 的只有 DocType／Report／Page／Workspace（及 Dashboard），纯代码放普通包；**并写明上条「二」同名 fixture 的用途**，否则下一个人会把它当成多余文件删掉。

**原决策（2026-09-25，已由上文取代，保留备查）**：`modules.txt` 现在只列 1 个模块：`cn_tax`（中国财税，承载 8 个 DocType + 3 个 Report）。其余代码放普通 python 包，不进 `modules.txt`：

| 目录 | 内容 | 是否模块 |
|---|---|---|
| `cn_tax/` | 8 DocType + 3 Report + 科目表 JSON | ✅ `modules.txt` 列 1 项 |
| `i18n/` | 译名 csv + 自检 | 普通包 |
| `patches_mfg/` | 服务端修正的 `doc_events` handler | 普通包 |
| `demo/` | 演示操控 whitelisted 方法 + 节点 js + 数据生成器 + 数据集 json | 普通包 |
| `workspace_sidebar/` | 自有侧栏 json | app 级 json 目录（`sync.py:120`） |
| `desktop_icon/` | 入口图标 json | app 级 json 目录 |

## 后果

**正面**
- 只多出 1 个 hammer 侧栏，而非 6 个。与 CR-010 的方向一致。**（2026-09-28 补）**：发了同名 fixture 后，`cn_tax` 自动生成的那一条也不会出现。
- `modules.txt` 可随时追加，现在预留无收益。**（2026-09-28 补）**：追加有前提，见「上下文」第 4 条。

**负面**
- 「中国财税」这件事的代码分散于三处：模块 `cn_tax/`、`hooks.py`（覆盖位与 `doc_events`）、`after_install`（配置数据）。**C 步复核建议把这条界线点名为模块边界最模糊处**，并给出收拢办法（让 `after_install` 只调用 `cn_tax` 模块内的一个入口函数）。**本步裁定采纳该收拢办法**：`after_install` 不写业务逻辑，只按序调用 `cn_tax` 内的入口函数。这样「中国财税」的逻辑全在模块内，`hooks.py` 与 `after_install` 只剩接线。**（2026-09-28 修订）**：「逻辑全在模块内」已由「决策·三」取代——逻辑可以在普通包里；仍成立的是「`hooks.py` 与 `after_install` 只剩接线」。
- **⚠ `cn_tax` 的对外接口 16 项，命中 C 步分解检查的拆分信号「公开接口超过 10 个」。** 如实登记：若将来报表继续增加，应把「报表」独立成第二个模块。**（2026-09-28 更正）**：① 接口数随 S4 需求文档变化——whitelisted 覆盖 4 条减为 3 条（`get_all_nodes` 纯冗余，`frappe/desk/treeview.py:17` 已自行调用覆盖派发）、资产负债表与利润表的两对 Settings DocType 不带入，另增月末结转、导入前置处理、建账结果自检；确切数目待 S4 的 C 步。② **「报表增加就独立成模块」是反向参照**：erpnext 的 `Accounts` 一个模块装 92 个非子表 DocType 与 52 个 Report，没为报表另立模块，而是挂 8 份侧栏 fixture（`module` 全是 `Accounts`）⇒ 官方把「报表要不要单独露出」当侧栏问题而非模块问题。原理由只对一半：`Report.module` 确是**报表列表**的分组依据，但它不是**侧栏**的分组依据——原文把两个目标混在一起。

**中性**
- 普通包与模块的区别对读代码的人不直观（目录长得一样），故判据必须写进 README，否则下一个人会把普通包当模块加进 `modules.txt`。

## 备选方案

**按域分 6 个模块** —— 代码组织最清楚，每域一个模块。**没选**：**发现十五**——`modules.txt` 每多一项，`auto_generate_sidebar_from_module()` 就自动生成一个 hammer 侧栏进 boot ⇒ 6 个模块＝自己又造 6 个噪音入口，**与 CR-010「折叠四个第三方 App 的无关入口」直接相悖**。见 NV-048。**（2026-09-28 注）**：按「上下文」的三条限定，其中纯代码的几个模块本就不产侧栏，此否决理由的量级偏大；但结论不变——多声明模块没有收益。

**只 1 个模块装全部**（含将来的生产增强报表）—— 界面成本最低。**没选**：中国财税的 8 个 DocType 与将来的生产增强报表混在一个模块下，**Report 的模块归属会体现在报表列表分组里**，客户看到财税报表与产能报表同组。见 NV-049。故取「现在 1 个、演示后追加第 2 个」而非「永远 1 个」。**（2026-09-28 注）**：此理由针对的是报表列表分组，成立；侧栏分组另靠 fixture（见「后果·负面」更正 ②）。

**「逻辑全在模块内」**（原决策的组织取向）—— 模块边界与代码位置一致。**2026-09-28 被取代**：官方 app 一致采普通包分层，见「决策·三」与 P1-S4 需求文档 §3.2 DEC-108。

## 关联

- 依赖：~~ADR-0001（单 app 内才有「内部怎么分模块」这个问题）~~ → **ADR-0013**（两个 app 各自内部怎么分）、ADR-0007（`cn_tax` 的 DocType 与覆盖位来自该决策）
- 被依赖：前瞻性设计 P-3（`modules.txt` 留出第二个模块位置 → IM-010／IM-011）
- 取代：无

## 失效条件

演示后做需求图谱 §3.2 那批时追加第 2 个模块（生产增强）；~~若报表继续增加应把「报表」独立成第三个~~（**2026-09-28 删**：反向参照，见「后果·负面」更正 ②；报表要单独露出时发侧栏 fixture）。**另**：官方 app 的组织惯例变化时，重判「决策·三」。

## 修订记录

| 日期 | 改了什么 | 来源 |
|---|---|---|
| 2026-09-28 | 标题去掉 `erx_core`；「上下文」补判据的三条限定与一条前提（第 4 条的补建路为 B 步读码补查、未实测）；「决策」改为现行四点（1 个模块／同名侧栏 fixture／普通包分层／单位归属表），原决策保留；「后果」「备选方案」就地加注、更正拆分信号；「关联」「失效条件」随改 | P1-S4-R1 A 步第 5 步 ⑤、第 6 步、第 8 步（缺口清单 #14／#15／#16／#26）；P1-S4-R6 B 步落成 |
