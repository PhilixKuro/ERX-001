# S4-G1a 财税核心清点（zelin erpnext_china → erx_core）

> 批次：G1a（三批第一批）。范围：`chart_of_accounts/`（12）+ `setup/`（3）+ 顶层散文件（6，另 stackdump 1）。
> 目标 app：`erx_core`，目标模块 `cn_tax`。并入式（抄源码，不装 app）。
> 只读调查，未改 Reference/ 与 frappe-bench/ 任何文件。
> 状态：**已完成**

## 0. 上游基线（已核实，本次自查）

| 事实 | 出处 | 结论 |
|---|---|---|
| 4 个待覆盖方法**无一带** `@erpnext.allow_regional` | `chart_of_accounts.py`（`allow_regional` 出现 0 次）；`get_chart`@L101-102 与 `get_charts_for_country`@L134-135 上方只有 `@frappe.whitelist()`；`erpnext/accounts/utils.py:1616` `get_coa` 同；`frappe/desk/treeview.py:9-10` `get_all_nodes` 同 | 证实：只能走 `override_whitelisted_methods`（L4），无 L3 替代路 |
| 上游 v16 元数据键是 **8 个**，抽成了函数 `get_chart_metadata_fields()` | `chart_of_accounts.py:281-290` | 8 键含 `account_category`；zelin 把 7 键**硬编码**在两处（`custom_account.py:32-40` 与 `:107-118`），**缺 `account_category`** |
| 上游 `create_charts` 会写 `account_category` 字段 | `chart_of_accounts.py:50` `"account_category": child.get("account_category")` | zelin 的 `erpnext_china_create_charts` **没有这一行** → 抄后必补 |
| 上游 `account_currency` 取值逻辑 v16 已改 | `chart_of_accounts.py:51-53`：`child.get("account_currency") if custom_chart else frappe.get_cached_value(...)` | zelin 写的是 `child.get(...) or frappe.get_cached_value(...)`（`custom_account.py:64-65`）→ **与 v16 语义不同**，抄后要对齐 |
| 上游 `_import_accounts` v16 带 `nonlocal custom_chart` | `chart_of_accounts.py:21` | zelin 无（因其不需要 custom_chart 分支） |
| 税模板 OR 过滤确认 | `taxes_setup.py:217-223`（`or_filters={"account_name":…}`，有 number 才 update 进去，`frappe.get_all` 传 `or_filters=`） | **OR 成立**：按名可命中 ⇒ 笔误不致功能缺失 |
| 不命中时会**创建**科目 | `taxes_setup.py:228-242` `get_or_create_account` 后半段 | 证实：笔误最坏后果是多建科目，不是静默失败 |
| 上游 `get_chart` 用 `os.path.dirname(__file__)` 定位 | `chart_of_accounts.py:124` | 对比：zelin 改用 `get_bench_path()+apps/...` 拼绝对路径 ⇒ 这是硬编码来源 |

## 1. 三条重点的核实结果

### 1.1 `tax_template.json` 笔误（已核实，**你的判断成立，且笔误比你说的多一处**）

`chart_of_accounts` 下有 **3 个准则键**（不是 1 个）：`小企业会计准则` / `小企业会计准则(2024)` / `一般企业会计准则(2024)`，每键各 5 条 sales + 5 条 purchase。

`小企业会计准则(2024)` 键下 `sales_tax_templates` 的 5 条 `account_head.account_number`：

| 下标 | title | account_number | 在表内？ | account_name | 判定 |
|---|---|---|---|---|---|
| [0] | P13专票含税 | `222105` | ✗ | 销项税额 | 笔误（少一位） |
| [1] | P3专票含税 | `2221005` | ✓ | 销项税额 | 正确 |
| [2] | P13专票未税 | `22210005` | ✗ | 销项税额 | 笔误（多一位） |
| [3] | P3专票未税 | `2221005` | ✓ | 销项税额 | 正确 |
| [4] | P0无税 | `2221005` | ✓ | 销项税额 | 正确 |

`purchase_tax_templates` 5 条全部 `2221001`（进项税额），**全部正确**。

**性质核实（与你一致）**：`销项税额` 在 SME(2024) 表内确为 `2221005`，`is_group=0` / `root_type=Liability` / `account_type=Tax` / 父 `应交增值税(2221000)` / 祖 `应交税费(2221)`。上游 `taxes_setup.py:217-223` 的 `or_filters` 确为 OR（`account_name` 必进，有 number 才 `update` 进去），`:222-223` 传 `or_filters=or_filters`、`filters={"company","root_type"}`。⇒ **按名命中、模板照常建出且指向正确科目**。`:226-227` 命中即 return；未命中才走 `:229-242` 建科目。
**结论：应修否则埋脆依赖，非必修**。补一句你没提的风险：`account_head` 里 **`root_type` 为 None**（见 recheck R3），`get_or_create_account:215-216` 用 `default_root_type="Liability"` 兜住了，恰好与实际一致 ⇒ 当前不出错，但同样是脆依赖。

### 1.2 `default_accounts.csv` 的 35 与 14（已核实，**35 成立；14 成立但你的举例口径要修**）

- **35 行**：文件共 35 行、**无表头**（首行即数据 `default_bank_account,银行存款`）。✓
- **14 行落不到叶子科目**：✓ 成立。但要分两层：
  - **11 行**在 SME(2024) 表里**完全查不到该名字**
  - **另 3 行**（`主营业务收入` / `主营业务成本` / `累计折旧`）**名字在表内但是 group**，被 `utils.py:25` 的 `"is_group": 0` 过滤掉
  - 你举的 `round_off_account → 财务费用-圆整差异` 属**前 11 行**那类，说法正确。
- **净影响只有 6 个字段真的空着**：27 个 distinct 字段中，21 个另有可解析候选行兜住（`csv` 同字段多行，`utils.py:31` 的字典推导只收可解析的）。**无一字段出现多候选争抢**（已查，冲突数 0）⇒ 不存在「后者覆盖前者」的隐患。

**14 行清单**（行号=文件物理行号，无表头）：

