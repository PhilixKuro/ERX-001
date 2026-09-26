# S4-G2 官方 Frappe 系 app 的后端代码组织形态

- 缺口编号：G2
- 性质：针对性调查（只读，不改 Reference/ 与 frappe-bench/，无 git 操作）
- 日期：2026-09-27
- 命题：官方 Frappe 系 app 的「后端代码组织形态」是怎样的，本项目的中国财税模块能否照那样组织
- 结论提要：**官方做法与 ADR-0012「模块最少」在总体方向上反向**；但 ADR-0012 的立论链路本身**基本如实、缺一个决定性限定条件**。两件事要分开说。

## 版本前提（先读，否则下面的对照会误读）

| 对象 | 版本 | git HEAD |
|---|---|---|
| `frappe-bench/apps/frappe` | **16.34.0** | `c1f1e8e` 2026-09-15 |
| `frappe-bench/apps/erpnext` | **16.35.0** | `12cd563` 2026-09-15 |
| `Reference/hrms` | **17.0.0-dev** | `aa1ec5a` 2026-09-23 |
| `Reference/frappe-crm` | — | `2324bd9` 2026-09-23 |

⚠ **本次最关键的一条前提**：`Reference/hrms` 是 **17.0.0-dev**，它所针对的 frappe 与本地 16.34.0 **不是同一套侧栏机制**。

证据：`Reference/hrms/hrms/tests/test_sidebar_fixtures.py:26-28` 导入的是

```
frappe.desk.doctype.sidebar.convert_fixtures.export_path
frappe.desk.doctype.sidebar.sidebar.resolve_sidebar
```

而本地 frappe 16.34.0 **没有** `desk/doctype/sidebar/`（只有 `desk/doctype/workspace_sidebar/`、`workspace_sidebar_item/`、`sidebar_item_group/`），也**没有** `resolve_sidebar`／`sidebar_for_module`／`convert_fixtures`／`sync_module_defs` 这四个名字（全库 `grep -rn "def <name>"` 零命中）。

因此 hrms 同时**双份**发侧栏 fixture，两代机制各一份：

| 形态 | 路径 | 声明的 doctype | 对应框架版本 |
|---|---|---|---|
| v16（本地生效） | `hrms/workspace_sidebar/*.json`（app 级 9 份） | `"Workspace Sidebar"` | 16.x，由 `sync.py:120` 的 `app_level_folders` 导入 |
| v17（本地**不生效**） | `hrms/<module>/sidebar/<title>/<title>.json`（模块级 9 份） | `"Sidebar"` | 17.x |

⇒ 读 hrms 时凡遇 `sidebar/`、`resolve_sidebar`、`sync_module_defs` 的说法，**都属于 v17 语义，不能直接套到本项目当前的 16.34.0 上**。`test_sidebar_fixtures.py` 那段很详细的 docstring 描述的是 v17 行为。

## 一、官方 app 组织形态对照表

`modules.txt` 项数与 DocType 落点（DocType 数按目录数计；括号内为 `istable=0` 的非子表数）：

