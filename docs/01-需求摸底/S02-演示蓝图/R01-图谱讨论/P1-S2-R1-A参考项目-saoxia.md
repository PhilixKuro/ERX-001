# P1-S2-R1-A 参考项目调研：saoxia/erpnext_china

> 调研对象：`https://github.com/saoxia/erpnext_china`
> 本地副本：`D:\ERX-001\Reference\saoxia-erpnext_china\`（浅克隆，117 提交，分支 `develop`，无 tag）
> 调研日期：2026-09-22
> 对应待验命题：V-08

## 结论速览

| 问题 | 答复 |
|---|---|
| 是否 app + hook 形态 | **基本是**，但 `after_install` 里有一处硬依赖 frappe/erpnext 源码文件布局（见第三节） |
| 是否实现了中国**财税**本地化 | **完全没有**。零科目表、零增值税逻辑、零发票、零金税盘、零财务报表、零银行对账 |
| 它实际做的是什么 | 中文 CRM（线索自动分配）+ 中国 HR（身份证解析、社保公积金字段、自制薪资单）+ 企业微信集成 + 汉化 + 行政区划 |
| 许可证 | MIT（但版权行是未填写的模板占位 `Copyright (c) [year] [fullname]`，且多个源文件头标 GPL v3） |
| 适配版本 | ERPNext/Frappe **v15**（Dockerfile 硬编码 `version-15`；README 称 v15 已测、v14 理论兼容、**未提及 v16**） |
| 可借用性 | 财税方向**无可借用内容**。个别技术手法可当参考，代码本身掺杂了特定客户的生产数据 |
| 对 V-08 的判定 | **no-go** |

---

## 一、项目基本情况

### 1.1 许可证

`license.txt` 是 **MIT License**，但版权声明未填：

```
Copyright (c) [year] [fullname]
```

`hooks.py` 中 `app_license = "mit"`，`pyproject.toml` 作者为 `digitii <lingyu_li@foxmail.com>`，`app_publisher = "Digitwise Ltd."`。

**需要注意的不一致**：多个源文件顶部写的是 **GPL v3**，与仓库根的 MIT 冲突。例如：

- `erpnext_china/setup/after_install/operations/install_fixtures.py:1-2`
- `erpnext_china/erpnext_china/custom_form_script/lead/lead.py:1-2`
- `erpnext_china/hrms_china/custom_form_script/employee/employee.py:1-2`

这些文件头都写着 `# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors` / `# License: GNU General Public License v3. See license.txt` —— 这是从 frappe/erpnext 复制文件后未改文件头留下的痕迹（这些文件确实继承或复刻了 erpnext 的类实现）。**即：仓库声明 MIT，但其中含有从 GPL v3 上游复制来的代码片段，文件头仍标 GPL。** 若要引用其代码，许可证状态需法务角度重新确认，不能简单按 MIT 处理。

### 1.2 适配版本

| 证据来源 | 内容 |
|---|---|
| `docker/images/development/Dockerfile:91-94` | `ARG FRAPPE_BRANCH=version-15` / `ARG ERPNEXT_BRANCH=version-15` |
| README「版本兼容性」 | 「V15：已通过兼容测试 / V14：理论兼容，未测试」 |
| `pyproject.toml` | `requires-python = ">=3.10"`；Dockerfile 用 Python 3.11.8、Node 20.17.0 |
| 测试文件 import | 全部用 `from frappe.tests.utils import FrappeTestCase`（v15 的测试基类；v16 已迁到 `UnitTestCase`/`IntegrationTestCase`） |

**结论：目标是 v15，无任何 v16 适配证据。** 本项目是 v16，直接安装大概率需要改动（至少测试基类已在 v16 变更；`override_doctype_class` 覆盖的 `SalesOrder` / `Lead` / `Employee` / `Batch` 在 v15→v16 之间的方法签名变化需逐个核对）。

### 1.3 活跃度

git log 显示**已实质停更**：

- 最近两个提交只改文档与依赖：`666097b Update README.md`（2026-01-07，只加了一行微信联系方式）、`7594726 Update pyproject.toml`（2025-12-24，只删了 `pandas==2.0.2` 依赖）
- **最后一个功能提交是 `38ad0d7`（2025-01-21）**，即功能开发停在 2025 年 1 月，此后近一年只有两次无关痛痒的改动
- 2025 年 1 月中下旬提交非常密集（1/15–1/21 十余次），呈「某项目交付期集中开发、交付后停更」的形态
- 只有 `develop` 一个分支（`origin/HEAD -> origin/develop`），**无 `main`、无 tag、无 release**

### 1.4 作者与组织背景

- `pyproject.toml` 作者 `digitii <lingyu_li@foxmail.com>`；`hooks.py` 里 `app_publisher = "Digitwise Ltd."`、`app_email = "lingyu_li@foxmail.com"`
- 提交者 `digitwise <407469895@qq.com>`，另有贡献者 `ilqc`、`xuguim`（通过 PR 合入）
- README 唯一联系方式是 `wx:lilingyu4`，无公司官网、无文档站
- **实际服务的客户可从代码里直接读出**：`erpnext_china/hrms_china/doctype/salary_slip/salary_slip.py:53` 的注释残留 `'山东朱氏药业集团有限公司'`，`erpnext_china/utils/old_system_data.py` 与 `erpnext_china/utils/timed_tasks.py:59-68` 含 10 个 `@zhushigroup.cn` 邮箱。**这是一个服务于单一客户（山东朱氏药业集团）的定制项目，以「中国本地化」之名开源。**

---

## 二、实现了哪些中国本地化能力

先给逐块盘点结论表，再逐项说明。

