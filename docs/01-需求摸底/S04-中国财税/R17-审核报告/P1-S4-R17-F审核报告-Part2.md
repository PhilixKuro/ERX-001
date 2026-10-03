# 审核报告·Part2（复核轮）：月末结转凭证与 closing.py／ledger.py

**轮次**：P1-S4-R17｜**步骤**：`plannedDev` F（play-audit，回 F 复核）·分片 2｜**日期**：2026-10-03｜**执行者**：Claude 子 Agent（Opus 5.5，独立第三方）
**依据**：R7 开发方案 Part2（TS-009、TS-010、SL-005 验收 13 条）与总纲 §六；B 需求文档 §4.7；R15 C 开发方案 TS-024／TS-025（只看与本片的交互）；DEC-121（R12 SB 讨论记录）、DEC-122／124（R15 C 讨论记录）；`docs/业务规则.md`；`docs/开发守则.md`「静默失败」；R14 F 审核报告主报告（当场修清单）与 Part2 分片报告；R14 SB 修复回执。
**被审范围**：`frappe-bench/apps/frappe_china`，`git diff 40200dc 21faeb9` 中 Part2 相关部分；HEAD＝`21faeb9`，工作区干净。
**片内编号**：`P2-xx`，收口时转 `FD-` 前缀。

---

## 覆盖自证

**读全了的**
- 文档：R7 Part2 全文；R14 Part2 分片报告全文；R14 主报告的 FD-004…043 表格行、「当场修清单」与复核节；R14 SB 修复回执全文；R15 C 方案 TS-024／TS-025 全文与 §SL-012；R15 C 讨论记录的 DEC-122…124 与否决方案；R12 SB 讨论记录的 DEC-121；`业务规则.md` 全文；B 需求 §4.7.3、§4.7.4。
- 代码（21faeb9 全文）：`accounting/closing.py`（413 行）、`accounting/ledger.py`（130 行）、`month_end_closing_voucher.py`、`month_end_closing_voucher_list.js`、`month_end_closing_voucher.json` 的 permissions。
- diff（40200dc→21faeb9）：`closing.py`、`ledger.py`、`month_end_closing_voucher/*`、`hooks.py`、`statements/engine.py`（只看 FD-030 那段）、`statements/balance_sheet.py`（1901 说明行）、`tests/test_closing.py`、`tests/test_closing_voucher.py`、`tests/test_translations.py`、`translations/zh.csv`。
- 上游读码：`erpnext/accounts/general_ledger.py`（`make_gl_entries:36-56`、`validate_accounting_period:155-187`、`distribute_gl_based_on_cost_center_allocation:205-245`、`make_reverse_gl_entries:683-760`）；`erpnext/hooks.py:326-357`（`period_closing_doctypes` 与 doc_events）；`accounting_period.py:86-107`；`controllers/queries.py:906-912`；`accounts/utils.py`（`is_immutable_ledger_enabled:2706`、`repost_gle_for_stock_vouchers:1647-1693`、`compare_existing_and_expected_gle`）；`controllers/accounts_controller.py:534-560`（`on_trash`）；`frappe/handler.py:99-110`、`frappe/__init__.py:426-466`、`public/js/frappe/request.js:110`；`frappe/model/delete_doc.py`。

**站点只读查询**（两站，`bench mariadb -e "SELECT …"`）
- `tabDocPerm`（结转凭证）：Accounts Manager／System Manager `delete=0`、`amend=0`，Accounts User 只读；`tabCustom DocPerm` 0 行。两站相同。
- `Accounts Settings`：`enable_immutable_ledger=0`、`delete_linked_ledger_entries=0`。
- `Accounting Period`、`Finance Book`、`Cost Center Allocation`、`Month End Closing Voucher` 均 0 行。

