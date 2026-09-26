# P1-S3-R1-A 术语标准草案（CR-001）

> 本文是 P1-S3 R1 的 A 步（shape）中 CR-001 议题的调研产物，由子 Agent 只读扫描产出。
> **不是已裁定的标准**——除「收付款方向 5 条」的方向归属已由用户裁定（方案丙）外，其余每一行的新用词都是**待裁选项**。
> 本文不改任何既有文件，不做任何 git 动作。

## 来源权威度分级

全文每条事实后括注来源，按下表读：

| 级 | 含义 | 本文中的形态 |
|---|---|---|
| **A** | **本 bench 已安装的源码与官方翻译**，可原地复算 | `erpnext:12345` = `frappe-bench/apps/erpnext/erpnext/locale/zh.po` 第 12345 行；`frappe:1234` 同理；DocType json 与 JS 给相对路径+行号 |
| **B** | **第三方仓与本项目既有文档的结论**，未逐条复核 | `Reference/zelin-tech-erpnext_china/.../zh.csv`；`P1-S2-R1-A参考项目-zelin-翻译.md:行号`；`最小闭环操作稿.md:行号` |
| **C** | **我的推断**，无源码支撑 | 全部集中在 §四；正文中不得不用时显式标 `[C]` |

**版本**：`frappe` 16.34.0 / `erpnext` 16.35.0（`frappe-bench/sites/apps.txt` 只列这两个 app）[A]。

### 开篇必读：两条改变前提的核实结果

**（1）演示站点上不装 zelin，故 914 组不是演示线的基线。**

`frappe-bench/sites/apps.txt` 只有 `frappe` 与 `erpnext` 两行 [A]，`erpnext_china` 未安装。S2 那 914 组是扫 `Reference/` 里 zelin 的 `zh.csv` 得出的 [B `P1-S2-R1-A参考项目-zelin-翻译.md:93`]，那份 csv 在本演示上**一条也不生效**（`translate.py:172-187` 只遍历 `frappe.get_installed_apps()` [A]）。

所以本文给两套数：

| 基线 | 撞名组 | 涉及源词 | 演示线上感知到的 |
|---|---|---|---|
| zelin `zh.csv`（S2 的 914 所在） | **917**（我复算值，与 914 有差，见 §5.3） | 2191 | 53 组 |
| **`frappe`+`erpnext` 官方 po（实际生效）** | **747** | 1770 | **143 组**（见 §2.3.4 的口径更正；初扫报 49 是方法失误） |

**本标准以 747/143 这套为准**，zelin 那套只当词汇素材（与 S2 移交事实 2 一致）。

**（2）「收付款方向」5 条全部是官方译文，不是 zelin 引入的。**

五条在官方 `erpnext/locale/zh.po` 里逐字就是那样 [A]：`Unpaid` → 未付 `:59191`、`Paid` → 已付款 `:35517`、`Paid Amount` → 付款金额 `:35541`、`Payment Type` → 付款类型 `:37024`、`Mode of Payment` → 付款方式 `:31702`。

即 Stage 概况执行边界第 2 条说的「两条继承自官方」是**低估**——收付款这 5 条也全是继承的。这不改变处置，但改变归因：**CR-001 是在修官方译文，不是在修第三方仓**。

## 一、收付款方向 5 条（用户已裁：方案丙）

### 1.0 `context` 的准确值：查实的结果

`context` 的 key 形态是 `source + ":" + context`（`frappe/translate.py:196-217` 的 csv 分支 [A]）。**运行期自动带进去的 context 值是 DocType 名**，三处渲染点确证：

| 渲染点 | 代码 | context 实际取值 |
|---|---|---|
| 字段标签 | `frappe/public/js/frappe/form/controls/base_input.js:198-200` 的 `__(this.df.label, null, this.df.parent)` [A] | `df.parent` = 该字段所属 DocType 名（子表字段则是**子表名**） |
| 可编辑 Select 的选项值 | `.../controls/select.js:158-177` 的 `__(v, null, doctype)`，doctype 由 `:78-83` 的 `this.df.context` → `this.df.parent` → `this.doctype` 三级回退传入 [A] | 同上。**`df.context` 是可用 Property Setter 注入的逃生口，不必改上游** |
| 列表状态徽标 | `erpnext/accounts/doctype/sales_invoice/sales_invoice_list.js:30`、`purchase_invoice_list.js:22,43` 都是裸 `__(doc.status)` [A] | **无 context** |

**一个容易写错的地方**：官方 `.po` 里那 147 条 `msgctxt` 的值**不是** DocType 名，是描述性短语（如 `Button in list view actions menu`、`Number system`、`Confirmation dialog message`）[A]——那是开发者在调用点手写的 context，与运行期自动带的 DocType 名是两套。**本标准要填的是 DocType 名那一套**。zelin 那 32 条 3 列行填的也是 DocType 名（如 `Rate,税率,Sales Taxes and Charges`）[B `P1-S2-R1-A参考项目-zelin-翻译.md:72-85`]，可作写法参照。

### 1.1 五条的落地表

| # | 源词 | context 值 | 目标词 | 落在哪些 DocType.字段 | 依据 |
|---|---|---|---|---|---|
| 1 | `Unpaid` | `Purchase Invoice` | **未付款** | `Purchase Invoice.status` 选项 | `erpnext/accounts/doctype/purchase_invoice/purchase_invoice.json:1277-1285`（Select，**无 read_only**）[A] |
| 1 | `Unpaid` | 无（平条目兜底） | 见 §1.2 末 | `Sales Invoice.status` 及一切裸渲染点 | `sales_invoice.json:1650-1661`（Select，**`read_only` = 1**）[A] |
| 2 | `Paid` | `Purchase Invoice` | **已付款** | `Purchase Invoice.status` 选项 | 同上 [A] |
| 2 | `Paid` | 无（兜底） | 见 §1.2 末 | `Sales Invoice.status` | 同上 [A] |
| 2b | `Is Paid` | — | **是否已付**（FREE） | `Purchase Invoice.is_paid` | `purchase_invoice.json:269` [A]。**必须一并改**：现译「已付款」（`erpnext:26545`）与 `Paid` 同词，两者同在 PI 一张表 |
| 3 | `Paid Amount` | `Purchase Invoice` | **付款金额** | `Purchase Invoice.paid_amount` | `purchase_invoice.json`（Currency）[A] |
| 3 | `Paid Amount` | `Sales Invoice` | **收款金额** | `Sales Invoice.paid_amount` | `sales_invoice.json`（Currency）[A]。该词现被 `Received Amount` 占，须同时办 3c |
| 3b | `Paid Amount` | `Payment Entry` | **出账金额**（FREE） | `Payment Entry.paid_amount` | `payment_entry.json:279-285` [A]。PE 一张单既收也付，方向不定，故取中性 |
| 3c | `Received Amount` | `Payment Entry` | **到账金额**（FREE） | `Payment Entry.received_amount` | 现译「收款金额」（`erpnext:43696`）[A]，**会与第 3 条销售侧撞**，且与 `paid_amount` 同在 PE 一张表 |
| 3d | `Paid Amount` | `Payment Schedule` | **已收付金额**（FREE） | `Payment Schedule.paid_amount` | `payment_schedule.json:88-90`，`istable` = 1 于 `:221` [A]。**共享子表，context 只取到子表名，分不出销/采** |
| 3e | `Payment Amount` | — | **分期金额**（FREE） | `Payment Schedule.payment_amount`、`Overdue Payment.payment_amount` | `payment_schedule.json:73-76`、`overdue_payment.json:84` [A]。现译「付款金额」与 3d **同一网格行两列撞名** |
| 4 | `Payment Type` | **不用 context** | **收付款类型**（FREE） | `Payment Entry.payment_type`（Select）、`Payment Entry Reference.payment_type`（Data） | `payment_entry.json:120-129`、`payment_entry_reference.json:130` [A] |
| 4b | `Type of Payment` | — | **收付款方向**（FREE） | `Payment Entry.type_of_payment`（**Section Break**） | `payment_entry.json:105-109` [A]。现译「付款类型」与第 4 条**同在 PE 一张表**（分节标题套着同名字段），必须另给一词。该分节下正是 `payment_type`（选项 `Receive/Pay/Internal Transfer`），叫「收付款方向」名实相符 |
| 5 | `Mode of Payment` | **不用 context** | **收付款方式**（FREE） | 17 处 label，见下 | 逐处 grep 所得 [A] |
| 5b | 同义族 `Mode Of Payment` / `Payment Mode` / `Payment Method` / `Mode of Payments` / `Modes of Payment` | — | **收付款方式**（一并改） | 报表列与设置项 | 现全译「付款方式」（`erpnext:31649` / `:36694` / `:36683` / `:31711` / `:31722`）[A]。不一并改则字段说「收付款方式」、报表说「付款方式」，看起来像两个东西 |

第 5 条的 17 处 label（全部 [A]）：`payment_entry.json:164`、`purchase_invoice.json:1016`、`sales_invoice_payment.json:23`、`payment_schedule.json:83`、`journal_entry.json:443`、`mode_of_payment.json:21`、`payment_request.json:102`、`payment_term.json:44`、`payment_terms_template_detail.json:89`、`overdue_payment.json:65`、`payment_order_reference.json:71`、`pos_payment_method.json:25`、`pos_closing_entry_detail.json:19`、`pos_opening_entry_detail.json:16`、`cashier_closing_payments.json:18`，另加 `workspace/invoicing.json:582` 与 `workspace_sidebar/accounts_setup.json:102`（导航侧，`boot.py:465` 的 `_(item.label)` 会译它 [A]）。

### 1.2 方案丙**落不了地**的四处（逐处有源码）

