# P1-S4-R17 F 审核报告 Part5（分片 5：依据 R15 开发方案）

**轮次**：P1-S4-R17｜**步骤**：F 分片 5（plannedDev audit 复核轮，依据 R15 开发方案）｜**执行者**：Claude（Opus 5.5）子 Agent｜**日期**：2026-10-03

**依据**：
- 要求层：[R15 C开发方案](../R15-开发方案/P1-S4-R15-C开发方案.md) §二、§三、§五、TS-023…026；[R15 C讨论记录](../R15-开发方案/P1-S4-R15-C讨论记录.md) DEC-122…124；[R15 C回执](../R15-开发方案/P1-S4-R15-C回执.md)
- 执行层：[R16 D回执](../R16-代码/P1-S4-R16-D回执.md)、[R16 D讨论记录](../R16-代码/P1-S4-R16-D讨论记录.md) DEC-125
- 意图层：R14 F 报告 FD-004、FD-007、FD-032 行；Part1 P1-02、Part2 P2-01／P2-07、Part3 P3-01；B 需求文档 §4.4.4、§4.7.3 第 4 条、§4.11 第 4 条；DEC-121（R12 SB 讨论记录）；`docs/业务规则.md`

**被审范围**：`frappe_china` 提交 21faeb9 相对 48e7933 的 12 个文件（README、`closing.py`、`balance_sheet.py`、`company_defaults.json`、`patches.txt`、`patches/fd004_default_accounts.py`、5 个测试文件、`zh.csv`），以及其中 `closing.py`、`balance_sheet.py`、补丁文件、`company.py`、`ledger.py` 的当前全文。上游对照 `erpnext` v16 的 `company.js/py`、`stock_reconciliation.py/js`、`stock_entry.py`、`stock_controller.py`、`depreciation.py`、`sales_invoice_item.py`、`bom.py`，以及 `frappe` 的 `patch_handler.py`、`utils/error.py`。

**方法与边界**：只读。没跑测试，没 migrate，没写站点。站点只做了 SELECT：演示站 HDTH 的两个默认科目、`tabPatch Log`、Error Log、SLE 计数、Temporary 科目、物料组默认科目；测试站的 `tabPatch Log`。

## 覆盖自证

| 依据条目 | 逐条核了吗 | 落在哪一节 |
|---|---|---|
| §二 替换关系 6 行 | 是 | 逐项落地核查 R-01…R-06 |
| §三 接口契约（`month_closing_state` 返回结构、PENDING_LOSS_ISSUE、`_incomplete_previous_months`、报错源词） | 是 | R-07…R-10 |
| SL-011 验收 1–9 | 是（9 条各一行） | A11-1…A11-9 |
| SL-012 验收 1–6 | 是（6 条各一行） | A12-1…A12-6 |
| TS-023 具体改动（json、patch、README、两条 test_company、postings 测试） | 是 | T23-a…T23-f |
| TS-024 具体改动（closing、balance_sheet、zh.csv／test_translations） | 是 | T24-a…T24-c |
| TS-025 具体改动（删旧函数、改调用、改词条、删旧词条） | 是 | T25-a…T25-d |
| TS-026（两站 migrate、Patch Log、全量回归、自检、变异） | 是（全量回归和变异没复跑，只核了站点数据） | T26-a…T26-d |
| HT-015／016／017 | 是（读码） | 开放查漏、自证复核 |
| DEC-121／122／123／124／125 | 是 | 开放查漏、会计口径、合规核表 |
| 任务 4 开放查漏点（9 项） | 是（逐项都有结论，见「开放查漏逐点结论」） | 开放查漏 |

## 逐项落地核查

