# P1-S2-R1-A 参考项目盘点：zelin-tech/erpnext_china —— 中国财税本地化能力

对象：`D:\ERX-001\Reference\zelin-tech-erpnext_china\`，上游 `https://gitee.com/yuzelin/erpnext_china.git`。
51 commits，最新 2026-08-08。93 文件（43 py / 22 json / 11 js / 4 csv）。
`pyproject.toml` 声明 `frappe/erpnext >=15.0.0,<17.0.0`（即声明兼容 v16）。
本报告只盘点财税；翻译与接入机制归另两份报告。

## 0. 结论速览

**与 saoxia 截然相反：这个仓真做了财税，财税就是它的主体。** saoxia 的零命中清单在这里几乎全部转为命中。
但它做的是**账务侧**（科目表 + 增值税模板 + 三张报表），**票据侧完全没做**。

| 盘点项 | 结论 | 落点 |
|---|---|---|
| 1 会计科目表 | **有**（最扎实） | 4 份中国准则 JSON，190–353 科目 |
| 2 增值税 | **部分** | 原生 Tax Template 三件套配数据；**2 处科目号硬伤** |
| 3 发票/开票 | **无** | 只有"专票"作税目名；发票/开票/fapiao 零命中 |
| 4 金税盘/税控 | **零命中** | 金税/税控/航信/百望/诺诺 全 0 |
| 5 财务报表 | **有**（代码量最大） | 双栏资产负债表 + 利润表 + 现金流量表(直接法) + 遗漏科目检查 |
| 6 银行对账 | **零命中** | bank_reconcil / 对账 全 0 |
| 7 其他中国特色 | **部分** | 中文 UOM、金额大写、系统默认值；**无**统一社会信用代码/微信/支付宝/行政区划 |
| 8 真实 PII | **干净** | 手机号 0 个（saoxia 33727），邮箱全占位 |
| 9 许可证 | **有矛盾** | 根 MIT（`[fullname]` 未填），核心科目表文件标 GPL v3 |

有实质逻辑的约 6 个文件、90KB；其余是 4 份科目表 JSON（240KB）与 `zh.csv`（1.16MB）。
三位署名作者（Vnimy 写 doctype、杨嘉祥 写报表、余则霖/Fisher Yu 提交），拼接痕迹明显。

**质量判断：架子对，数据带病。** 四处已验证缺陷都在**配置数据层而非代码逻辑层**，
且 `setup_tax_template` / `setup_tax_rule` / `set_default_accounts` / `set_item_group_account`
**全部包在裸 `except` 里只写 log**（如 `utils.py:58-59`），失败不中断建公司 ——
缺陷静默带病上线，建完公司看不出问题，做账时才发现科目挂错。

## 1. 会计科目表 —— 有

`erpnext_china/chart_of_accounts/custom_accounts/chart_of_accounts/`：

| 文件 | `name`（界面显示名） | 科目数 |
|---|---|---|
| `cn_norm_chart_of_accounts2024.json` | 一般企业会计准则(2024) | 353 |
| `cn_smes_chart_of_accounts2024.json` | 小企业会计准则(2024) | 266 |
| `cn_cnpo_chart_of_accounts2025.json` | 民间非营利组织会计制度(2025) | 217 |
| `cn_sme_coa.json` | 小企业会计准则 | 190 |

格式与 erpnext 原生 `chart_of_accounts/verified/*.json` 一致（`country_code`/`name`/`tree`，
节点带 `is_group`/`root_type`/`account_number`/`account_type`/`tax_rate`），全部 `country_code: cn`，
层级到四级（如 `负债/应交税费/应交税费-应交增值税/应交税费-应交增值税-销项税额`）。

**建公司时能选到**，靠 `hooks.py` 的 `override_whitelisted_methods` 覆盖 4 个原生方法：
`get_charts_for_country` / `get_chart` / `erpnext.accounts.utils.get_coa` / `frappe.desk.treeview.get_all_nodes`
→ 全部指向 `custom_account.py`。后者在扫完 erpnext 原生 `verified/` 后**再扫本 app 的
`custom_accounts/chart_of_accounts` 与 `custom_of_accounts` 两目录**（`custom_account.py:175-189`、`:233-245`），
按文件名前缀 `cn` 过滤，**硬编码 app 目录名为 `erpnext_china`**。