| 行 | 字段 | 写的科目名 | 失配原因 | 该字段最终是否仍被设上 |
|---|---|---|---|---|
| 4 | `default_payable_account` | 应付账款-供应商款 | 表内无此名 | 是（行3 `应付账款` 兜住） |
| 5 | `default_payable_account` | 应付账款-结算 | 表内无此名 | 是（同上） |
| 6 | `default_payroll_payable_account` | 应付职工薪酬-职工工资 | 表内无此名 | 是（行7 `职工工资` 兜住） |
| 9 | `round_off_account` | 财务费用-圆整差异 | 表内无此名 | **否，空着** |
| 10 | `write_off_account` | 营业外支出-坏账损失 | 表内无此名 | **否，空着** |
| 11 | `exchange_gain_loss_account` | 财务费用-汇兑损益 | 表内无此名 | 是（行12 `财务费用_汇兑差额` 兜住，注意是下划线） |
| 13 | `unrealized_exchange_gain_loss_account` | 财务费用-汇兑损益 | 表内无此名 | **否，空着** |
| 14 | `default_income_account` | 主营业务收入 | **表内有，但 is_group=1** | 是（行15 `销售商品收入` 兜住） |
| 16 | `default_expense_account` | 主营业务成本 | **表内有，但 is_group=1** | 是（行17 `销售商品成本` 兜住） |
| 19 | `default_discount_account` | 财务费用-现金折扣 | 表内无此名 | **否，空着** |
| 22 | `stock_adjustment_account` | 制造企业成本-库存调整 | 表内无此名（属一般准则表用语） | 是（行21 `生产成本-库存调整` 兜住） |
| 27 | `expenses_included_in_valuation` | 制造企业成本-结转库存 | 表内无此名（同上） | 是（行26 `制造费用-结转库存` 兜住） |
| 28 | `accumulated_depreciation_account` | 累计折旧 | **表内有，但 is_group=1** | **否，空着** |
| 29 | `depreciation_expense_account` | 管理费用-折旧费 | 表内无此名 | **否，空着** |

**6 个真空字段**：`round_off_account` / `write_off_account` / `unrealized_exchange_gain_loss_account` / `default_discount_account` / `accumulated_depreciation_account` / `depreciation_expense_account`。
`accumulated_depreciation_account` 这条值得单列：`累计折旧` 在 SME(2024) 里是 **group(1602)**，其下才有叶子 —— 抄后要改成指向具体叶子，否则固定资产折旧跑不起来。

### 1.3 SME(2024) 科目表结构（已核实，**你给的数全对**）

- **总节点 266**，全部有 `account_number` 且 **266 个号唯一无重**，distinct 名字 256，叶子 225 / group 41，最大深度 4。
- `root_type` 分布：Asset 72 / Liability 68 / Expense 85 / Income 26 / Equity 15，**无一节点 root_type 落空** ⇒ `report_type` 推导不会误判。
- **2 对同名父子**，与你给的完全一致：
  - `生产性生物资产` 父 `1620`(is_group=1) / 子 `1621`(is_group=0, Fixed Asset)
  - `无形资产` 父 `1700`(is_group=1) / 子 `1701`(is_group=0, Fixed Asset)
- 另有 **3 组非父子的同名**（你未提，供参考）：`其他` ×7、`应付利润` ×2、`未分配利润` ×2。这些靠 `add_suffix_if_duplicate` 的「号+名」组合键区分，因 266 个号唯一 ⇒ **不会触发加后缀**，安全。
- 4 份表**全都不含 `account_category` 键**（0 处）。

## 2. 硬编码 `apps/erpnext_china/` 路径全清单（并入式必改）

**只在一个文件、两处**（G1a 范围内已穷尽）：

| file:line | 原文 |
|---|---|
| `chart_of_accounts/custom_accounts/custom_account.py:175` | `custom_path = os.path.join(bench_dir, "apps", "erpnext_china", "erpnext_china", "chart_of_accounts", "custom_accounts")` |
| `chart_of_accounts/custom_accounts/custom_account.py:233` | 同上（`get_charts_for_country` 内，与 :175 字面完全相同） |

配套还有 **2 处硬编码 `apps/erpnext/`**（不是 erpnext_china，但同属「绕开 `__file__` 拼 bench 绝对路径」的同一毛病，抄后同样建议改）：
`custom_account.py:157` 与 `custom_account.py:216`，均为
`os.path.join(bench_dir, "apps", "erpnext", "erpnext", "accounts", "doctype", "account", "chart_of_accounts")`。
上游原版用的是 `os.path.dirname(__file__)`（`chart_of_accounts.py:124`）。

另有 **5 处 `/assets/erpnext_china/` 前端资源路径**（不是 py 路径，但 app 名同样写死）：`hooks.py:12,15,16,20,21` 与 `setup/install.py:128`。

## 3. 额外核实出的问题（你的「已知」里没有的）

### 3.1 【硬伤】`custom_account.py` 6 处 `log_error` 调用会抛 `TypeError`

v16 真实签名（`frappe/utils/error.py:44-51`）：`log_error(title=None, message=None, reference_doctype=None, reference_name=None, *, defer_insert=False)`。
zelin 写法 `frappe.log_error(f"...{e}", title="...")` ⇒ **第一个位置参已绑定 `title`，再给 `title=` ⇒ `TypeError: log_error() got multiple values for argument 'title'`**（已实机复现，见 `S4-G1-out/S4-G1a-logerror.txt`）。

出现位置：`custom_account.py:86 / 173 / 189 / 208 / 227 / 245`（共 6 处，与你说的 6 处吻合）。

**后果比「日志记不上」严重**，因为 6 处全在 `except` 块里：
- `:86` 在 `erpnext_china_create_charts` 的 `except Exception as e` 内 ⇒ 建表一旦出错，`log_error` 自己再抛 TypeError**顶替**原异常上抛，**且 `:87` 的 `frappe.local.flags.ignore_update_nsm = False` 永远执行不到**，NSM 更新标志被留在 True（跨请求污染 `frappe.local`）。
- `:173/:189/:208/:227/:245` 在读 json 的 `except` 内 ⇒ 单个文件读坏就整个 `get_chart`/`get_charts_for_country` 崩，失去「跳过坏文件继续找」的本意。

另 8 处 `log_error("单个字符串")`（`utils.py:38,59,84,103,178`、`install.py:75,115`、`doc_events.py:32`）**语法合法**：该串绑到 `title`，`message=None` ⇒ 走 `error.py:62` 的 `if message:` False 分支，traceback 仍由 `get_traceback()` 自动补 ⇒ **能用，只是把「消息」塞进了 title 位**。抄后建议改为 `title=`/`message=` 显式传。

### 3.2 【硬伤】`erpnext_china_create_charts` 漏 `account_category`

上游 `chart_of_accounts.py:50` 有 `"account_category": child.get("account_category")`，zelin 的复刻版（`custom_account.py:53-67`）**没有这一行**；且其硬编码 7 键元数据表（`:32-40` 与 `identify_is_group` 的 `:107-118`）**缺 `account_category`**，而上游 v16 已把该表抽成 `get_chart_metadata_fields()`（`chart_of_accounts.py:281-290`，**8 键**）。
后果：若科目表 json 里出现 `account_category` 键，它会被当成**子科目名**去建一个假科目，并把父节点误判为 group。
**当前 4 份中国表都不含该键（已核实 0 处）⇒ 眼下不炸**，但这是典型脆依赖：抄进 `erx_core` 后必须改为调用上游 `get_chart_metadata_fields()`，不要自己维护键表。

