# 审核报告·Part2（对象：frappe_china Part2 范围 / 审核标准：B 需求文档 + R7 开发方案 Part2）

**轮次**：P1-S4-R14｜**步骤**：`plannedDev` F（play-audit，开放式查漏）·第 2 片｜**日期**：2026-10-02｜**审核者**：Claude（Opus 5.5，独立第三方）
**被审代码**：`frappe-bench/apps/frappe_china` HEAD `40200dc`（Part2 相关文件工作区与 HEAD 无差异，`git diff --stat HEAD` 为空）
**问题编号**：片内行号 `P2-01…`；收口报告转为 `FD-` 前缀。

---

## 覆盖自证

**读全了的依据**
- 审核纪律：`F-codeAudit-plannedDev-audit.md`、`bricks/audit.md`、`bricks/sharding.md`。
- 意图层：B 需求文档 §4.7（全）、§4.14、§4.15、§4.17、§八（AC-007/008 及整表）、§十 遗留问题表。B 讨论记录 DEC-099 段（第 209–213 行）。
- 要求层：总纲全文（§二 A10、§五 偏离 1/5/6、§六 接口契约、§七 HT-004/012、§十）；Part2 全文（SL-005 验收 13 条、TS-009、TS-010）；C 讨论记录议题 ⑤（DEC-118/119）；R12 SB 讨论记录（DEC-121、LG-153）。
- 规则与守则：`docs/业务规则.md` BR-001…007；`docs/开发守则.md`「断言机制可用前两侧都查」「判据须能区分」「静默失败」「探针三条纪律」及 §跨 Phase 接口契约表。
- 历史参考（只看查过什么，不采信结论）：R8 D 回执 Part2；R9/R12/R13 E 确认报告中与 Part2 相关的行；R9/R10/R11/R12 SB 回执中 IT-011/016/017/024/031 相关行。

**读过的代码**
- 全读：`accounting/closing.py`（366 行）、`accounting/ledger.py`（125 行）、`cn_tax/doctype/month_end_closing_voucher/` 下 `.py`／`.json`／`_list.js`、子表 `.json`、`fixtures/custom_field.json` 中城建税字段、`hooks.py`、`tests/test_closing.py`、`tests/test_closing_voucher.py` 的断言部分。
- 读了消费方：`statements/balance_sheet.py:55-80`（`_closing_notes`）、`statements/engine.py:60-80`、`statements/mapping.py:36,103`、各处 `gl_sums` 调用。
- 上游读码：`erpnext/accounts/general_ledger.py`（`make_gl_entries`、`process_gl_map`、`save_entries`、`make_entry`、`make_reverse_gl_entries`、`check_freezing_date`、`validate_accounting_period`、`validate_against_pcv`）；`controllers/accounts_controller.py`（`get_gl_dict`、`get_voucher_subtype`）；`period_closing_voucher.py`（冻结与不可变总账的处理）；`accounting_period.py`；`erpnext/hooks.py` 的 `period_closing_doctypes`；`budget_controller.py:268-283`；`financial_statements.py:590-632`；`gl_entry.py`（成本中心与维度校验）；`accounts/utils.py` `get_fiscal_years`；`frappe/app.py:455-468`、`auth.py:28-29`、`frappe/__init__.py` `whitelist`、`model/naming.py` `getseries`、`base_document.py` `RESERVED_KEYWORDS`。

**站点只读查询**（两站，SQL 文件经容器执行，临时目录 `frappe-bench/tmp_r14_p2/` 已删）
- `Accounts Settings`：`enable_immutable_ledger=0`、`delete_linked_ledger_entries=0`、`use_legacy_budget_controller=0`（两站同）。
- `System Settings.rounding_method = Commercial Rounding`（两站同）。
- Finance Book／Accounting Dimension／Accounting Period／Budget／Cost Center Allocation 均为 0 行（两站同）。
- 测试站：无 Company 行、无 MECV、FY 2025–2027 均为自然年；演示站：唯一公司 HDTH（`cn_urban_construction_tax_rate=7`、`cost_center=主 - HDTH`、无冻结日）、FY 2026 绑定 HDTH、MECV 0 行。
- MariaDB `11.8.9`，`transaction_isolation=REPEATABLE-READ`、`innodb_snapshot_isolation=ON`；`tabSeries`／`tabGL Entry`／`tabMonth End Closing Voucher` 均 InnoDB。
- 离线计算（容器 python，调用 frappe `flt(..., "Commercial Rounding")`）：附加税三项全舍入为 0 的计税依据区间（见 P2-02）。