| 能力块 | 有/部分/无 | 说明 |
|---|---|---|
| 会计科目表（中国准则模板） | **无** | 全仓检索 `chart_of_accounts` / `科目表` / `会计科目` 零命中（排除 translations） |
| 增值税逻辑（进项/销项、多税率、价税分离） | **无** | 唯一相关命中是一行按名字查模板的辅助方法，见 2.1 |
| 发票（普票/专票、开票接口） | **无** | 检索 `fapiao` / `发票` / `专票` / `普票` 在代码中零命中；`发票` 仅出现在 `translations/zh.csv` 的界面译文里 |
| 金税盘 / 税控设备 | **无** | `金税` / `税控` 零命中 |
| 财务报表（中国准则三大报表） | **无** | `balance_sheet` / `profit_and_loss` / `cash_flow` / `资产负债` / `利润表` / `现金流量` 零命中 |
| 银行对账 | **无** | `bank_reconcil` / `bank statement` / `银行对账` / `对账` 零命中 |
| 中文译名与翻译 | **有** | `erpnext_china/translations/zh.csv`，9221 行，自称是对官方机器翻译的人工优化 |
| 中国三级行政区划 | **有** | `erpnext_china/setup/after_install/data/territory.csv`，422 行，`after_install` 时灌入 `Territory` |
| 企业微信（登录 + 通讯录 + 消息） | **有** | 见 2.2 |
| 身份证号解析 | **有** | 见 2.3 |
| 社保与公积金字段 | **部分** | 只有字段与清空逻辑，无计算引擎，见 2.4 |
| 个人所得税（个税） | **无** | `个税` / `个人所得税` / `income_tax` 在代码中零命中 |
| 微信支付 / 支付宝 | **无** | `alipay` / `wechat_pay` / `wxpay` / `支付宝` / `微信支付` 零命中 |
| 手机号登录 | **无** | 登录只做了企业微信 OAuth |
| 统一社会信用代码校验 | **无** | `统一社会信用` / `credit_code` 零命中 |
| 中国地址格式 | **部分** | 有行政区划 Territory 数据，但未改 Address 的字段顺序与格式 |
| 中国式姓名录入 | **有** | README 第 1 条，通过 `custom/employee.json`、`custom/user.json` 的 property_setter 调整姓名字段 |
| 微信/QQ 作为联系方式 | **有** | `custom/lead.json`、`custom/contact.json` 加 `custom_wechat` 等字段并隐藏 Google 通讯 |

### 2.1 增值税：唯一一处「税」相关代码

全仓与增值税相关的代码只有这一处，在 `erpnext_china/erpnext_china/custom_form_script/sales_order/sales_order.py:21-26`：

```python
@frappe.whitelist()
def get_p13(self):
    company = self.company
    name = frappe.db.get_value('Sales Taxes and Charges Template', filters={'company': company, 'tax_category': 'P13专票含税'}, fieldname='name')
    if name:
        return {'name': name}
```

这是**按硬编码的中文字符串 `'P13专票含税'` 去查一个需由用户手工预先建好的原生 `Sales Taxes and Charges Template`**。它不创建模板、不定义税率、不做价税分离、不区分进项销项，只是个查名字的便利方法。`'P13'` 是该客户内部的税种编码约定。

并且该方法**在全仓无任何调用方**：检索 `get_p13` / `P13` 只有这一处定义，`sales_order.js` 里没有调用。即这是一段死代码或半成品。

### 2.2 企业微信集成（本项目真正投入较多的功能之一）

- `erpnext_china/utils/oauth2_logins.py`：企业微信 OAuth 登录，调 `qyapi.weixin.qq.com/cgi-bin/gettoken`、`/auth/getuserinfo`、`/user/get`
- `erpnext_china/utils/wechat/api.py`（407 行）：通讯录接口 `/user/simplelist`、`/user/get` 等
- `erpnext_china/utils/wechat/WXBizMsgCrypt3.py`（279 行）：企业微信回调消息加解密，是腾讯官方示例代码
- 自建 DocType：`wecom_setting`、`wecom_msgapi_setting`、`wecom_message`
- `override_doctype_class` 覆盖 `Social Login Key` 以注入企业微信 provider（`hrms_china/custom_form_script/social_login_key/social_login_key.py`，215 行）
- `scheduler_events`：每 3 分钟刷 access_token、每 5 分钟拉打卡数据、每天核对企业微信用户
- 配置文档：`.github/doc/企业微信登录配置说明.md`

登录匹配逻辑是「企业微信账号与 ERPNext 用户邮箱一致则匹配成功」——依赖企业把企业微信 userid 设成邮箱，是一个较强的环境假设。

### 2.3 身份证号解析（`hrms_china/custom_form_script/employee/employee.py`）

从 `custom_chinese_id_number` 推导四项：

| 推导项 | 实现 | 问题 |
|---|---|---|
| 出生日期 | `f'{id_card[6:10]}-{id_card[10:12]}-{id_card[12:14]}'`（`set_date_of_birth`） | 裸切片，`try/except: pass` 吞掉所有异常 |
| 性别 | `int(id_card[-2]) % 2`，奇为男偶为女（`set_gender`） | 逻辑正确 |
| 户籍地 | 读同目录 `china_city_code.json`，`dict[id_card[:6]]`（`set_city_of_birth`） | **直接下标取值，前 6 位不在字典里会抛 KeyError**，无 `.get()` 兜底。且该 json 我在仓库对应目录未找到 |
| 年龄 | `int(days.days/365)`（`custom_age` property） | 按 365 天整除，非精确周岁 |

**没有身份证校验位（第 18 位）的合法性校验** —— 只做解析，不做校验。检索 `校验` 无命中。

### 2.4 社保与公积金：只有字段，没有计算

