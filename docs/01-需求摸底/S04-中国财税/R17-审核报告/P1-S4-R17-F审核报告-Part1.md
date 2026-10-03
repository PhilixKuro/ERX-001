# 审核报告·Part1（复核轮）（对象：frappe_china Part1 范围的已修项与连带改动 / 审核标准：R7 开发方案 Part1＋总纲、R15 开发方案、B 需求文档、R14 F 审核报告）

**轮次**：P1-S4-R17｜**步骤**：`plannedDev` F（audit，回 F 复核），分片 1｜**日期**：2026-10-03｜**执行者**：Claude 子 Agent（Opus 5.5，只读）
**依据**：R7 `P1-S4-R7-C开发方案-Part1.md`（全文）、`-总纲.md`（全文）；R15 `P1-S4-R15-C开发方案.md`（全文）与 C 讨论记录（DEC-122／123）；R16 D 回执与 D 讨论记录（DEC-125）；需求 §4.3、§4.4（含 4.4.1–4.4.4）、§4.5、§4.6.1；`docs/业务规则.md`；`docs/开发守则.md`（静默失败、探针判别力两节）；R14 F 审核报告主报告（FD-003／004／008／028／037–040 各行、当场修清单、变异表）与 `-Part1.md` 分片报告（全文）；R14 SB 修复回执（全文）
**被审范围**：`frappe-bench/apps/frappe_china`，基线 `40200dc` → 被审 `21faeb9`（HEAD＝`21faeb9`，工作区干净）；其中 Part1 相关文件的 diff。上游对照 `apps/erpnext`、`apps/frappe`。站点只读 SQL：`test.localhost`、`erx.localhost`
**本片要复核的已修项**：FD-003（F 当场修）、FD-028（SB）；FD-004 对 Part1 的连带影响；延迟项 FD-008／037／038／039／040 只核「没有变得更糟」

## 覆盖自证（实际查了哪些、跳过哪些及原因）

**逐行读过的代码（`21faeb9`）**：`frappe_china/install.py`、`accounting/install.py`（第 1–6、55–83 行，CN_UOMS 段未变未重读）、`accounting/company.py`（全文）、`cn_tax/data/company_defaults.json`（全文）、`patches.txt`、`patches/fd004_default_accounts.py`、`tests/test_install.py`（全文）、`tests/test_company.py`（全文）、`tests/test_default_account_postings.py`（全文）；`README.md` 的 diff 与第 66–75、127 行。

**diff 范围**：`git diff 40200dc 21faeb9` 全量 `--stat`（42 个文件）；逐行看了 Part1 相关的 `install.py`、`company.py`、`company_defaults.json`、`patches.txt`、`patches/`、`hooks.py`、`tests/test_install.py`、`tests/test_company.py`、`README.md`。确认 `accounting/selfcheck.py`、`accounting/taxes.py`、`accounting/chart.py`、`cn_tax/data/tax_setup.json`、`tests/utils.py`、`tests/test_selfcheck.py`、`tests/test_taxes.py`、`tests/test_e2e_minimal.py`、`tests/test_chart.py` 在两个基线之间**无改动**。

**对照读过的上游**：`global_defaults.py`（全文）；`frappe/defaults.py` `set_default`／`add_default`；`database.py` `set_single_value`／`get_single_value`／`value_cache`；`model/document.py` `clear_document_cache`、`get_single`；`company.js:279-363`（字段过滤与 `set_custom_query` 的 AND 合成）；`company.py` `validate`、`validate_default_accounts`、`on_update` 第 344–374 行、`create_default_accounts`、`set_default_accounts`、`_set_default_account`、`validate_coa_input`、`set_chart_of_accounts`；`company.json` 中 `enable_perpetual_inventory` 默认值（1）；`stock_reconciliation.py` `validate`、`validate_expense_account`、`get_difference_account`；`stock_entry.py:2665-2750、3377-3396`；`stock_entry_utils.py:125-135`；`stock_entry_type.py:310-330`；`bom.py:1595-1615`；`subcontracting_receipt.py:935-950`；`depreciation.py:636-700、780-790`；`sales_invoice_item.py:128-138`；`sales_invoice.py:458-460、1813-1827`；`accounts_controller.validate_account_head`；`stock_controller.check_expense_account`；`installer.py:358-361`（新装时全部 patch 标记为已执行）；setup wizard 的 `defaults_setup.py`、`install_fixtures.py` 中 Global Defaults 的保存。

