# R12 SB FD-009：27 个出处没记全的无 context 覆盖键，逐条判

来源：`Spike/P1S6R4-baseline.py` 新加的 `source_index`／`hidden_refs`（`baseline.json` 的 `official_overrides[].hidden_refs`），列表见 `hidden.txt`。判据：未记出处处的语义是否与覆盖译文相符。

| 键 | 覆盖 | 未记出处（取要） | 判定 | 处置 |
|---|---|---|---|---|
| `Accounting Ledger` | 会计账簿 | hrms 报销单「会计账簿」按钮 | 同义（总账跳转按钮） | 不改 |
| `Bot` | 机器人 | Raven 用户列表、私信头、悬停卡片的徽标 | 同义 | 不改 |
| `Create Quotation` | 创建报价单 | CRM 商机页动作 | 同义 | 不改 |
| `Dr` | 借方 | `account_tree.js:63`、`bank_clearance.py:84`、银行对账网格 | 同义（会计借方）；称呼义的代价已登记（LG-011、FD-030） | 不改 |
| `Due Date` | 到期日期 | 总账、日记账等 16 处字段 | 同义 | 不改 |
| `Hold` | 暂挂 | hrms 应聘者状态 | 可用（「暂挂」应聘） | 不改 |
| `Is Paid` | 是否已付 | hrms 报销单字段 | 同义 | 不改 |
| **`Item Type`** | 物料类别 | **`navbar_item.json` 条目类型列（Route／Action／Separator）** | **误伤** | **写 `Item Type,条目类型,Navbar Item`**（用户 2026-10-14 定） |
| **`Ledger`** | 会计账簿 | 日记账／收付款／期末结账凭证的总账按钮（同义）；**打印设置 PDF 纸张尺寸选项（`print_settings.py:56`，432×279mm 纸型）** | **纸型处误伤** | **写 `Ledger,账簿纸,Print Settings`**（用户 2026-10-14 定） |
| `Master` | 少爷 | 工位看板分组 | 误伤 | 已由 FD-002 看板覆盖处置 |
| `Mode Of Payment`／`Mode of Payment` | 收付款方式 | hrms 工资单、员工借款、报销单 | 同义 | 不改 |
| `Note`／`Notes` | 备注说明 | Raven 提醒、询价单、CRM 备注、应聘者等 | 同义 | 不改 |
| `Outstanding Amount` | 未结金额 | hrms 两张报表列 | 同义 | 不改 |
| `Payment` | 收付款 | hrms 报销单、员工借款、休假折现按钮 | 可用（统称） | 不改 |
| `Payment Entry Reference` | 核销明细 | 收付款凭证引用类型选项；hrms 报销借款子表隐藏字段 | 同义；后者 `hidden=1` 不显示 | 不改 |
| `Process Payment Reconciliation` | 收付款核销任务 | Link 选项（DocType 名） | 同义 | 不改 |
| `Receivable` | 应收类 | hrms 员工借款「科目类型须为 {1}」报错 | 同义（科目类型） | 不改 |
| `Sales Invoice Timesheet`／`Timesheet`／`Time Sheet`／`Timesheet Detail` | 工时单族 | Link 选项、报表列、hrms 侧栏 | 同义（DEC-016 全族） | 不改 |
| `Sales Partner` | 销售伙伴 | Link 选项 | 同义 | 不改 |
| `Serial and Batch Bundle` | 序列批次包 | Link 选项 | 同义 | 不改 |
| `Setup` | 基础设置 | 各侧栏「Setup」分节 25 处；工位状态选项 1 处 | 分节同义；工位状态已有 `Setup:Workstation` 调机行（DEC-019），列表徽标不带 context 已登记 `SH-P1S6004` | 不改 |
| `old_parent` | 原上级 | 各树形 DocType 隐藏字段 | 同义 | 不改 |
| **`Credit Note`／`Debit Note`** | 红字发票／采购红字发票 | **日记账「凭证类型」选项**（main.pot 有记，报告点名） | 会计判断 | **登记延迟** `SH-P1S6007`（用户 2026-10-14 定，待会计确认） |
