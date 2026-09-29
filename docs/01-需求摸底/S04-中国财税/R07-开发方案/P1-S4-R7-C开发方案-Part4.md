# P1-S4 开发方案·Part4：现金流量表、打印与导出、银行对账、演示站落地

**来源需求**：[B 需求文档](../R06-需求文档/P1-S4-R6-B需求文档.md) §4.10、§4.11、§4.12、§4.13，AC-004／009／013／014｜**前置依赖**：Part3（TS-011 数据集、`ledger.py`、`engine.py`）｜**日期**：2026-09-29｜**编写者**：Claude（Opus 5.5）
**总纲**：[P1-S4-R7-C开发方案-总纲.md](P1-S4-R7-C开发方案-总纲.md)

## 切片划分与验收

| 切片 | 功能点 | 验收条件 |
|---|---|---|
| **SL-007** 现金流量表 | 需求 TS-010／014、§4.10、AC-004 ⑤、DEC-096／117 | 1. `Cash Flow Code` 22 条，代码 1–22 与法定行次一一对应，`cash_flow_name` 与财政部原文逐字相同（zelin 原数据第 2、6、21 条与原文不同，已改正）<br>2. 数据集每月建一张现金流量底稿，点「取现金流明细」后：客户收款行预填代码 1、供应商付款行预填 3；两条腿都在 `1000` 组下的现金内部转账（提现）两行都标为内部转账、不要求代码<br>3. **期末现金余额**：每个月的底稿里，代码 22 的本月金额与本年累计金额**都**等于 `1001＋1002＋1012` 的月末余额；代码 21 的本月金额等于月初余额、本年累计金额等于年初余额（修正 zelin 把各月期末余额累加进「本年累计」的缺陷）<br>4. `小企业现金流量表` 月报列头 `项目｜行次｜本年累计金额｜本月金额`，年报第四列为 `上年金额`；22 行，行名与行次逐字符合原文；5 条勾稽全部成立<br>5. **异常路径**：① 有非内部转账行缺代码时提交 → 报错并列出行号；② 本年更早的某月有现金流水、却没有已提交的底稿，此时提交后一个月 → 报错并列出月份；③ 同一公司同一个月建第二张 → 报错；④ 已有更晚月份的底稿时取消本月底稿 → 报错；⑤ 拆分行合计与原总账分录不符 → 报错（沿用 zelin）；⑥ 所选月份没有已提交底稿时出表 → 报错「该月没有已提交的现金流量底稿」，不输出全零；⑦ 底稿提交后又有新的现金流水进该月 → 出表时说明行提示「底稿之后该月又有现金流水，请取消后重取明细」<br>6. **年报**：对 2026-04 至 2026-12 各建一张空底稿并提交（无流水的月份允许零行提交）→ 2026 年报「上年金额」等于 2025 年报的「本年累计金额」，逐行相同 |
| **SL-008** 三表打印与导出 | 需求 AC-004 ①②、DEC-095、§4.11 第 1–3 条 | 以下都在 `frappe.local.lang = "zh"` 下做：<br>1. **屏幕**：三张报表经 `frappe.desk.query_report.run` 返回的 `columns[].label` 与法定列头逐字相同<br>2. **XLSX**：经 `frappe.desk.query_report.export_query` 导出，用 `openpyxl` 读第一行，与法定列头逐字相同、列数相同（资产负债表 8 列，两个「行次」各占一列）；随后各行的行名与行次同屏幕（HT-007）<br>3. **PDF**：三张表经 `download_statement_pdf` 生成的 PDF，`pdftotext` 能取出法定标题（资产负债表／利润表／现金流量表）、表号（会小企 01 表／02 表／03 表）、`编制单位：华东弹簧…`（测试公司名）、全部列头与行名；`pdffonts` 显示 `NotoSansCJK` 已嵌入；`pdfinfo` 报资产负债表页面宽大于高（横向），利润表与现金流量表高大于宽<br>4. **LG-134 守卫**：`test_legal_labels.py` 通过；另往测试站 `Translation` 表临时写一条 `资产 → Assets`，守卫测试**失败**（证明它有判别力），测试结束删除该条<br>5. 三张报表的 Report 记录都是 `disable_prepared_report_automation = 1` 且 `prepared_report = 0`；让一张报表的 `execute` 人为睡眠 16 秒后执行完毕，`prepared_report` 仍为 0（LG-136） |
| **SL-009** 银行流水导入与对账 | 需求 TS-015、§4.12、AC-009、DEC-082／086 | 1. 一份 **GB18030 编码**的仿网银 csv：3 行抬头、1 行表头、6 行明细、1 行「合计」。经前置处理并导入后：`Bank Transaction` 新增 6 条，日期、金额与明细逐行相符，`description` 与对方户名中文逐字相同<br>2. 其中一行流水号与一张已提交的收款 `Payment Entry` 的 `reference_no` 相同 → `auto_reconcile_vouchers(bank_account, from_date, to_date)` 之后，该收款的 `clearance_date` 有值，对应 `Bank Transaction` 为 `Reconciled`（AC-009）<br>3. 同一文件再导入一次 → 新增 0 条，前置处理结果写明「6 行已存在，跳过」<br>4. 同一内容的 `.xlsx` 版本导入结果与 csv 版本相同<br>5. **异常路径**：① 明细区某行日期写成「2026-13-01」→ 前置处理报错并指出行号，不生成文件、不导入；② 金额写成「1,2x3.00」→ 同样报错；③ 文件里找不到格式所定义的表头 → 报错并列出期望的表头；④ 同一文件内两行流水号相同 → 报错；⑤ 某行存入、支取都为 0 → 报错<br>6. 导入前后，该银行 `Bank` 记录的 `bank_transaction_mapping` 均为空（不留陈旧映射，V-22 缺陷 ④） |
| **SL-010** 演示站落地 | 需求 TS-001／009／016、§4.13、AC-001／005／013／014、DEC-101／116 | 1. **清站前**：已当场取得用户对范围与动作的确认，确认原话记进 D 回执；`docker/backups/20260922_145623-*` 与 `保留-R6重装前/` 四个文件都存在、`gzip -t` 通过；另做一份清站前备份，复制到 `docker/backups/保留-S4清站前/`<br>2. 重装后演示站 System Settings：国家 China、语言 zh、时区 Asia/Shanghai、日期格式 yyyy-mm-dd、币种 CNY、舍入 `Commercial Rounding`；`list-apps` 为 `frappe`／`erpnext`／`frappe_china`；`default_site` 为 `erx.localhost`；desk 页全部静态资源返回 200（`docker/README.md` 的检查脚本）<br>3. `华东弹簧有限公司`（`HDTH`）建成，自检 `checked=True, ok=True`、`account_count = 266`；6 个 DEC-097 默认科目值与 TS-006 表相符（AC-005）<br>4. 站上 Company 只有这一家；Sales Invoice、Purchase Invoice、Journal Entry、Payment Entry、Month End Closing Voucher、Cash Flow、Bank Transaction 条数都为 0（AC-013）<br>5. app README 的「相对 zelin 的修改」逐条列出每个自 zelin 并入的文件及每一处修改的原因，与 TS-020 清单一一对应（AC-014）<br>6. **全量回归**：测试站上 `run-tests --app frappe_china` 全部通过；测试站 System Settings 未被测试改动 |

