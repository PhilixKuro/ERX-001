# 审核报告·Part3（复核轮）（对象：frappe_china Part3 范围 / 审核标准：R7 开发方案 Part3＋B 需求文档 §4.8、§4.9、§4.11＋R18 F 审核报告）

**轮次**：P1-S4-R19｜**步骤**：`plannedDev` F（play-audit）复核轮，分片 3｜**执行者**：Claude 子 Agent（Opus 5.5）｜**日期**：2026-10-04
**被审代码**：`frappe_china` HEAD `6cb779c`（工作区干净），对照 R18 审核基线 `cd5d565`；中间提交 `49e76c4`（R18 F 当场修，本片只涉及 `tests/test_mapping.py`）、`6cb779c`（R18 SB，FD-085）
**依据**：R7 `C开发方案-Part3.md`（全文）；B 需求文档 §4.8、§4.9、§4.11；`docs/业务规则.md`（全文）；R18 `F审核报告.md`（FD-084、FD-085 行、当场修清单与复核、状态节）、`-Part3.md`（全文）；R18 `SB修复回执.md`（全文）
**本片复核项**：FD-084（R18 当场修，`test_mapping.py` 子行包含检查）、FD-085（R18 SB，资产负债表年初差额标红）；开放查漏（修出的新问题、方案外夹带）

## 覆盖自证

**实际查了**：
- `git diff cd5d565..6cb779c` 中本片的四个文件逐行读完：`statements/balance_sheet.py`、`tests/test_balance_sheet.py`、`tests/test_mapping.py`、`translations/zh.csv`。`git show --stat` 确认 `49e76c4` 只动了 `README.md` 与 `test_mapping.py`，`6cb779c` 只动了上面除 `test_mapping.py` 外的三个文件；`README.md` 的改动属 FD-083／088（Part2），本片没读内容。
- 现状全文读：`engine.py`、`mapping.py`、`balance_sheet.py`、`profit_and_loss.py`、`printing.py`、`templates/statements/balance_sheet.html`、`tests/test_mapping.py`、`tests/test_balance_sheet.py`；`tests/test_profit_and_loss.py` 前 75 行（分摊用例）；`ledger.gl_sums`（核年初快照口径）；`小企业资产负债表` 的 `.js`（核前端无自定义 summary 消费）。
- 全仓 grep：`report_summary`、`Opening Difference`、`_render_notes_html`、`SURTAX_ACCOUNT_LINES`／`allocate_surtax` 的全部出现处；官方 `frappe`、`erpnext` 的 `locale/zh.po` 与 `main.pot` 里是否已有 `Opening Difference`（均无，`Difference` 只在 erpnext `main.pot:17197`）；测试里有没有「每个编号行必须有取数／公式／空行原因」之类的断言（无）。
- 只读 SQL（演示站 `erx.localhost`，公司「华东弹簧有限公司」）：`1400`、`1490`、`1710`、`4` 成本类、`5301`、`5601`～`5603`、`5711` 下科目的号、层级与 lft/rgt，用来推演 FD-084 测试对各种变异的反应。
- 离线读码推演：FD-084 新测试对 6 种映射写错形态的判定；FD-085 新用例的两次快照（年初、期末）各自的数值；FD-085 修法对既有 `test_imbalance_is_reported_in_red`、`test_report_returns_two_column_layout` 的影响；6 组变异下新用例的反应。
- 文件换行：`git ls-files --eol` 看 `zh.csv`、`balance_sheet.py` 都是 `i/lf`，与仓库其他文件相同。

**跳过及原因**：
- **没跑测试、没做变异、没 migrate、没写站点**（本片硬约束）。R18 当场修复核的「`test_mapping` 12/12」「变异 B 修后失败 1 条」和 SB 回执的「157/157」「变异回退后新用例失败」都没法复核，只靠读码判断测试能不能区分修前修后。需要实跑的都列在文末清单。
- `README.md` 的改动（FD-083、FD-088）、`closing.py`、`cash_flow_statement.py`、`docker/` 下的改动（FD-080～082）不在本片。
- PDF 与 XLSX 的版式归 Part4，已登记为 FD-092（延迟）。本片只核了 summary 变成 4 项后这两条路径会不会坏。