| app | `modules.txt` 项数 | 模块清单 | DocType 落点 | 有无普通包层 | py 分层 | 主要扩展键（条目数） | 加功能的主导方式 |
|---|---|---|---|---|---|---|---|
| **frappe-crm** | **3** | FCRM／Lead Syncing／Domain Enrichment | `crm/fcrm/doctype/` 39（29 非子表）<br>`crm/lead_syncing/doctype/` 5（4）<br>`crm/domain_enrichment/doctype/` 8（4） | **有，且重** `api/`(20 py)、`integrations/`(13)、`automation/`(6)、`permissions/`(3)、`overrides/`(2)、`extends/`(2)、`utils/`(1)、`patches/`(27) | 模块内只放 `doctype/`＋`workspace/`；跨切面代码全在普通包 | `doc_events`=29、`override_doctype_class`=2、`after_migrate`=5、`doctype_js`=5、`permission_query_conditions`、`has_permission`、`after_install`=1 | **自有 DocType 为主**（独立产品，不依赖 erpnext） |
| **helpdesk** | **1** | Helpdesk | `helpdesk/helpdesk/doctype/` 36（27） | 有：`api/`、`overrides/`、`extends/`、`integrations/`、`setup/`、`patches/` | 同上 | `doc_events`=18、`override_doctype_class`=3、`override_whitelisted_methods`=1、`after_install`=1、`after_migrate`=2 | 自有 DocType 为主 |
| **hrms** | **10** | HR Setup／Tenure／Recruitment／Shift and Attendance／Leaves／Expenses／Performance／Payroll／Tax and Benefits／HR | **仅 2 个目录**：`hrms/hr/doctype/` 117（81）、`hrms/payroll/doctype/` 43（25）<br>**另 8 个模块 0 个 DocType** | 有：`overrides/`(6 py)、`controllers/`、`mixins/`、`api/`、`regional/`、`utils.py` | `hr/` 与 `payroll/` 内还有 `report/`、`dashboard_chart/`、`number_card/`、`print_format/`、`notification/`、`web_form/`、`page/` | `doc_events`=39、`override_doctype_class`=4、**`regional_overrides`=3**、`doctype_js`=8、`override_doctype_dashboards`、`extend_bootinfo`、`app_include_js` | **覆盖上游为主**（唯一依赖 erpnext 的官方 app） |
| **insights** | **1** | Insights | `insights/insights/doctype/` 21（16） | 有：`api/`、`setup/`、`fixtures/`、`workbook_templates/` | 同上 | `doc_events`=1、**`fixtures`=1**、`after_install`=1、`after_migrate`=1、`app_include_js`、`standard_queries` | 自有 DocType 为主 |
| **raven** | **6** | Raven／Raven Messaging／Raven Channel Management／Raven Bot／Raven Integrations／Raven AI | **6 个目录各一份**：11／11／3／1／8／7（非子表 6／7／2／1／5／4） | 有：`ai/`、`api/`、`realtime/`、`scheduler/`、`patches/` | 同上 | `doc_events`=14、`after_install`=1、`app_include_js`、`extend_bootinfo`、`on_session_creation` | 自有 DocType 为主 |
| **flow** | **1** | Flow | `flow/flow/doctype/` 16（12） | 有：`api/`、`assistant/`、`knowledge/`、`lib/`、`memory/`、`tools/`、`triggers/`、`utils/` | 同上 | `doc_events`=5、`after_migrate`=1、`app_include_js`、`extend_bootinfo` | 自有 DocType 为主 |
| **erpnext**（本体，参照） | **21** | Accounts／CRM／Buying／… | 每模块一个 `doctype/` | 有：`controllers/`、`utilities/`、`regional/`、`patches/` | 模块内 `doctype/`＋`report/`＋`workspace/`＋`dashboard*/`＋`print_format/` | `doc_events`=22、**`regional_overrides`=6**、`override_whitelisted_methods`=1、`doctype_js`=5、`extend_bootinfo`=2 | 自有为主＋`regional_overrides` 做区域差异 |

**三条横向共性**

1. **每个 app 都有普通包层，且普通包比模块多。** 6 个 app 无一例外。命名高度收敛：`api/`、`utils/`、`overrides/`、`patches/`、`integrations/` 是通用词汇；`overrides/` 专放类覆盖实现（hrms `overrides/` 6 个 py 恰对应 `override_doctype_class` 的 4 项加 `company.py`、`dashboard_overrides.py`）。
2. **`modules.txt` 与目录结构可以完全解耦。** hrms 是铁证：声明 10 个模块，**只有 2 个目录装 DocType**，其余 8 个目录只有 `sidebar/`＋`workspace/`＋（app 级）`workspace_sidebar/`。即**模块可以是纯导航单位，不含任何代码**。
3. **`doc_events` 是压倒性主力**（5–39 条），`override_doctype_class` 是少数派（0–4 条），`override_whitelisted_methods` 极罕见（helpdesk 1、erpnext 1，hrms 把它整段注释掉了，见 `hrms/hooks.py:338-340`）。

**「整段替换上游流程」的实例**（第一部分第 4 问）

