# P1-S4 开发方案·Part2：月末结转（自有结转凭证）

**来源需求**：[B 需求文档](../R06-需求文档/P1-S4-R6-B需求文档.md) §4.7、BR-004／BR-005，[C 讨论记录](P1-S4-R7-C讨论记录.md) DEC-118／119｜**前置依赖**：Part1 全部（TS-008）｜**日期**：2026-09-29｜**编写者**：Claude（Opus 5.5）
**总纲**：[P1-S4-R7-C开发方案-总纲.md](P1-S4-R7-C开发方案-总纲.md)

> **本 Part 相对需求的偏离**（总纲 §五 第 1、5 条）：结转生成的是自有单据 `Month End Closing Voucher`（界面译名「结转凭证」），不是 Journal Entry；附加税计税依据改为一般式。「每月按序三张、12 月加一张、逆序取消、不重复、可机械识别」原样保留。

## 切片划分与验收

| 切片 | 功能点 | 验收条件 |
|---|---|---|
| **SL-005** 月末结转 | 需求 TS-011、§4.7、AC-007／008、DEC-099／118 | 以下全部在测试站的一家本表测试公司上做，造数用正常单据提交（销售发票、采购发票、Journal Entry），不直接写 GL。<br>1. **正常月**（销项 > 进项）：生成后恰好 3 张结转凭证，按「增值税结转 → 附加税计提 → 损益结转」顺序，编号 `JZ-{abbr}-{yyyymm}-001…003`；此后 `2221000` 组余额为 0；`2221020` 本月贷方增加额 ＝ 销项税额 − 进项税额；`5403` 借方 ＝ 应纳税额分别 × 7%、3%、2%，**每项各自四舍五入到分后相加**；全部 Income／Expense 明细科目在月末的余额为 0（按科目＋成本中心逐一为 0）；`3103` 贷方增加额 ＝ 本月利润（取数时排除结转分录）；每条结转分录的 `voucher_subtype` 等于该凭证的结转类别<br>2. **重复生成**：同一公司同一月份再调一次 → 报错「本月已结转，请先取消」，结转凭证条数不变<br>3. **逆序取消与重做**：在界面或代码里直接取消「增值税结转」而「附加税计提」仍有效 → 报错；`cancel_month_end_closing` 按 损益 → 附加税 → 增值税 的顺序取消全部，之后该月除结转外的 GL 余额与结转前逐科目相同；随后重新生成成功，编号接着排（`-004…006`）<br>4. **留抵月**（进项 > 销项）：只生成「损益结转」1 张，不生成增值税结转与附加税计提；`2221000` 组借方余额 ＝ 进项 − 销项、原样留存。**下月**销项超过进项＋上月留抵时，增值税结转额 ＝ 本月销项 − 本月进项 − 上月留抵<br>5. **多交月**：本月以 Journal Entry 借 `2221002 已交税金` 贷 `1002`，金额大于本月应纳 → 增值税结转凭证为 借 `2221020` 贷 `2221009`，金额 ＝ 已交 − 应纳；附加税计税依据 ＝ 应纳（不是已交）<br>6. **草稿提醒**：该月有一张草稿销售发票时，第一次调用返回 `created=[]` 与草稿清单，不建任何凭证；带 `ignore_drafts=1` 再调才生成<br>7. **上月未结**：上月有损益发生额但未结转，生成本月 → 报错并列出未结月份；本年第一个有业务的月份不受此限<br>8. **结转不完整**：结转后再提交一张该月的销售发票 → `month_closing_state(...)` 返回 `complete=False`，`issues` 里有「结转后该月又有凭证变动」；取消该月结转并重新生成后 `complete=True`<br>9. **冻结期**：公司 `accounts_frozen_till_date` 不早于该月月末时生成 → 报错，且**一张结转凭证也不留**（原子性）<br>10. **年末**：12 月生成 4 张，第 4 张为「本年利润结转」；此后 `3103` 年末余额为 0，`3104090` 贷方增加额 ＝ 全年各月损益结转转入 `3103` 的合计（AC-008 前半）<br>11. **折旧科目**：当月有一张借 `5602070` 贷 `1602020` 的折旧凭证（Journal Entry，类型「折旧凭证」），损益结转照常提交（DEC-118 的起因）<br>12. **异常输入**：绕过生成函数直接 `insert()` 一张结转凭证 → 报错；经生成函数的内部入口建一张 3 月的「本年利润结转」→ 报错；只有 `Accounts User` 角色的用户调生成 → `frappe.PermissionError`；会计年度不是自然年 → 报错（校验函数单测）<br>13. **城建税档位**：把公司的城建税税率改为 5 后生成 → `2221040` 贷方 ＝ 应纳 × 5%；未设（空值）时按 7% 计并在返回的 `message` 里提示「按市区 7% 计」 |