## 已修项复核表

| R18 项 | 定位（文件:行） | 落地 | 生效 | 原问题消失 | 说明 |
|---|---|---|---|---|---|
| FD-084 「其中」子行映射写错只剩提示，没有测试兜住 | `tests/test_mapping.py:163-197`（`_assert_sub_rows_within_parent` 与两条用例） | ✅ | ✅（读码；运行结果采信 R18 复核记录） | ✅ 对「取了上级行之外的科目」这一形态；⚠ 另有两种相邻形态没管住（P3-01、P3-02） | **判据**：对每条 ≥ 式，把右边各子行每个 `Src` 用 `resolve` 展开成明细科目，扣掉 `exclude`，记下取数方向（`sign`），再要求这个「科目→方向」集合包含在左边上级行的同类集合里（`:189` `signs <= parent.get(account, set())`）。**逐项核了问到的几种情况**：① **范围外的科目**：`5602040`（lft 443）不在 `5301`（340-361）里，`1490`（53-54）不在 `1400`（31-52）里，两种都会被抓到。② **方向相反**：比如第 19 行改成 `cr 5603210`，上级行第 18 行是 `dr 5603`，方向集合 `{cr}` 不包含于 `{dr}`，也能抓到。③ **exclude**：两边都按 `resolve` 结果扣掉，口径与 `engine._source_value:174-177` 一致，不会把上级行用 exclude 剔掉的科目当成「上级行取到了」。现在 ≥ 式涉及的行都没有用 exclude（只有第 36 行用，它不在 ≥ 式里），这条分支现在不起作用，但写法是对的。④ **跳过 alloc**：利润表第 4～10 行（alloc）的 `Src.numbers` 在 `evaluate:225` 里**根本不参与取数**，值来自 `allocate_surtax`。分摊金额由 `allocated_total = min(amount_5403, mapped_total)`（`engine.py:119`）限住，不会超出 `5403`，所以「取了上级行之外的科目」这种错在 alloc 行上不可能发生，跳过是对的、没放过这一类错误。如果有人把某个 alloc 行的 `alloc` 标记删掉，它变成普通取数，`2221xxx` 不在 `5403` 里，会被抓到。alloc 行另有一种「分错行」的错误，这条测试管不到，见 P3-02。⑤ **静态基准是不是自证**：被比较的两边（子行和上级行）都取自被测常量。这是包含关系检查本身的性质：它只管两行之间的关系，不管每一行本身对不对。≥ 式本身是从 `BS_CHECKS`／`PL_CHECKS`（被测常量）取的，没有从 `statutory_layout` 的独立基准取。但同文件 `test_check_formulas_match_original_text:50-54` 断言两者集合相等，删掉或改写一条 ≥ 式会在那里失败，所以不构成自证漏洞（只是和 `_sub_rows` 注释里写的「从独立基准取」不是一个写法，不立项）。两边一起改错的情况，比如把 `1490` 同时加到第 9 行和第 12 行：本测试会放过，但 `test_balance_sheet_accounts_are_not_claimed_twice` 会抓到（第 9 行和第 14 行都按「all」取 `1490`），整体上不漏。**覆盖面**：资产负债表 1 条 ≥ 式（9≥10…13），利润表 6 条（3、11、14、18、22、24）。其中 `3>=4+…+10` 的子行全是 alloc 或 empty_reason，对这条式子检查是空跑。现在的映射按演示站科目树逐条成立，与 R18 片 3 的结论一致。**测试能区分修前修后**：R18 复核记录写着变异 B 修前全过、修后失败 1 条，与我的推演一致（失败的应是 `test_profit_and_loss_sub_rows_within_parent`） |
| FD-085 年初列不平时不醒目 | `balance_sheet.py:92-102`（`_render_notes_html`）、`:133-145`（年初差额与 summary）、`:149`（调用）；`translations/zh.csv:151`；`tests/test_balance_sheet.py:87-111` | ✅ | ✅ | ✅（读码推演） | **三层**：① 落地：`opening_difference = flt(opening[30] − opening[53], 2)`（`:134`），出现差额时在说明块里插一行「年初余额：资产总计与负债和所有者权益总计不等，差额 X」（`:95-96`），说明块用红色（`:101`），前两项 summary 标红（`:136、139-140`），并追加第四项 `_("Opening Difference")`（`:144-145`）。② 生效：`execute:149` 把年初差额传进 `_render_notes_html`。`_render_notes_html` 全仓只有这一个调用方（利润表用自己的 `_render_notes`）。③ 原问题消失：推演新用例。年初快照按 `gl_sums` 的 `fy_opening_of` 口径取「`posting_date < 2025-01-01` 或 `is_opening='Yes'` 且属 2025 年」，结果是 `1002` +1000、`9999` −1000（`9999` 不映射），第 30 行 1000、第 53 行 0，差额 1000。期末快照把 setUpClass 那笔 1000 也算进来，`1002` 2000、`3001` 2000，平衡。断言的各项都成立；改前这一场景下说明块是 `text-muted`、summary 全是 Green，用例会失败，与 SB 的变异记录一致。**中文硬写、没经 `_()` 算不算问题**：不算。同文件的期末差额那句（`:98`）、`check()` 产出的勾稽说明、`_closing_notes` 的各句、利润表与现金流量表的说明行，都是中文字面量。R13 E 确认报告:175 已经裁过：方案伪码本身就把说明行写成中文，按伪码判通过。新那句和期末那句是同一写法、同一格式（`:.2f`，不带千分位）。需要走 `_()` 的 summary 标签（方案 Part3:282 只规定第三项用英文源词 `_("Difference")`）照做了：`Opening Difference` 走 `_()` 加 csv，官方 `zh.po`／`main.pot` 里都没有这个键，符合总纲 A9「csv 只收官方没有的键」。**消费方**：`printing.py:73` 用 `columns, data, message, *_rest` 解包，不读 summary，PDF 不受 4 项影响；PDF 模板只输出 `{{ message }}`，红块在 PDF 里仍是 `#555` 灰色，这是已登记的 FD-092（延迟），不是新问题；XLSX 走框架导出，不带 summary 和 message（同属 FD-092）；`.js` 只有 formatter 和打印按钮，不读 summary；全仓没有别处按「summary 恰好 3 项」取数。**旧用例不受影响**：`test_imbalance_is_reported_in_red` 把第 1 行打成空取数，但年初快照没有数据（setUpClass 那笔在 1 月 15 日、不是开账凭证），年初平衡，summary 仍是 3 项、全 Red，断言照过；`test_report_returns_two_column_layout` 年初是 0＝0，summary 3 项、全 Green，照过。**测试判别力**：见文末 N1～N6，6 组针对性变异都会让某条断言失败，没有只改一半还能通过的写法。**隔离**：新用例用 savepoint 加 `addCleanup` 回滚。如果回滚失效，按字母序排在后面的 `test_report_returns_two_column_layout` 会因为年初不平而失败，相当于自带一道检查 |