| R15 要求（SL/TS 条目） | 定位（文件:行） | 落地 | 生效否 | 原问题消失否 | 偏差说明 |
|---|---|---|---|---|---|
| R-01 §二：stock_adjustment_account → 1901 | `cn_tax/data/company_defaults.json:11` | ✅ | ✅ 建账时 `set_cn_default_accounts` 按 `DEFAULT_ACCOUNT_NUMBERS` 取（`accounting/company.py:93-106`） | ✅ 盘点差额进 1901，年末不清零会提示 | 盘点之外的兜底路径也会落 1901，见 P5-03 |
| R-02 §二：disposal_account → 5711010 | `company_defaults.json:16` | ✅ | ✅ 上游 `get_disposal_account_and_cost_center` 从 Company 取（`depreciation.py:781-791`） | ✅ 报废净损失进营业外支出 | 有净收益时记成营业外支出负数（DEC-123 已认），见 P5-09 |
| R-03 §二：400103 余额性质存疑注关闭 | `mapping.py:48`（400103 仍在第 9 行） | ✅ 不改映射 | — | ✅ 400103 已不是默认科目 | 无 |
| R-04 §二：`_unclosed_previous_months` → 按 `complete` 判 | `closing.py:110-116`、`:296-298` | ✅ | ✅ 唯一调用点已换；旧函数全仓 grep 无残留（只剩旧 .pyc） | ✅ 补录后下月被拦 | 「结转后变动」的判据过宽，硬拦后影响放大，见 P5-01 |
| R-05 §二：SL-005 第 7 条保留 | `tests/test_closing.py:396-402` | ✅ | ✅ | ✅ | 无 |
| R-06 §二：12 月另查 1901 | `closing.py:403-407` | ✅ | ✅ | ✅ | 无 |
| R-07 §三：返回结构不变 | `closing.py:408-413` | ✅ 仍是 closed/complete/vouchers/issues 四键 | ✅ | — | 无 |
| R-08 §三：PENDING_LOSS_ISSUE 常量、经 `_()` 输出 | `closing.py:32`、`:407`；`balance_sheet.py:82` | ✅ 源词与方案逐字一致 | ✅ | — | 用变量调 `_()`，`_app_source_strings` 的正则扫不到它；D 已把它显式写进 `REQUIRED_TRANSLATIONS`（`test_translations.py:65`），不漏 |
| R-09 §三：`_incomplete_previous_months` 签名与返回 | `closing.py:110-116` | ✅ 返回 `list[(month, issues)]` | ✅ | — | 无 |
| R-10 §三：报错源词与拼接 | `closing.py:297-298` | ✅ `"；"` 连月份、`"，"` 连原因，与方案伪代码一致 | ✅ | — | 拼出来的中文有歧义，见 P5-06 |
| A11-1 新建公司两个字段为 1901／5711010，其余 20 个不变 | `test_company.py:65-68`；json diff 只改 2 行 | ✅ | ✅ | ✅ | 「其余 20 个不变」靠 diff 证明，老测试 `test_cn_company_builds_complete_chart_and_defaults` 是拿 json 比 json，不独立 |
| A11-2 22 项过滤，例外显式 | `test_company.py:70-106` | ✅ 22 条与 `company.js:283-345` 逐条对过，一致 | ✅ | ✅（disposal） | DEC-125 把例外扩成 `{root_type, account_type}` 以后，库存调整那一项已经没有条件可查，任何科目都能过，见 P5-05(a) |
| A11-3 盘盈：1901 贷 20、存货借 20；第 28 行 -20；第 9 行与勾稽不受影响 | `test_default_account_postings.py:47-55` | ✅ | ✅ | ✅ | 期望值都写死（-20、120、0） |
| A11-4 转出 1901→5301050：第 22 行 20，1901 归 0 | 同文件 `:56-59` | ✅ | ✅ | ✅ | 无 |
| A11-5 盘亏：1901 借 10 | 同文件 `:60-61` | ✅ | ✅ | ✅ | 无 |
| A11-6 报废：5711010 借 1000，第 24 行 1000，1606 无分录 | 同文件 `:64-87` | ✅ | ✅ | ✅ | 测试另外 `db_set` 了 `depreciation_cost_center`，多余：演示站上它本来就有值，见 P5-05(e) |
| A11-7 12 月 1901 有余额 → complete=False＋issue；报表说明行带金额；余额为 0 不出 | `test_closing.py:454-470`；`test_balance_sheet.py:44-57` | ✅ | ✅ 检查放在 `closed` 判断之外（`closing.py:403`，与 `:398` 平级） | ✅ | 说明行金额只给「借−贷」，没写方向，见 P5-07 |
| A11-8① 非 12 月有余额不影响 | `test_closing.py:472-478`；`test_balance_sheet.py:55` | ✅ | ✅ | ✅ | 无 |
| A11-8② patch：只改旧值、被改过的不动、两次相同、非本表公司不动 | `test_company.py:108-129`；补丁 `:14-29` | ✅ | ✅ | ✅ | 「非本表公司」这一条，测试分不清是哪道闸挡住的；缺目标科目的分支没测，见 P5-04、P5-05(b) |
| A11-9 1901 与 5711010 不算漏科目 | `test_default_account_postings.py:33-36` | ✅ | ✅ | ✅ | 这条断言换成旧科目也能过（400103／1606 本来就有映射），只防回归，没有判别力 |
| A12-1 2 月结转后补录 2 月发票 → 生成 3 月报错，含「2 月」与「结转后该月又有凭证变动」，3 月零凭证 | `test_closing.py:404-413` | ✅ | ✅ | ✅ | 无 |
| A12-2 取消重做 2 月后 3 月成功；3103 贷增 ＝ 3 月利润；2 月 complete | 同 `:414-421` | ✅ | ✅ | ✅ 期望值 -500 写死，按 3 月一笔 500 的造数推出，不取自被测函数 | 无 |
| A12-3 10 月未结 → 生成 11 月报错，含「10」「尚未结转」 | `test_closing.py:396-402` | ✅ | ✅ | ✅ | 无 |
| A12-4 空月不拦（DEC-121） | `test_closing.py:423-429` | ✅ | ✅ `closed = 有损益结转 or 无损益发生额`（`:369`），空月 vouchers 为空，不进变动／余额检查 | ✅ | 无 |
| A12-5 2 月、4 月各自不完整 → 生成 5 月，两月两因都列出 | `test_closing.py:431-443` | ✅ | ✅ | ✅ | 无 |
| A12-6 zh 下报错全中文 | `test_closing.py:445-452` | ✅ 断言消息里没有任何拉丁字母 | ✅ | ✅ | 基类本来就设了 zh（`tests/utils.py:33`），这里再设一遍是冗余，无害 |
| T23-a json 两行 | `company_defaults.json:11,16` | ✅ | ✅ | ✅ | 文件头注释没动 ✅ |
| T23-b 新 patch 登记在 `[post_model_sync]` | `patches.txt:6`（在 `[post_model_sync]` 之下） | ✅ | ✅ 两站 `tabPatch Log` 各 1 行（本片实查） | ✅ | 无 |
| T23-c 补丁逻辑 | `patches/fd004_default_accounts.py:14-29` | ✅ | ✅ | ✅ | 比方案多一道 `not old` 闸（`:21`），更稳；缺科目分支只记一次日志，见 P5-04 |
| T23-d README 补偏离 | app `README.md:127` | ✅ 内容准确（DEC-125 的两项都写了） | — | — | 写进了「已知限制」，没进「相对 zelin 的修改」表；后面多一行空行，见 P5-08 |
| T23-e test_company 两条（另多一条 numbers） | `test_company.py:65-129` | ✅ | ✅ | ✅ | 见 P5-05 |
| T23-f postings 新文件 | `tests/test_default_account_postings.py` | ✅ 用带 `update_stock` 的采购发票入库 10×10；报废的日期取当天 | ✅ | ✅ | 无 |
| T24-a `month_closing_state` 12 月 1901 | `closing.py:403-407` | ✅ 与方案伪代码逐字一致 | ✅ | ✅ | 1901 一旦拆明细或被删，`_one_account` 直接抛错，见 P5-02 |
| T24-b `_closing_notes` 追加说明行 | `balance_sheet.py:82-85` | ✅ 按源词匹配，单独取余额，金额经 `_money` | ✅ | ✅ | 从 `closing` 导入私有的 `_one_account`、`_money`，属风格问题，不立项 |
| T24-c 译文＋测试 | `zh.csv:55`；`test_translations.py:65` | ✅ | ✅ | ✅ | 无 |
| T25-a 删旧函数、换调用 | `closing.py:110-116、296-298` | ✅ | ✅ | ✅ | 位置在「已结转拒」和账簿检查之后、草稿检查之前，savepoint 之外 ✅ |
| T25-b 两条新词条 | `zh.csv:23-24`；`test_translations.py:33-34` | ✅ | ✅ | ✅ | 无 |
| T25-c 旧词条「Previous months are not closed」两处删 | `zh.csv`、`test_translations.py` | ✅ 全仓源码 grep 无残留 | — | — | 无 |
| T25-d issue 源词旧译文不动 | `zh.csv:51-53` | ✅ | — | — | 无 |
| T26-a 测试站 migrate＋Patch Log | 本片实查 test.localhost `tabPatch Log` | ✅ 1 行 | ✅ | — | 无 |
| T26-b 演示站备份＋migrate＋HDTH 两字段 | 本片实查 erx.localhost | ✅ HDTH=`1901 - 待处理财产损溢_非流动资产 - HDTH`／`5711010 - 非流动资产处置净损失 - HDTH`；Patch Log 1 行（13:35:00）；`country=China`；`保留-R15迁移前/` 目录存在（13:34） | ✅ | ✅ | 备份文件的 gzip／tar 校验没复做 |
| T26-c 全量回归 ≥137 | 未复跑（主会话在跑） | — | — | — | 测试数 137＋12＝149，与新增 12 条（company 3、postings 2、closing 6、balance_sheet 1）对得上 |
| T26-d 自检 ok | 未复跑 | — | — | — | `check_company_chart` 不查这两个字段（只查 DEC097 六项），所以它 ok 说明不了这两个字段，见 P5-04 |

