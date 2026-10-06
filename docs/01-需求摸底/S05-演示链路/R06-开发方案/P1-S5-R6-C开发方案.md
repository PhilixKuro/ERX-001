# P1-S5-R6 开发方案：删公司清理与报销映射保存前预配（R5 E 确认 IT-002、IT-003）

**来源**：[R5 E确认报告](../R05-确认报告/P1-S5-R5-E确认报告.md) IT-002、IT-003（档位 `出方案修`）｜**改的是**：[R3 开发方案](../R03-开发方案/P1-S5-R3-C开发方案-总纲.md) Part1 TS-005 与 SL-002、Part2 TS-006 第 8 步｜**裁决**：[C讨论记录](P1-S5-R6-C讨论记录.md) DEC-023～028｜**日期**：2026-10-06｜**编写者**：Claude（Opus 5.5）

> R3 方案是只读依据，本方案不改写它。凡与 R3 不一致之处**以本方案为准**，替换关系见 §二。总量小，不拆 Part。R3 总纲 §九的执行纪律（站点安全、测试纪律、密钥、版本管理、不静默）**全部照旧适用**，本方案只在 §九 补三条。

## 一、概述

**要解决的两个问题**（事实依据见 C 讨论记录第 1 步②，F1～F11 均为测试站探针实跑、事务回滚）

| 编号 | 问题 | 实测后果 |
|---|---|---|
| IT-002 | `frappe_china` 与 HRMS 都不在删公司时清 `Expense Claim Account`；中式公司另有 13 条 `Tax Rule` | **不带 `force` 删不掉任何一家公司**（中式被 `Tax Rule` 与报销行拦，`Standard` 被报销行拦，F1、F3）；带 `force` 删则留悬空行，此后**全站建不出任何公司**（HRMS 自己整单保存报销类型也报 `LinkValidationError`，F2、F3）。E 报告写的「删一次中式公司后建不出中式公司」只是其中一面 |
| IT-003 | `company.py` `on_update` 非建账分支：HRMS 建出通用科目即删该公司**全部**报销行与该科目，不补回；按 `_("Expense Claims")` 判科目 | 中式公司新增一个报销类型后保存，6 行全被删、每次保存重演（F6）；复制建账的新公司 0 行（F7）；按界面语言判科目，跨语言会漏（F8） |

**改法**（DEC-023～028）：删公司时由 `frappe_china` 清该公司的报销行（所有公司）与 `Tax Rule`（中式公司）；保存中式公司前先补齐报销行，让 HRMS 的建科目钩子没有空缺可补；复制建账时 HRMS 先于本 app 跑、来不及预配，事后把指向无号科目的报销行改挂到映射科目、再删掉那个通用科目；不在映射里的报销类型挂 `5602250`。

**完成标准**：SL-011、SL-012 验收条件全部通过；全量回归不少于 R5 的 180 条且全部通过，回执分报收集、通过、跳过条数。

## 二、与 R3 方案的替换关系

| R3 位置 | 原内容 | 本方案 |
|---|---|---|
| Part1 TS-005 `set_cn_expense_claim_accounts` 伪代码 | 只遍历映射里的 5 个类型；站上没有的类型告警跳过 | **遍历站上全部 `Expense Claim Type`**：按名称或其译名命中映射，未命中挂兜底科目号 `5602250`（DEC-028）；映射里有、站上没有的类型照旧告警 |
| Part1 TS-005 入口 | 入口 1 建账末尾、入口 2 `after_app_install` | 两入口不变；**另加入口 3：Company `validate`**（已有中式公司保存前补齐，DEC-026） |
| Part1 SL-002 ①～⑧ | 原文 | 原文保留（④⑥⑧ 不受影响；①③ 在 5 个标准类型下结果不变）；另加 SL-011、SL-012 |
| D 步实现里方案外的 `_remove_hrms_expense_claim_account`（`company.py:58-60、81-94`） | 每次保存删全部报销行与通用科目 | **删除**，由 TS-019 的 `repoint_generic_expense_claim_accounts` 取代（DEC-027） |
| Part2 TS-006 第 8 步「删 `_FCT 入口二`……HRMS 的 `on_trash` 会顺带删其关联记录」 | 假设不成立（HRMS 的 `company_data_to_be_ignored` 不含这张子表） | 删公司由本方案的 `on_trash` 清理兜住；**今后任何步骤删测试公司都不带 `force`**（§九第 2 条） |

