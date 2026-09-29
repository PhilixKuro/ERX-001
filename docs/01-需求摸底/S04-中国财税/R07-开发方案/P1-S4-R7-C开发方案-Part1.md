# P1-S4 开发方案·Part1：基础设施、安装期、科目表建账、增值税

**来源需求**：[B 需求文档](../R06-需求文档/P1-S4-R6-B需求文档.md) §4.2–§4.6、§4.13 第 5 条｜**前置依赖**：无｜**日期**：2026-09-29｜**编写者**：Claude（Opus 5.5）
**总纲**：[P1-S4-R7-C开发方案-总纲.md](P1-S4-R7-C开发方案-总纲.md)（接口契约、技术假设、执行纪律都在总纲，本 Part 不重复）

## 切片划分与验收

| 切片 | 功能点 | 验收条件 |
|---|---|---|
| **SL-001** 工程基础设施 | 测试站点、中文字体（需求 TS-002／DEC-095）、app 骨架、测试脚手架（需求 TS-004） | 1. `bench --site test.localhost list-apps` 列出 `frappe`／`erpnext`／`frappe_china`；`bench --site erx.localhost list-apps` **只**列出 `frappe`／`erpnext`；`common_site_config.json` 的 `default_site` 仍是 `erx.localhost`<br>2. 测试站 System Settings：国家 China、语言 zh、时区 Asia/Shanghai、日期格式 yyyy-mm-dd、币种 CNY、舍入 `Commercial Rounding`；会计年度 2025／2026／2027 存在<br>3. `bench --site test.localhost run-tests --app frappe_china` 退出码 0，且至少跑了 1 个测试（输出里的测试数 ≥ 1，**不接受「0 tests」**）<br>4. 容器内 `fc-list :lang=zh family` 非空，`pdftotext`／`pdffonts` 可用；一份含「资产负债表」四字的 HTML 经 `frappe.utils.pdf.get_pdf` 生成的 PDF：`pdftotext -enc UTF-8` 取出的文本含这四个字，`pdffonts` 列出的字体含 `NotoSansCJK` 且 `emb` 列为 `yes`（HT-003）<br>5. 四个中文名报表桩经 `frappe.desk.query_report.run` 各返回一次（HT-001）；`frappe.boot.get_bootinfo()` 的 `sidebar_items` 里没有 `cn tax` 键（HT-006）<br>6. **异常路径**：`setup.sh` 里的字体安装段在网络不通时只打印告警、脚本继续执行（把 apt 源临时指向不可达地址实跑一次，脚本退出码 0 且有告警行）；跑完测试后测试站 System Settings 的时区、语言与跑之前逐项相同（HT-013）<br>7. 演示站基线未变：Company 1（`华东弹簧`）、GL Entry 22、SLE 12、Account 95 |
| **SL-002** 安装期设置 | 需求 TS-005、AC-010、DEC-100 | 1. 45 个中文计量单位全部存在且启用<br>2. 装 app 前已存在的每个计量单位，其 `enabled` 值装后逐条不变（装前快照对比）<br>3. `Global Defaults.disable_rounded_total = 1`，8 类单据的 `rounded_total` 已隐藏（Property Setter 存在）<br>4. **异常与边界**：`after_install()` 连续调用两次，计量单位条数不变、不报错；`bench --site test.localhost install-app frappe_china --force` 重跑一次同样不产生重复；安装前后 System Settings 除 `modified` 外逐字段相同；站点里预先把某个中文单位（如「支」）置为停用后再装，装后它**仍是停用**（只新增、不改既有） |
| **SL-003** 中国科目表建公司 | 需求 TS-006／007、AC-001／005／006／012、DEC-097／103／104 | 1. 三个原方法路径经 `frappe.override_whitelisted_method` 解析（即 HTTP 入口用的同一解析），都指向本 app 的函数；另在测试站界面上实点一次作为 HTTP 层证据（TS-008 截图）。国家 China 时建公司下拉含 `小企业会计准则(2024)`、`Standard`、`Standard with Numbers` 三项；国家 United States 时结果与卸掉覆盖前一致；科目树预览按本表结构返回（根节点 6 个）；`get_chart` 查不存在的名字返回 `null`<br>2. 以本表建公司：`Account` 266 条，与 JSON 按（科目号, 科目名）双向无差；每个科目的 `root_type` 与 JSON 顶层节点一致；22 个默认科目字段按 TS-006 的映射表落值，其中 DEC-097 的 6 个逐一相符（AC-005）；5 个默认仓库存在，成品库指向 `1405`、在制品库指向 `1409`；`Products` 物料组的费用科目为 `5401010`；现金付款方式挂 `1001`<br>3. 自检函数对这家公司返回 `checked=True, ok=True`，`account_count == 266`<br>4. **同一进程连续建两家公司，两个顺序各一次**（AC-006）：先本表再 `Standard`、先 `Standard` 再本表。均不报错；`Standard` 那家有原生科目（>0 条）与默认仓库；本表那家 266 条<br>5. **异常路径**：① 进程里人为残留 `frappe.local.flags.ignore_chart_of_accounts = True` 后建 `Standard` 公司，原生建账照常执行；② 建账中途抛异常（测试里替换 `create_charts` 使其抛错）→ 公司插入失败并回滚，`ignore_chart_of_accounts` 已复位，随后建 `Standard` 公司正常；③ 国家选 United States、科目表选本表 → 明确报错、不建公司；④ 以 `Existing Company` 方式基于一家本表公司建新公司 → 走原生路径，科目与源公司一致<br>6. 自检的异常输入（AC-001 后半）：公司不存在 → `checked=False, ok=False` 且有告警；`Standard` 公司 → `checked=False, ok=True`；删掉一个明细科目后 → `ok=False` 且 `missing_from_chart` 列出它；自检内部出错（测试里替换 `frappe.get_all` 使其抛错）→ 不抛异常、`ok=False`、告警里有原因。四种情形**均不抛异常** |
| **SL-004** 增值税与端到端最简路径 | 需求 TS-008、AC-002／003、DEC-094 | 1. 税类别 9 个；销项模板 5 个、进项模板 7 个；税规则 13 条（名称与税率见 TS-008 数据表）<br>2. 12 个模板的税行 `account_head` 全部是 `2221005 - 销项税额 - {abbr}`（销项）或 `2221001 - 进项税额 - {abbr}`（进项）；含税模板税行 `included_in_print_rate = 1`、未税与无税为 0；建税前后 `Account` 条数都是 266（AC-002）<br>3. `get_tax_template` 按税类别 `P9专票含税`、类型 Purchase 取到 `P9专票含税 - {abbr}`<br>4. **异常路径**：对一家 `Standard` 公司调用 `setup_cn_taxes()`（它没有 `2221005`／`2221001`）→ 明确报错、列出缺的科目号，该公司 `Account` 条数不变（**不按名兜底、不新建科目**）；对本表公司重跑一次 `setup_cn_taxes()` → 税类别、模板、规则条数都不变<br>5. **端到端最简路径（首个 Phase 方案要求 P-2）——这条路径能真的跑通**：在测试站上，`frappe_china` 已装 → 以本表建公司 → 开销售发票、单价 113、选 `P13专票含税` → 提交后 `net_total = 100.00`、`total_taxes_and_charges = 13.00`、总账贷记 `2221005` 13.00、贷记 `5001010` 100.00、借记 `1122` 113.00；单价 100、选 `P13专票未税` → 税额 13.00、合计 113.00；采购发票运费 109、选 `P9专票含税` → 不含税 100.00、税额 9.00、总账借记 `2221001` 9.00（AC-003）<br>6. **舍入边界**：销售退货（数量 -1、单价 0.50、`P13专票未税`）的税额为 **-0.07**。这是 `Commercial Rounding` 对 -0.065 的对称四舍五入；legacy 会得 -0.06。期望值来自 C 步在容器里直接调用舍入函数的结果，未经单据实跑；若实跑结果不同，先查税额计算链，不改期望值。另验凑整已关：`rounded_total = 0` 且 `rounding_adjustment = 0`（`taxes_and_totals.py:842-844`），总账无尾差分录 |