建账走自建 `erpnext_china_create_charts`（`custom_account.py:20-87`），
由 `doc_events.py` 在 Company 的 `before_insert`/`after_insert`/`on_update` 串起：
`before_insert` 置 `ignore_chart_of_accounts=True` 拦掉原生建账，`on_update` 判断"该公司尚无 Account"后自建。
准则白名单硬编码在 `doc_events.py:5`，4 个中文字符串须与 JSON 的 `name` 逐字相等，且 `doc.country=='China'`。

`erpnext_china_create_charts` / `add_suffix_if_duplicate` / `identify_is_group` 是从 erpnext 原样复刻
（且又被从 erpnext import 一次，`:12-17`，本地重定义覆盖了 import，属冗余）。

## 2. 增值税逻辑 —— 部分

用原生 Tax Template / Tax Category / Tax Rule 三件套**配数据，无自建计税代码**。
数据在 `chart_of_accounts/company_default/`（`tax_template.json` 19KB、`tax_rule.csv`、`default_accounts.csv`），
装配代码 `company_default/utils.py`，由 `doc_events.company_on_update` → `set_company_default()` 触发。

**7 个 Tax Category**，命名法 `P{税率}{票种}{含税/未税}`：
`P13专票含税 / P3专票含税 / P1专票含税 / P13专票未税 / P3专票未税 / P1专票未税 / P0无税`，覆盖 13/3/1/0 四档。

**进项销项分离：做到了**，按科目表分三组，每组 5 sales + 5 purchase 模板挂不同 `account_head`：

| 科目表 | 销项挂 | 进项挂 |
|---|---|---|
| 小企业会计准则 | `22210108` 销项税额 | `22210101` 进项税额 |
| 小企业会计准则(2024) | `222105`/`2221005`/`22210005` 三值不一致 | `2221001` |
| 一般企业会计准则(2024) | `22210210` **待转销项税额** | `22210190` **待抵扣进项税额** |

**⚠ 缺陷一：`小企业会计准则(2024)` 销项科目号两个是错的。** 脚本遍历该 COA 确认实际销项号为
`2221005`（`/负债类/流动负债/应交税费/应交增值税/销项税额`）；而 `tax_template.json` 把
`P13专票含税` 写成 `222105`、`P13专票未税` 写成 `22210005`，**两者在该表中均 NOT FOUND**。
只有 `P3专票含税`/`P3专票未税`/`P0无税` 写对。后果：13% 这两个最常用销项模板建不出或挂错，且静默。

**⚠ 缺陷二：`一般企业会计准则(2024)` 挂的是过渡科目。** 该组用 `待转销项税额`/`待抵扣进项税额`
而非 `应交增值税` 明细。原因看得出是 `cn_norm_chart_of_accounts2024.json` 里只给这几个标了
`account_type: "Tax"`，而 `应交增值税`(`22210010`) 的 `account_type` 为空串 ——
原生 Tax Template 只接受 `account_type=Tax` 的科目，属科目表标注不全导致的将就。

**价税分离：做到了，但原生不足处打了补丁。** 每个 `account_head` 带 `included_in_print_rate`，
但 erpnext 原生 `from_detailed_data` 不读该字段，故 `utils.py:47-57` 事后补一条 qb update：
```python
# 标准功能中未处理含税字段，这里单独处理
frappe.qb.update(detail).join(header).on(header.name == detail.parent
    ).where(header.title.like('%含税%')).set(detail.included_in_print_rate, 1).run()
```
即**按标题是否含"含税"二字反推置位**，不读 JSON 那个字段。模板改名即失效；
且 `where` 只按 title like，**无公司过滤，会改到全站点所有公司的同名模板**。

**自动选税：有。** `tax_rule.csv` 11 条，9 条按 tax_category 直配（priority 1），
2 条兜底 `billing/shipping_country=China, priority=99` → 销/购均落 `P13专票含税`。
`setup_tax_rule`（`utils.py:61-84`）按 `f'{tax_template} - {abbr}'` 拼名。
CSV 与 JSON 不对称：销项无 `P1`、`P0无税` 只配了 Purchase、`P1专票未税` 声明在 tax_categories
里但两处都无对应模板与规则。