`hrms_china/custom/employee.json` 有 27 个 custom field，涉及社保公积金的有：

```
custom_two_social_insurance / _pay_type / _base_rate
custom_three_social_insurance / _pay_type / _base_rate
custom_housing_provident_fund / _pay_type / _base_rate
custom_social_security_payment_company
custom_social_security / custom_housing_fund
```

而 `employee.py` 里 `set_two_social_insurance` / `set_three_social_insurance` / `set_housing_provident_fund` 三个方法**只做一件事：复选框未勾选时把关联字段清空**。没有任何缴费基数计算、比例套用、地区政策差异处理。

自制 `salary_slip` DocType（`hrms_china/doctype/salary_slip/`，82 行）**绕开了 hrms 官方的 Salary Slip**，继承的是裸 `Document`：

```python
class SalarySlip(Document):
	@property
	def total_amount(self):
		total = 0
		for i in self.salary_detail:
			doc = frappe.get_doc('Salary Component', i.component)
			if doc.type == '收入':      # 硬编码中文枚举
				total += i.amount
			else:
				total -= i.amount
		return total
```

主体是一个把薪资明细行转成宽表的 CSV/Excel 导出函数。**无个税累进计算、无社保代扣代缴、无年度汇算**。注意 `doc.type == '收入'` 是硬编码中文枚举值，且该 `Salary Component` 是它自建的同名 DocType（与 hrms 官方 `Salary Component` 撞名）。

### 2.5 CRM 线索自动分配（代码量最大的功能块，与本地化无关）

这是全项目投入最大的部分，纯业务定制：

- `custom_form_script/lead/auto_allocation.py`（322 行）+ `lead.py`（319 行）+ `utils/lead_tools.py`（350 行）
- 自建 DocType：`auto_allocation_rule`、`auto_allocation_config_item`、`auto_allocation_time`、`auto_allocation_time_rule`、`auto_allocation_time_rule_link`、`auto_allocation_log`、`lead_quantity_config`、`original_leads`、`readd_contact_log`
- 百度/抖音线索落地页对接：`lead_domain_for_baidu`（195 行）、`lead_domain_for_douyin`（181 行）
- `custom/lead.json` 有 24 个 custom field + 54 个 property setter，是全项目定制最重的 doctype
- 私有/公共线索池、线索查重、重复联系方式拦截、四个 number card 统计

### 2.6 库存报表（不是财务报表）

`erpnext_china/erpnext_china/report/` 下只有两个：`stock_balance_china`、`stock_ledger_china`。两者 `"report_type": "Custom Report"`，`"reference_report": "Stock Balance"` / `"Stock Ledger"`，即**原生报表的「另存为自定义报表」产物**，纯配置无逻辑（目录下只有空 `__init__.py` 与一个 `.json`）。做的事是把列标题改成中文、加 `custom_uoms_string` 列。

**与财务报表完全无关。** 项目里没有任何 `Financial Statements` 相关的东西。

### 2.7 其他

- `button_permission` / `button_permission_check_doctype` DocType + `public/js/form_button_permission.js`：表单顶部按钮的权限配置能力（README 第 6 条），设计上与国别无关，是个通用增强
- `product_category` DocType：自建产品分类（与原生 Item Group 并存，未说明关系）
- `customer_payment_confirmation` DocType：客户打款确认单，`autoname: "format:CPC-{YY}-{MM}-{#####}"`，带银行账户/IBAN/SWIFT 字段。**注意它带 IBAN 和 SWIFT，这是国际汇款字段，恰恰不是中国银行转账的常用字段**；且它的 `.py` 只有 13 行（空 Document 类），无任何与 Payment Entry 的联动逻辑
- `permission_query_conditions` / `has_permission`：给 `Original Leads`、`Contact`、`Lead Source` 做行级权限
- `theme_switcher.js` + `override_whitelisted_methods` 覆盖 `switch_theme`

### 2.8 README 与代码的出入

**README 的自我描述与代码基本一致，但项目名严重名不副实。**

README 列了 6 条功能，逐条核对：

| README 条目 | 代码是否支撑 |
|---|---|
| 1. 姓名录入中国化、员工身份证/政治面貌，性别年龄户籍自动生成 | **是**，`employee.py` + `custom/employee.json`。但「自动创建」的健壮性有问题（见 2.3） |
| 2. CRM/客户/线索加微信 QQ 字段，同步到联系人，隐藏 Google 通讯 | **是**，`custom/lead.json`、`custom/contact.json` + `lead.py` 的 `create_contact` |
| 3. 区域列表自动添加中国三级行政区划 | **是**，`territory.csv` 422 行 + `install_fixtures.install()` |
| 4. 企业微信登录 | **是**，且是投入较多的功能 |
| 5. workspace 汉化（Your Shortcuts、Report&Master 等） | **是**，但实现方式硬依赖 erpnext/frappe 源码布局（见 3.2） |
| 6. 表单按钮权限配置（button permission） | **是** |

**真正的出入在于项目标题 `ERPNext China Location（ERPNext中国本地化）`**：以「中国本地化」命名，而 V-08 关心的财税本地化（科目表/增值税/发票/金税盘/报表/对账）一项未做。README 自己的功能列表也没有承诺这些——**它没说谎，是项目名给出了过度的预期**。

此外 README 完全没有提及代码量最大的 CRM 线索自动分配（2.5）、自制薪资单（2.4）、百度抖音线索对接——**README 描述的范围远小于代码实际范围**，未披露的部分恰恰是客户定制成分最重、最不可移植的部分。

---

## 三、接入机制（本次调研的核心技术问题）

### 3.1 用了哪些 Frappe hook

`erpnext_china/hooks.py` 全文 101 行，用到的 hook：