执行每个切片前，对照该切片验收条件检查方案覆盖性——如发现按方案写出的代码无法通过验收条件，暂停反馈，不硬写。

## 任务清单

| 任务 | 对应切片 | 可并行否 |
|---|---|---|
| TS-015 现金流四件套并入与修正 | SL-007 | 否 |
| TS-016 现金流量表 | SL-007 | 否 |
| TS-017 法定格式 PDF、导出核对与 LG-134 守卫 | SL-008 | 否 |
| TS-018 银行流水前置处理 | SL-009 | 可（乙组） |
| TS-019 导入与对账测试 | SL-009 | 可（乙组） |
| TS-020 README、并入登记与译名 csv | SL-010 | 否 |
| TS-021 演示站清站与建 `HDTH`（**须用户确认**） | SL-010 | 否 |
| TS-022 全量回归 | SL-010 | 否 |

---

## 任务 15：现金流四件套并入与修正（对应切片 SL-007）

### 目标
沿用 zelin 的直接法取数（DEC-107：原生引擎做不到凭证级遍历），修掉已知缺陷，补齐需求 §4.10.1 的约束。

### 具体改动

四个 DocType 自 zelin `erpnext_china/erpnext_china/doctype/` 复制到 `cn_tax/doctype/`，`module` 一律改为 `CN Tax`。并入时逐项修改如下（每项都登记进 TS-020 README）：