- **有，但是类覆盖而非整段替换**：`hrms/overrides/employee_payment_entry.py:21` `class EmployeePaymentEntry(PaymentEntry)` —— **继承**上游类再覆盖 `get_valid_reference_doctypes`、`set_missing_ref_details` 等方法，不是重写整个流程。
- **`regional_overrides` 才是真正的「函数级整段替换」机制**，而且是**框架内建的、给区域差异用的**。写入端 `erpnext/hooks.py:609-622`（France／UAE／Saudi Arabia／Italy 共 6 条）、`hrms/hooks.py:315-321`（India 3 条）；读取端 `erpnext/__init__.py:143-154` 的 `allow_regional` 装饰器：

  ```python
  overrides = frappe.get_hooks("regional_overrides", {}).get(get_region())
  function_path = f"{inspect.getmodule(fn).__name__}.{fn.__name__}"
  if not overrides or function_path not in overrides:
      return fn(*args, **kwargs)
  # Priority given to last installed app
  return frappe.get_attr(overrides[function_path][-1])(*args, **kwargs)
  ```

  `get_region()`（`erpnext/__init__.py:120-133`）取 `Company.country`，无 company 时回退 `frappe.flags.country` 或 System Settings 的 country。
- ⚠ **只有被 `@erpnext.allow_regional` 装饰过的上游函数才能这样替换**——这是一个**白名单机制**，不是任意函数都能覆盖。
- ⚠ **erpnext 现有 `regional_overrides` 里没有 China**（`grep -rni china erpnext/hooks.py erpnext/regional/` 零命中；`erpnext/regional/` 下有 australia／italy／south_africa／turkey／united_arab_emirates／united_states，**无 china**）。

**hrms 怎么挂 erpnext 的**（第一部分第 5 问，本项目 LG-101 风险的原型）

`hrms/hooks.py:180-186`：
```python
"Company": {
    "validate": "hrms.overrides.company.validate_default_accounts",
    "on_update": [
        "hrms.overrides.company.make_company_fixtures",
        "hrms.overrides.company.set_default_hr_accounts",
        "hrms.overrides.company.set_expense_claim_type_accounts",
    ],
```
即 **Company 一个事件挂 3 个 handler**，且都在普通包 `overrides/` 里而非某个模块内。加上 `override_doctype_class` 覆盖 `Employee`／`Timesheet`／`Payment Entry`／`Project` 四个上游 DocType 类（`hooks.py:162-167`）。**这正是本项目 `cn_tax` 的 Company 三钩子的官方先例。**

## 二、与 ADR-0012 的比对

### 结论：**总体反向，判据部分成立**

拆成两件事：

**(1) 「官方 app 倾向于少声明模块」——反向，证据确凿。**

| app | 模块数 | 装 DocType 的模块数 | 纯导航／纯代码模块数 |
|---|---|---|---|
| hrms | 10 | **2** | **8** |
| raven | 6 | 6 | 0 |
| frappe-crm | 3 | 3 | 0 |
| erpnext | 21 | 21 | 0 |
| helpdesk／insights／flow | 1 | 1 | 0 |

- 用户给我的「已知」里推测 **CRM 的 `modules.txt` 只有一项**——**这条是错的**。`Reference/frappe-crm/crm/modules.txt` 实有 **3** 项：`FCRM`、`Lead Syncing`、`Domain Enrichment`。那份 228 行旧调研记「39 个 DocType 全在 `crm/fcrm/doctype/`」本身没错（该目录确有 39 个子目录），但 CRM 另有 `lead_syncing/doctype/` 5 个与 `domain_enrichment/doctype/` 8 个，**旧调研漏了这两个模块**。
- hrms 走得最远：**为了导航而声明模块**，8 个模块零 DocType、只为挂一条侧栏。这与「模块数是界面成本、故要少声明」**方向完全相反**——hrms 把模块当作**界面收益**来用。

**(2) 「`modules.txt` 多一项 ⇒ 自动多一个 hammer 侧栏」——链路如实，但缺一个决定性限定，且实际后果比 ADR 设想的轻。** 详见第四节。

### 判据评估：「模块数是界面成本」在 16.34.0 下部分成立

成立的部分：`Module Def` 确实会被 `auto_generate_sidebar_from_module()` 逐个扫、确实会生成 `Workspace Sidebar` 并进 boot。

**ADR 未掌握的三条，每条都削弱「成本」的量级：**

1. **官方的规避办法是发一份同名 fixture，而不是不声明模块。** 守卫在 `workspace_sidebar.py:243`：
   ```python
   if not (frappe.db.exists("Workspace Sidebar", {"name": module, "for_user": None})):
   ```
   ⇒ 只要站上已有一条 `name == <模块名>` 且 `for_user IS NULL` 的 `Workspace Sidebar`，**该模块就不会生成 hammer 侧栏**。app 级 `workspace_sidebar/*.json` 正是干这个用的（`sync.py:120-127` 的 `app_level_folders` 导入）。这条守卫 ADR-0012 与架构文档 §3 均未记载。