**站点只读查询**：两站 `tabDefaultValue`（`__default` 下 country／currency／company／disable_rounded_total 等）、`tabSingles` 的 Global Defaults 全部字段与 System Settings.country、8 类单据 `rounded_total` Property Setter、`tabPatch Log` 的本 app patch；演示站 HDTH 的 22 个默认科目逐项 `root_type／report_type／account_type／is_group／disabled`、仓库科目、物料组 Item Default、`account_type = Stock Adjustment`／`Temporary` 的科目清单、Account 266、Stock Reconciliation 0、Error Log 中迁移失败记录 0、`round_row_wise_tax`；测试站 Company 0、迁移失败日志 0。科目表 JSON 只读解析：1606／1901／4001xx／5301xx／5711xx 的 root_type／account_type／is_group。

**跳过及原因**：
- 未跑任何测试、变异、migrate、`bench execute`（硬约束：主会话正在测试站跑全量回归）。「测试能否抓住原缺陷」全部是读码推演，变异结论沿用 R14／SB／R16 回执所报，未复核。
- 未在全新站点上实装一次 app（写操作），FD-003「新装不再删 country」只有读码与测试代码推演，两站的现状是 R14 当场修的数据修复结果，**不能作为代码修复生效的证据**。
- FD-004 本体（closing 年末提示、balance_sheet 说明行、mapping）归分片 5，只读了与 Part1 交界的部分（`company_defaults.json`、patch、`test_company` 两条新测试、`test_default_account_postings`）。
- `accounting/install.py` 的 `CN_UOMS` 段、`chart.py`、`taxes.py`、`selfcheck.py` 无改动，未重读，沿用 R14 Part1 结论。

## 已修项复核表

| FD 号 | R14 判定标准 | 定位（文件:行） | 落地 | 生效否 | 原问题消失否 | 自证一致否 | 说明 |
|---|---|---|---|---|---|---|---|
| FD-003 | 改用 HT-005 备选写法（`set_single_value`＋`set_default`＋显式 `toggle_rounded_total()`），不走整单 `save()`；安装测试快照加 `tabDefaultValue`；两站补回 `country=China` 并把 `Global Defaults.country` 填为 China | `accounting/install.py:70-83`；调用链 `hooks.py:89` → `install.py:1-5` → `disable_rounded_total()`；测试 `tests/test_install.py:83-104` | ✅ | ✅ | ✅（代码层）；两站数据层 ✅ | 一致 | ① 读码：新路径只写 `disable_rounded_total` 一个 Singles 值和同名默认值，不再触发 `GlobalDefaults.on_update`，`country` 等其余 6 个键不被重写。`set_single_value` 内调 `clear_document_cache` 清了 `value_cache`，随后的 `get_single` 取到的是新值 1，`toggle_rounded_total` 建出的 Property Setter 与原先相同。② 全仓再无 `Global Defaults` 的 `save()`。③ 测试判别力：推演旧代码——`on_update` 会 `set_default("country", "")`，`set_default` 遇到旧值 China ≠ "" 即删再插 ""，`defaults()` 前后不等，断言失败；与 R14 变异 M4 的报告一致。④ 两站实查：`tabDefaultValue.country=China`，`Global Defaults.country=China`（两站 `modified` 10-02 22:05，即 R14 当场修时刻），Property Setter 8 类齐全。⑤ 与旧写法的差异：不再调 `toggle_in_words()`、不再启用默认币种，见 P1-05（无功能影响）。⑥ 建站脚本没跟进 `Global Defaults.country`，见 P1-04 |
| FD-028 | 仓库科目与物料组科目按科目号查不到时报错、不写 NULL；与默认科目那段同法「先收齐缺项再 `frappe.throw`」 | `accounting/company.py:109-114`（`_throw_missing_accounts`）、`:117-130`（仓库）、`:133-171`（物料组）；调用 `build_cn_company` `:80-81`；测试 `tests/test_company.py:257-276` | ✅ | ✅ | ✅ | 一致 | ① 两段都先查全部科目号、收齐缺项，**全部查到后才写**（`:129-130`、`:158-171`），与 SB 回执「通过后才写」相符；报错源词与默认科目同一条（`zh.csv:99` 有译文）。② 异常从 `on_update` 抛出、经 `raise` 让插入失败，公司回滚；测试断言公司不存在。③ 测试判别力：`patch` 的是模块全局 `_account_name`，只对目标号返回 None；旧代码不报错，`assertRaises` 失败，能抓住原缺陷。第二组断言子串 `"=400102"` 偏弱（没有带上物料组名），但足以区分新旧。若测试站缺 `Services` 物料组，该组会被跳过而不报错，测试会**失败**而不是误通过，不构成假阳性。④ 缺物料组本身仍只记 warning，属原方案（§4.4.4），SB 回执已写明不在本项范围 |