执行每个切片前，对照该切片验收条件检查方案覆盖性——如发现按方案写出的代码无法通过验收条件，暂停反馈，不硬写。

## 任务清单

| 任务 | 对应切片 | 可并行否 |
|---|---|---|
| TS-001 建测试站点 | SL-001 | 否 |
| TS-002 开发容器装中文字体 | SL-001 | 可（甲组，见总纲 §八） |
| TS-003 app 骨架与测试脚手架 | SL-001 | 否 |
| TS-004 安装期设置 | SL-002 | 否 |
| TS-005 科目表数据与三个覆盖 | SL-003 | 否 |
| TS-006 Company 钩子与建账编排 | SL-003 | 否 |
| TS-007 建账结果自检函数 | SL-003 | 否 |
| TS-008 税类别、税模板、税规则；端到端测试 | SL-004 | 否 |

---

## 任务 1：建测试站点（对应切片 SL-001）

### 目标
一个与演示站完全隔离、设置与演示站一致的站点，供 D 步全部开发与验收使用（总纲 A1）。

### 具体改动
全部在容器内执行（`docker/shell.sh` 或 `docker compose exec -T -w /workspace/frappe-bench frappe …`）。**不改任何脚本、不跑 `docker/up.sh`**（总纲执行纪律 4）。

```bash
bench new-site test.localhost \
  --db-root-password "$DB_ROOT_PASSWORD" --admin-password admin \
  --mariadb-user-host-login-scope=% --no-mariadb-socket \
  --install-app erpnext                     # 不加 --set-default
bench --site test.localhost set-config developer_mode 1
bench --site test.localhost set-config allow_tests true --parse
SITE_NAME=test.localhost bash /workspace/docker/scripts/seed-demo.sh --bare   # v16 初始化五处缺口
SITE_NAME=test.localhost UI_LANGUAGE=zh bash /workspace/docker/scripts/set-locale.sh
```