**观察（不立项）**：
- 只有年初不平时，summary 前两项（数值是**期末**合计，两者相等）也标红。会计可能以为期末不平。不过第三项「差额 0」是绿色、第四项「年初差额」是红色，读下来能分清。这是 SB 按 R18 建议「summary 标红」做的，回执「拿不准处」已写可以去掉第四项，但没讨论前两项要不要红。交收口看是否需要用户确认。
- 年初或期末不平时，说明块里同时有醒目的「…不等，差额 X」和 `check()` 产出的「年初余额：勾稽不符：第 53 行为 …，按第 30 行计算应为 …」，同一件事说了两遍。期末那边 R7 起就是这样，新加的年初这边照旧，不立项。

## 开放查漏新发现

| 片内编号 | 严重程度 | 定位 | 问题 | 违背的标准 | 建议修法 | 建议档位 | 待裁决点 | 证据 |
|---|---|---|---|---|---|---|---|---|
| P3-01 | 低 | `engine.py:215-229`（编号行没有 `src`、`formula`、`empty_reason` 时 `values[no] = flt(sum([]), 2) = 0`）；`tests/test_mapping.py:128-197`（三组静态测试都不看子行有没有取数） | **「其中」子行的取数被删光后会静默显示 0，运行时和测试都不报。** 引擎对「既没有取数，也没有公式和空行原因」的编号行不报错，直接给 0。主行如果这样会被覆盖测试抓到（它的科目变成没人覆盖）。子行不会：覆盖测试（`:203-206`）和重复覆盖测试（`:134`）都按设计排除子行；新的子行包含检查里，空集合包含于任何集合，照过。运行时 ≥ 式是 `0 ≤ 上级行`，也成立，连提示都没有。例如把第 13 行「周转材料」改成 `_line(13, "周转材料", indent=1)`，报表这一行恒为 0.00，全量测试推演全过。子行只删掉一部分科目（如第 10 行漏掉 `1404`）也同样静默，但这种情况没有逐行的独立基准就无法静态发现，不在本条建议范围内。现在的映射里所有编号行都有取数、公式或空行原因之一，**这是潜在缺口，不是现存错误**；也不是 R18 引入的，R7 起就这样。之所以现在提出：FD-084 补的是「子行写错」这一类的静态守卫，它的近邻「子行写空」仍然没管住 | 需求 §4.11 第 4 条（命中零个科目时报错，不静默出 0）；R7 Part3 SL-006 验收第 8 条 | 二选一：① `evaluate` 或 `resolve` 里对编号行三者全无时 `frappe.throw`，与「命中零个科目报错」同口径；② 在 `test_mapping.py` 加一条静态断言，每个编号行恰好有取数、公式、空行原因之一。都不涉及现有映射常量 | 本Session修 | 补在引擎（运行时也守住）还是只补测试 | 读码 `engine.py:220-229`；变异 M4（见清单，预期全量照过） |
| P3-02 | 观察 | `engine.py:42-55`（`SURTAX_ACCOUNT_LINES`）与 `mapping.py:112-118`（第 4～10 行 alloc 的 `Src.numbers`）；`tests/test_profit_and_loss.py:42-60`（只验了 `2221040→6`、`2221110→10`） | **税金及附加明细的「科目→行」映射有两份，没有测试核对它们一致。** 取数实际只用 `SURTAX_ACCOUNT_LINES`；`mapping.py` 里 alloc 行的科目号只在 `resolve` 里检查是否存在。两份现在逐条一致（12 个科目都对得上）。如果以后只改了 `SURTAX_ACCOUNT_LINES` 里某个科目的行号（如 `2221060` 改成 8），金额会在第 4～10 行之间挪动，合计不变，第 3 行的 ≥ 式照样成立，不报任何东西；12 个科目里有 10 个没有测试锁定行号。只改 `mapping.py` 不改字典时，金额会进入「未能按税种明细分摊」的说明，看得见，不算静默。R18 P3-01 的建议里写过「第 3 行另由 `SURTAX_ACCOUNT_LINES` 与 4～10 行的 2221 号核对」，收口合成 FD-084 时这一半被省掉了，当场修也没做 | R7 Part3 TS-013 分摊注（行 4–10 的来源科目）；R18 P3-01 建议修法后半句 | 在 `test_mapping.py` 加一条断言：`{号: 行 for 第 4～10 行的 alloc Src 的每个号}` 等于 `SURTAX_ACCOUNT_LINES`。也可以让引擎从 `PL_LINES` 生成这个字典，去掉一份重复 | 延迟或不修 | 是否随 P3-01 一起顺手补（成本是一条断言） | 读码；变异 M5（预期全量照过） |

