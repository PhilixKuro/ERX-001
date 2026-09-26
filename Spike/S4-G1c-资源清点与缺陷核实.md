# S4-G1c 资源清点与缺陷核实

调查对象：`Reference/zelin-tech-erpnext_china/erpnext_china/`
范围：第一部分 = `fixtures/` `public/` `templates/` `translations/` `locale/` `config/` 六目录；
第二部分 = 9 条已登记缺陷核实（不受目录限制、只读）。
不碰：`chart_of_accounts/` `setup/` 顶层散文件（G1a）、`erpnext_china/erpnext_china/`（G1b）。

本文件边查边写，**未标「已核实」的条目均为未完成**。

---

## 0. 目录物理清点（已核实，wc -l / stat）

| 文件 | 行数 | 字节 |
|---|---|---|
| fixtures/cash_flow_code.json | 287 | 10335 |
| fixtures/custom_field.json | 44 | 1318 |
| fixtures/property_setter.json | 492 | 16314 |
| public/.gitkeep | 0 | 0 |
| public/icons/account_report.svg | 22 | 1685 |
| public/icons/cn_account_report.svg | 24 | 1859 |
| public/js/purchase_order.js | 12 | 691 |
| public/js/sales_invoice.js | 12 | 687 |
| public/js/sales_order.js | 12 | 688 |
| public/js/setup_wizard.js | 31 | 1242 |
| templates/__init__.py | 0 | 0 |
| templates/pages/__init__.py | 0 | 0 |
| translations/zh.csv | 19350 | 1157708 |
| locale/zh.po | 179 | 4922 |
| config/__init__.py | 0 | 0 |

注：`public/` 计 7 个文件（`.gitkeep` + 2 svg + 4 js），**与任务书的 7 个一致**。
（本文件早期草稿曾误记为 6 个，已用 `find public -mindepth 1` 复核纠正。）

---

## 1. hooks.py 全文已读（已核实）

`Reference/zelin-tech-erpnext_china/erpnext_china/hooks.py` 共 52 行。要点：

- **L8 `app_license = "MIT"`** —— app 元数据声明 MIT。（与缺陷 9 相关）
- **无 `fixtures` 键** —— 全文 52 行不含 `fixtures`。这是缺陷 8 前半句的关键证据（待补读取端旁证）。
- L10 `after_install = "erpnext_china.setup.install.after_install"`（缺陷 8 后半句待核，install.py 属 G1a 范围但缺陷核实不受限）
- L12 `setup_wizard_requires = "assets/erpnext_china/js/setup_wizard.js"` ⇒ **public/js/setup_wizard.js 有消费方**
- L14-22 `app_include_icons` / `web_include_icons` ⇒ **public/icons 两个 svg 有消费方**
- L24-28 `doctype_js` ⇒ **public/js 三个 js（purchase_order/sales_order/sales_invoice）有消费方**
- L30-37 `override_whitelisted_methods` 4 条，含 `get_chart` / `get_charts_for_country` / `get_coa` / `get_all_nodes`（缺陷 5 相关）
- L39-45 `doc_events` Company 三个钩子
- L47-51 `jinja.methods = ["erpnext_china.print_utils"]`

---

## 2. 上游基准（已核实，读的是本项目实装的 v16）

`frappe-bench/apps/erpnext/erpnext/accounts/doctype/account/chart_of_accounts/chart_of_accounts.py`（共 291 行）

- **L281-291 `get_chart_metadata_fields()` 确为 8 键**，第 4 个是 `account_category`：
  `account_name, account_number, account_type, account_category, root_type, is_group, tax_rate, account_currency`
- 上游三处消费它：L26（`create_charts` 的排除表）、L93（`identify_is_group` 的集合差）、L236（`validate_bank_account`）、L261（`build_tree_from_json`）
- 上游 L50 建 Account 时**写入** `"account_category": child.get("account_category")`

`frappe-bench/apps/frappe/frappe/utils/error.py` **L44-49 `log_error` 签名（已核实）**：

```python
def log_error(title=None, message=None, reference_doctype=None,
              reference_name=None, *, defer_insert=False) -> "ErrorLog":
```

⇒ **首个位置参数确实就是 `title`**。`frappe/__init__.py:1609` 有 `from frappe.utils.error import log_error`，故 `frappe.log_error` 即此函数。

---

## 3. 缺陷 1（account_category 7 键 vs 8 键）：**成立，但登记的行号锚点错了**

zelin `chart_of_accounts/custom_accounts/custom_account.py` 两处硬编码 7 键、均缺 `account_category`：

- **L32-40**（`erpnext_china_create_charts._import_accounts` 的排除表）—— 登记册写的是「custom_account.py:52」，**L52 实为 `)`（report_type 三元表达式的收尾），不是那张表**。正确锚点是 **L32-40**。
- **L106-118**（本地重定义的 `identify_is_group` 的集合差）—— 登记册没提这处。

另：zelin L53-67 建 Account 的 dict **不含** `account_category`（上游 L50 有）⇒ 即便不抛错，该字段也丢失。

**AttributeError 的成因链（已核实代码路径，未跑站点实测）**：`account_category` 不在 L32-40 排除表内 ⇒ 若科目表 JSON 里出现该键，`_import_accounts` 会把它当成一个**科目名**来迭代，此时 `child` 是字符串（如 `"Asset"`）⇒ L41 `child.get("account_number")` ⇒ `AttributeError: 'str' object has no attribute 'get'`。
第二症状：L106-118 集合差非空 ⇒ `is_group` 被误判为 1。

---

## 4. 缺陷 2（log_error 首位置参误用）：**成立，6 处全部核实；但登记的 `:97` 锚点错了**

`custom_account.py` 6 处形如 `frappe.log_error(<位置参字符串>, title=<关键字参>)`：

| 行 | 所在函数 |
|---|---|
| L86 | `erpnext_china_create_charts` |
| L173 | `get_chart`（verified/unverified 循环）|
| L189 | `get_chart`（custom 循环）|
| L208 | `get_charts_for_country._get_chart_name` |
| L227 | `get_charts_for_country`（erpnext 路径）|
| L245 | `get_charts_for_country`（custom 路径）|