| # | 落不了的点 | 根因（源码） | 后果 | 可选出路 |
|---|---|---|---|---|
| 1 | **列表视图的状态徽标** | `sales_invoice_list.js:30`、`purchase_invoice_list.js:22,43` 是裸 `__(doc.status)`，不传 context [A]。本可救的 `meta.states` 分支（`frappe/public/js/frappe/model/indicator.js:82-87` 的 `__(doc.status, null, doctype)` [A]）救不了——`sales_invoice.json` 与 `purchase_invoice.json` 的 `states` 都是空数组 [A]，该分支不触发，erpnext 自己的 `get_indicator` 赢 | 两张发票的列表徽标一律显示**平条目**的词 | 改上游 `*_list.js`，或给两个 DocType 配 `states`（Workflow State） |
| 2 | **销售发票表单上的 `status`** | `sales_invoice.json:1650` 有 `read_only` = 1 [A]，于是走 `base_input.js:104-152` 的 `set_disp_area` → `base_input.js:178` 的 `frappe.format(...)` → **`frappe/public/js/frappe/form/formatters.js:52-54` 的 `Select` 分支，里面是裸 `__()`，无 context** [A]。而 `purchase_invoice.json:1277` 的 `status` **没有** `read_only`，走 `select.js:172` 是**带** context 的 | **销采不对称**：PI 表单能按 context 显示「未付款」，SI 表单只能吃平条目 | 去掉 SI `status` 的 `read_only`（会让字段可编辑，不可取），或改上游 formatter，或接受平条目 |
| 3 | **标准筛选器（`in_standard_filter`）的选项值** | 标签是 `__(df.label, null, df.parent)`（`base_list.js:1145` 起的 `make_standard_filters` [A]），但控件经 `frappe/public/js/frappe/ui/page.js:843` 的 `add_field` 构造时**不传 doctype**，`select.js:82` 的三级回退全 undefined [A] | 筛选下拉里的 `Unpaid`/`Paid` 吃平条目 | 用 Property Setter 给该字段设 `df.context`（`select.js:82` 的逃生口）[A] |
| 4 | **共享子表 `Payment Schedule` / `Sales Invoice Payment` / `Overdue Payment` / `Payment Entry Reference`** | 都是 `istable` = 1 的共享子表（`payment_schedule.json:221`、`payment_entry_reference.json:177` [A]），父单可以是 SO / SI / PO / PI / Quotation / POS Invoice。渲染时 `df.parent` = **子表名**，一个 context 值分不出销/采 | 「收款金额 / 付款金额」在这些格子里**无法二分** | 只能给中性词（已按此办，见 3d / 3e） |

**由此定出「平条目（无 context）取哪个词」——这是落地成败的关键，且用户裁决未覆盖：**

裸渲染点（列表徽标、SI 表单只读 status、筛选下拉）一律吃平条目。

- 若平条目取采购侧词（即保持现状「未付」），销售侧 3 个渲染面全错（客户欠我的钱写成「未付」）。
- 若取销售侧词「未收款」，采购侧只剩列表徽标与筛选 2 个面错（表单靠 context 正确）。
- **[C] 我的建议**：平条目取**方向中性**词，两个方向词全靠 context 上——`Unpaid` 平条目 → **未结**（查实 FREE [A]）；`Paid` 平条目 → **已付讫**（查实 FREE [A]；不能用「已结清」，被 `Settled` 占，`erpnext:50658`）。这样裸渲染点的词**不精确但不会方向错**。此条属推断，记入 §四-1 供裁。

### 1.3 连带必须改的（否则改完会新生撞名）

| 源词 | 现译 | 冲突原因 | 建议新词（均查实 FREE） | 依据 |
|---|---|---|---|---|
| `Is Paid` | 已付款（`erpnext:26545`） | 与 `Paid` 采购侧同词，同在 PI 一张表 | 是否已付 | `purchase_invoice.json:269` [A] |
| `Received Amount` | 收款金额（`erpnext:43696`） | 与 `Paid Amount` 销售侧同词，且与 `paid_amount` 同在 PE 一张表 | 到账金额 | `payment_entry.json` [A] |
| `Outstanding Amount` | 未付金额（`erpnext:34847`） | 销售侧语义是「未收」，方向错；且须与 `Outstanding` 同步（见 §2.3 未付组） | 未结金额 | [A] |
| `Outward` / `Inward` | 付款 / 收款（`erpnext:34875` / `:26220`） | 报表里指资金流向，不是动作；且占着「付款」「收款」两词 | 资金流出 / 资金流入 | [A]，不在演示线渲染面上，一并建议 |

**占用核查方法**（全文所有「FREE」的来路）：把 `frappe` + `erpnext` 两份 `locale/zh.po` 反向索引成「目标词 → 占用它的源词」，逐个候选词查是否已被占。标 FREE 即无任何源词占用 [A]。不做这步的话，改词只是把撞名挪个地方。脚本见 §2.2。

## 二、演示线撞名组的目标侧唯一用词

### 2.1 演示线边界的界定法（据 23 环节）

Stage 概况（S2 移交资产表）定「演示线的边界即由最小闭环操作稿界定」。本文把它**操作化**成一条可机械判定的判据。

**先否掉一个错做法**：拿撞名组的目标词去操作稿正文里文本匹配。实测会大量过采——「上」会匹配到 `Up` / `on`，「04」会匹配到 `Apr` / `May`。已弃用。

**采用的判据**：一个源词在演示线上，当且仅当用户走 23 环节时**能看见它渲染出来**，即它是以下三者之一：

1. 演示线 DocType 的**字段 label**（渲染为表单标签，`base_input.js:200` [A]）；
2. 该 DocType 某字段的**Select 选项值**（渲染为值，`select.js:172` [A]）；
3. 该 DocType 自己的 `.js` / `_list.js` 里的 `__("...")` 字面量（渲染为按钮 / 徽标 / 对话框标题）。

**演示线 DocType 的取法**：从操作稿的 23 个环节标题及其步骤里手工取出「用户真的打开了表单或列表」的 DocType，**39 个**；再自动展开它们的子表（Table / Table MultiSelect 字段的 options），子表 label 渲染在父单网格里，也算看得见 → **共 109 个**在范围内 [A 脚本输出]。

环节行号锚点（`最小闭环操作稿.md`，`grep -n '^## '` 所得 [A]）：环节 0 `:59`、1 `:117`、2 `:217`、3 `:280`、4 `:325`、5 `:412`、6 `:532`、7 `:691`、8 `:724`、9 `:764`、10 `:842`、11 `:915`、12 `:963`、★13 `:1025`、14 `:1146`、15 `:1185`、16 `:1237`、17 `:1288`、18 `:1379`、19 `:1461`、★20 `:1585`、21 `:1714`、22 `:1759`、★23 `:1813`。

按环节归的五个阶段（后文「在哪个环节看到」用它定位）：

| 阶段 | 环节 | 主要 DocType |
|---|---|---|
| **P0 建底座** | 0–3 | Company / Global Defaults / Fiscal Year / Account / Warehouse / Cost Center / UOM / Stock Settings / Accounts Settings / Manufacturing Settings / Transaction Deletion Record |
| **P1 建主数据** | 4–7 | Item / Item Group / Item Price / Price List / Operation / Workstation / BOM / Customer / Supplier |
| **P2 采购到付款** | 8–13 | Purchase Order / Purchase Receipt / Purchase Invoice / Payment Entry / Mode of Payment / GL Entry / Stock Ledger Entry / Bin |
| **P3 订单到生产** | 14–20 | Quotation / Sales Order / Production Plan / Work Order / Job Card / Stock Entry / Stock Entry Type |
| **P4 发货到收款** | 21–23 | Delivery Note / Sales Invoice |

**一处已知的过采边界**：Stock Settings / Accounts Settings / Manufacturing Settings 这三张设置表，操作稿是**作为 Company 的分节**进去的（`最小闭环操作稿.md:145,151` 的 Company 分节；`Manufacturing Settings` 在 `:185,1306` 被提到但没有仓库字段 [B]），不是打开独立的设置页。把它们整表算进范围会略微放大「看得见」的集合。涉及的组在 §2.3 里已标注。

### 2.2 撞名机械扫的方法与脚本

五个脚本全部只读，留在 `Spike/` 下，可原地复跑：

| 脚本 | 做什么 | 关键输出 |
|---|---|---|
| `Spike/P1S3R1-collision-scan.py` | 扫 zelin `zh.csv`（变长列，按 `translate.py:196-217` 的约定解析 3 列 = context 行），反向索引求「同一目标词 ≥2 源词」 | 唯一平条目 source 18296、context 行 32、目标词 17022、**撞名组 917**、涉及源词 2191 |
| `Spike/P1S3R1-collision-classify.py` | 归一化剔掉**良性变体**（大小写、单复数含不规则、前导 `against/for/from/to/set/in/on/by/is/enter/...`、尾随角色词） | **良性 104 / 真撞名 170**（自 274 组松散触线组中分） |
| `Spike/P1S3R1-demoline-intersect.py` | 按 §2.1 三条判据求交集；每个命中点记下**渲染点是否可带 context**（`[CTX-OK ...]` / `[BARE ...]`） | 范围内 DocType 109、可渲染串 2189、**≥2 源词可见的真撞名组 53**、只有 1 源词可见的 58 |
| `Spike/P1S3R1-official-po-collisions.py` | **同一套扫法改打实际生效的基线**（`frappe` + `erpnext` 的 `locale/zh.po`），自写 po 解析器处理 `msgctxt` 与多行续接 | frappe 5990 / erpnext 8415 条有译文；唯一 msgid（无 msgctxt）14250、msgctxt 条 147、目标词 13227、**撞名组 747**、涉及 msgid 1770。**它报的「演示线上 49 组」是错的**——见下一行 |
| `Spike/P1S3R1-po-demoline-direct.py` | **口径更正扫**。上一行那个脚本判「在演示线上」时，是拿 msgid 去问 zelin 的 GENUINE 组源词集，**等于先被 zelin 的词表筛了一道**。本脚本直接用演示线 DocType 的渲染面（同一套 harvest 规则）去交官方 po 的 747 组 | 演示线 DocType 109（含子表）、可渲染串 2189；**≥2 源词在演示线上可见 143 组**、恰 1 个可见 206、完全不在线 398。143 组里 **49 组是初扫已覆盖的（一组没丢）**，**新增 94 组** |
| `Spike/P1S3R1-cooccurrence.py` | 给初扫那 49 组排危害：两个撞名源词**同屏**（同 DocType 或其子表）= SAME-FORM；**同阶段不同屏** = SAME-FLOW；否则 SPLIT | **SAME-FORM 21 / SAME-FLOW 9 / SPLIT 19** |

**为什么要按同屏排序**：撞名只在用户「同时看见两个同名标签且分不清哪个是哪个」时才真正咬人。同屏的 21 组是演示里会被当场问住的，SPLIT 的 19 组只是术语不整齐。CR-001 的有限工时应按这个次序花。