| 文件 | 修改 | 原因 |
|---|---|---|
| `cash_flow.json` | `month` 由字符串 Select 改为 Int（1–12，必填）；`autoname` 改为控制器生成 `XJ-{abbr}-{yyyymm}`；保留 `amended_from` | 需求 §4.10.1（比较隐患、公司全名拼的名字过长） |
| `cash_flow_item.json` | `read_only_depends_on` 的 `evel` 改为 `eval`（两处）；`against` 改为 Small Text，不再截断到 140 字；新增 `is_internal_transfer`（Check，只读） | G1b 清点；直接法要看完整的对方科目 |
| `cash_flow_subtotal.json` | `monthly_amount`／`yearly_amount` 由 Float 改为 Currency | G1b |
| `cash_flow.py` `get_cash_flow_items` | 过滤键 `"Company"` 改为 `"company"`；账户类型取 `Cash`／`Bank`；查询增加 `(finance_book IS NULL OR finance_book = '')`；取数后按下文标记内部转账 | G1b；与 `ledger.py` 口径一致 |
| `cash_flow.py` `sync_subtotal` | 按下文重写本年累计与期初、期末的算法；期初余额改用 `ledger.gl_sums` 计算，不再依赖 `trial_balance.get_rootwise_opening_balances` | 修 zelin 缺陷（验收第 3 条）；不依赖上游报表的内部函数 |
| `cash_flow.py` 新增 `validate` 分支 | 同公司同月唯一；提交时逐项检查 SL-007 验收第 5 条 ①② | 需求 §4.10.1「须每月按序提交」 |
| `cash_flow.py` 新增 `before_cancel` | 更晚月份已有有效底稿时拒绝取消 | 后面月份的本年累计依赖本月 |
| 测试 | `FrappeTestCase` 改为 `FrappeChinaTestCase` | G1b |
| `fixtures/cash_flow_code.json` | 第 2、6 条的 `cash_flow_name` 删去「的」，与原文「收到其他／支付其他与经营活动有关的现金」一致；第 21 条「加:」改为全角「加：」 | 原文逐字 |

`Account.allow_all_party_type` **不带入**（LG-148：全仓无读取方）。三个 `cash_flow_code` Custom Field 连同 `insert_after` 原样带入。

**内部转账的判定**：一条现金类总账分录，如果它所在凭证的全部分录都记在现金类科目上（即该凭证只在 `1000` 组内部转移资金），就标 `is_internal_transfer = 1`。这类行不计入任何现金流项目，也不要求填代码。同一凭证下的内部转账行，借贷合计必为 0，validate 时检查。

**本年累计与期初、期末**（替换 zelin `sync_subtotal` 的年度部分）：

```
cash = 公司全部 account_type ∈ {Cash, Bank} 的明细科目
open_month = Σ(借−贷) of gl_sums(company, to_date=月初−1天, accounts=cash)
open_year  = Σ(借−贷) of gl_sums(company, to_date=年初−1天, accounts=cash)
prior      = 本年内比本月早、已提交底稿的 cash_flow_subtotal，按代码汇总 monthly_amount
对每个代码：
  代码 1–19 的非公式行与分类小计行（7、13、19）：monthly 同 zelin；yearly = prior[code] + monthly
  代码 20（现金净增加额）：monthly = Σ 1–19 的净流量（流入正、流出负）；yearly 同理，按 yearly 汇总
  代码 21（期初现金余额）：monthly = open_month；yearly = open_year
  代码 22（期末现金余额）：monthly = 20.monthly + 21.monthly；yearly = 20.yearly + 21.yearly
                           另断言 monthly == yearly == 月末现金余额，不等则报错（说明流水取漏）
```