**6 个行号与登记册完全一致 ✓。** 报错机理更精确地说是：位置参已绑定 `title`，又传 `title=` 关键字 ⇒
`TypeError: log_error() got multiple values for argument 'title'`。

**登记册的「custom_account.py:97」是错的**：L97 是 `count = accounts.count(account_name_in_db)`，在
`add_suffix_if_duplicate` 里，**不是 log_error 调用点**。6 处最小行号是 L86。

**对照（新发现）**：`company_default/utils.py` 的 5 处 `log_error`（L38/59/84/103/178）都只传**一个位置参**、
不带 `title=` ⇒ **这 5 处没有这个 TypeError**。即该误用只在 custom_account.py 内。

---

## 5. 缺陷 6（裸 except 计数）：**部分成立——登记册的表述自相矛盾，事实是「4 裸 + 1 具名宽泛 = 5」**

`chart_of_accounts/company_default/utils.py`（177 行 + 末行无换行，故 grep 报到 L178）：

| 行 | 形态 | 是否裸 |
|---|---|---|
| L37 | `except:` | 裸 ✓ |
| L58 | `except:` | 裸 ✓ |
| L83 | `except:` | 裸 ✓ |
| L102 | `except:` | 裸 ✓ |
| **L177** | **`except Exception as e:`** | **不裸** |

登记册原话「裸 `except` 是 5 处而非 4 处……第五处是 `except Exception as e`」**自身即矛盾**：
`except Exception as e` 不是裸 except。准确说法应是「**吞掉一切的处理器共 5 处，其中 4 处裸、1 处具名**」。
四个裸 except 的行号 37/58/83/102 **与登记册一致 ✓**；第五处在 L177（`set_item_group_account`）**位置也对 ✓**。

附带（新发现）：L177 绑定的 `e` 在 L178 **从未被使用**，异常信息同样丢失，与裸 except 实际效果等同。

---

## 6. 缺陷 7（import 后本地重定义、影子覆盖）：**成立**

`custom_account.py`：

- **L12-17** 从上游 import 了 4 个名字：
  `get_chart as original_get_chart`、**`add_suffix_if_duplicate`**、**`identify_is_group`**、`get_account_tree_from_existing_company`
- **L90 `def add_suffix_if_duplicate(...)`** —— 同名模块级重定义
- **L103 `def identify_is_group(child)`** —— 同名模块级重定义

`def` 在 import 之后执行，故模块全局里这两个名字**最终指向本地版本**；L42／L46 的调用点在函数体内、运行期按模块全局解析 ⇒ **实际调用的是本地版，上游那两个 import 成了死 import**。

**与缺陷 1 复合**：本地 `identify_is_group`（L106-118）把 7 键写死，所以**即便上游改成 8 键也压不过来**——
影子覆盖正是让缺陷 1 无法靠升级上游自愈的原因。

---

## 7. 缺陷 9（许可证不一致）：**成立**

- `erpnext_china/chart_of_accounts/custom_accounts/custom_account.py` **L1-2**：
  `# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors` /
  `# License: GNU General Public License v3. See license.txt`
- 仓库根 `license.txt` **L1 `MIT License`**（正文为标准 MIT，且 L3 占位符 `Copyright (c) [year] [fullname]` 未填）
- `erpnext_china/hooks.py` **L8 `app_license = "MIT"`**

⇒ 文件头声明 GPL v3、而它所指的 `license.txt` 是 MIT，app 元数据也报 MIT。**三者不一致，已核实。**
该文件正是 `get_chart` / `get_charts_for_country` 的所在（hooks.py L30-37 的 4 条
`override_whitelisted_methods` 有 3 条指向它）⇒ 「建公司能选到中国科目表」确实依赖此文件。

---

## 8. 缺陷 5（get_chart 全不匹配返回原始文件文本）：**成立，且比登记册描述的更糟**

已用可执行仿真核实（`Spike/S4-G1c-getchart-sim.py`，纯 python 复刻控制流、不碰站点、不导 frappe）。

**代码差异（已核实）**：

- 上游 `erpnext/.../chart_of_accounts.py` `get_chart()` L102-131：else 分支循环结束后**没有任何 return**
  ⇒ 函数体末尾坠落 ⇒ 返回 **`None`**。（L103 那个 `chart = {}` 其实是死初始化，上游从不返回它）
- zelin `custom_account.py` `get_chart()` L152-191：**L191 多了一句 `return chart`**。
  而 **L169 `chart = f.read()` 已把 `chart` 从 `{}` 重绑成 str**，每轮循环覆盖一次
  ⇒ 全不匹配时返回的是**最后一个被读到的 json 文件的整篇原文**。

**实测输出**（对本机真实 `verified/` 目录，73 个 json，问一个不存在的模板名 `小企业会计准则`）：

```
ZELIN    get_chart -> str  | truthy: True  | len: 56761
  首 90 字符: '{\n    "country_code": "tw", \n    "name": "Taiwan - Chart of Accounts", \n    "tree": {...'
UPSTREAM get_chart -> NoneType | truthy: False
```

⇒ 返回的是 **`tw_chart_of_accounts.json`（台湾科目表）的 56761 字符全文**（`verified/` 按字典序最后一个 json）。

**这比「抛 AttributeError」更坏，关键在真假值**：

| | 上游 | zelin |
|---|---|---|
| 返回值 | `None` | 56761 字符的 str |
| `if chart:` | **False ⇒ 安全短路** | **True ⇒ 穿过守卫** |
| 随后 `.items()` / `.get()` | 走不到 | **AttributeError** |

已核实的两个受害调用点：

- `custom_account.py:23-24` `chart = custom_chart or get_chart(...)` ⇒ `if chart:`（L24）**被 str 骗过** ⇒
  L28 `children.items()` ⇒ `AttributeError: 'str' object has no attribute 'items'`