2. **空模块的自动侧栏会被 boot 整条丢弃。** `boot.py:500-504`：
   ```python
   # A sidebar (and its desktop icon) is shown only if the user can see at least one
   # real item in it, i.e. a non-Section-Break item survived the per-item filter above.
   if not is_my_workspaces and not any(item["type"] != "Section Break" for item in items):
       continue
   ```
   ⇒ **一个纯代码模块（0 DocType／0 Report／0 Workspace／0 Dashboard／0 Page）产生的侧栏只含 Section Break，会在此处被 `continue` 掉，不进 boot。** 实测 erpnext 的 `Portal` 模块（0/0/0/0/0）即属此列。
3. **`hammer` 这个值在前端是死值。** 写入端 `workspace_sidebar.py:250` `sidebar.header_icon = "hammer"`；读取端 `sidebar_header.js:299-316`：
   ```js
   } else if (this.sidebar.sidebar_data) {
       this.header_icon = this.sidebar.sidebar_data.header_icon;      // 取到 "hammer"
       this.header_icon = frappe.utils.desktop_icon(this.sidebar.sidebar_title, "gray", "sm");
   }
   ```
   **下一行立刻覆盖**，改用 `desktop_icon()` 按标题首字母渲染字母块（`utils.js:1372-1393`，取 `label.charAt(0).toUpperCase()`）。全库 `grep -rn hammer public/js/` **零命中**，`--include=*.html` 亦零命中。⇒ **用户看到的不是锤子图标，而是模块名首字母的灰底字母块。** 「hammer 侧栏」这个说法在 16.34.0 的前端不成立（字符串确实在 boot payload 里，但不渲染）。

**综上：**「模块数是界面成本」这个方向没错，但**成本的真实形态**是「多一个按首字母渲染的侧栏条目，且仅当该模块至少有一个 DocType/Report/Workspace/Dashboard/Page 时才出现，且可用一份同名 fixture 消掉」。ADR-0012 据此否掉「按域分 6 个模块」的备选方案时，**高估了代价**：若那 6 个模块中有纯代码模块，它们本来就不会产出侧栏；若有内容，发 6 份 fixture 即可控住外观。

## 三、`cn_tax` 照官方形态会变成什么样

### 3.1 照 hrms 形态（最贴近的参照样本）

```
erx_core/
├── modules.txt                 # 声明：CN Tax / Reports / (可选) Demo …
├── hooks.py                    # 只接线：doc_events / override_* / after_install
├── cn_tax/                     # 模块①：出账（代码模块）
│   ├── doctype/                #   8 个 DocType
│   ├── report/                 #   3 个 Report
│   └── utils.py
├── cn_reports/                 # 模块②：报表（照 §3.1 拆分信号预留）
│   ├── report/
│   └── workspace/
├── overrides/                  # ★普通包：类覆盖与 doc_events handler 实现
│   ├── company.py              #   Company 三钩子（对标 hrms/overrides/company.py）
│   └── coa.py                  #   4 个 whitelisted 方法的覆盖
├── regional/                   # ★普通包：区域差异（对标 hrms/regional/india/）
│   └── china/
│       ├── setup.py
│       └── utils.py
├── api/                        # ★普通包：whitelisted 方法（演示操控等）
├── utils/                      # ★普通包
├── patches/                    # ★普通包
├── i18n/                       # ★普通包（本项目既有）
├── patches_mfg/                # ★普通包（本项目既有）
├── demo/                       # ★普通包（本项目既有）
├── workspace_sidebar/          # app 级 json：★每个模块发一份同名 fixture 压掉自动侧栏
│   ├── cn_tax.json
│   └── cn_reports.json
├── desktop_icon/               # app 级 json
└── fixtures/                   # app 级 json
```

关键差异只有两处是**形态性**的：

- **多一层 `overrides/`＋`regional/`**：把「覆盖上游」的实现从模块内挪到普通包，模块只留自有 DocType／Report。hrms、frappe-crm、helpdesk 三家都是这个分法。
- **每个模块配一份同名 `workspace_sidebar/*.json`**：这是官方压住自动侧栏的标准手法，也顺带把侧栏内容做成自己排的（而非按 `get_module_info()` 自动取前 3 个 DocType）。