### FD-004 对 Part1 其余部分的连带影响（代码本体归分片 5）

| 检查点 | 结论 | 依据 |
|---|---|---|
| 新科目号在本表中是明细 | ✅ | JSON：`1901`（Asset，account_type 空，is_group 0）、`5711010`（Expense，`Fixed Asset`，is_group 0）；`_account_name` 要求 `is_group=0`，取得到 |
| `set_cn_default_accounts` 缺项报错路径 | ✅ 不受影响 | 22 项仍走同一循环；新号能查到，不会触发 |
| 自检 `selfcheck` | ✅ 不受影响 | `DEC097_FIELDS` 只含 6 个 DEC-097 字段，不含这两个字段；`selfcheck.py` 无改动；R16 回执与演示站自检 `ok=True` 一致 |
| 漏科目 | ✅ | 科目表 JSON 未动（Account 266）；`test_default_account_postings.py:34-36` 断言 1901／5711010 不在漏科目里（Part3 职责，只读到断言） |
| 其余 20 个默认科目 | ✅ 未变 | json diff 只动两行；演示站 HDTH 22 项逐项实查：除 `stock_adjustment_account` 外全部满足 `company.js` 过滤，`disposal_account=5711010` 为 Profit and Loss |
| 仓库科目、物料组科目、付款方式、税 | ✅ 未变 | json 其余段、`taxes.py`、`tax_setup.json` 无改动；HDTH 实查成品 1405、在制品 1409、五个物料组科目与 R14 相同 |
| 建账总测试 `test_cn_company_builds_complete_chart_and_defaults` | ✅ 自动跟随 | 按 `DEFAULT_ACCOUNT_NUMBERS` 逐项断言，取自同一 json |
| 新增 `test_default_accounts_satisfy_upstream_filters` 的过滤常量 | ✅ 与上游一致 | 逐项对 `company.js:281-338`：22 项条件相同；永续盘存默认开（`company.json` 默认 1），故 `stock_adjustment_account`／`stock_received_but_not_billed` 两条也适用。例外名单使该字段完全不被此测试检查，见 P1-01 |
| patch 对新装站点 | ✅ 无副作用 | `installer.py:358` 新装时把全部 patch 标为已执行，patch 只在已有站点 migrate 时跑；两站 `Patch Log` 各 1 行、迁移失败日志 0 |
| 上游其它以 `stock_adjustment_account` 兜底的路径 | ⚠️ 见 P1-02 | 委外收货分摊损失、库存凭证行缺费用科目、BOM／Stock Entry Type 兜底，都会落 1901 |
| `Existing Company` 克隆路径 | ⚠️ 见 P1-03 | 上游按 `account_type` 取到的仍是 `400103` |