**默认科目映射**：`default_accounts.csv` 36 行，把 Company 的 20 余个默认科目字段按**中文科目名**
匹配（`utils.py:21-31`）。同字段给多候选名以兼容不同科目表，但 `values` 是 dict comprehension，
**同键后者覆盖前者**，CSV 行序决定结果，行为不显式。

**物料组成本科目**：`set_item_group_account`（`utils.py:105-178`）**只配了 `小企业会计准则` 与
`一般企业会计准则(2024)` 两套映射**，其余两准则回落到前者（`:130-131`）——
即按错准则的科目名去找，找不到静默跳过。`一般企业会计准则(2024)` 那套里 `Services` 一行是注释掉的。

**仓库库存科目**：只设 `Finished Goods`→库存商品、`Work In Progress`→在产品 两个（`utils.py:86-103`）。

**小规模/一般纳税人：代码里查无此物。** README 声称建这四个税种，实际 `tax_categories` 是那 7 个
`P*` 档位；全仓 grep `纳税人` 只命中科目表里的科目名。见第 10 节。

## 3. 发票（普票 / 专票 / 开票接口）—— 无

零命中（`grep -ril`，排除 `translations/zh.csv` 与 `locale/zh.po`）：
`发票` 0、`普票` 0、`fapiao` 0、`开票` 0、`电子发票` 0。

`专票` 仅 2 文件命中，全是税目名字符串：`company_default/tax_rule.csv` 与 `tax_template.json`。
**无 Fapiao 相关 DocType，无发票号/代码/校验码字段，无购方开户行/账号/纳税人识别号字段，
无任何开票平台 HTTP 调用**（43 个 py 文件里无 `requests`/`urllib`/外部 API）。

与 saoxia 的关系：saoxia 那个硬编码 `'P13专票含税'` 的死代码，字符串来源正是本仓这套命名法
（说明两仓之一抄了另一个的税目约定）；但本仓这套命名是**活的** —— 有对应数据和装配代码。

`public/js/sales_invoice.js` 是唯一涉及 Sales Invoice 的文件，与发票业务无关 ——
用 `setTimeout` + jQuery 抓 DOM 把"创建→付款"按钮文字改成"收款"。`purchase_order.js`/`sales_order.js` 同类。

## 4. 金税盘 / 税控设备 —— 零命中

搜 `金税`、`税控`、`航信`、`百望`、`诺诺`，全部 0 文件。无串口/USB 设备交互，无相关 DocType 或配置。

## 5. 财务报表（中国准则三大表）—— 有

自建模块 `ERPNext China`，工作区 `erpnext_china/erpnext_china/workspace/中国财务报表/`，8 个链接：
Fin Balance Sheet / Fin Profit and Loss Statement / Cash Flow + Balance Sheet Settings /
Profit and Loss Statement Settings / BS and PL Missing Account / Cash Flow Code。

**5.1 资产负债表** `report/fin_balance_sheet/fin_balance_sheet.py`（23.8KB），两个类
`BalanceSheetSingleColumn`/`BalanceSheetDoubleColumns` 按 filter `show_all_months` 分派（`:12-16`）。
**做成中国习惯的左右双栏（资产 | 负债和权益）**，这是与原生纵向 Balance Sheet 的本质差别。
配置 DocType `Balance Sheet Settings`（Single），子表字段成对 `lft_*`/`rgt_*`
（`name`/`indent`/`bold`/`empty`/`calc_type`/`calc_sources`）。`calc_type` 两值：
`Closing Balance`（按科目号取余额）/ `Calculate Rows`（按行号加减）；`calc_sources` 逗号分隔，
**支持前置负号取负**（校验时 `.replace('-','')` 剥掉）。内置示例 31 行。

**5.2 利润表** `fin_profit_and_loss_statement.py`（15.2KB）。配置子表单栏，
特有 `amount_from` Select：`Balance/Credit/Debit` —— 指定按借方、贷方还是净额取数
（费用类取借方、收入类取贷方，中国利润表必需的区分）。未配置时 msgprint 提示并返回（`:19-22`）。

**5.3 配置校验** `profit_and_loss_statement_settings.py:18-115`，被 Balance Sheet Settings
import 复用（两表共一套）。两项：`check_duplicate_account_numbers`（Warning，资产负债表左右栏
纳入同一命名空间，**只告警不阻止**）、`check_calculation_row_logic`（Error，`Calculate Rows`
引用的行号必须存在）。**没有"资产=负债+权益"合计校验，也不校验 `calc_sources` 里的科目号是否真实存在。**