- `custom_account.py:136` `chart_data = get_chart(chart)` ⇒ L139 传给上游 `build_tree_from_json`；
  上游该函数 L252 `if not chart: return` 同样**被 str 骗过** ⇒ L259 `children.items()` 炸

**登记册说「调用方 `.get()` 抛 AttributeError」**——方向对，但更准确的首爆点是 **`.items()`**（L28／上游 L259）；
`.get()` 是在递归进去以后才炸。两者都实测复现（见脚本输出末段）。

**「抄 zelin 时必须一并修的第二处」这个判断成立**：因为上游靠「返回 None ⇒ `if chart:` 短路」来兜底，
zelin 的 `return chart` 把这条兜底拆了。

---

## 9. 缺陷 8：**前半句「fixtures 是死文件」不成立（推翻）；后半句成立**

### 9.1 前半句：`fixtures/` 三个 json **有消费方**，不是死文件 —— 已核实

登记册的推断链应是「hooks.py 没有 `fixtures` 键 ⇒ 没人读」。**这条推断错了。**

**写入端（已核实）**：`hooks.py` 全文 52 行**确实没有 `fixtures` 键**（两种工具独立确认：`grep -rn fixtures`
在 zelin 全仓只命中 `translations/zh.csv:13594` 的一条译文 `Furniture and Fixtures,家具及固定装置`）。

**读取端（已核实，这是关键）**：`frappe-bench/apps/frappe/frappe/utils/fixtures.py`

```python
32  def import_fixtures(app):
33      fixtures_path = frappe.get_app_path(app, "fixtures")   # 目录路径，不看 hook
34      if not os.path.exists(fixtures_path):
35          return
36
37      fixture_files = sorted(os.listdir(fixtures_path))      # 直接列目录
39      for fname in fixture_files:
40          if not fname.endswith(".json"):
41              continue
43          file_path = frappe.get_app_path(app, "fixtures", fname)
45          import_doc(file_path, sort=True)
```

⇒ **导入端 `import_fixtures` 根本不读 `fixtures` hook，它 `os.listdir` 整个目录。**
`fixtures` hook（`fixtures.py:75 frappe.get_hooks("fixtures", ...)`）只在
**`export_fixtures`（L67-114，导出方向）** 里用，另外 `translate.py:368/433` 用它找 Workflow/Custom Field 抽译文。

**调用链（已核实）**：`frappe/installer.py:294 install_app()` → **L367 `sync_fixtures(name)`**
（位置在 L360-361 的 `after_install` 钩子**之后**）→ `fixtures.py:16 sync_fixtures` → L26 `import_fixtures(app)`
→ `os.listdir` → `import_doc`（`data_import.py:350`，`.json` 逐个 `import_file_by_path(force=True)`）。
另一条：`frappe/migrate.py:171 sync_fixtures()`（每次 `bench migrate` 都全量重跑）。

⇒ **只要 app 被 `bench install-app` 装上，这三个 json 必然被导入，与 hooks.py 无关。**

**三个 json 的内容与其下游消费方（已核实）**：

| 文件 | doctype | 条数 | 下游读取端 |
|---|---|---|---|
| `fixtures/cash_flow_code.json` | `Cash Flow Code` | 22 | 该 doctype 存在于 `erpnext_china/erpnext_china/doctype/cash_flow_code/`；`cash_flow.py:43,201` `frappe.get_all('Cash Flow Code', ...)` 读它 |
| `fixtures/custom_field.json` | `Custom Field` | 4 | `Account.cash_flow_code`／`Customer.cash_flow_code`／`Supplier.cash_flow_code`／`Account.allow_all_party_type`；`cash_flow.py:179-231` 读 `cash_flow_code` |
| `fixtures/property_setter.json` | `Property Setter` | 49 | 首条即 `Account-root_type_options`，把 `root_type` 选项扩出 `Common Accounts`（中国「共同类」科目所需）|

⇒ **这三个不是死文件，是「中国现金流量表 + 共同类科目」这条功能线的数据底座。**

**但本项目的情形不同（这是判定的真正依据）**：已定「zelin 素材**并入式抄源码、不装 app**」。
`import_fixtures` 的入口 `frappe.get_app_path(app, "fixtures")` 里 `app` 来自
`frappe.get_installed_apps()`／`install_app(name)` ⇒ **只对「被安装的 app」生效**。
本项目自有 app 是 `erx_core`，故这三个 json 若要生效，**必须挪到 `erx_core/fixtures/` 下**才会被
`sync_fixtures('erx_core')` 扫到。**判定因此是「抄后改（换落点）」，不是「不抄（死文件）」。**

### 9.2 后半句：`after_install` 整体包在 `if not frappe.is_setup_complete():` 下 —— **成立**

`Reference/zelin-tech-erpnext_china/erpnext_china/setup/install.py`（140 行）：

```python
54  def after_install():
55      if not frappe.is_setup_complete():
56          set_china_default()
57          set_v16_icon()
```

⇒ **函数体只有这一个 if，没有 else、没有后续语句**，`set_china_default()`（UOM 46 个 / 语言 zh /
Global Defaults / System Settings / Property Setter）与 `set_v16_icon()` **全部**在守卫之下。

`frappe/__init__.py:1537 is_setup_complete()` 判据（已核实）：
`Installed Application` 表里 `app_name in ("frappe","erpnext")` 的 `is_setup_complete` **全为真**即返回 True。

⇒ **站点已过 setup wizard 后再装此 app，`after_install` 静默什么都不做**，中国默认值全不生效。**成立。**

补充（已核实，登记册未提）：`fixtures` 的导入**不受这个守卫影响**——`installer.py:367 sync_fixtures(name)`
在 `after_install` 钩子（L360-361）之后**无条件**执行。所以「装晚了」的后果是**分裂的**：
三个 fixtures json 照样进库，而 UOM／System Settings／Property Setter 全部丢失。

---

## 10. 缺陷 1／2 的可执行复现（`Spike/S4-G1c-defect12-sim.py`，纯 python、不导 frappe）

用 **v16 真实签名**复刻，输出：