## 自证复核

| D 回执声称 | 实际复核 | 一致否 |
|---|---|---|
| TS-023 落在 `company_defaults.json:11`、`patches/...:15`、`patches.txt:6`、`test_company.py:65` | 行号对得上 | ✅ |
| TS-024 落在 `closing.py:36`、`balance_sheet.py:98` | 实际在 `closing.py:32`（常量）／`:403-407`（检查），`balance_sheet.py:82-85` | ⚠ 行号不准（不影响结论） |
| TS-025 落在 `closing.py:119`、`test_closing.py:403` | 实际在 `closing.py:110`（函数）／`:296`（调用） | ⚠ 行号不准 |
| 「年末未结及已结都检查 1901」 | `:403` 不依赖 `closed`；测试在生成前、生成后各断言一次（`test_closing.py:458`、`:463`） | ✅ |
| 补录拦截后 3 月零凭证；重做后 3 月 3103 贷增 500，与 2 月补录额无关 | 测试写死 -500；造数是 3 月一笔 500，3 月没有增值税业务，推导成立 | ✅ |
| TS-023 变异 4/4 失败 | 读码确认：json 两行都改回时，numbers、filters（因为 disposal）、两条 postings 都会失败。**但只改回 stock_adjustment 时 filters 测试照样通过**（例外把条件全豁免了） | ✅（回执说的是两行一起改回的情形）；补充见 P5-05(a) |
| TS-024 变异 2/2、TS-025 变异 2/2 | 读码确认，判别力成立 | ✅ |
| 缺目标科目分支本轮未实跑 | 读码确认：不会让 migrate 中断，Error Log 会写、print 会打，但补丁仍记为已执行、以后不再跑 | ✅ 回执如实；后果见 P5-04 |
| 两站 Patch Log 各 1；HDTH 已改；country=China | 本片 SELECT 实查一致；Error Log 里没有本补丁的告警 | ✅ |
| 全量 149/149 | 没复跑；数字自洽 | 未复核 |
| HT-015／016「先以进程内默认值替换验证通过」 | 读码：报废 `depreciation.py:635-680、760-778` 只记净损益一笔进 `disposal_account`；盘点 `stock_reconciliation.py:975-990` 在「全站无 SLE」或「Opening Stock」时只拒损益类科目，1901 是资产负债表类，能过 | ✅ |
| README 写准 DEC-125 | 上游过滤只在 `enable_perpetual_inventory` 时生效（`company.js:330-345`）；HDTH 是 1，生效；服务端 `company.py:248-290` 只校验所属公司、组科目、停用 | ✅ |

