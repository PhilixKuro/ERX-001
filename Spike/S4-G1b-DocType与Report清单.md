# S4-G1b 清点：zelin `erpnext_china/erpnext_china/` 的 DocType 与 Report

调查对象：`D:\ERX-001\Reference\zelin-tech-erpnext_china\erpnext_china\erpnext_china\`
范围：`doctype/`(35) + `report/`(13) + `workspace/`(1) + `__init__.py`(1) = 50 文件
调查方式：只读。未建 app、未跑 bench、未动站点、未做 git 操作。
核对基准：`D:\ERX-001\frappe-bench\apps\frappe`(16.34.0) / `apps\erpnext`(16.35.0)，站点 `erx.localhost` db_type=mariadb。

---

## 0. 先更正三处「已知」

### 0.1 本目录里**没有** CRM／线索／企微／按钮权限的东西

任务书说「其余的是 CRM／线索／企微／按钮权限一类，那些判不抄」。**核实为不成立**：本目录 50 个文件**全部**是财税相关。

`find . -type f` 实测只有 8 个 DocType 目录 + 3 个 Report 目录 + 1 个 workspace。8 个 DocType 恰好就是任务书列的那 8 个。CRM/企微那批不在本目录（应在 G1a／G1c 范围的 `fixtures/`／`setup/`／顶层散文件内）。**本批无「不抄」的类别合并行，也无一个「不抄」判定。**

### 0.2 `report/` 的 13 是「文件数」不是「报表数」

任务书要我「报其余 10 张是什么」——**没有其余 10 张**。13 = 3 个 Report × 4 文件（`__init__.py`／`.js`／`.json`／`.py`）+ `report/__init__.py` 1 个。

3 张报表全是 `report_type: "Script Report"`，**不是** `Custom Report`；`.json` 里的 `columns`／`filters` 都是空数组 `[]`（Script Report 的正常形态，列与筛选在 `.py`／`.js` 里定义），**三个 `.json` 都没有 `query` 字段也没有 `javascript` 字段**。所以「`query` 长度 0 ⇒ 有壳无实」这个判据在此不适用。三张都是真实现，详见 §3。

### 0.3 「资产负债表两个 Settings 无准则维度」正确，但**BS Settings 有三个字段不是纯 items**

`balance_sheet_settings.json` 的 `field_order` 是 `asset_row`／`liability_row`／`equity_row`／`items`——**前三个 Int 字段是「合计行行号」**，报表 `get_report_summary()` 靠它们定位总资产/总负债/总权益行。抄的时候不能只当成「一个 items 子表」。PL Settings 则确实只有 `items` 一项。

---

## 1. 清点表

### 1.1 现金流量表四件套

| 文件路径 | 类型 | 行数 | 判定 | 目标落点 | 抄后要改什么 | 依据 |
|---|---|---|---|---|---|---|
| `doctype/cash_flow/cash_flow.json` | DocType 定义 | 157 | 抄后改 | `erx_core/cn_tax/doctype/cash_flow/cash_flow.json` | `module` 改 `CN Tax`；`autoname: format:{company}_{fiscal_year}_{month}` 用公司全名拼 name，中文公司名会很长，待评估是否换 abbr | 已核实 `:100 "is_submittable": 1`、`:104 "module": "ERPNext China"` |
| `doctype/cash_flow/cash_flow.py` | 业务逻辑 | 230 | 抄后改 | 同上 | ① `:9` 依赖 `erpnext...trial_balance.get_rootwise_opening_balances`，**v16 存在但签名要注意**（§4）② `:101` 过滤键大写 `"Company"`（§5-A）③ 依赖 `Account`/`Customer`/`Supplier` 上的 `cash_flow_code` 自定义字段，**该字段由 G1a 范围的 `fixtures/custom_field.json` 提供**（§2）④ `:7 Cast_` 在 v16 存在 | 已核实：从 GL Entry 取数 `:148-175` |
| `doctype/cash_flow/cash_flow.js` | 表单脚本 | 78 | 抄后改 | 同上 | `:78 frappe.tools.downloadify` v16 存在（`frappe/public/js/frappe/utils/tools.js:8`）；`:24 erpnext.utils.get_fiscal_year` 依赖 erpnext bundle，并入式下**本项目装了 erpnext 故可用** | 已核实 |
| `doctype/cash_flow/test_cash_flow.py` | 测试 | 9 | 抄后改 | 同上 | `:5 from frappe.tests.utils import FrappeTestCase` —— v16 仍可 import 但**已标记废弃**，应改 `IntegrationTestCase`（§4） | 已核实 |
| `doctype/cash_flow_code/cash_flow_code.json` | 主数据 DocType | 105 | 抄后改 | `.../doctype/cash_flow_code/` | `module`。`autoname: field:code`；`cash_flow_type` 的 5 个中文选项（一～五大类）与 `formula` 的 3 个值（`type_subtotal`/`last_period_balance`/`above_subtotal`）是报表小计逻辑的契约，改名即破 | 已核实 `:5`、`:43`、`:53` |
| `doctype/cash_flow_code/cash_flow_code.py` | 空壳 | 8 | 抄 | 同上 | 仅 `pass` | 已核实 |
| `doctype/cash_flow_code/cash_flow_code.js` | 空壳 | 8 | 抄（或删） | 同上 | 全文只有被注释掉的 refresh，**实际是空文件** | 已核实 |
| `doctype/cash_flow_code/test_cash_flow_code.py` | 测试 | 9 | 抄后改 | 同上 | 同 `FrappeTestCase` | 已核实 |
| `doctype/cash_flow_item/cash_flow_item.json` | 子表 | 200 | 抄后改 | `.../doctype/cash_flow_item/` | ① `module` ② **`:79`/`:96` `read_only_depends_on` 写成 `"evel:doc.manual_split === 0"`（`evel` 拼错），该只读控制失效**（§5-B）③ `:157 voucher_type` 选项含 `Expense Claim`/`Payroll Entry`/`Employee Advance`/`Fees`/`Full and Final Statement`/`Loan` 等 **hrms/lending 凭证类型，本项目未装 hrms**，可精简 | 已核实 `:188 istable` |
| `doctype/cash_flow_item/cash_flow_item.py` | 空壳 | 8 | 抄 | 同上 | 仅 `pass` | 已核实 |
| `doctype/cash_flow_subtotal/cash_flow_subtotal.json` | 子表 | 74 | 抄后改 | `.../doctype/cash_flow_subtotal/` | `module`；`monthly_amount`/`yearly_amount` 是 **`Float` 不是 `Currency`**，无货币精度/符号，建议改 Currency | 已核实 `:48`/`:55` fieldtype=Float，`:61 istable` |
| `doctype/cash_flow_subtotal/cash_flow_subtotal.py` | 空壳 | 8 | 抄 | 同上 | 仅 `pass` | 已核实 |

### 1.2 资产负债表 Settings 一对

| 文件路径 | 类型 | 行数 | 判定 | 目标落点 | 抄后要改什么 | 依据 |
|---|---|---|---|---|---|---|
| `doctype/balance_sheet_settings/balance_sheet_settings.json` | DocType 定义 | 75 | 抄后改 | `.../doctype/balance_sheet_settings/` | `module`；**`issingle: 1` 本期不改**（只用小企业准则一套） | 已核实 `:54 "issingle": 1`；脚本核字段集：**无 `company` 字段**，字段仅 asset_row/liability_row/equity_row/items + 2 个 break |
| `doctype/balance_sheet_settings/balance_sheet_settings.py` | 业务逻辑 | 18 | **抄后改（必改）** | 同上 | **`:8` 硬编码绝对 import `from erpnext_china.erpnext_china.doctype.profit_and_loss_statement_settings.profit_and_loss_statement_settings import validate_report_settings` —— 并入式抄进 `erx_core` 后该包路径不存在，import 即 ImportError** | 已核实 |
| `doctype/balance_sheet_settings/balance_sheet_settings.js` | 表单脚本 | 28 | 抄后改 | 同上 | `:14-17` 跳转 `query-report / "BS and PL Missing Account"`；`:7` 按钮名「导入范例数据」是**硬编码中文未走 `__()`** | 已核实 |
| `doctype/balance_sheet_settings/example_data.json` | 范例数据 | 596 | 存疑 | 同上 | 31 行两栏式；`asset_row=31 liability_row=22 equity_row=30`；科目号体系为 `1001/100201/100202/1012/1101/1121…`（4位+6位明细）。**须核是否小企业会计准则(2024)，且科目号必须与本项目自己的科目表逐一对齐**，否则报表取数全空 | 已核实结构，准则版本待核（§5-E） |
| `doctype/balance_sheet_settings/test_balance_sheet_settings.py` | 测试 | 9 | 抄后改 | 同上 | 同 `FrappeTestCase` | 已核实 |
| `doctype/balance_sheet_settings_item/balance_sheet_settings_item.json` | 子表 | 142 | 抄后改 | `.../doctype/balance_sheet_settings_item/` | `module`。双栏：`lft_*`／`rgt_*` 各 7 字段（empty/bold/name/indent/calc_type/calc_sources + title）。字段完整性脚本核过：**无 field_order 悬挂、无 depends_on 引用缺失字段** | 已核实 `:132 istable` |
| `doctype/balance_sheet_settings_item/balance_sheet_settings_item.py` | 空壳 | 7 | 抄 | 同上 | 仅 `pass` | 已核实 |

### 1.3 利润表 Settings 一对

| 文件路径 | 类型 | 行数 | 判定 | 目标落点 | 抄后要改什么 | 依据 |
|---|---|---|---|---|---|---|
| `doctype/profit_and_loss_statement_settings/profit_and_loss_statement_settings.json` | DocType 定义 | 42 | 抄后改 | `.../doctype/profit_and_loss_statement_settings/` | `module`；**`issingle: 1` 本期不改** | 已核实 `:21 "issingle": 1`；`field_order` **只有 `items` 一项**，无 company 无准则维度 |
| `doctype/profit_and_loss_statement_settings/profit_and_loss_statement_settings.py` | 业务逻辑 | 114 | 抄 | 同上 | 无 app 外依赖（只 `os`/`frappe`）。**注意这是三个校验函数的宿主**：`validate_report_settings`(`:18`)／`check_duplicate_account_numbers`(`:34`)／`check_calculation_row_logic`(`:82`)，BS Settings 反向依赖它 ⇒ **两个 Settings 必须成对抄，不能只抄一个** | 已核实 |
| `doctype/profit_and_loss_statement_settings/profit_and_loss_statement_settings.js` | 表单脚本 | 28 | 抄后改 | 同上 | 同 BS `.js`（报表跳转 + 硬编码中文按钮） | 已核实 |
| `doctype/profit_and_loss_statement_settings/example_data.json` | 范例数据 | 227 | 存疑 | 同上 | 32 行单栏；**顶层只有 `items` 一个 key**（BS 那份还有三个 row 号）。含「业务收入/业务成本/税金及附加/…/净利润」，科目号 `5001,5051/5401,5402/5403/222103…`。**所有 `amount_from` 均为 `None`**（未用 Credit/Debit 取向）。准则版本待核 | 已核实结构（脚本读取） |
| `doctype/profit_and_loss_statement_settings/test_profit_and_loss_statement_settings.py` | 测试 | 9 | 抄后改 | 同上 | 同 `FrappeTestCase` | 已核实 |
| `doctype/profit_and_loss_statement_settings_item/profit_and_loss_statement_settings_item.json` | 子表 | 78 | 抄后改 | `.../doctype/profit_and_loss_statement_settings_item/` | ① `module` ② **`:20` `label` 字段的 `depends_on: "eval:!doc.lft_empty"` 引用了本子表不存在的 `lft_empty`** —— 从 BS 双栏子表复制粘贴的残留（§5-C） | 已核实 `:68 istable`；字段完整性脚本报出该悬挂引用 |
| `doctype/profit_and_loss_statement_settings_item/profit_and_loss_statement_settings_item.py` | 空壳 | 8 | 抄 | 同上 | 仅 `pass` | 已核实 |

### 1.4 空 `__init__.py`（11 个，全 0 字节）

| 文件路径 | 行数 | 判定 |
|---|---|---|
| `__init__.py`（顶层）、`doctype/__init__.py`、`report/__init__.py` | 0 | 抄（新建即可） |
| 8 个 DocType 目录 + 3 个 Report 目录下的 `__init__.py` | 0 | 抄（新建即可） |

### 1.5 Report ×3

| 文件路径 | 类型 | 行数 | 判定 | 目标落点 | 抄后要改什么 | 依据 |
|---|---|---|---|---|---|---|
| `report/fin_balance_sheet/fin_balance_sheet.py` | Script Report | 676 | 抄后改 | `erx_core/cn_tax/report/fin_balance_sheet/` | ① `:10 from erpnext.accounts.utils import get_balance_on` v16 存在，**但 `in_account_currency` 默认值 v16 是 `True`**，本代码 `:214` 显式传 `False` 故安全 ② `:4 import inspect` **全文未使用**，删 ③ `:214` **对每个科目单独调一次 `get_balance_on` ⇒ N 次查询**，双栏模式性能隐患 ④ 单栏模式 `:408-417` 在 13 次循环里**每次都重算同一个 `get_opening_balances`**，且 13 列取的是同一个期初值（§5-D） | 已核实真实现：`BalanceSheetDoubleColumns`／`BalanceSheetSingleColumn` 两类 + 自建 `get_opening_balances`(`:639`) 直查 GL Entry |
| `report/fin_balance_sheet/fin_balance_sheet.json` | Report 定义 | 28 | 抄后改 | 同上 | `module`；**`:5 "disable_prepared_report"` 在 v16 的 Report DocType 里已不存在**（§4），清掉 | 已核实 `:20 "report_type": "Script Report"`，`columns`/`filters` 为 `[]` |
| `report/fin_balance_sheet/fin_balance_sheet.js` | 报表脚本 | 118 | 抄后改 | 同上 | `:5-8` 先 `$.extend({}, erpnext.financial_statements)` 赋值，**`:11` 立刻整体覆盖同一个 key ⇒ 该 extend 是死代码**（erpnext v16 确有 `financial_statements.js`，但这里没用上） | 已核实；v16 资产存在于 `erpnext/public/js/financial_statements.js` |
| `report/fin_profit_and_loss_statement/fin_profit_and_loss_statement.py` | Script Report | 367 | 抄后改 | `erx_core/cn_tax/report/fin_profit_and_loss_statement/` | ① `:9` import `FiscalYearError, get_fiscal_year, get_currency_precision`，**前两个全文未使用**，删 ② `:183` 遗留 `print()` 调试语句，删 ③ `:228` **自己重写了一个同名 `get_balance_on` 并 `@frappe.whitelist()` 暴露**——遮蔽了 `:9` 的 import 语义，且 whitelist 让它成为可被前端调用的 API（无必要，建议去掉 whitelist）④ `:357-368` 末尾三引号块里 `:359` 的 import 路径 `erpnext_china.erpnext_chinacounting...` **明显笔误且含则霖真实公司名**，整块删 | 已核实真实现 |
| `report/fin_profit_and_loss_statement/fin_profit_and_loss_statement.json` | Report 定义 | 28 | 抄后改 | 同上 | `module`；`:5 "disable_prepared_report"` v16 已无，清掉；`ref_doctype: "GL Entry"` | 已核实 `:20 "Script Report"` |
| `report/fin_profit_and_loss_statement/fin_profit_and_loss_statement.js` | 报表脚本 | 70 | 抄后改 | 同上 | 同 BS：`:5-8` extend 被 `:11` 覆盖，死代码 | 已核实 |
| `report/bs_and_pl_missing_account/bs_and_pl_missing_account.py` | Script Report | 83 | 抄 | `erx_core/cn_tax/report/bs_and_pl_missing_account/` | 无 app 外依赖（只 `frappe`）。逻辑：列出 `report_type` 对应但没被 Settings 任何 `Closing Balance` 行引用、且不在已引用父科目子树内的叶子科目 | 已核实真实现 |
| `report/bs_and_pl_missing_account/bs_and_pl_missing_account.json` | Report 定义 | 31 | 抄后改 | 同上 | `module`；**`:12 "letter_head": "\u65b0\u6c34\u5370"`（「新水印」）是则霖自家信笺名，本站不存在，须清掉**；`:13 "letterhead": null` 这个 key **在 v16 Report DocType 里不存在**（与 `letter_head` 是两回事），清掉 | 已核实；v16 Report 字段集脚本核过 |
| `report/bs_and_pl_missing_account/bs_and_pl_missing_account.js` | 报表脚本 | 20 | 抄 | 同上 | 无 | 已核实 |

### 1.6 Workspace

| 文件路径 | 类型 | 行数 | 判定 | 目标落点 | 抄后要改什么 | 依据 |
|---|---|---|---|---|---|---|
| `workspace/中国财务报表/中国财务报表.json` | Workspace | 117 | 抄后改 | `erx_core/cn_tax/workspace/...` | ① `module` ② **`:106`/`:110` `modified_by`/`owner` = `fisher@abc.com`（则霖员工账号），本站不存在，须改 Administrator** ③ `:10 "icon": "cn-account-reporting"` 是**自定义图标名，依赖 G1c 范围的 `public/` 图标资源**，若不抄图标则须换内置图标 ④ `:115 "sequence_id": 8.0` 与 `parent_page: ""` 影响侧栏位置，按本项目调 ⑤ 链接 6 项全部指向本批对象（见 §2） | 已核实 |

---

## 2. 两侧核查（写入端／读取端）

按规范要求，凡断言「有消费方」或「是死的」，写入端与读取端都查、都给 file:line。

### 2.1 `cash_flow_code` 自定义字段 —— **活的，但写入端在我范围外（G1a）**

| 侧 | 位置 | 事实 |
|---|---|---|
| 写入端（字段定义） | `erpnext_china/fixtures/custom_field.json:5,11`（`Account-cash_flow_code`）、`:26,32`（`Customer-cash_flow_code`）、`:37,43`（`Supplier-cash_flow_code`） | 三个 Custom Field 由 fixtures 提供 |
| 读取端 | `doctype/cash_flow/cash_flow.py:192-199`（读 `Account.cash_flow_code`）、`:200-207`（读 `Cash Flow Code.party_type`）、`:212-223`（读 `Customer`/`Supplier` 的 `cash_flow_code`） | `assign_default_cash_flow_code()` 靠这三处自动带出现金流量编码 |

**结论：不是死代码。但有跨批依赖**——本批的 `cash_flow.py` 要正常工作，**必须连带 G1a 范围的 `fixtures/custom_field.json` 里那三个 Custom Field 一起抄**。只抄本批会让 `assign_default_cash_flow_code()` 静默失效（`frappe.get_all` 带一个不存在的字段名会直接报错，不是静默——见下）。

注：`Account`/`Customer`/`Supplier` 都是 erpnext 原生 DocType，v16 原生**没有** `cash_flow_code` 字段（已核 fixtures 是唯一来源）。

### 2.2 `Cash Flow Item.manual_split` 的只读控制 —— **死的**

| 侧 | 位置 | 事实 |
|---|---|---|
| 字段定义（写入端） | `doctype/cash_flow_item/cash_flow_item.json:182-186` | `manual_split` Check 字段确实存在 |
| 消费端 | 同文件 `:79` 与 `:96`：`"read_only_depends_on": "evel:doc.manual_split === 0"` | 前缀拼成 **`evel:`**（应为 `eval:`） |

**结论：`debit`/`credit` 的「非手工拆分时只读」这个控制永不生效。** 与任务书提示的 `Bank Transaction Mapping` 同型：字段结构看着对，消费端键名写错 ⇒ 永不命中。`manual_split` 字段本身在 `.py`／`.js` 里**也没有任何其它读取方**（已 grep 全目录），所以这个字段目前是纯装饰。

### 2.3 `profit_and_loss_statement_settings_item.label` 的 `depends_on` —— **死的（幸而无害）**

`:20 "depends_on": "eval:!doc.lft_empty"`，而本子表字段集是 `label`/`indent`/`amount_from`/`calc_type`/`calc_sources`/`cb_01`，**没有 `lft_empty`**（脚本核字段集确认）。JS 里 `doc.lft_empty` 求值为 `undefined` ⇒ `!undefined === true` ⇒ `label` 恒显示。**碰巧等于「没有这个 depends_on」，所以不出错**，但是从 BS 双栏子表复制粘贴的残留，抄后应删。

### 2.4 三张报表的消费方 —— **全部有，且有双向入口**

| 对象 | 被谁引用（读取端） | 位置 |
|---|---|---|
| `Fin Balance Sheet` | Workspace 链接 | `workspace/中国财务报表/中国财务报表.json:28-30` |
| | PL 报表的下拉菜单 | `fin_profit_and_loss_statement.js:56-59` |
| | 自身 onload 菜单 | `fin_balance_sheet.js:109-112` |
| `Fin Profit and Loss Statement` | Workspace 链接 | 同上 `:38-40` |
| | BS 报表的下拉菜单 | `fin_balance_sheet.js:114-117` |
| `BS and PL Missing Account` | Workspace 链接 | 同上 `:87-89` |
| | BS Settings 表单按钮 | `balance_sheet_settings.js:12-18`（传 `{report:"BS"}`） |
| | PL Settings 表单按钮 | `profit_and_loss_statement_settings.js:12-18`（传 `{report:"PL"}`） |
| | 读取端消费该 `report` 筛选 | `bs_and_pl_missing_account.py:31,37,38`（`"BS"` → Balance Sheet / Balance Sheet Settings Item；否则 PL 一路） |

**结论：`report` 筛选两侧对齐**（js `:8 options: "BS\nPL"` ↔ py `:31,:37` 判 `== "BS"`），非死代码。

### 2.5 `Cash Flow` DocType 的消费方

| 侧 | 位置 |
|---|---|
| Workspace 链接 | `workspace/中国财务报表/中国财务报表.json:48-51` |
| `Cash Flow Subtotal` 的写入端 | `cash_flow.py:138 self.append('cash_flow_subtotal', subtotal_doc)` |
| `Cash Flow Subtotal` 的读取端 | `cash_flow.py:79-83`（下个月读上月 `yearly_amount` 做累计）、`cash_flow.js:59-77`（导出 Excel 读 meta + 行数据） |
| `Cash Flow Item` 写入端 | `cash_flow.py:185 self.append('items', d)` |
| `Cash Flow Item` 读取端 | `cash_flow.py:19,29-32`（校验拆分金额）、`:56-63`（按编码/类型小计）、`:190-191`（取科目集合） |

**结论：现金流四件套内部闭环完整，无死表。** `Cash Flow Subtotal` 的跨月累计依赖 `docstatus == 1`（`cash_flow.py:73`）⇒ **必须提交才能被下月引用**，这与 `is_submittable: 1` 一致。

### 2.6 `Cash Flow.month` 是 `Select` 存字符串 —— 两侧一致但脆

写入端 `cash_flow.json:51-57` `fieldtype: Select`，options 是 `\n1\n2…\n12`（字符串）。读取端 `cash_flow.py:65 if self.month != '1'`（**字符串比较**）、`:72 Cast_(cf.month,'integer')`（SQL 侧转整数排序）、`:86 month=cint(self.month)`。三处混用但各自自洽，**未发现命中失败**。抄后若改成 Int 字段，`:65` 的 `!= '1'` 会静默失效（`1 != '1'` 恒为 True），属改造风险点。

---

## 3. 三张报表是否真实现

三个 `.json` 均为 `report_type: "Script Report"`，**无 `query` 字段、无 `javascript` 字段**（`columns`/`filters` 为空数组是 Script Report 正常形态）。任务书提示的「`report_type=Custom Report` + `query` 长度 0 + `.py` 0 字节 = 有壳无实」这一形态**在此三张里都不成立**。

| 报表 | `.py` 字节 | 是否真实现 | 实现要点 |
|---|---|---|---|
| `Fin Balance Sheet` | 23826（676 行） | **真实现（已核实）** | `execute()` 按 `show_all_months` 分派两个类。双栏类 `get_data()` 自建 `get_opening_balances()` 直查 GL Entry 取期初，并对每科目调 `erpnext.accounts.utils.get_balance_on` 取期末；再按 Settings 的 `Closing Balance`（科目号）与 `Calculate Rows`（行号）两阶段求值，含 `-` 减号前缀。单栏类多出 13 列月度 + `get_chart_data()` |
| `Fin Profit and Loss Statement` | 15204（367 行） | **真实现（已核实）** | `execute()` 读 PL Settings items → `get_acc_nums()` 展开父科目到叶子 → **自己重写的 `get_balance_on(account_numbers=[...])`**（`:228-354`，用 frappe.qb 批量按 `account_number` 分组，返回 `{acc_num:{Debit,Credit,Balance}}`）→ 两阶段求值 + 收入类自动 `*-1` |
| `BS and PL Missing Account` | 2846（83 行） | **真实现（已核实）** | 84 行有效逻辑：取 `report_type` 匹配的未禁用科目，与两个 Settings Item 子表里 `Closing Balance` 行引用的科目号集合求差，并排除已被引用父科目子树覆盖的叶子 |

**附带发现（重要）**：PL 报表 `:228` 自己定义了一个**与 `:9` import 同名**的 `get_balance_on`，函数体注释（`:310`「对应源码」`:322`「严格按源码 sql」）说明作者是照 erpnext 老版 SQL 手工改写成 query builder 的。这意味着**它不是调 erpnext 的函数，而是复刻**——好处是抄进 `erx_core` 后不随 erpnext 升级漂移，坏处是 erpnext 修 bug 它不跟。BS 报表则是**真的调** erpnext 的 `get_balance_on`（`:10` import，`:214` 调用），两张报表取数路径不一致。

---

## 4. 对外 import 依赖与 v16 风险

### 4.1 import zelin 自己的模块（G1a/G1c 范围）

| 引用方 | 被引用 | 风险 |
|---|---|---|
| `doctype/balance_sheet_settings/balance_sheet_settings.py:8` | `erpnext_china.erpnext_china.doctype.profit_and_loss_statement_settings.profit_and_loss_statement_settings.validate_report_settings` | **仍在本批内**（指向 §1.3 那个文件），但写成了**绝对包路径 `erpnext_china.erpnext_china.…`** ⇒ 并入式抄进 `erx_core` 后路径不存在，**必改**为 `erx_core.cn_tax.doctype.…` 或相对 import |
| `report/fin_profit_and_loss_statement/fin_profit_and_loss_statement.py:359` | `erpnext_china.erpnext_chinacounting.report.…` | 在三引号注释块内、**且路径本身是笔误**（`erpnext_chinacounting`），不会执行。整块删 |

**结论：本批对 G1a/G1c 的 Python import 依赖为零。** 唯一跨批依赖是数据层面的 `fixtures/custom_field.json`（§2.1）与 workspace 图标资源 `public/`（§1.6）。

### 4.2 import erpnext 的东西（v16 逐条核实）

| 引用处 | 符号 | v16 实测 | 判断 |
|---|---|---|---|
| `cash_flow.py:9` | `erpnext.accounts.report.trial_balance.trial_balance.get_rootwise_opening_balances` | **存在**，`erpnext/accounts/report/trial_balance/trial_balance.py:147`，签名 `(filters, report_type, ignore_is_opening, exchange_rate=None, ignore_reporting_currency=True)` | **可用**。zelin `:97` 传 3 个位置参数 `(filters, "Balance Sheet", 1)`，与 v16 前三参对齐 ✅ |
| `fin_balance_sheet.py:10` | `erpnext.accounts.utils.get_balance_on` | **存在**，`erpnext/accounts/utils.py:202`。v16 签名含 `finance_book`/`include_default_fb_balances` 两个新参，**且 `in_account_currency` 默认 `True`**，`ignore_account_permission` 默认 `False` | **可用但需留意**。zelin `:214` 显式传 `in_account_currency=False` ✅；未传 `ignore_account_permission` ⇒ 走 v16 默认 `False` ⇒ **会做科目读权限检查**（`utils.py:270-271`），低权限用户跑报表可能抛权限错。**未实测**，列为待验 |
| `fin_profit_and_loss_statement.py:9` | `erpnext.accounts.utils.get_currency_precision` | **存在**，`erpnext/accounts/utils.py:1191` | 可用 ✅ |
| `fin_profit_and_loss_statement.py:9` | `FiscalYearError`（`utils.py:51`）、`get_fiscal_year`（`utils.py:64`） | 都存在 | **但全文未使用**，删 import |
| `cash_flow.js:24`、两张报表 `.js:26` | `erpnext.utils.get_fiscal_year`（前端） | 属 erpnext bundle | 本项目装了 erpnext ⇒ 可用。**未在浏览器实测** |
| 两张报表 `.js:5-8` | `erpnext.financial_statements` | v16 **存在**：`erpnext/public/js/financial_statements.js:8`，经 `erpnext.bundle.js:37` 打包 | 资产在，**但代码里被下一行覆盖成死代码** |

### 4.3 import frappe 的东西（v16 逐条核实）

| 符号 | 引用处 | v16 实测 | 判断 |
|---|---|---|---|
| `frappe.tests.utils.FrappeTestCase` | 4 个 `test_*.py:5` | **`frappe/tests/utils.py` 文件不存在**；`frappe/tests/utils/` 是**包**，其 `__init__.py:75` 有 `FrappeTestCase = get_tests_CompatFrappeTestCase()`，工厂在 `frappe/deprecation_dumpster.py:558`，内部 `:604-607` 发废弃警告，指明**改用 `frappe.tests.UnitTestCase` / `frappe.tests.IntegrationTestCase`**，计划 v17 移除 | **能 import，但已废弃**。4 个测试文件都是 `pass` 空壳，**抄后应直接改成 `IntegrationTestCase`**，成本极低 |
| `frappe.query_builder.functions.Cast_` | `cash_flow.py:7` | **存在**，`frappe/query_builder/functions.py:163 class Cast_(Function)` | 可用 ✅ |
| `frappe.query_builder` 的 `DocType`／`Order`／`Criterion` | `fin_balance_sheet.py:7`、`fin_pl.py:6` | `DocType` 经 `frappe/query_builder/__init__.py:9` 导出；`Order`/`Criterion` 来自 `from pypika import *`（`:2`） | 可用 ✅。`Order` 在 `fin_balance_sheet.py` 里**是否真用到未核**（疑同 `inspect` 一样是废 import） |
| `frappe.query_builder.functions.Sum`／`Round` | 两张报表 | 存在 | 可用 ✅ |
| `frappe.get_file_json` | 两个 Settings `.py` | **存在**，`frappe/__init__.py:1101` | 可用 ✅ |
| `frappe.get_precision` | `fin_balance_sheet.py:648` | **存在**，`frappe/__init__.py:698` | 可用 ✅ |
| `frappe.get_single`／`get_single_value`／`get_cached_value` | 报表与 doctype 多处 | 存在（`frappe/__init__.py:1599-1602` 处再导出） | 可用 ✅ |
| `frappe.utils.get_link_to_form` | 两张报表 | **存在**，`frappe/utils/data.py:1931` | 可用 ✅ |
| `frappe.tools.downloadify`（前端） | `cash_flow.js:78` | **存在**，`frappe/public/js/frappe/utils/tools.js:8` | 可用 ✅ |
| `frappe.utils` 的 `cint/cstr/flt/getdate/datetime/get_first_day/get_last_day/formatdate/add_days/nowdate` | 多处 | 常规工具，均在 | 可用 ✅ |

### 4.4 Report DocType 的 JSON 键在 v16 的有效性（脚本核 `frappe/core/doctype/report/report.json`，29 字段）

| 键 | v16 | 出现处 |
|---|---|---|
| `query`／`javascript`／`report_type`／`add_translate_data`／`timeout`／`letter_head`／`prepared_report`／`ref_doctype`／`columns`／`filters`／`roles`／`module`／`is_standard`／`add_total_row` | **存在** | — |
| **`disable_prepared_report`** | **不存在（v16 已移除）** | `fin_balance_sheet.json:5`、`fin_profit_and_loss_statement.json:5` ⇒ 抄后清掉 |
| **`letterhead`** | **不存在**（只有 `letter_head`） | `bs_and_pl_missing_account.json:13` ⇒ 抄后清掉 |

---

## 5. 疑点与待核项

### 5-A `cash_flow.py:101` 过滤键写成大写 `"Company"` —— 实测判断：**MariaDB 下侥幸能跑**

```python
cash_accounts = frappe.get_all("Account",
    filters = {"Company": self.company,          # ← 大写 C
                "account_type": ("in", ['Cash','Bank'])},
    pluck = 'name')