## 三、接口契约

只列变动的部分，其余同 R3 Part1 接口契约。

```python
# ---- frappe_china/accounting/company.py ----
def is_cn_company(doc_or_name) -> bool:
    """本公司是否用本表建账：chart_of_accounts 是本表；为空时沿 existing_company 链向上找（复制的复制），
    链上出现环或超过 10 层即判否。替代 on_update / before_insert 里的 is_cn_chart(_company_chart(doc))。"""

def validate(doc, method=None) -> None:           # hooks: Company.validate（新增）
    """已有中式公司保存前：set_cn_expense_claim_accounts(doc.name)。新公司（doc.is_new()）不动作——
    此时科目还没建，标准建账由入口 1 配、复制建账由 on_update 的改挂兜住。"""

def on_update(doc, method=None) -> None:          # 已有，改非建账分支
    """非建账分支：is_cn_company(doc) 时调 repoint_generic_expense_claim_accounts(doc.name)，
    不再调 _remove_hrms_expense_claim_account（删除）。建账分支不变。"""

def on_trash(doc, method=None) -> None:           # hooks: Company.on_trash（新增）
    """clear_company_expense_claim_accounts(doc.name)（所有公司）；is_cn_company(doc) 时另删该公司的 Tax Rule。
    只删 company == doc.name 的行。框架先跑 on_trash 再查链接（HT-018），故删除随后不再被这两类拦下；
    删除最终失败（如有交易）时随事务回滚。"""

# ---- frappe_china/accounting/hr.py ----
FALLBACK_KEY: Final = "expense_claim_type_fallback"     # company_defaults.json 新键，值 "5602250"

def expense_claim_account_number(expense_type: str) -> str:
    """映射命中顺序：名称本身 → 名称等于某映射键的 _() 译文 → 兜底科目号。"""

def set_cn_expense_claim_accounts(company: str) -> list[str]:
    """签名、返回值、「站点无该 DocType 返回 []」「只配缺的、不覆盖」「缺科目一次报全、不写任何行」均不变。
    变的：遍历对象是站上全部 Expense Claim Type，科目号取 expense_claim_account_number()。"""

def repoint_generic_expense_claim_accounts(company: str) -> dict:
    """把本公司指向「无科目号的明细科目」的报销行改挂到 expense_claim_account_number(parent) 的科目；
    随后对这些通用科目逐个：无 GL Entry 时 frappe.delete_doc("Account", name)（不带 force），
    有 GL 或删除报 LinkExistsError → 保留、logger warning、记进返回值。站点无该 DocType 返回空结果。
    判「通用科目」只看 account_number 为空，不用 _()。
    返回 {"repointed": [类型名…], "deleted": [科目名…], "kept": [{"account", "reason"}…]}。"""

def clear_company_expense_claim_accounts(company: str) -> int:
    """站点无该 DocType 返回 0；否则删 Expense Claim Account 里 company == company 的行，返回删除行数。"""
```

`hooks.py` `doc_events["Company"]` 增 `"validate"`、`"on_trash"` 两项，指向上面同名函数。

## 四、技术假设

| 编号 | 假设内容 | 状态 | 验证方式 | 不成立时 |
|---|---|---|---|---|
| HT-017 | Company `validate` 钩子先于 HRMS 的 `on_update` 钩子跑；该时点补齐的报销行使 `set_expense_claim_type_accounts` 全部跳过、不建通用科目 | 已验证（探针 003b 以手工预调模拟；`frappe/model/document.py` `run_before_save_methods` 先于 `run_post_save_methods`） | TS-018 测试 | 暂停反馈 |
| HT-018 | 删除时框架先跑 `on_trash`（控制器在前、doc_events 钩子在后），再做链接检查；钩子里删掉报销行与 `Tax Rule` 后，不带 `force` 的删除成功 | 已验证（`delete_doc.py:173-183`、`document.py` `compose`；探针 d） | TS-017 测试 | 暂停反馈 |
| HT-019 | 复制建账的新公司上，改挂后不带 `force` 删通用科目成功，zh、en 两种语言下都成立；结果 267 科目（源 266＋`VAT`） | 已验证（探针 003c） | TS-019 测试 | 暂停反馈 |
| HT-020 | 在 Company `validate` 内保存 `Expense Claim Type` 不影响公司本身的保存（HRMS 在 `on_update` 里做同样的事） | 未验证 | TS-018 测试 | 暂停反馈 |
| HT-021 | 没有别的 DocType 链接 `Tax Rule`，删它不会被反向拦 | 已验证（全 bench `*.json` 搜 `"options": "Tax Rule"` 零命中） | TS-017 测试 | 暂停反馈 |
| HT-022 | 有交易的公司删除仍被框架拦下（GL Entry 链着公司），且本方案在 `on_trash` 里的删除随事务回滚 | 未验证（读码推断） | TS-017 测试 | 暂停反馈 |