**5.4 遗漏科目检查** `report/bs_and_pl_missing_account/`（2.8KB，3 函数）：列出有余额但未被两张报表
任何一行 `calc_sources` 引用的科目。README 说的"自动检查科目遗漏"**确有此物**。

**5.5 现金流量表（直接法）** —— **不是 Report，是可提交单据**，按「公司+会计年度+月份」一份，
`cash_flow.py` 10.9KB，本仓设计最有意思的一块：
- **取数** `get_cash_flow_items`（`:141-187`）：从 `GL Entry` 拉当月所有 `account_type in ('Cash','Bank')`
  分录，left join `Payment Entry` 带出 `party_type`/`party` —— 以现金/银行流水为基础，直接法的正确做法。
- **归类** `assign_default_cash_flow_code`（`:189-231`）：四级优先级自动打编码
  `Account.cash_flow_code` → 对方科目 `against` 的 → `Customer/Supplier.cash_flow_code`
  → `Cash Flow Code.party_type` 兜底；人工改过的行保留不覆盖。这些字段靠
  `fixtures/custom_field.json` 建（4 个 Custom Field）。
- **一笔拆多项**：`Cash Flow Item.manual_split`，`validate_split_amount`（`:18-39`）校验同一
  `gl_entry` 拆出各行 `debit-credit` 之和须等于总账原值，否则 throw。
- **小计与累计** `sync_subtotal`（`:41-138`）：逐月累计靠读上月已提交单据（`docstatus==1`）的
  `yearly_amount`；期初现金余额走 `erpnext...trial_balance.get_rootwise_opening_balances`。
- **编码表** `fixtures/cash_flow_code.json` 预置 **22 条**，三大类齐全
  （经营/投资/筹资）+ 四、现金净增加额 + 五、期末现金余额，带 `is_outflow`、`report_sequence`、
  三种 `formula`（`type_subtotal`/`last_period_balance`/`above_subtotal`）。项目名是标准表述。

**⚠ 缺陷三：Cash Flow Code 无公司维度。** 那 22 条 fixture 是站点全局的，
`sync_subtotal` 里 `frappe.get_all('Cash Flow Code')`（`:43-51`）也无公司过滤，多公司共享一套编码表。

**⚠ 缺陷四：示例配置与所有随包科目表都对不齐。** 脚本比对两份 `example_data.json` 引用的
144 个科目号与 4 份科目表：

| 科目表 | 命中 |
|---|---|
| 小企业会计准则 | 119/144（缺 25） |
| 小企业会计准则(2024) | 54/144 |
| 民间非营利组织会计制度(2025) | 19/144 |
| 一般企业会计准则(2024) | **0/144** |

示例是按 `cn_sme_coa.json` 编的，对另三份基本不可用；对 `一般企业会计准则(2024)` 一个都对不上
（该表用 8 位补零编码如 `22210010`，与示例的 4/6 位体系完全不同）。
**即使对 `小企业会计准则`，利润表示例的税金明细行也系统性错位**（逐行核 label vs 科目表实际名）：

| 行 | 示例 label | 引用号 | 该号实际是 |
|---|---|---|---|
| 4 | 其中：消费税 | 222103 | 应交税费-**预交增值税** |
| 5 | 营业税 | 222104 | 应交税费-**待认证进项税额** |
| 6 | 城市维护建设税 | 222108 | 应交税费-**转让金融商品应交增值税** |
| 7 | 资源税 | 222105 | 应交税费-**待转销项税额** |
| 8 | 土地增值税 | 222107 | 应交税费-**简易计税** |
| 10 | 教育费附加… | 222113 | 应交税费-**应交所得税** |
| 12 | 其中：商品维修费 | 560103 | 销售费用-**业务招待费** |

正确的号在同表里是存在的（应交消费税=`222111`、应交城建税=`222115`、商品维修费=`560110`），
看起来示例是按早期版本科目编号编的，科目表后来重排号但示例没跟着改。
**照搬示例会得到一张数字错位的利润表。** 另有 25 个号（`560118`–`560120`、`560214`–`560220`、
`1410`–`1420`、`100201`/`100202` 等）在科目表中根本不存在。

## 6. 银行对账 —— 零命中