### 3.2 与架构文档 §3.1 现状的差异表

| 维度 | 架构文档 §3 现状 | 照官方形态 | 差异性质 |
|---|---|---|---|
| `modules.txt` 项数 | **1**（`cn_tax`） | 1–2（`cn_tax`＋可选 `cn_reports`） | 反向（官方不忌讳多声明） |
| 覆盖位实现的落点 | `cn_tax` 模块内（§3.1 裁定「逻辑全在模块内」） | **普通包 `overrides/`** | **反向**：官方把覆盖实现放模块外 |
| 区域差异机制 | 未使用 `regional_overrides` | hrms／erpnext 都用 | **本项目未覆盖的一项**（见下） |
| 普通包数量 | 3（`i18n`／`patches_mfg`／`demo`） | 6–8（＋`overrides`／`api`／`utils`／`patches`／`regional`） | 同向，只是更细 |
| app 级 json 目录 | 2（`workspace_sidebar`／`desktop_icon`）＋`fixtures`／`module/custom` | 同 | 同向 |
| 侧栏 fixture 与模块的关系 | §3.5 只发「一份自有 title 侧栏」（23 环节业务流），**未按模块名发** | **每模块一份同名 fixture** | **本项目有一处遗漏**：见复核建议 (a) |

**⚠ 一处本项目当前方案会踩的实际后果**：架构文档 §3.5 的侧栏 json 用的是**自有 title**（23 环节业务流），而**不是** `name == "CN Tax"`。按 `workspace_sidebar.py:243` 的守卫（匹配 `name == 模块名`），这份侧栏**压不住** `cn_tax` 模块的自动侧栏。而 `cn_tax` 有 8 DocType＋3 Report，`boot.py:504` 的空判过不了 ⇒ **会实打实多出一条 "Cn Tax" 侧栏（首字母 C 的字母块）**。要消掉它，需另发一份 `name: "CN Tax"` 的 fixture。这与 ADR-0012 的目标（只多 1 个）一致，但**手段在现方案里缺位**。

### 3.3 官方做法对「报表拆第二个模块」这一拆分信号的参照价值

**有，而且是反向参照：官方不用「模块」来解决「接口数多」，而用「普通包」解决；模块只在需要一条独立侧栏时才加。**

三条实证：

1. **erpnext 的 `Accounts` 模块一个人装了 92 个非子表 DocType＋52 个 Report**，远超「接口 10 项」的量级，**并没有为报表另立模块**。它的做法是**一个模块配多份侧栏**：`Accounts` 这一个模块名下挂了 **8 份** `workspace_sidebar` fixture——`Accounts Setup`、`Banking`、`Budget`、`Financial Reports`、`Invoicing`、`Payments`、`Share Management`、`Subscription`、`Taxes`（均 `module: "Accounts"`）。⇒ **「报表要不要单独露出」在官方那里是侧栏问题，不是模块问题。** 本项目若只是想让财税报表与产能报表**在界面上分组**，发第二份侧栏 fixture 就够，不必加模块。
2. **反过来，hrms 为了导航而加模块**（8 个零 DocType 模块）。⇒ 模块在官方语汇里是**导航单位**优先于代码单位。
3. ⚠ **但 ADR-0012 备选方案②里那条理由仍然站得住**：「Report 的模块归属会体现在报表列表分组里」。`get_module_info()`（`workspace_sidebar.py:255-284`）按 `{"module": module_name}` 过滤 Report，`Report` 的 `module` 字段是真实分组依据。所以**若目标是报表列表里的分组**，那确实要靠模块；**若目标是侧栏里的分组**，靠 fixture 即可。**这两个目标 ADR-0012 没有区分**，NV-049 的论证混用了二者。

## 四、那条链路的核实结果

命题：**`modules.txt` 多一项 ⇒ 自动多一个 hammer 侧栏**。

### 判定：链路如实，但**缺一个决定性限定条件**，且末端表现与描述不符。

逐段核（写入端与读取端两侧都查）：