**本片改动没有方案外夹带**：`6cb779c` 的三个文件 +45／−12，全是 FD-085 的内容。`_render_notes_html` 的新参数有默认值 0，只有一个调用方。`49e76c4` 在本片的部分只有两条测试和一个辅助方法，生产代码没动。summary 第四项超出了 R7 Part3:277-282 写的「三项」，但这是 R18 FD-085 待裁决点给的选项（「可加第四项」），用户裁决「按建议来」，SB 回执里也写明了，按已裁决的偏离处理，不算夹带。R7 方案原文没随之更新，属于历史产物，不改。

## 业务规则合规核表

| 规则条款 | 本片是否涉及 | 结论 | 备注 |
|---|---|---|---|
| BR-006 资产总计 ＝ 负债和所有者权益总计 | 涉及（FD-085） | 合规（未经专家确认） | 期末、年初两列不等时都用红色说明报出、summary 标红；R14 Part3 写的「两列都校验，不等时出红色说明并标红」现在对年初一列也成立了。PDF 不分颜色（FD-092，延迟），这点状态没变 |
| BR-001 执行《小企业会计准则》 | 间接涉及（映射测试） | 合规（未经专家确认） | 映射常量没改；FD-084 只加静态测试。标「推定」的映射（第 10～13、12 行等）仍待会计确认，状态没变 |
| BR-002 三表＋附注、月报年报 | 间接涉及 | 合规（未经专家确认） | 利润表没改；资产负债表月报照常 |
| BR-003／004／005／007 | 不涉及 | — | 本片本轮的改动不涉及税率、结转与价税分离 |
| 草案（R17 FD-047，R18 已登记送审）：≥ 式不成立一律只出提示，= 式仍判不符 | 涉及（FD-084 是它的补偿措施） | **草案·待领域专家确认**；代码没变 | FD-084 补上了「子行取了上级行之外的科目」的静态守卫；「子行写空」与「税种分错行」仍然只靠人眼（P3-01、P3-02） |
| 本轮新增或变更的规则 | — | 无 | 年初列也标红是 BR-006 的呈现方式，不是新的领域不变量，不触发送审 |

