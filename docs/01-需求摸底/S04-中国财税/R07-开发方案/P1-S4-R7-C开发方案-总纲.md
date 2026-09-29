# P1-S4 中国财税 —— 开发方案·总纲

**版本**：v1.0｜**日期**：2026-09-29｜**编写者**：Claude（Opus 5.5）
**产出步骤**：P1-S4-R7 · `plannedDev` C 步（`build`）
**来源需求**：[B 需求文档](../R06-需求文档/P1-S4-R6-B需求文档.md) v1.0（下称「需求」）＋本轮 [C 讨论记录](P1-S4-R7-C讨论记录.md)（DEC-116…119）
**状态值与复核建议**：不在本文件——见 [P1-S4-R7-C回执](P1-S4-R7-C回执.md)
**执行者**：Claude（路线文档 §四 S4 的偏离：D 步不交 CodeX）

> **读法**：本方案是 D 步的唯一权威依据，也是 E 步的核对清单。总纲装跨 Part 的约定、接口契约与执行纪律；各 Part 按「切片 → 任务」展开。**凡与需求字面不一致处，以本方案为准**，偏离逐条列在本文件 §五，理由在 C 讨论记录。
> **编号**：切片 `SL-`、任务 `TS-`、技术假设 `HT-` 为本方案内编号。**需求文档里也有 `TS-` 编号，二者不是一回事**，引用需求的任务一律写「需求 TS-00x」。

---

## 一、概述

**做什么**：在自有 app `frappe_china` 里做出一套符合《小企业会计准则》的账与表：中国科目表建账、增值税模板、月末结转、资产负债表／利润表／现金流量表（月报与年报两种口径），以及银行流水导入与对账。另外装好中文字体，在演示站清站后建出 `华东弹簧有限公司`（`HDTH`）。

**完成标准**：十个切片的验收条件全部通过（见 §三），并满足首个 Phase 方案的四条额外要求（§四）。验收一律要有正向证据，不能以「没报错」代替。

**Part 索引**

| Part | 文件 | 内容 | 切片 | 任务数 |
|---|---|---|---|---|
| 1 | [Part1](P1-S4-R7-C开发方案-Part1.md) | 基础设施、安装期设置、科目表建账、增值税与端到端最简路径 | SL-001…SL-004 | 8（TS-001…008） |
| 2 | [Part2](P1-S4-R7-C开发方案-Part2.md) | 月末结转（自有结转凭证） | SL-005 | 2（TS-009…010） |
| 3 | [Part3](P1-S4-R7-C开发方案-Part3.md) | 取数层、行映射、资产负债表、利润表、漏科目检查 | SL-006 | 4（TS-011…014） |
| 4 | [Part4](P1-S4-R7-C开发方案-Part4.md) | 现金流量表、打印与导出、银行对账、演示站落地、全量回归 | SL-007…SL-010 | 8（TS-015…022） |

---

## 二、关键架构决策（本方案新定，C 步职责内）