| # | ADR 引用 | 实际 file:line | 核实 |
|---|---|---|---|
| 1 | `__init__.py:899` | `frappe/__init__.py:899-901` `def get_module_list(app_name)` → `get_file_items(get_app_path(app_name, "modules.txt"))` | ✅ 行号精确 |
| 2 | `installer.py:749-755` | `frappe/installer.py:749-755` `def add_module_defs(app, ...)`：遍历 `get_module_list(app)`，逐个 `frappe.new_doc("Module Def").insert()` | ✅ 行号精确 |
| 3 | `workspace_sidebar.py:239-252` | `frappe/desk/doctype/workspace_sidebar/workspace_sidebar.py:239-252` `auto_generate_sidebar_from_module()` | ✅ 行号精确 |
| 4 | `boot.py:449-450` | `frappe/boot.py:449-450` `module_sidebars = auto_generate_sidebar_from_module()` / `workspace_sidebars.extend(module_sidebars)`；入口在 `boot.py:173` `bootinfo.workspace_sidebar_item = get_sidebar_items(allowed_pages)` | ✅ 行号精确 |

**四段行号全部如实。** 但有四条限定，前两条是 ADR 未掌握的机制、后两条影响「多一项就多一个」的字面正确性：

**(a) `frappe.db.exists` 守卫（`workspace_sidebar.py:243`）——最重要的一条**

```python
for module in frappe.get_all("Module Def", pluck="name"):
    if not (frappe.db.exists("Workspace Sidebar", {"name": module, "for_user": None})):
```
读取端确认 `for_user: None` 会编译成 `IS NULL`：`database/query.py:650` `if _value is None and isinstance(_field, Field):` → `:675 return _field.isnull()`（非 `!=` 分支）。
⇒ **发一份 `name == 模块名`、`for_user` 为 NULL 的 `Workspace Sidebar` 即可完全消掉该模块的自动侧栏。** erpnext 与 hrms 都靠这个。

**(b) 空模块的侧栏在 boot 被丢弃（`boot.py:504`）**

`create_sidebar_items()`（`workspace_sidebar.py:286-337`）对 `report` 分支**无条件**先加一个 `Section Break`（`:298-299`，`add_section_breaks("Reports", idx)` 不受 `len(items)` 约束，与 dashboard／page 分支的 `len(items) > 1` 不同）⇒ 零内容模块产出的 `items` **全是 Section Break** ⇒ 命中 `boot.py:504` 的 `continue`。
实测（按 `get_module_info()` 的 5 类实体逐模块盘点，DocType 依 `istable=0` 过滤、并依 `:283` 的 `doctype_limit = 3` 截断）：

- erpnext 21 个模块中，`Portal`（0/0/0/0/0）**唯一**会被丢弃；其余 20 个都有内容。
- frappe-crm：`Lead Syncing`（4 非子表 DocType）、`Domain Enrichment`（4）**都有内容，会各生成一条**。
- raven：6 个模块**全都有** DocType，**会生成 6 条**（`Raven` 自带 workspace 除外仍有 6 DocType）。
- hrms：10 个模块全都有内容（8 个纯导航模块各有 1 个 `Workspace`）。

**(c) `hammer` 在前端不渲染**（写入端 `workspace_sidebar.py:250`，读取端 `sidebar_header.js:310-311` 下一行即覆盖为首字母字母块；`grep -rn hammer public/js/` 零命中）。⇒ **「hammer 侧栏」名不副实**，实际是首字母灰底字母块。

**(d) `Module Def` 只在 `install_app` 时创建，`migrate` 不创建（16.34.0）**

`add_module_defs` 的**唯一**调用点是 `installer.py:345`（在 `install_app` 内）。全库 `grep -rn "add_module_defs"` 只有定义处与该调用处两条；`migrate.py` 的步骤序列（`:139-195`：`run_all(pre_model_sync)` → `sync_all()` → `run_all(post_model_sync)` → `sync_jobs` → `sync_fixtures` → `sync_standard_items` → `sync_dashboards` → `sync_customizations` → `sync_languages` → `remove_orphan_doctypes` → `remove_orphan_entities` → `delete_duplicate_icons`）**不含**创建 `Module Def` 的步骤；`patches/` 下亦无任何补丁创建它（`grep -rln 'add_module_defs\|new_doc("Module Def")' patches/` 零命中）。
⚠ ⇒ **在 16.34.0 上，往已装好的 app 的 `modules.txt` 里追加一项，`bench migrate` 不会为它建 `Module Def`**，该模块的 DocType 会因 `module` 外键指向不存在的 `Module Def` 而在导入时出问题。hrms 的 v17 测试 docstring 说「`Module Def` 行由框架的 `sync_module_defs` 在每次 migrate 时送达，app 新增模块不再需要自己写补丁」——**那是 v17 的行为，16.34.0 没有 `sync_module_defs`**。
⇒ 对本项目的直接含义：ADR-0012「`modules.txt` 可随时追加，现在预留无收益」这句在 16.34.0 下**有一个未登记的前提**——追加后需要 `bench install-app` 级别的动作或自写补丁，不是改一行 txt 就完事。**此条未实测**（只读推断，见复核建议 (c)）。