`bank_reconcil` 0 文件、`对账` 0 文件。`银行`/`Bank` 的命中全部无关：
`default_accounts.csv:1` 的 `default_bank_account,银行存款`、4 份科目表的"银行存款"科目名、
`cash_flow.py:102`/`:160` 按 `account_type in ('Cash','Bank')` 筛科目。
**无 Bank Statement 导入、无流水解析、无对账单匹配，也无对原生 Bank Reconciliation Tool 的定制。**

## 7. 其他中国特色 —— 部分（皆配置层，不涉核算）

**a) 系统默认值** `setup/install.py:54-98`，`after_install` 且**加了
`if not frappe.is_setup_complete()` 前置**（`:55`，只对新站点生效）：
`country=China / language=zh / currency=CNY / time_zone=Asia/Chongqing /
rounding_method=Commercial Rounding / allow_login_using_user_name=1 /
allow_login_using_mobile_number=1 / currency_precision=2 / float_precision=5 / date_format=yyyy-mm-dd`。
`Global Defaults` 置 `disable_rounded_total=1`、`disable_in_words=1`。

**b) 手机号登录** 只是打开原生开关（`install.py:94`），**无短信验证码、无格式校验、无自建流程**。
与 saoxia 的企业微信登录不是一回事。

**c) 中文计量单位** `install.py:5-51` 预置 44 个中文 UOM（个/支/台/只/件/张/套/箱/包 + 长度重量体积面积
+ 时间 + 两/斤/公斤 + 摄氏度/华氏度），并**把不在清单内的所有原生 UOM 一律 `enabled=0` 禁用**
（`:69`）—— 破坏性较强。

**d) 金额转中文大写** `print_utils.py`（7.4KB），注册为 jinja method 供打印格式调用。
`cncurrency(value, capital=True, ...)`（`:88`）实现"壹贰叁肆伍陆柒捌玖拾佰仟万亿"；
`money_in_words`（`:30`）是**复刻 frappe 原方法后在中间插一段中文判断**（作者原注：
"把它原来的方法贴过来了，就是在中间加了一段"）。超上限时 `raise ValueError('金额太大了，不知道该怎么表达。')`。

**e) 字段标签与显隐** `fixtures/property_setter.json`（16.3KB）+ `setup/field_property.csv`
（由 `change_field_property()` 建 Property Setter，`install.py:100-115`）。
README 说的隐藏 PAN、改税率标签、流水码前缀改短都落在这两处；`property_setter.json` 里命中
`Sales Taxes`/`Purchase Taxes`。

**f) setup wizard 预填** `public/js/setup_wizard.js` 覆盖 `frappe.setup.utils.load_prefilled_data`，
从 System Settings 回填国家/币种/时区/语言，让 `install.py` 设的默认值在引导页已选中。

**g) v16 图标适配** `set_v16_icon()`（`install.py:117-141`）按 `Desktop Icon`/`Workspace Sidebar`
两表写图标，均包 `frappe.db.table_exists` 判断 —— **本仓唯一明确针对 v16 的适配代码**，
说明作者在 v16 上跑过。整个函数包在 `except: pass` 里。

**零命中**：`统一社会信用代码` 0、`tax_id` 0、`微信`/`wechat` 0、`支付宝`/`alipay` 0、`行政区划` 0。
**无纳税人识别号校验，无中国行政区划数据，无本地支付渠道对接。**

## 8. 真实 PII 与硬编码公司假设 —— 干净

- **手机号 0 个。** 正则 `1[3-9][0-9]{9}` 全仓扫描命中 **0**（saoxia 为 33727）。
- **8 位以上数字串**：排除科目表与示例数据后，全是增值税科目号 + 一个日期 `20260428`。
  无身份证号、无 18 位统一社会信用代码（`[0-9A-Z]{18}` 0 命中）。
- **邮箱** 7 个去重，全为占位或作者本人：`yuxinyong@163.com`（作者）、`test@test.com`、
  `test1@test.com`、`replies@yourcomany.com`（原文拼写如此）、`johndoe@mail.com`、
  `jane@example.com`、`fisher@abc.com`（workspace JSON 的 owner/modified_by）。**无真实客户/员工邮箱。**
- 无 `old_system_data.py` 之类数据倾倒文件。最大 py 是 `fin_balance_sheet.py`（23.8KB / 最长行 145 字符）。

