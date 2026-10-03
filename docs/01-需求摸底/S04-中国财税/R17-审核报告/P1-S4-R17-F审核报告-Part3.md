# 审核报告·Part3（复核轮）（对象：frappe_china Part3 范围 / 审核标准：R7 开发方案 Part3＋R15 开发方案＋B 需求文档）

**轮次**：P1-S4-R17｜**步骤**：`plannedDev` F（play-audit）复核轮，分片 3｜**执行者**：Claude 子 Agent（Opus 5.5）｜**日期**：2026-10-03
**被审代码**：`frappe_china` HEAD `21faeb9`（工作区干净），对照 R14 审核基线 `40200dc`；中间提交 `e55806e`（F 当场修）、`48e7933`（SB）
**依据**：R7 `C开发方案-Part3.md`（全文）、`-总纲.md`（A9 等，按需读）；B 需求文档 §4.11；R14 `F审核报告.md`（问题表、当场修清单）与 `-Part3.md`（全文）；R14 `SB修复回执.md`（全文）；R15 `C开发方案.md`（全文）与 `C讨论记录.md`（DEC-122～124、LG-154）；R16 `D回执.md`（全文）；`docs/业务规则.md`
**本片复核项**：当场修 FD-005、FD-020、FD-030；SB 修 FD-017、FD-018、FD-019；R15／R16 落地对 Part3 映射的影响（1901、5711010、400103、1606）；延迟项 FD-041 不恶化

## 覆盖自证

**实际查了**：
- `git diff 40200dc 21faeb9`：`accounting/statements/`（`engine.py`、`balance_sheet.py`、`profit_and_loss.py`、`unmapped.py`、`printing.py`、`cash_flow_statement.py`）、`accounting/ledger.py`、`cn_tax/report/` 两个 json、Part3 相关测试（`test_mapping`、`test_profit_and_loss`、`test_unmapped`、`test_statement_dataset`、`test_prepared_report`、`test_balance_sheet`、`test_statement_output`、`test_translations`）与 `zh.csv`，逐行读完。
- 现状全文读：`mapping.py`、`engine.py`、`balance_sheet.py`、`unmapped.py`、`ledger.py`、`profit_and_loss.py`（execute 段）、`closing.py`（常量、`_one_account`、`_incomplete_previous_months`、`month_closing_state`）、`patches/fd004_default_accounts.py`、`tests/test_default_account_postings.py`、`test_closing_voucher.py` 的 FD-030 测试、`test_mapping.py` 覆盖与重复覆盖两组测试。
- 上游读码：`frappe/desk/query_report.py`（`get_report_doc`、`run`、`validate_filters_permissions`）；erpnext `stock_entry.py`、`stock_entry_utils.py`、`stock_reconciliation.py`（validate、`validate_expense_account`、`get_difference_account`）、`subcontracting_receipt.py`、`bom.py`、`stock_entry_type.py` 中 `stock_adjustment_account` 的全部取用点；`depreciation.py` 处置分录、`sales_invoice.py` 固定资产出售分录；`company.js` 过滤、`company.py` `_set_default_account`；`stock_controller.py` `expenses_added_to_stock_*`。
- 只读 SQL（两站）：四个 CN Tax 报表的 `ref_doctype`、`modified`、角色；`GL Entry`／`Company`／`Fiscal Year` 的 DocPerm；演示站 1400／1900／2900／4／5301／5711 组下的科目与类型；HDTH 两个默认科目；2221 组的嵌套。
- 离线推演（容器 `./env/bin/python`，不连站点、不写库）：直接调 `engine.check()`，推演 A～G（见新发现的证据列）。注：离线无站点时 `frappe.utils.flt` 返回 0，推演里把 `engine.flt` 换成 `round` 后再算，不影响判别逻辑。

**跳过及原因**：
- **未跑任何测试、未 migrate、未写站点**（硬约束：主会话正在测试站跑全量回归）。149/149 与变异结果采信 R16 回执，本片未复核。
- 打印模板、现金流量表本身属 Part4；只核了 FD-005 中现金流量表 json 与库里的 `ref_doctype`。
- `closing.py` 的结转生成、FD-007（`_incomplete_previous_months`）属 Part2；`company.py`／patch 的旧值保护属 Part1，只读了与本片映射相关的部分。
- 没有财政部附录原文，1901 的列报位置无法对照填列说明（与 R15 的 LG-154 同一盲区）。