**跳过及原因**
- 未跑任何测试、未做变异（硬约束：主会话在测试站跑全量回归）。本表「生效否」一列是读码＋读断言，不是实测。
- 未在浏览器点列表页按钮（无浏览器自动化，与 R9–R14 相同）。
- FD-007 新逻辑本身的正确性（R15 验收逐条）归分片 5，本片只查它与 Part2 已修项的交互。
- `engine.py` 中 FD-017／018／019 的改动属分片 3，只看了 FD-030 那一处。

---

## 已修项复核表

| FD 号 | R14 判定标准 | 定位（文件:行） | 落地 | 生效否 | 原问题消失否 | 自证一致否 | 说明 |
|---|---|---|---|---|---|---|---|
| FD-010（closing.py 连带部分） | `_` 不被局部变量遮蔽，报错是原提示而非 `TypeError` | `closing.py:342` `_start, end`；`:215` `for _account, amount` | ✅ | ✅ | ✅ | ⚠️ 部分不一致 | 本片相关文件里已经没有 `_` 赋值（grep 查过）。`cancel_month_end_closing` 那处是真缺陷：函数体内任何地方给 `_` 赋值，`_` 在整个函数里都是局部变量。R14 收口说「`_surtax_rows` 里 `for _, amount` 同样把 `_` 变成局部变量」，**这一句不对**：生成器表达式有自己的作用域，原代码不会遮蔽外层 `_`，改名无害但也不是修复。另外「前者使空月取消报 `TypeError`」的描述也不准：40200dc 时空月直接返回 `[]`，根本不调 `_`。真正受害的是 `:349`「Cancel later Month End Closing Vouchers first」这句（从 R8 起，只要后面月份还有有效凭证就去取消前面的月份，就报 `TypeError`）。这条路径至今没有测试，见 P2-05 |
| FD-011 | 计税依据很小、三项附加税都舍入成 0 时，整月照常结转，并给出说明 | `closing.py:311-319`；`zh.csv` 新词条；`test_closing.py:493-502` | ✅ | ✅ | ✅ | ✅ | `_surtax_rows` 总会放一行 5403 借方，金额为 0 的贷方行不放，所以 `len(rows) > 1` 正好等价于「至少一项不为 0」。返回的 message 是「月末结转已完成；附加税各项舍入后均为 0…」。测试按应纳 0.05 造数，断言只生成 VAT Transfer、带说明、5403 为 0，能区分修前和修后（R14 M6）。与 FD-007 的交互：这个月有 VAT Transfer、没有损益发生额，所以 `closed` 为真（`:369`），状态完整，下月不会被拦 |
| FD-012 | 会计期间关闭后不能再生成或取消结转凭证 | `hooks.py:161-163`；上游 `general_ledger.py:48`（过账）、`:718`（冲销）、`:155-187`；`accounting_period.py:86-94` | ✅ | ✅（只对**登记钩子之后**新建的会计期间生效） | ✅（有条件） | ✅ | `get_hooks` 会把各 app 的列表合并，`get_doctypes_for_closing` 预填时能带上本单据。过账和冲销两条路都走 `validate_accounting_period`。erpnext `doc_events` 里的 `tuple(period_closing_doctypes)` 用的是 erpnext 自己模块里的列表，不包括本单据，但它不是拦截所必需的。**条件**：钩子之前已经存在的会计期间，其「已关闭单据」子表不会自动补上本单据（两站都是 0 个会计期间，现在没有影响）。测试只覆盖了生成，没覆盖取消。见 P2-04 |
| FD-013 | 带账簿的损益 GL 不再被静默漏结 | `closing.py:128-151`（`_assert_no_finance_book_pl`）、`:295` 调用；`zh.csv`；`test_closing.py:546-567` | ✅ | ✅ | ⚠️ 部分 | ✅（回执写明只管损益类） | 损益类一侧已消失：查本年初至本月末 `is_cancelled=0`、有账簿、根类型为损益的 GL，有就报错并列出账簿名。测试先造损益类账簿分录（被拦），再造资产类账簿分录（照常结转），能区分。**遗留**：结转还从 `gl_sums` 读 2221000 组（增值税结转与计税依据）和 3103（年末结转），这些科目上带账簿的分录照样被静默排除。测试里的判别用例反而把「资产负债类带账簿不拦」固定成了预期行为。见 P2-01 |
| FD-014 | 开启不可变总账时，生成与取消的所有入口都明确报错 | `closing.py:119-125`、`:284`、`:338`；`month_end_closing_voucher.py:127-129`；`test_closing.py:569-584` | ✅ | ✅ | ✅ | ✅ | 三个入口都覆盖：批量生成、批量取消、单张取消（`before_cancel`，列表页批量取消也会走到它）。测试 patch 的是 `frappe_china.accounting.closing.is_immutable_ledger_enabled`，`before_cancel` 调的也是 closing 模块里的这个名字，所以三条路都会被 patch 到，有判别力。检查顺序：生成时排在权限之后、其它所有检查之前，不会与别的报错叠加。报错词与上游官方译名一致（「启用不可篡改账本」「会计设置」，`erpnext/locale/zh.po:19188,2292`） |
| FD-015 | 两个写入口只收 POST | `closing.py:281`、`:335`；前端 `frappe.call` 默认 `type: "POST"`（`request.js:110`）；`handler.py:99-110` | ✅ | ✅ | ✅ | ✅ | 列表页两处都用 `frappe.call` 且不指定 `type`，所以前端不受影响。测试直接断言 `allowed_http_methods_for_whitelisted_func` 并调用 `is_valid_http_method`，有判别力（R14 M8） |
| FD-016 | 取消主按钮不再叫「取消」、有二次确认；空月报错，不返回空列表 | `month_end_closing_voucher_list.js:32-48`；`closing.py:350-353`；`zh.csv:16`（「取消月末结转」）及新确认词条；`test_closing_voucher.py:170-175` | ✅ | ✅（前端未实点） | ✅ | ✅ | 主按钮是「取消月末结转」，接着弹 `frappe.confirm`「确定冲销第 {0} 月的全部结转凭证？」。后端报错时 `frappe.call` 不走 callback，不会再出现「已取消」。确认框里没有公司和年度（观察，见 P2-07） |
| FD-030 | 「排除哪些结转子类型」只在一处定义，取数 SQL 引用它 | `ledger.py:11`、`:77-83`；`engine.py:12`、`:72-73`、`:89`；`closing.py:11`、`:20` 再导出 | ✅ | ✅ | ✅ | ✅ | 全仓 grep：子类型字面量只剩 `ledger.py:11` 和 `CLOSING_TYPES`。参数化 `IN %(…)s` 传的是 tuple，pymysql 会展开。测试断言 `is` 同一对象，并且源码里不再出现 `'P&L Transfer'`。这个字符串检查只认单引号，写成双引号的字面量查不出来（判别力偏弱，观察） |
| FD-031 | 结转凭证不可删除 | `month_end_closing_voucher.json` permissions；两站 `tabDocPerm` | ✅ | ✅（两站 SELECT 实证 `delete=0`） | ✅ | ✅ | Administrator 照上游惯例仍能删（`permissions.py:108`），不算问题。`write=1` 仍在，但本单据只能经生成入口建，建完马上提交，没有草稿可写，无影响 |
| FD-033 | 「有无损益发生额」「月末损益余额非 0」两处都按科目＋成本中心判 | `closing.py:100-107`、`:393-397`；`test_closing.py:504-518` | ✅ | ✅ | ✅ | ✅ | 两处都加了 `by_cost_center=True`。测试（成本中心间重分类）只能区分第一处（R14 M12 变异的也只是 `_pl_has_activity`）。第二处（状态里的余额判据）**没有能区分它的测试**，见 P2-02。和 FD-007 的交互：只有成本中心重分类的月份现在算有发生额，必须先结转，否则下月被拦（测试 `:514` 已覆盖） |