之后用一段 python（`frappe.init(site="test.localhost")`）补设：
- `System Settings`：`date_format = "yyyy-mm-dd"`、`rounding_method = "Commercial Rounding"`（DEC-116）；
- 建会计年度 `2025`／`2026`／`2027`（自然年，不挂公司）；
- `commit`。

**不要**跑 `bench use test.localhost`。浏览器访问测试站用 `http://test.localhost:8000`（Windows 把 `.localhost` 解析到本机）。

### 验证方式
对应 SL-001 验收第 1、2、7 条：`list-apps` 两个站点各跑一次；读回测试站 System Settings 与 Fiscal Year；读 `common_site_config.json`；核演示站四项基线。

---

## 任务 2：开发容器装中文字体（对应切片 SL-001）

### 目标
PDF 里的汉字可读（DEC-095／LG-135）；容器重建后能自动恢复。

### 具体改动
- **`docker/scripts/setup.sh`**：在第 7 段（开发模式）之前加一段「中文字体」，形态如下。**失败只告警**（`setup.sh` 开着 `set -e`，这一段必须自己兜住）：

```bash
# ---------- 6.5 中文字体（PDF 打印用，P1-S4 DEC-095） ----------
# wkhtmltopdf 靠 fontconfig 找字形；镜像只带 dejavu 等西文字体，汉字会出方块。
# apt 不走 GIT_PROXY，故有代理时显式传给 apt。离线时只告警，不中断搭建。
if fc-list :lang=zh family | grep -q . && command -v pdffonts >/dev/null; then
  ok "中文字体与 PDF 检查工具已安装"
else
  log "安装中文字体 fonts-noto-cjk"
  apt_proxy=()
  [ -n "${GIT_PROXY:-}" ] && apt_proxy=(-o "Acquire::http::Proxy=$GIT_PROXY" -o "Acquire::https::Proxy=$GIT_PROXY")
  # poppler-utils 提供 pdftotext／pdffonts，供测试核对 PDF 里的文字与嵌入字体
  if sudo apt-get "${apt_proxy[@]}" update -qq && \
     sudo apt-get "${apt_proxy[@]}" install -y -qq fonts-noto-cjk poppler-utils; then
    fc-cache -f >/dev/null && ok "中文字体已安装"
  else
    echo "  警告：中文字体安装失败（网络不通？）。PDF 里的汉字会显示为方块，联网后重跑 up.sh 即可补装" >&2
  fi
fi
```

- **当前容器**：不跑 `up.sh`，直接在容器里执行同一段命令一次。
- **`docker/README.md`**：「Windows 上的几处适配」表之后加一小节「中文字体」，写三件事：为什么要装、装在哪（`setup.sh` 6.5 段）、离线机怎么办（联网后重跑 `up.sh`；容器被 `down.sh` 删掉后字体随之丢失，由 `up.sh` 补装）。

### 验证方式
对应 SL-001 验收第 4、6 条：
- `fc-list :lang=zh family`；
- 用 `get_pdf` 生成含中文的 PDF，写到临时文件，在容器内用 `pdftotext -enc UTF-8` 取文本、用 `pdffonts` 看字体与嵌入列；这一检查写成 `tests/utils.py` 里的工具函数 `pdf_text_and_fonts(pdf_bytes) -> tuple[str, list[dict]]`，供 TS-017 复用；
- 失败降级：在容器里临时把该段的 apt 源指向不可达地址（只改运行时参数，不改文件），执行这一段，确认只打告警。

---

## 任务 3：app 骨架与测试脚手架（对应切片 SL-001）

### 目标
`frappe_china` 建成、装进测试站；三条关键假设（HT-001／006／013）在写业务代码前先验掉。

### 具体改动

**1. 生成 app**：在容器内 `/workspace/frappe-bench` 下跑 `bench new-app --no-git frappe_china`。**必须带 `--no-git`**：不带时 bench 会自动 `git init` 并提交一次，属于须用户许可的版本管理动作（总纲执行纪律 6）。带了 `--no-git` 就不会生成 `.gitignore`，由执行者照 frappe 的 boilerplate 模板补写一份。交互提示用管道按序喂答案：
- App Title `Frappe China`
- App Description `中国财税、译名与导航、对原生 ERPNext 与官方 app 的修复`
- App Publisher：主仓库 `git config user.name` 的值
- App Email：主仓库 `git config user.email` 的值（取不到则暂停问用户，**不编造**）
- License `mit`
- GitHub workflow `N`
- Branch 用默认值

生成后 `bench --site test.localhost install-app frappe_china`。

**2. 目录形态**（生成后改成这样；方括号内的由后续任务填）：