```
[zelin custom_account 风格] log_error("msg", title="T")
  -> TypeError: log_error() got multiple values for argument 'title'
[zelin utils.py:38 风格]   log_error("single")  -> title='single', message=None   # 不报错
missing from zelin: {'account_category'}
  [zelin7] 把 'account_category' 当成子科目 -> AttributeError: 'str' object has no attribute 'get'
  [upstream8] set(child)-set(table) = set()            -> is_group = 0
  [zelin7]    set(child)-set(table) = {'account_category'} -> is_group = 1
```

⇒ 缺陷 1、2 的**故障机理均已可执行复现**（非仅代码推理）。

### 10.1 缺陷 1 的**可达性**：中国科目表走不到，`Standard` 走得到（已核实，这是登记册缺的一环）

扫了所有科目表里 `account_category` 键的出现（`Spike/S4-G1c-trigger.py`）：

| 科目表 | `account_category` 节点数 |
|---|---|
| `verified/in_standard_chart_of_accounts.json`（印度）| **56** |
| `verified/standard_chart_of_accounts.py`（Standard）| **73 处** |
| `verified/standard_chart_of_accounts_with_account_number.py` | **74 处** |
| 其余 72 个 verified json | 0 |
| **zelin 四个中国科目表**（`cn_sme_coa.json`／`cn_smes_...2024`／`cn_norm_...2024`／`cn_cnpo_...2025`）| **全为 0** |

⇒ **结论分两层（重要）**：

1. **建中国公司这条主路不会触发缺陷 1** —— 四个中国科目表里没有 `account_category` 键。
2. **但 `Standard` / `Standard with Numbers` 会** —— 而 `custom_account.py:149-150` 对这两个模板
   **直接转发给 `original_get_chart`**，返回的 dict **来自上游那 73/74 处带 `account_category` 的 py 文件**；
   随后 `doc_events.py:21` 仍调 **zelin 自己的 `erpnext_china_create_charts`**（L32-40 的 7 键表）去建账
   ⇒ **选 Standard 建公司时会踩**。印度科目表同理。

**这修正了登记册的隐含定性**：缺陷 1 不是「建中国公司必炸」，而是
「**建中国公司不炸、建 Standard／印度公司炸**」。`account_category` 字段丢失（zelin L53-67 建 Account 的
dict 不含它）则**对所有科目表都成立**。

---

## 11. `translations/zh.csv` 实际情况（已核实，两套工具交叉验证）

脚本：`Spike/S4-G1c-verify.py`／`-cov3.py`／`-cov4.py`／`-cov5.py`。
PO/MO 解析用 **bench 自带的 babel 2.16.0**（`frappe-bench/env/lib/python3.14/site-packages`，纯 python、只读导入），
与我手写的解析器结果互相印证。

### 11.1 规模

| 指标 | 数值 |
|---|---|
| 字节 | 1 157 708 |
| LF 换行数 | **19 350**（`wc -l` 报的就是这个）|
| `csv.reader` 解析出的**记录**数 | **18 332**（差额源于译文里含换行的引号字段）|
| 2 列行 / 3 列行 | 18 300 / 32（3 列 = 带 context）|
| 可用键值对 | 18 331 |
| **去重后唯一源串** | **18 296** |
| 重复源串 | 35 |
| 空译文 | 0 |

**「18297」这个已知数字差 1 的确切原因（已定位）**：CSV **第 10511 行的键是两个空格** ——
`['  ', 'If enabled']`。按「非空白键」过滤得 **18296**，把这个空白键也算进去正好 **18297**。
⇒ 你给的 18297 不算错，是**没过滤掉一个空白键**；干净口径是 **18296**。

### 11.2 与官方 zh 译文的关系 —— **「仅 748 条覆盖官方」这个说法要纠正**

v16 官方 zh 译文的**运行时**来源是编译后的 mo：`frappe-bench/sites/assets/locale/zh/LC_MESSAGES/{frappe,erpnext}.mo`
（源文件 `apps/{frappe,erpnext}/{frappe,erpnext}/locale/zh.po`；**v16 两个 app 都已无 `translations/` 目录**）。

| 对照口径 | 数值 |
|---|---|
| 官方 zh 已译条目（frappe 5933 + erpnext 8412，去重）| **14 330** |
| zelin 18296 条中**官方已有该源串**的 | **14 262** |
| ├ 其中译法**完全相同** | **13 513** |
| └ 其中译法**不同**（撞译名）| **749** |
| zelin 独有、**官方完全没有 zh 译文**的 | **4 034** |

（按 po 口径而非 mo 口径：官方 universe 16 445、重叠 15 994、不同 2 481、独有 2 302。
差异来自 po 里有 2 115 条 msgid 尚未翻译；**运行时以 mo 为准**，故上表是有效口径。）

**⇒ 「zelin 18297 条译文里仅 748 条覆盖官方」是错的，数字与方向都要改**：
- **覆盖官方的是 14 262 条（78%），不是 748 条。**
- **748（精确 749，严格不 strip 则 750）实际是「官方已有但 zelin 译法不同」的撞车条数** ——
  即「**需要人工裁决的冲突数**」，不是「覆盖数」。这个数字被安到了相反的语义上。

### 11.3 能当词汇素材的部分

- **4 034 条**：官方无 zh 译文，**纯增量**，是最有价值的素材（含中国财税专有词）。
- **749 条**：官方已有但译法不同，**需逐条人工裁决**（zelin 更符合中国会计习惯 vs 官方术语一致性）。
- 13 513 条：与官方逐字相同，**抄过去等于零增益**，且会在 `erx_core/translations/zh.csv` 里
  堆 13 513 行噪音、掩盖真正的改动。
- 合计可议素材 **4 783 条**（4034 + 749），约占 26%。

### 11.4 与 ADR-0006 的关系（已核实 ADR 原文）

`docs/01-需求摸底/0-P1文档/ADR-0006-译名全走csv单一来源.md`：译名**全走 `erx_core/translations/zh.csv` 单一来源**。

