# P1-S2-R1-A 参考项目调研：zelin-tech/erpnext_china — 接入机制与代码质量

**调研对象**：`Reference/zelin-tech-erpnext_china/`（gitee.com/yuzelin/erpnext_china，51 提交，最新 `4d9c1c5 update translation for v16`）
**调研范围**：接入机制、上游污染、自建内容管理形态、代码质量、与 saoxia 同源性。**不含**财税能力盘点与翻译内容（另两份报告）。

## 一、hooks.py 全量盘点

`erpnext_china/hooks.py` 全文仅 52 行，**只用了 7 个 hook**（不含元数据），极其克制：

| hook | 用途 | 指向 |
|---|---|---|
| `after_install` | 装后初始化（语言/地区/字段标签/隐藏印度字段/流水码前缀） | `erpnext_china.setup.install.after_install` |
| `setup_wizard_requires` | 向安装向导注入 JS | `assets/erpnext_china/js/setup_wizard.js` |
| `app_include_icons` / `web_include_icons` | 注册 2 个 svg 图标 sprite（v16 新增 hook，见 `7f3c908 update icon path for v16`） | `public/icons/account_report.svg`、`cn_account_report.svg` |
| `doctype_js` | 表单级 JS 扩展（**非** `app_include_js`，作用域更窄） | Purchase Order / Sales Order / Sales Invoice 各一个 js |
| `override_whitelisted_methods` | 4 处，全部为科目表接入 | ↓ |
| `doc_events` | 仅 1 个 doctype（Company）3 个事件 | `erpnext_china.doc_events.company_before_insert` / `_on_update` / `_after_insert` |
| `jinja` | 打印模板可调用的方法 | `erpnext_china.print_utils`（金额中文大写等，7.4 KB） |

`override_whitelisted_methods` 的 4 项（全部指向 `chart_of_accounts/custom_accounts/custom_account.py`）：
- `erpnext...chart_of_accounts.get_charts_for_country` → 让"中国科目表"出现在可选列表
- `erpnext...chart_of_accounts.get_chart` → 返回自建 json 科目树
- `erpnext.accounts.utils.get_coa` → 科目表树形预览
- `frappe.desk.treeview.get_all_nodes` → 树视图节点（**唯一一处覆盖 frappe 核心方法**）

**明确未使用的 hook（逐项确认）**：
- `regional_overrides` — **未使用**。作者未走 ERPNext 为本地化预留的正规覆盖点（`erpnext/__init__.py:145`），而是用 `override_whitelisted_methods` + `doc_events` 达成目的。可能原因是其需求（科目表选单、公司默认值）恰好不在 20 个 `@allow_regional` 覆盖点之内。
- `override_doctype_class` — **未使用**（因此本报告第四节的反模式在此项目中不存在，见下）。
- `fixtures` — **未使用**（但 `fixtures/` 目录存在，见第三节）。
- `app_include_js` / `app_include_css` — 未使用（只用了 `doctype_js`，避免全局注入）。
- `after_migrate`、`scheduler_events`、`website_route_rules`、`permission_query_conditions`、`has_permission`、`on_session_creation`、`boot_session`、`doc_events` 中除 Company 以外任何 doctype — 均未使用。
- `patches.txt` **为空**（只有两个段落注释，无任何 patch 条目）。

## 二、是否污染或绕过上游

### 结论：当前 HEAD 无 monkeypatch、无上游文件写入。但它曾经有过，作者主动拆掉了

**搜索结果（全仓 .py/.js，排除翻译）**：
- `setattr` — **0 命中**
- `monkey` — **0 命中**
- `save_page` — **0 命中**
- `patches.txt` — 空
- 无 `.patch`/`.diff` 文件，README 无任何"手工改上游文件"的指示
- `open()` 8 处、`__file__` 拼路径 4 处，**全部读模式**，且全部读自有目录下的 csv/json（`default_accounts.csv`、`tax_template.json`、`tax_rule.csv`、`field_property.csv`、`example_data.json`）

### 一处需要点明的上游目录读取（与 saoxia 手法不同）

`chart_of_accounts/custom_accounts/custom_account.py` 两处用 `frappe.utils.get_bench_path()` 拼出
`apps/erpnext/erpnext/accounts/doctype/account/chart_of_accounts/` 并 `os.listdir` + `open()` 读上游科目表 json（`get_chart` :156、`get_charts_for_country` :197）。