- 流出项在展示时取正数，`is_outflow` 语义同 zelin。

### 验证方式
`tests/test_cash_flow.py`：数据集每月建底稿，覆盖 SL-007 验收第 1–3 条与第 5 条 ①–⑤。

---

## 任务 16：现金流量表（对应切片 SL-007）

### 目标
法定格式的现金流量表，列头写死、逐字合规（DEC-096），支持月报与年报（DEC-117）。

### 具体改动

**Report `小企业现金流量表`**：Report 记录的字段、筛选（含 `period_type`）同 TS-013。

**`frappe_china/accounting/statements/cash_flow_statement.py`**

```python
CF_LINES: tuple[Line, ...]     # 22 个行定义 + 3 个分类标题（一、二、三无行次），行名为原文逐字；代码 = 行次
CF_CHECKS = ("7=1+2-3-4-5-6", "13=8+9+10-11-12", "19=14+15-16-17-18", "20=7+13+19", "22=20+21")

def execute(filters):
    f = _validate_filters(filters)
    doc = 本公司、本会计年度、报告月的已提交 Cash Flow；没有 → frappe.throw("该月没有已提交的现金流量底稿")
    ytd = {code: yearly_amount}；second = {code: monthly_amount}
    if Annual:
        doc 取 12 月底稿（没有 → 报错）
        prev = 上一个自然年 12 月的已提交底稿；没有 → second 全 0，说明「上年无数据」；有 → second = 其 yearly_amount
    notes = check(ytd, CF_CHECKS) + check(second, CF_CHECKS)
    if 该月有 creation 晚于底稿提交时间、posting_date 在该月的现金类 GL（is_cancelled 不限）: notes += ["底稿之后该月又有现金流水…"]
    return columns, data, message, None, None, True
```

- 期末现金余额与科目余额的核对已在底稿提交时做过（TS-015）。出表时对报告月末再核一次，不等时写进说明行。

### 验证方式
`tests/test_cash_flow_statement.py`，覆盖 SL-007 验收第 4、5 ⑥⑦、6 条。

---

## 任务 17：法定格式 PDF、导出核对与 LG-134 守卫（对应切片 SL-008）

### 目标
三张报表在屏幕、XLSX、PDF 三处的列头逐字合规，PDF 汉字可读（需求 §4.11 第 1 条、DEC-095）。

### 具体改动

**`frappe_china/accounting/statements/printing.py`**

```python
STATEMENTS = {  # 报表名 → (法定标题, 表号, 模板, 纸张方向)
  "小企业资产负债表": ("资产负债表", "会小企 01 表", "balance_sheet.html", "Landscape"),
  "小企业利润表":     ("利润表",     "会小企 02 表", "profit_and_loss.html", "Portrait"),
  "小企业现金流量表": ("现金流量表", "会小企 03 表", "cash_flow.html", "Portrait"),
}

def render_statement_html(report_name: str, filters: dict) -> str:
    columns, data, message, *_ = EXECUTORS[report_name](filters)
    # EXECUTORS：报表名 → balance_sheet.execute／profit_and_loss.execute／cash_flow_statement.execute，
    # 即屏幕所用的同一个函数，保证同源；用 frappe.render_template 渲染
    # 模板文件放 frappe_china/templates/statements/，以 "templates/statements/<名>.html" 引用；必须输出：标题、表号、
    #   资产负债表「编制单位：{公司}　{yyyy} 年 {m} 月 {d} 日　单位：元」，
    #   利润表／现金流量表「编制单位：{公司}　{yyyy} 年 {m} 月　单位：元」；
    #   列头与行名取自 columns／data，不在模板里另写一套；说明行（message）置于表下
    # CSS：font-family: "Noto Sans CJK SC", "Noto Sans CJK", sans-serif；金额右对齐、千分位

@frappe.whitelist()
def download_statement_pdf(report_name: str, filters: str | dict):
    frappe.has_permission("GL Entry", "read", throw=True)
    html = render_statement_html(report_name, frappe.parse_json(filters))
    frappe.local.response.filename = f"{法定标题}_{公司}_{期间}.pdf"
    frappe.local.response.filecontent = get_pdf(html, {"orientation": 方向, "page-size": "A4"})
    frappe.local.response.type = "pdf"
```