## 五、按规范 §2.2 的复核建议

### (a) 最弱环节／未覆盖什么

1. **全部结论都是读码结论，一次都没有在站点上实测。** 本项目已有七次「读码即判断」被推翻的记录。下列四条最该实测，各给了最小验证法：
   - **最该实测的一条**：`cn_tax` 单模块究竟会不会多出一条侧栏。验证法：装 app 后读 `frappe.sessions.get()['workspace_sidebar_item'].keys()`，看有无 `cn tax`。这直接决定 ADR-0012 的核心权衡是否还成立。
   - `hr_setup.json` 的 `for_user: ""` 是否真的落成 `""` 而非 NULL——**若落成 `""`，守卫 `for_user: None`（→`IS NULL`）就匹配不上，该模块仍会生成自动侧栏**。我查到的链路是：`import_doc`（`modules/import_file.py:234`）设 `doc.flags.ignore_validate = True`，而 `document.py:1407-1408` `if self.flags.ignore_validate: return` **会跳过 `before_save`** ⇒ `workspace_sidebar.py:48-51` 的 `before_save` 不执行。但 `""` 是否在别处被归一化成 NULL **我没查到确证**（`get_valid_dict` 只对 datetime 与 unique 字段做 `"" → None`，见 `base_document.py:566-567`，Link 不在内）。**这条我拿不准，见 (c)。**
   - `Shift & Attendance`／`Tax & Benefits` 两份 fixture 的 `name`（含 `&`）与 `module`（含 `and`）**不相等**，按 `:243` 的 `name == module` 守卫**匹配不上** ⇒ 这两个模块在 16.34.0 下**应当仍会生成自动侧栏**。hrms 的 v17 测试注释说 v17 靠 `sidebar_for_module` 走「模块自己的列」来解决，**16.34.0 没有这条路**。若本项目的模块名需要 `&`，会撞同一个坑。
   - 模块名 `CN Tax` 在 boot 里的键是 `sidebar_title.lower()`（`boot.py:507`）即 `cn tax`（**带空格**），而前端多处按 `.toLowerCase()` 取（`sidebar.js:670`、`:749`、`:767`，`utils.js:1321`）。大小写一致但**空格**是否影响路由匹配，未验。
2. **`regional_overrides` 这条路本次只查了机制，没查可行性。** 本项目 `cn_tax` 要覆盖的 4 个 whitelisted 方法（`get_charts_for_country`／`get_chart`／`get_coa`／`get_all_nodes`）**是否带 `@erpnext.allow_regional` 装饰器，我没有逐个核**。若带，则 `regional_overrides` 是比 `override_whitelisted_methods` 更正规的官方路；若不带，这条路走不通。**这是本次最该补的一个具体查证点，且很便宜**（4 次 grep）。
3. **只查了 `Reference/` 下的静态源码与 16.34.0 的框架源码，没查 `Reference/zelin-tech-erpnext_china`**（它是本项目 A 案的源码来源，其组织形态本可作第三方对照）。按约束，`Reference/saoxia-erpnext_china` 已跳过、未读取任何内容。
4. **`Module Def` 的 `restrict_to_domain` 机制没查**（`domain_settings.py:58` 会写这个字段）。若它能隐藏模块，可能是「多声明模块但不露出」的另一条路，本次未展开。

### (b) 你给我的「已知」里有错的

**有两处，都是实质性的。**