与 saoxia 的差别（客观事实）：
- **只读，不写**，不入库，不生成上游对象的数据库副本，无"脱钩上游更新"的副作用；
- 这段逻辑是**复刻上游 `get_chart` / `get_charts_for_country` 的目录扫描部分**，为的是在结果里追加自有科目表。属于第四节反模式的同类写法（详见第四节）。
- 它也**同样用 `get_bench_path()` 拼 `apps/erpnext_china/...` 读自己的目录** —— 这是可疑处：app 读自己的资源本可用 `frappe.get_app_path()`，硬拼 bench 路径会在 app 目录名与 app 名不一致时失效。

### 历史：曾有完整 monkeypatch 框架，2026-03 整体移除

- `e2a62c0 add base_document monkey patches`（2026-01-07）引入 `erpnext_china/monkey_patches/`，共 5 个模块：`base_document.py`、`chart_of_accounts.py`、`core_data_exporter.py`、`core_data_import.py`（146 行）、`taxes_setup.py`。
- 加载方式相当激进：`__init__.py` 里 **包装 `frappe.connect`**（`frappe.connect = custom_connect`），每次连库时遍历**所有已安装 app** 的 `monkey_patches/` 目录并 `importlib.import_module` 逐个导入。即它不只 patch 自己，而是给整个 bench 建了一套隐式 patch 加载协议。
- `59752c1 去掉monkey patch`（2026-03-27）把这 5 个模块和 `frappe.connect` 包装全部删除，净减 319 行；原 `monkey_patches/data.py` 改名保留为 `print_utils.py`，改由 `jinja` hook 暴露；原 patch 承担的公司初始化职责改由新增的 `doc_events` `before_insert` + `override_whitelisted_methods` 承担。

**这是本报告最有价值的一条事实**：同一作者在真实项目里走完了"monkeypatch → 纯 hook"的迁移，并且迁移后 hook 集合反而更小（7 个 hook，一个 doctype 的 doc_events）。说明这类本地化需求确实可以在不 patch 上游的前提下落地。

## 三、自建内容的管理形态

### 自建 DocType（7 个，全在 `erpnext_china/erpnext_china/doctype/`）

| DocType | 性质 |
|---|---|
| Balance Sheet Settings | 单例设置（报表项↔科目号对照+公式） |
| Balance Sheet Settings Item | 上者的子表 |
| Profit and Loss Statement Settings | 单例设置 |
| Profit and Loss Statement Settings Item | 子表 |
| Cash Flow | 业务单据（现金流量表，直接法） |
| Cash Flow Item / Cash Flow Subtotal | Cash Flow 的两个子表 |
| Cash Flow Code | 主数据（现金流编码） |

另有 4 个自建 Report（`fin_balance_sheet`、`fin_profit_and_loss_statement`、`bs_and_pl_missing_account`，含 js/json/py）和 1 个自建 Workspace（`中国财务报表`，117 行 json，9 个 link）。

### Custom Field / Property Setter：三种形态并存，且有一个空洞

1. **`fixtures/` 目录里有 3 个 json**，但 **`hooks.py` 里没有 `fixtures` hook**（`git log -S"fixtures" -- hooks.py` 零命中，即从未有过），代码里也没有任何手动读 `fixtures/` 的逻辑。
   - `custom_field.json`：4 个 Custom Field（Account 上 `cash_flow_code`/`allow_all_party_type`，Customer/Supplier 各一个 `cash_flow_code`）
   - `property_setter.json`：49 个 Property Setter，覆盖 35 个 doctype，property 分布为 label 25 / hidden 8 / description 7 / default 3 / no_copy 2 / options 2 / in_list_view 1 / in_standard_filter 1
   - `cash_flow_code.json`：287 行现金流编码主数据
   - **客观后果**：无 `fixtures` hook 时，`bench migrate` 既不会安装这些 fixture，也不会在 `bench export-fixtures` 时回写。这 3 个文件在当前 HEAD 下是**死文件**，靠它们的功能（如 Cash Flow Item 上的 `cash_flow_code` 引用、Account 上的默认编码字段）需要装完后手工 Customize Form 补齐，除非另有装法（见复核建议）。这可能是漏配，也可能是作者刻意改为手工导入。