## 开放查漏新发现

| 片内编号 | 严重程度 | 定位 | 问题 | 违背的标准 | 建议修法 | 建议档位 | 待裁决点 | 证据 |
|---|---|---|---|---|---|---|---|---|
| P5-01 | 中 | `closing.py:383-392`（判据）×`:296-298`（DEC-124 改成硬拦） | 「结转后该月又有凭证变动」的判据是：该月有**任何**非结转凭证的 GL 晚于结转。以前它只出一行报表提示，DEC-124 以后变成**拦下月生成**。于是结转后补录到上月的、与损益和增值税都无关的凭证，例如晚导入的银行流水生成的收付款、内部转账、只动资产负债表的调整分录，也逼会计按逆序取消、重做上月（若更晚的月份已结，还得先把它们一并取消）。重做出来的凭证与原来完全一样。补库存类单据还会触发上游 repost，重建后续凭证的 GL，同样会被判「变动」 | DEC-124 的目的「补录金额不再被算进本月」只涉及损益与增值税组科目；需求 §4.7.3 第 4 条说的是「结转已不完整」，资产负债表科目的补录不影响结转是否完整 | 变动判据只看「损益类科目＋`2221000` 组下明细」的 GL；或者硬拦只针对「尚未结转／损益余额不为 0／影响损益或增值税的变动」，其余变动降为提示 | 出方案修（或接受现状、登记为延迟） | 「变动」要不要按科目范围收窄；收窄后报表说明行是否同步 | `closing.py:383-392` 过滤只有 company、posting_date、`voucher_type != MECV`、creation；`stock_controller.py:1951-1966` 有 repost |
| P5-02 | 低 | `closing.py:404`、`balance_sheet.py:83` | 1901 余额用 `_one_account(company, "1901")` 取，要求恰好一个明细科目。会计若按国内习惯把 1901 拆成「流动资产／非流动资产」两个明细（R15 C 回执自己也提到本表缺流动资产那个明细），或 1901 被删、被改号，12 月的 `month_closing_state` 和 12 月资产负债表都会直接抛「科目号 1901 必须恰好对应一个明细科目」。报错是明的，不静默；但整张 12 月报表打不开 | §4.11 第 4 条（不静默已满足）；可用性 | 改成 `gl_sums(..., accounts=leaf_accounts_under(company, "1901"))` 合计所有明细，与 `_vat_transfer_rows` 取 `2221000` 组的写法一致 | 本Session修（两行，可顺手） | — | `ledger.py:107-130`；`closing.py:79-83` |
| P5-03 | 低 | 上游兜底路径；app `README.md:127` | `stock_adjustment_account` 在上游不只用于盘点。Stock Entry 的物料若没有物料默认、物料组默认费用科目（`stock_entry.py:2726-2747`，例如会计新建的物料组），Material Issue／Receipt 就落 1901；BOM 与 Stock Entry Type 带出的默认（`bom.py:1606`、`stock_entry_type.py:321`）、委外收货分摊损失（`subcontracting_receipt.py:944`），以及**服务端**建的 Opening Stock 盘点（`stock_reconciliation.py:68-71`，不分 purpose 都取它）也落 1901。界面上的 Opening Stock 走 `get_difference_account`，取第一个 Temporary 科目：演示站是 `9999 临时开账科目`（权益类），没问题。以前这些路径落 400103（生产成本），现在落「其他非流动资产」。年末检查会抓到，不静默，但年中各月的资产负债表分类不对；领料挂在 1901 也不合会计习惯。README 只写了盘点 | DEC-122 的适用范围（讨论记录列了这些兜底，但没给对策）；需求 §4.4.4 | README「已知限制」补一句：新建物料组须设公司默认费用科目，否则领料、入库差额会落 1901；或者自检列出没有本公司默认费用科目的物料组 | 新Session修（文档）／延迟（自检） | 要不要把物料组缺默认科目纳入自检 | 演示站实查：5 个内置物料组都有默认费用科目；全站 SLE＝0 |
| P5-04 | 低 | `patches/fd004_default_accounts.py:25-29`；`selfcheck.py`（DEC097_FIELDS） | 读码确认缺目标科目的分支不会中断 migrate：`frappe.log_error(title=, message=)` 不抛错，标题没有换行，traceback 取 message；`print` 会出现在 migrate 输出里。但补丁照样执行成功、记入 Patch Log（`patch_handler.py:187-191`），以后**不会再跑**。`check_company_chart` 又不查这两个字段，所以这家公司以后补建了 1901 也一直停在 400103／1606，只剩那条 Error Log 提醒。这个分支也没有测试 | R15 TS-023「不静默」；R7 总纲 §十 不静默 | ① 加测试：`patch` `_account_name` 让新科目返回 None，断言字段不变、Error Log 增 1 条；② 可选：自检对这两个字段改查「不是旧值」或「科目号符合 json」 | 本Session修（①）／延迟（②） | 自检要不要覆盖全部 22 个默认科目 | 实际触发要求本表公司缺 1901 或 5711010；科目表按原字节入库（IT-035），概率很低 |
| P5-05 | 观察 | 测试 | 判别力缺口：(a) `test_default_accounts_satisfy_upstream_filters` 在 DEC-125 后对 stock_adjustment 一项已经不查任何属性，只改回这一项也能过。建议把例外改成「正向断言偏离」：`root_type == "Asset"`、`report_type == "Balance Sheet"`。(b) `test_fd004_patch` 的「标准公司不动」有两道闸（`is_cn_chart`、`not old`），去掉任一道测试都过，测不出 `is_cn_chart`。(c) 缺科目分支未测（同 P5-04）。(d) `test_pending_property_loss_at_year_end` 末尾断言的是**同一年**的 1 月 complete，与「跨年 1 月不受上年 12 月影响」无关：这一点代码按构造成立（`range(1, 1)` 为空），断言并不证明它。(e) postings 测试里 `db_set("depreciation_cost_center")` 多余，可能掩盖建账漏设（演示站实查已设 `主 - HDTH`，上游 `company.py:741` 会设，目前没有缺陷） | 方案 TS-023「名单之外任何一项不满足即失败」的本意 | (a) 加正向断言；(b) 可接受，或另造一个带 400103 号科目的非本表公司；(d) 删掉或改注释 | 本Session修（a、c），其余可不修 | — | 测试源码 |
| P5-06 | 观察 | `closing.py:297-298`；`zh.csv:52` | 报错拼接：① 连接符 `"；"`、`"，"` 写死为全角，不经 `_()`，en 会话下中英混排；② 「变动」那条 issue 的译文自带「，」，与连接符同形，例如「2 月：结转后该月又有凭证变动（新增或取消），请取消本月结转后重新生成，损益科目月末余额不为 0」，看不出几条原因；③ 拦 3 月生成时，「请取消**本月**结转」读起来像让取消 3 月；④「10 月：2026 年 10 月尚未结转」月份重复 | §4.11（中文合规已满足），可读性 | 原因之间用「；」、月份之间换行或用「｜」；issue 译文的「本月」改「该月」 | 新Session修 | — | 测试 `test_closing.py:451` 已锁定「10 月：{year} 年 10 月尚未结转」，改文案要同步测试 |
| P5-07 | 观察 | `balance_sheet.py:85` | 说明行金额是「借−贷」：盘盈未处理（贷方余额）显示「尚有余额 -20.00」，没写借贷方向，会计要自己推 | 可读性 | 改为「借方 x」／「贷方 x」 | 新Session修 | — | — |
| P5-08 | 观察 | app `README.md:127-128`；D 回执行号 | R15 TS-023 要求在「偏离」处补一行；D 写进了「已知限制」，内容准确。但「相对 zelin 的修改 → 科目表、税与默认科目」表没有登记「zelin 的 400103／1606 被换成 1901／5711010」这一处抄后改；新条目后面多一行空行，把列表断成两段。D 回执 TS-024／025 的行号与提交后的代码不符 | README 是 zelin 差异的登记处 | 修改表补一行；删空行 | 新Session修 | — | — |
| P5-09 | 观察（会计，草案·待领域专家确认） | DEC-123 | 处置有净收益时记为 5711010 的负数，利润表第 22 行「营业外收入」不含这笔利得，第 24 行变小。按《小企业会计准则》，固定资产清理的净收益应转营业外收入。DEC-123 已知并接受，LG-154 待确认，本片不另立修法 | 小企业会计准则 1606 科目说明（AI 推断） | 维持，随 LG-154 一并确认 | 延迟或不修 | 客户会计是否接受 | C 讨论记录 ② |
| P5-10 | 观察 | `closing.py:405`；`ledger.py:38` | 年末 1901 检查经 `gl_sums`，只取空账簿；带 finance book 的 1901 分录看不到。`_assert_no_finance_book_pl` 只拦损益类，不覆盖 1901 | 与 FD-013 同类 | 随 FD-013（本 Stage 不支持账簿）一并说明即可 | 延迟或不修 | — | — |