## 已修项复核表

| FD 号 | R14 判定标准 | 定位（文件:行） | 落地 | 生效否 | 原问题消失否 | 自证一致否 | 说明 |
|---|---|---|---|---|---|---|---|
| FD-005 | 现金流量表、漏科目检查 `ref_doctype` 改 `GL Entry`；只有 Accounts User 的会计能打开四张表；补以 Accounts User 身份的测试 | `cn_tax/report/漏科目检查/漏科目检查.json:24`、`小企业现金流量表.json:24`；`tests/test_prepared_report.py:23-47` | ✅ | ✅ | ✅ | 基本一致 | 两站 SQL：四张表都是 `GL Entry`，`modified=2026-10-02 21:00` 已导入；角色都是 Accounts Manager／Accounts User；`GL Entry` 的 Accounts User 有 `report=1`。`run()` 余下一道检查是筛选 Link 的 read 权限（`query_report.py:1158-1187`），Company、Fiscal Year 对 Accounts User 都有 read，成立。测试只调了 `get_report_doc`，没有按 R14 建议「经 `run()` 跑四张表」，但 `get_report_doc:49` 正是原来抛错的那一行，判别力够（P3-05 观察）。浏览器端未验 |
| FD-020 | 四个列头经 `_()`；csv 补 `Balance or Movement`；`zh` 下显示中文 | `statements/unmapped.py:16-23`、`:132`；`zh.csv` 新增「Balance or Movement,余额或发生额」；`tests/test_unmapped.py:48-50` | ✅ | ✅ | ✅ | 一致 | 改成每次调用的 `_columns()`（模块级常量会在 import 时定死语言，改函数是对的）。另三个词条取官方 po：Account→科目（frappe）、Account Number→科目代码、Issue→问题（erpnext），符合 A9「csv 只收官方没有的键」。测试在 `zh` 下逐字断言四个中文列头，R14 SB 变异 M10 失败。R14 P3-06 顺带提的「Currency 列缺 `options`」没改，也没登记（P3-06 观察） |
| FD-030 | `PL_EXCLUDED_SUBTYPES` 成为单一来源，`ledger.py`、`engine.py` 两处 SQL 引用它 | `ledger.py:11`、`:78-83`；`engine.py:12`、`:72-73`、`:89`；`closing.py:11`、`:20`；`tests/test_closing_voucher.py:158-170` | ✅ | ✅ | ✅ | 一致 | 常量移到 `ledger.py`（`closing.py` 依赖 `ledger.py`，反向会成环，理由成立），`closing.py` 只做再导出。两处 SQL 用 `IN %(pl_excluded_subtypes)s` 传元组，与上游 `bank_transaction.py:496` 同写法。两条取数路径都真被调用：`snapshot_movement → gl_sums(exclude_pl_closing=True)`、`profit_and_loss._period_values → allocate_surtax`。测试断言对象同一并扫源码字面量，M11 变异失败。`tests/dataset.py:460` 仍是字面量——那是独立期望值的造数侧，留着合理，但没有在任何地方写明是有意为之 |
| FD-017 | 汇兑收益较大时 `18>=19` 不误报为错误；说明行写清列名 | `engine.py:245-273`（判据在 `:269`）；`balance_sheet.py:125`；`profit_and_loss.py:103-104`；`tests/test_mapping.py:88-108`；`tests/test_statement_dataset.py:56-59` | ✅ | ✅ | ⚠️ 部分 | **不一致** | 列名：两张表四个调用点都带 `column`，✅。≥ 式判据是「涉及的各行**都不为负**才算勾稽不符」，只覆盖了「上级行或其中项本身变成负数」这一种。R14 的原问题是「上级行 ＜ 其中项」在合法业务下出现，而它出现的条件是**上级行里其中项以外的部分为负**，与各行正负无关。推演 F：利息支出 100、汇兑收益 30 → 行 18＝70、行 19＝100，各行非负，仍报「勾稽不符」。测试只用了 R14 推演 D 的极端数（行 18＝-400），测不到这种常见情形。R15 讨论记录又据此断言「FD-017 已把这类 ≥ 式降为提示，不误报」，同样只在净收益超过全部营业外支出时成立 → **P3-01** |
| FD-018 | 红字冲回附加税时明细同步减少，`3>=4+…+10` 不误报 | `engine.py:98-127`；`tests/test_profit_and_loss.py:53-61` | ✅ | ✅ | ✅ | 一致 | 每张凭证取 `5403` 借减贷净额；为正按同凭证税种明细的贷方分摊，为负按借方反向冲减，符号随 `sign`。外层 SQL 排除损益结转子类型，结转凭证里贷 `5403` 的那一行不会进来（子查询不排除，但外层排除，结果正确）。测试：计提 100 后冲回 20 → 80／56／24，且断言说明里没有「勾稽」，旧逻辑下会出「3 < 100」，判别力成立（M4）。未分摊说明带符号，可读 |
| FD-019 | 组科目下没有明细、`exclude` 写错号都报错，不静默出 0 | `engine.py:131-158`、`:174`；`unmapped.py:60-70`；`tests/test_mapping.py:65-86`、`:163-167` | ✅ | ✅ | ✅ | 一致 | `resolve` 同时解析 `numbers` 与 `exclude`，缺号、空组两类收齐一次报出；`_source_value` 改为 `resolved[number]`，不再 `.get(…, ())` 静默吞掉。**连带改动核过**：`resolve` 返回值含 exclude 号，`unmapped._covered_accounts` 与 `test_mapping._covered` 都改为只取 `numbers`，否则 `2221000` 组被当成已覆盖；`test_mapping._claims` 仍用 `resolved.get` 取 exclude，不受影响。2221 下被排除的号在库里确实都嵌在 2221 组内（SQL 查过）。连带影响：漏科目检查本身也走 `resolve`，遇空组或错号时整张检查报错，不再列出其它问题（P3-07 观察） |