### 3.3 `account_currency` 取值与 v16 语义不一致

上游 v16（`chart_of_accounts.py:51-53`）：`child.get("account_currency") if custom_chart else frappe.get_cached_value(...)`。
zelin（`custom_account.py:64-65`）：`child.get("account_currency") or frappe.get_cached_value(...)`。
差异：上游在**非** custom_chart 时**无条件用公司默认币**，zelin 则只要 json 里写了币种就用它。4 份中国表是否写了 `account_currency` —— 待查（见 §待核实）。

### 3.4 【硬伤】`hooks.py:36` 覆盖 `get_all_nodes` 是**多余的**

`frappe/desk/treeview.py:17` 的 `get_all_nodes` **自己第一行就调了** `tree_method = frappe.override_whitelisted_method(tree_method)`。
也就是说：`get_coa` 的覆盖**已经**在 treeview 内部自动生效，不需要再覆盖 `get_all_nodes`。
zelin 的 `custom_account.py:250-254` 只是「再解析一次 tree_method 再转调原函数」—— **纯冗余**。
**并入式建议：`get_all_nodes` 这条覆盖直接不要**（4 个方法降到 3 个，侵入面缩小）。这是本次清点发现的最值钱的一条减法。
注意 `handler.py:67` 与 `api/v2.py:36` 也各自会解析覆盖，所以 3 条覆盖走 HTTP 调用时都能生效。

### 3.5 `print_utils.py:5` 的 `from frappe.utils.data import *` 会污染 jinja 命名空间

`hooks.py:47-51` 把整个 `print_utils` **模块**注册为 jinja methods。`frappe/utils/jinja.py:239-243` 对模块用 `getmembers(obj, isfunction)` —— **把模块里所有函数全塞进 jinja 命名空间**。
而 `print_utils.py:5` 是 `import *`，`frappe/utils/data.py` **没有 `__all__`**（已核实 0 处），公开顶层函数 **167 个** ⇒ 这 167 个连同 zelin 自己的 4 个一起进 jinja。
其中 `money_in_words` **同名**：`data.py` 的原版会被 `print_utils` 自己定义的版本覆盖（定义在 import 之后）—— 这恰好是 zelin 想要的效果，但**是靠 import 顺序偶然达成的**，非常脆。
**抄后要改**：删 `import *`，改成显式 `from frappe.utils import flt, cint, in_words`；并考虑把 jinja 注册从「模块」改成「显式函数列表」。

### 3.6 `print_utils.money_in_words` 复刻的是 **v15 版本**，与 v16 上游已分叉

zelin 的实现（`print_utils.py:30-86`）来自旧版，用：

- `get_number_format_info(number_format)`（`print_utils.py:56`）—— v16 **已弃用**，现居 `frappe/deprecation_dumpster.py:994`，`@deprecated(... "v16", "Use NumberFormat.from_string() from frappe.utils.number_format instead")`。经 `utils/data.py:1495` 再导出，故 `from frappe.utils.data import *` **仍能取到**、能跑。
- 按 `number_format` 反推 `fraction_length`；v16 上游（`utils/data.py:1518-1556`）已改为读 `Currency.fraction_units` + `math.ceil(math.log10(...))`，并用 `get_number_format()` 而非 `get_number_format_info()`。

⇒ **抄后要改**：中文分支（`:72-73`）是唯一真正要留的东西，其余应改为「先调上游 `money_in_words`，仅在 `lang=='zh'` 时接管」，而不是整段复刻。`Currency.number_format` 字段 v16 仍存在（已核实），所以不改也能跑。

### 3.7 `setup/field_property.csv` 是 **36 行**（不是 35），其中 5 行的目标字段 v16 已不存在

已核实：`GL Entry` / `Stock Ledger Entry` / `Task` / `Period Closing Voucher` / `Asset Movement` 这 5 个 doctype 在 v16 **没有 `naming_series` 字段**。
`Property Setter`（`frappe/custom/doctype/property_setter/property_setter.py`）**不校验字段是否存在**（只有 `validate_fieldtype_change`，且只管 `property=="fieldtype"`）⇒ 这 5 行会**静默建出 5 条无效 Property Setter**，不报错、不中断。
性质：**垃圾数据，非崩溃**。抄后应删这 5 行。

### 3.8 【本批最大影响】`ignore_chart_of_accounts=True` 把 v16 新增的财报模板同步一起跳过了

v16 `Company.on_update`（`company.py:339-365`）：

- `:346` `if not frappe.local.flags.ignore_chart_of_accounts:` → 内含 `:348 sync_financial_report_templates(...)` + `:349 create_default_accounts()` + `:350 create_default_warehouses()`
- `:362` 同一个 flag 再判一次 → `self.set_default_accounts()`

zelin 置 `ignore_chart_of_accounts=True`（`doc_events.py:10` before_insert、`:20` on_update）把上面整块跳掉，自己在 `:21` 调 `erpnext_china_create_charts` + `:22` `create_default_warehouses()`。

**但 `sync_financial_report_templates` 被一起跳掉了 —— 这是 v16 新增功能**（`accounts/doctype/financial_report_template/financial_report_template.py:131`；v16 才有 `Account Category` 与 `Financial Report Template` 两个 doctype，已核实目录存在）。
后果：用 zelin 路径建的公司**不会同步财务报表模板**。与 §3.2 漏 `account_category` 是同一条链上的两处 —— v16 的「科目分类 → 财报模板」整套新机制被绕过。
**这是本批对「做中国财税」影响最大的一条**，因为中国财务报表正要靠它。

钩子时序已核实：`Document.insert` 先 `:505 run_method("after_insert")` 再 `:513 run_post_save_methods()`（内含 `on_update`）⇒ `company_after_insert` 置的 `erpnext_china_in_insert` 标志确实能被随后的 `company_on_update` 读到（`doc_events.py:26`）。逻辑成立。

另：`install_country_fixtures`（`company.py:858-861`）找 `erpnext.regional.china.setup.setup` —— v16 **无 `regional/china` 目录**（已核实，只有 australia/italy/south_africa/turkey/uae/us），走 `except ImportError: pass` ⇒ 无中国 fixtures，这正是 zelin 要自己补的原因。

### 3.9 【必改】`set_item_group_account` 的配置字典**没有 `小企业会计准则(2024)` 键**