执行每个切片前，对照该切片验收条件检查方案覆盖性——如发现按方案写出的代码无法通过验收条件，暂停反馈，不硬写。

## 任务清单

| 任务 | 对应切片 | 可并行否 |
|---|---|---|
| TS-009 结转凭证单据与过账 | SL-005 | 否 |
| TS-010 结转的计算、生成、取消与状态 | SL-005 | 否 |

---

## 任务 9：结转凭证单据与过账（对应切片 SL-005）

### 目标
一种可提交、提交即过账、取消即冲销的自有凭证，不受 Journal Entry 的折旧类型校验与 100 行排队限制（DEC-118，HT-004）。

### 具体改动

**DocType `Month End Closing Voucher`**（模块 `CN Tax`，`is_submittable: 1`，`track_changes: 1`，不设 `amended_from`，即不允许修订；命名由控制器 `autoname`）

| 字段 | 类型 | 说明 |
|---|---|---|
| `company` | Link Company，必填 | |
| `fiscal_year` | Link Fiscal Year，必填 | |
| `month` | Int，必填 | 1–12。**用整数**，不学 zelin 用字符串 Select（需求 §4.10.1 提到的比较隐患） |
| `closing_type` | Select，必填 | `VAT Transfer`／`Surtax Accrual`／`P&L Transfer`／`Year-end Profit Transfer`（界面经 csv 译为 增值税结转／附加税计提／损益结转／本年利润结转） |
| `posting_date` | Date，只读 | 该月最后一天，由 validate 写入 |
| `remark` | Small Text | 生成时写明计算依据，如「应纳增值税 1,300.00 ＝ 已交 0.00 ＋ 转出未交 1,300.00 − 转出多交 0.00」 |
| `accounts` | Table → `Month End Closing Voucher Account` | |
| `total_debit`／`total_credit` | Currency，只读 | |

**子表 `Month End Closing Voucher Account`**（`istable: 1`）：`account`（Link Account，必填）、`cost_center`（Link Cost Center）、`debit`（Currency）、`credit`（Currency）、`remark`（Data）。

**权限**：`Accounts Manager` 与 `System Manager` 可读、建、提交、取消；`Accounts User` 只读。

**Custom Field** `Company-cn_urban_construction_tax_rate`：
- 类型 Select，`options = "\n7\n5\n1"`，label `Urban Maintenance and Construction Tax Rate (%)`；
- `insert_after = "tax_id"`；`depends_on = eval:doc.chart_of_accounts=="小企业会计准则(2024)"`；
- 以 fixture 发布，已列入总纲 §六 的 `fixtures` 名单。

**控制器** `month_end_closing_voucher.py`

