# D回执（对象：代码 / 依据：[R6-C 开发方案](../R06-开发方案/P1-S5-R6-C开发方案.md)）

**轮次**：P1-S5-R7｜**日期**：2026-10-06｜**执行者**：Codex（TS-017～019 代码，提交 `8433978`）；Claude（Opus 5.5，续做：修正、测试、TS-020 收尾）
**状态值**：`代码已落地`

> **续跑说明**：Codex 交回时 TS-020 未完成，测试文件没有写，集成测试一条都没跑（原回执「尚未验证」节）。本 Session 按续跑锚点从 TS-017 的测试部分续做，没有重做已完成的代码，只修了下面「偏离与暂停」列出的几处与方案不符的地方。

## 逐项执行结果

| 任务 | 对应切片 | 落地位置（文件:行） | 结果 | 完成时间 | 说明 |
|---|---|---|---|---|---|
| TS-017 删公司清理 | SL-011 | `accounting/company.py` `is_cn_company`:33-49、`before_insert`:60-61、`on_trash`:109-113；`accounting/hr.py` `clear_company_expense_claim_accounts`:132-137；`hooks.py`:160；`tests/test_company_hr_lifecycle.py` SL-011 七例 | ✅完成 | 2026-10-06 | Codex 写了代码；Claude 把 `before_insert` 的判法改为 `is_cn_company`（方案要求，Codex 漏改），补测试 |
| TS-018 保存前预配与兜底科目 | SL-012 | `cn_tax/data/company_defaults.json`（`expense_claim_type_fallback`、`_comment`）；`accounting/hr.py` `expense_claim_account_number`:19-26、`set_cn_expense_claim_accounts`:29-69；`accounting/company.py` `validate`:76-79；`hooks.py`:158；`tests/test_hr.py`:28；`tests/test_company_hr_lifecycle.py` SL-012 ①②④⑤⑥②③④ | ✅完成 | 2026-10-06 | Claude 把 `set_cn_expense_claim_accounts` 改为遍历站上全部类型（Codex 版仍只遍历映射，未映射类型永远不配）；`_comment` 补兜底说明 |
| TS-019 复制建账改挂，删旧删行逻辑 | SL-012 | `accounting/hr.py` `repoint_generic_expense_claim_accounts`:82-129；`accounting/company.py` `on_update`:82-90；`tests/test_company_hr_lifecycle.py` SL-012 ③、⑥①；`tests/test_scaffold.py` ⑦ | ✅完成 | 2026-10-06 | Codex 删了 `_remove_hrms_expense_claim_account` 的定义，但 `on_update` 仍在调它（任何已有中式公司保存都会报 `NameError`）；Claude 改为调 `repoint`，并补 warning 日志、改用一条 join 查无号科目 |
| TS-020 全量回归与收尾 | SL-011、SL-012 | `README.md`「已知限制」两条；测试站残留核对；本回执「新增约定」 | ✅完成 | 2026-10-06 | 见「全量验证」 |

## 全量验证

| 门 | 结果 |
|---|---|
| 专项 `run-tests --module frappe_china.tests.test_company_hr_lifecycle` | 15/15 通过 |
| 判别力变异（各跑一次专项，跑完还原，`git status` 无残留 `.bak`） | TS-017 去掉 `on_trash` 两行删除 → 14 例报错（SL-011 全部 7 例失败，删公司报 `LinkExistsError`、此后建公司报 `LinkValidationError`）；TS-018 去掉 `hooks.py` 的 `validate` → SL-012 ① 失败在「`repointed` 为空」断言上（与方案预期一致），⑥② 失败；TS-019 让 `repoint` 直接返回 → SL-012 ③ zh／en／复制的复制全部失败（出现无号通用科目、科目号为空），⑥① 失败 |
| 全量 `bench --site test.localhost run-tests --app frappe_china`（`logs/s5-r7-regression.log`） | **收集 196、通过 196、跳过 0、`EXIT=0`**，耗时 12 分 47 秒。对比 R5 基线 180：只增不减（+15 生命周期、+1 SL-012 ⑦ 静态检查） |
| 残留核对（TS-020 第 2 步） | `_FCT` 前缀公司 0；`Expense Claim Account` 指向不存在公司的行 0；`_FCT` 前缀报销类型 0 |
| `python -m py_compile`（改过的 4 个 .py ＋ 新测试） | 通过 |

S4 的 `test_company.test_existing_company_path_uses_native_clone`（复制建账差集 `{("", "VAT")}`）未改，照旧通过。

## 偏离与暂停

Codex 的实现与方案不符、本 Session 已改正的几处（都在方案范围内，不是方案外改动）：

1. `on_update` 仍调已删除的 `_remove_hrms_expense_claim_account`，任何已有中式公司保存即报 `NameError`。改为方案 TS-019 的 `repoint_generic_expense_claim_accounts`。
2. `set_cn_expense_claim_accounts` 仍只遍历映射里的 5 个键，方案 §二要求遍历站上全部 `Expense Claim Type`；不改则 DEC-028 兜底永远不生效，SL-012 ① 不成立。
3. `before_insert` 仍用 `is_cn_chart(_company_chart(doc))`，方案 TS-017 要求改调 `is_cn_company`（复制的复制要沿链找）。
4. `repoint` 通用科目被保留时没有 warning 日志（SL-012 ⑥① 要求）；补上。
5. `company.py` 一行注释被存成乱码（`涓?set_cn_default_accounts 鍚屼竴…`，GBK 误读后存成 UTF-8），已还原原文。`hooks.py` 两行缩进是空格，与周围制表符不一致，已改。

无暂停反馈项。

## 新增约定

| 约定 | 类别 | 在哪个任务确立 |
|---|---|---|
| 删公司时须清理的、别的 app 不清的子表行由本 app 的 `Company.on_trash` 兜住；测试与脚本删公司一律不带 `force` | 跨层调用／错误处理 | TS-017（R6 方案 TS-020 第 4 条） |
| 依赖可选 app 的功能只在该 DocType 存在时生效、模块顶层不 import 它（R3 Part1 TS-005 已提出，本轮测试沿用） | 依赖 | TS-018 |
| 判「通用科目」看科目号是否为空，不按 `_()` 比科目名（科目按建出时的语言命名） | 命名 | TS-019 |

## 未做项

无。

## 状态值

`代码已落地`：TS-017～020 全部完成；SL-011、SL-012 验收条件各有测试覆盖并通过；全量 196/196。下一步回 E 复核（与 SB 的 IT-005／006 等合并复核）。

## 复核建议

1. **最该看：本 Session 对 Codex 实现的 3 处功能性改正**（「偏离与暂停」1～3）。查法：`git -C frappe-bench/apps/frappe_china diff 8433978 -- frappe_china/accounting`。第 1 条若漏改，演示站接入 HRMS 后任何人点一次公司「保存」就报错。
2. **SL-012 ① 的「`repointed` 为空」断言**是区分「保存前预配」与「建了再改挂」的唯一判据，两者终态完全相同。查法：看 TS-018 变异的输出，失败只落在这条断言上，终态断言都过了。
3. **拿不准处**：
   - HT-020（在 Company `validate` 里保存 `Expense Claim Type` 不影响公司本身保存）由 SL-012 ①② 间接覆盖，没有单独构造冲突场景。
   - LG-014：演示站装 HRMS 时报销类型名是否为英文，要到 SB 的 IT-005 才能实测；若是中文名，按译名命中映射（SL-012 ⑤ 已测「译名命中」这一路）。