### 开放查漏逐点结论（任务 4 所列各点）

| 点 | 结论 |
|---|---|
| 12 月 1901 的余额口径 | `gl_sums(to_date=end)` 不带 from_date，走 `posting_date <= end`，含全部以前年度和 `is_opening=Yes` 的分录，剔除已取消的，只取空账簿。口径是「截至年末的累计余额」，正确。账簿缺口见 P5-10 |
| `_one_account` 遇到多个 1901 明细 | 抛错，不静默，见 P5-02 |
| `month_closing_state` 在循环里调 N 次 | 只读：几次 `get_all`、`gl_sums`、`exists`，没有写，也没有缓存副作用。`_incomplete_previous_months` 最多调 11 次，从不传 12，所以 1901 检查不影响任何月份的生成，符合方案「只影响 12 月自身」 |
| DEC-121 空月不拦 | 保留：`closed` 定义没改（`:369`），空月 vouchers 为空，跳过变动／余额检查；`test_empty_month_does_not_block` 有判别力 |
| 1901 设为默认后，上游首次 Stock Reconciliation（全站无 SLE，当作期初）的差额科目校验 | `validate_expense_account` 只拒 `report_type = Profit and Loss`（`stock_reconciliation.py:981-990`），1901 是资产负债表类，能过；GL 的 `is_opening` 只有 purpose 为 Opening Stock 时才是 Yes（`stock_controller.py:982`）。服务端 Opening Stock 不带差额科目时会落 1901，见 P5-03 |
| 报废时 `disposal_account` 的取值 | `get_asset_details` → `get_disposal_account_and_cost_center`（`depreciation.py:781-791`），读 Company 字段，`depreciation_cost_center` 必填；出售资产时，销售发票行的 income_account 也取它（`sales_invoice_item.py:128-135`）。5711010 在本表的 account_type 是 Fixed Asset（zelin 原值），上游没有按这个类型拒绝它的地方 |
| 跨年 1 月不受上年 12 月 1901 影响 | 按构造成立（`range(1, 1)` 为空），符合方案；测试并没有证明这一点（P5-05(d)）。上年 12 月不完整、新年照常结转，属 FD-032（已裁延迟），不重复立项 |
| 报错消息中文拼接格式 | 见 P5-06 |
| DEC-125 在 README 写准没有 | 准，含过滤只在永续盘存下生效这一前提（HDTH 是 1）。位置与空行见 P5-08 |