**R14 判为延迟的 Part2 项（只确认有没有变得更糟）**

| FD 号 | 结论 | 说明 |
|---|---|---|
| FD-032 跨年不设闸 | 未变糟 | `_incomplete_previous_months` 仍是 `range(1, month)`，只看本年。R15 新加的 12 月 1901 检查只影响 12 月自己，次年 1 月照常能生成，与 R15 方案明写的一致 |
| FD-034 附加税法定调整 | 未变糟 | 计税依据公式未改；FD-011 只在全为 0 时跳过 |
| FD-035 原生损益报表与预算失真 | 未变 | 无相关改动 |
| FD-036 并发重复 | 基本未变 | 互斥机制仍是「先查后写」。生成前多了 `_incomplete_previous_months` 的读（最多 11 个月），检查和写入之间的时间窗略长，概率仍低 |

---

## 开放查漏新发现

| 片内编号 | 严重程度 | 定位 | 问题 | 违背的标准 | 建议修法 | 建议档位 | 待裁决点 | 证据 |
|---|---|---|---|---|---|---|---|---|
| P2-01 | 低 | `closing.py:128-151`；`:167-193`（`_vat_transfer_rows`）、`:261-277`（`_year_end_rows`）；`ledger.py:38` | **FD-013 只挡住了损益类，结转读的另外两组科目仍会静默漏掉带账簿的分录。** 增值税结转与计税依据读 2221000 组和 2221002，年末结转读 3103，全都经 `gl_sums`，而 `gl_sums` 只取空账簿。一张填了账簿的 Journal Entry（借 1002 贷 2221005）不会被拦，增值税组余额 B 少算，计税依据和附加税跟着少算，结转后 2221000 组也不归零。`month_closing_state` 不查增值税组，所以没有任何提示。测试 `test_finance_book_pl_entries_block_closing` 的判别用例写的是「只有资产负债类科目带账簿时不拦」，把这个缺口固定成了预期行为。两站 Finance Book 为 0 行，现在只是潜在问题 | 开发守则「静默失败」；SB 回执新增约定「本 app 不支持的站点级开关在每个入口明确报错挡住，不在取数里静默忽略」；BR-004（组余额应全部转出） | 检查范围从「损益类」扩大到「结转会读的科目」：损益类 ∪ `leaf_accounts_under("2221000")` ∪ 3103。或者干脆查本年初至月末任何带账簿的 GL（与「本 Stage 不支持账簿」的裁决最一致）。补一条用例：2221005 带账簿 → 被拦 | 本Session修 | 只扩到结转读的科目，还是凡带账簿一律拦（后者会让 1001/1002 的判别用例反转） | 读码：`closing.py:140` 的 `root_type IN ('Income','Expense')`；`:168-173` 与 `:263` 都经 `gl_sums`；`ledger.py:38` |
| P2-02 | 观察 | `closing.py:393-397`；`tests/test_closing.py` | FD-033 改的第二处（`month_closing_state` 里「月末损益余额非 0」那条判据）没有能区分修前修后的测试。改回只按科目汇总，全量测试照样通过：已结转月份如果出现「按科目净额为 0、按成本中心不为 0」的情况，现有测试只会走「结转后有变动」那条，碰不到这条判据。现在 FD-007 用状态做硬拦截，这条判据也会决定下月能不能生成 | 开发守则「判据须能区分」 | 补一条用例，造出「已结转、无后续 GL、按科目＋成本中心不为 0」的状态。最简单的办法是在测试里直接改一条结转 GL 的 `cost_center`（只为造状态），断言出现 nonzero 那条 issue。或者在变异清单里加一组 | 本Session修 | — | 读断言：`test_cost_center_reclassification_counts_as_activity` 只断言 `closed`／`complete`／生成被拦，结转后不会出现按成本中心不为 0 的余额 |
| P2-03 | 观察 | 上游 `general_ledger.py:194-195`、`:205-245`；`closing.py:224-251`、`:216` | **Cost Center Allocation 会把结转凭证的分录拆到子成本中心。** `process_gl_map` 对所有不是期末结账单的单据都做成本中心分摊，本单据也一样。有两种情形：① 某主成本中心设了分摊，而本年有早于分摊生效日的分录记在该主成本中心上，损益结转按 (科目, 主成本中心) 冲平的那行会被按比例拆到子成本中心，主成本中心的余额冲不掉，子成本中心反而出现反向余额；② 附加税那行 5403 记在公司默认成本中心上，如果默认成本中心设了分摊，按比例拆分各自舍入后，借贷可能差一分钱（是走舍入科目还是直接报错，没有读到底）。以前状态判据只按科目，看不出情形 ①。FD-033 之后能看出来了，但 FD-007 又把它变成硬拦截：下月一直生成不了，取消重做也是同样结果，没有出路。两站 Cost Center Allocation 为 0 行 | SL-005 ①「按科目＋成本中心逐一为 0」；SB 新增约定（不支持的开关在入口明确报错） | 生成入口参照 FD-013／014，查本公司有没有生效的 Cost Center Allocation，有就报「月末结转不支持成本中心分摊」。或者登记为已知限制 | 新Session修 | 是否支持成本中心分摊（建议本 Stage 不支持、报错挡住） | 读码：`general_ledger.py:194` 只把期末结账单排除在分摊之外；读码推断，未实跑 |
| P2-04 | 观察 | `hooks.py:161-163`；上游 `accounting_period.py:86-107`；`test_closing.py:520-544` | FD-012 只对**加钩子之后**新建或手工补行的会计期间生效：已经存在的会计期间，「已关闭单据」子表是建的时候按当时的钩子填的，不会自动补上本单据。测试只覆盖了生成被拦，没覆盖取消（`make_reverse_gl_entries:718` 同样会查，读码可知）。与 FD-007 的交互：如果一个不完整的以前月份落在已关闭的会计期间里，以后各月都生成不了，只有 `exempted_role` 的人能处理，报错里也不提这一点 | 方案 Part2 的「过账自带会计期间校验」（FD-012 原意） | README 已知限制写一句「加装本 app 之前建的会计期间，须手工在『已关闭单据』里补上结转凭证」。补一条取消被拦的测试 | 延迟或不修 | 是否值得为存量会计期间写 patch（两站都是 0 个，建议不写） | 读码；两站 `tabAccounting Period` 0 行 |
| P2-05 | 低 | `closing.py:343-349`；`tests/` 全目录 | 方案 TS-010「取消时若有更晚月份的有效结转凭证，抛错并列出」，`cancel_month_end_closing` 这条路径**从 R8 到现在都没有测试**。R14 修掉的 `_` 遮蔽恰好就藏在这里：40200dc 及以前，只要后面月份还有有效凭证，去取消前面的月份就抛 `TypeError`（`'datetime.date' object is not callable`），而不是「请先取消以后月份的结转凭证」。现有测试没发现它，FD-010 的复核也把它描述成了「空月取消」。现在 FD-007 的恢复流程正好要用到这条路（补录 2 月而 3 月已结 → 先取消 3 月 → 再取消 2 月），出现频率比以前高 | §4.7.3 第 2 条；方案 TS-010 取消第 2 点；开发守则「判据须能区分」 | 补测试：2 月、3 月都结转后调 `cancel_month_end_closing(…, 2)`，断言报 `ValidationError`，消息含 3 月凭证号的译文，且两月凭证仍为已提交 | 本Session修 | — | grep `tests/`：`cancel_month_end_closing` 共 9 处调用，没有一处是在更晚月份仍有效时调用；40200dc `closing.py` 有 `_, end = _month_dates(...)`，其后才 `frappe.throw(_("Cancel later …"))` |
| P2-06 | 观察 | `zh.csv`「Documents changed after month end closing; cancel and regenerate」→「…请取消本月结转后重新生成」；`closing.py:296-298` | FD-007 把状态 issue 原样拼进「生成本月」的报错，如「以下月份结转不完整，请先处理：2 月：结转后该月又有凭证变动（新增或取消），请取消**本月**结转后重新生成」。会计此时正在生成 3 月，「本月」容易读成 3 月。另外，2 月之后如果已经有月份结转过，按提示「取消本月」会被「请先取消以后月份」挡住，提示里没说要先取消更晚的月份 | 需求 §4.11 第 4 条（提示要真、要能照着做）；DEC-124「告诉会计该先重做哪个月」 | 译文「本月」改「该月」。在生成拦截的报错末尾加一句「如之后月份已结转，须先逆序取消」。只改译文和一条新词条，不改源词，报表说明行按源词匹配，不受影响 | 本Session修 | 措辞（属界面文案，可由 Claude 定） | 读 `zh.csv` 与 `closing.py:296-298`、`balance_sheet.py:66-86` |
| P2-07 | 观察 | `month_end_closing_voucher_list.js:40-41` | 取消的确认框只说「确定冲销第 {0} 月的全部结转凭证？」，没有公司和年度。多公司、跨年度时容易点错 | DEC-119 会计习惯（冲销须确认清楚） | 确认词条改为带公司和年度：`__("Reverse all Month End Closing Vouchers of {0} {1} month {2}?", [company, fiscal_year, month])` | 延迟或不修 | — | 读码 |
| P2-08 | 观察 | `closing.py:110-116`、`:364-413`；`balance_sheet.py:71-72` | `month_closing_state` 现在被循环调用：生成 12 月时调 11 次，资产负债表和利润表各调 1…month 次。每次最多 5 条查询，其中「本年初至月末、按科目＋成本中心」的 `gl_sums` 让总扫描量与月份数的平方成正比。函数只读、没有副作用（已核：全部是 `get_all`／`exists`／`gl_sums`），按小企业数据量不构成问题 | — | 不修；数据量大了再考虑每个请求缓存一次年初至各月末的汇总 | 延迟或不修 | — | 读码 |