| # | 决策 | 理由 |
|---|---|---|
| A1 | **开发与验收全在独立测试站点 `test.localhost` 上做**，演示站 `erx.localhost` 只在最后一个切片清站并建 `HDTH` | ① 单号序列全站共用，测试单据会占掉演示公司的前几个发票号，删公司也恢复不了；② 清站不可逆，挪到最后可以把风险集中在一次操作里；③ 需求 §4.13 第 4 条「验收数据不留在演示公司」由此自然满足 |
| A2 | **清站手段取「重装站点」**（`docker/README.md`「重装站点」节的既有流程，三个坑已记在那里） | 比「删交易再删公司」干净。删交易需要按依赖逆序删十几类单据，删漏了会挡住删公司（Tax Rule、Fiscal Year Company 子表都会挡）。**执行前仍须用户当场确认**（DEC-101） |
| A3 | **建科目树直接调用上游 `create_charts(company, custom_chart=tree)`**，不自写建树逻辑 | 该函数的 `custom_chart` 参数本来就能绕过 `get_chart`（`chart_of_accounts.py:16`），元数据键取的是 `get_chart_metadata_fields()`，`account_category` 也会写入。需求 §4.4.3「以上游为底、不硬编码键表」由此原样满足，胶水层缩小到只剩编排 |
| A4 | **被覆盖的三个方法只对 HTTP 调用生效**（`frappe/__init__.py:1577-1580`，只在 `handler.py:67` 等入口解析覆盖）⇒ 本 app 的 Python 代码一律显式调用自己的实现，不依赖覆盖 | 原生 `create_charts` 在 Python 内部调的是原生 `get_chart`，按中文表名取会得到 `None` |
| A5 | **行映射按「科目号 → 该科目及其全部下级」定义**，不按科目号前缀，也不列死明细科目名 | ① zelin 表里 `101010 股票` 号码不带 `1101` 前缀，按前缀会漏；② 将来补弹簧明细科目（`SH-P1S4003`）时，新科目挂在已映射的组下自动被覆盖，映射不用改 |
| A6 | **报表列头与行名写成中文字面量**，不经 Python 侧 `_()`；另设一条自动测试守住 LG-134（`zh` 下 `_(列头) == 列头`） | 屏幕路径不经 `_()`，XLSX 与 PDF 两条路径会经过（`query_report.py:692`、`print_grid.html:28`）。把 S6 须遵守的约束做成可执行的测试，S6 往词典里加撞名键时测试会立即失败 |
| A7 | **法定格式的 PDF 在服务端渲染**：`statements/printing.py` 用 Jinja 模板（文件放 `frappe_china/templates/statements/`，以 `templates/statements/<名>.html` 引用）输出标题、表号、「编制单位／日期／单位：元」行与账户式双栏，经 `frappe.utils.pdf.get_pdf` 生成，报表页加一个按钮下载。原生菜单的「打印／PDF」保留不动 | ① 原生 `print_grid` 只能输出一张单表，标题取报表名，没有表号；② 报表目录下的 `.html` 模板在浏览器里渲染，执行者无法自动化验证 PDF（本项目尚无浏览器自动化，S7 才建）。服务端渲染后，测试能直接取 PDF 字节核对文字与字体 |
| A8 | 普通包命名为 **`frappe_china/accounting/`**，模块目录为 `frappe_china/cn_tax/`（`modules.txt` 一行 `CN Tax`） | ADR-0012 把包名留给 C 步。`accounting` 与模块名不同，不会被当成模块；按职责命名，与官方 app 的 `api/`、`utils/`、`overrides/` 同一风格 |
| A9 | **界面文字（DocType 与字段 label、提示、按钮）一律用英文源词**，经 `_()`／`__()` 翻译；本 app 自己新增的词条由 `frappe_china/translations/zh.csv` 提供中文（TS-020）。**csv 只收 frappe／erpnext 官方词典里没有的键**，已有的键沿用官方译文 | ADR-0006「译名全走 csv 单一来源」。只收新键是为了不在全站范围内改动官方译文（csv 是全站生效的）。S6 的 CR-002 往同一个文件里继续追加 |
| A10 | **结转凭证编号按「公司缩写＋年月」分段计数**：`JZ-{abbr}-{yyyymm}-###`，由控制器的 `autoname` 生成 | 会计按月翻凭证。naming series 的 `.YYYY.`／`.MM.` 取的是当天日期、不是记账日期（`frappe/model/naming.py:349`），不能用 |

---

## 三、切片划分与验收（索引；各切片的完整验收条件在所在 Part）