**跳过及原因**
- **验证门未实跑**（F spec 预设提示词第 3 条要求自跑测试）：主会话正在跑全量回归，本片受「不跑测试」硬约束。本片无测试实测值，验证门由主会话负责。
- 列表页按钮未在浏览器里点（本项目无浏览器自动化；R9–R13 同样未点）。
- 并发重复生成、不可变总账、账簿（Finance Book）三类场景只读码推断，未在站点造数实测（只读约束）。
- Part3/Part4 的报表实现只读了与 Part2 契约相接的几处，不判其正确性（属别片）。

---

## 逐项落地核查

TS 编号为方案 TS；「生效否」指第二层（真被调用、未被绕过）。

| 意图层依据 | 要求层要求（方案任务/验收条款逐条） | 定位（文件:行） | 落地 | 生效否 | 偏差说明 |
|---|---|---|---|---|---|
| §4.7、DEC-118 | TS-009 DocType：模块 CN Tax、`is_submittable`、`track_changes`、无 `amended_from` | `month_end_closing_voucher.json` | ✅ | ✅ | — |
| 同上 | 字段 company/fiscal_year/month(Int)/closing_type(Select 四项)/posting_date(只读)/remark/accounts/total_debit/total_credit | 同上 `fields` | ✅ | ✅ | — |
| 同上 | 子表 account(必填)/cost_center/debit/credit/remark，`istable` | `month_end_closing_voucher_account.json` | ✅ | ✅ | — |
| 同上 | 权限：AM／SM 读建提交取消，AU 只读 | `.json` `permissions` | ⚠️ | ✅ | 另带 `delete/write/email/print/share/report`，方案未列（P2-12） |
| §4.7.1②、LG-144 | Custom Field `Company-cn_urban_construction_tax_rate`（Select `\n7\n5\n1`、insert_after tax_id、depends_on 中文表名）以 fixture 发布 | `fixtures/custom_field.json`；`hooks.py` fixtures | ✅ | ✅ | depends_on 字面与 `CN_CHART_NAME` 逐字相同（unicode 比对） |
| 总纲 A10、HT-012 | `autoname` → `JZ-{abbr}-{yyyymm}-.###` | `month_end_closing_voucher.py:34-42` | ✅ | ✅ | 年份取 FY 起始年，不取当天 |
| §4.7.3 | validate：非生成入口新建即拒 | `:45-48` | ✅ | ✅ | `flags` 属 `RESERVED_KEYWORDS`，经 JSON 无法注入 |
| 同上 | validate：自然年、月份 1–12、类型合法、年末仅 12 月 | `:50-57`；`assert_calendar_fiscal_year` `:13-20` | ✅ | ✅ | — |
| 同上 | posting_date = 月末 | `:59` | ✅ | ✅ | — |
| 同上 | 行校验：本公司、非组、未停用；损益科目须成本中心且属本公司、非组、未停用；借贷恰一方>0；flt 2 位 | `:70-108` | ✅ | ✅ | 「恰一方>0」与附加税全 0 的情形相撞（P2-02） |
| 同上 | 合计借=贷>0，至少一行 | `:63-68` | ✅ | ✅ | — |
| §4.7.3 第 1 条 | before_submit 同公司同月同类型不重复 | `:110-122` | ✅ | ⚠️ | 无锁「先查后写」，并发未实测（P2-14） |
| HT-004 | on_submit `make_gl_entries(..., merge_entries=False)` | `:124-125` | ✅ | ✅ | 冻结期、停用科目校验真跑（`general_ledger.py:49,416`）；**会计期间关闭对本单据默认不生效**（P2-04） |
| §4.7.3 第 2 条 | before_cancel：同月后序或更晚月份仍有效即拒 | `:127-146` | ✅ | ✅ | 跨年度也拦（按 posting_date 比） |
| HT-004 | on_cancel 忽略 GL/PLE 链接、`make_reverse_gl_entries` | `:148-150` | ✅ | ⚠️ | 未传 `posting_date`，开启不可变总账时红冲落在当天（P2-03） |
| HT-004、§4.7.4 | get_gl_entries 每行一条 GL；`get_voucher_subtype` = closing_type | `:152-171` | ✅ | ✅ | 另传 `account_currency=company_currency`，方案未写，无害 |
| §4.7.3 | 列表页「生成／取消」按钮、草稿确认后以 `ignore_drafts=1` 再调 | `month_end_closing_voucher_list.js` | ⚠️ | 未实点 | 取消入口无二次确认、空月取消也报「已取消」（P2-10） |
| TS-009 验证 | HT-004 两行凭证 GL 2 条、红冲、subtype；HT-012 编号；第 12 条前三项 | `test_closing_voucher.py` 4 个用例 | ✅ | — | 读断言，未跑 |
| TS-010 | `gl_sums` 签名与契约一致；共同条件；余额/发生额/年初三口径；exclude_pl_closing；accounts 显式空返回 {} | `ledger.py:9-98` | ✅ | ✅ | `finance_book` 条件与原生「默认含公司默认账簿」不一致（P2-05）；排除条件写字面量（P2-11） |
| 同上 | `leaf_accounts_under` 科目号不存在抛错 | `ledger.py:101-124` | ✅ | ✅ | — |
| 总纲 §六 | `CLOSING_TYPES`、`PL_EXCLUDED_SUBTYPES` 常量 | `closing.py:13-19` | ✅ | ⚠️ | `PL_EXCLUDED_SUBTYPES` 全仓无读取方（P2-11） |
| §4.7.3 | generate：权限 create、自然年、中国公司、重复拒、上月未结拒、草稿先返回、savepoint 原子 | `closing.py:252-296` | ✅ | ⚠️ | 「上月未结」只查有无损益结转凭证，不查是否完整（P2-01）；方法接受 GET（P2-06） |
| 同上 | `_make` 不加 ignore_permissions | `closing.py:41-57` | ✅ | ✅ | insert/submit 时按单据查权限（含 User Permission） |
| §4.7.1①、BR-004 | 增值税结转：组余额 B、本月已交 paid；B<0 借 2221003 贷 2221020；B>0 且 paid>0 取 min 借 2221020 贷 2221009；否则不结转 | `closing.py:139-165` | ✅ | ✅ | 会计推演见「业务规则合规核」 |
| §4.7.1②、偏离 5 | 计税依据 = paid + 转出未交 − 转出多交，下限 0 | `closing.py:279` | ✅ | ✅ | — |
| BR-005、DEC-116 | 附加税各自舍入后相加；城建税取公司档位、空值按 7 并提示；无默认成本中心抛错；0 额贷方行不写 | `closing.py:172-193` | ⚠️ | ✅ | 三项全为 0 时借方行为 0 → 整月生成失败（P2-02） |
| §4.7.1③ | 损益结转：本年 Income/Expense 按科目＋成本中心逐一结平，差额进 3103 | `closing.py:196-223` | ✅ | ✅ | 方向核对无误；前提「以前各月已结转」可被打破（P2-01） |
| §4.7.2 | 12 月本年利润结转：3103 余额转 3104090 | `closing.py:233-249` | ✅ | ✅ | — |
| §4.7.3 第 2 条 | cancel：权限 cancel、更晚月份有效即拒、逆序取消、savepoint、返回名单 | `closing.py:299-320` | ✅ | ✅ | 空月返回 []，前端报「已取消」（P2-10） |
| §4.7.3 第 4 条、DEC-121 | `month_closing_state`：closed 定义、结转后变动、损益余额非 0、年末缺本年利润结转 | `closing.py:323-365` | ✅ | ✅ | 判据只按科目、不按科目＋成本中心（P2-13）；跨年不在其职责内（P2-07） |
| SL-005 ① | 正常月 3 张、顺序、编号、组余额 0、2221020=销−进、附加税各自舍入、逐一为 0、3103=利润、subtype | `test_closing.py:234-278` | ✅ | — | 63.19 vs 63.18 有判别力 |
| SL-005 ② | 重复生成报错、条数不变 | `:280-284` | ✅ | — | — |
| SL-005 ③ | 直接取消前序被拒；逆序取消；快照还原；重做 -004…006 | `:286-293` | ✅ | — | 仅在不可变总账关闭时成立（P2-03） |
| SL-005 ④ | 留抵月只 1 张；下月扣上月留抵 | `:295-309` | ✅ | — | — |
| SL-005 ⑤ | 多交月借 2221020 贷 2221009；附加税按应纳 | `:358-371` | ✅ | — | — |
| SL-005 ⑥ | 草稿销售发票先返回清单 | `:311-318` | ✅ | — | — |
| SL-005 ⑦ | 上月有发生额未结 → 报错 | `:385-388` | ✅ | — | 只测了「无结转凭证」一种，未测「已结转后又变动」（P2-01） |
| SL-005 ⑧ | 结转后又提交发票 → 不完整；重做后完整 | `:327-341` | ✅ | — | — |
| SL-005 ⑨ | 冻结期报错且不留凭证 | `:373-383` | ✅ | — | 判别力问题 R12 E 已记，不重报 |
| SL-005 ⑩ | 12 月 4 张、3103 归零、3104090 | `:390-401` | ✅ | — | — |
| SL-005 ⑪ | 折旧凭证月份损益结转照常 | `:403-411` | ✅ | — | DEC-118 起因已消除 |
| SL-005 ⑫ | 直插拒、3 月年末结转拒、AU 拒、非自然年拒 | `test_closing_voucher.py`；`test_closing.py:343-356` | ✅ | — | — |
| SL-005 ⑬ | 城建税 5% 与空值 7% 提示 | `test_closing.py:358-371、324` | ✅ | — | — |