## 交接摘要

- **本片依赖别片的**：
  - Part2（`ledger.gl_sums`）：年初快照的 `fy_opening_of` 口径（上年末余额加本年开账凭证）。FD-085 的年初差额完全依赖它；Part2 如果改这个口径，年初差额会跟着变，但新用例会把它暴露出来。
  - Part2（`closing.py`）：`_closing_notes` 依赖的四个公开名，本轮没变（R18 片 3 已核）。
  - Part4（打印与导出）：`printing.py:73` 不读 summary，靠 `*_rest` 吞掉多出来的返回值；FD-092 的 PDF 颜色问题由 Part4 跟。
- **本片暴露给别片的**：
  - `balance_sheet.execute` 的 `report_summary` 从固定 3 项变成 **3 项或 4 项**（只在年初不平时多一项，`label` 为 `_("Opening Difference")`，`indicator` 为 `Red`）；前两项的 `indicator` 现在由期末、年初两列的差额共同决定。S6 译名、S7 演示脚本或以后的自检如果按下标取 summary，需要知道这一点。
  - 说明块在年初不平时也是 `text-danger`，第一条（或期末也不平时的第二条）是「年初余额：资产总计与负债和所有者权益总计不等，差额 X」（中文硬写、不经 `_()`）。
  - 新增 csv 源词 `Opening Difference` → `年初差额`。按 SB 回执，演示站要 `clear-cache` 后才显示中文，在那之前，年初不平时 summary 第四项显示英文源词。
- **给收口**：
  - P3-01、P3-02 与 FD-084 是同一组（「其中」子行的静态守卫），建议一起裁决。
  - 「只有年初不平时，summary 前两项也标红」这一点没有经过用户确认（见已修项复核表下的观察）。

## 建议主会话做的实跑清单