- 三张报表的 `.js` 各加一个按钮，label 用 `__("Print Statutory Format")`，点击后以当前筛选打开 `/api/method/frappe_china.accounting.statements.printing.download_statement_pdf?...`。
- **不改动**原生菜单的「打印」与「PDF」。它们走浏览器端 `print_grid`，列头经 `__()`，由 LG-134 守卫兜底。
- 模板里的固定文字（标题、表号、「编制单位」「单位：元」）一律收进 `labels.LEGAL_LABELS`。

**测试** `tests/test_statement_output.py`：
- 屏幕：`query_report.run` 返回的列头；
- XLSX：调 `export_query`，从 `frappe.response.filecontent` 用 `openpyxl` 读取；
- PDF：`download_statement_pdf` 生成的字节交给 `tests/utils.pdf_text_and_fonts` 解析。

**测试** `tests/test_legal_labels.py`：在 TS-011 的基础上补 SL-008 验收第 4 条的判别力测试。

**测试** `tests/test_prepared_report.py`：SL-008 验收第 5 条。16 秒那项标记为慢测试，默认也要跑。

### 验证方式
上述三个测试文件。另在测试站界面上以 `zh` 用户打开三张报表，各导出一次 XLSX、下载一次法定格式 PDF，目视核对后截图存 `Spike/`（界面层证据）。

---

## 任务 18：银行流水前置处理（对应切片 SL-009）

### 目标
把网银导出的流水（GBK／UTF-8 的 csv 或 xlsx，带抬头块与合计行）转成原生 `Bank Statement Import` 一定能正确导入的文件。本 app 不自研匹配逻辑（DEC-082）。

### 具体改动

**DocType `Bank Statement Format`**（模块 `CN Tax`，普通主数据）：

| 字段 | 类型 | 说明 |
|---|---|---|
| `format_name` | Data，唯一 | 如「仿网银对公明细」 |
| `encoding` | Select `Auto`／`GB18030`／`UTF-8` | Auto：依次试 `utf-8-sig`、`gb18030`，都失败则报错 |
| `date_header`、`reference_header`、`description_header`、`counterparty_header` | Data | 源文件表头文字，逐字匹配（去首尾空格）；前两项必填 |
| `deposit_header`、`withdrawal_header` | Data | 收入、支出分两列的版式用 |
| `amount_header` | Data | 单列带符号金额的版式用；与上一行二选一，validate 检查 |
| `date_formats` | Small Text | 每行一个 `strptime` 格式，默认 `%Y-%m-%d`、`%Y%m%d`、`%Y/%m/%d`、`%Y年%m月%d日` |
| `summary_keywords` | Small Text | 默认 `合计`、`总计`、`小计`、`本页`、`共` |

**不发 fixture**。测试用的「仿网银对公明细」格式由测试夹具创建。演示站上的格式要等 S7 按实际网银版式来建：本项目没有任何真实网银导出文件（LG-147），现在猜一个格式发出去，到时反而要删。这样做也让本任务不改 `hooks.py`，才能与左支并行（总纲 §八）。

**DocType `Bank Statement Preprocess`**（模块 `CN Tax`，非可提交）：
- 字段：`company`、`bank_account`（Link Bank Account，必填）、`statement_format`（Link，必填）、`source_file`（Attach，必填）；
- 只读字段：`status`（`Draft`／`Prepared`／`Imported`／`Failed`）、`output_file`、`bank_statement_import`（Link）、`row_count`、`skipped_count`、`log`（Long Text）；
- 表单按钮 label 用 `__("Preprocess and Import")`，调用 `run_preprocess_and_import`。

**`frappe_china/accounting/bank_import.py`**