---

## 业务规则合规核

| 规则条款 | 本片是否涉及 | 结论 | 备注 |
|---|---|---|---|
| BR-001 小企业会计准则 | 是（3103 本年利润、3104090 未分配利润、5403 税金及附加） | 合规 | 科目号与名称在 JSON 中逐一核对：2221003 转出未交增值税、2221009 转出多交增值税、2221020 未交增值税、2221040/2221110/2221150 三项附加、3103、3104090、5403 |
| BR-002 报表构成 | 否（属 Part3/4） | — | — |
| BR-003 增值税税率 | 否（结转不涉及税率） | — | — |
| BR-004 增值税月末转出 | 是 | 合规（规则本身「中」可信度，未经专家确认） | 会计推演 6 例全部方向正确：① 销 1300 进 0 未交 → 借 2221003 1300 贷 2221020 1300，组归零；② 上月留抵 500、本月销 1300 → B=−800，转出未交 800（＝销−进−上月留抵）；③ 销 1300、本月已交 2000 → B=+700，借 2221020 贷 2221009 700，计税依据 2000−700=1300；④ 留抵 500、本月净 300、已交 100 → B=+200，多交取 min=100，计税依据 0；⑤ 销 1000、已交 1000 → B=0 不结转，计税依据 1000；⑥ 进>销且无已交 → 不结转、留抵原样留存。「多交取 B 与 paid 较小者」「结转范围限 2221001…2221010」由需求推定，**草案·待领域专家确认** |
| BR-005 附加税 | 是 | 部分合规；计税依据细则 **草案·待领域专家确认** | 税率 7/5/1、3、2 正确；各项各自舍入（Commercial Rounding，两站实测）。计税依据取「本月应纳增值税」（计提口径），与法条「实际缴纳」的关系是会计惯例推定；未覆盖：免抵税额加回、留抵退税扣除（财政部 税务总局公告 2021 年第 28 号）、月销售额 ≤10 万免征教育费附加与地方教育附加（财税〔2016〕12 号，一般纳税人也适用）。见 P2-08 |
| BR-006 资产负债平衡 | 间接（每张结转凭证借贷相等，`validate` 强制） | 合规 | 结转不改变资产负债表两侧合计 |
| BR-007 价税分离舍入 | 间接（附加税舍入） | 合规 | 站点 `Commercial Rounding`（DEC-116）；舍入口径本身待专家确认 |
| 本片推定的新规则 | DEC-121「无损益发生额的月份不算尚未结转」 | **草案·待领域专家确认**（LG-153） | 代码 `closing.py:328`、`:112` 两处与之一致 |
| 本片推定的新规则 | 偏离 5「计税依据 = 已交 + 转出未交 − 转出多交，下限 0」 | **草案·待领域专家确认** | 回执拿不准处第 1 条已登记 |
| 本片推定的新规则 | 「上月未结」只判有无损益结转凭证（方案字面） | **草案**（本审核认为应判完整，见 P2-01） | 是否算会计惯例须专家判 |