## 建议主会话实跑的变异清单

| # | 改哪一行 | 预期失败的测试 | 目的 |
|---|---|---|---|
| M1 | `closing.py:403`：把 `if month == 12:` 改成 `if month == 12 and closed:` | `test_pending_property_loss_at_year_end`（生成前 `:458` 的断言） | 证明「未结转的 12 月也提示」被测到 |
| M2 | `closing.py:403`：去掉月份条件（改 `if True:`） | `test_pending_property_loss_midyear_does_not_block`；`test_pending_property_loss_year_end_note` 的 6 月断言 | 证明「只限 12 月」被测到 |
| M3 | `closing.py:115`：`if not state["complete"]` 改 `if not state["closed"]` | `test_supplement_after_closing_blocks_next_month`、`test_multiple_incomplete_months_listed` | 和 D 的 TS-025 变异是两种写法，证明拦的是「不完整」而不只是「未结」 |
| M4 | `closing.py:297`：`"，".join(issues)` 改 `""` | `test_supplement…`（「结转后该月又有凭证变动」）、`test_incomplete_message_in_chinese` | 原因是否真写进消息 |
| M5 | `closing.py:369`：`or not _pl_has_activity(...)` 删掉 | `test_empty_month_does_not_block` | DEC-121 |
| M6 | 补丁 `:21`：删掉 `or current != old` | `test_fd004_patch` 的第三科目断言（`:128`） | 「被人改过的不动」 |
| M7 | 补丁 `:16-17`：删掉 `is_cn_chart` 两行 | **预期全部通过** | 证明 P5-05(b)：非本表公司这道闸没被测到 |
| M8 | 补丁 `:27-29`：换成 `pass` | **预期全部通过** | 证明 P5-04：缺科目分支没被测到 |
| M9 | `company_defaults.json:11` 单独改回 `"400103"`（16 行保持 5711010） | `test_default_account_numbers_match_r15`、`test_stock_gain_transfer_and_loss` 失败；**`test_default_accounts_satisfy_upstream_filters` 预期通过** | 证明 P5-05(a) |
| M10 | `balance_sheet.py:85`：`_money(debit - credit)` 改 `_money(0)` | `test_pending_property_loss_year_end_note` | 金额真取自 1901 |