2. **`setup/field_property.csv` + `after_install` 代码建 Property Setter**（35 行，`install.py:100 change_field_property()`）。内容是流水码前缀改短（`SO-.YY.-` 等约 20 条）和字段标签/隐藏调整。形态是 **csv + 代码 insert**，非 fixtures、非 `custom/{doctype}.json`。

3. **未使用 `module/custom/{doctype}.json`**（`find -type d -name custom` 零命中）。即 Frappe 官方 Customize Form 内置的、按 doctype 分文件的托管形态在此项目完全没用上。

**与 saoxia 的形态对比**：saoxia 用 `module/custom/{doctype}.json` 管 65 field + 173 setter；zelin 用"无 hook 的 fixtures json + csv + after_install 代码"三条路，数量小（4 field + 49+ setter），但**没有任何一条是 migrate 自动生效的声明式形态**。

## 四、反模式排查（复刻上游方法体）

### 有，共 3 处，且已实测出一处真实失效

它不用 `override_doctype_class`，所以没有 saoxia 那种 `CustomEmployee.validate()` 复刻。但在
`chart_of_accounts/custom_accounts/custom_account.py`（254 行，**文件头保留的是上游 Frappe 版权声明**）里是同一个病灶：**整段复刻上游函数体再改**，而非"调上游再补"。

我用本机 `frappe-bench/apps/erpnext`（`__version__ = 16.35.0`）逐函数 diff 比对，结果：

1. **`erpnext_china_create_charts`（:20-88）复刻上游 `create_charts`（chart_of_accounts.py:13-76）。已因上游演进而失效：**
   - 上游把元数据字段列表抽成了 `get_chart_metadata_fields()`，并在其中**新增了 `account_category`**（v16 的 Account doctype 确有此字段，上游 73 个 verified 科目表中 4 个已在用）；复刻版仍是硬编码 7 项的 inline list，**没有 `account_category`**。客观后果有两层：
     - 过滤时不认 `account_category`，该键会被当作子科目名递归下去；
     - `identify_is_group()` 的副作用更直接——带 `account_category` 的叶子科目会因 keys 差集非空而被**误判为 is_group=1**。
     - **触发范围**：该项目自带的 4 个中国科目表 json 都不含 `account_category`（已 grep 确认），所以走"选中国科目表"主路径时不触发；触发条件是导入含该键的科目表，或上游后续给 cn_* 模板补上该键。
   - 上游 `account = frappe.get_doc({...})` 里已有 `"account_category": child.get("account_category")`，复刻版**没有这一行**，即该字段静默丢失。
   - 上游 `_import_accounts` 有 `nonlocal custom_chart`，复刻版删了；`account_currency` 的取值逻辑也从上游的 `if custom_chart else` 三元改成了 `or`（行为在 custom_chart 场景下不同）。
   - 复刻版把 `rebuild_tree` 包进了 `try/except` + `frappe.log_error`，**建账失败会被吞成日志而非抛错**（错误标题还写着已不存在的函数名 `create_charts2`）。
2. **`add_suffix_if_duplicate`（:90）和 `identify_is_group`（:103）被同时 import 又重新定义**（:12-17 从上游 import 了这两个名字，:90/:103 又本地重写，后者覆盖前者）。重写版同样停在 `get_chart_metadata_fields()` 抽取之前的旧写法。这种"import 了却影子覆盖"的写法让"用的是上游还是自己的"完全不可从调用点看出。
3. **`get_chart` / `get_charts_for_country`（:147 / :195）复刻上游的目录扫描段**，把 `os.path.dirname(__file__)` 换成 `get_bench_path() + apps/erpnext/...`，再追加自有目录扫描。`get_chart` 里对 `Standard` / `Standard with Numbers` 是委派回 `original_get_chart` 的（这部分做法正确），但非标准模板分支是复刻。

**唯一做对的一处**：`get_all_nodes`（:250）是真正的"薄包裹"——`tree_method = frappe.override_whitelisted_method(tree_method)` 后原样委派 `original_get_all_nodes`，5 行，零复刻。这是这套手法的正确形态。