| hook | 用途 |
|---|---|
| `after_install` | `erpnext_china.setup.after_install.operations.install_fixtures.install` —— 此处有问题，见 3.2 |
| `app_include_js` / `app_include_css` | `erpnext_china.bundle.js` / `business.bundle.css` |
| `override_doctype_class` | 6 个：`Social Login Key`、`Employee`、`Lead`、`Batch`、`Sales Order`、`Sales Order Item` |
| `override_whitelisted_methods` | 1 个：`frappe.core.doctype.user.user.switch_theme` |
| `doctype_js` | 6 个：Opportunity、Quotation、Sales Order、Stock Entry、Lead、Customer |
| `doctype_list_js` | 1 个：Lead Source |
| `doc_events` | Sales Order `on_submit` → 生成内部采购单；Purchase Order `on_submit` → 生成内部销售单 |
| `permission_query_conditions` | Original Leads、Contact、Lead Source |
| `has_permission` | 同上三个 |
| `fixtures` | `Custom Field` 与 `Property Setter`，filter 为 `module = "ERPNext China"` |
| `override_doctype_dashboards` | Sales Order |
| `scheduler_events` | 4 条 cron（其中一条被注释掉） |
| `add_to_apps_screen` | 应用图标 |

**没有用到的**：`after_migrate`、`before_install`、`on_session_creation`、`jinja`、`website_route_rules`、`boot_session` 等。`required_apps` 是注释状态（第 8 行 `# required_apps = []`）——虽然项目重度依赖 hrms 的 Employee/Salary 相关语境，却没声明依赖。

覆盖方式值得注意的是 **它用 `override_doctype_class` 而非 `doc_events`** 来做主要定制。例如 `CustomEmployee.validate()` 是**整段抄写 erpnext 原 `Employee.validate()` 的方法体**，再插入自己的 6 个 `set_*` 调用：

```python
class CustomEmployee(Employee):
	def validate(self):
		from erpnext.controllers.status_updater import validate_status
		validate_status(self.status, ["Active", "Inactive", "Suspended", "Left"])
		self.employee = self.name
		self.set_employee_name()
		self.validate_date()
		# ... 逐行复刻上游 validate 的全部调用
		#定制
		self.set_gender()
		self.set_date_of_birth()
		# ...
```

**这种「复刻父类方法体再插入」的做法会随上游版本漂移而静默失效**：v15→v16 若 `Employee.validate()` 增删了任何一个内部调用，这个覆盖类就会丢掉上游新增的校验，且不会报错。这是对本项目 v16 迁移最直接的风险提示。

### 3.2 是否改动 erpnext / frappe 本体源码

**结论：磁盘上的上游源码未被篡改，但存在对上游源码布局的硬依赖，不是干净的 hook 接入。**

`erpnext_china/setup/after_install/operations/install_fixtures.py` 的 `overwrite_workspace()`（第 46-67 行）注释直接写明「**直接在源文件上修改**」：

```python
#修改workspace文件
def overwrite_workspace():
	#直接在源文件上修改
	workspace_file_path =[(Path(__file__).parent.parent.parent.parent.parent.parent / 'frappe' / 'frappe' / 'automation' / 'workspace'  / 'tools' / 'tools.json')
					   	,(Path(__file__).parent.parent.parent.parent.parent.parent / 'frappe' / 'frappe' / 'website' / 'workspace'  / 'website' / 'website.json')
						,... # 共 17 个路径
```

它用 `Path(__file__)` 连续 6 层 `.parent` 爬到 `apps/` 目录，再横向进入 **`apps/frappe/` 与 `apps/erpnext/` 两个上游 app 的源码目录**，读取 17 个 workspace JSON（4 个 frappe 的 + 13 个 erpnext 的，含 `accounts/workspace/accounting/accounting.json`），做字符串替换：

```python
	updated_content = file_content \
		.replace('<b>Your Shortcuts</b>', '<b>快捷入口</b>') \
		.replace('<b>Reports &amp; Masters</b>', '<b>功能&报表</b>') \
		.replace('<b>Quick Access</b>', '<b>快捷入口</b>') \
		.replace('<b>Masters & Reports</b>', '<b>功能&报表</b>')
```

**需要精确说明的一点**：我核对了该文件所有 `open()` 调用（只有第 31、72 行两处，都是读模式 `'rt'` / `'r'`），**它读上游文件但没有写回上游文件**——替换后的内容是通过 `frappe.call("frappe.desk.doctype.workspace.workspace.save_page", ...)` 写进数据库的。所以代码注释里的「直接在源文件上修改」是作者措辞不准确，磁盘上的上游源码实际未被篡改。

但这仍构成四项硬依赖：

1. 依赖 `apps/frappe`、`apps/erpnext` 的**目录位置**（靠 6 层 `.parent` 相对爬升，假定自身被安装在标准 `apps/erpnext_china/erpnext_china/setup/after_install/operations/` 路径下——路径层数一变即失效）
2. 依赖 17 个上游 workspace JSON 的**具体文件路径**，任一路径在上游改名或移动，`open()` 直接抛 `FileNotFoundError`
3. 依赖上游 JSON 里的**具体英文字符串**（`<b>Your Shortcuts</b>` 等 HTML 片段），上游改文案即静默失效（replace 无命中不报错）
4. 它把上游 workspace 整体 `save_page` 一遍，等于**把 17 个标准 workspace 全部转成数据库里的用户自定义副本**，后续上游 workspace 的更新不再生效

`save_workspace_blocks()` 还把 `LinkValidationError` 降级成 `warnings.warn`，即**部分 workspace 汉化失败会被静默跳过**。