### 延迟项（只确认没有变得更糟）

| FD 号 | 相关文件是否被改 | 结论 |
|---|---|---|
| FD-008 克隆／子公司半套建账 | `company.py` 的 `_takes_cn_path`／`before_insert` 未改；`selfcheck.py` 未改 | 未变糟。FD-004 的修复没有覆盖这条路径，克隆公司的库存调整科目仍是 `400103`，见 P1-03，建议并入该延迟项的登记 |
| FD-037 税类别与规则对不齐 | `tax_setup.json`、`taxes.py` 未改 | 未变 |
| FD-038 多行发票舍入颗粒度 | 演示站 `round_row_wise_tax=0`，未改 | 未变 |
| FD-039 保存点回滚不复位标志 | `company.py:34-65` 未改 | 未变 |
| FD-040 `get_chart(existing_company=)` 不查权限 | `chart.py` 未改 | 未变 |

## 开放查漏新发现

| 片内编号 | 严重程度 | 定位 | 问题 | 违背的标准 | 建议修法 | 建议档位 | 待裁决点 | 证据 |
|---|---|---|---|---|---|---|---|---|
| P1-01 | 观察 | `tests/test_company.py:70-110`（`exceptions` 第 98 行） | 例外名单 `{"stock_adjustment_account": {"root_type", "account_type"}}` 把该字段过滤里的两个条件都豁免了，所以这条测试对 `stock_adjustment_account` 只剩「属本公司、非组科目」两项检查。默认科目改回 `400103` 或改成任何明细科目，这条测试都会通过。目前由 `test_default_account_numbers_match_r15`（第 65-68 行）与记账测试兜住，**整体判别力够**，但 R15 SL-011 ② 写的「名单之外任何一项不满足即失败」对这个字段落空了 | R15 SL-011 验收 2 的意图；开发守则「探针判别力」 | 对例外字段改为正向断言它的预期属性，例如 `report_type == "Balance Sheet"` 且科目号为 1901，让这条测试本身也能抓住改动 | 延迟或不修 | 是否值得为这一个字段补正向断言 | 读码：`exceptions.get(field)` 跳过 `root_type`／`account_type` 后 `conditions` 已无剩余项 |
| P1-02 | 低 | `cn_tax/data/company_defaults.json:11`；上游 `subcontracting_receipt.py:942-944`、`stock_entry.py:2741-2749`、`stock_entry.py:3393`、`stock_entry_utils.py:133-134`、`bom.py:1607`、`stock_entry_type.py:321` | **`1901` 除了收盘点差额，还会收到上游另外几处的兜底分录**：委外收货的分摊损失；库存凭证（物料入库等）里物料与物料组都没有费用科目的行；按 BOM／库存凭证类型带出的默认费用科目。这些都不是「待处理财产损溢」的性质，但会和盘点差额混在 1901 里，12 月触发年末提示，会计又看不出来源。R15 C 讨论记录 ① 的「查证的事实」列出了这三处用法，但 DEC-122 的结论、R15 方案和 README 都没有交代它们的去向。与改前相比不算回归（`400103` 同样是资产负债表科目），本 app 配好的 5 个物料组也挡住了最常见的情形；用户自建的物料组（例如按弹簧品类建的组）没有 Item Default，就会走到兜底 | 开发守则「静默失败」；需求 §4.4.4 的意图（默认科目要可解释） | README「已知限制」补一句：1901 还会收到上游以库存调整科目兜底的分录（列出这三处），年末提示时要逐笔查来源；或在 S7 造数据／物料组建档时要求每个物料组都设费用科目 | 新Session修 | 只登记，还是另给委外损失指定科目（属 FD-004 的口径，交分片 5 与用户定） | 上游代码行见定位列；演示站 `account_type = Stock Adjustment` 的只有 `400103` |
| P1-03 | 观察 | 上游 `company.py:346-365、412-415、625-645`；`patches/fd004_default_accounts.py:15-17`；本 app `company.py:26-31` | **FD-004 的修复没有覆盖以本表公司为源的克隆公司。** 选 `Existing Company` 时 `chart_of_accounts` 被清空，走原生建账；原生 `set_default_accounts` 按 `account_type = Stock Adjustment` 取第一条，本表里只有 `400103`，于是克隆公司的库存调整科目仍是 `400103`；`disposal_account` 按名字 `Gain/Loss on Asset Disposal` 取不到，为空，资产处置时上游会报错。patch 也因 `is_cn_chart(None)` 为假跳过这类公司。FD-008 本就判为延迟，本轮没有让它更糟，只是 FD-004 的问题在这条路径上原样存在 | RS-014；FD-008 的待定规则 | 不在本轮修。在 FD-008 对应的延迟登记里补一句「克隆公司也带 FD-004 的旧科目、处置科目为空」，多公司立项时一并定 | 延迟或不修 | 是否在登记册里补这一句 | 读码；JSON 中 `account_type = Stock Adjustment` 只有 `400103`（演示站实查同） |
| P1-04 | 低 | `docker/scripts/seed-demo.sh:105-128`（`--bare` 段）；上游 `global_defaults.py:45-48` | **FD-003 的数据修复只落在现有两站，建站脚本没跟进。** `seed-demo.sh --bare` 只写 System Settings 的 country，不写 `Global Defaults.country`。按脚本重建测试站或演示站后，`Global Defaults.country` 又是空的。本 app 现在不会再删 `country` 默认值，但之后任何人在界面上保存一次 Global Defaults（上游行为），`country` 默认值又会被清空，FD-003 的症状会复现。R14 当场修专门把两站的 `Global Defaults.country` 填成 China，就是为了防这一点，这层防护不能随建站重放 | FD-003 的修复意图（R14 当场修清单第 3 条「防此后界面保存时再被上游删掉」）；TS-001 测试站的可重建性 | `seed-demo.sh` 写 System Settings.country 的地方，同时 `frappe.db.set_single_value("Global Defaults", "country", "$COUNTRY")`（不走 `save()`） | 新Session修 | 是否算本 Stage 的事（脚本归基础设施，TS-001 在 Part1） | 两站 `Global Defaults.country=China`（`modified` 10-02 22:05 手工修）；`seed-demo.sh` 全文无 `Global Defaults` 的 country 写入（grep） |
| P1-05 | 观察 | `accounting/install.py:77-83` 对比上游 `global_defaults.py:45-57` | 新写法不再调 `toggle_in_words()`、不再启用默认币种。旧写法在 `disable_in_words=0` 时会为 8 类单据建 `in_words` 的 `hidden=0`／`print_hide=0` Property Setter，与字段默认值相同。所以**没有功能差异**，也符合需求 §4.3「不做 `disable_in_words`」 | — | 无须改。记一行，供以后对比两种安装结果时不误判 | 延迟或不修 | 无 | 读码 |