---

## 业务规则合规核表

| 规则 | 本片改动是否涉及 | 结论 | 备注 |
|---|---|---|---|
| BR-001 小企业会计准则 | 是（1901 年末检查、3103／3104090 未动） | 合规；1901 处理口径为**草案·待领域专家确认**（DEC-122、LG-154） | 准则科目说明：待处理财产损溢应在期末（年末）结账前处理完毕，处理后应无余额。R15 只在 12 月提示、不拦截，与「年末结账前处理完毕」一致。本片未取得准则原文逐字比对 |
| BR-004 增值税月末转出 | 是（逻辑未改；P2-01 涉及取数口径） | 计算逻辑合规（同 R14 推演 6 例，代码 `:167-193` 未变）；**P2-01 情形下组余额会漏转** | 「多交取 B 与 paid 较小者」「结转范围限 2221001…2221010」仍是**草案·待领域专家确认** |
| BR-005 城建税与附加 | 是（FD-011） | 合规；舍入全为 0 时不计提，属**草案·待领域专家确认** | 各项按分舍入后为 0，即应计提额为 0，不计提与「应纳 × 税率」不矛盾。申报时税务系统按月计税依据另算，可能与账面差几分钱，属既有的各自舍入口径（DEC-116）。FD-034 的法定调整仍未覆盖（延迟） |
| BR-006 资产负债平衡 | 间接 | 合规 | FD-011 跳过的是整张凭证，不会出现借贷不平的单张凭证；`validate` 的借贷相等校验未动 |
| BR-007 价税分离舍入 | 否 | — | — |
| DEC-121 空月不算未结转 | 是（FD-007 依赖） | 保留（草案·待专家确认，LG-153） | `month_closing_state:369` 中「无损益发生额 → closed」未变。FD-033 之后「有无发生额」改为按成本中心判，只有成本中心重分类的月份也要求结转，与「无余额即无结转对象」的意图一致 |
| DEC-124 以前月份须完整 | 是（与本片交互） | 与 Part2 已修项不冲突（本片视角） | 交互见下方交接摘要；拦截口径本身是**草案·待领域专家确认** |
| SB 新增约定「不支持的开关在每个入口明确报错」 | 是（FD-013／014） | FD-014 完全符合；FD-013 只覆盖损益类（P2-01）；Cost Center Allocation 未纳入（P2-03） | — |