**硬编码公司名：一处，惰性。** `fin_profit_and_loss_statement.py:356-367` 文件末尾
`"""for testing ..."""` 三引号串里留了作者公司的调试上下文：
```python
filters = frappe._dict({"company":"则霖信息技术（深圳）有限公司","fiscal_year":"2024","month":"2"})
```
是**字符串字面量而非可执行代码**（文件共 367 行，该段在最末，无赋值无 exec），不会被 import。
同段 import 路径 `erpnext_china.erpnext_chinacounting.report...` 是错的（该模块不存在），
佐证它从未执行过。全仓 grep `有限公司|股份|集团` 仅此 1 行。

**其他硬编码假设（影响可移植性）**：app 目录名 `erpnext_china`（`custom_account.py:175`、`:233`）；
准则名 4 个中文串（`doc_events.py:5`）；含税判定"含税"二字且无公司过滤（`utils.py:55`）；
时区 `Asia/Chongqing`；44 个 UOM 白名单外全禁用。

## 9. 许可证 —— 有矛盾

根 `license.txt`：**MIT**，且 copyright 行是**未填写的模板占位** `Copyright (c) [year] [fullname]`。
`hooks.py:8` 与 `pyproject.toml` 亦声明 MIT，README 末尾同。

**⚠ 抽查文件头发现一处 GPL v3**：`chart_of_accounts/custom_accounts/custom_account.py:1-2`
```python
# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt
```
成因与 saoxia 一致：该文件复刻了 erpnext 的 `chart_of_accounts.py`，连原文件头一起搬了过来。
**这恰是本仓最核心的科目表接入文件** —— "建公司时能选到中国科目表"这个能力所依赖的文件。
其 `See license.txt` 指向的本仓 license.txt 写 MIT，两者直接冲突。

其余 24 处文件头为三位作者自有版权，均写 `For license information, please see license.txt`
（回落 MIT），**无第二处 GPL**：`Copyright (c) 2023, Vnimy and contributors`（全部 doctype 及其 test）、
`Copyright (c) 2023, 杨嘉祥 and contributors`（两张报表 `fin_*`）。
无版权头的：`company_default/utils.py`、`doc_events.py`、`setup/install.py`、`print_utils.py`、
`hooks.py`、`bs_and_pl_missing_account.py`。

注意 `print_utils.py` 的 `money_in_words` **亦是复刻 frappe 原方法**（作者注释自陈），
但该文件无版权头、未标 GPL —— 属漏标而非声明冲突，性质与 `custom_account.py` 同源。

**提交者与版权署名不一致**：git 作者为 余则霖(39, gitee)、Fisher Yu(7, github)、丰茂德(3)、
xu.gui(1)、笑熬浆糊(1) 共 51 commits；代码署名却是 `Vnimy`/`杨嘉祥`，publisher 是 `yuxinyong`。
**license.txt 的 `[fullname]` 从未填写，即无人正式主张著作权归属。**

## 10. README 与代码的不一致

README 整体比代码**乐观**：

| README 声称 | 实际 |
|---|---|
| 中国科目表，建新公司时可选 | **符合** |
| 创建税种：内销/外销增值税、小规模/一般纳税人 | **不符**，这四个名字全仓无；实际是 7 个 `P*` 票种档位 |
| 税率模板 13% / 0% / 1% | **不完整**，实际 13/3/1/0 四档，README 漏了 3% |
| 分配默认科目 | **符合**，36 行 |
| 设置仓库库存科目 | **部分**，只 2 个仓 |
| 配置物料组费用科目 | **部分**，只覆盖 2 个准则，另 2 个错误回落 |
| 设置小数精度尾差科目 | **符合** |
| 中国资产负债表/利润表 | **符合** |
| 自动检查科目遗漏 | **符合** |
| 现金流量表（直接法） | **符合** |
| 默认语言中文/地区中国 | **符合** |
| 隐藏 PAN 等印度专用字段 / 流水码前缀改短 | **未逐项核对**，在 `property_setter.json` 里，见复核建议 |

README **完全没提**（代码里有）：44 个中文 UOM 且禁用其余所有原生 UOM（破坏性）、金额转大写 jinja
方法、手机号/用户名登录开关、`Commercial Rounding`、时区 `Asia/Chongqing`、三处按钮改文字。
README 自陈"建议卸载中文汉化和开箱即用后再安装" —— 作者承认与同类 app 冲突。