`utils.py:108-123` 的 `chart_of_accounts_config` 只有 2 个键：`小企业会计准则`（非 2024）与 `一般企业会计准则(2024)`。
`utils.py:130-131` 的兜底：不在字典里就退回 `小企业会计准则`。
⇒ **我们选定的 `小企业会计准则(2024)` 正好落进兜底分支，用的是非 2024 的映射表。**

实测这套映射在 2024 表里的命中情况：

| Item Group | 映射到的科目 | 在 2024 表里 |
|---|---|---|
| Raw Material / Sub Assemblies / Consumable | `生产成本-基本生产成本` | 是叶子，可用 |
| Services | `生产成本-辅助生产成本` | 是叶子，可用 |
| Product | `主营业务成本` | **是 group** ⇒ 被 `utils.py:141` 的 `is_group:0` 过滤，**Product 组的 expense_account 设不上** |

**⇒ 抄后必改**：给 `小企业会计准则(2024)` 加显式键，且 `Product` 要指向叶子（2024 表里 `销售商品成本` 是叶子，可用）。
附带风险：`utils.py:110-114` 用 `_("Raw Material")` 取**已翻译**的 Item Group 名，而上游 `install_fixtures.py:49` 建组时也用 `_()` ⇒ 两边一致，成立。但这依赖翻译表两侧一致，属脆依赖。

### 3.10 `set_warehouse_account` 的两个科目在 2024 表里都是叶子

已核实：`库存商品` 与 `在产品` 在 `小企业会计准则(2024)` 中均 `is_group=0`。`utils.py:94-98` 的查询**没有 `is_group` 过滤**（与 `set_default_accounts` 不同），故即使是 group 也会被设上 —— 当前不出问题，但少了一道防护。

### 3.11 `tax_template.json` 的 `included_in_print_rate` 放错层级（解释了那段补偿 SQL）

`tax_template.json` 把 `included_in_print_rate` 放在 **`account_head` 内**（见 `S4-G1a-extra.txt` E5 的逐字输出）。
但上游 `make_taxes_and_charges_template`（`taxes_setup.py:140-158`）只从 `account_head` 取 `account_name`/`tax_rate`，整个 dict 直接喂给 `get_or_create_account` ⇒ 而 **`Account` doctype 没有 `included_in_print_rate` 字段**（已核实），该键被丢弃。
`included_in_print_rate` 真正的归宿是**税行子表** `Sales Taxes and Charges`（已核实该字段存在于 `sales_taxes_and_charges.json`）。
⇒ 这正是 `utils.py:47-57` 那段「标准功能中未处理含税字段」补偿 SQL 存在的原因：它按 `header.title like '%含税%'` 事后批量置 1。
**性质**：能用，但靠**标题里含「含税」二字**这种字符串约定。`tax_rate` 则确实被上游 `:156` 从 `account_head` 捞出来用（上游支持）。抄后建议把 `included_in_print_rate` 提到 `taxes[]` 行级，删掉那段 SQL。

### 3.12 `custom_account.py` 把 2 个上游函数 import 进来后又重新定义了一遍

`:12-17` 从上游 import 了 `add_suffix_if_duplicate` 与 `identify_is_group`，**然后 `:90-100` 与 `:103-124` 又各自重新定义了同名函数**（覆盖掉刚 import 的）。
两份实现当前等价，但重定义版把元数据键表**硬编码成 7 键**（缺 `account_category`，见 §3.2）⇒ 这是「重复定义把上游修复挡在门外」的典型。
**抄后要改**：删掉 `:90-124` 两个重定义，只保留 import。
`erpnext_china_create_charts`（`:20-87`）是真正需要复刻的那个（因为要改 currency/category 逻辑），但也应尽量贴近上游。

### 3.13 覆盖 `get_chart` 覆盖不到 Python 内部直调（覆盖盲区，已核实）

`override_whitelisted_methods` 只在 **HTTP 入口**生效（`handler.py:67`、`api/v2.py:36`、`treeview.py:17`、`model/mapper.py:20,44`）。
v16 内部有 **4 处直接 python 调用 `get_chart`**，全部**绕过**覆盖：

- `chart_of_accounts.py:16`（`create_charts` 内）
- `chart_of_accounts.py:230`、`:249`
- `financial_report_template.py:132-143`（`sync_financial_report_templates` 内）

⇒ 这解释了 zelin 为什么必须同时用 `doc_events` 拦 Company 并自己调 `erpnext_china_create_charts`：**光靠 override 挡不住服务端建表路径**。
**结论：`override_whitelisted_methods`（管 UI 下拉与树展开）+ `doc_events`（管实际建表）两条路缺一不可**，这一点 zelin 的架构是对的。同时也意味着 `sync_financial_report_templates` 里那个 `get_chart(chart_of_accounts)` 拿不到中国表 ⇒ 与 §3.8 呼应。

### 3.14 `tax_template.json` 三个准则键彼此独立，删键安全（已核实）

三块的科目号互不相同、无共用：

| 准则键 | sales 用号 | purchase 用号 |
|---|---|---|
| `小企业会计准则`（非 2024） | `22210108`（该表内名为 `应交税费-应交增值税-销项税额`） | `22210101` |
| `小企业会计准则(2024)` | `222105`(误)／`2221005`／`22210005`(误) | `2221001` |
| `一般企业会计准则(2024)` | `22210210`（`待转销项税额`） | `22210190`（`待抵扣进项税额`） |

上游 `from_detailed_data`（`taxes_setup.py:95-101`）按公司的 `chart_of_accounts` 名取键、取不到才退 `"*"` ⇒ **删掉不用的 2 键不会有任何代码去读它们**，且因无 `"*"` 键，误配也只会得到空而非错配。

### 3.15 `print_utils.cncurrency` 实机复现结果（**修正我自己先前的一处误判**）

把 `cncurrency` 抽成纯函数跑（不需 frappe、不碰站点，脚本 `Spike/S4-G1a-cncurrency.py`，输出 `S4-G1-out/S4-G1a-cncurrency.txt`）。

**先纠正我自己**：我一度按读码推断「`:109 prefix = ''` 会把负号清掉」。**这个推断是错的** —— `:109` 在 `:127-129` **之前**执行，负号是之后才 `+=` 上去的。实测 10 个用例，负数符号**全部正确**：

```
-1.23     -> 负壹元贰角叁分      -100.00 -> 负壹佰元整      -0.01 -> 负壹分
0.00      -> 零元                0.50    -> 伍角整          10000.05 -> 壹万元零伍分
1234567.89-> 壹佰贰拾叁万肆仟伍佰陆拾柒元捌角玖分            100000000.00 -> 壹亿元整
```