| 切片 | 功能点（需求编号） | 验收条件要点 | Part |
|---|---|---|---|
| **SL-001** 工程基础设施（豁免「用户可感知」） | 测试站点、中文字体（需求 TS-002／DEC-095）、app 骨架与测试脚手架（需求 TS-004）、中文名报表探针 | 测试站点三个 app 装成、测试可跑且通过、`fc-list :lang=zh` 非空、中文名报表能经 `frappe.desk.query_report.run`（HTTP 入口所调的函数）执行；**演示站数据未被触碰**；字体安装失败时降级为告警、不中断 `setup.sh` | 1 |
| **SL-002** 安装期设置 | 需求 TS-005／AC-010／DEC-100 | 45 个中文单位存在；既有单位的启用状态逐条不变；凑整合计关闭；重装不产生重复；System Settings 未被本 app 改动 | 1 |
| **SL-003** 中国科目表建公司 | 需求 TS-006／007、AC-001／005／006／012、DEC-097／103 | 下拉、预览、取表三个覆盖；266 科目双向一致；22 个默认科目；同一进程两个顺序各建两家公司；自检函数在异常输入下只告警、不抛异常；非中国公司选本表会被拒 | 1 |
| **SL-004** 增值税与**端到端最简路径** | 需求 TS-008、AC-002／003、DEC-094 | 9 个税类别、5＋7 个模板、13 条规则；税行按科目号精确命中且不新建科目；**建公司 → 开票 → 总账**整条路径跑通（含半分舍入边界） | 1 |
| **SL-005** 月末结转 | 需求 TS-011、AC-007／008、DEC-099／118 | 三类结转凭证按序生成，12 月另生成本年利润结转；不重复、逆序取消、可重做；留抵月、多交月、草稿提醒、上月未结、结转不完整、冻结期都有明确结果 | 2 |
| **SL-006** 资产负债表与利润表 | 需求 TS-003／012／013、AC-004 ③④、AC-011、DEC-087／117 | 行次与财政部原文一致；平衡；跨年只含本年；结转前后利润表数不变；年报口径；映射缺科目时报错而不是出 0；漏科目检查 | 3 |
| **SL-007** 现金流量表 | 需求 TS-010／014、AC-004 ⑤、DEC-096／117 | 四件套可用；本年累计期末现金余额等于科目余额（修 zelin 一处累加缺陷）；逐月按序；未编码行拒绝提交；年报口径 | 4 |
| **SL-008** 三表打印与导出 | 需求 AC-004 ①②、DEC-095 | `zh` 会话下屏幕、XLSX、PDF 三处列头逐字合规；PDF 中文可读、字体已嵌入 | 4 |
| **SL-009** 银行流水导入与对账 | 需求 TS-015、AC-009、DEC-082／086 | GBK、带抬头与合计行的仿网银流水导入后逐字无乱码、条数相符；一笔自动核销；重复导入不重复建；坏行响亮失败 | 4 |
| **SL-010** 演示站落地 | 需求 TS-001／009／016、AC-001／005／013／014、DEC-101 | 经用户确认后清站；站点设置还原（含 DEC-116）；`HDTH` 建成、自检通过；站上只有这一家公司；README 并入登记完整；全量回归通过 | 4 |

执行每个切片前，对照该切片验收条件检查方案覆盖性——如发现按方案写出的代码无法通过验收条件，暂停反馈，不硬写。

---

## 四、首个 Phase 方案的四条额外要求（写成验收条件）

P1 是本项目第一个写代码的 Phase，上游是 devBlueprint 产出的路线文档，故 C Spec 的四条额外要求适用。E 步把下面四条当作验收条件逐条核对。

| # | 要求 | 本方案的落点 | 验收条件 |
|---|---|---|---|
| P-1 | 含工程基础设施切片 | SL-001 | SL-001 验收条件全部通过 |
| P-2 | 含端到端最简路径切片 | SL-004（装 app → 以中国科目表建公司 → 开 13% 含税发票 → 总账贷记 `2221005`） | SL-004 验收第 5 条「这条路径能真的跑通」的三组数字逐位相符 |
| P-3 | 路线文档标「仅定义契约、不实现」的接口，要有「只定 Protocol」任务 | **本 Stage 没有这类接口**：路线文档 §七 里归 S4 的只有「建账结果自检函数」，它要实现、不是只定契约（TS-007 实现并定签名）；标「仅定义契约」的「建单辅助函数」归 S7。另把 S6 须遵守的 LG-134 做成可执行约束（A6） | 回执写明「无仅定义契约的接口」及判据；TS-007 的签名与 §六 接口契约一致；LG-134 守卫测试存在且通过 |
| P-4 | 关键技术假设已验证 | §七 技术假设表 | D 回执逐条写明 HT-001…HT-013 的验证结果；任一条不成立时，依赖它的任务按执行纪律暂停 |