```python
def preprocess_statement(name) -> dict:
    doc = frappe.get_doc("Bank Statement Preprocess", name); fmt = frappe.get_doc(... statement_format)
    rows = _read(doc.source_file, fmt.encoding)       # csv：按编码解码后 csv.reader；xlsx：openpyxl；xls：xlrd；统一成 list[list[str]]
    h = 第一个同时包含 date_header 与 reference_header 的行下标；找不到 → 报错并列出期望表头
    idx = {目标: 列下标}；表头缺失任一已配置的列 → 报错
    out, errors = [], []
    for i, r in enumerate(rows[h+1:], start=h+2):     # i 为源文件行号（从 1 起）
        if 全空: continue
        d = _parse_date(r[idx.date], fmt.date_formats)
        if d is None:
            if any(k in "".join(r) for k in fmt.summary_keywords): continue    # 合计行
            errors.append(f"第 {i} 行：日期「{r[idx.date]}」无法解析"); continue
        dep, wd = _amounts(r, idx)          # 去掉 ¥ ￥ 元 , 及空格；空、"-"、"--" 视为 0；其余非数字 → 记错
        if dep == 0 and wd == 0: errors.append(f"第 {i} 行：存入与支取都为 0")
        if dep < 0 or wd < 0: errors.append(...)   # 分两列的版式里出现负数：报错，不猜方向
        out.append(Row(d, dep, wd, desc, ref, party, i))
    if 文件内流水号重复（非空）: errors += 列出行号
    if errors: doc.status="Failed"; doc.log="\n".join(errors); doc.save(); frappe.throw(errors 前 20 条)
    existing = 该 bank_account 下 docstatus<2 的 Bank Transaction 的 reference_number 集合
    keep = [r for r in out if not r.ref or r.ref not in existing]；skipped = len(out) - len(keep)
    流水号为空的行照常导入，并在 log 里告警「无流水号的行不能自动核销、也不能防重复」
    写 UTF-8 csv（带 BOM）：表头依次为
      Date, Deposit, Withdrawal, Description, Reference Number, bank_party_name, Currency, Bank Account
      # 英文 label 与 fieldname 在任何语言下都能命中；Bank Account 不放第一列（V-22 缺陷：该列下标为 0 时补列出错）
      # Date 写 YYYY-MM-DD；金额写两位小数；Currency 取 bank_account 的科目币种；Bank Account 写 Bank Account 的 name
    output_file = save_file(..., "Bank Statement Preprocess", name, is_private=1)
    doc.update(status="Prepared", row_count=len(keep), skipped_count=skipped, log=...); doc.save()
    return {"rows": len(keep), "skipped": skipped, "file": output_file.file_url}

@frappe.whitelist()
def run_preprocess_and_import(name) -> dict:
    frappe.has_permission("Bank Statement Import", "create", throw=True)
    res = preprocess_statement(name)
    if res["rows"] == 0: return {**res, "message": "没有新流水需要导入"}
    bank = Bank Account 的 bank；把该 Bank 的 bank_transaction_mapping 清空并保存（V-22 缺陷 ④：陈旧的列序号键会优先于表头生效）
    bsi = new Bank Statement Import(company, bank_account, import_type="Insert New Records", submit_after_import=1).insert()
    挂上 output 文件（复制一份挂到 bsi 上，df="import_file"）→ bsi.save() → bsi.start_import()
    if 同步执行完（developer_mode 或测试中）:
        核对：本次新建的 Bank Transaction 数 == res.rows，不等 → status="Failed" 并写明差异；相等 → status="Imported"
    else: status 保持 "Prepared"，返回「已提交后台导入，完成后在 Bank Statement Import {name} 查看结果」
    再次清空该 Bank 的 bank_transaction_mapping（start_import 会按本次 template_options 重建）
    return {...}
```

- `Bank Statement Import` 的 `import_type` 取值在 D 步读 json 核实，本方案按 Insert 写。
- 提示文字用英文源词经 `_()`（总纲 A9）；上面伪代码里的中文只是示意。