大写金额主路径（`capital=True`）**完全正确**，这是 `money_in_words` 中文分支唯一实际走到的路径 ⇒ **当前生产行为无碍**。

**但实测暴露了 3 个真实缺陷**（均已复现，非推断）：

1. **`capital=False` 必崩。** `:119 if classical:` 让 `classical=False` 时 `iunit[0]` 停留在 `None`，`''.join(so)` 抛 `TypeError: sequence item 2: expected str instance, NoneType found`。而 `:105-106` 又让 `capital=False` 默认推出 `classical=False` ⇒ **文档承诺的「一般汉字金额」模式默认就崩**。实测：`capital=False, classical=None` → 异常；`capital=False, classical=True` → `一元整`（唯一能用的组合）。
2. **`'圆'` 分支永不可达。** `:120 iunit[0] = '元' if classical else '圆'` 整句嵌在 `if classical:` 里，进到这句时 `classical` 必为真 ⇒ 三元的 `else '圆'` 是死代码。与 `:104` 注释「默认大写金额用圆」直接矛盾，且 `capital=True` 永远输出「元」。
3. **`prefix` 参数形同废止。** `:109 prefix = ''` 无条件覆盖入参。实测 `prefix=True` 与 `prefix=False` 输出完全相同（均 `壹元整`），docstring 承诺的「以人民币开头」从未生效。

**对判定的影响**：`print_utils.py` 仍是「抄后改」，但改动理由从「修负号 bug」换成上面 3 条；且因主路径无碍，**这 3 条属改进而非阻塞项**。

## 4. 清点表（22 项 = 21 个文件 + 1 个崩溃残留）

判定四档：抄／抄后改／不抄／存疑。目标根 `erx_core/`，目标模块 `cn_tax`。