**917 与 S2 的 914 对不上**，已试的变体：原始平条目 917；source 与 target 都去空白 910；把 3 列行的 source 也算进去 917；source 转小写 823。914 落在 910 与 917 之间，任何直白变体都复现不出。记入 §5.3。

### 2.3 交集结果：演示线上的撞名组

**先加一条判据，否则会白改一批**：撞名分两种——

- **异义撞名**：两个源词**意思不同**却共用一个中文词，用户分不清哪个是哪个。**必须改**。
- **同义撞名**：两个源词**本来就是一回事**，只是官方源串写法不统一（`Qty` / `Quantity`、`WIP Warehouse` / `Work-in-Progress Warehouse`、` BOM` / `BOM`）。共用一个中文词**是对的**，改反而制造混乱。**不改**，只在 §5.1 报给上游。

先按初扫那 49 组逐组定（§2.3.1–2.3.3），再补上口径更正扫新增的 94 组（§2.3.4）。**49 组里 43 组需要至少改一个源词的用词，6 组属同义写法、共用一个中文词是对的，不改**（计数核对见 §2.3.3 表后附注 3）。

下表「环节」列按 §2.1 的阶段与环节号，指用户在哪一步会看到。每个新词都过了占用核查（§1.3 末），标 FREE 即无源词占用 [A]。

#### 2.3.1 SAME-FORM 21 组（两个同名标签**同屏**，危害最高，优先办）

| 目标词 | 撞它的源词（po 行号） | 处置 | 环节 |
|---|---|---|---|
| **数量** | `Qty` `erpnext:41993`／`Qty ` `:41997`／`Quantity` `:42625`／`Batch Quantity` `:8320` | **同义，表单上那三个不改**（都是数量，`Qty ` 只是官方源串多个尾空格）。仅 `Batch Quantity` → **批次数量**（FREE），它指批次可用量，与行数量不是一回事 | 6·8·15·18·22 全程 |
| **联系人** | `Contact` `frappe:5844`／`Contact Person` `erpnext:12630`／`Contacts` `frappe:5894` | `Contact Person` **保留 联系人**（是 Link 选择框，真正那个）；`Contact` → **联系人详情**（FREE），它是 `contact_display` Small Text，显示姓名电话一串；`Contacts` 不在表单渲染面，保留。**七张单上这两个字段并排**（Purchase Receipt／Purchase Invoice／Quotation／Sales Order／Delivery Note／Sales Invoice／Payment Entry）[A] | 9·10·11·14·15·21·22 |
| **付款金额** | `Paid Amount` `:35541`／`Payment Amount` `:36486` | 见 §1.1 第 3／3b／3d／3e 行。**`Payment Schedule` 子表一行里两列同名**（`payment_schedule.json:73-76` 与 `:88-90`）[A] | 10·11·15·22 |
| **更多信息** | `More Info` `frappe:17535`／`More Information` `frappe:17549`／`Other Info` `erpnext:34678` | `More Info` **保留**；`More Information` → **补充信息**（FREE）；`Other Info` → **其它信息**（FREE）。三者是三个不同的分节／页签，Stock Entry 上同时有后两个（`.more_info` 与 `.other_info_tab`），BOM 上同时有前两个 [A] | 6·8·18 |
| **工序** | `Operation` `frappe:19745`／`Operations` `erpnext:34300`／`Item operation` `:28039`／`For Operation` `:21407` | `Operation` **保留 工序**；`Operations` → **工序清单**（FREE，是 Table 与其分节标题）；`Item operation` → **所属工序**（FREE，`BOM Item.operation`，指该行料在哪道工序领用）；`For Operation` → **对应工序**（FREE，`Job Card.for_operation`）。**BOM 表上同屏三个**，Job Card 上同屏两个 [A] | 6·17·19 |
| **税费** | `Taxes and Charges` `:55063`／`Taxes and Charges Added` `:55078` | 分节标题 `Taxes and Charges` **保留 税费**；`Taxes and Charges Added` → **加计税费**（FREE），与官方已有的 `Taxes and Charges Deducted` → 抵扣税费（`:55138`）成对 [A]。**采购三张单上分节标题与金额字段同屏同名** | 8·9·10 |
| **仓库** | `Warehouse` `frappe:31281`／`Warehouses` `:61168`／`For Warehouse` `:21461`／`Accepted Warehouse` `:1359`／`Request for` `:44937`／`Requesting Site` `:45030`／`Stores` `:52957` | `Warehouse` **保留 仓库**；`Warehouses` → **仓库范围**（FREE，`Production Plan.warehouses` 是 Table MultiSelect）；`For Warehouse` → **需求仓库**（FREE，`Production Plan.for_warehouse`，即"产给哪个仓"）；`Accepted Warehouse` → **验收仓库**（FREE，与官方 `Rejected Warehouse` → 拒收仓 `:44371` 成对）；`Request for` → **补货仓库**（FREE，见表后注）；`Requesting Site` → **需求方地点**（FREE）；`Stores` → **库房**（FREE，是仓库记录名不是字段）。**Production Plan 上同屏三个** [A] | 2·9·10·16 |
| **完工数量** | `Completed Qty` `:12072`／`Manufactured Qty` `:30261`／`Produced Qty` `:40521` | `Manufactured Qty` **保留 完工数量**（`Work Order.produced_qty` 与 `Job Card.manufactured_qty`，整单级）；`Completed Qty` → **已报工数量**（FREE，`Work Order Operation`／`Job Card Operation`／`Job Card Time Log`，工序级）；`Produced Qty` → **已生产数量**（FREE，`Production Plan Item`，计划行级）。**Work Order 与 Job Card 两张表上都同屏两个** [A] | 17·19·20 |
| **成本价** | `Valuation Rate` `:60208`／`Valuation` `:60141`／`Incoming Rate (Costing)` `:24998`／`Costing Rate` `:13343` | `Valuation Rate` **保留 成本价**；`Valuation` → **计入成本价**（FREE，是 `Purchase Taxes and Charges.category` 的选项；官方 `Valuation and Total` → 成本价与总计 `:60251` 宜随之改「计入成本价与总计」）；`Incoming Rate (Costing)` → **出库成本价**（**同义合并**到官方 `Outgoing Rate`／`Consumption Rate` 已有的 `:34798`／`:12515`，它是 SI 行的销货成本）；`Costing Rate` 只在报表列，本 Stage 不定（§5.2）。**Purchase Receipt／Purchase Invoice 上 `Valuation` 与 `Valuation Rate` 同屏** [A] | 9·10·22 |
| **未付** | `Unpaid` `:59191`／`Outstanding` `:34809` | 见 §1.1 与 §1.2。`Outstanding` → **未结**（FREE）、`Outstanding Amount` → **未结金额**（FREE）。**两张发票上状态值与未结金额同屏** | 10·11·22 |
| **付款** | `Pay` `:36405`／`Payment` `:36469`／`Payments` `:37110`／`Outward` `:34875` | `Pay` **保留 付款**（`Payment Entry.payment_type` 选项，与 `Receive` → 收款 `:43683` 成对）；`Payments` → **收付款**（FREE，PI 与 SI 上的页签与分节、`Accounts Settings.payments_tab`）；`Payment` → **收付款单**（FREE，`Accounts Settings.exchange_gain_loss_posting_date` 的选项，意为"按收付款单的日期"）；`Outward` → **资金流出**（FREE）。**Accounts Settings 上 `Payment` 与 `Payments` 同屏** [A] | 10·11·22 |
| **付款类型** | `Payment Type` `:37024`／`Type of Payment` `:58691` | 见 §1.1 第 4／4b。**`Type of Payment` 是 Section Break，它正套着 `payment_type` 字段**，同屏同名 | 11 |
| **工单数量** | `Qty To Manufacture` `:42082`／`Planned Qty` `:37867`／`Planned Quantity` `:37877`／`Work Order Qty` `:61856` | `Qty To Manufacture` **保留 工单数量**（`Work Order.qty`／`Job Card.for_quantity`）；`Planned Qty` → **计划数量**（FREE，`Bin.planned_qty`／`Production Plan Item.planned_qty`）；`Planned Quantity` → **计划生产数量**（FREE）；`Work Order Qty` → **已开工单数量**（FREE）。**`Sales Order Item` 同一行里 `planned_qty` 与 `work_order_qty` 两列并排**——一个是"打算生产多少"、一个是"已开出工单多少"，必须分开 [A] | 15·16·17·19 |
| **工费成本** | `Operating Cost` `:34170`／`Operating Costs` `:34195` | `Operating Cost` **保留 工费成本**；`Operating Costs` → **工费构成**（FREE，`Workstation.over_heads` 是页签标题）。**Workstation 上页签标题与金额字段同屏** | 5·6 |
| **待处理** | `Open` `frappe:19619`／`Pending` `frappe:20495` | `Open` **保留 待处理**（`Job Card.status`／`Quotation.status`）；`Pending` → **待执行**（FREE，`Job Card Operation.status` 与 Transaction Deletion Record 六个进度字段）。**Job Card 表上单级状态与工序行状态同屏** | 0·14·19 |
| **成品** | `Finished Goods` `:21045`／`Finished Good` `:20951`／`Item To Manufacture` `:27868`／`Production Item` `:40652`／`Final Product` `:20794` | `Finished Goods`／`Item To Manufacture`／`Final Product` **保留 成品**（泛称、`Work Order.production_item`、`Job Card.production_item`，语义同一）；`Finished Good`（单数）→ **成品件**（FREE，`Purchase Order Item.fg_item`／`Sales Order Item.fg_item`／`Production Plan Sub Assembly Item.parent_item_code`，指具体那一件）；`Production Item` → **成品信息**（FREE，它是 BOM 与 Work Order 上的**页签标题**）。**Work Order 上页签标题与字段同屏同名** [A] | 6·8·15·16·17·19 |
| **物料号** | `Item Code` `:27197`／`Item Reference` `:27741` | `Item Code` **保留 物料号**；`Item Reference` → **物料参照号**（FREE，`Production Plan Item.item_reference` 是 Data，存外部参照号）。**Production Plan 明细行两列同屏** | 16 |
| **科目表模板** | `Chart Of Accounts Template` `:10516`／`Create Chart Of Accounts Based On` `:13508` | `Chart Of Accounts Template` **保留**；`Create Chart Of Accounts Based On` → **科目表来源**（FREE，`Company.create_chart_of_accounts_based_on`，选"按模板建还是按现有公司建"）。**Company 上两个 Select 同屏同名，是演示第一屏就撞的一组** | 1 |
| **税** | `Tax` `:54604`／`Taxes` `:55034`／`Tax Masters` `:54771` | `Tax` **保留 税**（`Account.account_type` 选项与 Customer／Supplier／Item 的税页签）；`Taxes` → **税率表**（FREE，`Item.taxes`／`Item Group.taxes` 是子表，`Sales Order.taxes_section` 分节宜随之调）；`Tax Masters` 只在报表／工作区，本 Stage 不定（§5.2）。**Item 表上页签标题与子表同屏同名** | 1·4·7·15 |
| **进行中** | `Work In Progress` `:61768`／`Work in Progress` `:61930`／`In Process` `:24533`／`In Progress` `frappe:13862`／`Ongoing` `:33717` | `Work In Progress`（`Job Card.status`）与 `In Progress` **保留 进行中**；`In Process` → **生产中**（FREE，`Work Order.status`／`Production Plan.status`，整单在产）；`Work in Progress`（小写 p，`Work Order Operation.status`）→ **在制**（FREE，工序级）；`Ongoing` 不在表单渲染面，不定。**Work Order 上单级状态与工序行状态同屏**，Job Card 同理 [A] | 16·17·19 |
| **采购** | `Purchase` `:41256`／`Purchasing` `:41837`／`Buying` `:9285`／`Buy` `:9249`／`For Buying` `:21382`／`Procurement` `:40479`／`Purchased` `:41825`／`Purchases` `:41829` | `Purchase` **保留 采购**（`Item.default_material_request_type` 等选项）；`Purchasing` → **采购属性**（FREE，`Item.purchasing_tab` 页签；不能用「采购信息」，已被 `Purchase Details` `:41296` 占）；`Buying` → **用于采购**（FREE，`Item Price.buying`／`Price List.buying` 是 Check）；其余五个只在报表／工作区，**保留 采购**。**Item 表上页签标题与选项值同屏同名** | 4 |