## 五、代码质量与版本适配

### 版本适配：v16 已实际落地，但版本号自身是乱的

- `pyproject.toml` 的 `[tool.bench.frappe-dependencies]` 声明 `frappe >=15.0.0,<17.0.0`、`erpnext` 同，即**同时声明兼容 v15 与 v16**，未按 v16 收紧。`requires-python = ">=3.10"`。
- `erpnext_china/__init__.py` 里 `__version__ = '15.0.0'`（移除 monkeypatch 前是 `1.0.8`）。**app 自身版本号写成 15.0.0，与"适配 v16"的宣称对不上**，且近期有 5 个连续提交（`9ccb08d`→`85116f8`）都在反复调版本号，说明这里作者自己也在试。
- **确有 v16 专属适配**（非口头声明）：
  - `app_include_icons` / `web_include_icons`（v16 新增的 icon sprite hook），配 `7f3c908 update icon path for v16`；
  - `install.py:set_v16_icon()` 直接写 `Desktop Icon.logo_url` 和 **`Workspace Sidebar.header_icon`**（Workspace Sidebar 是 v16 的导航结构），且两处都用 `frappe.db.table_exists()` 先探测，属于 v15/v16 双版本兼容写法；
  - workspace json 加了 v16 要求的 `type` 字段（`da7ed8a 16版workspace中加了type字段`）；
  - `4fb31fc 修复trial balance参数变化的影响`——跟随了 v16 上游 report 签名变更。
- **残留 v15 写法**：4 个测试文件仍 `from frappe.tests.utils import FrappeTestCase`（v16 已迁到 `frappe.tests.UnitTestCase` / `IntegrationTestCase`，旧路径为兼容 shim）。另有 `45be544 convert db.sql to query builder`，说明作者主动把裸 SQL 迁到了 qb，现全仓无 `frappe.db.sql(` 命中。

### 测试：4 个文件，全部 9 行空壳，零有效测试

四个 `test_*.py` 各 9 行，函数体一律 `pass`，且版权头仍是脚手架生成的 `Copyright (c) 2023, Vnimy`。**与 saoxia 的 29 个 9 行空壳同构，只是数量更少。两个项目都没有任何可执行的回归测试。**

### CI：无

无 `.github/`、无 `.gitlab-ci.yml`、无 `.woodpecker`。**但有 `.pre-commit-config.yaml`**（pre-commit-hooks v5.0.0 + ruff v0.8.1 lint/format/import-sort + prettier），`pyproject.toml` 里 ruff 配置完整（line-length 110、tab 缩进、双引号、选了 F/E/W/I/UP/B/RUF）。即**有本地 lint 纪律、无服务端门禁**。

### 其他代码质量观察

- **TODO/FIXME/XXX/HACK 全仓 0 命中**，注释掉的大段代码几乎没有（1 处）。
- 但有一处**明确写坏的路径**：`fin_profit_and_loss_statement.py:359` 文档字符串里的调试片段 `from erpnext_china.erpnext_chinacounting.report...`（`erpnext_china` + `counting` 粘连，模块不存在）。在三引号里所以不会报错，但说明该调试块从未被复核，且里面还硬编码了作者自己公司名。
- **异常处理普遍是裸 `except:` + `frappe.log_error` 吞掉**：`install.py` 3 处（`set_china_default`、`change_field_property`、`set_v16_icon` 且最后一个是 `except: pass`）、`doc_events.py` 1 处、`custom_account.py` 建账树重建 1 处。客观后果是**装不上/建账不全时不报错，只在 Error Log 里留痕**，排障要去翻日志。
- `after_install` 整体包在 `if not frappe.is_setup_complete():` 下——**站点已完成初始化后再装此 app，全部中国默认值（UOM、语言、时区、币种、精度、流水码前缀）都不会生效**。
- 代码体量：3 个报表 py 共 1126 行（`fin_balance_sheet.py` 单文件 676 行），是本仓最重的部分。
- README 的"常见问题"只有一条，且是限制而非问题：与其它中文汉化/开箱即用 app **冲突，建议先卸载**。

## 六、与 saoxia-erpnext_china 是否同源

### 结论：**不是 fork，无共同祖先。同名是因为都用了 `bench new-app erpnext_china` 的脚手架。**