**对 V-01（不改源码即可接入）的证据价值**：这个项目表明中文 UI 层面的定制可以不写回上游源码，但它**也没有给出干净的 workspace 汉化方案**——它选的路子是读上游源文件 + 全量 `save_page`，脆弱且有副作用。它没有触及 V-01 真正关心的财税接入点（科目表注册、税码、报表），因为**它压根没做财税**。所以 **V-08 无法为 V-01 提供实证支撑**。

其余检索结果：全仓无 monkeypatch（无 `frappe.xxx = ` 式赋值、无 `setattr` 打补丁上游对象、无 `import builtins`）、无 `patches.txt` 式的上游补丁文件、README 无任何「手工修改上游文件」的安装说明。`docker/images/development/patches/` 目录名中的 patches 是误导——里面只有一个 `common_site_config.json`（bench 站点配置，非源码补丁）。

### 3.3 自建 DocType 与 Custom Field

**自建 DocType 共 29 个**，全部集中在 CRM 线索分配、企业微信、HR 三块：

```
线索分配（9）：auto_allocation_rule / auto_allocation_config_item / auto_allocation_time /
              auto_allocation_time_rule / auto_allocation_time_rule_link / auto_allocation_log /
              lead_quantity_config / original_leads / readd_contact_log
渠道对接（2）：lead_domain_for_baidu / lead_domain_for_douyin
企业微信（3）：wecom_setting / wecom_msgapi_setting / wecom_message
HR（12）：    employee_type / employee_contract / employee_checkin_log / employee_salary_component /
             position_level / leave_request / leave_request_files / attendance_shift_type /
             salary_slip / salary_component / salary_component_account / salary_detail
其他（3）：   button_permission / button_permission_check_doctype / product_category /
             customer_payment_confirmation
```

**无一个与财税相关。** 注意 `salary_slip` / `salary_component` / `leave_request` 与 hrms 官方 DocType **同名**，这是潜在冲突点。

**Custom Field 的分布揭示了一个重要事实**：`fixtures/custom_field.json` 只有 **6 个** custom field（Sales Order Item 3 个、Employee 1 个、Selling Settings 1 个、Payment Entry 1 个），`fixtures/property_setter.json` 只有 **1 个**。

但 `*/custom/*.json` 目录下的 Customize Form 文档里有 **65 个 custom field + 173 个 property setter**：

| 文件 | custom_fields | property_setters |
|---|---|---|
| `hrms_china/custom/employee.json` | 27 | 55 |
| `erpnext_china/custom/lead.json` | 24 | 54 |
| `erpnext_china/custom/contact.json` | 3 | 6 |
| `erpnext_china/custom/crm_note.json` | 4 | 1 |
| `erpnext_china/custom/opportunity.json` | 2 | 21 |
| `hrms_china/custom/employee_education.json` | 2 | 7 |
| `erpnext_china/custom/batch.json` | 1 | 4 |
| `erpnext_china/custom/lead_source.json` | 1 | 3 |
| `hrms_china/custom/social_login_key.json` | 1 | 2 |
| `hrms_china/custom/user.json` | 1 | 9 |
| `erpnext_china/custom/quotation.json` | 0 | 10 |
| `erpnext_china/custom/webhook_request_log.json` | 0 | 1 |

即它**主要走 `module/custom/{doctype}.json` 这个 Frappe 官方机制**（app 内置 Customize Form 定义，`bench migrate` 时自动应用），`fixtures` 只是零散补充。这是一个干净且可借鉴的组织方式——**这是本项目在机制层面最值得参考的一点**，比 fixtures 导出更适合版本管理。

### 3.4 docker/ 目录做什么

只有两个文件：

- `docker/images/development/Dockerfile`：**开发环境**镜像。Python 3.11.8-slim-bookworm 基础，装 wkhtmltopdf / Node 20 / MariaDB client / redis / supervisor，`bench init --frappe-branch=version-15` + `bench get-app --branch=version-15 erpnext` + `bench get-app --branch develop erpnext_china`。时区设 `Asia/Shanghai`
- `docker/images/development/patches/common_site_config.json`：`developer_mode: true`、`http_port: 80`、`server_script_enabled: 1`、`gunicorn_workers: 29`、`background_workers: 8`

**它不是生产部署方案，是单容器开发环境**（一个容器里塞了 redis + mariadb-client + nginx + supervisor + sshd，`CMD ["/bin/bash"]`）。

**安全上要指出**：Dockerfile 把 root 和 frappe 的密码都硬编码成 `frappe`（`RUN echo 'root:frappe' | chpasswd`），开 sshd 于 22222 端口、`PermitRootLogin yes`、给 frappe 加 `ALL=(ALL:ALL) ALL` 免限 sudo，`developer_mode` 与 `server_script_enabled` 全开。**这个镜像不能用于任何可被外部访问的环境。**

---

## 四、代码质量与可借用性

### 4.1 测试：形同虚设

找到 29 个 `test_*.py` 文件，**全部是 9 行的空壳**，无一例外：

```python
# Copyright (c) 2024, Digitwise Ltd. and Contributors
# See license.txt

# import frappe
from frappe.tests.utils import FrappeTestCase


class TestSalarySlip(FrappeTestCase):
	pass
```

这是 `bench new-doctype` 自动生成的模板，作者一个都没填。**全项目零有效测试。** `.github/` 下只有 `doc/` 与 `images/`，**无 workflow 目录、无 CI**。

### 4.2 代码组织

**可取的部分**：

- 双模块划分 `erpnext_china/`（CRM/销售）与 `hrms_china/`（HR）清楚，各自带 `custom/`、`custom_form_script/`、`doctype/`、`number_card/`
- `custom_form_script/{doctype}/{doctype}.py|.js` 按 doctype 归类，py 与 js 并置，找东西容易
- 用 `module/custom/*.json` 管理 Customize Form 而非全靠 fixtures 导出（见 3.3），适合 git 版本管理