**`Request for` 与 `Requesting Site` 的误归疑问已核实——不是误归。** `Request for` 确实是 `erpnext/stock/doctype/item_reorder/item_reorder.json:33` 上 `warehouse` 这个 Link 字段的 label [A]，译「仓库」语义不错，只是官方 label 起得差；`Requesting Site` 是 `erpnext/buying/report/procurement_tracker/procurement_tracker.py:46` 的报表列 `_("Requesting Site")` [A]，官方 po `:45030` 就译「仓库」。两条都**继承自官方**，不是 zelin 引入的。S2 文档记为「明显误归」[B `P1-S2-R1-A参考项目-zelin-翻译.md:104,174-175`]，应更正为「官方 label 用词差 + 官方译文过度合并」。

#### 2.3.2 SAME-FLOW 9 组（不同屏但**同一阶段**内，用户会带着词走到下一屏）

| 目标词 | 撞它的源词（po 行号） | 处置 | 环节 |
|---|---|---|---|
| **会计** | `Accounts` `:2181`／`Accounting` `:1816`／`Accountant` `:1790`／`Accounts User` `frappe:1079` | `Accounting` **保留 会计**（Item／Customer／Supplier 的页签与 PI 行分节）；`Accounts` → **会计科目**（FREE，`Company.accounts_tab`／`Mode of Payment.accounts`／`Payment Entry.payment_accounts_section`，实指科目而非"会计"）；`Accountant` → **会计人员**（FREE，是角色名）；`Accounts User` → **会计操作员**（FREE，角色名）。**注**：`Account` 单数官方已译「科目」（`frappe:1057`），所以把 `Accounts` 改成「会计科目」与它同族 [A] | P0 1·P1 4·7·P2 10·11 |
| **单据类型** | `DocType` `frappe:8174`／`Doctype` `frappe:8283`／`Document Type` `frappe:8529`／`Document Types`／`Against Doctype`／`Enter Form Type`／`For Document Type`／`From Document Type`（8 个） | `DocType`／`Doctype`／`Document Type` 属**同义**（官方源串大小写不统一），**保留 单据类型**；`Against Doctype` → **源单类型**（FREE，`Quotation Item.prevdoc_doctype`，指报价行来自哪张单）；其余四个只在报表／对话框，本 Stage 不定。**注**：官方另有一族 `Reference DocType`／`Ref DocType`／`Link DocType`／`Source Document Type` 等 10 个源词全译「源单据类型」[A]，改 `Against Doctype` 时要避开那个词 | P0 0·P3 14 |
| **收到数量** | `Received Qty` `:43756`／`Received Quantity` `:43774`／`In Qty` `:24544` | `Received Qty` 与 `Received Quantity` **同义，保留 收到数量**；`In Qty` → **入库数量**（FREE，库存报表列，与官方 `Out Qty` → 发出数量 `:34741` 成对）| P2 8·9·10 |
| **日期** | `Date` `frappe:7023`／`Dates` `erpnext:15538`／`As On Date`／`On This Date` | `Date` **保留 日期**；`Dates` → **日期区间**（FREE，`GL Entry.dates_section` 分节）；`As On Date`／`On This Date` 只在报表筛选，本 Stage 不定 | P2 8·9·13 |
| **生产** | `Manufacturing` `:30352`／`Production` `:40624`／`For Production`／`production` | `Manufacturing` **保留 生产**（Company／Item 的分节与页签）；`Production` → **生产中**？**不可**——已给 `In Process`。它是 `Workstation.status` 的选项（工位状态"正在生产"），取 **运行中**（FREE）；`For Production`／`production` 只在报表，不定 | P0 1·P1 4·5·P3 16 |
| **设置** | `Settings` `frappe:25853`／`Setup` `frappe:25873`／`Setting`／`Set` | 这是 S1 记的「缺陷 1」。`Settings` **保留 设置**（Customer／Supplier 的 `settings_tab`）；`Setup` → **调机**（FREE）——核实后它在演示线上的唯一渲染点是 `Workstation.status` 的选项，指工位"正在调机准备"，不是"设置"[A]，官方这条译文本身就是**误译**；`Setting`／`Set` 不在表单渲染面。**这条与 S2 记的形态不同**：S2 说的是侧栏两个分节同名 [B]，那属工作区定义（S6 的 CR-002 范围），演示线上的 `Setup` 其实是工位状态 | P1 5·7 |
| **车间仓** | `WIP Warehouse` `:60992`／`Work-in-Progress Warehouse` `:61935` | **同义，不改**。同一概念官方两种写法（`BOM Operation.wip_warehouse`／`Job Card.wip_warehouse` 用前者，`Work Order.wip_warehouse` 用后者）[A]。**注**：官方另有 `WIP WH` → 在制品仓库（`:60984`），三条同义却两个译名，宜统一到「车间仓」 | P3 17·18·19·20 |
| **选物料** | `Get Items` `frappe:12120`／`Get Items From` `erpnext:22556` | `Get Items` **保留 选物料**（`Stock Entry.get_items` 按钮）；`Get Items From` → **取物料来源**（FREE，`Production Plan.get_items_from` 是 Select，选"从销售订单还是从物料需求取"）。一个是动作按钮、一个是来源选择框，同译会让人以为点了就取 | P3 16·18 |
| **销售** | `Sales` `:47741`／`Selling` `:49480`／`For Selling`／`Sell` | `Sales` **保留 销售**（`Item.sales_details` 页签、`Quotation.order_type`／`Sales Order.order_type` 选项）；`Selling` → **用于销售**（FREE，`Item Price.selling`／`Price List.selling` 是 Check，与 §2.3.1 `Buying` → 用于采购 对称）；`For Selling`／`Sell` 只在报表，不定 | P1 4 |

#### 2.3.3 SPLIT 19 组（两个源词分散在不同屏且不同阶段，危害最低）

这批**不同屏**，用户不会当场对着两个同名标签发懵，但仍会"同一个中文词在两处指两件事"。**按语义先过一遍异义／同义**：19 组里 **14 组异义须改、5 组是同义或纯写法变体不改**。