- 本站点 `frappe-bench/sites/apps.txt` 只有 **`frappe` 与 `erpnext`**（已核实，无换行分隔的两行），
  且 `erx_core` **在磁盘上尚不存在**（全仓 `find -name "erx_core*"` 无命中）。
  `translate.py:190-193` 的 csv 路径按 **已安装 app** 拼 ⇒ **zelin 那份 csv 在本站点完全不生效，已核实。**
- 故 zelin `translations/zh.csv` **只能当词汇素材**，判定 **不抄（整份）**，仅从上述 4 783 条里择取。
- **ADR-0006 的硬纪律直接否掉 zelin 的 `locale/zh.po`**：「自有 app 内只放 csv、不放 po、不生成 mo」，
  因为同 app 内装载次序是先 csv 后 mo（`translate.py:180-181`，已核实原文）⇒ 自有 app 一旦有 mo 就盖掉自己的 csv。
  ⇒ `locale/zh.po` **判不抄**；其 56 条 msgid 若有价值，**转写成 csv 行**并入单一来源。

---

## 12. `locale/zh.po` 实际情况（已核实）

- **56 条 msgid**，全部已译，**无 PO header**（babel 读出 `locale=None`）⇒ 不是 `bench` 正规导出的产物，是手写拼的。
- **无 `main.pot`**、**全仓无任何 `.mo`**（已核实）⇒ 这份 po **从未被编译**，故**当前在 zelin 自己那边也不生效**
  （`translate.py:180-181` 只读编译后的 mo，不读 po）。
- 引用注释暴露来源：**`hrms/` 2 条、`erpnext/` 3 条、51 条无注释** ⇒ 含 **HRMS**（本项目未装）的词条。
- 与官方运行时 zh.mo 重叠 39 条、po 独有 17 条。
- **56 条全部已存在于 zelin 自己的 `translations/zh.csv` 里，且译法完全一致（0 处分歧）** ⇒ **这份 po 是 csv 的子集副本，纯冗余。**

⇒ **判定「不抄」**：① ADR-0006 硬纪律禁止自有 app 放 po；② 内容是 csv 的真子集，零增量；③ 含 HRMS 词条。

---

## 13. 第一部分清点表（15 个文件）

目标落点一律指自有 app `erx_core`（**磁盘上尚不存在**，已核实 `find -name "erx_core*"` 无命中）。

| 文件路径（相对 `Reference/zelin-tech-erpnext_china/erpnext_china/`）| 类型 | 行数 | 判定 | 目标落点 | 抄后要改什么 | 依据 |
|---|---|---|---|---|---|---|
| `fixtures/cash_flow_code.json` | 数据 fixture，22 条 `Cash Flow Code` | 287 | **抄后改** | `erx_core/fixtures/cash_flow_code.json` | 落点必须在**被安装的 app** 下才会被 `sync_fixtures` 扫到；依赖 `Cash Flow Code` doctype 一并抄（G1b 范围）；`modified` 时间戳可留 | `frappe/utils/fixtures.py:32-45` `os.listdir` + `installer.py:367` |
| `fixtures/custom_field.json` | 4 条 `Custom Field` | 44 | **抄后改** | `erx_core/fixtures/custom_field.json` | 同上落点；4 个字段挂 `Account`／`Customer`／`Supplier`，`insert_after` 锚点须对 v16 复核；`Account.cash_flow_code` 的 `options` 依赖 `Cash Flow Code` doctype 先存在 | 同上；`cash_flow.py:179-231` 读该字段 |
| `fixtures/property_setter.json` | 49 条 `Property Setter` | 492 | **抄后改** | `erx_core/fixtures/property_setter.json` | ① **删掉重复的 `Account-root_type_options`**（见新发现 N-1）；② `root_type` 加 `Common Accounts` 这一改**上游 v16 不认**（见 N-2），需决策；③ 25 条是 `label` 覆盖，与 ADR-0006 的 csv 译名单一来源**职责重叠**，须逐条裁决走 csv 还是走 Property Setter | 同上；`erpnext/.../account.py:191` |
| `public/icons/account_report.svg` | 前端图标（裸 svg，**无 `<symbol>`**）| 22 | **抄后改** | `erx_core/public/icons/` | 作为 `Desktop Icon.logo_url` 的图片路径可用；**但放进 `app_include_icons` 无意义**（见 N-3）；路径里的 `/assets/erpnext_china/` 须改成 `/assets/erx_core/` | `frappe/hooks.py:40`、`jinja_globals.py:113-128`、`icon.js:13` |
| `public/icons/cn_account_report.svg` | 图标精灵（含 1 个 `<symbol id="icon-cn-account-reporting">`）| 24 | **抄后改** | `erx_core/public/icons/` | 同上改 assets 路径；`id="frappe-symbols"` 与 frappe 自带文件**撞 DOM id**（见 N-3）；symbol id 与 `install.py:138` 写入的 `cn-account-reporting` 对得上（`icon.js` 去掉 `icon-` 前缀）**已核实一致** | 同上 |
| `public/js/purchase_order.js` | Client script（改按钮文案）| 12 | **不抄** | — | **不是 CRM/企微资源**（见复核建议 b）。作用是把「创建 > 付款」下拉项文案改成「预付款」。实现方式是 `setTimeout(200)` + jQuery 抓 `data-label` 的 DOM，**与 frappe 内部 DOM 结构和英文原 label 双重强耦合**（`page.js:644` 用 `encodeURIComponent(label)` 生成）⇒ 脆。同一诉求应走 ADR-0006 的 csv 译名 | `frappe/public/js/frappe/ui/page.js:567-656` |
| `public/js/sales_order.js` | 同上（→「预收款」）| 12 | **不抄** | — | 同上 | 同上 |
| `public/js/sales_invoice.js` | 同上（→「收款」）| 12 | **不抄** | — | 同上 | 同上 |
| `public/js/setup_wizard.js` | 覆盖 setup wizard 预填 | 31 | **不抄** | — | 整体覆盖 `frappe.setup.utils.load_prefilled_data`（上游 `setup_wizard.js:540-570`）。与上游唯一实质差异：上游 `language = values.language \|\| r.message.language`（**保留用户已选**），zelin 改成**无条件覆盖**并转成显示名。这是「安装后语言强制跟随 System Settings」的补丁，属 `after_install` 那条线；本项目 `erx_core` 若直接把 System Settings 设成 zh 就不需要它。整份覆盖上游函数=版本升级即失配 | 上游 `frappe/desk/page/setup_wizard/setup_wizard.js:540-570`、`boot.py:257` |
| `public/.gitkeep` | 占位空文件 | 0 | **不抄** | — | 目录占位，`erx_core` 的 `public/` 有实文件后无需占位 | — |
| `templates/__init__.py` | 空包标记 | 0 | **不抄**（而非「抄」）| — | 零字节，`erx_core` 由脚手架 `bench new-app` 自带同名文件；**抄一个空文件没有意义**，但该目录结构本身须存在 | — |
| `templates/pages/__init__.py` | 空包标记 | 0 | **不抄** | — | 同上；且 zelin `templates/pages/` 下**没有任何真实页面**⇒ 这条功能线是空的 | — |
| `config/__init__.py` | 空包标记 | 0 | **不抄** | — | 零字节；且 **v16 已不读 `app/config/desktop.py` 这套旧约定**（已核实：全仓 grep `config/desktop` 无命中）⇒ 该目录在 v16 属历史残留 | — |
| `translations/zh.csv` | 译文 | 19350（记录 18332／唯一 18296）| **不抄（整份）**，仅择取 | `erx_core/translations/zh.csv` | 只取 **4 034 条官方无译文的**（纯增量）；**749 条撞译名须逐条人工裁决**；13 513 条与官方逐字相同**不要抄**（纯噪音）。另须清掉那个空白键行（第 10511 行 `['  ','If enabled']`）| §11；ADR-0006 |
| `locale/zh.po` | 译文（po）| 179 | **不抄** | — | ADR-0006 硬纪律「自有 app 内只放 csv、不放 po、不生成 mo」；且 56 条**全是自家 csv 的子集、译法零分歧**（纯冗余）；含 HRMS 词条（本项目未装）；无 header、无 pot、无 mo ⇒ 从未生效 | §12；ADR-0006 原文 |