**问题**：

- `utils/` 是杂物间：`old_system_data.py`（34864 行数据）、`lead_tools.py`、`timed_tasks.py`、`oauth2_logins.py`、`wechat/` 混在一起
- 报错信息全中文硬编码、不走 `_()`，如 `frappe.throw("行 #{0} 的物料没有公司{1}的默认值配置...")`、`frappe.throw('薪资构成项不可重复！')`。项目自己带了 9221 行 zh.csv 却不给自己的消息做 i18n
- 裸 `except: pass` 吞异常（`employee.py` 的 `set_degree`、`set_date_of_birth`）
- `sales_order.py:41-53` 用 f-string 拼 SQL：
  ```python
  query = f"""
      select sup.name from `tabSupplier` sup, `tabAllowed To Transact With` al
      where ... and al.company = '{self.company}'
        and sup.represents_company in {tuple(shipping_company)}
  """
  ```
  `self.company` 是 Link 字段受约束、`tuple()` 来自数据库查询结果，实际注入面窄，但这是不该出现的写法（Frappe 有 `frappe.qb` 与参数化 `frappe.db.sql(query, values)`）。且 `tuple()` 长度为 1 时会产出 `('x',)` 的非法 SQL——作者的对策是第 39-40 行手工 append 一个空字符串凑长度，很脆
- git 历史里有 `f139eaa fix`、`1f9 40a Revert "Update sales_order.js"`、多个 `Update sales_order.py` 连环提交（1/17、1/18 各两次），是边改边试的痕迹

### 4.3 硬编码的特定公司与环境假设（最严重的问题）

这是判断可借用性的决定性因素。

**① `erpnext_china/utils/old_system_data.py`：34864 行硬编码生产数据，含真实个人信息**

```python
# 白名单内的用户录入的线索不过滤
white_list = [
	"bianxuezhen@zhushigroup.cn",
	"wangzhenhua@zhushigroup.cn",
	... # 10 个真实员工邮箱
]

# 联系方式
old_system_contacts = [
"15010632377",
"15602296515",
...
]
```

`old_system_contacts` 含 **33727 个真实手机号**（按 `^"1[0-9]{10}",` 计数）。这些是该客户旧系统的存量线索联系方式，被当作源代码提交进了公开仓库。

它被 `custom_form_script/lead/lead.py:5` 直接 import 并在 `check_in_old_system()` 里用于线索查重（`lead.py:214-226`）：

```python
def check_in_old_system(self):
	if self.is_new():
		user = frappe.session.user
		if frappe.db.get_value('Has Role',{'parent': user,'role':['in',['System Manager','网络推广管理']]}) or (user in white_list):
			return True
		else:
			if (self.phone in old_system_contacts) or (self.mobile_no in old_system_contacts) or ...
				frappe.throw("当前系统中已经存在此联系方式！")
```

**这意味着 `Lead` 的覆盖类（`CustomLead`）在模块导入期就依赖这 3 万多个号码**，任何人安装此 app 都会把该客户的存量线索号码库装进自己系统，且新建线索时会被这个库查重拦截。**这一块不仅不可借用，其存在本身让整个 `Lead` 定制无法被干净复用。** 同一份白名单在 `utils/timed_tasks.py:59-68` 又抄了一遍。

**② `employee.py` 里把组织树根硬编码成一个员工编号**

`get_employee_tree()` 里：

```python
if is_root:
	# 树的最顶点
	employee = 'HR-EMP-00002'
```

**③ 业务规则里硬编码特定员工邮箱**

`custom_form_script/lead/lead.py:153`：

```python
if note.added_by in ['jintingyan@zhushigroup.cn', 'wangjiali@zhushigroup.cn']:
```

**④ 硬编码中文枚举值**

- `salary_slip.py:20`：`if doc.type == '收入'`
- `employee.py:48`：`d = ['博士研究生','硕士研究生','本科','大专','高中(中专)']`（学历排序表）
- `sales_order.py:24`：`tax_category: 'P13专票含税'`
- 角色名 `'网络推广管理'`（`lead.py:217`）

**⑤ 残留的客户名**

`salary_slip.py:53` 注释里 `'山东朱氏药业集团有限公司'`。

### 4.4 哪些能借用，哪些只能当参考

**可以直接借用（纯数据，无业务耦合）**：

| 内容 | 路径 | 理由 |
|---|---|---|
| 中国三级行政区划 CSV | `erpnext_china/setup/after_install/data/territory.csv` | 422 行纯数据（`ID,区域名称,上级区域,是否群组`），无代码耦合，直接可用。但需先解决 4.5 与 6.1 的许可证疑问 |
| 中文翻译 zh.csv | `erpnext_china/translations/zh.csv` | 9221 行，自称人工优化过官方机器翻译，是纯数据。**但它按 v15 的 source string 对齐**，v16 改了文案的条目会失配，需比对 |

**只能当参考（手法可学，代码要重写）**：

| 内容 | 为什么只能参考 |
|---|---|
| `module/custom/{doctype}.json` 组织 Customize Form 的做法（3.3） | 机制层面最值得学的一点，但它的具体 json 内容全是该客户的 CRM/HR 字段 |
| 身份证解析（2.3） | 思路对（性别取倒数第二位奇偶、生日取 6-14 位），但实现无校验位验证、`KeyError` 不兜底、异常裸吞。重写比改便宜。且依赖的 `china_city_code.json` 仓库里没有 |
| 企业微信 OAuth 登录 + `override_doctype_class` 注入 Social Login Key provider | 接入路径有参考价值（`social_login_key.py` 215 行示范了怎么加 provider），但 `WXBizMsgCrypt3.py` 是腾讯官方示例代码，直接从腾讯拿更好 |
| `button_permission` 表单按钮权限机制 | 与国别无关的通用增强，思路可借，实现要看是否契合本项目需要 |
| `override_doctype_class` 的使用方式 | **反面参考**：它「复刻父类 validate 方法体再插入」的做法会随上游漂移静默失效（见 3.1），本项目应避免 |