---

## 五、相对需求文档的偏离与更正

| # | 需求原文 | 本方案 | 依据 |
|---|---|---|---|
| 1 | §4.7「生成三张 Journal Entry」 | 生成三张**自有结转凭证**（`Month End Closing Voucher`，每类一张），12 月加一张本年利润结转凭证。「按序生成、逆序取消、不重复、可机械识别」原样保留 | DEC-118（Journal Entry 的折旧类型校验使损益结转在计提过折旧的月份提交不了，`journal_entry.py:349-357`） |
| 2 | §4.13 第 2 条把 `Banker's Rounding (legacy)` 称为「逢 5 取偶」 | 更正：两位小数下它是逢 5 向正无穷进位，只在取整时才逢 5 取偶（容器实跑）。站点改设 `Commercial Rounding` | DEC-116 |
| 3 | §4.8／§4.9 行次「来自两个非官方转载站互证」 | 改为按**财政部会计司原文**（附录第 68–82 页）。行次全部一致，另补两个合计行（非流动负债合计 46、负债合计 47）；LG-145 定为「期末余额｜年初余额」；利润表第 3 行按财会〔2016〕22 号称「税金及附加」 | 讨论记录第 1 步 ② |
| 4 | 利润表、现金流量表只有月报格式 | 增加年报口径：第二金额列改为「上年金额」 | DEC-117（原文编制说明） |
| 5 | §4.7.1 ② 附加税计税依据「＝① 的结转额（贷方情形）＋本月已交税金」 | 一般化为「本月已交税金＋本月转出未交增值税－本月转出多交增值税」，下限为 0。需求写到的两种情形结果不变；需求没写的「多交」情形，按原式会多计附加税 | 会计推算（回执「拿不准处」第 1 条，待会计确认） |
| 6 | §4.8「未分配利润 ＝ 3103＋3104」 | 另加「尚未结转的损益科目余额」。已结转的月份这一项为 0，与需求原式相同；未结转时报表仍然平衡，同时给出「本月尚未结转」提示 | 使未结转月份的资产负债表也能平衡。AC-008「结转前后未分配利润相同」因此在任何月份都成立 |
| 7 | 需求 TS-004「骨架排在清站之后」 | 骨架装在测试站点上，最早做；演示站最后装 | A1 |
| 8 | 需求 TS-003「法定报表格式核准」列为 D 步任务 | 核准已在 C 步完成（原文取得），行映射表直接写进 Part3。D 步只做实现 | 原文已取得 |
| 9 | §4.4.3「挂 Company 的 `before_insert`／`on_update`／`after_insert`」 | 只挂 `before_insert` 与 `on_update`。`after_insert` 没有职责：zelin 用它给文档打「本次是新建」标记，本方案在 `before_insert` 里直接给同一个文档对象打标记 | 少一个空钩子。架构文档 §3.1 对外接口 ② 写的「3 个 handler」待同步（回执「交后续同步」） |

---

## 六、接口契约

**新增文件的模块职责与对外接口。** 函数签名是契约，D 步不得改；内部实现由 D 步判断。