| 目标词 | 撞它的源词（po 行号） | 处置 | 环节 |
|---|---|---|---|
| **借方** | `Debit` `erpnext:15676`／`Debit Amount` `:15701` | `Debit` **保留 借方**（`Account.balance_must_be` 的选项，指"该科目余额方向必须是借"）；`Debit Amount` → **借方金额**（FREE，`GL Entry.debit` 是金额字段）。一个是方向、一个是钱数 [A] | 1·13 |
| **贷方** | `Cr` `:13473`／`Credit` `:14086`／`Credit Amount` `:14112` | `Cr` 与 `Credit` **同义保留 贷方**（前者是科目树上的余额方向标记 `account_tree.js:63`，后者是 `Account.balance_must_be` 选项）；`Credit Amount` → **贷方金额**（FREE，`GL Entry.credit`）[A]。**另见表后「`Dr` → 博士」一条，那是同一处渲染点上的独立缺陷** | 1·13 |
| **完成** | `Complete` `frappe:5562`／`Done` `frappe:8723`／`Finish` `erpnext:20933` | `Complete` **保留 完成**（`Job Card Operation.status` 的状态值）；`Done` → **已处理**（FREE，`Transaction Deletion Record Details.done` 是个 Check，指该表清完了）；`Finish` → **完工**（FREE，`work_order.js:904/919/928` 的按钮，制造语境标准说法就是"完工"，且它触发的是生成完工入库的 Stock Entry）[A] | 0·19·20 |
| **工单发料** | `Material Transfer for Manufacture` `:30944`／`Material Transferred for Manufacture` `:30959` | `Material Transfer for Manufacture` **保留 工单发料**（`Stock Entry.purpose`／`Stock Entry Type.purpose`，它是**单据用途**）；`Material Transferred for Manufacture` → **已发工单料**（FREE，`BOM.backflush_based_on`／`Manufacturing Settings.backflush_raw_materials_based_on` 的选项，意思是"倒冲按已发的工单料算"，是**倒冲依据**不是单据用途）[A]。两者只差一个 `-ed`，官方本身就容易混 | 3·6·18 |
| **库存设置** | `Inventory Settings` `:25987`／`Stock Settings` `:52629` | `Stock Settings` **保留 库存设置**（既是全局设置 DocType，又是 `Company.auto_accounting_for_stock_settings` 分节）；`Inventory Settings` → **库存参数**（FREE，`Item.inventory_settings_section`，是**单个物料**的库存参数分节，不是全局设置）[A] | 3·4 |
| **库存** | `Stock` `:52066`／`Inventory` `:25956`／`In Stock` `:24548` | `Stock` **保留 库存**（`Account.account_type` 选项 + `item_list.js:21` 的列表筛选）；`Inventory` → **库存信息**（FREE，`Item.inventory_section` 是分节标题）；`In Stock` → **有库存**（FREE，它是个布尔状态"有货"，不是"库存"这个名词）[A] | 1·4·7 |
| **应收账款** | `Accounts Receivable` `:2244`／`Debtors` `:15827`／`Receivable` `:43645`／`Receivable Account` `:43659`／`Receivables` `:43676` | **这就是 Stage 概况 §2 点名的两条继承缺陷之一** [B `P1-S3-概况.md:35`]。`Accounts Receivable` **保留 应收账款**（`customer.js:162` 的按钮，指的是那张报表）；`Receivable` → **应收类**（FREE，`Account.account_type` 的选项，它标的是**科目类别**不是科目名）；`Debtors` → **应收账款**科目名本身，**保留**（是科目表里的记录名）；`Receivable Account` → **应收科目**（FREE）；`Receivables` 只在报表／工作区，保留。**关键**：真正咬人的是 `Receivable`（科目类别选项）与 `Debtors`（科目名）在建科目那一屏都显示「应收账款」，改前者即解 [A] | 1·22·23 |
| **应付账款** | `Accounts Payable` `:2219`／`Creditors` `:14276`／`Payable` `:36426`／`Payables` `:36441` | 与上一组对称。`Accounts Payable` **保留**（`supplier.js:135` 按钮）；`Payable` → **应付类**（FREE，`Account.account_type` 选项）；`Creditors` **保留 应付账款**（科目名）；`Payables` 只在报表，保留。**不能给 `Payable` 用「应付科目」**——已被 `Payable Account` `:36434` 占 [A] | 1·11·12 |
| **发票** | `Invoice` `:26027`／`Invoices` `:26188`／`Billing` `frappe:3847`／`Linked Invoices` `:29371` | `Invoice` → **发票**，但它在演示线上的唯一渲染点是 `Accounts Settings.exchange_gain_loss_posting_date` 的选项，意为"按发票的过账日"，**保留**；`Invoices` → **发票列表**（FREE，`Supplier.hold_type` 的选项，指"暂停哪一类：发票还是付款"——此处宜作 **发票类**，见 §4 推断）；`Billing`／`Linked Invoices` 不在演示线表单面，保留 [A]。**本组危害最低**：两处都是下拉选项且隔了九个环节 | 3·9 |
| **开始日期** | `From Date` `frappe:11916`／`Start Date` `frappe:26930`／`Date of Commencement` `erpnext:15501` | `From Date` 与 `Start Date` **同义保留 开始日期**（六张单上的 `from_date`／服务期起始）；`Date of Commencement` → **开业日期**（FREE，`Company.date_of_commencement`，指公司成立开业那天，与单据的期间起始完全两回事，在演示第一屏就出现）[A] | 1·10·11·16 |
| **源单** | `Return Against` `:45663`／`Adjustment Against` `:3424` | `Return Against` → **退货源单**（FREE，`Sales Invoice.return_against`／`Delivery Note.return_against`，指这张退货单冲的是哪张原单）；`Adjustment Against` → **冲销源单**（FREE，`sales_invoice.js:1180` 的对话框字段）。**两个都改**——「源单」太泛，两处都需要说清"冲什么的源单" [A] | 21·22 |
| **物料清单** | ` BOM` `:44`／`BOM` `:7095`／`Bill of Materials` `:8458` | **同义，全部保留**。` BOM` 只是官方源串带了个前导空格（`:44`，同一个词）；`Bill of Materials` 是 `BOM` 的全称（`stock_entry.js:786`）。三条共用「物料清单」是**对的** [A]。只在 §5.1 报给上游：` BOM` 那条前导空格是官方源串的脏数据 | 6·8·18 |
| **物料清单号** | `BOM No` `:7228`／`BOM Detail No` `:7168` | `BOM No` **保留 物料清单号**（八张单上的 `bom_no` Link）；`BOM Detail No` → **物料清单行号**（FREE，`Purchase Order Item Supplied.bom_detail_no`／`Purchase Receipt Item Supplied.bom_detail_no`，指的是 BOM **明细行**的行 ID，不是 BOM 本身）[A]。这条在委外发料场景会直接选错 | 6·9·16·17 |
| **结束时间** | `To Time` `:57015`／`End Time` `:19448`／`Ended At` `frappe:9892`／`Ends on` `frappe:9903`／`To Datetime` `:56853` | `To Time` 与 `End Time` 在演示线上**是同义的两处**（`Job Card Time Log.to_time`／`Workstation Working Hour.end_time`，都是"到几点"）→ **保留 结束时间**；`Ended At`／`Ends on`／`To Datetime` 不在演示线表单面，不定 [A]。**本组判为不改** | 5·19 |
| **行业** | `Industry` `:25210`／`Domain` `frappe:8659` | `Industry` **保留 行业**（`Customer.industry`，客户所属行业）；`Domain` → **业务领域**（FREE，`Company.domain`，它是 ERPNext 的 Domain 机制——制造／零售／服务那套开关，不是客户行业）[A]。演示第一屏建公司时就会碰 | 1·7 |
| **销售税费模板** | `Sales Taxes and Charges Template` `:48494`／`Sales Tax Template` `:48442` | **同义，不改**。后者只在 `company.js:144` 一处（建公司时自动建模板的提示），指的就是前者那个 DocType [A] | 1·14·15·21·22 |
| **会计凭证** | `Ledger` `frappe:15787`／`Accounting Ledger` `:2117` | **两个都是"账簿"不是"凭证"**，官方这条译文本身就错（S1 已记为确定译错 [B `P1-S2-R1-A参考项目-zelin-翻译.md:178`]）。两处都是跳 General Ledger 报表的按钮（`payment_entry.js:426`／`customer.js:173`／`supplier.js:123`），**都改为 会计账簿**（FREE）。改完这组**不再是撞名**（两源词同义），但**必须改**——因为官方另有 `Voucher` → 凭证 `:60758`，现状是"账簿"和"凭证"两个概念在中文里被拉平 [A] | 11·12·23 |
| **重新打开** | `Re-open` `:43470`／`Reopen` `frappe:23107` | **同义，不改**。同一动作官方两种拼法，七个按钮点位（Production Plan／Purchase Order／Sales Order／Delivery Note／Purchase Receipt）语义完全一致 [A]。只在 §5.1 报给上游统一源串 | 9·15·16·21 |
| **员工** | `Employee` `:18953`／`Employees` `:19066`／`From Employee` `:21871` | `Employee` **保留 员工**（`Job Card.employee`／`Job Card Time Log.employee`）；`Employees` → 官方在 `workstation.js:351` 用它做分组标题，与单数同义，**保留**；`From Employee` 只在报表筛选，保留。**本组判为不改**——三者都指人，单复数差异不构成歧义 [A] | 19 |

**表后三条附注（都是这一节查出来的独立缺陷，不属撞名但同屏可见）**：

1. **`Dr` → 博士**（`frappe/locale/zh.po:8794`）。这条不是撞名（「博士」只有它一个源词），但它与本节 `Cr` → 贷方 **在同一个渲染点**：`account_tree.js:63` 的 `balance > 0 ? __("Dr") : __("Cr")`，即**科目表树上每个科目右侧的余额方向标记** [A]。现状是余额为正显示「博士」、为负显示「贷方」。官方之所以这样译，是因为这条 msgid 的注释指向 `install_fixtures.py:46` 的称谓表（Mr／Ms／Mx／**Dr**／Mrs），即**官方把"博士"这个称谓和"借方"缩写当成同一个 msgid** ——这是典型的"同一源词多义"，**正是 `context` 该上场的形态**（与撞名相反）。建议：`Dr` 配 context 分两路（称谓保「博士」，会计场景取「借」），或至少让科目树那处不走裸 `__()`。**演示环节 1 建科目表时一眼可见。**
2. **同义组不改，但要报上游**：` BOM`（前导空格）、`Re-open`／`Reopen`（拼法）、`WIP Warehouse`／`Work-in-Progress Warehouse`／`WIP WH`（三种写法两个译名）、`Qty`／`Qty `（尾空格）、`DocType`／`Doctype`／`Document Type`（大小写）——都是官方**源串**层面的不统一，不是译文问题。
3. **计数核对**。SAME-FORM 21 组**全部**至少改一个源词；SAME-FLOW 9 组里 8 组改、`车间仓` 1 组不改；SPLIT 19 组里 14 组改、**5 组不改**（物料清单／结束时间／销售税费模板／重新打开／员工）。合计 **43 组改、6 组不改 = 49**。

#### 2.3.4 口径更正：补扫查出的另 94 组（36 组异义须定，58 组同义／写法变体）

**先认一个我自己的方法失误。** `Spike/P1S3R1-official-po-collisions.py:111-121` 判一个 msgid「是否在演示线上」，用的是 `vis` 集合，而 `vis` 是从 `P1S3R1-demoline-intersect.py` 的输出 `inter["result"].values()` 里攒的——那是 **zelin GENUINE 组的源词**。等于官方 po 的组先被 zelin 的词表筛了一道：源词在演示线上渲染、但从没进过任何 zelin 撞名组的，一律漏掉。

**暴露它的例子**：`付款方式` 组（`Mode Of Payment`／`Mode of Payment`／`Mode of Payments`／`Modes of Payment`／`Payment Method`／`Payment Methods`／`Payment Mode`，7 个源词）被报成 `visible-on-demo=False`，可 `Mode of Payment` 本身就是演示线上的 DocType，§1.1 第 5b 条正是在裁它。

**更正后的口径**（`Spike/P1S3R1-po-demoline-direct.py`，直接从演示线 DocType 的渲染面建集合，不经 zelin）：

| 官方 po 747 组的分布 | 组数 |
|---|---|
| ≥2 个源词在演示线上可见（**本 Stage 该定的**） | **143** |
| 恰 1 个源词可见（另一个源词在线外，用户不会同时见到两个中文相同的标签） | 206 |
| 完全不在演示线上 | 398 |