## 业务规则合规核表

（BR 均「未经专家确认」；AI 推断的规则另标「草案·待领域专家确认」）

| 规则条款 | 本片是否涉及 | 结论 | 备注 |
|---|---|---|---|
| BR-001 准则为《小企业会计准则》，「(2024)」只是文件名 | 是（科目表、默认科目） | 合规 | 科目表未动；README 新增行只称科目名 |
| BR-002 报表组成与编报期 | 否 | — | Part3／Part4 |
| BR-003 税率与征收率 | 是（税模板） | 合规（未变） | `tax_setup.json` 无改动；R14 的草案（`P0无税` 同时承接零税率与免税）仍待确认 |
| BR-004 增值税月末结转 | 否 | — | Part2 |
| BR-005 城建税与附加 | 否 | — | Part2 |
| BR-006 资产负债表平衡 | 间接（1901 进资产负债表第 28 行） | 合规 | 盘点差额在资产与 1901 之间对记，平衡不受影响。**草案·待领域专家确认**：存货盘盈盘亏挂账属流动资产性质，本表只有「1901 待处理财产损溢_非流动资产」一个明细，年中挂在「其他非流动资产」行是否可接受；交分片 3／5 与报表映射一并看 |
| BR-007 价税分离、按分舍入 | 是（税模板） | 单行合规（未变） | 多行颗粒度的草案同 R14 FD-038，未变 |
| R14 草案「存货盘盈盘亏、资产处置损益应进损益」（**草案·待领域专家确认**） | 是（两个默认科目） | 部分合规 | ① 资产处置：净损益一步进 `5711010` 营业外支出，进了损益 ✅；但**净收益**会记成营业外支出的负数，准则口径是净收益进「营业外收入」（`5301010`）。DEC-123 已知此代价、以「损失为主」取舍。② 盘盈盘亏：先挂 1901，靠会计手工转营业外收支，12 月有提示 ✅（经人工环节合规）。另见 P1-02：1901 还会收到非盘点性质的兜底分录 |
| 需求 §4.3「装 app 只做两件事」 | 是 | 合规 | 新写法只写凑整开关与对应 Property Setter，不再连带重写其余 6 个系统默认值 |