1. **「推测其 `modules.txt` 只有一项」——错。** `Reference/frappe-crm/crm/modules.txt` 实有 **3** 项：`FCRM`、`Lead Syncing`、`Domain Enrichment`。
   - 出处：`D:\ERX-001\Reference\frappe-crm\crm\modules.txt`
   - 旧调研「39 个 DocType 全在 `crm/fcrm/doctype/`」这半句**没错**（该目录确有 39 个子目录，29 个非子表），错在由此**推出**只有一个模块。CRM 另有 `crm/lead_syncing/doctype/`（5 个）与 `crm/domain_enrichment/doctype/`（8 个）。
   - ⚠ 补一条：这两个模块在本地副本里是**同一个 merge commit**（`2324bd9`，2026-09-23）引入的，`git log -- crm/modules.txt` 只有这一条记录——即该副本的 git 历史是浅克隆或压缩过的，**不能据此判断它们是新加的**。

2. **「`hammer` 侧栏」——这个说法在 16.34.0 的前端不成立。** `header_icon = "hammer"` 确实写进 boot payload（`workspace_sidebar.py:250`），但读取端 `sidebar_header.js:310-311` 在取到它后**下一行立即覆盖**为 `frappe.utils.desktop_icon(sidebar_title, "gray", "sm")`，渲染的是**模块名首字母的灰底字母块**（`utils.js:1372-1393`）。全库 `grep -rn hammer public/js/` 与 `--include=*.html` 均零命中。
   - 这不改变「多一条侧栏」的结论，但**改变了「用户看到什么」**——若 ADR-0012 的说服力部分来自「锤子图标很刺眼」，那个具体印象是不准的。

3. 另有一处**不算错、但需补限定**：ADR-0012 与架构文档 §3 都写「`modules.txt` 每多一项，`auto_generate_sidebar_from_module()` 就自动生成一个 hammer 侧栏进 boot」。**缺 `:243` 的守卫与 `boot.py:504` 的空判这两个限定**——加上它们后，正确表述是「每多一项**且该模块至少有一个 DocType/Report/Workspace/Dashboard/Page**、**且站上没有同名 `Workspace Sidebar`**，才多一条侧栏」。

### (c) 拿不准处

1. **`for_user: ""` 会不会落成空串**（从而使守卫失效）。我确认了 `before_save` 在 import 路径上被 `ignore_validate` 跳过（`import_file.py:234` + `document.py:1407`），也确认 `get_valid_dict` 的 `"" → None` 只覆盖 datetime 与 unique 字段（`base_document.py:566-567`）、Link 不在内。但**没找到**能证明 Link 空串一定入库为 `""` 的正面代码，也没跑过站点。**这条是本报告里唯一影响「守卫是否真的生效」的未决问题**，且 hrms 9 份 fixture 里只有 `hr_setup.json` 一份带 `for_user: ""`，其余 8 份根本没这个键（不带该键 ⇒ 字段为 None ⇒ 守卫正常匹配），所以**即使我的担心成立，影响面也只有 1 个模块**。
2. **16.34.0 下往既装 app 追加 `modules.txt` 项的实际后果**。我确认了 `add_module_defs` 只被 `install_app` 调用、`migrate` 不调用、无补丁调用，但**没有实测** `bench migrate` 后追加的模块会怎样失败（是 DocType 导入报错、还是静默跳过）。ADR-0012「可随时追加」这句的风险程度取决于此。
3. **`Reference/hrms` 是 17.0.0-dev，与本地 16.34.0 机制不同**——我据此把 hrms 的 `sidebar/`、`resolve_sidebar`、`sync_module_defs` 全部归为 v17 语义。但我**没有验证** hrms 17.0.0-dev 是否仍能在 16.34.0 上正常安装运行（它 `workspace_sidebar/` 那份 v16 fixture 的存在暗示可以，但这是推断）。**若本项目将来装 hrms，这是必须先实测的一条。**
4. **第三部分 3.1 的目录树是我按官方形态推演的，不是任何官方 app 的原样。** 其中 `regional/china/` 一项尤其**建议先验证第 (a).2 条**（4 个方法是否带 `@allow_regional`）再决定要不要这层。
5. **`Reference/flow`** 也有 app 级 `workspace_sidebar/flow.json`（`name`/`module` 均为 `Flow`，守卫可正常匹配）。它是 6 个参照 app 里除 hrms、erpnext 外**唯一**发这份 fixture 的，helpdesk／insights／raven／frappe-crm **都没发**——即这四家的模块**都在按自动生成的侧栏露出**。这条我没展开查（为什么它们不介意），可能说明自动侧栏的观感成本比 ADR-0012 设想的低。