直接法是初扫的**严格超集**：初扫那 49 组**一组没丢**，另**新增 94 组**。49 组的危害分级（21 SAME-FORM／9 SAME-FLOW／19 SPLIT）与逐组处置照旧有效，不推翻。

**94 组按语义先分两堆**（这个分法是我的判断，不是查出来的事实，见 §四）：

- **58 组同义或纯写法变体——不改**。绝大多数是单复数、大小写、全称／缩写之差：`公司`／`名称`／`描述`／`成本中心`／`条码`／`资产`／`银行`／`工序行ID`／`已开票%`／`单价（本币）`／`金额（本币）`／`税后付款金额(本币)`／`数量(库存单位)`／`时间(分)`／`最小起订量`／`条款和条件`／`拒收数量`／`收货数量`／`待处理数量`／`库存单位`／`物料名称`／`物料需求`／`质检单`／`费用科目`／`默认科目`／`预付金额`／`额外费用`／`汇兑损益`／`打印设置`／`信用额度`／`供应商信息`／`地址和联系方式`／`发票地址`／`子工序`／`工单拆解`／`工单耗用`／`工序顺序号`／`工费成本（本币）`／`已取消`／`已开票金额`／`已预留库存`／`开始时间`／`所需物料`／`框架订单`／`创建多规格物料`／`生成{0}个多规格物料`／`动态定价规则`／`半成品/产成品`／`由供应商交货（直运）`／`竞争对手`／`纳税登记号`／`销售发票`／`销售订单`／`销售订单明细`／`需要检验`／`RGT`／`临时冻结原因`／`采购税费模板`，加一个边界的 `参考`（见下表）。
- **36 组异义须定**，逐组处置如下。

表读法同 §2.3.1：**保留**＝沿用官方现译；**→ X** ＝该源词改用 X（X 均已核占用，未被别的 msgid 占）。

| 目标词 | 源词与渲染处 | 处置 | 换词理由 | 演示环节 |
|---|---|---|---|---|
| **科目** | `Account` GL Entry.account／`Account Head` 税费子表.account_head | `Account` 保留；`Account Head` **→ 税目科目**（FREE） | 税费子表里那一列指的是"这条税走哪个科目"，与凭证行的科目不是一个层级。同屏（采购发票主表有税费子表） | 环节 10、12 |
| **总计** | `Grand Total`／`Total`／`Totals` — 三个**同时**出现在送货单与采购发票 | `Grand Total` 保留；`Total` **→ 合计**；`Totals` **→ 合计栏** | 三个中文全叫「总计」，用户分不清哪个是含税总额。`Grand Total` 是含税总额，`Total` 是不含税小计，`Totals` 是分节标题 | 环节 10、12、22 |
| **退货** | `Is Return` 送货单+采购入库+库存凭证／`Return` 送货单+采购发票 status 选项 | `Is Return` **→ 是否退货**；`Return` 保留 | 同屏：勾选框与状态值都叫「退货」。勾选框是布尔，按本文档 §2.3.1 的布尔命名法加「是否」 | 环节 23（如演退货）；否则只在字段面上 |
| **默认** | `Default` bom_list.js:7+Sales Invoice Payment.default／`Defaults` 客户+物料组+库存设置／`Is Default` BOM | `Default` 保留；`Defaults` **→ 默认值**；`Is Default` **→ 是否默认** | 物料清单列表里「默认」标记与 BOM 的 `is_default` 勾选同屏出现 | 环节 7（建物料清单） |
| **发料仓** | `From Warehouse`／`Set From Warehouse`／`Set Source Warehouse`／`Source Warehouse` | `Source Warehouse` 保留；`From Warehouse` **→ 调出仓**；`Set From Warehouse` **→ 批量调出仓**；`Set Source Warehouse` **→ 批量发料仓**（**不能用「默认发料仓」——已被 `Default Source Warehouse` `:16249` 占** [A]） | 四个源词全译「发料仓」，其中两个 `Set …` 是**主表上给子表行批量赋值的**字段，与子表每行的仓库同屏并列 | 环节 18、19（工单发料、库存凭证） |
| **收料仓** | `Set Target Warehouse`／`Target Warehouse` | `Target Warehouse` 保留；`Set Target Warehouse` **→ 批量收料仓**（**不能用「默认收料仓」——已被 `Default Target Warehouse` `:16276` 占** [A]） | 同上，主表批量赋值字段与子表行字段同屏 | 环节 18、19 |
| **可用数量** | `Available` workstation.js:513／`Available Qty`／`Available Quantity`／`Projected Qty` Bin／`Stock Projected Qty` item.js:174 | `Available Qty`+`Available Quantity` 同义保留；`Available` **→ 工位可用**；`Projected Qty` **→ 预计可用量**；`Stock Projected Qty` **→ 预计可用量** | `Projected` 是"现存＋在途−已占用"的**预测**量，与"当前可用"是两个数，摆在一起用户会以为是同一个 | 环节 6（工位）、环节 11（查库存） |
| **已付款** | `Is Paid` 采购发票.is_paid／`Paid` 采购发票+销售发票 status 选项 | `Is Paid` **→ 是否已付**；`Paid` 按 §1.1 第 2 条走方案丙（销→已收款／采→已付款） | 同屏：勾选框与状态值都叫「已付款」。且 `Paid` 已被 §1.1 裁为方向词，此处只把勾选框让开 | 环节 13、23 |
| **已发料数量** | `Supplied Qty` 采购订单委外明细／`Transferred Qty` 工时卡明细+库存凭证明细+工单明细 | `Supplied Qty` **→ 已供料数量**；`Transferred Qty` **→ 已调拨数量** | 两个都改。委外的"供给供应商"与工单的"调进车间仓"是两件事，共用「已发料数量」会让人以为委外料和工单料是同一笔 | 环节 18、19 |
| **总完工数量** | `Total Completed Qty` 工时卡／`Total Produced Qty` 生产计划 | `Total Completed Qty` **→ 工序总完工数量**；`Total Produced Qty` **→ 计划完工数量** | 工时卡统的是**该工序**报工累计，生产计划统的是**整单**产出。演示里两个数不相等，同名会被当成对不上账 | 环节 16、20 |
| **委外原材料** | `Consumed Items` 采购入库／`Material to Supplier` po.js:394／`Supplied Items` 采购发票+采购订单 | `Supplied Items` 保留；`Consumed Items` **→ 供应商已耗用**；`Material to Supplier` **→ 发往供应商物料** | 三处分别是"发出去的""供应商用掉的""结算用的"，同名会让用户分不清哪个数该对 | 环节 8–10（若演委外） |
| **生产任务单** | `For Job Card` 工时卡.for_job_card／`Job Card`／`Job Cards` — **工时卡表单上两个都在** | `Job Card`+`Job Cards` 同义保留；`For Job Card` **→ 所属生产任务单** | 同屏：工时卡上有个指向另一张工时卡的 Link 字段，与自身单据名同名 | 环节 16、17 |
| **源单据类型** | `Reference DocType` payment_entry.js:1727／`Reference Type` 采购发票预付款+销售发票预付款子表 | `Reference DocType` 保留；`Reference Type` **→ 源单类型** | 收付款单主表与其预付款子表同屏，两列都叫「源单据类型」 | 环节 13、23 |
| **折扣金额** | `Discount Amount` 各明细行／`Discounted Amount` 付款计划 | `Discount Amount` 保留；`Discounted Amount` **→ 折后金额** | `Discounted Amount` 是**打折后的应付额**，不是折扣额本身，现译方向反了。付款计划子表与主表明细同屏 | 环节 10、22 |
| **预付款** | `Advance Paid` 销售订单／`Advance Payment` list.js／`Advance Payments` 公司+采购发票+销售发票 | `Advance Paid` **→ 已预收款**（销售侧）；`Advance Payment` 保留；`Advance Payments` **→ 预收/预付款** | `Advance Paid` 在销售订单上指客户已预付给我们的钱，中文说「预付款」会被理解成我们付出去的。分节标题那条用中性词 | 环节 15、23 |
| **找零** | `Change Amount` 销售发票.change_amount／`Changes` 销售发票.section_break_88 — 同一张表单 | `Change Amount` **→ 找零金额**；`Changes` 保留（「找零」现被 `Changes` `frappe:4743` 与 `Change Amount` `:10432` 共占，让开后归 `Changes`） | 同屏一个分节标题和一个金额字段同名。金额字段带「金额」二字更明确 | 环节 23（现金收款时） |
| **退款** | `Credit Note` dn.js:89+库存凭证.credit_note／`Issue Credit Note` 送货单 | `Credit Note` **→ 红字发票**；`Issue Credit Note` **→ 开红字发票** | 两个都改。`Credit Note` 是**红字发票／贷记通知单**，不是退款（钱退不退是另一回事）。中国开票语境下「红字发票」是标准说法 | 环节 23（如演退货） |
| **临时冻结** | `Hold` po.js:338+so.js:995／`On Hold` 工时卡+采购订单 status／`Temporarily on Hold` pi_list.js:29 | `On Hold` 保留；`Hold` **→ 暂挂**；`Temporarily on Hold` **→ 已暂挂** | 按钮（动作）与状态值（状态）必须区分，同名时用户不知道按钮是"设为冻结"还是"查看冻结" | 环节 9、15 |
| **冻结发票** | `Block Invoice` pi.js:109,269／`Hold Invoice` 采购发票.on_hold | `Block Invoice` 保留；`Hold Invoice` **→ 暂挂发票** | 同一张采购发票上，按钮与勾选框同名。两者在 ERPNext 里确实是一套机制的两个入口，但按钮是动作、字段是状态 | 环节 12 |
| **失效日期** | `End of Life` 物料／`Expiry Date`／`Valid Till` 报价单 | `Expiry Date` 保留；`End of Life` **→ 停用日期**；`Valid Till` **→ 报价有效期** | 三件事：物料停产日、批次过期日、报价有效期。演示里报价单与物料卡都要开，同名会让人以为报价也会"过期失效" | 环节 5、14 |
| **到期日** | `Due Date` GL Entry+收付款单参照／`Expires On` frappe／`Expiry` 库存设置.pick_serial_and_batch_based_on | `Due Date` 保留；`Expires On` **→ 失效于**；`Expiry` **→ 失效期优先** | `Expiry` 是库存设置里**拣货排序策略**的一个选项值（按失效期先出），译「到期日」完全不成句 | 环节 3、10 |
| **备注** | `Note` item.js:751+物料价格.note／`Notes`／`Remark`／`Remarks` GL Entry+工时卡+收付款单 | `Remarks` 保留 **备注**；`Note`+`Notes` **→ 备注说明**；`Remark` 与 `Remarks` 同义**保留** | `Note`/`Notes` 是给人看的说明性长文本，`Remark(s)` 是凭证摘要栏。凭证上那栏是财务要认的，留「备注」 | 环节 5、10、19 |
| **序列号与批号** | `Serial & Batch Item`／`Serial and Batch`／`Serial and Batch Bundle`／`Serial and Batch No` | `Serial and Batch No` 保留；`Serial & Batch Item` **→ 序列批次物料**；`Serial and Batch` **→ 序列批次设置**；`Serial and Batch Bundle` **→ 序列批次包** | Bundle 是 v16 新引入的**一张单据**（批号序列号的集合凭证），与字段同名会让人找不到那张单 | 环节 5、9、19 |
| **取消预留** | `Stock Unreservation`／`Unreserve`／`Unreserve Stock` | `Unreserve` 保留（按钮）；`Unreserve Stock` **→ 取消库存预留**；`Stock Unreservation` **→ 解除预留** | 三处一按钮、一动作名、一记录类型。演示若开库存预留会同屏出现 | 环节 15、21（若开预留） |
| **套件明细** | `Bundle Items` 报价单／`Packed Item`／`Packed Items` 送货单+销售发票+销售订单 | `Packed Items` 保留；`Packed Item` 与之同义**保留**；`Bundle Items` **→ 组合套件明细** | **报价单上两个都在**（`Bundle Items` 与 `Packed Items` 同屏）。`Bundle` 指产品组合的定义，`Packed` 指实发的拆解行 | 环节 14、21、23 |
| **委外** | `Is Subcontracted`／`Sub-contracting`／`Subcontract`／`Subcontracting` | `Subcontracting` 保留；`Subcontract`+`Sub-contracting` 同义**保留**；`Is Subcontracted` **→ 是否委外** | 只需把勾选框让开（采购订单上勾选框与分节标题同屏）。三个名词形态属同义写法差 | 环节 8（若演委外） |
| **工时表** | `Time Sheet`／`Time Sheets`／`Timesheet`／`Timesheets`（4 个，**销售发票上有两个**） | `Timesheet` 保留 **工时单**（改词见理由）；其余三个 → **工时单**／**工时单列表** 按单复数分 | 官方源串四种写法译出两个中文。**更要紧的是「工时表」这个译名本身偏"报表"**，而 `Timesheet` 在 ERPNext 里是一张**单据**（工时卡汇总成的计费单）。全族统一为「工时单」，与 `Job Card` → 生产任务单 同系 | 环节 19、23 |
| **选工时单** | `Fetch Timesheet` si.js:305／`Get Timesheets` si.js:357 — **同一张销售发票上两个按钮** | `Get Timesheets` 保留；`Fetch Timesheet` **→ 取工时单** | 同屏两个按钮中文完全一样，用户不知道该按哪个。`Fetch` 是取单行、`Get` 是批量拉 | 环节 23 |
| **日记账凭证** | `Journal Entries`／`Journal Entry` accounts_settings.js:58／`Journals` 会计设置.journals_section | `Journal Entry`+`Journal Entries` **保留 日记账凭证**（单复数同义）；`Journals` **→ 日记账** | 会计设置一屏上分节标题与按钮同名。分节标题指的是"日记账这一类"，不是某张凭证 | 环节 11、12 |
| **模板物料** | `Template Item` bom.js:457／`Variant Of` 物料.variant_of | `Template Item` 保留；`Variant Of` **→ 派生自** | `Variant Of` 是**指向父模板的 Link**，语义是"这件是谁的变体"，译「模板物料」把方向说反了 | 环节 5（若演多规格） |
| **物料需求明细** | `Material Request Item`／`material_request_item`（小写，是 fieldname 被当串译了） | `Material Request Item` 保留；小写那条 **→ 物料需求行** | 小写那条是官方误把 fieldname 收成了可译串，本不该露出来。不撞的办法是让它与正名不同 | 环节 16（若经物料需求） |
| **额外物料调拨** | `Additional Material Transfer` work_order.js:838／`Extra Material Transfer` 生产设置 | `Extra Material Transfer` 保留；`Additional Material Transfer` **→ 超领调拨** | 一个是生产设置里的**策略开关**，一个是工单上的**动作按钮**。按钮改为「超领调拨」正好说清它干什么（超出 BOM 用量再领） | 环节 18 |
| **业务伙伴** | `Referral Sales Partner` 报价单.referral_sales_partner／`Sales Partner` | `Sales Partner` **→ 销售伙伴**；`Referral Sales Partner` **→ 推荐销售伙伴** | 两个都改。「业务伙伴」在中文 ERP 里通常指客户+供应商的统称（SAP 的 Business Partner），拿来译 Sales Partner 会误导；且两者同屏 | 环节 14 |
| **参考** | `Reference` BOM.reference_section／`References` 客户.references_section | 两者**同义，均保留**（边界情形） | 都是分节标题、都在不同 DocType 上、单复数之差。列在这里是因为机械扫会把它判成撞名，**人工判为不改** | 环节 7、14 |
| **这是不能被编辑的树形结构的根结点。** | `This is a root account…` 等 **6 条**（account／department／item group／sales person／supplier group／territory） | **全部保留** | 官方把六句合译成一句通用话，是**有意的合并**，句子本身通顺且六处语义相同。不是缺陷 | 环节 1（点科目表根节点时） |
| **使用公司默认小数精度尾差成本中心** | `Use Company Default Round Off Cost Center` `:59670`（采购发票）／`Use Company default Cost Center for Round off` `:59676`（销售发票） | **均保留** | 官方**同一概念写了两种英文**（一个在 PI、一个在 SI），译文相同是对的。列在此处是因为机械扫判它撞名，**人工判为不改**；真正该修的是上游源串不统一 | 环节 10、22 |