```python
class MonthEndClosingVoucher(AccountsController):
    def autoname(self):
        abbr = frappe.get_cached_value("Company", self.company, "abbr")
        self.name = make_autoname(f"JZ-{abbr}-{self._year()}{self.month:02d}-.###", doc=self)   # HT-012

    def validate(self):                    # 不调 super().validate()：同 Period Closing Voucher
        if self.is_new() and not self.flags.frappe_china_generated:
            frappe.throw(_("Month End Closing Vouchers can only be created by Generate Month End Closing"))
        fy = frappe.get_cached_value("Fiscal Year", self.fiscal_year, ["year_start_date", "year_end_date"], as_dict=True)
        assert_calendar_fiscal_year(fy)                          # 1 月 1 日至 12 月 31 日，否则报错
        if not 1 <= cint(self.month) <= 12: frappe.throw(...)
        if self.closing_type == "Year-end Profit Transfer" and self.month != 12: frappe.throw(...)
        self.posting_date = get_last_day(date(fy.year_start_date.year, self.month, 1))
        for row in self.accounts: self._validate_row(row)        # 属本公司、非组、未停用；损益科目须带成本中心
                                                                 # 且成本中心属本公司、非组；借贷恰有一方 > 0；flt(,2)
        self.total_debit  = flt(sum(r.debit for r in self.accounts), 2)
        self.total_credit = flt(sum(r.credit for r in self.accounts), 2)
        if not self.accounts or self.total_debit != self.total_credit or self.total_debit <= 0: frappe.throw(...)

    def before_submit(self):
        if frappe.db.exists(self.doctype, {"company": self.company, "fiscal_year": self.fiscal_year,
                            "month": self.month, "closing_type": self.closing_type,
                            "docstatus": 1, "name": ("!=", self.name)}):
            frappe.throw(...)                                    # 不重复（需求 §4.7.3 第 1 条）

    def on_submit(self):
        make_gl_entries(self.get_gl_entries(), merge_entries=False)

    def before_cancel(self):
        # 同月里排在本张之后的结转凭证仍有效 → 拒绝；任何更晚月份仍有有效结转凭证 → 拒绝
        ...

    def on_cancel(self):
        self.ignore_linked_doctypes = ("GL Entry", "Payment Ledger Entry")
        make_reverse_gl_entries(voucher_type=self.doctype, voucher_no=self.name)

    def get_gl_entries(self):
        return [self.get_gl_dict({"account": r.account, "cost_center": r.cost_center,
                                  "debit": r.debit, "credit": r.credit,
                                  "debit_in_account_currency": r.debit, "credit_in_account_currency": r.credit,
                                  "remarks": r.remark or self.remark}, item=r)
                for r in self.accounts]

    def get_voucher_subtype(self):         # 写进每条 GL Entry 的 voucher_subtype（HT-004）
        return self.closing_type
```

- 同月内的先后顺序由常量 `CLOSING_TYPES` 的下标定（总纲 §六）。
- 冻结期、会计期间关闭、科目停用等校验不自己写：`make_gl_entries` 过账时自带（`general_ledger.py:48-49`、`:802-852`），取消时 `make_reverse_gl_entries` 也会查。
- **列表页按钮** `month_end_closing_voucher_list.js`：`onload` 时加两个按钮。「生成月末结转」弹出对话框（公司、会计年度、月份），调 `generate_month_end_closing`：返回里有草稿清单时，弹出确认框列出草稿，用户确认后以 `ignore_drafts=1` 再调；成功后列出新建的凭证。「取消月末结转」同一对话框，调 `cancel_month_end_closing`。提示文字用英文源词经 `__()`（总纲 A9）。

### 验证方式
`tests/test_closing_voucher.py`：
- HT-004：用生成函数的内部入口造一张两行凭证并提交，断言 GL 条数为 2、借贷相符、`voucher_subtype` 正确；取消后原分录 `is_cancelled=1`，另有红冲分录。
- HT-012：同一公司两个月、两家公司同一个月，各建两张，断言编号。
- 覆盖 SL-005 验收第 12 条的前三项。

---

## 任务 10：结转的计算、生成、取消与状态（对应切片 SL-005）

### 目标
一次操作为指定公司、指定月份按序生成结转凭证（需求 §4.7），并给报表提供「本月结转状态」（需求 §4.7.3 第 4 条）。

### 具体改动

**`frappe_china/accounting/ledger.py`**——总账取数的唯一入口。本任务先建，Part3 的报表复用，签名不改。

```python
def gl_sums(company: str, *, to_date: date, from_date: date | None = None,
            accounts: Iterable[str] | None = None, root_types: Iterable[str] | None = None,
            by_cost_center: bool = False, by_party: bool = False, exclude_pl_closing: bool = False,
            fy_opening_of: str | None = None) -> dict:
    """返回 {account: (debit, credit)}；by_cost_center 时键为 (account, cost_center)，
    by_party 时键为 (account, party_type, party)（两者不同时用）。未出现的科目不在结果里。
    共同条件：gle.company = company AND is_cancelled = 0 AND (finance_book IS NULL OR finance_book = '')
    余额口径（from_date 为空）：posting_date <= to_date
        另给 fy_opening_of 时（「年初余额」用）：posting_date < 该年起始日 OR (is_opening = 'Yes' AND fiscal_year = 该年)
    发生额口径（给 from_date）：from_date <= posting_date <= to_date AND is_opening = 'No'
    exclude_pl_closing：排除 voucher_type = 'Period Closing Voucher'，
                        以及 voucher_type = 'Month End Closing Voucher' AND voucher_subtype IN PL_EXCLUDED_SUBTYPES
    accounts 与 root_types 同时给出时取交集；都不给则全部科目。"""

def leaf_accounts_under(company: str, account_number: str) -> list[str]:
    """该科目号本身（若为明细）或其全部下级明细科目的 Account.name。科目号不存在 → 抛错（不返回空列表）。"""
```