```
frappe_china/                    # app 仓库根（apps/frappe_china）
├── README.md                    # 模块判据、同名侧栏用途、并入登记（TS-020 补全）
├── license.txt                  # MIT
└── frappe_china/
    ├── hooks.py                 # 只接线（总纲 §六）
    ├── modules.txt              # 一行：CN Tax
    ├── install.py               # after_install → accounting.install 的两个入口
    ├── cn_tax/                  # 模块（替换掉 bench 生成的 frappe_china/frappe_china/frappe_china/）
    │   ├── chart_of_accounts/   # [TS-005] 科目表 JSON
    │   ├── data/                # [TS-006/008] 默认科目映射、税设置
    │   ├── doctype/             # [TS-009/015/018]
    │   └── report/              # [TS-012/013/014/016]
    ├── accounting/              # 普通包（总纲 A8）
    │   └── statements/
    ├── fixtures/                # [TS-015] Custom Field、Cash Flow Code
    ├── workspace_sidebar/
    │   └── cn_tax.json          # 与模块同名的空侧栏，压住自动侧栏（ADR-0012「二」）
    └── tests/
        ├── __init__.py
        └── utils.py             # 测试基类与工具
```

- `modules.txt` 改为一行 `CN Tax`。删掉 bench 生成的默认模块目录，新建 `cn_tax/__init__.py`。
- `workspace_sidebar/cn_tax.json`：`{"doctype": "Workspace Sidebar", "name": "CN Tax", "title": "CN Tax", "module": "CN Tax", "app": "frappe_china", "items": []}`。README 写明：它的名字必须与 `modules.txt` 那一行逐字相同，删了会多出一条侧栏。

**3. `tests/utils.py`**：

```python
class FrappeChinaTestCase(IntegrationTestCase):
    """本 app 全部测试的基类。不 import erpnext.tests.utils（HT-013）。"""
    @classmethod
    def setUpClass(cls): ...      # super()；frappe.local.lang = "zh"；frappe.set_user("Administrator")

def make_cn_company(name: str, abbr: str) -> "Company": ...    # 国家 China、币种 CNY、科目表 CN_CHART_NAME
def make_std_company(name: str, abbr: str) -> "Company": ...   # 国家 China、科目表 Standard
TEST_PREFIX = "_FCT"            # 测试造的记录名一律带此前缀，清理时据此正向限定
```

- 公司名以 `TEST_PREFIX` 开头，缩写 3–4 位大写。
- `make_cn_company` 在 TS-006 完成前只是桩。

**4. 探针**（验完即删，结论写 D 回执）：
- HT-001：在 `cn_tax/report/` 下建四个 Script Report 桩，名为 `小企业资产负债表`／`小企业利润表`／`小企业现金流量表`／`漏科目检查`，各返回一列一行。`bench --site test.localhost migrate` 后，经 `frappe.desk.query_report.run` 各调一次。`git status` 里路径可读（`core.quotepath` 显示问题不算失败）。**这四个桩在 TS-012 起转为正式报表，不删**。
- HT-006：`bench migrate` 后，以 Administrator 身份取 `frappe.boot.get_bootinfo()["sidebar_items"]`，断言没有 `cn tax` 键。
- HT-013：记下测试站 System Settings 的 `time_zone`／`language`，跑一次 `run-tests --app frappe_china`，再读一次，两次相同。

**5. 一条占位测试** `tests/test_smoke.py`：断言 `frappe_china` 在已装 app 列表里，且 `frappe.local.lang == "zh"`。

**6. 编辑器与版本管理**：
- `.vscode/settings.json` 的 `git.scanRepositories` 加一行 `frappe-bench/apps/frappe_china`（该文件注释要求新增 app 时追加）；
- `docs/README.md`「代码去哪找」表的「本项目二次开发内容」一行改为指向 `frappe-bench/apps/frappe_china/`（写前载入常驻文件契约）；
- app 目录**暂不 `git init`**。建仓库、首次提交、建远端都等用户许可（总纲执行纪律 6）。在此之前，`git.scanRepositories` 那一行照加，编辑器找不到仓库时会自动忽略。

### 验证方式
对应 SL-001 验收第 1、3、5、6、7 条。

---

## 任务 4：安装期设置（对应切片 SL-002）

### 目标
装 app 时只做两件事，都要幂等，且**不得包在 `frappe.is_setup_complete()` 的判断里**（需求 §4.3）。

### 具体改动

`frappe_china/accounting/install.py`：

```python
CN_UOMS: Final[tuple[str, ...]] = (...)   # zelin setup/install.py 的 uom_list 45 项，原样照抄、顺序不变

def ensure_cn_uoms() -> list[str]:
    """只新增缺的；不启用、不停用、不修改任何既有单位。返回新建的名字。"""
    existing = set(frappe.get_all("UOM", pluck="name"))
    created = []
    for name in CN_UOMS:
        if name in existing: continue
        frappe.get_doc({"doctype": "UOM", "uom_name": name, "enabled": 1}).insert(ignore_permissions=True)
        created.append(name)
    return created

def disable_rounded_total() -> bool:
    """Global Defaults.disable_rounded_total = 1，经 save() 触发 toggle_rounded_total 建 Property Setter。
    已是 1 时不 save，返回 False。"""
```

`frappe_china/install.py`：

```python
def after_install() -> None:
    from frappe_china.accounting.install import ensure_cn_uoms, disable_rounded_total
    ensure_cn_uoms()
    disable_rounded_total()
```