## 五、切片划分与验收

| 切片 | 功能点 | 验收条件 |
|---|---|---|
| **SL-011** 删公司不再被拦、不留悬空行 | IT-002；DEC-023／024／025 | 1. HRMS 在场：新建中式公司后 `frappe.delete_doc("Company", name)`（不带 `force`）成功；该公司 `Expense Claim Account` 0 行、`Tax Rule` 0 条<br>2. `Standard` 公司同法删除成功，报销行 0<br>3. 删后同名再建中式公司：科目 266、报销行齐全且科目号与映射一致；随后再建一家 `Standard` 公司不报错<br>4. 只删本公司的：另一家公司的报销行与 `Tax Rule` 条数删前删后相同<br>5. **异常与边界**：① 站点无 `Expense Claim Type`（patch `frappe.db.exists`）→ 删公司不报错，`clear_company_expense_claim_accounts` 返回 0；② 公司有一张已提交凭证 → 删除仍报错，报错后该公司报销行与 `Tax Rule` 条数不变（HT-022）；③ `Standard` 公司删除不动任何 `Tax Rule` |
| **SL-012** 保存中式公司不丢报销映射 | IT-003；DEC-026／027／028 | 1. 中式公司新增一个报销类型 `_FCT 新类型` 后保存：报销行 6，新类型挂 `5602250` 的明细科目，原 5 行不变；科目 266、无无号明细科目；**且该次保存里 `repoint_generic_expense_claim_accounts` 的返回值 `repointed` 为空**（行在 HRMS 钩子之前已配好，不是建了再改挂）。`zh`、`en` 各跑一次<br>2. 连续保存两次结果相同（不再翻转）<br>3. **复制建账**：以中式公司为源、`Existing Company` 建新公司，`zh`、`en` 各一次 → 新公司报销行齐全，每行科目带科目号且与映射一致；无「费用报销记录」／`Expense Claims` 科目；科目数 267。复制的复制同样成立（`is_cn_company` 走链）<br>4. 某类型已指向别的**有号**科目时保存：该行不变（只改无号科目的行）<br>5. 类型名为译名（测试里建名为 `_("Travel")` 在 `zh` 下译文的类型）时按映射命中 `5602130`，不落兜底<br>6. **异常与边界**：① 通用科目已有 GL Entry → 行照改、科目保留，返回值 `kept` 列出它且有 warning 日志；② 映射科目号查不到 → 报错列全缺项、不写任何行（沿用 SL-002 ⑤）；③ 站点无 `Expense Claim Type` → `validate`／`on_update`／`repoint` 零写入；④ `Standard` 公司保存行为不变（HRMS 照常给它配通用科目，本 app 不动）<br>7. 静态检查：`frappe_china/**/*.py` 中无 `_remove_hrms_expense_claim_account`，无 `_("Expense Claims")` |

执行每个切片前，对照该切片验收条件检查方案覆盖性——如发现按方案写出的代码无法通过验收条件，暂停反馈，不硬写。

## 六、并行开发说明

无可并行任务：四个任务都改 `accounting/company.py` 或 `accounting/hr.py`。按序号执行。

## 七、任务清单

| 任务 | 对应切片 | 可并行否 |
|---|---|---|
| TS-017 删公司清理 | SL-011 | 否 |
| TS-018 保存前预配与兜底科目 | SL-012 | 否 |
| TS-019 复制建账改挂，删除旧删行逻辑 | SL-012 | 否 |
| TS-020 全量回归与收尾 | SL-011、SL-012 | 否 |

---

## 任务 17：删公司清理（对应切片 SL-011）