- `finance_book` 与原生报表的默认条件一致（`financial_statements.py:628-632`）。
- 余额口径下 `is_opening` 不设限：期初凭证本来就是余额的一部分。

**`frappe_china/accounting/closing.py`**（签名见总纲 §六）

```python
DRAFT_CHECK_DOCTYPES = ("Sales Invoice", "Purchase Invoice", "Journal Entry", "Payment Entry",
                        "Purchase Receipt", "Delivery Note", "Stock Entry", "Stock Reconciliation")
SURTAX = (("2221040", None), ("2221110", 3), ("2221150", 2))   # None = 取公司城建税档位，空值按 7

@frappe.whitelist()
def generate_month_end_closing(company, fiscal_year, month, ignore_drafts=False):
    frappe.has_permission("Month End Closing Voucher", "create", throw=True)
    month = cint(month); fy = _calendar_fy(fiscal_year)          # 非自然年 → 抛错
    _assert_cn_company(company)
    start, end = 月初, 月末
    if _submitted_vouchers(company, fiscal_year, month):
        frappe.throw(_("Month End Closing for {0} is already done. Cancel it first.").format(...))
    if unclosed := _unclosed_previous_months(company, fiscal_year, month):
        frappe.throw(...列出月份...)           # 本年内更早的月份有损益发生额、却无有效的损益结转凭证
    if (drafts := _drafts(company, start, end)) and not cint(ignore_drafts):
        return {"created": [], "drafts": drafts, "message": _("There are draft documents in this month")}
    frappe.db.savepoint("frappe_china_closing")
    try:
        created, notes = [], []
        vat = _vat_transfer_rows(company, fiscal_year, start, end)            # ①
        if vat.rows: created.append(_make(company, fiscal_year, month, "VAT Transfer", vat.rows, vat.remark))
        base = max(0, flt(vat.paid + vat.transferred_unpaid - vat.transferred_overpaid, 2))   # 本月应纳增值税
        if base > 0:                                                          # ②
            rows, remark, note = _surtax_rows(company, base)
            created.append(_make(..., "Surtax Accrual", rows, remark)); notes += note
        if rows := _pl_transfer_rows(company, fy.year_start_date, end):      # ③：必须在 ② 提交之后取数
            created.append(_make(..., "P&L Transfer", rows, ...))
        if month == 12 and (rows := _year_end_rows(company, end)):          # ④
            created.append(_make(..., "Year-end Profit Transfer", rows, ...))
    except Exception:
        frappe.db.rollback(save_point="frappe_china_closing"); raise
    message = "；".join(notes) if created else _("Nothing to transfer for this month")
    return {"created": created, "drafts": [], "message": message}
```

- `_make(...)`：`new_doc` → 填字段与明细 → `doc.flags.frappe_china_generated = True` → `insert()` → `submit()` → 返回凭证名。**不加 `ignore_permissions`**：权限由 DocType 自身把守（验收第 12 条）。

**① 增值税结转** `_vat_transfer_rows`（依财会〔2016〕22 号二（六），BR-004）：

```
G   = leaf_accounts_under(company, "2221000")               # 2221001…2221010
B   = Σ(借−贷) over gl_sums(company, to_date=end, accounts=G)          # 截至月末的组余额，含以前各月留抵
paid = Σ(借−贷) over gl_sums(company, from_date=start, to_date=end, accounts=[2221002])  # 本月已交税金
if B < 0:  unpaid = −B；rows = [借 2221003 unpaid, 贷 2221020 unpaid]           # 当月应交未交
elif B > 0 and paid > 0: over = min(B, paid)；rows = [借 2221020 over, 贷 2221009 over]  # 多交（取二者较小）
else: rows = []                                                                 # 留抵，不结转
remark = "应交增值税组余额 {B}；本月已交 {paid}；…"
```