**不做**：
- 停用非中文单位（zelin 第 69 行）；
- 改 System Settings（zelin `set_system_settings`）；
- `disable_in_words`、`field_property.csv`、`set_v16_icon`。

`tests/test_install.py`：覆盖 SL-002 验收 1–4。「预先停用『支』」这一条的做法：测试里先把「支」置为停用，再调用 `ensure_cn_uoms()`，断言它仍是停用。

### 验证方式
- 跑 `test_install.py`；
- 按 SL-002 验收第 4 条，在测试站实跑一次 `install-app frappe_china --force`，前后对比 UOM 条数与 System Settings（HT-005 一并验掉）。

---

## 任务 5：科目表数据与三个覆盖（对应切片 SL-003）

### 目标
建公司下拉、取表、科目树预览三处能认出中国科目表（需求 §4.4.1–§4.4.2）。

### 具体改动

- **科目表 JSON**：把 zelin `chart_of_accounts/custom_accounts/chart_of_accounts/cn_smes_chart_of_accounts2024.json` **逐字节**复制到 `frappe_china/cn_tax/chart_of_accounts/cn_smes_chart_of_accounts2024.json`，前后两份 sha256 相同（写进 D 回执）。另三份科目表不带（需求 §4.2）。
- **`frappe_china/accounting/chart.py`**（签名见总纲 §六）：

```python
_CHART_PATH = Path(__file__).resolve().parents[1] / "cn_tax" / "chart_of_accounts" / "cn_smes_chart_of_accounts2024.json"

def load_cn_chart_tree() -> dict:
    # 每次返回新对象（调用方会改动它）：可缓存文件内容，返回前 deepcopy
    return deepcopy(_read_json(_CHART_PATH))["tree"]

def get_charts_for_country(country, with_standard=False):
    charts = original_get_charts_for_country(country, with_standard)       # erpnext 原函数，行为不变
    if frappe.get_cached_value("Country", country, "code") == "cn" and CN_CHART_NAME not in charts:
        charts.insert(0, CN_CHART_NAME)
    return charts

def get_chart(chart_template, existing_company=None):
    if existing_company or not is_cn_chart(chart_template):
        return original_get_chart(chart_template, existing_company)          # 找不到时原函数本就返回 None
    return load_cn_chart_tree()                                              # 不带 zelin 末尾那句 return chart

def get_coa(doctype, parent, is_root=None, chart=None):
    chart = chart or frappe.flags.chart
    frappe.flags.chart = chart
    parent = None if parent == _("All Accounts") else parent
    accounts = build_tree_from_json(chart, chart_data=get_chart(chart)) or []   # 取表走本模块的 get_chart
    return [a for a in accounts if a["parent_account"] == parent]
```

  - 原函数用 `from erpnext... import get_chart as original_get_chart` 引入。
  - 不硬编码任何 `apps/...` 路径（需求 §4.4.2）。
- **`hooks.py`**：按总纲 §六写 `override_whitelisted_methods` 三项。

### 验证方式
`tests/test_chart.py`，对应 SL-003 验收第 1 条。
- **经 HTTP 调用**（总纲 A4：覆盖只对 HTTP 生效）：测试里用 `frappe.client` 不行，改用 `frappe.handler.execute_cmd` 的解析函数 `frappe.get_attr(frappe.override_whitelisted_method(<原路径>))`，断言解析到的是本模块的函数。
- 再直接调用本模块函数，断言返回值。
- 「United States 的结果与原函数一致」：断言 `get_charts_for_country("United States") == original_get_charts_for_country("United States")`。
- JSON 节点数：遍历树数到 266（元数据键取 `get_chart_metadata_fields()`）。

---

## 任务 6：Company 钩子与建账编排（对应切片 SL-003）

### 目标
选了本科目表的公司，由本 app 建出科目树、默认科目、仓库科目、物料组科目、付款方式与税；其余公司完全走原生路径。`ignore_chart_of_accounts` 不跨公司残留（RW-07）。

### 具体改动

**`frappe_china/accounting/company.py`**