---

## 集成点登记（交接摘要）

**本片暴露给别片**
- `ledger.gl_sums(...)`、`ledger.leaf_accounts_under(...)`：签名与总纲 §六／Part2 一致。调用方：`statements/engine.py:33,34,39,124`、`unmapped.py:72-95`、`cash_flow_statement.py:146`、`cash_flow.py:199,201,230`。口径：`finance_book IS NULL OR ''`（P2-05 影响所有调用方）。
- `closing.month_closing_state(company, fiscal_year, month) -> {closed, complete, vouchers, issues}`：消费方 `balance_sheet._closing_notes`（`balance_sheet.py:64-80`，利润表经它复用）。**耦合点**：消费方按 `_()` 源词**整句相等**识别 issue，两端源词须逐字一致（现一致：`closing.py:351,354,359` 与 `balance_sheet.py:66-68`）。
- GL 标记：`voucher_type='Month End Closing Voucher'` + `voucher_subtype ∈ CLOSING_TYPES`。利润表排除条件在 `ledger.py:74-77` 与 `engine.py:72-73` 各写一份字面量，未引用 `PL_EXCLUDED_SUBTYPES`（P2-11）。
- 结转后的状态不变量（供 Part3 `UNCLOSED_PL_ROOTS=("500","540")` 使用）：已结转月份损益科目本年余额为 0。P2-01、P2-05、P2-07 三处会让这个不变量不成立。
- 数据：Company 字段 `cn_urban_construction_tax_rate`（fixture）。