```

已核：`frappe/model/db_query.py:795 prepare_filter_condition()` 把 fieldname **原样**拼成 `` `tabAccount`.`Company` ``（`:813`），无 `.lower()` 规整（该文件里的 `.lower()` 全部用于 operator 与 field 表达式，非 filter 键名）。本站 `db_type=mariadb`（`sites/erx.localhost/site_config.json`），**MariaDB 列名不区分大小写 ⇒ 能命中**。

**但**：① 若将来迁 Postgres 会直接报列不存在；② `meta.get("fields", {"fieldname": "Company"})`（`:818-819`）匹配不到 df ⇒ `can_be_null` 与 `ifnull` 包裹逻辑走的分支与预期不同。**抄后应改成小写 `company`。** 这条是「读码 + 查框架源码」得出，**未跑 SQL 实测**。

### 5-B `cash_flow_item.json:79,96` 的 `evel:` 拼写错误 —— 已核实为死控制（详见 §2.2）

### 5-C `profit_and_loss_statement_settings_item.json:20` 的 `lft_empty` 悬挂引用 —— 已核实，无害但应删（详见 §2.3）

### 5-D `fin_balance_sheet.py` 单栏模式的 13 列疑为同值 —— **存疑，倾向是 bug，未实测**

`:408-417`（原文 `for i in range(13)` 循环内）每轮算 `key = "balance_" + str(i)`，并按 `i` 算出不同的 `from_date`（`:411-416`），**但紧接着 `:417` 调的是 `get_opening_balances(self.filters.company, add_days(self.year_start_date, -1))`——参数与 `i` 无关**，13 轮传的是同一个 `to_date`（会计年度前一天）。

⇒ 推断：单栏「13 个月列」取到的是**同一个期初余额**，`from_date` 那段计算是废码。**这只是读码推断，未跑报表验证。** 若为真，单栏模式（`show_all_months=1`）产出的月度趋势列与图表都不可用。列为**存疑**，B/C 步若要用单栏模式必须先实测。

另注：双栏模式 `:214` 对每个科目单调一次 `get_balance_on`，科目数百量级下是 N 次 SQL，**性能隐患（未实测耗时）**。

### 5-E 两份 `example_data.json` 的准则版本 —— **存疑，须业务确认**

已核实结构（脚本读取，非猜）：BS 31 行两栏 + 三个合计行号（31/22/30）；PL 32 行单栏，`amount_from` 全为 `None`。科目号体系 4 位大类 + 6 位明细（`1001`/`100201`/`2001`/`5001`/`222103`…），从「业务收入/业务成本/税金及附加…净利润」的行名看**像小企业会计准则口径**。

但：① **无法从文件本身确认是「小企业会计准则(2024)」还是则霖自用的旧版**；② 这是则霖客户的实际配置，**科目号必须与本项目自己的科目表逐一对齐**，否则 `accounts_by_num.get(account_number)` 全部返回 None ⇒ 报表数字全 0 且**不报错**（`fin_balance_sheet.py:250-263`：`if account:` 不成立就跳过 append，但 `+=` 那两行用 `.get(…, {}).get(…, 0.0)` 兜底 ⇒ 静默 0）。**这是静默失败，不是显式报错，风险高。**

### 5-F `fin_profit_and_loss_statement.py:43` 把 dict 当 name 传 —— **存疑，疑似侥幸不报错**

```python
fiscal_year = frappe.db.get_value("Fiscal Year", filters.fiscal_year, [...], as_dict=True)  # :32-34 → dict
...
if filters.month:
    year = frappe.db.get_value('Fiscal Year', fiscal_year, 'year_start_date').year          # :43 传的是上面那个 dict