**最大一处不一致**：README 把示例数据说成"需设置报表项与科目号对照"的起点，
但第 5.5 节已证示例与随包科目表**系统性对不上**。README 读者会以为点一下"载入示例"就能用。

**v16 兼容性**：最近 4 个提交（2026-04-30~2026-08-08）明确针对 v16：`update translation for v16`、
`update icon path for v16`、`continue handle v16 workspact and desktop icon`；
`set_v16_icon()` 是实机跑过 v16 的证据。但**未见任何 v16 会计模块的适配提交** ——
科目表接入、税务装配、三张报表的实质改动都在 v16 适配之前。

## 11. 复核建议

**拿不准的（需实机验证）**

1. **本报告全部结论来自静态阅读，未在 v16 实机装过。** 四处缺陷是脚本逐号比对 JSON 得出的，
   逻辑上确定；但"装上去会怎样"（throw、静默跳过，还是建出挂错科目的模板）只能实装验证。
2. **对 erpnext 内部私有函数的依赖是否在 v16 仍存在，未核** —— 引入风险最高的一点。共 4 处：
   `erpnext.setup.setup_wizard.operations.taxes_setup.from_detailed_data`（`utils.py:3`）；
   `erpnext...chart_of_accounts.chart_of_accounts` 的 4 个函数（`custom_account.py:12-17`）；
   `erpnext.accounts.report.trial_balance.trial_balance.get_rootwise_opening_balances`（`cash_flow.py:9`）；
   `erpnext.accounts.utils` 的 `get_balance_on`/`get_fiscal_year`/`get_currency_precision`。
   都不是公开 API，而 **v16 适配提交只碰了图标和翻译，没碰会计**。
3. **两张报表的取数正确性未核。** 我只读了文件头、函数清单与入口，
   **未逐行核算法**（余额取数、期初结转、外币折算、`amount_from` 借贷方取数、双栏合计）。
   `fin_balance_sheet.py:213` 有注释提到外币科目需取本币余额并加 `in_account_currency=False`，
   说明这块踩过坑，值得单独细看。
4. **`property_setter.json`（16.3KB）与 `field_property.csv` 未逐项核。** 只确认命中
   `Sales Taxes`/`Purchase Taxes`，**未核到底改了哪些 doctype 的哪些字段** ——
   可能与本项目自己的字段定制冲突。
5. **`一般企业会计准则(2024)` 挂待转销项/待抵扣进项，我按会计常理判为"将就"，未向作者求证。**
   另一种可能是作者有意按纳税义务时点做过渡核算。但示例数据对该准则 0/144 命中，
   倾向支持"该准则整体未打磨完"。

**没看完的**

6. **4 份科目表 JSON（共 1026 科目）只抽查了应交税费子树与被引用的号，未整体审。**
   科目名称/编号是否合规、`root_type`/`account_type` 标注是否齐全（已知 `account_type: "Tax"`
   标注不全，导致缺陷二），未系统核。
7. `translations/zh.csv`（1.16MB）与 `locale/zh.po` **完全未读** —— 属另一份报告。
   但财税术语翻译质量直接影响报表可读性，两份报告在此有交界。
8. **git 历史只看了作者统计与最近 12 条**，未追溯缺陷引入时点。若要判断"示例与科目表脱节"
   是否最近一次科目表重排造成，需查 `cn_sme_coa.json` 与 `example_data.json` 的相对修改时间。
9. **未核 `bs_and_pl_missing_account.py` 的查询条件是否真能覆盖所有遗漏场景**
   （is_group 科目、已停用科目、零余额科目怎么算，边界未验）。
10. **22 条 Cash Flow Code 是否构成完整的直接法表，未按准则逐条核。** 骨架在，但
    "收到的税费返还""支付的各项税费"等标准项目是否齐全、`is_outflow` 是否全对，未对照表样。
    另 `code` 是 1–22 纯序号且与 `report_sequence` 相同，看起来没留扩展位。

**可靠度**：零命中类结论（发票/金税/银行对账/统一社会信用代码/微信支付宝）可靠度高 ——
关键词覆盖够，且这类能力不可能无痕存在。"有"类结论中，科目表与现金流量表的机制读到了实现细节，可靠；
两张报表的**存在与配置机制**可靠，但**算得对不对未验**。四处缺陷是脚本比对的硬结论，可靠。