### 验证方式
`tests/test_bank_preprocess.py`：覆盖 SL-009 验收第 5 条，以及 `_read` 的三种格式与两种编码。样本在测试里由 UTF-8 字符串常量 `encode("gb18030")` 生成，不在仓库里放二进制样本。

---

## 任务 19：导入与对账测试（对应切片 SL-009）

### 目标
用原生工具走完「导入 → 自动核销」，给 AC-009 提供正向证据。

### 具体改动
`tests/test_bank_reconcile.py`：
- 测试夹具：`Bank` `_FCT 测试银行`；`Bank Account` 挂本公司 `1002`，`is_company_account = 1`；一张收款 `Payment Entry`（`reference_no = "FCT20260105001"`，`reference_date`，`paid_to = 1002`）；
- 样本 6 行明细，其中一行流水号为 `FCT20260105001`、金额相同；**明细不超过 10 行**：`auto_reconcile_vouchers` 超过 10 笔会转入后台 long 队列（`bank_reconciliation_tool.py:974-986`）；
- 调 `run_preprocess_and_import` → 断言 SL-009 验收第 1、6 条 → 调 `auto_reconcile_vouchers(bank_account, from_date=..., to_date=...)`（显式传日期，不依赖 None 的行为）→ 断言第 2 条 → 再导入一次断言第 3 条 → xlsx 版本断言第 4 条。
- 生产环境下的两处后台依赖写进 README「银行对账」节：非 developer_mode 时导入走后台队列；一次对账超过 10 笔也走后台。两者都要求 `bench start` 在运行（worker 在 Procfile 里）。

### 验证方式
上述测试文件；另在测试站界面上走一次「银行流水预处理 → 对账工具 → 自动对账」，截图存 `Spike/`。

---

## 任务 20：README、并入登记与译名 csv（对应切片 SL-010）

### 目标
AC-014 的可追溯性；本 app 新增界面词条的中文（总纲 A9）。

### 具体改动
- **`README.md`**（中文），各节：
  - 定位与装载位置（ADR-0013）；
  - 模块判据与同名侧栏的用途（ADR-0012「二」，并写明删掉它会多出一条侧栏）；
  - 开发与测试（测试站、`run-tests` 命令、不 import `erpnext.tests.utils` 的原因）；
  - 「相对 zelin 的修改」：逐文件列出来源路径、处置（原样／抄后改／重写／不带入）、每处修改与原因。至少覆盖：科目表 JSON 原样；税模板两处笔误与「含税」位置；默认科目 csv 改为按科目号的 json，删 5 个 v16 不存在的字段，补 DEC-097 六项；物料组 `Product` 科目；胶水层重写要点（`create_charts`、flag 复位、不吞异常、`log_error` 用法、`__file__` 定位、`get_chart` 末尾多余的 return）；现金流四件套 TS-015 表；不带入清单（需求 §4.2）；
  - 已知限制：超过 1 年的预付／预收未做账龄拆分；生产设备折旧入管理费用（LG-142）；所得税未计提（LG-143）；小规模纳税人未处理（LG-150）；各类单据各自编号（LG-152）；
  - 银行对账的后台依赖（TS-019）；
  - 许可：MIT。zelin 原文件头的 GPL 声明按 DEC-102 视为标错，不保留。
- **`frappe_china/translations/zh.csv`**：本 app 新增的 DocType 名、字段 label、Select 选项、按钮与提示的英文源词 → 中文。
  - 例：`Month End Closing Voucher,结转凭证`；`Cash Flow,现金流量底稿`；`Cash Flow Code,现金流量项目`；`Bank Statement Preprocess,银行流水预处理`；`Bank Statement Format,银行流水格式`；四个结转类别；`Print Statutory Format,打印法定格式`。
  - **键不得与 frappe／erpnext 官方词典已有的键重复**；**译文不得与 `LEGAL_LABELS` 里的任何一项相同后又被用作其他键**（LG-134）。
  - `tests/test_translations.py` 断言以上两条：用 `frappe.translate.get_all_translations("zh")` 取官方词条做比对。

### 验证方式
`test_translations.py`；README 与 TS-015 表、需求 §4.2 逐条对照（D 回执附对照表）。