```python
# ---- frappe_china/accounting/chart.py  —— 科目表数据与三个 whitelisted 覆盖 ----
CN_CHART_NAME: Final[str] = "小企业会计准则(2024)"   # 与 JSON 的 "name" 逐字相同

def load_cn_chart_tree() -> dict: ...                 # 每次返回新对象；读 cn_tax/chart_of_accounts/*.json（__file__ 相对定位）
def is_cn_chart(chart_template: str | None) -> bool: ...

@frappe.whitelist()
def get_charts_for_country(country: str, with_standard: bool = False) -> list[str]: ...
@frappe.whitelist()
def get_chart(chart_template: str, existing_company: str | None = None) -> dict | None: ...
@frappe.whitelist()
def get_coa(doctype: str, parent: str, is_root: bool | None = None, chart: str | None = None) -> list[dict]: ...

# ---- frappe_china/accounting/company.py  —— Company 三个 doc_events 与建账编排 ----
def before_insert(doc: "Company", method: str) -> None: ...
def on_update(doc: "Company", method: str) -> None: ...
def build_cn_company(doc: "Company") -> None: ...      # 科目树→默认科目→仓库与科目→物料组→付款方式→税；由 on_update 调用
                                                       # 收 doc 而非公司名：默认科目用 doc.db_set 写，内存里的 doc 同步更新，
                                                       # 调用方随后 doc.save() 不会用旧值把默认科目冲掉

# ---- frappe_china/accounting/selfcheck.py —— 建账结果自检（消费方：S8G-S1 的 IM-007） ----
class ChartCheckResult(TypedDict):
    company: str
    checked: bool                  # 公司存在且用本科目表时为 True；否则 False（此时 ok 的含义见下）
    ok: bool                       # checked 时：无缺科目、root_type 全对、6 个默认科目非空；
                                   # 未 checked：公司不存在或自检自身出错 → False，公司用别的科目表 → True
    is_cn_chart: bool | None       # 公司不存在时为 None
    account_count: int | None
    expected_account_count: int    # = JSON 节点数（266）
    missing_from_chart: list[str]  # JSON 有、库里没有的「科目号 科目名」
    extra_accounts: list[str]      # 库里有、JSON 没有的（用户自建明细属正常，只报不判失败）
    root_type_mismatches: list[str]
    missing_defaults: list[str]    # 6 个 DEC-097 字段中为空的
    warnings: list[str]

def check_company_chart(company: str) -> ChartCheckResult: ...   # 永不抛异常；取值一律 .get() 语义
def check_all_cn_companies() -> list[ChartCheckResult]: ...       # 供 after_migrate 调用

# ---- frappe_china/accounting/closing.py —— 月末结转 ----
CLOSING_TYPES: Final = ("VAT Transfer", "Surtax Accrual", "P&L Transfer", "Year-end Profit Transfer")
PL_EXCLUDED_SUBTYPES: Final = ("P&L Transfer", "Year-end Profit Transfer")  # 利润表取数排除

@frappe.whitelist()
def generate_month_end_closing(company: str, fiscal_year: str, month: int,
                               ignore_drafts: bool = False) -> dict: ...
    # 返回 {"created": [凭证名...], "drafts": [...], "message": str}
@frappe.whitelist()
def cancel_month_end_closing(company: str, fiscal_year: str, month: int) -> list[str]: ...
def month_closing_state(company: str, fiscal_year: str, month: int) -> dict: ...
    # {"closed": bool, "complete": bool, "vouchers": [...], "issues": [str]}；报表与前置检查共用

# ---- frappe_china/accounting/statements/ ——取数层、行映射、三张报表的计算 ----
# 详见 Part3 §接口；报表目录下的 execute() 只做一行转发

# ---- frappe_china/accounting/bank_import.py —— 银行流水前置处理 ----
def preprocess_statement(name: str) -> dict: ...   # name = Bank Statement Preprocess 的名；读→清洗→去重→生成 UTF-8 csv；不导入
@frappe.whitelist()
def run_preprocess_and_import(name: str) -> dict: ...

# ---- frappe_china/install.py ----
def after_install() -> None: ...                       # 只接线：调用 accounting.install 的两个入口
```

**`hooks.py` 要点**（只接线、不写逻辑）：

```python
app_name = "frappe_china"; app_title = "Frappe China"; app_license = "MIT"
required_apps = ["erpnext"]
after_install = "frappe_china.install.after_install"
override_whitelisted_methods = {
  "erpnext.accounts.doctype.account.chart_of_accounts.chart_of_accounts.get_charts_for_country":
      "frappe_china.accounting.chart.get_charts_for_country",
  "erpnext.accounts.doctype.account.chart_of_accounts.chart_of_accounts.get_chart":
      "frappe_china.accounting.chart.get_chart",
  "erpnext.accounts.utils.get_coa": "frappe_china.accounting.chart.get_coa",
}   # 不覆盖 frappe.desk.treeview.get_all_nodes（需求 §4.4.2）
doc_events = {"Company": {"before_insert": "frappe_china.accounting.company.before_insert",
                          "on_update":     "frappe_china.accounting.company.on_update"}}
fixtures = [{"dt": "Custom Field", "filters": [["name", "in", [
                "Account-cash_flow_code", "Customer-cash_flow_code", "Supplier-cash_flow_code",
                "Company-cn_urban_construction_tax_rate"]]]},
            {"dt": "Cash Flow Code"}]
# 不注册 regional_overrides、override_doctype_class、update_gl_dict_with_app_based_fields（需求 §4.15）
```