只读比对证据：

| 判据 | zelin | saoxia |
|---|---|---|
| remote | github.com/zelin-tech/erpnext_china（README 里给的安装源是 gitee.com/yuzelin/erpnext_china） | github.com/saoxia/erpnext_china |
| 提交数 | 51 | 117 |
| root commit | `921167d` "feat: Initialize App" | `9af9ffd` / `0c05812`（两个 root，有 merge 进来的独立历史） |
| 交叉对象测试 | 各自 `git cat-file -e` 对方 root commit **均 rc=1**（对象不存在） | 同 |
| 主要作者 | 余则霖(yuzelin) 39、Fisher Yu 7、丰茂德 3 | digitwise 53、ilqc 46、allen.xu 11 |
| publisher | `yuxinyong` | `Digitwise Ltd.` |
| modules.txt | `ERPNext China` | `ERPNext China` + `HRMS China` |
| hooks.py | 52 行，7 hook | 101 行 |
| 受版本控制的文件数 | 93 | 244 |

**19 个同路径文件里只有 `license.txt` 内容完全相同**（标准 MIT 文本）。其余同路径文件（README、pyproject、hooks、modules.txt、fixtures/custom_field.json、zh.csv）内容全不同；同名只因都是 `bench new-app` 生成的固定骨架文件（`__init__.py`、`templates/pages/__init__.py`、`.gitkeep` 之类）。

`zh.csv` 交集 319 行 / zelin 19350 行 / saoxia 9221 行，重合率约 3%，且这 319 行多为短词条，属独立翻译偶然撞车而非复制。

**有一条弱人员往来**：zelin 的 gitee PR `!2`（`10a3962`，2026-03-01）来自作者 **笑熬浆糊 <qinyanwan@qq.com>**，只改了 `zh.csv` 2 行；另 `allen.xu` 这个名字同时出现在 zelin 的 PR `!1`（翻译 bug fix）和 saoxia 的作者榜（11 提交）。**即两个项目的翻译贡献者圈子有重叠，但代码库无同源关系。**

**谁更新**：zelin 最新提交 2026-08-08（`4d9c1c5 update translation for v16`），且已有成体系的 v16 适配（icon hook、Workspace Sidebar）。saoxia 最新为 `666097b Update README.md`（本次只做同源判定，未核其日期与 v16 适配程度——saoxia 的详情见另一份已完成报告）。

## 复核建议

拿不准的：

1. **`fixtures/` 三个 json 到底怎么生效，未闭合。** 我确认了 `hooks.py` 无 `fixtures` hook（且 `git log -S` 证明从未有过）、代码里无手动读取。但这意味着 Custom Field `Account.cash_flow_code` 装不上，而现金流量表功能依赖它（README 也写"需预先设置现金流编码"）。两种可能未区分：(a) 确为漏配，用户需手工 Customize Form；(b) 我漏看了某个加载路径。**建议实装一次 `bench install-app` 后查 `Custom Field` 表验证**——这是唯一能定论的办法。
2. **第四节的 `account_category` 失效，是静态 diff 推断，未运行验证。** 我比对的是本机 `frappe-bench/apps/erpnext`（16.35.0），结论"带 `account_category` 的科目会被误判 is_group、且该字段静默丢失"在逻辑上成立，但**未实际跑一次建账来观察**。触发范围已 grep 收窄（其自带 4 个科目表不含该键，故主路径不触发），但"复刻上游方法体"这个结构性问题本身不受此收窄影响——下一次上游改 `create_charts` 仍会静默分叉。
3. **没看的部分**：`locale/zh.po` 与 `translations/zh.csv` 内容（按分工归另一 Agent）；财税能力（科目表 json 的会计准则符合度、税率模板、三张报表的公式正确性）均未评估；4 个 `public/js/*.js` 和 3 个报表的 js 只看了行数、未读逻辑；`print_utils.py`（7.4 KB，金额大写等）只确认了它由 `jinja` hook 暴露，未读实现。
4. **saoxia 一侧只做了同源判定**（remote / root commit / 作者 / 文件 md5 / zh.csv 交集），未复核其 v16 适配程度与最新提交日期，全程只读未改动。
5. **`get_bench_path()` 硬拼 `apps/erpnext_china/...` 读自有资源**这一条，我判断它在 app 目录名被改时会失效，但未验证 bench 是否强制目录名等于 app 名。若 bench 强制一致，该条只是风格问题而非缺陷。