每跑一组都要恢复，之后核对 `git -C frappe-bench/apps/frappe_china diff 21faeb9` 为空。

## 业务规则合规核表

| 规则 | 本片涉及否 | 结论 | 说明 |
|---|---|---|---|
| BR-001 执行《小企业会计准则》 | 是 | 合规（未经专家确认） | DEC-122／123 按小企业准则附录 1901／1606 推定 |
| BR-002 报表组成 | 否 | — | 没有改动 |
| BR-003 增值税税率 | 间接 | 合规 | 没改税率；DEC-124 防止补录的销项被算进下月 |
| BR-004 增值税月末转出 | 间接 | 合规（未经专家确认） | 补录上月发票后下月被拦，转出金额不再跨月（A12-1／2） |
| BR-005 附加税 | 间接 | 合规（未经专家确认） | 同上，计税依据不跨月 |
| BR-006 资产负债表平衡 | 是 | 合规 | 盘盈后报表照样平衡、不出勾稽不符（A11-3）；「平衡」不等于「分类正确」，P5-03 的兜底路径照样平衡 |
| BR-007 价税分离 | 否 | — | — |
| 草案·待领域专家确认：存货盘盈盘亏先记「待处理财产损溢」，批准后盘盈转营业外收入、盘亏扣残料与赔偿后转营业外支出 | 是 | 合规（DEC-122） | 上游一张单据一个差额科目，经 1901 中转是唯一能让两个方向都落对的选法；非正常损失要做的进项税额转出也可以在转出分录里手工带上 |
| 草案·待领域专家确认：待处理财产损溢年末结账前处理完毕、无余额 | 是 | 合规（不静默） | 12 月状态与报表说明都会提示；不强拦年末结转，符合「提示不代判」 |
| 草案·待领域专家确认：1901 年中余额列「其他非流动资产」 | 是 | 存疑 | 本表 1901 只有「非流动资产」明细，存货差额挂在这里名不副实；财政部填列说明没对过（LG-154） |
| 草案·待领域专家确认：非流动资产处置净损失进营业外支出、净收益进营业外收入 | 是 | 部分合规 | 净损失合规；净收益记成营业外支出负数（P5-09，DEC-123 已认） |
| 草案·待领域专家确认：账结法下逐月结转，上月结转不完整不得结下月 | 是 | 合规（DEC-124） | 拦截范围偏宽，见 P5-01 |
| 草案·待领域专家确认：无损益发生额的月份不算未结（DEC-121） | 是 | 合规 | 保留 |