**本片依赖别片**
- Part1：中国科目表的科目号结构（2221000 为组且下挂 2221001…2221010；2221002/003/009/020/040/110/150、3103、3104090、5403 均为明细）、`is_cn_chart`、建公司时设的 `Company.cost_center`。
- Part4/TS-021 与建站脚本：`System Settings.rounding_method=Commercial Rounding`（DEC-116；两站实测已是）。
- Part4/TS-020：`translations/zh.csv` 的结转词条（R13 已核）。

**事件 / 共享状态**
- 不发出、不消费 SSE 或 realtime 事件。
- 共享状态：`tabSeries` 中 `JZ-{abbr}-{yyyymm}-` 前缀；`Company.accounts_frozen_till_date`（只读消费）；`Accounts Settings.enable_immutable_ledger`（**未读取，但上游会按它改变冲销行为**，P2-03）。
- **供收口交叉比对**：Part3 `_closing_notes` 只遍历所选会计年度的 1…month（`balance_sheet.py:70`），上年 12 月未结转／未做本年利润结转在新年度报表上不提示（P2-07）。请收口与 Part3 片核对这一点是否另有覆盖。

---

## 自证复核

| 被审产物声称 | 实际复核结果 | 一致否 |
|---|---|---|
| 方案 Part2：「冻结期、会计期间关闭、科目停用等校验不自己写：`make_gl_entries` 过账时自带」 | 冻结期（`general_ledger.py:416,727`）、停用科目（`:49`）确实自带；**会计期间关闭**只查 `Closed Document.document_type == voucher_type`（`:155-187`），而本 app 未注册 `period_closing_doctypes`，`erpnext/hooks.py:326-345` 的默认清单里没有本单据 ⇒ 默认不生效 | 不一致（P2-04） |
| 方案 Part2：「`finance_book` 与原生报表的默认条件一致（`financial_statements.py:628-632`）」 | 原生默认 `include_default_book_entries=1`（`profit_and_loss_statement.js:45-48`），会把公司默认账簿的分录也算进来（`financial_statements.py:615-627`）；本片只取空账簿 | 部分不一致（P2-05） |
| D 回执 Part2：「失败插入会消耗序号，属上游 tabSeries 既有语义」 | `tabSeries` 是 InnoDB（实测），生成失败走 savepoint 回滚（`closing.py:293`），HTTP 请求异常也整体回滚 ⇒ 本流程中失败**不**消耗序号。读码推断，未实跑 | 不一致（无业务影响，不列为问题） |
| D 回执／R12/R13 E：SL-005 ①～⑬ 全部有断言 | 逐条读断言，13 条均有；⑦ 只覆盖「上月无结转凭证」一种情形 | 一致（覆盖面见 P2-01） |
| R13 E：结转相关源文件本轮空 diff | `git log` 显示 Part2 源文件最后改动在 `ab3803f`（R11），之后只有 `ee5fe6a` 改测试一行；工作区与 HEAD 无差异 | 一致 |
| 方案 SL-005 ③：取消后「该月除结转外的 GL 余额与结转前逐科目相同」 | 在 `enable_immutable_ledger=0`（两站现值）下成立；开启后不成立 | 条件成立（P2-03） |