**表后三点：**

1. **本节 36 组里实际要改源词的是 30 组**，另 6 组（`参考`／`这是不能被编辑的树形结构的根结点。`／`使用公司默认小数精度尾差成本中心`／`员工`类的单复数同义，即表中标「均保留」的行）判为不改。
2. **`工时表` → `工时单` 这一条不是撞名修复，是纠译名**。它顺带解决了四写法撞一词的问题，但主因是 `Timesheet` 是单据不是报表。归在此表是因为撞名扫描把它捞出来了，**落地时要与 §2.3.3 附注 1 的 `Dr` 一样，单列为"顺带发现的译名缺陷"**。
3. **全 Stage 计数合并**：初扫 49 组里 **43 改／6 不改**；补扫 94 组里 **30 改／64 不改**（36 组异义中 30 改 6 不改，加 58 组同义全不改）。**演示线上 143 组，合计 73 组要改源词用词、70 组不改。**

### 2.4 落在演示线外、本 Stage 不处理的（只给计数与抽样，不逐组列）

**依据**：Stage 概况执行边界 §1「不要在本 Stage 试图定全部术语——914 组撞名里绝大多数不在演示线上」[B `P1-S3-概况.md:34`]。

官方 po 747 组里，**604 组本 Stage 不定**，分两类：

#### 2.4.1 恰 1 个源词在演示线上可见 — 206 组

这类**撞名成立但演示当场感觉不到**：另一个源词在演示线外渲染，用户不会在同一次走查里见到两个中文相同的标签。

| 分布 | 全部 206 组都是「演示线上 1 个可见 + 线外 ≥1 个」 |
|---|---|
| 抽样（10 组） | `月` ← Month／**Months**；`电子邮件` ← **Email ID**／Emails／email；`项目` ← **Project**／Projects；`标题` ← Heading／**Title**／title；`激活` ← Activate／**Active**；`图片` ← **Image**／Images；`国家` ← **Country**／Your Country；`物料` ← ` Item`／For Item／**Items**／Items Catalogue／Material；`默认预付账款科目` ← Default Advance Account／**Default Advance Paid Account**；`积分兑换` ← **Loyalty Points Redemption**／Redemption／Loyalty Point Entry Redemption（加粗＝演示线上可见的那个） |

抽样看下来，这批**绝大多数是单复数或大小写差**，本身多半连"该改"都不成立。**唤醒条件**：若后续把演示线扩到这些源词的渲染面（如开项目模块、开积分），该组即升级进 §2.3。

#### 2.4.2 完全不在演示线上 — 398 组

| 源词数 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|
| 组数 | 340 | 45 | 11 | 1 | 1 |

涉及 msgid **870** 个。源词最多的几组（**全部在演示线外**，列出来只为说明形态，不是要定）：`分钟` ← 6 个（In Minutes／In mins／In minutes／Minute／Time in mins／Time in mins.）；`目标` ← For／Goal／Objectives／Target／Targets；`取消` ← Cancel／cancel／canceled／on_cancel；`女士` ← Madam／Miss／Mrs／Ms；`完成日期`／`差异`／`标签`／`无数据`／`角色`／`成功`／`选择单据类型`／`选择字段` 各 4 个。

**形态判读**：这 398 组里大量是 frappe 平台层的界面词（`on_cancel` 这种连 fieldname／hook 名都被收成可译串）、称谓（`女士` 那组）、和纯写法变体。**真正会咬业务的极少**，与执行边界 §1 的判断一致。

**不定的理由写清**：本 Stage 只对"演示当场会被看到"的撞名负责（完成标志第 1 条限定为"**演示线涉及的那批**"[B `P1-S3-概况.md:26`]）。这 604 组不登记为延迟需求——它们不是"待办事项"，而是**上游官方译文的既有状态**；哪天演示线扩了，按 §2.2 的脚本重跑一次即可重新筛。

## 三、不属本表的（明确划出去）

以下四类形态上像"同名"，但**不是撞名、也不由术语标准解决**。划出来是为了让 B 步改文件时不误改，也为了让后续 Stage 知道该在哪接手。

### 3.1 中国科目表的同名父子结构 → S4 处理