## 交叉确认（应翻译 Agent 请求）

翻译 Agent 的假设是「zelin 可能靠改 workspace 标签或自定义科目表科目名，从结构上绕开官方两处撞名缺陷」。**两点都查了：假设不成立，但第二点的实际情况比"未回避"更值得记一笔。**

### 1. workspace 标签：未回避，照搬官方英文标签

唯一的 workspace 是 `erpnext_china/erpnext_china/workspace/中国财务报表/中国财务报表.json`（117 行）。只有 workspace 自身的 `label`/`title` 是中文（`中国财务报表`）；**内部两个 Card Break 的 label 是裸的英文 `Report` 和 `Settings`**（`content` 字段里的 `card_name` 同样是 `"Report"` / `"Settings"`），全部依赖运行时翻译。

即它**没有用「系统设置」「报表设置」这类加限定词的写法**。`Settings` 一旦被译成「设置」，这张页面上的分节名就与官方 `Setup` 译出的「设置」同名，撞名照旧。作者对 workspace 标签语言是有意识的（有一个提交 `9e891c8 workspace label use english` 专门把标签改成英文），但**动机是走翻译层、不是回避撞名**。

### 2. 中国科目表：撞名成因不同（与翻译无关），但同名父子结构确实存在于 2 / 4 张表

**官方缺陷 2 的成因是翻译层**：`Accounts Receivable`（group）与 `Debtors`（明细）两个不同英文源词译到同一个「应收账款」。**在 zelin 的 4 张科目表里，科目名是直接写死的中文字面量，不经翻译层**，所以"两个源词撞一个目标词"这条路径在它这里根本不存在——这是数据结构决定的，与 zh.csv 改不改无关。

但我顺手查了「父节点与子节点同名」这个结构本身（用官方缺陷 2 的同款症状去反查），结果是**存在，且不止应收**：

| 科目表文件 | 同名父子对 |
|---|---|
| `cn_norm_chart_of_accounts2024.json`（一般企业会计准则 2024） | **13 处**。含 `应收票据 > 应收票据`（11210 / 11211）、`应收账款 > 应收账款`（11220 / 11221）、`其他应收款 > 其他应收款`、`长期应收款 > 长期应收款`，另有固定资产、无形资产、在建工程、债权投资、长期股权投资、油气资产、生产性生物资产、其他应付款、长期应付款 |
| `cn_smes_chart_of_accounts2024.json`（小企业会计准则 2024） | 2 处：`生产性生物资产`、`无形资产` |
| `cn_cnpo_chart_of_accounts2025.json`（民间非营利组织 2025） | 4 处：`短期投资`、`存货`、`受托代理资产`、`受托代理负债`。**应收段反而是干净的**——父节点叫`应收款项`(1110)，下挂`应收票据`/`应收账款`/`其他应收款`/`坏账准备`，无同名 |
| `cn_sme_coa.json`（小企业会计准则） | **0 处**。应收段全是平铺叶子（`应收票据` 1121、`应收账款` 1122），无 group 层 |

**一处需要说清的差别**：这些同名父子**不会触发官方那种"子科目被追加数字 1"**。`add_suffix_if_duplicate` 的去重键是 `account_number + " - " + name.lower()`，而这些同名父子的科目号各不相同（如 11220 vs 11221），键不冲突，故不加后缀。**症状因此从"只差一个数字 1"变成"只差科目号前缀"**（下拉里 `11220 - 应收账款` 是 group、`11221 - 应收账款` 才能记账）。选错科目的风险形态仍在，但触发机制和表现都与官方缺陷 2 不同，且来源是科目表 json 自身、不是翻译。

**结论**：翻译 Agent 的两处缺陷在 zelin 项目里都**没有被结构性回避**。缺陷 1（Setup/Settings）在它的 workspace 上原样存在；缺陷 2 的翻译成因在它的科目表里不适用（中文字面量不过翻译层），但同名父子结构在 4 张表中有 3 张存在、`cn_norm_chart_of_accounts2024.json` 达 13 处。