**R15／R16 对 Part3 映射的影响**

| 核对点 | 定位 | 结论 | 说明 |
|---|---|---|---|
| `1901` 落哪行 | `mapping.py:68`（第 28 行 `dr 1900`）；库：`1901` 是 `1900` 组下唯一明细 | ✅ 与 SL-011 ③ 一致 | 盘盈时 1901 贷方余额 → 第 28 行 -20.00，测试 `test_default_account_postings.py` 断言 `values[28] == -20`。1901 不在第 9～13 行，`9>=10+…+13` 不再受盘点影响，R14 P3-01 的 ② 消失。列报是否合规见 P3-03 |
| `5711010` 落哪行 | `mapping.py:132`（第 24 行 `dr 5711`） | ✅ 与 SL-011 ⑥ 一致 | 不在任何「其中」子行（25～29）。报废 1000 → 行 24＝1000 有测试。有处置净收益时记 `5711010` 贷方，行 24 减少或为负（P3-01、P3-02） |
| `5301050` 落哪行 | `mapping.py:130`（第 22 行 `cr 5301`） | ✅ 与 SL-011 ④ 一致 | 不在第 23 行（政府补助只取 `5301040`） |
| `400103` | `mapping.py:48` 仍在第 9 行，不在 10～13 | ✅ 注关闭合理（附条件） | 读遍上游 `stock_adjustment_account` 的取用点（盘点、Stock Entry 无费用科目时、委外收货损耗、BOM、Stock Entry Type），现在都指向 1901；`_set_default_account` 只在字段为空时按 `account_type` 回填，本 app 已填。HDTH 无 GL，没有历史余额。条件：有历史余额的公司（只在测试站）余额仍挂存货；没有任何东西阻止用户在单据上手选 400103。属会计手工误用，不立项 |
| `1606` | `mapping.py:63` 第 23 行 | ✅ | 不再是默认处置科目，报废测试断言 1606 无分录 |
| 漏科目检查 | `unmapped.py` | ✅ | 1901 被第 28 行、5711010 被第 24 行覆盖，测试 `assert_no_missing_accounts` 断言 |
| 年末 1901 说明行 | `balance_sheet.py:82-85`；`closing.py:403-407` | ✅ | 只在 `month==12` 的状态里出现；利润表也共用 `_closing_notes`，12 月／年报同样会出这一行。金额是借减贷，盘盈未转出时显示负数（P3-03） |
| FD-041（延迟） | `tests/dataset.py` 未改；`test_statement_dataset.py:162` 的 `bs[20] == -bs[19]` 仍在 | ✅ 未恶化 | `assertChecksPass` 由判 `!=` 改为判「勾稽」，把「勾稽提示」也算失败，比以前更严，没有变松 |

## 开放查漏新发现