**完全不能借用**：

- `utils/old_system_data.py` 及依赖它的 `lead.py` 全部线索查重逻辑（3 万真实手机号 + 真实员工邮箱）
- 全部 CRM 线索自动分配（9 个 DocType + 991 行代码，纯客户业务规则）
- 百度/抖音线索落地页对接（376 行，特定渠道特定账号）
- 自制 `salary_slip` / `salary_component`（与 hrms 官方撞名，无个税无社保计算，只是个导出器）
- `docker/` 的 Dockerfile（硬编码弱密码 + root SSH + 全开 developer_mode，且钉死 v15）
- `install_fixtures.overwrite_workspace()`（硬依赖 17 个上游 JSON 的路径与英文字符串）

**与 V-08 的财税关切直接相关的结论：可借用内容为零。** 它一行财税代码都没有。

### 4.5 明显的坑与未完成部分

| 坑 | 位置 | 说明 |
|---|---|---|
| 零测试 | 29 个 `test_*.py` 全空 | 无回归保障，改动风险自负 |
| 零 CI | `.github/` 无 workflow | 无自动化校验 |
| `get_p13` 死代码 | `sales_order.py:21-26` | 全仓无调用方 |
| `china_city_code.json` 缺失 | `employee.py:78` 引用 `Path(__file__).parent / 'china_city_code.json'` | 该目录下我未找到此文件，`set_city_of_birth` 会抛 `FileNotFoundError` |
| `KeyError` 未兜底 | `employee.py:81` `china_city_code_dict[id_card[:6]]` | 非常见行政区划码直接崩 |
| 裸吞异常 | `employee.py` `set_degree` / `set_date_of_birth` | 身份证格式错误被静默忽略，字段留空无提示 |
| 汉化失败静默 | `install_fixtures.save_workspace_blocks` | `LinkValidationError` 降级为 `warnings.warn` |
| 未声明 `required_apps` | `hooks.py:8` 注释状态 | 重度依赖 hrms 语境却不声明 |
| 自制 DocType 与 hrms 撞名 | `salary_slip`、`salary_component`、`leave_request` | 与 hrms 官方同名，共存行为未知 |
| f-string 拼 SQL | `sales_order.py:41-53` | 应参数化；`tuple()` 单元素时靠 append 空串凑合 |
| 遗留 TODO | `lead.py:13`（联系人查重未做）、`wechat/example.py:75,107` | |
| 被注释掉的代码 | `hooks.py:47`（wecom OAuth 那行）、`hooks.py:33-35`（一条 cron）、`hooks.py:88-92`（旧 doc_events） | |
| 许可证矛盾 | 根 MIT vs 多个源文件头标 GPL v3 | 见 1.1，引用前需法务确认 |
| 公开仓库含真实 PII | `old_system_data.py` 33727 手机号 + 10 员工邮箱 | 即便许可证允许，引入这份数据本身有合规问题 |
| 目标 v15，无 v16 适配 | Dockerfile / README / 测试基类 | 见 1.2 |
| 已停更 | 最后功能提交 2025-01-21 | 见 1.3 |

---

## 五、对 V-08 的回答

V-08 命题：**`saoxia/erpnext_china` 是否以自有 app + hook 形态实现了可用的中国本地化逻辑，且其实现方式可被本项目借用（许可证允许、v16 兼容或可移植）。**

命题是合取式，三个条件逐一核验：

| 条件 | 核验结果 |
|---|---|
| ① app + hook 形态 | **基本成立**。它是标准 Frappe app，靠 13 类 hook 接入，磁盘上未篡改上游源码。但 `after_install` 读取 17 个上游 workspace JSON 的硬路径依赖，不是干净的 hook 接入 |
| ② 实现了可用的中国本地化逻辑 | **对财税不成立**。科目表/增值税/发票/金税盘/财务报表/银行对账六项全为零。它实现的是中文 CRM + 中国 HR 字段 + 企业微信 + 汉化 + 行政区划 |
| ③ 可被本项目借用 | **不成立**。许可证状态矛盾（根 MIT vs 文件头 GPL v3）；只适配 v15 无 v16 证据；核心代码耦合了特定客户的 33727 条真实 PII 与硬编码员工编号、邮箱、中文枚举 |

**判定：no-go。**

「可用的中国本地化逻辑」按 V-08 的语境（本项目关心增值税专用发票、金税盘、银行对账、中国财务报表格式、中国会计科目表）衡量，该项目做到的是零。可借用的只有两份纯数据文件（行政区划 CSV、zh.csv），与财税诉求无关。

**同时要明确一点**：**V-08 不能为 V-01（不改 erpnext/frappe 源码即可接入中国本地化）提供实证支撑**，因为该项目没在财税方向做任何接入尝试，没有触碰 `get_charts_for_country()`、税码、Financial Statements 这些 V-01/V-03/V-04/V-06 真正关心的接入点。V-01 仍需由读 erpnext 源码的 Agent 回答。

---

## 六、复核建议

### 6.1 我拿不准的结论

1. **许可证的实际状态**。我看到的是：根 `license.txt` 为 MIT（版权行未填 `[year] [fullname]`）、`hooks.py` 声明 `app_license = "mit"`，但多个源文件头写 `# License: GNU General Public License v3`。我的判断是「从 erpnext 复制文件时未改文件头」，**但这是推断**。这些文件（`employee.py`、`lead.py`、`install_fixtures.py`）确实继承或复刻了 erpnext 的类实现，GPL 的传染性是否适用需法务判断，不是我能定的。若本项目真要引用其任何代码（包括我列为「可借用」的两份数据文件），**必须先解决这个问题**。