### 目标
任何公司都能不带 `force` 删掉，删后不留报销悬空行（DEC-023～025）。

### 具体改动
- **`accounting/company.py`**：新增 `is_cn_company`（伪代码见下）、`on_trash`；`before_insert`／`on_update` 里的 `is_cn_chart(_company_chart(doc))` 改调 `is_cn_company(doc)`（`_takes_cn_path` 不变，它只看本公司字段）。

```text
is_cn_company(doc):
    seen = set(); cur = doc（name 时 get_value 取 chart_of_accounts, existing_company）
    for _ in range(10):
        if is_cn_chart(cur.chart_of_accounts): return True
        if not cur.existing_company or cur.existing_company in seen: return False
        seen.add(cur.existing_company); cur = 取 existing_company 的两字段
    return False

on_trash(doc):
    from frappe_china.accounting.hr import clear_company_expense_claim_accounts
    clear_company_expense_claim_accounts(doc.name)
    if is_cn_company(doc):
        frappe.db.delete("Tax Rule", {"company": doc.name})
```
- **`accounting/hr.py`**：新增 `clear_company_expense_claim_accounts`（`frappe.db.delete`，不 import hrms）。
- **`hooks.py`**：`doc_events["Company"]["on_trash"]`。
- **测试** 新文件 `tests/test_company_hr_lifecycle.py`（继承 `FrappeChinaTestCase`，`setUpClass` 里 `Expense Claim Type` DocType 不存在则 `skipTest("HRMS 未安装")`）：SL-011 ①～⑤ 各一例。⑤② 用 `frappe.db.savepoint` 包住删除，断言报错后回到 savepoint 前的条数；造交易用一张最简 Journal Entry（`1001`／`5602250` 各 1 元）提交。

### 验证方式
`run-tests --module frappe_china.tests.test_company_hr_lifecycle`。判别力：临时注释掉 `on_trash` 两行删除，①②③ 失败；还原后 `git diff` 仅剩本任务改动。

## 任务 18：保存前预配与兜底科目（对应切片 SL-012）

### 目标
已有中式公司保存时，报销行在 HRMS 钩子跑之前已齐全（DEC-026、DEC-028）。

### 具体改动
- **`cn_tax/data/company_defaults.json`**：新增键 `"expense_claim_type_fallback": "5602250"`；`_comment` 补一句「未映射的报销类型挂此科目，待领域专家确认」。科目 `5602250 管理费用_其他` 已核为本表明细科目。
- **`accounting/hr.py`**：新增 `expense_claim_account_number`；改 `set_cn_expense_claim_accounts`：

```text
set_cn_expense_claim_accounts(company):
    if not frappe.db.exists("DocType", "Expense Claim Type"): return []
    mapping = _load_defaults()["expense_claim_type"]
    on_site = frappe.get_all("Expense Claim Type", pluck="name")
    对 mapping 里不在 on_site 的键 → logger warning（同原逻辑）
    todo = [(t, expense_claim_account_number(t)) for t in on_site
            if not frappe.db.exists("Expense Claim Account", {"parent": t, "company": company})]
    以下同原逻辑：取科目 → 收齐缺项一次 throw → 逐个 append + save

expense_claim_account_number(t):
    mapping = ...["expense_claim_type"]
    if t in mapping: return mapping[t]
    for key, number in mapping.items():
        if _(key) == t: return number
    return ...[FALLBACK_KEY]
```
- **`accounting/company.py`**：新增 `validate`（伪代码见接口契约）；判中式用 `is_cn_company(doc)`。
- **`hooks.py`**：`doc_events["Company"]["validate"]`。
- **测试**：`tests/test_company_hr_lifecycle.py` 补 SL-012 ①②④⑤，及 ⑥ 的 ②③④。① 用 `patch(..., wraps=...)` 包住 `repoint_generic_expense_claim_accounts` 取返回值。`tests/test_hr.py` 的 `test_missing_accounts_are_reported_together_before_any_write` 改为同时 patch `frappe.get_all` 返回那两个类型（原测试只 patch 了 `exists`，新实现会读真实类型列表），断言不变。

### 验证方式
SL-012 ①②④⑤，⑥ 的 ②③④。判别力：临时去掉 `hooks.py` 的 `validate` 项，① 失败——终态会被 TS-019 的改挂救回，失败落在「`repointed` 为空」那条断言上；还原。

