# D回执（对象：代码 / 依据：P1-S4-R7-C开发方案-Part2）

**轮次**：P1-S4-R8｜**日期**：2026-09-30｜**步骤**：`plannedDev` D（build）
**依据**：[开发方案总纲](../R07-开发方案/P1-S4-R7-C开发方案-总纲.md)＋[Part2](../R07-开发方案/P1-S4-R7-C开发方案-Part2.md)
**执行纪律**：按任务顺序、测试先行；技术假设先验证再写依赖代码；本回执逐任务实时更新。

## 逐项执行结果

| 任务 | 对应切片 | 落地位置（文件:行） | 结果 | 完成时间 | 说明 |
|---|---|---|---|---|---|
| TS-009 结转凭证单据与过账 | SL-005 | `frappe_china/cn_tax/doctype/month_end_closing_voucher/month_end_closing_voucher.py:23`；`frappe_china/tests/test_closing_voucher.py:38` | ✅完成 | 2026-09-30 | 自有可提交凭证、子表、列表页生成/取消入口、Company 城建税档位 fixture 均已落地；提交过账、逆序取消约束与独立命名序列通过测试 |
| TS-010 结转的计算、生成、取消与状态 | SL-005 | `frappe_china/accounting/ledger.py:9`；`frappe_china/accounting/closing.py:230`；`frappe_china/tests/test_closing.py:16` | ✅完成 | 2026-09-30 | 统一 GL 取数、增值税/附加税/损益/本年利润四类结转、草稿提醒、原子生成取消与状态检查落地 |

## 方案要求的验证

| 任务 | 验证方式（方案原文） | 怎么跑的 | 实测结果 |
|---|---|---|---|
| TS-009 | `test_closing_voucher.py`：HT-004、HT-012 与异常输入 | 先跑到 4/4 因模块缺失红灯；实现并迁移测试站后反复定向运行 | ✅4/4；2 条 GL、借贷相等、`voucher_subtype` 正确，取消产生冲销；公司/月前缀分别从 001 独立起号；直插、非 12 月年末结转与 Accounts User 创建均被拒绝 |
| TS-010 | `test_closing.py`：SL-005 验收第 1–11 条与第 13 条 | 9 个集成测试真实提交 Journal Entry 与结转凭证，金额断言直接查 GL、不经被测 `gl_sums` | ✅9/9；正常月、重复、逆序取消重做、留抵跨月、多交、草稿、上月未结、结转后变动、冻结期、年末、折旧、非自然年与城建税档位均覆盖 |

## 技术假设验证

| 假设 | 依赖任务 | 状态 | 实测结果 |
|---|---|---|---|
| HT-004 自有 `AccountsController` 单据可提交、过账、取消并写入 `voucher_subtype` | TS-009 | ✅成立 | 提交后 2 条有效 GL、借贷各 100、类型均为 `VAT Transfer`；取消后原分录标取消并生成冲销 |
| HT-012 动态前缀命名序列按公司与月份独立计数 | TS-009 | ✅成立 | 同公司 3/4 月、两公司 3 月分别得到 `001/002`；失败插入会消耗序号，属上游 `tabSeries` 既有语义，业务重做继续编号亦符合方案 |

## 全量验证

| 门 | 结果 |
|---|---|
| Part2 定向测试 | ✅`test_closing_voucher.py` 4/4；`test_closing.py` 9/9 |
| `bench --site test.localhost run-tests --app frappe_china` | ✅43/43 全部通过（100.411 秒；Part1 基线 30 个，新增 13 个） |
| 格式与静态检查 | ✅主仓与 app 仓 `git diff --check`；Python `compileall`；列表页 JS `node --check` 均通过。ruff 仍未安装 |
| 演示站基线 | ✅只读 SQL：Company 1／GL 22／SLE 12／Account 95，未安装或写入本 app |

## 偏离与暂停

- 测试站首次迁移时发现 v16 要求子表也有同名 Python 模块；补入空 `Document` 控制器后迁移成功，未改变方案接口。
- `tabSeries` 在凭证插入后续校验失败时也会消耗序号；验收只要求公司/月前缀独立与重做接着排，故保留上游行为，不自行回退序号。

## 新增约定

| 约定 | 类别（命名/位置/错误处理/依赖/跨层调用） | 在哪个任务确立 |
|---|---|---|

## 未做项

| 项 | 为什么没做 |
|---|---|

## 状态值

- **Part2 已完成（D 步进行中）**——TS-009～010 全部完成；下一续跑点为 Part3 的 TS-011。

## 复核建议

1. 优先抽查 `frappe_china/accounting/closing.py` 的 `_vat_transfer_rows` 与 `_pl_transfer_rows`：前者决定留抵/未交/多交分支，后者按科目＋成本中心逐一结平。
2. 抽查 `MonthEndClosingVoucher.before_cancel` 与 `cancel_month_end_closing` 的双层逆序约束，确认直接取消和批量取消都不会留下半套结转。
3. 当前结转算法测试以正常提交的 Journal Entry 精确造数；销售/采购发票的含税与未税过账由 Part1 `test_e2e_minimal.py` 独立覆盖，尚未写成“发票提交后立即结转”的单一跨模块测试，这是本切片最薄处。
4. `month_end_closing_voucher_list.js` 已做语法检查但未做浏览器点击验收；建议 E 步手动点一次生成、草稿确认和取消三个交互。