| 文件路径（相对 `erpnext_china/`） | 类型 | 行数 | 判定 | 目标落点 | 抄后要改什么 | 依据 |
|---|---|---|---|---|---|---|
| `chart_of_accounts/__init__.py` | 空包标记 | 0 | **抄** | `erx_core/cn_tax/chart_of_accounts/__init__.py` | 无 | 0 字节 |
| `chart_of_accounts/company_default/__init__.py` | 空包标记 | 0 | **抄** | 同级 `company_default/__init__.py` | 无 | 0 字节 |
| `chart_of_accounts/company_default/default_accounts.csv` | 数据 | 35 | **抄后改** | `…/company_default/default_accounts.csv` | ① 删 2 行一般准则专用词（行 22／27 的 `制造企业成本-*`）② 修 6 个真空字段（§1.2）③ `累计折旧` 改指叶子 ④ 行 12 `财务费用_汇兑差额` 的**下划线**确认是否有意（同字段行 11 用的是连字符） | §1.2 实测：35 行无表头／14 行失配／6 字段真空／无多候选冲突 |
| `chart_of_accounts/company_default/tax_rule.csv` | 数据 | 12（含表头） | **抄** | 同目录 `tax_rule.csv` | 零改动。可选：`P1专票未税` 已声明却无 Tax Rule 引用 | 交叉核实：引用的 6 个模板名在三个准则块下全都存在，无悬空引用；tax_category 亦无未声明项 |
| `chart_of_accounts/company_default/tax_template.json` | 数据 | 480 | **抄后改** | 同目录 `tax_template.json` | ① **修 2 处号笔误**：`222105`→`2221005`、`22210005`→`2221005` ② 删 `小企业会计准则` 与 `一般企业会计准则(2024)` 两键（本期不用，且指向另两份表的号，是死数据）③ `included_in_print_rate` 提到 `taxes[]` 行级（§3.11）④ 建议显式补 `root_type: "Liability"` 免吃默认值 | §1.1 + §3.11 + §3.14 实测 |
| `chart_of_accounts/company_default/utils.py` | py 业务 | 177 | **抄后改** | `…/company_default/utils.py` | ① **`set_item_group_account` 加 `小企业会计准则(2024)` 键、`Product` 改指叶子**（§3.9，必改）② 5 处 `log_error` 改显式 `title=`/`message=` ③ 5 处裸 `except:` 改 `except Exception:` 并保堆栈 ④ 若按 §3.11 改了 json，可删 `:47-57` 补偿 SQL ⑤ `set_default_accounts` 的 `is_group:0` 过滤要配合 csv 一起修 | 全文已读 + §3.9／§3.11 实测 |
| `chart_of_accounts/custom_accounts/__init__.py` | 空包标记 | 0 | **抄** | 同级 | 无 | 0 字节 |
| `…/custom_accounts/chart_of_accounts/cn_smes_chart_of_accounts2024.json` | 数据·**核心** | 1602 | **抄** | `…/custom_accounts/chart_of_accounts/` 同名 | 原样抄，**本期唯一要用的科目表**。可选增强：补 `account_category` 键以接 v16 财报模板（§3.2／§3.8） | §1.3 实测：266 节点／266 个号全唯一／root_type 无缺／2 对同名父子结构合法 |
| `…/chart_of_accounts/cn_sme_coa.json` | 数据 | 1251 | **不抄** | — | `小企业会计准则`（非 2024），本期不用。不抄不影响代码：`get_chart` 遍历目录按 `name` 匹配，少文件只少一个可选项 | 已核实 `custom_account.py:180-187` 按目录遍历 + name 匹配，无硬编码文件名 |
| `…/chart_of_accounts/cn_norm_chart_of_accounts2024.json` | 数据 | 2124 | **不抄** | — | `一般企业会计准则(2024)`，本期不用。连带删 `default_accounts.csv` 2 行 + `utils.py` 该准则映射 + `tax_template.json` 该键 | 同上 |
| `…/chart_of_accounts/cn_cnpo_chart_of_accounts2025.json` | 数据 | 1307 | **不抄** | — | `民间非营利组织会计制度(2025)`，本期不用。代码里无任何按名引用处 | 已核实；其表内本就无 `库存商品`/`在产品` |
| `…/custom_accounts/custom_account.py` | py 业务·**核心** | 254 | **抄后改** | `…/custom_accounts/custom_account.py` | ① **6 处 `log_error` 必修**（现会抛 TypeError，§3.1）② **2 处硬编码 `apps/erpnext_china/` 必改**（§2）③ 2 处硬编码 `apps/erpnext/` 建议改回 `__file__` 相对定位（§2）④ **补 `account_category`**，键表改调上游 `get_chart_metadata_fields()`（§3.2）⑤ `account_currency` 对齐 v16 语义（§3.3）⑥ **删 `:90-124` 两个重复定义**（§3.12）⑦ **`get_all_nodes` 整个函数删掉**（§3.4）⑧ `:87` flag 复位挪进 `finally` | 全文已读 + 逐条实测 |
| `setup/__init__.py` | 空包标记 | 0 | **抄** | `erx_core/cn_tax/setup/__init__.py` | 无 | 0 字节 |
| `setup/field_property.csv` | 数据 | 36 | **抄后改** | `erx_core/cn_tax/setup/field_property.csv` | **删 5 行**（`GL Entry`／`Stock Ledger Entry`／`Task`／`Period Closing Voucher`／`Asset Movement` 的 `naming_series`，v16 无此字段）。其余 31 行目标 doctype+字段均存在 | §3.7 实测（36 行，5 行失效，Property Setter 不校验故静默留垃圾） |
| `setup/install.py` | py 安装 | 140 | **抄后改**（须大改） | 业务逻辑拆到 `erx_core/cn_tax/setup/*.py`；`after_install` 只在 `hooks.py` 接线 | ① **`:69` 禁用 UOM 那句必须去掉或改语义** —— 现写法把**不在 45 个中文单位表里的所有 UOM 全置 `enabled=0`**，会禁掉上游默认单位，波及全站 ② `:85-98` 改 System Settings 9 个字段，其中 `country`/`language`/`currency`/`time_zone` 属站点级决策，**须本项目重新裁决**，不可照抄 ③ `:54-55` 的 `is_setup_complete()` 守卫保留 ④ `:117-139 set_v16_icon` 依赖 `/assets/erpnext_china/…` 与「中国财务报表」具名记录 ⇒ **存疑（见 §7）** ⑤ 2 处 `log_error` 同 §3.1 ⑥ 按架构约定 `after_install` 不写业务逻辑 | 全文已读；`uom_list` 实测 45 项；`Desktop Icon`/`Workspace Sidebar` doctype v16 均存在；`set_value`/`set_single_value` 接受 dict 过滤器（签名已核实） |
| `__init__.py`（顶层） | py 版本标记 | 8 | **不抄** | — | 内容是 `__version__='15.0.0'` 加 3 个**未使用**的 import（`os`／`importlib`／`frappe`）。`erx_core` 自有版本号，`15.0.0` 是误导 | 全文已读 |
| `doc_events.py` | py 接线·**核心** | 31 | **抄后改** | `erx_core/cn_tax/doc_events.py` | ① `china_coa`（`:5`）删到只剩 `小企业会计准则(2024)` ② `:32` `log_error` 同 §3.1 ③ `:31` 裸 `except:` 改掉 ④ **补 `sync_financial_report_templates` 调用，或明确裁决接受「不建财报模板」**（§3.8，本批最大影响项）⑤ `:17` 的 `frappe.db.exists(..., docstatus ("<",2))` 与 v16 `company.py:341-345` 的 `docstatus<2` SQL 判据看起来等价，**未逐字比对，建议复核** | 全文已读；flags 消费点、钩子时序均已核实（§3.8） |
| `hooks.py` | py 接线 | 51 | **抄后改**（不整抄） | 条目并进 `erx_core/hooks.py` | ① `app_name`/`app_title`/`publisher`/`email`/`license` 全删（并入式无独立 app）② `after_install` 指向改 `erx_core…` ③ **`override_whitelisted_methods` 从 4 条减到 3 条**（删 `get_all_nodes`，§3.4），3 条目标路径改 `erx_core.cn_tax…` ④ `doc_events` 目标路径改 `erx_core…` ⑤ `jinja.methods` 改显式函数列表而非整模块（§3.5）⑥ `app_include_icons`/`web_include_icons`/`setup_wizard_requires`/`doctype_js` 的 `/assets/erpnext_china/` 全改 `/assets/erx_core/` —— **但被引资源属 G1c 范围，我方未核实其存在 ⇒ 这几条标存疑** | 全文已读；覆盖机制与 jinja 机制均已核实 |
| `print_utils.py` | py 工具 | 198 | **抄后改** | `erx_core/i18n/print_utils.py`（普通包，非 `cn_tax`） | ① **删 `:5 from frappe.utils.data import *`** 改显式 import（§3.5）② `money_in_words`（`:30-86`）改为「先调上游、仅 `lang=='zh'` 时接管」，别整段复刻 v15（§3.6）③ `:56 get_number_format_info` 已弃用，换 `frappe.utils.number_format.NumberFormat.from_string()` ④ **`capital=False`（文档写的「一般汉字金额」模式）必崩** —— `:119 if classical:` 使 `classical=False` 时 `iunit[0]` 停留在 `None`，`:168/:198 ''.join(so)` 抛 `TypeError: sequence item 2: expected str instance, NoneType found`；而 `:105-106` 让 `capital=False` 默认推出 `classical=False` ⇒ **默认就崩**（已实机复现）⑤ `:120 iunit[0] = '元' if classical else '圆'` 整句嵌在 `if classical:` 内 ⇒ **`'圆'` 分支永不可达**，与 `:104` 注释「大写金额用圆」直接矛盾（已实机复现）⑥ `:109 prefix = ''` **无条件丢弃调用方的 `prefix=True`** ⇒ 「人民币」前缀参数形同废止（已实机复现：`prefix=True/False` 输出相同） | 全文已读；弃用位置、`Currency.number_format` 字段、jinja 模块展开机制均已核实。④⑤⑥ 三条**已实机复现**（§3.15，纯函数级、未碰站点） |
| `modules.txt` | 配置 | 1 | **不抄** | — | 内容 `ERPNext China`；`erx_core` 的 `modules.txt` 按架构只声明 `cn_tax` | 已读 |
| `patches.txt` | 配置 | 5 | **不抄** | — | 只有 `[pre_model_sync]`／`[post_model_sync]` 两个空节与注释，**零条实际 patch** | 全文已读 |
| `grep.exe.stackdump` | **崩溃残留** | 15 | **不抄** | — | Cygwin/MSYS 版 `grep.exe` 的崩溃转储（首行 `Stack trace:`，其余 14 行全是十六进制 Frame/Function/Args）。**是上一轮调查在本目录跑 grep 时崩溃留下的产物，不属 zelin 上游代码**；时间戳 `Sep 27 00:45` 亦明显晚于其余文件的 `Sep 22 23:02` | 全文已读 |

## 5. 要抄的核心文件清单（判定「抄」或「抄后改」）

**共 13 项**：9 项有实质内容 + 4 个空 `__init__.py`。

**必抄且改动量大（4 个，本批硬核）**