---

## 交接摘要

**本片依赖别片**
- 分片 5（R15/R16）：`_incomplete_previous_months` 与 12 月 1901 检查是否满足 SL-011 ⑦⑧、SL-012 ①–⑥，本片未逐条核。
- 分片 1：中国科目表里 1901 是明细科目（已读科目表 JSON：`1900` 组下的唯一明细 `1901`，`root_type` 为空，从上级继承 Asset）；2221000 组结构；`Company.cost_center`。
- 分片 3：`_closing_notes` 消费 `month_closing_state` 的 issue 源词（R16 新增的 `PENDING_LOSS_ISSUE` 分支，`balance_sheet.py:82-85`）；`engine.allocate_surtax` 引用 `PL_EXCLUDED_SUBTYPES`。

**本片暴露给别片**
- `month_closing_state(...)` 的 `complete` 现在同时是**报表说明行**和**生成拦截**的判据（DEC-124）。它的盲区会同时影响两处：P2-01（账簿分录不进增值税组与 3103）、P2-03（成本中心分摊）、P2-02（余额判据无测试）。
- 生成入口的检查顺序（`closing.py:283-301`）：权限 → 不可变总账 → 月份 → 自然年 → 中国公司 → 本月已结转 → 账簿损益 → 以前月份完整 → 草稿。第一个不通过就报错，后面的不再查，**不会叠加报错**。以前月份的多个原因在一条报错里逐月列出。整个过程都在 savepoint 之外，只读。
- `month_closing_state` 只读、无副作用；12 月的 1901 检查不进入 `_incomplete_previous_months`（`range(1, 12)` 不含 12），次年 1 月不受影响。
- 取消路径（`cancel_month_end_closing`）不受 FD-007 拦截，FD-007 的恢复流程依赖它的「先取消以后月份」检查，这条路径没有测试（P2-05）。
- `PL_EXCLUDED_SUBTYPES` 的权威定义在 `ledger.py:11`，`closing.py` 再导出同一对象。