---

## 任务 21：演示站清站与建 `HDTH`（对应切片 SL-010）

### 目标
演示站 `erx.localhost` 上只剩 `华东弹簧有限公司`，科目、税、默认科目全部就绪，供 S7 造数据（需求 §4.13、DEC-101）。

### 具体改动

1. **停下来，向用户确认**（DEC-101）。确认内容当场给全：
   - 要删的：`华东弹簧`（HDS）及其 GL 22 条、SLE 12 条、各类单据与主数据；
   - 保留的：两份 S1 备份，另做一份新备份；
   - 手段：重装站点。

   未获明确确认即停，任务标为未完成。
2. **核备份**：`ls -la` 与 `gzip -t` 检查 `docker/backups/20260922_145623-*` 与 `docker/backups/保留-R6重装前/*`。跑 `docker/backup.sh`，把新生成的一套复制到 `docker/backups/保留-S4清站前/`。
   - 更正一处文档：`backup.sh` 实际每次**新增**一套带时间戳的文件、不覆盖旧文件（`backup.sh:22-35`），`docker/README.md:68` 与需求 §4.13 写的「每类只留最新一份」不成立。真正的风险在 `restore.sh`：它按修改时间取最新的一套（`restore.sh:16-22`），新备份会成为默认恢复对象。README 该句按此改写。
3. **重装**：照 `docker/README.md`「重装站点」节执行：
   - `reinstall --yes --admin-password … --db-root-password …`；
   - `install-app erpnext`；
   - `seed-demo.sh --bare`；
   - `set-locale.sh`。

   然后补设 System Settings（`date_format`、`rounding_method = Commercial Rounding`、币种 CNY）；建会计年度 `2026`；`install-app frappe_china`；按 README 做重装后核验，并跑 desk 静态资源检查脚本。
   - **再跑一次 `erpnext…financial_report_template.sync_financial_report_templates()`（不传参数）**。原生只在建「第一家走原生建账的公司」时才同步 6 条出厂报表模板与 Account Category（`company.py:348`）；清站后第一家公司就是 `HDTH`，走的是本 app 的路径，站上会一条都没有。本步只是一次性的站点动作，不写进 app 代码，DEC-104（Company 钩子不补调）不变。不传参数时不会调用 `get_chart`，也就不会因中文表名报错（`financial_report_template.py:141-144`）。完成后核对 `Financial Report Template` 为 6 条。
4. **建公司**：`华东弹簧有限公司`，缩写 `HDTH`，国家 China，币种 CNY，科目表 `小企业会计准则(2024)`，`enable_perpetual_inventory = 1`，`cn_urban_construction_tax_rate = 7`（LG-144 待客户确认）。然后设为默认公司（`DEFAULT_COMPANY="华东弹簧有限公司" docker/set-locale.sh`）。
5. **核验**：
   - `check_company_chart("华东弹簧有限公司")`；
   - 读 6 个默认科目；
   - 各类单据条数；
   - 以上结果全部写进 D 回执。
6. **改写 `docs/项目概况.md`「开发环境」节**：公司、闭环样本的去处、备份基准点（需求 §5.2）。写前载入 `docs/流程体系/常驻文件契约.md`。

### 验证方式
SL-010 验收第 1–4 条，逐条在 D 回执里给出命令与输出。

---

## 任务 22：全量回归（对应切片 SL-010）

### 目标
确认全部切片的验收在最终代码上同时成立，演示站状态正确。

### 具体改动
1. 测试站：`bench --site test.localhost migrate`，然后 `run-tests --app frappe_china`，全部通过。跑前记录测试站 System Settings，跑后比对。
2. 演示站：只读复核 SL-010 验收第 2–4 条；`list-apps`；desk 静态资源检查。
3. D 回执汇总：每个切片的每条验收条件对应哪个测试、结果如何、证据在哪。
4. 清理：删除 `frappe-bench/tmp_s4c/` 等临时文件；测试站保留，供 E、F 步复用。

### 验证方式
即本任务本身；E 步以本方案为清单逐项复核。