| 片内编号 | 严重程度 | 定位 | 问题 | 违背的标准 | 建议修法 | 建议档位 | 待裁决点 | 证据 |
|---|---|---|---|---|---|---|---|---|
| P3-01 | 低 | `engine.py:269`（≥ 式判据）；`mapping.py:144` 的 `18>=19`、`24>=25+…+29`、`3>=…`、`11>=…`、`14>=…` | **FD-017 只修了一半**：≥ 式只在「某一行本身为负」时降为提示，而合法的「上级行 ＜ 其中项」取决于上级行里其中项以外的科目是否为贷方，与行的正负无关。两条仍会出「勾稽不符」的合法情形：① 汇兑收益（`5603220` 贷方）或现金折扣（`5603230` 贷方）小于利息支出、但大于手续费等其余项时，`18 < 19`；② **R15 DEC-123 新开的路径**：资产处置净收益记 `5711010` 贷方，只要它小于其余营业外支出合计，行 24 仍为正，`24 < 25+…+29`。R15 讨论记录「FD-017 已把这类 ≥ 式降为提示，不误报」的说法只在净收益超过全部营业外支出时成立 | 需求 §4.11 第 4 条的反面（报错要真）；R14 FD-017 判定标准「汇兑收益较大时 `18>=19` 不误报为错误」 | 判据改为看「上级行 − Σ其中项」这一残差：残差为负、且上级行里其中项以外的明细中有贷方余额（借方性质行）／借方余额（贷方性质行）的，出提示；否则才是勾稽不符。实现上可在 `evaluate` 时顺带算出每行「其中项以外部分」是否含反向余额，交给 `check`。补推演 E、F 两条测试 | 新Session修 | ≥ 式什么时候算错（须会计）；是否干脆把利润表的 ≥ 式全部降为提示 | 离线推演 F：`18=70, 19=100` → `["M：勾稽不符：第 18 行 70.00 小于其中项第 19 行之和 100.00"]`；推演 E：`24=50, 25=100` → `["M：勾稽不符：第 24 行 50.00 小于其中项第 25+26+27+28+29 行之和 100.00"]`；对照推演 A：`24=-400, 25=100` → 「勾稽提示」。科目：`5603220 财务费用_汇兑差额`、`5603230 财务费用_现金折扣`（`company_defaults.json` 的 `exchange_gain_loss_account`、`default_discount_account`）；上游 `depreciation.py:760-778` 净收益记 `disposal_account` 贷方 |
| P3-02 | 观察 | `company_defaults.json`（`disposal_account=5711010`）× `mapping.py:130`、`:132` | 处置净收益以负数进第 24 行「营业外支出」，第 22 行「营业外收入」不含它。利润总额不受影响，但两行的分类与准则「营业外收入含非流动资产处置净收益」不符。R15 已知并接受（DEC-123 缺点栏），LG-154 待会计确认。本片只确认它在报表上的落点与 R15 描述一致 | 草案规则：处置净收益列营业外收入（见业务规则核） | 若会计要求分列：报表层把 `5711010` 的贷方余额改列第 22 行（`split=neg` 一对拆分），不必改默认科目 | 延迟或不修（随 LG-154） | 会计是否接受净收益列为营业外支出负数 | `depreciation.py:760-778`；R15 讨论记录 DEC-123 |
| P3-03 | 观察 | `mapping.py:68`（第 28 行 `dr 1900`）；`balance_sheet.py:85` | 盘盈未转出时 1901 是贷方余额，在资产栏第 28 行列负数；年末说明行写「尚有余额 -20.00」。科目表另有 `2901 待处理财产损溢_非流动负债`（Liability，在 `2900` 组下 → 第 45 行），说明 zelin 科目表的设计是借贷两向分挂两个科目，而 ERPNext 只有一个 `stock_adjustment_account`。另外 1901 承接的是存货差额（流动性质），却列在非流动资产 | R15 LG-154（「1901 年中挂在其他非流动资产是否合规」未对照填列说明） | 随 LG-154 一并问会计：① 待处理的存货盘盈盘亏列哪一行；② 贷方余额是否改列负债栏（如第 28 行 `split=pos`、第 45 行加 `cr 1901 split=neg`）。说明行金额可改为「借方／贷方 X」而不是带符号 | 延迟或不修（随 LG-154） | 列报位置（须会计） | 库：`1901` 在 `1900` 下、`2901` 在 `2900` 下；`test_default_account_postings.py` 断言 `values[28] == -20` |
| P3-04 | 观察 | `mapping.py:48`（第 9 行含 `4101`、`410103`、`410199`、`400199`）；R14 P3-01 推演 C | R14 P3-01 有两半：默认科目（并入 FD-004、已由 R15 改）与「结转类科目留在第 9 行会误报 `9>=…`」。后一半在 R14 合并成 FD-004 时成了待裁决点「结转类科目是否留在第 9 行」，R15 方案与 R16 都没提，也没登记延迟。现状：`410199` 只在第 9 行、不在任何子行，它的贷方超过 `4101` 借方时第 9 行仍非负，仍出「勾稽不符」；`400199` 同时在第 9、11 行，贷方大时第 11 行为负，降为提示。实际触发面小：v16 公司没有字段指向 `410199`（HDTH 的 `expenses_added_to_stock_account` 为空），只会来自手工凭证 | R14 FD-004 待裁决点未闭环 | 在 S4 收口时登记为 LG（或明确判「不修」），写清触发条件 | 延迟或不修 | 是否登记 | `git diff 40200dc 21faeb9 -- mapping.py` 为空；R15 方案 §二 只替换了默认科目两行与 400103 注 |
| P3-05 | 观察 | `tests/test_prepared_report.py:23-47` | FD-005 的测试只调 `get_report_doc`，没有按 R14 建议经 `run()` 执行四张表。本片读码确认 `run()` 余下的权限检查只有筛选 Link 的 read（Company、Fiscal Year 对 Accounts User 都有），报表代码里取数都走 `frappe.db`／`get_all`，不查权限，所以目前结论成立；但以后报表代码里一旦用 `get_list` 或 `get_doc` 读别的 DocType，这条测试测不到 | R14 FD-005 建议「补一条以 Accounts User 身份经 `run()` 跑四张表的测试」 | 在同一测试里以 Accounts User 调一次 `run(name, filters)`（用已有测试公司） | 延迟或不修 | — | `query_report.py:43-53`、`:287-289`、`:1158-1187`；两站 DocPerm |
| P3-06 | 观察 | `unmapped.py:21` | `balance_or_movement` 是 Currency 列，没有 `options`，行里也没有 `currency`。R14 P3-06 顺带提过，FD-020 只修了列头，这一处没修也没登记。前端会按系统默认币种显示，单币种公司下看不出差别 | R7 Part3 TS-012「Currency 列统一 `options = "currency"`」（TS-014 「各字段同 TS-012」） | 加 `"options": "currency"`，每行带公司币种 | 延迟或不修 | — | 对照 `balance_sheet.py:21-26` |
| P3-07 | 观察 | `unmapped.py:62`（`_covered_accounts → resolve`） | FD-019 之后，组科目被删空或映射里有错号时，漏科目检查整张报错，而不是把问题列出来。符合 §4.11 第 4 条「不静默」，报错里也列出了号；只是这张本来用来查映射问题的表，在映射出问题时自己先打不开 | — | 可接受。如要改：漏科目检查里捕获 `resolve` 的错误，把缺号、空组作为结果行列出 | 延迟或不修 | — | `engine.py:149-157` |