| # | 类型 | 植入点／场景 | 预期结果 |
|---|---|---|---|
| R1 | 回归 | `bench --site test.localhost run-tests --app frappe_china` | 157/157；与 SB 回执一致 |
| M1 | 变异（FD-084 判别力，复跑 R18 变异 B） | `mapping.py:131` 第 23 行改取 `5602040` | `test_profit_and_loss_sub_rows_within_parent` 失败 |
| M2 | 变异（范围外科目，资产负债表侧） | `mapping.py:51` 第 12 行取数加 `"1490"` | **只有** `test_balance_sheet_sub_rows_within_parent` 失败；`test_balance_sheet_accounts_are_not_claimed_twice` 照过（子行被排除）。用来证明新测试补的是旧测试管不到的部分 |
| M3 | 变异（方向） | `mapping.py:127` 第 19 行 `"dr"` 改成 `"cr"` | `test_profit_and_loss_sub_rows_within_parent` 失败（方向集合不包含） |
| M3b | 变异（alloc 跳过不放过真错） | `mapping.py:114` 第 6 行去掉 `alloc=True` | `test_profit_and_loss_sub_rows_within_parent` 失败（`2221040` 不在 `5403` 里）；分摊用例也可能失败 |
| M4 | 变异（证明 P3-01） | `mapping.py:52` 第 13 行改成 `_line(13, "周转材料", indent=1)` | **预期全量照过**；如果有测试失败，P3-01 降为观察或撤销 |
| M5 | 变异（证明 P3-02） | `engine.py:45` `"2221060": 7` 改成 `8` | **预期全量照过**；如果有测试失败，P3-02 撤销 |
| N1 | 变异（FD-085） | `balance_sheet.py:101` 类名只看 `difference` | `test_opening_imbalance_is_reported_in_red` 在 `text-danger` 断言处失败 |
| N2 | 变异 | `balance_sheet.py:134` 年初差额改用 `close` | 同一用例失败（没有年初那句，summary 只有 3 项） |
| N3 | 变异 | `balance_sheet.py:136` `indicator` 只看 `difference` | 同一用例在 indicator 列表断言处失败 |
| N4 | 变异 | `balance_sheet.py:141` 第三项 indicator 改用合并判据 | 同一用例失败（第三项变成 Red） |
| N5 | 变异 | `balance_sheet.py:134` 改成 `opening[53] − opening[30]` | 同一用例失败（差额 -1000.00） |
| N6 | 变异 | `balance_sheet.py:135` 阈值改成 `>= 0` | `test_report_returns_two_column_layout` 失败（年初 0＝0 也会标红） |
| T1 | 探针 | 测试站按新用例数据出 1 月资产负债表的 PDF（`render_statement_html`） | 能正常渲染，不因 summary 多一项而出错；说明块为灰字（FD-092 现状） |

## 盲区自述与把握最低处

- **没往这些方向找**：没核 FD-085 在浏览器里的实际渲染（`report_summary` 4 项的布局、红色说明块在 `query_report.js` 里的样式），只是从生成的 HTML class 和 summary 结构推出来的；没核演示站 `clear-cache` 前后的显示差异（SB 自己说过演示站没清缓存，这会改动站点状态，不在本片权限内）；没看多币种、多账簿下的年初快照。
- **把握最低的**：
  - P3-01 的定级（低还是观察）：现在的映射没有问题，缺口只在以后有人改映射时出现。定为低，是因为它直接违背 §4.11 第 4 条的字面要求（命中零个科目时报错），而且补起来成本很低；如果认为「子行写空」属于人工改映射时自然会发现的错误，可以改判观察。
  - P3-02 是否值得单独立项：只在维护 `SURTAX_ACCOUNT_LINES` 时出问题；也可以并进 P3-01 一起处理，或不立项。
  - FD-084 的「生效」一层：两条用例以 `test_` 开头、放在测试类里，会被收集运行。「12/12」和「变异 B 修后失败 1 条」采信的是 R18 复核记录，本片没跑。
- **验证门**：本片一项都没有实跑。FD-085 的数值推演是按 `gl_sums` 的 SQL 条件手算的，不是整张报表实际算出来的。