---

## 问题清单

| # | 严重程度 | 定位 | 问题描述 | 违背的标准/意图 | 建议 | 建议档位 | 待裁决点 | 状态 |
|---|---|---|---|---|---|---|---|---|
| P2-01 | 中 | `closing.py:107-123`（`_unclosed_previous_months`）；`:196-223` | 「上月未结」只看上月有没有有效的损益结转凭证，不看是否完整。常见场景：2 月已结转后，又补录一张 2 月发票。此时生成 3 月不会被拦：3 月增值税组余额 B 会带上 2 月补录的税额，计税依据和附加税随之多算；3 月损益结转按本年累计取数，把 2 月补录的收入一并转进 3 月的凭证。结果是 3 月的 `3103` 增加额不等于 3 月利润，3 月状态却判为 `complete`（它只查本月）。2 月的提示一直挂着，要清掉只能把 3 月、2 月逐月取消再重做。方案 TS-010 注释「以前各月已结转，故这里只剩本月净额」的前提由此失效 | 需求 §4.7.3 第 4 条（结转后又有新单据须明确提示，不得静默）；SL-005 ①「`3103` 贷方增加额 ＝ 本月利润」；Part2 TS-010 ③ 的前提 | 生成前对本年更早的月份调 `month_closing_state`，凡 `complete=False` 的拒绝生成并列出；补一条「上月结转后补录 → 本月生成被拒」的测试 | 出方案修 | 拦截条件是「上月有损益结转凭证」（方案字面）还是「上月结转完整」；补录上月单据后应该怎么处理，要不要请会计确认 | 待裁决 |
| P2-02 | 低 | `closing.py:181-188`；`month_end_closing_voucher.py:84-85` | 计税依据大于 0 但很小时，三项附加税各自舍入后都是 0，借方 `5403` 那行也是 0，触发「借贷恰一方>0」校验，整次生成报错回滚，这个月就结转不了。连带下月也会被「上月未结」拦住，而且无法绕过。实测（Commercial Rounding）全零区间：城建 7% 档为 0.01–0.07，5% 档为 0.01–0.09，1% 档为 0.01–0.16 | SL-005 ①④ 的可结转性；方案只写了「金额为 0 的贷方行不写」，没写合计为 0 的情形 | 合计为 0 时不生成附加税计提凭证，在 `message` 里说明一句 | 本Session修 | 合计为 0 时跳过附加税并提示，是否可以 | 待裁决 |
| P2-03 | 低（开启不可变总账后为高） | `month_end_closing_voucher.py:148-150`；上游 `general_ledger.py:722-727,792-794` | `on_cancel` 调 `make_reverse_gl_entries` 时没传 `posting_date`。如果开启 `Accounts Settings.enable_immutable_ledger`，原分录保持 `is_cancelled=0`，红冲分录记在**当天**。后果：取消 3 月结转后 3 月账面不变，红冲落进当前月份，把 3 月的损益重新打进当月；接着重新生成 3 月得到「本月无需结转」；`month_closing_state` 又把 3 月判为已结转。原生期末结账单对这个开关有专门处理（`period_closing_voucher.py:55-60`），本单据没有。两站该开关现为 0 | SL-005 ③（取消后逐科目还原、可重做）；需求 §4.7.3 第 2 条 | 生成与取消入口检查该开关，开启时明确报错；或研究按原月末日期冲销是否合规后再定 | 新Session修 | 开启时直接拒绝，还是要支持 | 待裁决 |
| P2-04 | 低 | `hooks.py`（未注册 `period_closing_doctypes`）；上游 `general_ledger.py:155-187`、`erpnext/hooks.py:326-357` | 会计期间（Accounting Period）关闭后，结转凭证照样能生成和取消：上游只拦 `Closed Document` 里列出的单据类型，默认清单来自 `period_closing_doctypes` 钩子，本 app 没往里加。方案说「会计期间关闭……过账时自带」，这一项默认不成立。两站 Accounting Period 均为 0 行，属潜在问题 | 方案 Part2 TS-009 第 105 行的声称；开发守则「断言机制可用前写入端与读取端两侧都查」 | 在 `hooks.py` 加 `period_closing_doctypes = ["Month End Closing Voucher"]`（L3 追加，不占覆盖位） | 本Session修 | 是否加这个钩子 | 待裁决 |
| P2-05 | 低 | `ledger.py:33` | 共同条件写死 `finance_book IS NULL OR ''`。带账簿的 GL（比如资产折旧按账簿计提、或日记账凭证填了账簿）会被结转整体漏掉：总账里这些损益科目月末不归零，`month_closing_state` 用的是同一个口径，也看不到，**静默**。另外原生报表默认把公司默认账簿也算进来（见自证复核），所以方案说的「与原生默认一致」不准确。两站 Finance Book 均为 0 行，属潜在问题 | 需求 §4.7.1③「使这些科目月末余额为 0」；开发守则「静默失败」 | 生成前检查本月有没有带账簿的损益 GL，有就报错；或者至少把公司默认账簿纳入取数口径 | 新Session修 | 本 Stage 是否支持账簿；不支持时用报错挡住，还是写进遗留 | 待裁决 |
| P2-06 | 低 | `closing.py:252,299`（`@frappe.whitelist()` 未限定 methods）；上游 `frappe/__init__.py:454-455`、`app.py:465-468` | 生成和取消这两个写操作接受 GET。GET 请求会把整套结转跑完，返回 `created` 名单，但请求结束时被 `db.rollback`，凭证并没有落库：返回值说成功，实际什么都没留下（例如用地址栏或书签调用） | 开发守则「静默失败」（须有正向证据） | 两处改为 `@frappe.whitelist(methods=["POST"])` | 本Session修 | — | 待裁决 |
| P2-07 | 观察 | `closing.py:110`；`balance_sheet.py:70`（Part3） | 跨年度不设闸：上年 12 月有损益没结转、或没做本年利润结转，次年 1 月照常能结；上年遗留的损益余额不会被新年度的结转扫进来（本年取数从 1 月 1 日起）。Part3 的说明行只遍历本年月份，新年度报表不会提示上年未结。方案验收 ⑦「本年第一个有业务的月份不受此限」明文允许，所以记为观察 | 需求 §4.7.2（年末本年利润结转）、§4.7.3 第 4 条的意图 | 生成 1 月前检查上年 12 月 `month_closing_state(...)["complete"]`；或在报表说明里加一行上年状态 | 出方案修 | 跨年要不要拦（会改变方案已明文允许的行为） | 待裁决 |
| P2-08 | 观察 | `closing.py:172-193、279`；`docs/业务规则.md` BR-005 | 附加税计税依据没覆盖三种法定调整：① 免抵税额要加回（2221008「出口抵减内销产品应纳税额」借方会压低 B，进而少计）；② 期末留抵退税额要扣除；③ 月销售额 ≤10 万时免征教育费附加和地方教育附加，一般纳税人也适用。LG-150 只排除了小规模纳税人和「六税两费」，没说到这几项。演示公司未必碰得到 | BR-005（规则表述不完整）；财政部 税务总局公告 2021 年第 28 号；财税〔2016〕12 号 | 补进 BR-005 送审范围；没纳入的写进遗留问题 | 延迟或不修 | 是否登记为遗留、送专家时一起问 | 待裁决 |
| P2-09 | 观察 | 上游 `financial_statements.py:594-598`、`budget_controller.py:268-283` | 采用账结法后原生功能跟着失真：原生「损益表」「试算表」只排除期末结账单，已结转月份的损益显示为 0；原生预算控制按本年损益科目 GL 净额算实际支出，每月结转一冲就归零，预算的「停止／警告」从此不再触发。需求只要求自写的利润表排除结转凭证。两站 Budget 为 0 行 | DEC-099 的连带影响，需求与方案都没有登记 | 在 S6 导航或 README 说明原生损益类报表和预算在本账套下不适用；或登记为遗留 | 延迟或不修 | 登记到哪里（遗留问题或 S6 约束） | 待裁决 |
| P2-10 | 低 | `month_end_closing_voucher_list.js`（`primary_action_label`、`call_closing_method`）；`closing.py:312-320` | 取消入口：对话框主按钮叫「取消」（zh 下 `Cancel`→取消），和「关掉对话框」同名，点了就直接冲销整月，没有二次确认；该月没有有效凭证时后端返回 `[]`，前端照样提示「月末结转已取消」 | 开发守则「静默失败」；DEC-119 会计习惯（冲销须确认） | 主按钮改为「取消结转」并加 `frappe.confirm`；后端在无凭证时报错或返回明确说明 | 本Session修 | — | 待裁决 |
| P2-11 | 低 | `closing.py:19`；`ledger.py:74-77`；`statements/engine.py:72-73` | `PL_EXCLUDED_SUBTYPES` 全仓没有读取方，是死常量；利润表的排除条件在 `ledger.py` 和 `engine.py` 各写了一遍字面量。改常量时两处不会跟着变 | 总纲 §六 契约（常量的用途就是「利润表取数排除」） | 两处 SQL 改为引用常量（参数化 `IN %(subtypes)s`） | 本Session修 | — | 待裁决 |
| P2-12 | 观察 | `month_end_closing_voucher.json` `permissions` | 方案外夹带：Accounts Manager 和 System Manager 另有 `delete/write/email/print/share/report`，方案只列了读、建、提交、取消。`delete` 让已取消的结转凭证可以被删，编号出现断档、审计痕迹缺失（GL 留着，因为 `delete_linked_ledger_entries=0`）。疑为脚手架默认值 | 方案 TS-009 权限行 | 去掉 `delete`；其余可以保留 | 本Session修 | 已取消的结转凭证是否允许删除 | 待裁决 |
| P2-13 | 观察 | `closing.py:98-104`（`_pl_has_activity`）、`:352-354` | 「有无损益发生额」和「月末损益余额非 0」两处判据都只按科目汇总，不按科目＋成本中心。同一科目在不同成本中心之间做了重分类的月份，按科目净额为 0，会被判为「无发生额／已结转」，而 SL-005 ① 要求的「按科目＋成本中心逐一为 0」其实不成立，也没有提示 | SL-005 ①「逐一为 0」；开发守则「判据须能区分」 | 两处判据改成 `by_cost_center=True` | 本Session修 | — | 待裁决 |
| P2-14 | 观察 | `closing.py:263`；`month_end_closing_voucher.py:110-122` | 防重复是无锁的「先查后写」。两次请求并发时能不能挡住，取决于 MariaDB 11.8 `innodb_snapshot_isolation=ON` 在 `tabSeries FOR UPDATE` 上报错这一副作用，不是设计出来的互斥。只读码，未实测 | 需求 §4.7.3 第 1 条 | 生成前 `SELECT … FOR UPDATE` 锁 Company 行（或按 公司＋月 建锁） | 延迟或不修 | 是否值得加锁（单人操作场景下概率低） | 待裁决 |