```python
DEFAULTS_FILE = <cn_tax/data/company_defaults.json>

def _takes_cn_path(doc) -> bool:
    return (is_cn_chart(doc.chart_of_accounts)
            and doc.create_chart_of_accounts_based_on != "Existing Company"
            and not doc.parent_company)            # validate 会把有 parent_company 的改为 Existing Company（company.py:597-601），before_insert 早于 validate

def before_insert(doc, method):
    cn = _takes_cn_path(doc)
    if cn and doc.country != "China":
        frappe.throw(f"科目表「{CN_CHART_NAME}」只适用于国家为 China 的公司")
    # 每一家新建公司都显式赋值：上一家公司若在 on_update 之前失败、标志残留，这里会覆盖掉（RW-07）
    frappe.local.flags.ignore_chart_of_accounts = cn
    doc.flags.frappe_china_build = cn
    if cn:
        frappe.db.after_rollback.add(_reset_flag)   # 插入失败回滚时也复位

def on_update(doc, method):
    if not doc.flags.get("frappe_china_build"):
        return
    doc.flags.frappe_china_build = False            # 只在新建时建一次；此后的保存不再进来
    try:
        build_cn_company(doc)
    except Exception:
        frappe.log_error(title="frappe_china 建账失败", message=frappe.get_traceback())
        raise                                       # 不吞异常：整个插入失败、由调用方回滚
    finally:
        _reset_flag()

def _reset_flag():
    frappe.local.flags.ignore_chart_of_accounts = False

def build_cn_company(doc):
    prev = frappe.local.flags.ignore_root_company_validation
    frappe.local.flags.ignore_root_company_validation = True        # 同原生 create_default_accounts（company.py:422）
    try:
        create_charts(doc.name, custom_chart=load_cn_chart_tree())  # 上游函数（总纲 A3）
    finally:
        frappe.local.flags.ignore_root_company_validation = prev
    set_cn_default_accounts(doc)          # 22 个字段，见下表
    doc.create_default_warehouses()       # 原生方法，被标志跳过了，这里补调
    set_cn_warehouse_accounts(doc)
    set_cn_item_group_accounts(doc)
    doc.set_mode_of_payment_account()     # 原生方法，同上；依赖 default_cash_account 已在内存里
    # setup_cn_taxes(doc.name)            ← 由 TS-008 加入；本任务结束时 build_cn_company 不建税
```

- 提示文字一律用**英文源词经 `_()`**，例如 `frappe.throw(_("Chart of accounts {0} is only for companies in China").format(CN_CHART_NAME))`。中文译文由 TS-020 的 `translations/zh.csv` 提供（ADR-0006；总纲 A9）。**唯一例外**是报表的法定列头与行名，它们写中文字面量（总纲 A6）。
- `set_cn_default_accounts(doc)` 的算法：
  1. 读 `company_defaults.json` 的 `default_accounts`（字段 → 科目号）；
  2. 逐项用 `{"company": doc.name, "account_number": 号, "is_group": 0}` 查 `Account.name`；
  3. 有任何一项查不到，**报错并列出全部缺项**（这是数据文件与科目表不一致，属代码缺陷）；
  4. 全部查到后逐项 `doc.db_set(字段, 值)`。
  - 按科目号取值、不按科目名：避免 zelin「按名匹配、同名取错」的脆弱点。
- `set_cn_warehouse_accounts(doc)`：
  - 仓库名取 `_("Finished Goods")`／`_("Work In Progress")` 加 ` - {abbr}`。与 `create_default_warehouses` 在同一次调用、同一语言下取 `_()`，名字必然一致。
  - 用 `frappe.db.set_value("Warehouse", 名, "account", 科目)` 写入。
  - 仓库不存在时报错。
- `set_cn_item_group_accounts(doc)`：
  - 按 `company_defaults.json` 的 `item_group_expense`（物料组 → 科目号）处理，物料组名按原文与 `_()` 各查一次。
  - 不存在的物料组跳过，并记一条 `frappe.logger("frappe_china").warning`，不算失败。
  - 已有该公司的 `Item Default` 行则更新，没有则追加，然后 `save(ignore_permissions=True)`。

**`frappe_china/cn_tax/data/company_defaults.json`**（值为科目号；每项都**待客户会计确认**，文件头注释写明）：

| 字段 | 科目号 | 科目名 | 来源 |
|---|---|---|---|
| `default_bank_account` | 1002 | 银行存款 | zelin（V-19 修对） |
| `default_cash_account` | 1001 | 库存现金 | zelin |
| `default_receivable_account` | 1122 | 应收账款 | zelin（V-19 修对） |
| `default_payable_account` | 2202 | 应付账款 | zelin（V-19 修对） |
| `default_income_account` | 5001010 | 销售商品收入 | zelin（V-19 修对） |
| `default_expense_account` | 5401010 | 销售商品成本 | zelin |
| `default_inventory_account` | 1403 | 原材料 | zelin（V-19 修对） |
| `stock_adjustment_account` | 400103 | 生产成本-库存调整 | zelin |
| `stock_received_but_not_billed` | 220202 | 应付账款-暂估库存 | zelin |
| `default_provisional_account` | 220203 | 应付账款-暂估服务 | zelin |
| `asset_received_but_not_billed` | 220204 | 应付账款-暂估资产 | zelin |
| `capital_work_in_progress_account` | 1604 | 在建工程 | zelin |
| `disposal_account` | 1606 | 固定资产清理 | zelin |
| `exchange_gain_loss_account` | 5603220 | 财务费用_汇兑差额 | zelin |
| `default_advance_received_account` | 2203 | 预收账款 | zelin |
| `default_advance_paid_account` | 1123 | 预付账款 | zelin |
| `round_off_account` | 5603250 | 财务费用_其他 | DEC-097 |
| `write_off_account` | 5603250 | 财务费用_其他 | DEC-097 |
| `unrealized_exchange_gain_loss_account` | 5603220 | 财务费用_汇兑差额 | DEC-097 |
| `default_discount_account` | 5603230 | 财务费用_现金折扣 | DEC-097 |
| `accumulated_depreciation_account` | 1602020 | 累计折旧_机器 | DEC-097 |
| `depreciation_expense_account` | 5602070 | 管理费用_资产折旧摊销费 | DEC-097 |