**供收口交叉比对**
- R14 收口报告中 FD-010 关于 `closing.py` 的两句描述有误（生成器表达式不会遮蔽 `_`；受害的是「Cancel later」那句报错，不是空月取消）。对代码无影响，建议在 R17 收口里更正，免得以后引用。

---

## 盲区自述与把握最低处

- **全部是读码结论**：没跑测试、没做变异。「有判别力」一列来自读断言，加上 R14 当场修与 SB 回执中的变异记录，本片没有复现。
- **把握最低的三处**：
  1. P2-03 的情形 ②（5403 那行被分摊后借贷差一分钱）：上游会补一条舍入分录还是直接报错，我没有把 `process_gl_map` → `make_round_off_gle` 那条路读到底。情形 ① 的机制读码是确定的，但没有实跑。
  2. P2-01 的现实概率：上游哪些单据会让 2221xxx 或 3103 带上账簿，我只确认了 Journal Entry 有 `finance_book` 字段，没有穷举。
  3. FD-012 存量会计期间不补行：这是读 `get_doctypes_for_closing` 只在预填时调用推出来的，没有在站点上造会计期间验证。
- **没往这些方向找**：FD-007 新逻辑的验收逐条（属分片 5）；`engine.py` 中 FD-017／018／019（属分片 3）；不可变总账开启时**其它单据**的冲销对已结转月份的影响（结转入口已拒绝该模式，判为范围外）；Repost Item Valuation 重过账使已结月份被判「结转后有变动」（只在金额真的变了时才会重建 GL，属正当提示，未立项）。
- **拿不准的定级**：P2-01 定「低」而不是「观察」，是因为它违反了 SB 回执自己定下的「每个入口明确报错」约定，而且属于静默错数；但两站都没有账簿，现实概率低。P2-05 定「低」，是因为同一条路径已经出过一次真缺陷却没被测试发现，而 FD-007 之后它成了恢复流程的必经之路。