| 项 | 内容 |
|---|---|
| **形态** | 同一张科目表里父科目与子科目**中文名完全相同**，只差科目号前缀：`应收账款`(11220，group) > `应收账款`(11221，可记账) [B `P1-S3-概况.md:89`] |
| **规模** | zelin 4 张科目表里 3 张有此问题，**一般企业2024 有 13 处** [B 同上] |
| **症状** | 科目下拉里两个「应收账款」，选错了记不进账（group 不能记账） |
| **为什么不进本表** | **它与翻译无关**——两个中文名不是译出来的，是科目表 json 里的**数据**。改译名一个字也解决不了。它是科目表设计问题 |
| **归谁** | **S4**（S2 移交事实 3 已定此归属 [B `P1-S3-概况.md:89`]） |

### 3.2 行业术语（弹簧车间的叫法）→ 实地考察后

执行边界 §1 限死：「行业术语留到实地考察后」[B `P1-S3-概况.md:34`]。IM-003 摸底问点清单第①类正是去问五个管理侧环节（接单／排产／领料／入库／发货）的**车间叫法** [B `P1-S3-概况.md:72`]。**现场问回来的用词回流 CR-001** [B `P1-S3-概况.md:21`]，那是下一轮的事，本轮不猜。

### 3.3 frappe 平台内部的撞名（不在演示渲染面上）

典型是 `已提交` ← `Committed`／`Submitted`／`submitted`。S1 已把 `Committed` → 已提交 记为**确定译错**（库存语境下 Committed Qty 是"已占用/已承诺数量"，与单据的 Submitted 是两回事）[B `P1-S2-R1-A参考项目-zelin-翻译.md:177`]。

**但本 Stage 不定它**：核实过 `Committed` 在官方 po 里的渲染面不在演示线的 38 个 DocType 上（`Bin.indented_qty` 一族走的是另外的词），演示走查见不到。**登记为"已知上游译错、不在演示线"**，若 S6 做译名改造时顺手，可一并修。

### 3.4 工作区／侧边栏标签的同名 → S6 的 CR-002

`Setup`／`Settings` 都译「设置」这类，咬人的地方是**侧边栏两个分节同名** [B `P1-S2-R1-A参考项目-zelin-翻译.md:13`]。这类的解法有两条路：改译名（本表管），或**改工作区 label**（`boot.py:465` 是 `_(item.label)`，label 保持英文由 csv 去译 [B `P1-S3-概况.md:90`]）。

**本表只管前一条**：给源词定目标侧用词。**哪些入口要改 label、改成什么，是 S6 的 CR-002**（本表是它的硬前置）。

## 四、我的推断（无来源支撑）

本节把**判断**从**事实**里摘出来。上面表里凡带 [A] 的都是源码/官方 po 实证；本节这些没有任何来源能证，**全是我拍的**，须用户复核。

| # | 推断 | 它支撑了上面哪一处 | 为什么没来源 |
|---|---|---|---|
| 1 | **「哪个源词保留、哪个换掉」的每一次取舍** | §2.3.1–2.3.4 全部 73 组的处置列 | 没有任何客观判据说"应该 `Debit` 留、`Debit Amount` 改"。我的取法是：**渲染面窄的那个改，宽的那个留**（改动面小），以及**语义更泛的那个留**。这条取法本身也是我定的 |
| 2 | **每个新词的具体用字** | 所有 **→ X** 的 X | 「批量发料仓」「超领调拨」「派生自」这些是我造的词。我只证了**没被别的 msgid 占**（脚本查官方 po 反向索引），**没证它们符合中国制造业习惯说法**。这是最该找懂行的人过一遍的 |
| 3 | **异义 vs 同义的分类** | §2.3.3 的 14 改/5 不改、§2.3.4 的 36 异义/58 同义 | 判"`Qty` 与 `Quantity` 是同义、`Debit` 与 `Debit Amount` 是异义"靠的是我读源码后的理解。**94 组里 36/58 这个切分尤其软**——我是逐组看源词拼写和渲染点判的，没有第二个人复核 |
| 4 | **平条目兜底词 未结 / 已付讫** | §1.2 末（`Unpaid`/`Paid` 在四处无法按 context 二分的渲染点） | 「未结」「已付讫」是我为"既不能说收、也不能说付"的场合造的中性词。**核实过没被占**，但没有任何先例证明中国会计能接受它们作发票状态值 |
| 5 | **环节归属是约数** | 所有表最后一列的「环节 N」 | 我按 `最小闭环操作稿.md` 的 23 环节标题+步骤推的哪一屏会开哪个 DocType，**没在跑起来的实例上逐屏确认**。带"若演委外""若演退货"字样的行，取决于演示脚本最终演不演那段 |
| 6 | **危害分级的 SAME-FORM 判据** | §2.3.1 的 21 组定为最高危 | 判据是"两个源词都在同一 DocType 或其子表的渲染面上"（`Spike/P1S3R1-cooccurrence.py:104-116`）。**但"在同一 DocType 上"不等于"同时可见"**——字段可能在不同页签、或被 `depends_on` 隐藏。我没逐个查 `depends_on`，故 SAME-FORM 这 21 组里可能有几组实际不同屏 |
| 7 | **`Timesheet` 全族改「工时单」** | §2.3.4 `工时表` 行 | 「工时表」偏报表、`Timesheet` 是单据——这个判断我有信心；但**统一用「工时单」是否与 `Job Card` → 生产任务单 真的成系**，是我的语感，没有依据 |
| 8 | **`工时表`／`Dr` 两条归类为"顺带发现的译名缺陷"** | §2.3.3 附注 1、§2.3.4 附注 2 | 它们不是撞名（`Dr` 只有一个源词），严格说**超出 CR-001 被图谱限死的范围**（执行边界 §1）。我判"既然查到了就该报"，但**要不要在本 Stage 落地，是用户裁决**，不是我能定的 |

## 五、复核建议

### 5.1 最需要复核的

| # | 项 | 为什么最要紧 |
|---|---|---|
| 1 | **我自己的方法失误：49 → 143** | `Spike/P1S3R1-official-po-collisions.py:111-121` 把「在演示线上」错判成「在 zelin 撞名组的源词里」，漏了 94 组。**已用 `P1S3R1-po-demoline-direct.py` 补扫更正**，但这说明我的筛法链条上曾有一环靠不住。**若还有第三种漏法，143 也可能偏小**——建议独立重算一次 |
| 2 | **`Unpaid`／`Paid` 有四处落不了地** | §1.2 列的四处（列表徽标裸 `__(doc.status)`；销售发票 `status` 因 `read_only`=1 走裸 formatter，而采购发票不是——**销采不对称**；标准筛选器不传 doctype；四张共享子表 `df.parent` = 子表名）。这意味着**方案丙在演示的某些屏上必然露中性词**。要用户确认能不能接受，或愿不愿改上游 |
| 3 | **平条目兜底词 未结／已付讫** | 上一条的直接后果。这两个词是我造的（§四 #4），**中国会计认不认，我不知道** |
| 4 | **73 个新词的用字** | §四 #2。全部只证了"没被占"，**没证"是行业习惯说法"** |
| 5 | **`Dr` → 博士** | `frappe/locale/zh.po:8794`。**科目表树上余额为正的科目现在显示「博士」**（`account_tree.js:63` 的 `balance > 0 ? __("Dr") : __("Cr")`）。演示环节 1 一眼可见。这是"同源词多义"，`context` 正好能解，与撞名相反 |
| 6 | **要报上游的源串不统一** | ` BOM`（前导空格）／`Qty `（尾空格）／`Re-open`·`Reopen`／`DocType`·`Doctype`·`Document Type`／`Use Company Default Round Off Cost Center` 与 `Use Company default Cost Center for Round off`／`material_request_item`（fieldname 被收成可译串）。**这些改译文治不好，得改官方源串** |

### 5.2 拿不准的

1. **几个只在报表里渲染的源词我没定**：`Costing Rate`（→ 成本价）、`Tax Masters`（→ 税）、`Ongoing`（→ 进行中）。它们不在 38 个演示 DocType 的表单面上，但**报表若在演示里打开就会露**。演示脚本到底开不开哪几张报表，我按 23 环节判是不开，**不确定**。
2. **演示线 DocType 的取法可能过收**：`Stock Settings`／`Accounts Settings`／`Manufacturing Settings` 这三张我算进了演示线（环节 3 要配它们），但演示实际只碰其中几个字段。**它们的字段面很宽**，把整张表算进渲染面会多捞一些撞名。多捞比漏捞安全，但**§2.3 的 143 里有一部分可能是这样进来的**。
3. **SAME-FORM 21 组里可能有几组实际不同屏**（§四 #6，`depends_on` 与页签未查）。
4. **§2.3.4 那 58 组"同义不改"是否全都真无害**。我是按拼写形态批量判的，**没逐组看渲染点**。若其中某组其实是异义，就会漏一个该改的。
5. **`Accounts Receivable`／`Debtors` 这条我的解法**：判定"真正咬人的是 `Receivable`（科目类别选项）与 `Debtors`（科目名）在建科目那一屏同显应收账款，改前者即解"。这依赖"`Accounts Receivable` 只在按钮上出现"的判断，**若科目表数据里还有个叫这名的科目，解法就不够**。

### 5.3 明确没查到的

1. **914 这个数我复算不出来**。同样的 zelin `zh.csv`、同样的判据（同一目标词 ≥2 源词），我得 **917**；去首尾空白后 **910**；再统一小写后 **823**。差异来自空白与大小写的归并口径。S2 那份文档没写它的归并法 [B `P1-S2-R1-A参考项目-zelin-翻译.md:93`]。**本文档一律用官方 po 那套 747/143，不用 914**，但这个对不上的事实不掩盖。
2. **没有在跑起来的 v16 实例上目视确认任何一组撞名**。全部结论来自读 json/js/po 文件。**"同屏"是静态推断**，不是看见的。
3. **`hrms` 没算进来**。本 bench 的 `sites/apps.txt` 只有 `frappe`+`erpnext`，所以 hrms 不装、不生效。但若演示后要上工资/考勤，`hrms/locale/zh.po` 会引入新的一批撞名，**没扫**。
4. **没查 Property Setter 与 Translation DocType 里的既有覆盖**。若这个 bench 的站点数据库里已有人手工加过 `Translation` 记录，实际生效的译文可能与 po 文件不同。**我只读文件，没读数据库**。
5. **`Reference/saoxia` 那份完全没碰**（S2 已判两份第三方仓均不可作基线 [B `P1-S3-概况.md:88`]，本表只把 zelin 当词汇素材）。