---

## 本片盲区自述

- **没往这些方向找**：没核 Part1 的税模板与发票过账是否真把税额记到 2221005／2221001（假定 Part1 正确，由第 1 片负责）；没核 zh 译文本身（R13 已逐条核过）；没看 GL Entry 以外的账（Payment Ledger Entry 对结转无影响，未深究）；没查多币种科目（`get_gl_dict` 传了 `account_currency=company_currency`，外币损益科目会怎样没推演）；User Permission 场景只读码判断「insert/cancel 时会按单据查权限」，`_drafts` 用 `get_all` 会把别家公司的草稿单号回给调用者，影响很小，未列为问题。
- **把握最低的三处**：P2-03（不可变总账下的冲销路径完全靠读上游代码推断，没有实跑；开关的实际使用面也没查）；P2-14（并发是否真被 snapshot isolation 挡住，不确定）；P2-08（会计法规条文来自财政部、税务局网页检索，没取得法规库原文全文，「计提口径 vs 实际缴纳口径」更是会计惯例判断）。
- **拿不准的定级**：P2-01 在「中／低」之间。定为中，是因为补录上月单据在会计实务里很常见；改判为低的理由是可以靠逐月取消重做恢复，报表上也有上月提示。P2-02 在「低／中」之间：概率低，但一旦碰上就是硬阻断、绕不过去。
- **拿不准是否属于「方案外夹带」**：P2-12 的多余权限多半是脚手架默认值，不是有意加的；P2-07 是方案明文允许的行为，只记为观察。
- **验证门**：本片没跑任何测试（硬约束），上表的「—」都是读断言得出的结论，不是实测通过。