**合计**：抄 0 ／ 抄后改 5 ／ 不抄 10 ／ 存疑 0。

---

## 14. 新发现的缺陷

### N-1 `fixtures/property_setter.json` 有**重复主键**：`Account-root_type_options` 出现 2 次（已核实）

49 条里唯一 `name` 只有 48 个。两条同名记录 `value` 完全相同，**只有 `modified` 不同**
（`2025-08-17 19:42:47.535662` 与 `2023-08-22 19:42:47.535662`）。
后果：`import_doc`→`import_file_by_path(force=True)`（`data_import.py:362`）是**强制覆盖**语义，
按数组顺序后者覆盖前者 ⇒ 最终生效的是**时间戳较旧的那条**（数组第 451 行那条在后）。
此例两者 value 相同故无实害，但这是个**静默的顺序依赖**，一旦将来改其中一条就会被另一条覆盖。

### N-2 `root_type` 加 `Common Accounts` 选项在 v16 是**半截改造**（已核实）

`fixtures/property_setter.json` 把 `Account.root_type` 的选项从 v16 标准的
`Asset/Liability/Income/Expense/Equity`（已核实 `erpnext/accounts/doctype/account/account.json`）
扩成多一个 `Common Accounts`。但：

- **上游 v16 全仓没有任何代码认识 `Common Accounts`**（已核实：`grep -rn "Common Accounts" frappe-bench/apps/erpnext/` 无命中）
- 上游两处按 `root_type` 分派 `report_type` 都只列 5 个：
  `account.py:191` 与 `chart_of_accounts.py:35` 的 `root_type in ("Asset","Liability","Equity")`
  ⇒ `Common Accounts` 会被归到 **Profit and Loss**，而「共同类」科目本应进资产负债表
- **而且 zelin 自己也没用它**：`cn_norm_chart_of_accounts2024.json` 里的 `共同类` 节点
  （L1380）`root_type` 填的是 **`Asset`**，不是 `Common Accounts`（已核实）。
  全仓 `"root_type": "Common Accounts"` **零命中**。

⇒ 这个选项**加了但没人用、且用了会错**。抄的时候要么删掉、要么补齐 `report_type` 分派逻辑。

### N-3 `public/icons/account_report.svg` 放进 `app_include_icons` 无效（已核实）

`hooks.py:14-22` 把两个 svg 都列进 `app_include_icons`／`web_include_icons`。
该钩子的机制（`jinja_globals.py:113-128`）是 fetch 文件文本、`insertAdjacentHTML` 塞进 `#all-symbols`，
消费端 `icon.js:13` 只认 **`#all-symbols > svg > symbol[id]`**。

- `cn_account_report.svg`：有 `<symbol id="icon-cn-account-reporting">` ⇒ **有效**
- `account_report.svg`：**`<symbol>` 数为 0**，是裸 `<svg><path>…` ⇒ 塞进去**贡献不了任何图标**，属无效条目
  （它真正的用途是 `install.py:128` 的 `Desktop Icon.logo_url` 图片路径，那条是对的）

附带：`cn_account_report.svg` 的根元素用 `id="frappe-symbols"`，**与 frappe 自带的
`lucide/icons.svg`、`timeless/icons.svg` 同 id**（已核实两者都有 `id="frappe-symbols"`）⇒ 同页多个同名 DOM id。
frappe 自己就这么干，故属既存约定、非 zelin 独创，但仍是隐患。
另：zelin 两个 svg 都**缺** frappe 自带文件的 `style="display: none;"`（已核实）；因容器
`#all-symbols` 本身带 `style="display:none"`（`desk.html:43`、`base.html:90`）故不致可见，属冗余风险。

### N-4 `utils.py:177` 的 `except Exception as e` 捕获了 `e` 却从不使用（已核实）