**交给 S6 的约束**（LG-134，A6）：`frappe_china.accounting.statements.labels.LEGAL_LABELS` 列出三张报表全部法定列头与行名；`frappe_china/tests/test_legal_labels.py` 断言 `zh` 下每一项 `_(x) == x`。S6 的 CR-002 往 `translations/zh.csv` 或 `Translation` 表加词条后，必须跑这条测试。

---

## 七、技术假设

| 编号 | 假设内容 | 状态 | 验证方式 | 不成立时 |
|---|---|---|---|---|
| HT-001 | 名字为纯汉字的 Script Report（如 `小企业资产负债表`）能被导入并执行：`scrub()` 后的目录名是合法 Python 标识符，`frappe.get_attr` 可载入，且能经 Windows 宿主 bind mount 与 git 正常保存 | 未验证 | TS-003：建四个报表桩，经 HTTP 调 `frappe.desk.query_report.run` 各返回一次；`git status` 路径显示正常 | 暂停反馈。备选：ASCII 报表名，中文标题交打印模板与 S6 译名 |
| HT-002 | 上游 `create_charts(company, custom_chart=tree)` 建出的科目，与 V-19 实测的 zelin 建法逐项一致（科目号、科目名、上级、是否组、`root_type`、`account_type`） | 未验证 | TS-006 测试逐节点比对 JSON | 暂停反馈 |
| HT-003 | 装 `fonts-noto-cjk` 后，wkhtmltopdf 出的报表 PDF 汉字可读 | 未验证（LG-135） | TS-002 装字体后用一份含中文的 HTML 调 `frappe.utils.pdf.get_pdf`；宿主 `pdftotext` 能取出中文，并目视核一次 | 暂停反馈（RS-012：另查渲染链） |
| HT-004 | 以 `AccountsController` 为基类的自有单据：`get_gl_dict` 可用；`make_gl_entries(gl_map, merge_entries=False)` 能写总账；`make_reverse_gl_entries(voucher_type=, voucher_no=)` 能冲销；覆写的 `get_voucher_subtype()` 会写进每条 GL Entry | 未验证（期末结账单同法，`period_closing_voucher.py:26/260/298`） | TS-009 测试：提交后查 GL 条数、借贷、`voucher_subtype`；取消后原分录 `is_cancelled=1` | 暂停反馈 |
| HT-005 | 在尚无公司的站点上 `Global Defaults` 能正常 `save()`，且 `toggle_rounded_total` 为 8 类单据建出 Property Setter | 未验证 | TS-004 测试 | 改用 `db.set_single_value` ＋显式调 `toggle_rounded_total()`，并在回执说明 |
| HT-006 | app 级 `workspace_sidebar/cn_tax.json`（名为 `CN Tax`、`items` 为空）能压住 `CN Tax` 模块的自动侧栏：自动生成时被守卫跳过，自身又因无可见条目被丢弃 | 未验证（读码：`workspace_sidebar.py:243`、`boot.py:500-504`） | TS-003：`frappe.boot` 的 `sidebar_items` 里无 `cn tax` 键 | 暂停反馈 |
| HT-007 | XLSX 导出的列头是 `_(columns[].label)`（`query_report.py:692`），法定中文列头在 `zh` 下原样输出；两个同名列头（如两个「行次」）在 XLSX 里各占一列、不被合并 | 未验证（读码） | TS-017：经 `export_query` 导出，用 `openpyxl` 读表头行 | 暂停反馈 |
| HT-008 | 新建 Company 时执行顺序为：`before_insert` → 控制器 `validate` → `db_insert` → `after_insert` → 控制器 `on_update`（此时已建成本中心）→ 本 app 的 `on_update` 钩子 | 读码已确认（`document.py:480-513`、`:1635-1643`），未实跑 | TS-006 测试断言：钩子运行时公司已有成本中心、尚无科目 | 暂停反馈 |
| HT-009 | 税模板以正常 `insert()` 建（不置 `ignore_validate`／`ignore_links`）能通过全部校验 | 未验证 | TS-008 | 改为逐项查明是哪条校验挡住，再定；不得一律加 ignore 标志 |
| HT-010 | 用程序创建并启动 `Bank Statement Import` 的路线可行（先建单、再挂文件、再 `start_import()`） | **已验证**（V-22 seg10，`Spike/V22-seg10-clean-shipped.py:124-168`） | — | — |
| HT-011 | bench 环境自带 `openpyxl` 与 `xlrd` | **已验证**（`env/lib/python3.14/site-packages` 清点） | — | — |
| HT-012 | 控制器 `autoname()` 里用 `frappe.model.naming.make_autoname(f"JZ-{abbr}-{yyyymm}-.###")` 能按「前缀」独立计数（每个公司每月从 001 起） | 未验证（读码：前缀即 `tabSeries` 的键；已查实 naming series 的 `.YYYY.` 取当天日期、不能用，`naming.py:349`） | TS-009 测试：同公司两个月、两公司同月各建两张，看编号 | 暂停反馈 |
| HT-013 | `IntegrationTestCase` 在类结束时回滚；本 app 的测试**不 import `erpnext.tests.utils`**（该模块 import 即建 `_Test Company` 并把 System Settings 改成 `Asia/Kolkata`／`en`，`erpnext/tests/utils.py:227-233、3013`） | 读码已确认，未实跑 | TS-003：跑一遍测试后核对测试站 System Settings 未变 | 暂停反馈 |
| HT-014 | `frappe.db.after_rollback.add(fn)` 注册的回调在事务回滚时执行（`database.py:131-132`、`:1205`） | 读码已确认，未实跑 | TS-006：公司插入在 validate 阶段失败后，断言标志已复位 | 去掉该行。标志仍由下一家公司的 `before_insert` 显式覆盖（RW-07 的主防线不受影响），回执里说明 |