## 业务规则合规核表

| 规则条款 | 本片是否涉及 | 结论 | 备注 |
|---|---|---|---|
| BR-001 执行《小企业会计准则》 | 涉及（1901、5711010 的列报） | 合规（未经专家确认） | 映射未改，新默认科目落在既有行；列报细节见 P3-02、P3-03 |
| BR-002 月报、年报 | 间接涉及 | 合规（未经专家确认） | 年末 1901 提示在 12 月月报与年报都出现 |
| BR-006 资产总计 ＝ 负债和所有者权益总计 | 涉及 | 合规（未经专家确认） | 盘盈、转出、盘亏、报废四步后资产负债表平衡，测试断言差额为 0。本轮改动没有动平衡校验 |
| BR-003／004／005／007 | FD-018 涉及附加税的列报 | 合规（未经专家确认） | 只改利润表明细行的分摊，不重算税额，不碰结转 |
| R14 草案：存货盘盈盘亏应进损益（经待处理财产损溢转营业外收支） | 涉及 | **草案·待领域专家确认**；现状满足 | 盘点差额先挂 1901，会计手工转 `5301050`／`5711` 下科目后进第 22／24 行；年末未处理有提示 |
| 草案：待处理财产损溢应在年末结账前处理完毕，年末应无余额 | 涉及（`balance_sheet.py:82-85`） | **草案·待领域专家确认**；现状满足 | 来源是准则 1901 科目说明，R15 引用；本片未见原文 |
| 草案：非流动资产处置净收益列营业外收入、净损失列营业外支出 | 涉及（P3-02） | **草案·待领域专家确认**；现状**不满足**（净收益列为营业外支出的负数） | R15 DEC-123 已知并接受，LG-154 |
| 草案（FD-017）：≥ 式（「其中」项）遇到以「-」号填列的行只出提示，不判错误 | 涉及 | **草案·待领域专家确认**；且现判据覆盖不全（P3-01） | AI 推断。原文第 19 行「收入以“-”号填列」支持利润表一侧；资产负债表 `9>=10+…+13` 套用同一规则没有依据（SB 回执自己也写了） |
| 草案（FD-018）：附加税红字冲回按凭证借减贷净额冲减明细 | 涉及 | **草案·待领域专家确认**；与第 3 行同口径，内部一致 | — |
| 草案：待处理财产损溢（存货差额）列报在其他非流动资产 | 涉及（P3-03） | **草案·待领域专家确认** | LG-154 |