1. `chart_of_accounts/custom_accounts/custom_account.py`（254 行）—— 8 项改动，含 6 处 TypeError 必修、2 处硬编码路径、`get_all_nodes` 整删
2. `chart_of_accounts/company_default/utils.py`（177 行）—— 5 项改动，含 `小企业会计准则(2024)` 键必补
3. `setup/install.py`（140 行）—— 须大改并拆分；UOM 禁用与 System Settings 两段须重新裁决
4. `doc_events.py`（31 行）—— 财报模板同步缺口须裁决

**必抄改动小（4 个）**

5. `…/chart_of_accounts/cn_smes_chart_of_accounts2024.json`（1602 行）—— 原样抄，本期唯一科目表
6. `…/company_default/tax_template.json`（480 行）—— 修 2 处号笔误 + 删 2 个准则键
7. `…/company_default/default_accounts.csv`（35 行）—— 修 6 个真空字段 + 删 2 行
8. `setup/field_property.csv`（36 行）—— 删 5 行

**抄但要迁走位置 / 零改动（2 个）**

9. `print_utils.py`（198 行）→ `erx_core/i18n/`，5 项改动（含负数丢符号的疑似 bug）
10. `…/company_default/tax_rule.csv`（12 行）—— 唯一**零改动**可直接抄的实质文件

**`hooks.py` 不计入「抄文件」**：其 8 组条目并进 `erx_core/hooks.py`，属接线而非抄文件。

**4 个空 `__init__.py`**：`chart_of_accounts/`、`company_default/`、`custom_accounts/`、`setup/`。
注意 `custom_accounts/chart_of_accounts/`（放 4 份 json 的那层）**本来就没有 `__init__.py`**，是纯数据目录 —— 已核实，保持原样。

## 6. 不抄清单（8 项）与连带处理

| 文件 | 不抄理由 | 连带影响 |
|---|---|---|
| `cn_sme_coa.json` | 非 2024 版，本期不用 | 须同时删 `tax_template.json` 同名键与 `utils.py` 里该准则的 item_group 映射 |
| `cn_norm_chart_of_accounts2024.json` | 一般企业准则，本期不用 | 须同时删 `default_accounts.csv` 行 22／27、`utils.py` 该准则分支、`tax_template.json` 该键 |
| `cn_cnpo_chart_of_accounts2025.json` | 民非组织制度，本期不用 | 无连带（代码里无任何按名引用） |
| 顶层 `__init__.py` | `15.0.0` 误导；3 个 import 全未使用 | 无 |
| `modules.txt` | 声明 `ERPNext China`，与 `cn_tax` 冲突 | 无 |
| `patches.txt` | 零条实际 patch | 无 |
| `grep.exe.stackdump` | 崩溃转储，非源码 | 无 |
| `hooks.py`（作为**文件**） | 并入式无独立 app | 条目并入 `erx_core/hooks.py`，见 §4 该行 6 项改动 |

### 「不用 ≠ 不抄」的正面回答

本批里**同时服务三份表的文件共 3 个**，处理方式各不相同：

- **`tax_template.json`：抄文件、删 2 键。** 单文件内含 3 个准则键，键间完全独立（§3.14 实测三块科目号互不相同）。上游 `taxes_setup.py:97` 按公司的 `chart_of_accounts` 名取键、取不到才退 `"*"`；本文件**无 `"*"` 键** ⇒ 删掉的键永不被读，误配也只得空而非错配。
- **`default_accounts.csv`：抄文件、删 2 行。** 该文件**无准则键**，是按科目名盲匹配的扁平表。行 22／27 是一般准则的词汇（`制造企业成本-*`），在 2024 表里永远匹配不上 —— 不删也只是静默失配，删是为了干净。
- **`utils.py` 的 `chart_of_accounts_config`：抄代码、删一支、补一支。** 它**按准则名分支**，且 §3.9 已证 `小企业会计准则(2024)` 当前落进兜底分支并导致 Product 组设不上 ⇒ 这里**不是可选清理，是必改**。

## 7. 存疑项（未核实，卡在哪）

| 项 | 卡在哪 | 归谁 |
|---|---|---|
| `setup/install.py:117-139 set_v16_icon` | 依赖 `/assets/erpnext_china/icons/account_report.svg` 与名为「中国财务报表」的 `Desktop Icon`／`Workspace Sidebar` 记录。**两个 doctype v16 确实存在（已核实）**，但具名记录由谁建、svg 是否存在 —— 记录多半来自 `fixtures/`，svg 在 `public/`，**两者都在 G1c 范围**，我未越界查 | G1c |
| `hooks.py` 的 `setup_wizard_requires`／`doctype_js`／`app_include_icons`／`web_include_icons` | 共引 6 个前端资源（`js/setup_wizard.js`、3 个 `public/js/*.js`、2 个 svg），全在 `public/` 下 ⇒ **G1c 范围，未核实存在性** | G1c |
| ~~`print_utils.py` 负数丢符号~~ | **已转为已核实，且我原先的推断是错的** —— 见 §3.15 | 已闭环 |
| `doc_events.py:17` 与 v16 `company.py:341-345` 判据等价性 | 两者都是「本公司有无 docstatus<2 的 Account」，看起来等价，**未逐字比对 SQL 与 ORM 过滤的边界**（如 Account 被 cancel 的情形） | 建议实机建一个空公司观察 |
| `erpnext_china_create_charts` 与上游 `create_charts` 的其余逐行差异 | 我核实了 4 处关键差异（category／currency／键表／nonlocal），**未做整函数逐行 diff** | 建议抄的时候直接以上游 v16 函数为底，只叠中国需要的改动 |

## 8. 复核建议（按规范 §2.2）

### (a) 最弱环节 / 未覆盖什么

**最弱环节：一切「运行时才知道」的结论我都没跑。** 本批全程只读 + 纯函数级验证，**没建 app、没跑 bench、没动站点**（站点有演示数据，按约束）。具体地：

1. **没实机建过公司。** §3.8（财报模板同步被跳过）、§3.9（Product 组 expense_account 设不上）、§1.1（税模板按名命中）三条都是**静态推演 + 上游源码对读**得出的。推演链条我逐环核实了源码行号，但「实际建一个用 `小企业会计准则(2024)` 的公司、看落地结果」这一步没做。**这是本批最该补的验证**，一次建库就能同时确证这三条。
2. **`erpnext_china_create_charts` 未做整函数逐行 diff。** 我核实了 4 处关键差异（`account_category` 缺失、`account_currency` 语义、7 vs 8 键表、`nonlocal`），但没保证没有第 5 处。
3. **G1b／G1c 的交界面没查**（按分工纪律没越界）：`hooks.py` 与 `install.py:128` 共引 6 个前端资源 + 2 条具名记录，其存在性归 G1c；`erpnext_china/erpnext_china/` 那 50 个文件里是否还有别处引用我范围内的函数（尤其 `custom_account` 与 `print_utils`），归 G1b。**合批时要对一下**：若 G1b 发现有文件 import 了我判「不抄」的东西，我的判定要改。
4. **MIT 许可的署名义务没查。** 判「抄」的 13 项要带 zelin 的版权声明，具体怎么落我没定。另注意 `custom_account.py:1-2` 的文件头写的是 **GPL v3**（Frappe 原文照抄），与 zelin 仓库声明的 MIT **不一致** —— 这一处值得法务口径确认，我只记录现象。