**判为「成熟做法、未列入」的技术点**（这个判断本身可能错，见回执复核建议第 3 条）：Custom Field 以 fixtures 导入；Script Report 的 `execute()` 返回六元组；`frappe.qb` 聚合查询 GL Entry；`frappe.enqueue` 不用（全部同步）；`openpyxl` 读 xlsx。

---

## 七之二、工作量重估（LG-141／RW-09）

按任务逐项估，单位人日，口径是「含测试、写到验收全过」：

| 任务 | 人日 | 任务 | 人日 |
|---|---|---|---|
| TS-001 测试站 | 0.25 | TS-012 资产负债表 | 1–1.5 |
| TS-002 字体 | 0.25 | TS-013 利润表 | 1–1.5 |
| TS-003 骨架与探针 | 0.5 | TS-014 漏科目检查 | 0.25 |
| TS-004 安装期 | 0.25 | TS-015 现金流四件套 | 1–1.5 |
| TS-005 科目表覆盖 | 0.5 | TS-016 现金流量表 | 0.5–1 |
| TS-006 建账钩子 | 1–1.5 | TS-017 PDF 与导出 | 1–1.5 |
| TS-007 自检 | 0.5 | TS-018 银行前置处理 | 1–1.5 |
| TS-008 税与端到端 | 1–1.5 | TS-019 对账测试 | 0.5–1 |
| TS-009 结转凭证单据 | 1–1.5 | TS-020 README 与 csv | 0.5 |
| TS-010 结转计算 | 2–3 | TS-021 演示站 | 0.5 |
| TS-011 映射引擎与数据集 | 1.5–2.5 | TS-022 全量回归 | 0.25–0.5 |
| **合计** | | | **16.25–23.5** |