`utils.py:178 frappe.log_error("china_company_default.utils.set_item_group_account")` 只写死字符串，
**不含 `e`**，异常内容与 traceback 均不入库（`log_error` 在 message 为 None 时会自取 traceback，
故 traceback 尚存，但绑定的 `e` 是纯死变量）。5 处 log_error 全是这个模式。

### N-5 `utils.py` 的 5 个 `log_error` 全部只传 title、无 message（已核实）

L38/59/84/103/178 都是 `frappe.log_error("<固定串>")` ⇒ 进 Error Log 的 `method` 字段是那个固定串，
**同一函数的所有失败合并成同一个标题**，无法区分是哪次、哪家公司、哪条数据出错。
与缺陷 2 是**相反方向的同一类问题**：custom_account.py 是传多了参数报 TypeError，utils.py 是传少了信息丢失现场。

---

## 15. 9 条缺陷核实结论汇总

| # | 缺陷 | 结论 | 关键 file:line |
|---|---|---|---|
| 1 | `account_category` 7 键 vs 8 键 | **成立，但行号锚点错**（不是 `:52`，是 **L32-40** 与 **L106-118** 两处）；**且可达性要修正**：中国科目表**不会**触发，`Standard`/印度科目表**会** | zelin `custom_account.py:32-40,106-118,53-67`；上游 `chart_of_accounts.py:281-291`（8 键）、`:50` |
| 2 | `log_error` 首位置参误用，6 处 | **成立，6 个行号全对**；但登记的 `:97` 是错的（L97 在 `add_suffix_if_duplicate` 里），最小行号是 **L86** | zelin `custom_account.py:86,173,189,208,227,245`；上游 `frappe/utils/error.py:44-49` |
| 3 | 销项模板引用不存在科目号 | **归 G1a** | — |
| 4 | `default_accounts.csv` 14/35 行查不到科目 | **归 G1a** | — |
| **5** | `get_chart` 全不匹配返回原始文件文本 | **成立，且比登记描述更糟**——返回 56761 字符的台湾科目表全文（**truthy**，穿过 `if chart:` 守卫），上游返回 `None`（安全短路）。首爆点是 `.items()` 而非 `.get()` | zelin `custom_account.py:169,191`（多出的 `return chart`）；受害点 `:23-24,:28` 与 `:136,139`＋上游 `:252,259`；上游对照 `:102-131`（无 trailing return） |
| **6** | 裸 `except` 是 5 处而非 4 处 | **部分成立**——登记册表述**自相矛盾**。事实：**4 处裸 + 1 处 `except Exception as e` = 5 个吞一切的处理器**。4 个裸 except 行号与第五处位置**都对** | `company_default/utils.py:37,58,83,102`（裸）、**`:177`**（`except Exception as e`）。另全仓裸 except 共 **8** 处：另加 `doc_events.py:31`、`setup/install.py:74,114,140` |
| **7** | import 后本地重定义、影子覆盖 | **成立** | `custom_account.py:12-17`（import）vs **`:90`**（`add_suffix_if_duplicate` 重定义）、**`:103`**（`identify_is_group` 重定义）；调用点 `:42,:46` |
| **8** | 前半：fixtures 三 json 是死文件<br>后半：`after_install` 整体包在守卫下 | 前半 **不成立（推翻）**——`import_fixtures` 用 `os.listdir` 扫目录、**不读 `fixtures` hook**，装 app 即导入；三个 json 都有下游消费方<br>后半 **成立** | 前半：`frappe/utils/fixtures.py:32-45`（`os.listdir`）、`:75`（hook 只用于 **export**）、`installer.py:367`、`migrate.py:171`；hook 缺失 `hooks.py`（全文无 `fixtures`）<br>后半：`setup/install.py:54-57`；`frappe/__init__.py:1537-1551` |
| **9** | 许可证不一致 | **成立** | `custom_account.py:1-2`（GPL v3）vs 根 `license.txt:1`（MIT）vs `hooks.py:8`（`app_license="MIT"`）|

---

## 16. 复核建议（规范 §2.2）

### (a) 最弱环节／未覆盖什么

1. **全部结论都是静态阅读 + 纯 python 仿真，没有一条跑过真实站点。** 硬约束禁止动站点，故缺陷 1／2／5
   的「真实 frappe 运行期确实抛该异常」这一步**未覆盖**。仿真复刻的是控制流与真实函数签名，
   但没有验证 frappe 的 `override_whitelisted_methods` 在 v16 是否真的把调用导到 zelin 的函数
   （我只核实了 hook 声明存在，**没核实 v16 的 `override_whitelisted_method` 分派仍生效**）。
2. **缺陷 8 前半句我给的是「反证」（证明有读取端），而不是穷尽证明。** 我查了
   `frappe/utils/fixtures.py`、`installer.py`、`migrate.py` 三处调用链与三个 json 的下游消费者，
   但**没有穷举 v16 里所有可能读 `fixtures/` 目录的代码路径**。结论方向（不是死文件）可靠，
   但「还有没有别的读取端」未覆盖。
3. **`property_setter.json` 49 条、`custom_field.json` 4 条我只核了结构与重复主键，没逐条核对
   v16 的目标字段是否仍存在**（`insert_after` 锚点、`label` 覆盖的字段名）。49 条里若有字段在 v16 改名，
   fixtures 会静默跳过或报错，这是**和本项目刚踩的 `Bank Transaction Mapping` 同类的风险**，我没做。
4. **译文数字依赖 babel 对 mo 的解析**。我用手写解析器与 babel 双路交叉验证了 po，
   但 mo 只走了 babel 一条路。另外 `.mo` 是构建产物，若本机 assets 与 apps 源码不同步，数字会偏。
5. **`public/js` 三个 client script 我判「不抄」的理由是 DOM 耦合脆**，但**没有实际验证那段 jQuery
   在 v16 当前 DOM 下是否还命中**（要跑浏览器）。判定依据是耦合性质，不是实测失效。

### (b) 你给的「已知」里有错的 —— 有 3 处