- zelin csv 里 v16 Company 没有的 5 个字段不带：`default_payroll_payable_account`、`default_expense_claim_payable_account`、`service_received_but_not_billed`、`expenses_included_in_valuation`、`expenses_included_in_asset_valuation`。
- `item_group_expense`：`Products` → 5401010；`Raw Material`／`Sub Assemblies`／`Consumable` → 400101；`Services` → 400102。沿用 zelin 意图，并修正其 `Products` 指向组科目的缺陷（需求 §4.4.4）。
- `warehouse_account`：`Finished Goods` → 1405；`Work In Progress` → 1409。

**`hooks.py`**：按总纲 §六写 `doc_events`。

### 验证方式
`tests/test_company.py`，对应 SL-003 验收第 2、4、5 条：
- 「钩子运行时已有成本中心、尚无科目」（HT-008）：在钩子入口临时打点断言；
- 科目比对（HT-002）：逐节点比对（科目号, 科目名, 上级科目号, `is_group`, `root_type`, `account_type`）；
- 异常路径 ②：在测试里用 `unittest.mock.patch` 让 `frappe_china.accounting.company.create_charts` 抛错；
- 验收 5 ①：测试里先手动把标志置 True，再建 `Standard` 公司。

---

## 任务 7：建账结果自检函数（对应切片 SL-003）

### 目标
给 S8G-S1 的 IM-007 一个**永不抛异常**的检查函数，签名见总纲 §六（本任务定稿，路线文档 §七「签名未定」由此关闭）。

### 具体改动

**`frappe_china/accounting/selfcheck.py`**

```python
DEC097_FIELDS = ("round_off_account", "write_off_account", "unrealized_exchange_gain_loss_account",
                 "default_discount_account", "accumulated_depreciation_account", "depreciation_expense_account")

def check_company_chart(company):
    r = ChartCheckResult(company=company, checked=False, ok=False, is_cn_chart=None, account_count=None,
                         expected_account_count=0, missing_from_chart=[], extra_accounts=[],
                         root_type_mismatches=[], missing_defaults=[], warnings=[])
    try:
        row = frappe.db.get_value("Company", company, ["chart_of_accounts"], as_dict=True)
        if not row:
            r["warnings"].append(f"公司 {company} 不存在"); return r
        r["is_cn_chart"] = is_cn_chart(row.get("chart_of_accounts"))
        if not r["is_cn_chart"]:
            r["ok"] = True; return r                           # 不归本自检管，不判失败
        expected = _flatten(load_cn_chart_tree())              # {(科目号, 科目名): 顶层 root_type}
        actual = {(a.get("account_number") or "", a.get("account_name")): a.get("root_type")
                  for a in frappe.get_all("Account", filters={"company": company},
                                          fields=["account_number", "account_name", "root_type"])}
        r.update(checked=True, account_count=len(actual), expected_account_count=len(expected))
        r["missing_from_chart"] = sorted(f"{n} {m}" for (n, m) in expected.keys() - actual.keys())
        r["extra_accounts"]     = sorted(f"{n} {m}" for (n, m) in actual.keys() - expected.keys())
        r["root_type_mismatches"] = sorted(f"{n} {m}: 应为 {rt}，实为 {actual[(n, m)]}"
                                           for (n, m), rt in expected.items()
                                           if (n, m) in actual and actual[(n, m)] != rt)
        d = frappe.db.get_value("Company", company, list(DEC097_FIELDS), as_dict=True) or {}
        r["missing_defaults"] = [f for f in DEC097_FIELDS if not d.get(f)]
        r["ok"] = not (r["missing_from_chart"] or r["root_type_mismatches"] or r["missing_defaults"])
    except Exception as e:
        r["ok"] = False; r["warnings"].append(f"自检自身出错：{e!r}")
    return r

def check_all_cn_companies():
    try:
        names = frappe.get_all("Company", filters={"chart_of_accounts": CN_CHART_NAME}, pluck="name")
    except Exception as e:
        return [ChartCheckResult(company="*", checked=False, ok=False, ..., warnings=[f"自检自身出错：{e!r}"])]
    return [check_company_chart(n) for n in names]
```

- `_flatten`：顶层节点的 `root_type` 向下继承；元数据键取 `get_chart_metadata_fields()`。
- **本 Stage 不注册 `after_migrate`**：IM-007 属 S8G-S1（需求 NV-074）。本 Stage 只在建 `HDTH` 后调用一次（TS-021）。
- 本函数签名同步进路线文档 §七 与架构文档 §3.1 ⑧，这两处由本轮回执登记为「交后续同步」，C 步不改跨轮演进产物（见回执）。

### 验证方式
`tests/test_selfcheck.py`，对应 SL-003 验收第 3、6 条。「自检内部出错」用 `mock.patch("frappe_china.accounting.selfcheck.frappe.get_all", side_effect=RuntimeError)` 造。

---