## 任务 19：复制建账改挂，删除旧删行逻辑（对应切片 SL-012）

### 目标
复制建账出来的中式公司报销行齐全且指向带号科目，通用科目不留下（DEC-027）；删掉清零映射的旧逻辑。

### 具体改动
- **`accounting/hr.py`**：新增 `repoint_generic_expense_claim_accounts`：

```text
repoint(company):
    if not DocType 存在: return {"repointed": [], "deleted": [], "kept": []}
    rows = Expense Claim Account ⋈ Account on default_account
           where ECA.company == company and Account.account_number 为空或 NULL
    if not rows: return 空结果
    targets = {r.parent: _account_name(company, expense_claim_account_number(r.parent)) for r in rows}
    missing = [...] → _throw_missing_accounts（与预配同口径）
    for r in rows: frappe.db.set_value("Expense Claim Account", r.name, "default_account", targets[r.parent])
    for account in {r.default_account}:
        if GL Entry 存在: kept.append({account, "has GL entries"}); warning; continue
        try: frappe.delete_doc("Account", account, ignore_permissions=True)    # 不带 force
        except frappe.LinkExistsError as e: kept.append({account, str(e)}); warning
    frappe.clear_document_cache("Expense Claim Type")   # 绕过文档缓存直接改了子表
    return {...}
```
- **`accounting/company.py`**：`on_update` 非建账分支改为 `if is_cn_company(doc): repoint_generic_expense_claim_accounts(doc.name)`；**删除 `_remove_hrms_expense_claim_account`**。
- **测试**：`tests/test_company_hr_lifecycle.py` 补 SL-012 ③ 与 ⑥ 的 ①，⑦ 写进 `tests/test_scaffold.py`（读源码文本断言两个字符串不出现）。S4 的 `test_company` 复制建账用例（期望差集 `{("", "VAT")}`）不改，须照旧通过。③ 先断言 `frappe.get_installed_apps()` 里 `frappe_china` 在 `hrms` 之后（改挂必须在 HRMS 的钩子之后跑，讨论记录 F5），不满足即失败、不跳过。

### 验证方式
SL-012 ③、⑥ 的 ①、⑦；`test_company` 全过。判别力：临时让 `repoint` 直接 `return`，③ 失败（出现无号通用科目、科目数 268）；还原。

## 任务 20：全量回归与收尾（对应切片 SL-011、SL-012）

### 具体改动
1. 测试站 `bench --site test.localhost run-tests --app frappe_china`，回执报收集、通过、跳过条数，与 R5 的 180 条比只增不减。
2. 测试站残留核对：无 `_FCT` 前缀公司；`Expense Claim Account` 无指向不存在公司的行（`select count(*) from \`tabExpense Claim Account\` e left join tabCompany c on c.name=e.company where c.name is null` 为 0）。
3. 本 app `README.md`「已知限制」补一条：HRMS 在场时，未映射的报销类型保存公司时挂 `5602250`（DEC-028，待领域专家确认）；删公司时本 app 清该公司的报销行与（中式公司）`Tax Rule`。
4. D 回执「新增约定」记：「删公司时须清理的、他 app 未清的子表行由本 app 的 `Company.on_trash` 兜住；测试与脚本删公司一律不带 `force`」。

### 验证方式
完成标准两条；变异：TS-017／018／019 各一次判别力变异，均有测试失败，跑完 `git diff` 只剩本方案改动。

## 八、工作量

0.5–1 人日。最可能超出的是 SL-012 ③ 的「复制的复制」与 `en` 语言那两例（要各建三家公司）。

## 九、补充执行纪律（在 R3 总纲 §九之外）

1. **D 回执命名**：`P1-S5-R7-D回执.md`（D 步另起 Round R7，不拆 Part）；执行完回 E 复核。
2. **删公司一律不带 `force`**：测试清理靠事务回滚；确须删真实测试公司时用 `frappe.delete_doc("Company", name)`，被拦即暂停反馈，不改用 `force`。
3. **不碰演示站**：本方案只写测试站。演示站装 HRMS 是 SB 的 IT-005，装时一并带上本方案的代码；IT-006 补 SL-002 测试应在本方案 D 步之后做，写在 `tests/test_expense_claim.py`，不与本方案的 `tests/test_company_hr_lifecycle.py` 混写。