- 本表的 `2221020`／`2221009`／`2221003` 都是明细科目，用 `leaf_accounts_under` 按号取出唯一的一个。取到的不是恰好一个时抛错。

**② 附加税计提** `_surtax_rows`（BR-005）：

```
urban = cint(Company.cn_urban_construction_tax_rate) or 7；未设时 note = "城建税按市区 7% 计"
各项 amt_i = flt(base × rate_i / 100, 2)                   # 各自舍入（Commercial Rounding，DEC-116）
rows = [借 5403 Σamt_i（成本中心 = Company.cost_center）, 贷 2221040 amt_城建, 贷 2221110 amt_教育, 贷 2221150 amt_地方教育]
       金额为 0 的贷方行不写
```

- 公司没有默认成本中心时抛错。

**③ 损益结转** `_pl_transfer_rows`：

```
S = gl_sums(company, from_date=年初, to_date=end, root_types=("Income", "Expense"), by_cost_center=True)
    # 本年发生额：以前各月已结转，故这里只剩本月净额（上月未结已在前面拦掉）
rows = 对每个 (科目, 成本中心) 的净额 b = 借−贷 ≠ 0：b > 0 记贷方 b，b < 0 记借方 −b
total = Σb
if total < 0: rows += [贷 3103 −total]         # 盈利
if total > 0: rows += [借 3103 total]          # 亏损
```

- 按科目＋成本中心逐一结平（验收第 1 条「逐一为 0」）。
- 成本类（`4001`／`4101` 等，`root_type = Asset`）自然不在内。

**④ 本年利润结转** `_year_end_rows`：

```
b = Σ(借−贷) over gl_sums(company, to_date=end, accounts=[3103])
b < 0: [借 3103 −b, 贷 3104090 −b]；b > 0: [借 3104090 b, 贷 3103 b]；b = 0: []
```

**取消** `cancel_month_end_closing(company, fiscal_year, month)`：
- 先查权限 `cancel`；
- 若有更晚月份（本年或以后年度）的有效结转凭证，抛错并列出；
- 本月有效凭证按 `CLOSING_TYPES` 下标**逆序**逐张 `cancel()`，放在同一个 savepoint 里，失败整体回滚；
- 返回被取消的凭证名。

**状态** `month_closing_state(company, fiscal_year, month)`：

```
vouchers = 本月有效结转凭证（按类别顺序）
closed   = 其中有 "P&L Transfer"；或本月根本没有损益发生额（此时 vouchers 可为空）
issues = [] if closed else ["{yyyy} 年 {m} 月尚未结转"]
if closed and vouchers:
    t = 本月结转凭证 GL 的最大 creation
    若存在 posting_date 在本月、voucher_type ≠ 'Month End Closing Voucher'、creation > t 的 GL Entry（is_cancelled 不限）
        → issues += ["结转后该月又有凭证变动（新增或取消），请取消本月结转后重新生成"]
    若本月末损益科目的本年余额（gl_sums，按科目）有非 0 → issues += ["损益科目月末余额不为 0"]
if month == 12 and closed and 无 "Year-end Profit Transfer" 且 3103 年末余额 ≠ 0 → issues += ["尚未做本年利润结转"]
complete = closed and not issues
```

- 「取消」产生的红冲分录也是新 GL，creation 更晚，所以同一条规则能同时抓到「新增」与「取消」。

### 验证方式
`tests/test_closing.py`，逐条对应 SL-005 验收第 1–11 条与第 13 条：

| 项 | 做法 |
|---|---|
| 造数 | 用测试公司，单据全部正常提交 |
| 金额 | 一律按科目号查 GL 断言，取数**不经** `gl_sums`，避免拿被测函数验证自己 |
| 冻结期（第 9 条） | 测试里设 `accounts_frozen_till_date`，并把测试用户的角色限定为不含 `role_allowed_for_frozen_entries` 的角色 |
| 权限（第 12 条第三项） | 建一个只有 `Accounts User` 角色的测试用户，`frappe.set_user` 切过去调用 |