1. **「zelin 18297 条译文里仅 748 条覆盖官方」——数字的语义被安反了，这条是错的。**
   正确：**覆盖官方的是 14 262 条（78%）**；**749 条（≈你说的 748）是「官方已有但 zelin 译法不同」的
   撞车数，即需人工裁决的冲突数**，不是覆盖数。
   出处：`Spike/S4-G1c-cov4.py`（对 `frappe-bench/sites/assets/locale/zh/LC_MESSAGES/{frappe,erpnext}.mo`，
   babel 2.16.0 解析）。另「18297」应为 **18296**，多出的 1 条是第 10511 行键为两个空格的
   `['  ', 'If enabled']`（`Spike/S4-G1c-cov5.py` 精确定位，两种口径都复现了 18297/18296 的差）。

2. **「`public/` 那 7 个与 `templates/` 那 2 个大概率是 CRM/企微前端资源 ⇒ 判不抄」——前提错了。**
   `public/` 里**没有任何 CRM 或企业微信资源**。实际是：2 个**财务报表图标** svg
   （`install.py:128,138` 与 `hooks.py:14-22` 消费）、3 个**改按钮文案**的 client script
   （付款→预付款/预收款/收款）、1 个**覆盖 setup wizard 预填**的脚本。
   `templates/` 两个是**零字节 `__init__.py`**，不是前端资源。
   结论「不抄」对其中 4 个 js 仍成立，**但两个 svg 应判「抄后改」**（它们是中国财务报表工作区的图标，
   `install.py` 明确引用）。「合并成几行」这个处理会把 svg 的落点需求一起漏掉。

3. **「缺陷 6：裸 `except` 是 5 处而非 4 处……第五处是 `except Exception as e`」——表述自相矛盾。**
   `except Exception as e` 不是裸 except。准确说法：**吞一切的处理器 5 处，其中裸 4 处、具名 1 处**。
   另外若问的是「全仓裸 except 有几处」，答案是 **8 处**（utils.py 4 + `doc_events.py:31` +
   `install.py:74,114,140`），不是 4 也不是 5。

（顺带确认你给对的：`public/` 确为 **7 个文件**——`.gitkeep` + 2 svg + 4 js；
「zelin 那份 csv 在本站点根本不生效」**成立**，`sites/apps.txt` 精确内容是 `frappe\nerpnext`，
且 `erx_core` 磁盘上尚不存在。缺陷 2 的 6 个行号、缺陷 6 的 4 个裸 except 行号与第五处位置，全对。）

### (c) 拿不准处

1. **`fixtures/property_setter.json` 里 25 条 `label` 覆盖与 ADR-0006 的边界**。ADR-0006 管的是
   **译名**（`translations/zh.csv` 单一来源）；Property Setter 的 `label` 覆盖**在机制上是另一条路**
   （改 DocField 属性，不过 `__()`）。这 25 条到底算「译名」（该归 csv）还是「字段改名」（该归 Property Setter），
   我拿不准，**需要你按 ADR-0006 的意图裁决**。这会影响那 492 行 fixture 抄多少。
2. **缺陷 1 的严重度定级**。我核实了中国科目表不触发、Standard/印度触发。但本项目是否会有人用
   `Standard` 建公司（比如建测试公司、或多公司里有一家非中国），我不知道。若永不用，缺陷 1 降为
   「字段丢失」；若会用，是「建公司直接炸」。**定级取决于你的使用场景。**
3. **`Common Accounts`（N-2）该删还是该补全**。删掉最省事，但「共同类」科目在中国会计准则里是真实存在的
   一类（`cn_norm_chart_of_accounts2024.json:1380` 有 `共同类` 节点，只是 root_type 填了 `Asset`）。
   这是业务决策，不是我能定的。
4. **`custom_account.py` 的 GPL v3 文件头（缺陷 9）怎么处理**。该文件是从上游 erpnext 抄改的
   （文件头 `Copyright (c) 2015, Frappe Technologies` 与上游一致），而上游 erpnext 本身是 GPL v3。
   所以这个文件头**可能是准确的**（抄 GPL 代码得继承 GPL），反倒是 zelin 根目录标 MIT 才是问题。
   **本项目「并入式抄源码」会继承同样的许可证问题**——我不做法律判断，只报事实：
   本项目若抄这个文件，会把一份 GPL v3 衍生代码放进自有 app。**这条建议升级给你或法务定。**
5. **`setup_wizard.js` 覆盖上游函数这件事的必要性**。我推断本项目不需要（`erx_core` 直接设 System Settings
   即可），但没核实 v16 setup wizard 在「站点已设 System Settings 为 zh/CNY」时的实际预填行为。判「不抄」
   带一点推断成分。

---

## 17. 本次留下的脚本（全部只读，不碰站点／不导 frappe／不改 Reference）

| 脚本 | 用途 |
|---|---|
| `Spike/S4-G1c-verify.py` | zh.csv 规模、行数/记录数/唯一键/重复/空译文 |
| `Spike/S4-G1c-cov.py` | 手写 PO 解析做覆盖率初算（后被 babel 版取代）|
| `Spike/S4-G1c-cov2.py` | 探测 polib 可用性（不可用，留作记录）|
| `Spike/S4-G1c-cov3.py` | **babel 解析 po** 口径的覆盖率 |
| `Spike/S4-G1c-cov4.py` | **babel 解析 mo**（运行时口径）的覆盖率 + fixtures 重复主键 |
| `Spike/S4-G1c-cov5.py` | 定位 18297/18296 的那 1 条空白键 |
| `Spike/S4-G1c-po.py` | `locale/zh.po` 56 条的来源、与官方及自家 csv 的关系 |
| `Spike/S4-G1c-getchart-sim.py` | **缺陷 5 的可执行复现**（zelin 返回 str vs 上游返回 None）|
| `Spike/S4-G1c-defect12-sim.py` | **缺陷 1／2 的可执行复现**（TypeError / AttributeError / is_group 误判）|
| `Spike/S4-G1c-trigger.py` | **缺陷 1 的可达性**：哪些科目表带 `account_category` |