## 交接摘要

- **本片依赖别片的**：
  - Part2：`closing.PENDING_LOSS_ISSUE`、`month_closing_state` 的 12 月 1901 检查；`balance_sheet.py:12` 还导入了 `closing._money`、`closing._one_account` 两个私有函数，Part2 改名或改签名会直接打坏资产负债表。`_one_account(company, "1901")` 找不到恰好一个明细就抛错，12 月的资产负债表、利润表都会跟着打不开（与 3103 同一做法，符合不静默）。
  - Part1：`company_defaults.json` 的 1901／5711010 与 `fd004_default_accounts` patch（本片只核了落点，没核 patch 的旧值保护）。
  - Part4：FD-005 的另一半（现金流量表 json）本片已顺带核过库里的值，现金流量表执行路径与打印请 Part4 自核。
- **本片暴露给别片的**：
  - `engine.check()` 新增可选参数 `column`；全部勾稽说明改为中文句式（「勾稽不符」「勾稽提示」）。打印模板直接输出 `message`，S6 译名若引用旧的 `!=` 句式会受影响（现在没有）。
  - `engine.resolve()` 现在也解析 `exclude`，并对空组报错；任何新的调用方若把返回值整体当覆盖集合，会把被排除的明细误算为已覆盖。
  - `ledger.PL_EXCLUDED_SUBTYPES` 是单一来源，`closing` 只再导出（`closing.py` 里这一导入在本模块不被使用，靠 `test_pl_excluded_subtypes_is_the_single_source` 的 `assertIs` 防止被当作未用导入删掉）。
  - 给收口：P3-01 与 R15 讨论记录 DEC-123 缺点栏里那句「FD-017 已把这类 ≥ 式降为提示，不误报」互相矛盾，收口时须二选一更正。P3-04 是 R14 FD-004 遗留的待裁决点，须决定登记还是不修。

## 盲区自述与把握最低处

- **没往这些方向找**：没核 Part1 patch 的旧值保护与缺科目分支；没核 FD-007；没看多币种、会计维度、账簿；没逐张 ERPNext 单据实跑，`400103` 不再有分录这个结论来自读码（`stock_adjustment_account` 全部取用点）＋演示站 0 GL。
- **把握最低的**：
  - P3-01 的修法：我给的「残差含反向余额才提示」只是一种判据，会计可能更愿意把利润表的 ≥ 式统统降为提示。是不是问题我有把握（推演 E／F 的数在会计上都合法），怎么判须会计定。
  - P3-03：1901 在小企业资产负债表上列哪一行、贷方余额怎么列，我没有财政部附录原文。
- **验证门**：本片一项都没有实跑。离线推演把 `flt` 换成了 `round`，推演的是 `check()` 的判别逻辑，不是整张报表。
- **需主会话实跑验证的点**：
  1. 推演 F 上站：一张凭证借 `5603210` 100、另一张贷 `5603220` 30 → 利润表本月说明行是否出「本月金额：勾稽不符：第 18 行 70.00 小于其中项第 19 行之和 100.00」。
  2. 推演 E 上站：一项资产以高于净值 50 出售（或手工贷 `5711010` 50），同月借 `5711080` 100 → 是否出第 24 行「勾稽不符」。
  3. 以 Accounts User 身份经 `run()`（或浏览器）打开四张表各一次。