**比需求 §4.16 的 11.5–18.25 多 4.75–5.25 人日。** 增量主要来自四处：
- BS＋PL 改为自写。原估 1–1.5 按「抄 zelin」算，现 TS-011～014 合计 3.75–5.75，LG-141 所说的偏乐观应验；
- 结转凭证改为自有单据（DEC-118），约 +1；
- 年报口径（DEC-117），约 +0.5；
- 测试站与两年测试数据集，约 +1。

这组数字同样是读码估算，一项都没有实做过。回写路线文档的事见回执「交后续同步」。

## 八、并行开发说明

本方案默认**顺序执行**。可并行的只有两组，前提是写入的文件互不重叠：

| 组 | 任务 | 可访问的文件范围 | 前置 |
|---|---|---|---|
| 甲 | TS-002 字体 | `docker/scripts/setup.sh`、`docker/README.md` | 无 |
| 乙 | TS-018／TS-019 银行对账 | `frappe_china/cn_tax/doctype/bank_statement_*`、`frappe_china/accounting/bank_import.py`、`frappe_china/tests/test_bank_import.py` | TS-008 |

其余任务都会写 `hooks.py`、`modules.txt` 或共用的 `accounting/statements/`，**不标并行**。

## 九、执行顺序

```
TS-001 测试站 ─┬─ TS-003 骨架 ── TS-004 安装期 ── TS-005 科目表覆盖 ── TS-006 建账钩子 ── TS-007 自检 ── TS-008 税与端到端
TS-002 字体 ──┘                                                                                        │
                                          ┌──────────────────────────────────────────────────────────┤
                                          │                                                          │
                     TS-009 结转凭证 ── TS-010 结转生成                        TS-018 银行前置处理 ── TS-019 对账（可与左支并行）
                                          │
                     TS-011 取数与映射 ── TS-012 资产负债表 ── TS-013 利润表 ── TS-014 漏科目
                                          │
                     TS-015 现金流四件套 ── TS-016 现金流量表 ── TS-017 打印与导出
                                          │
                     TS-020 README ── TS-021 演示站（须用户确认）── TS-022 全量回归
```

---

## 十、执行纪律（给执行者，随方案走）

1. **切片前反查**：执行每个切片前，对照该切片验收条件检查方案覆盖性——如发现按方案写出的代码无法通过验收条件，暂停反馈，不硬写。
2. **假设先验**：任务依赖 §七 中「未验证」的假设时，先验掉再写；不成立按该行「不成立时」处理，表中写「暂停反馈」的就停下来报用户，不绕路。
3. **中断续跑**：从 D 回执里第一个未完成的任务续做。执行进度只写 D 回执，**不回写本方案**。
4. **站点安全**：
   - TS-001…TS-020 **只动 `test.localhost`**，不得对 `erx.localhost` 做任何写操作。
   - **D 步期间不得跑 `docker/up.sh`**：`setup.sh` 第 6 段会把 `apps/` 下的每个 app 装到 `.env` 指定的站点（即演示站，`setup.sh:229-240`），`frappe_china` 建出后跑一次就会装上演示站。确需重建容器时先报用户。
   - 每个切片结束时核对一次演示站基线：Company 1（`华东弹簧`）、GL 22、SLE 12、Account 95。
   - TS-021 清站前，**必须当场向用户确认范围与动作**（DEC-101）；未获确认即停。
5. **测试纪律**：
   - 自有测试不得 import `erpnext.tests.utils`（HT-013）。
   - 涉及语言的断言一律显式 `frappe.local.lang = "zh"`（开发守则「探针三条纪律」第 2 条）。
   - 会触发 `frappe.log_error` 的测试，清理时只删能证明是自己造的行（同上第 1 条）。
6. **版本管理**：
   - `frappe_china` 用 `bench new-app --no-git` 生成。**不 `git init`、不 commit、不建远端、不 push**，这些都须用户许可（CLAUDE.md「版本管理操作规则」）。
   - 主仓库的改动（`docker/`、`docs/`、`.vscode/`）同样只写不提交。
7. **不静默**：凡「查不到、算不出、对不上」一律报错或告警，不得输出 0 或空列表了事（需求 §4.11 第 4 条、开发守则「静默失败」）。
8. **最后一个任务（TS-022）做全量回归**：跑本 app 全部测试，并复核演示站最终状态。