## 交接摘要

**本片依赖别片**
- 分片 5（FD-004 本体）：`closing.py` 年末 1901 提示、`balance_sheet.py` 说明行、`mapping.py` 第 28 行取数、patch 缺目标科目分支——本片只核了与 `company_defaults.json` 的接口，结论以分片 5 为准。
- 主会话全量回归结果（149 项）：本片对 FD-003／FD-028 测试判别力的判断是读码推演，需要实跑结果佐证。

**本片暴露给别片**
- `company_defaults.json`：`stock_adjustment_account=1901`、`disposal_account=5711010`；其余 20 项与 R14 SB 后相同。
- `_account_name(company, number)` 现被 `patches/fd004_default_accounts.py` 跨模块引用（私有函数），改它的签名会连带影响 patch。
- `_throw_missing_accounts` 的报错源词与默认科目段相同：`Company {0} is missing required accounts: {1}`。
- 给分片 5：P1-02（1901 收到上游兜底分录，影响年末提示的可解释性）、P1-03（克隆公司仍是 `400103`，patch 跳过）。
- 给分片 3／5：BR-006 草案（1901 年中挂「其他非流动资产」行是否可接受）。
- 给负责基础设施／Part4 的分片：P1-04（`seed-demo.sh` 未写 `Global Defaults.country`）。

## 盲区自述与把握最低处

- **没跑任何东西**。FD-003、FD-028 的「测试能抓住原缺陷」是按上游 `set_default` 的删插逻辑和 mock 的作用面推演出来的，与 R14／SB 报的变异 M4、M11 一致，但没有自己复跑。
- **FD-003 在全新站点上的效果没实测**。两站现在的 `country=China` 来自 R14 的手工数据修复，证明不了新代码在新装时不删 `country`。代码层面的结论只靠读码和 `test_install_keeps_system_defaults` 的构造（它先把 `Global Defaults.country` 置空、再调函数，正好模拟新站）。**建议主会话在回归日志里确认这条测试通过。**
- **把握最低的是 P1-02 的影响面**。上游 Stock Entry 各用途（物料入库、制造、委外发料）到底哪些行会真的落到公司兜底科目，取决于物料与物料组有没有费用科目，我只读了取值点，没有逐用途推演 GL；P1-02 的严重程度可能偏高也可能偏低。
- **没往这些方向找**：安装向导路径下的 Global Defaults 保存（会写 country，读码判定不受影响，未实跑）；`Stock Reconciliation` 期初用途下 `get_difference_account` 取 `Temporary` 科目在本表会取到哪一个（上游行为，与本轮改动无关）；HRMS 等其它 app 对 Global Defaults 的保存。
- **拿不准处**：P1-04 算 Part1 的事还是基础设施的事。我放在本片，理由是 TS-001 测试站在 Part1，而且它关系到 FD-003 修复能否随建站重放。
