# P1-S6-R7 D 步讨论记录（执行中冒出的判断）

**主题**：执行 R6 开发方案时冒出、方案未写明的判断（`play-build` 纪律 3）｜**日期**：2026-10-11
**参与者**：Claude（Opus 5.5，D 步执行者）；用户未在环（本记录各判断待 E 步复核或用户追认）
**承接说明**：新文件。决策号接 R6 C 讨论记录续编，用 `DJ-` 前缀（D 步执行判断）与用户裁决的 `DEC-` 区分

#### 第 1 步：S3 改词落 csv 时用无 context 行还是 context 行

**① S3 改词的落法**
**提出者：** Claude（⚠ 执行中发现）
**背景：** TS-019 第 4、5 步要把 S3 术语标准的收付款方向全表与改词组落 csv。S3 写的都是无 context 的源词→新词，但 S3 当时只看了演示线 DocType 字段（§2.1），没看侧栏、首页、四个 App 与服务端 `_()` 造的数据名。按 S3 原样写无 context 行，新词会连带改掉它没分析过的渲染点。实测（`Spike/P1S6R7/s3_spread.py`、`s3_place.py`）：`Selling`／`Buying` 的演示面出处有 `selling.json`／`buying.json`／`business_flow.json` 侧栏（指模块），S3 的「用于销售／用于采购」是 `Item Price`／`Price List` 的勾选框；`Contact` 在 `crm.json`／`selling.json` 侧栏与 CRM 转商机框里指联系人 DocType 本身，S3 的「联系人详情」是八张单据的 `contact_display`；`Production`（→ 运行中）同时是部门名 `_("Production")`（`company.py:479`）；`Stores`（→ 库房）是建公司时 `_("Stores")` 生成并按名查回的仓库名（`company.py:387`、`defaults_setup.py:33`），演示面无出处。
**选项：**

| 选项 | 描述 | 优点 | 缺点 |
|---|---|---|---|
| A 全写无 context 行 | 照 S3 原样 | 与 S3 字面一致；基线撞名计数直接清掉 | 侧栏模块名、联系人 DocType 名、部门名等被改错，其中侧栏是 S6 本身的交付物 |
| B 按渲染点落（采用） | 演示面上有不能带 context 的渲染点（JS 字面量、侧栏、首页图标、需求 §4.2.4 点名）→ 无 context 行；演示面渲染点全是 DocType 字段／选项 → 每个 DocType 一行 context 行，无 context 保留官方；S3 §1.1／§1.3 收付款方向照方案「全表落」写无 context 行（带 context 的照写三列） | S3 新词原样保留（需求 §4.2.2 规则 2），只落到 S3 分析过的渲染点；字段 label、Select 选项、分节、页签、列表列头都带 `df.parent` 取 context（`base_input.js:200`、`select.js:175`、`section.js:66`、`tab.js:38`、`grid_row.js:593`、`list_view.js:2120`） | 基线 `demo_collisions` 只按无 context 键算，context 行解掉的组仍会被计入，须另出一张按渲染点算的核对表；服务端打印等不带 context 的点仍显示官方 |

**例外（按 B 判为无 context，但改按 context 行写）：** `Selling`、`Buying`、`Contact`、`Taxes`——无 context 渲染点是侧栏里的模块／DocType 名，与 S3 新词所指不是一个东西；这四个只写 S3 分析过的那几张 DocType 的 context 行，侧栏保留官方。
**不写：** `Stores`、`Accountant`（服务端 `_()` 生成的记录名或 fixture 数据，DEC-033「默认数据不改 csv」同判据）；以及演示面无任何出处的 §2.3 改词（`Accounts User`、`Batch Quantity`、`Expires On`、`In Qty`、`In Stock`、`Receivable Account`、`Requesting Site`、`Serial and Batch`）——方案 TS-019 的范围是演示面，这些在当前基线里不在演示面上，按 DEC-002「演示线外撞名不处理」不落；在回执列出。
**已知代价（照 B 写无 context 行的）：** `Available`→工位可用 波及 Raven 个人状态「可用」（`Profile.tsx`，不在演示面）；`Operations`→工序清单 波及新建公司的部门名；`Finish`→完工 波及 CRM 问卷按钮。均在回执「复核建议」列出。
**用户回答：** 待用户回答（E 步复核）
**结论：** **DJ-001**：按 B 落（落地后实跑：基线演示撞名 200 组中，42 组已由 context 行解开，见第 2 步）。占用重查 7 处命中全部判同义或随本轮改词消解（见回执附表），不改 S3 新词。另出 `Spike/P1S6R7/collision_effective.py`，按渲染点（字段带 context）重算演示撞名，作 SL-013 ② 的补充证据。

#### 第 2 步：演示撞名 200 组的判定

**提出者：** Claude（TS-019 第 3 步执行）
**背景：** TS-019 第 3 步要求演示撞名逐组判同义或异义（S3 DEC-075），异义的给唯一用词、候选先查占用。基线 `demo_collisions` 只按无 context 键归并，DJ-001 写的 context 行解掉的组仍会计入，故先用 `Spike/P1S6R7/collision_effective.py` 按每个出处实际显示的译文重算，再分组判。
**选项：** 非选择题。判法：① 机械同义（大小写、单复数、缩写与全称如 Qty／Quantity、标点写法），脚本 `Spike/P1S6R7/collision_classify.py` 判；② 其余逐组读各源词的演示面出处（文件:字段）判同义或异义；③ 异义的定词，`Spike/P1S6R4-occupancy.py` 查占用，占用者与之同义才可用。
**用户回答：** 待用户回答（E 步复核）
**结论：** **DJ-002**：200 组中 42 组已由 context 行解开；仍撞 158 组里，80 组机械同义、59 组逐组判同义保留（理由逐组见 `Spike/P1S6R7/collision_table.json`），19 组判异义、写 19 行定词（18 个源词，其中 `Document Naming` 两个 DocType 各一行）。定词全部未被占用或只被同义源词占用。E 点名的四组：`Stock Ledger`→库存台账（与 `Stock Ledger Entry` 物料凭证分开）；`Is Paid`／`Paid`、`Payment Type`／`Type of Payment`、`Paid Amount`／`Payment Amount` 三组已由 S3 改词解开（重算后不在仍撞表内）。两条判同义需留意：`应用`／`隐藏` 两组的出处是 `desktop_icon.json` DocType 定义文件，被基线脚本的图标 glob 误收，首页实际不显示，判同义保留；`商机`（CRM `Deals` 与 ERPNext `Opportunity`）判同一业务概念。