## 任务 8：税类别、税模板、税规则；端到端测试（对应切片 SL-004）

### 目标
12 个模板的税行按科目号精确命中、不新建科目（需求 §4.6、AC-002）；跑通首个 Phase 方案要求的端到端最简路径（总纲 §四 P-2）。

### 具体改动

**不用** erpnext 的 `from_detailed_data`：它经 `get_or_create_account` 按名兜底、找不到就新建科目（`taxes_setup.py:209-242`），还会丢掉 `included_in_print_rate`（`:161-163`）。改为自己建，逻辑如下。

**`frappe_china/cn_tax/data/tax_setup.json`**

- `tax_categories`（9 个）：`P13专票含税`、`P13专票未税`、`P9专票含税`、`P6专票含税`、`P3专票含税`、`P3专票未税`、`P1专票含税`、`P1专票未税`、`P0无税`
- `sales`（5 个，科目 `2221005`）：

| title／tax_category | rate | included |
|---|---|---|
| P13专票含税 | 13 | 1 |
| P13专票未税 | 13 | 0 |
| P3专票含税 | 3 | 1 |
| P3专票未税 | 3 | 0 |
| P0无税 | 0 | 0 |

- `purchase`（7 个，科目 `2221001`）：

| title／tax_category | rate | included |
|---|---|---|
| P13专票含税 | 13 | 1 |
| P13专票未税 | 13 | 0 |
| P9专票含税 | 9 | 1 |
| P6专票含税 | 6 | 1 |
| P3专票含税 | 3 | 1 |
| P1专票含税 | 1 | 1 |
| P0无税 | 0 | 0 |

- `tax_rules`（13 条）：
  - zelin `tax_rule.csv` 11 行原样保留：销项 P13含税／P3含税／P13未税／P3未税，优先级 1；进项 P13含税／P3含税／P1含税／P13未税／P0无税，优先级 1；国家为 China 的默认规则，销项与进项各一条，优先级 99，都落 `P13专票含税`。
  - 新增两条：进项 `P9专票含税`、`P6专票含税`，优先级 1。

**`frappe_china/accounting/taxes.py`**

```python
def setup_cn_taxes(company: str) -> dict:
    """幂等。返回 {"categories": n, "templates": n, "rules": n}（本次新建数）。"""
    data = _load("tax_setup.json")
    abbr, cost_center = frappe.db.get_value("Company", company, ["abbr", "cost_center"])
    heads = {n: frappe.db.get_value("Account", {"company": company, "account_number": n, "is_group": 0})
             for n in ("2221005", "2221001")}
    missing = [n for n, v in heads.items() if not v]
    if missing or not cost_center:
        frappe.throw(f"公司 {company} 建税失败：缺科目 {missing}" + ("；缺默认成本中心" if not cost_center else ""))
    # 1. 税类别：按 title 判重（Tax Category 以 title 命名），缺的 insert
    # 2. 模板：按 (title, company) 判重，缺的 insert，每个模板一行税行：
    #    {"category": "Total", "charge_type": "On Net Total", "account_head": heads[号],
    #     "rate": rate, "included_in_print_rate": included, "cost_center": cost_center,
    #     "description": f"{'销项税额' if 销项 else '进项税额'} {rate}%",
    #     [采购另加 "add_deduct_tax": "Add"]}
    #    模板 {"title", "company", "tax_category", "is_default": 0}；正常 insert()，不置 ignore 标志（HT-009）
    # 3. 规则：模板名 = f"{title} - {abbr}"；按 (tax_type, tax_category, billing_country, shipping_country,
    #    priority, company) 判重，缺的 insert
```

- 不写补偿 SQL（zelin `utils.py:47-57` 那段不按公司过滤、会改全站模板）：「含税」直接写在税行上（需求 §4.6.1）。
- 在 `company.build_cn_company` 末尾加上 `setup_cn_taxes(doc.name)`（TS-006 留的位置），并在 `test_company.py` 补断言：建公司后税类别、模板、规则已就绪。

**`tests/test_taxes.py`**：对应 SL-004 验收第 1–4 条。

**`tests/test_e2e_minimal.py`**：对应 SL-004 验收第 5–6 条。
- 测试夹具：非库存物料 `_FCT 弹簧样品`；客户 `_FCT 客户`；供应商 `_FCT 供应商`；运费物料 `_FCT 运费`。运费的费用科目显式设为 `5601150 销售费用_运输、仓储费`。
- 售价走 `Standard Selling`。
- 开票：`si.taxes_and_charges = "P13专票含税 - {abbr}"`；`si.set_taxes()`；`insert()`；`submit()`。
- 然后按 `voucher_no` 查 GL Entry 断言三组数；退货那张用 `is_return=1`。

### 验证方式
- 跑 `test_taxes.py` 与 `test_e2e_minimal.py`；
- 在测试站界面上以 Administrator 登录 `http://test.localhost:8000`，新建一张公司：确认下拉里有 `小企业会计准则(2024)`，科目树预览按中国结构展开。这是 AC-012 的界面层证据，截图存 `Spike/`。
- 核演示站基线。