## 交接摘要

**本片依赖**：
- 分片 1（建账／自检／默认科目）：`_account_name` 取「本公司＋科目号＋非组」的第一条（`company.py:86-90`），依赖每家公司科目号唯一；`check_company_chart` 只查 DEC097 六项。
- 分片 2（closing.py）：`month_closing_state` 的 `closed` 定义与「变动」判据（`:369-397`）沿用 R7／R14，本片没重审它们本身的正确性。
- 分片 3（报表映射）：1901 经组科目 1900 计入资产负债表第 28 行（`mapping.py:68`），5711010 经 5711 计入利润表第 24 行，5301050 经 5301 计入第 22 行。

**本片暴露给**：
- 分片 2：P5-01（「变动」判据被 DEC-124 放大成硬拦，请从结转正确性角度判断收窄后会不会漏）；P5-02（`_one_account` 用在 1901 上）；P5-06（拼接文案）；P5-10（账簿）。
- 分片 3：P5-03（兜底路径落 1901，年中第 28 行会混入非盘点差额）；P5-07（说明行金额方向）；请确认第 28 行出现负数（贷方余额）在法定格式上可以接受（R15 C 回执复核建议 2，LG-154）。
- 分片 1：P5-04（补丁缺科目后不再重试，自检不覆盖这两个字段）；P5-05(e)（`depreciation_cost_center` 由上游 `create_default_cost_center` 设定，本表建账路径要确认一直生效，演示站已设）；Existing Company 克隆公司 `chart_of_accounts` 为空，补丁会跳过它（与 R14 P1-03 同源，不另立项）。

## 盲区自述与把握最低处

- **没跑任何测试和变异**：判别力结论全部来自读码；M7、M8、M9 的「预期通过」是推断，要主会话实跑确认。
- **P5-01 的严重度**取决于会计实际怎么补录（银行流水晚导入有多常见）；我按本 Stage 有银行对账模块推断「常见」，没有业务证据。
- **会计口径**（DEC-122／123、第 28 行负数、1901 名称不符）全部是 AI 按准则附录推断，没有对照财政部报表填列说明原文，全部标「草案·待领域专家确认」。
- **上游 repost** 会重建后续凭证的 GL，这条只读到 `repost_future_sle_and_gle` 的入口，没追 Repost Item Valuation 生成的 GL creation 时间，属推断。
- 演示站备份的完整性（gzip／tar）没复做。
- 把握最低的是 P5-03：Stock Entry 兜底依赖「物料与物料组都没有本公司默认费用科目」，演示站 5 个内置物料组都设了，实际触发面取决于客户以后怎么建物料组。