```

已核 `frappe/database/database.py` 的 `get_value` 签名：`filters: FilterValue | dict | list | None` ⇒ **dict 是合法入参**，会被当**过滤条件**而非 name。所以 `:43` 实际是「按 `{year_start_date:…, year_end_date:…}` 过滤找 Fiscal Year」——**碰巧能找回同一条记录**（这两个日期唯一确定一个会计年度），故不报错。

对比 `fin_balance_sheet.py:112` 同样场景写的是 `self.fiscal_year`（正确的 name）。⇒ PL 这处是**写法错误但结果侥幸正确**，抄后应改成 `filters.fiscal_year`。**未实测**，判断依据是 `get_value` 的类型注解与语义。

### 5-G 其它待核（未覆盖）

- ~~`Order` 是否在 `fin_balance_sheet.py` 真被使用~~ —— **已核实：未使用**。`grep -n "Order"` 全文只命中 `:7` 的 import 行本身；`inspect` 同理只命中 `:4`。两个都是废 import，抄后删。
- **`get_balance_on` 的权限检查是否会挡住 Accounts User** —— v16 默认 `ignore_account_permission=False`，zelin 未显式传。未实测。
- **`Cash Flow` 的 `autoname` 用中文公司全名拼 name 是否超长** —— 未核 name 字段长度上限与实际公司名长度。
- **workspace 的 `icon: "cn-account-reporting"`** —— 图标资源在 G1c 的 `public/` 下，**我未进该目录核实其是否真存在**。
- **三张报表与现金流单据都未实际运行**（硬约束禁止动站点），所有「真实现」结论均为**静态读码 + v16 API 存在性核实**，不含运行验证。