2. **`territory.csv` 与 `zh.csv` 的来源与授权**。两份我列为「可直接借用」的数据文件，我只确认了内容和格式，**没有确认它们是原创还是从第三方数据源取得**。zh.csv 9221 行「人工优化过的官方机器翻译」——官方翻译本身来自 frappe/erpnext（GPL v3）与 Crowdin 社区，衍生数据的授权状态我无法判断。

3. **v16 兼容性我只做了静态推断，没有实测**。依据是 Dockerfile 钉 `version-15`、README 只提 v14/v15、测试基类用 v15 的 `FrappeTestCase`。**我没有在 v16 环境里实际安装过它**，所以「直接安装会失败」是推断而非实测。若需要确切答案，应在 v16 起一个干净站点跑 `bench get-app` + `install-app`，重点看 6 个 `override_doctype_class` 的父类方法签名是否还对得上。

4. **`china_city_code.json` 是否真的缺失**。我在 `hrms_china/custom_form_script/employee/` 下没找到它，而 `employee.py:78` 会去读。可能是仓库确实漏了（则 `set_city_of_birth` 必崩），或被 `.gitignore` 排除（我查了 `.gitignore`，只有 `.DS_Store`、`*.pyc`、`*.egg-info`、`*.swp`、`tags`、`node_modules`、`__pycache__`、`erpnext_china/public/dist`，**不含此文件**）。倾向于「仓库漏提交」，但不排除我检索方式有遗漏。

5. **自建 `salary_slip` / `salary_component` / `leave_request` 与 hrms 官方同名 DocType 的实际共存行为**。我只确认了撞名事实，没有验证 Frappe 在两个 app 都定义同名 DocType 时的行为（后装覆盖？报错？）。

6. **`docker/` 的定位**。我判断它是「开发环境而非生产部署」，依据是单容器塞了全部服务 + `CMD ["/bin/bash"]` + `developer_mode: true` + 目录名 `images/development`。但作者是否另有未开源的生产部署方案，无法知道。

### 6.2 没看完的部分

1. **浅克隆的历史限制**。任务说明提到「浅克隆只有 50 层历史」，但我实测 `git log --oneline | wc -l` 返回 **117**，与仓库总提交数一致，即当前分支的全部提交都在。`git branch -a` 只有 `develop` 与 `origin/HEAD -> origin/develop`，**无 `main` 分支**。所以 `develop` 的历史我是完整的，但**如果 upstream 有我看不到的其他分支（如未推送的 main、已删除的 feature 分支），我没覆盖**。若需要，可 `git fetch --unshallow` 或去 GitHub 看分支列表确认。

2. **`old_system_data.py` 我没逐行读完**（34864 行）。我确认了它的结构（只有 `white_list` 与 `old_system_contacts` 两个顶层变量，在第 3、17 行）、统计了手机号数量（33727）与邮箱域名分布。**理论上文件深处可能还有别的内容我没看到**，但按 `^[a-zA-Z_]+ *=` 检索只有这两个赋值，可信度较高。

3. **`translations/zh.csv` 我只抽查了首尾与 grep 命中行**，没有逐条核对 9221 行译文的质量，也没有与 v16 的 source string 做全量比对。「能否在 v16 用」这个问题需要实际比对才能答。

4. **前端 JS 我读得较浅**。36 个 `.js` 文件，我只完整读了 `public/js/` 的目录结构与几个 `custom_form_script/*/*.js` 的 grep 命中。`crm_note.js`（3755 字节）、`form_button_permission.js`（1598 字节）等未逐行读。**但 grep 已确认全仓 js 无任何财税关键字命中，这个遗漏不影响主结论。**

5. **`.github/doc/企业微信登录配置说明.md` 我只读了前 30 行**，两张配图未看。不影响主结论。

6. **没有联网核对 GitHub 上的 issue / PR / star / fork 情况**。若需要判断社区活跃度或有无他人指出的已知问题，这部分是空白（我只看了本地 git 历史里的 PR 合并记录，来自 `ilqc`、`xuguim` 两个贡献者）。

### 6.3 README 与代码的出入（汇总）

已在 2.8 详述，此处汇总为三条：

1. **项目名 `ERPNext China Location（ERPNext中国本地化）` 名不副实** —— 财税本地化零实现。这是最主要的出入，但严格说是项目名而非 README 正文在误导：README 的 6 条功能列表本身没有承诺财税能力。

2. **README 描述的范围远小于代码实际范围** —— 未披露代码量最大的 CRM 线索自动分配（9 个 DocType + 991 行）、自制薪资单、百度/抖音线索对接、`old_system_data.py` 的 3 万条真实 PII。**未披露的恰恰是客户定制成分最重、最不可移植、且有合规问题的部分。** 只看 README 会严重低估引入这个 app 的代价。

3. **README 第 5 条「对 workspace 不支持 zh.csv 汉化的位置进行汉化」没说实现方式** —— 实际做法是 `after_install` 去读 17 个 frappe/erpnext 源码目录下的 workspace JSON、字符串替换、再全量 `save_page` 写入数据库（3.2）。README 未提示这会把 17 个标准 workspace 转成数据库自定义副本、此后不再跟随上游更新。**这是安装该 app 的一个隐性副作用。**

另有一处 README 与代码一致但需注意的：README 称 v14「理论兼容，未测试」—— 考虑到全项目零测试（4.1），**v15 的「已通过兼容测试」也只能理解为人工点测，无自动化证据支撑。**