### (b) 你给我的「已知」里有没有错的

**你给的三条重点全部成立**，核实后只有口径需要收紧，没有实质错误：

1. **税模板笔误** —— 完全正确，包括「后果已被推翻」这个判断也正确（OR 过滤我在 `taxes_setup.py:217-223` 逐行复核了）。**补充你没提的**：`chart_of_accounts` 下其实有 **3 个准则键**（不止小企业一个），另两键的科目号是另两份表的；`account_head` 里 `root_type` 为 `None`，靠上游 `:215` 的 `default_root_type="Liability"` 兜住，恰好与实际一致 —— 又一处脆依赖。
2. **35／14** —— 数字全对。**但口径要拆**：14 行里 **11 行是「表内查不到这个名字」**，另 **3 行是「名字在表内但它是 group」**（`主营业务收入`／`主营业务成本`／`累计折旧`）。你举的 `round_off_account → 财务费用-圆整差异` 属前 11 行那类，说法准确。另外 14 行失配**不等于 14 个字段空着** —— 实际只有 **6 个字段真空**，其余 8 行被同字段的其它行兜住了。
3. **科目表结构** —— 266 节点、2 对同名父子（1620/1621、1700/1701，均 `is_group` 与 `account_type` 如你所述）全部复现无误。

**唯一需要纠正的是我自己**，不是你：我一度按读码推断 `print_utils.py:109` 会清掉负数的「负」字，实机跑完发现**推断错了**（`:109` 在 `:127` 之前，负号后加，不受影响）。已在 §3.15 明确改正。这是本次唯一一处「读码即判断」被自己的实测推翻，正好印证项目里那七次记录。

**另外提一条口径修正**：你说 `setup/` 是 3 个文件 —— 对；但 `field_property.csv` 是 **36 行**不是 35，且其中 5 行的目标字段 v16 已删除。另 `chart_of_accounts/` 你说 12 个文件 —— 我实测也是 12 个（含 3 个空 `__init__.py`），一致。

### (c) 拿不准处

1. **`get_all_nodes` 那条覆盖能不能删（§3.4）。** 我核实了 `treeview.py:17` 自己会解析覆盖，从代码上看 zelin 那层是纯冗余。但我**没实机点过科目树的「展开全部」**，不排除有我没看到的调用路径（比如前端直接打 `get_all_nodes` 且 `tree_method` 传法不同）。**这是我最想让人复核的一条**，因为它是唯一能减侵入度的发现，误判代价不对称。
2. **`default_accounts.csv` 行 12 `财务费用_汇兑差额` 用下划线**，同字段行 11 用连字符。表内确实存在下划线那个名字（所以能匹配上），但这看着像是为了绕开什么而故意写的，也可能就是打字错误。**属业务口径，我不敢替你定。**
3. **`install.py` 的 System Settings 九连改**（`country`/`language`/`currency`/`time_zone`/`rounding_method`/两个 login 开关/两个 precision）。技术上照抄能跑，但这些是站点级决策。我按「须重新裁决」标了，具体每项留不留**需要你定**。
4. **是否给 2024 科目表补 `account_category` 键**（§3.2 + §3.8）。补了能接上 v16 的「科目分类 → 财报模板」新机制，对做中国财报大概是想要的；不补则维持 zelin 现状。这是**架构取舍**不是事实问题，我只把机制讲清楚。
5. **`小企业会计准则` 这个键名的歧义。** `tax_template.json` 里有 `小企业会计准则`（非 2024）键，`utils.py` 的 item_group 配置也用这个键名，而**科目表文件 `cn_sme_coa.json` 的 `name` 也正是 `小企业会计准则`**。我们要用的是带 `(2024)` 的那个。删非 2024 的东西时**要留意别把 `(2024)` 的一起删了**，两者字符串是前缀关系，做批量替换容易出事。

## 9. 附注：两个 grep 崩溃残留

`Reference/zelin-tech-erpnext_china/` 下实际有**两个**崩溃转储：

| 路径 | 大小 | mtime |
|---|---|---|
| `erpnext_china/grep.exe.stackdump`（我范围内那个） | 1015 B | 2026-09-27 00:45:53 |
| `grep.exe.stackdump`（仓库根，范围外，同一性质） | 1013 B | 2026-09-27 00:32:26 |

两者**都早于本次调查开始时间**（我的首个命令在 01:20 之后），故均为上一轮 Agent 的产物，非本次产生。
两个都是 Cygwin/MSYS 版 `grep.exe` 的崩溃转储，内容全是十六进制栈帧地址，**都不抄**，且都未被 zelin 仓库跟踪（`git status` 显示为未跟踪）。
按只读约束我没有删除它们 —— **建议清理，但这属于改 `Reference/` 下的文件，需你授权。**

## 10. 本批产出的脚本与输出

| 文件 | 作用 |
|---|---|
| `Spike/S4-G1a-recheck.py` → `Spike/S4-G1-out/S4-G1a-recheck.txt` | 复核三条重点：4 份表清单、SME(2024) 结构（266／同名父子）、税模板号、`default_accounts.csv` 35／14、`tax_rule.csv` 交叉核对 |
| `Spike/S4-G1a-extra.py` → `S4-G1-out/S4-G1a-extra.txt` | `account_currency`/`tax_rate`/`account_category` 键普查、item_group 与 warehouse 科目命中、**`小企业会计准则(2024)` 兜底陷阱**、三个税模板块对比、UOM 45 项 |
| `Spike/S4-G1a-logerror.py` → `S4-G1-out/S4-G1a-logerror.txt` | 用 v16 真实签名实机复现 6 处 `log_error` 的 `TypeError` |
| `Spike/S4-G1a-cncurrency.py` → `S4-G1-out/S4-G1a-cncurrency.txt` | `cncurrency` 纯函数级实测（10 个金额 + 6 组参数组合），推翻了我自己关于负号的误判，暴露 3 个真实缺陷 |

全部脚本只读 `Reference/` 与 `frappe-bench/`，未 import frappe、未连站点、未跑 bench。
