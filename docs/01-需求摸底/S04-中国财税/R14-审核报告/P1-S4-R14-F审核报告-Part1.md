# 审核报告·Part1（对象：frappe_china Part1 范围 / 审核标准：B 需求文档 + R7 开发方案 Part1）

**轮次**：P1-S4-R14｜**步骤**：`plannedDev` F（audit），分片 1／4｜**日期**：2026-10-02｜**执行者**：Claude（Opus 5.5，只读子 Agent）
**被审代码**：`frappe-bench/apps/frappe_china/`（HEAD `40200dc`）；上游 `apps/erpnext`、`apps/frappe`；站点 `test.localhost`、`erx.localhost`（只读 SQL 与无副作用的 `bench execute`）

## 覆盖自证（实际查了哪些、跳过哪些及原因；不写「全部覆盖」）

**读全的依据**：F Spec、`bricks/audit.md`、`bricks/sharding.md`；方案总纲全文（§二、§五、§六、§七、§十）；Part1 全文；需求 §3.2（DEC 表）、§3.3、§4.1–§4.6、§4.13、§4.14、§4.15、§4.17、§六、§八（AC-001～014 全表）；`docs/业务规则.md`；`docs/开发守则.md`；D 回执 Part1；R9 E 报告 IT 表、R12／R13 E 报告的 IT 表与 R13 逐项表（作为「已核过什么」的索引，不采信结论）。

**逐行读过的代码**：`hooks.py`、`install.py`、`modules.txt`、`patches.txt`、`workspace_sidebar/cn_tax.json`、`accounting/{install,chart,company,selfcheck,taxes}.py`、`cn_tax/data/{company_defaults,tax_setup}.json`、`tests/{utils,test_smoke,test_scaffold,test_install,test_chart,test_company,test_selfcheck,test_taxes,test_e2e_minimal}.py`；`git log --stat` 看 Part1 文件的全部提交改动面（`ad4362b`、`cb93b40`、`8197786`、`dde0a4c`、`ee5fe6a`、`40200dc`）。

**对照读过的上游**：`chart_of_accounts.py`（全文）、`accounts/utils.py:get_coa`、`company.py`（validate／on_update／set_default_accounts／validate_coa_input／set_chart_of_accounts／on_trash）、`company.js` 字段过滤、`global_defaults.py`、`frappe/defaults.py`、`database.py` commit／rollback、`tax_rule.py:get_tax_template`、`taxes_and_totals.py`（含税、行级舍入、凑整）、`taxes_setup.py`、`depreciation.py` 处置科目、`stock_controller.py` 费用科目校验、`treeview.py`、`boot.py` 侧栏与 sysdefaults、`typing_validations.py`。zelin：`company_default/utils.py`、`default_accounts.csv`、`tax_rule.csv`、`setup/install.py`、`hooks.py`。

**站点只读查询**：两站 System Settings／Global Defaults 单值、`tabDefaultValue`（`__default` 全部行）、`tabVersion`（System Settings／Global Defaults）、HDTH 26 个相关科目的 `root_type／account_type／report_type`、各 `account_type` 下的科目清单、Item Group 与 Item Default、Warehouse 科目、Company 默认科目、Accounts Settings `round_row_wise_tax`、Property Setter 时间戳；`bench execute frappe.db.get_default country`（纯读）。

**跳过及原因**：
- 未跑任何测试与变异（硬约束）。全量回归数字采用主会话告知的 113/113，未自行复核；本片「测试只覆盖 happy path」类判断均为读码推演。
- SL-001 ⑥ 断网降级、SL-002 ④ `install-app --force`、TS-008 界面截图：都是写操作或界面操作，未做。`setup.sh` 6.5 段只读了代码（`docker/scripts/setup.sh:242-258`），与方案形态一致。
- 科目表 sha256：R12／R13 已四处核过且本轮无改动，未重算。
- `README.md` 的 zelin 并入登记只抽读了第 17–19、71–86 行（Part1 部分），未逐条与 zelin 全部差异比对（AC-014 归 Part4／TS-020）。
- 未创建临时脚本目录 `frappe-bench/tmp_r14_p1/`（全程只用了单行只读命令），无需清理。

## 逐项落地核查

| 意图层依据 | 要求层要求（方案任务/验收条款逐条） | 定位（文件:行） | 落地 | 生效否 | 偏差说明 |
|---|---|---|---|---|---|
| §4.13 第 2 条；A1 | TS-001 测试站：国家 China／语言 zh／时区 Asia/Shanghai／日期 yyyy-mm-dd／币种 CNY／Commercial Rounding | 测试站 `tabSingles` System Settings | ✅ | ✅ | 六项实查都对（IT-026 已修）。但 `tabDefaultValue` 里已没有 `country` 行，见 P1-01 |
| A1 | TS-001 不加 `--set-default`；演示站只装 frappe／erpnext（清站前） | — | ✅ | — | 演示站已在 TS-021 重装并装了本 app，旧基线无法回溯；沿用 R9 结论 |
| DEC-095 | TS-002 `setup.sh` 6.5 段，失败只告警 | `docker/scripts/setup.sh:242-258` | ✅ | 未实跑 | 形态与方案逐行一致；断网分支未实跑（写操作） |
| DEC-095 | TS-002 `docker/README.md`「中文字体」小节 | `docker/README.md:199` | ✅ | — | 只核到节标题 |
| HT-003 | TS-002 `tests/utils.pdf_text_and_fonts(pdf_bytes) -> tuple[str, list[dict]]` | `tests/utils.py:73-105` | ✅ | Part4 调用 | 签名一致 |
| §4.2 | TS-003 `--no-git` 生成；`modules.txt` 一行 `CN Tax`；删默认模块目录 | `modules.txt:1` | ✅ | ✅ | `git init` 一事 R9 IT-029 已裁「当初许可过」，不重报 |
| §4.2；ADR-0012 | TS-003 同名空侧栏 `CN Tax`；README 写明须与模块名逐字相同 | `workspace_sidebar/cn_tax.json`；`README.md:19` | ✅ | ✅ | `test_scaffold.py:24-31` 用 `get_sidebar_items` 断言无 `cn tax` 键，不是方案写的 `get_bootinfo()`，判别力等价 |
| HT-013 | TS-003 `FrappeChinaTestCase`（zh、Administrator）；不 import `erpnext.tests.utils` | `tests/utils.py:27-34` | ✅ | ✅ | 全仓 Part1 测试均继承它（IT-023 已修）；未见 `erpnext.tests.utils` import |
| TS-003 | `make_cn_company`／`make_std_company`／`TEST_PREFIX` | `tests/utils.py:11,45-70` | ✅ | ✅ | — |
| HT-001 | TS-003 四个中文名报表桩经 `query_report.run` 执行 | `tests/test_scaffold.py:13-20` | ⚠️ | ✅ | 现断言「不带筛选时报 ValidationError」，是 R9 IT-012 裁决后的口径，不重报 |
| TS-003 第 5 条 | 占位测试 `test_smoke.py` | `tests/test_smoke.py` | ✅ | ✅ | 另加了 Module Def 断言，属测试增强，不算夹带 |
| TS-003 第 6 条 | `.vscode/settings.json`、`docs/README.md` 指向 app | `.vscode/settings.json:9`；`docs/README.md:9` | ✅ | — | — |
| §4.3；DEC-100 | TS-004 `CN_UOMS` 45 项照抄 zelin、顺序不变 | `accounting/install.py:7-53` | ✅ | ✅ | 与 zelin `setup/install.py:5-51` 逐项相同 |
| §4.3 | TS-004 `ensure_cn_uoms()` 只新增缺的，不改既有 | `accounting/install.py:56-67` | ✅ | ✅ | 两站 45 项存在 |
| §4.3 | TS-004 `disable_rounded_total()` 经 `save()` 建 Property Setter；已是 1 不 save | `accounting/install.py:70-77` | ✅ | ✅ | **`save()` 的连带副作用删掉了站点 `country` 默认值**，见 P1-01 |
| §4.3 | TS-004 不包在 `is_setup_complete()` 里；不做 zelin 的停用非中文单位／System Settings／in_words | `install.py`（hooks.py:291-295 段） | ✅ | ✅ | — |
| AC-010 | SL-002 ④「安装前后 System Settings 除 modified 外逐字段相同」 | `tests/test_install.py:20-25,53` | ⚠️ | ✅ | 字面通过；快照只取 `tabSingles`，看不到 System Settings 镜像到 `tabDefaultValue` 的值，P1-01 的变化测不到 |
| §4.4.1 | TS-005 科目表 JSON 逐字节复制 | `cn_tax/chart_of_accounts/cn_smes_chart_of_accounts2024.json` | ✅ | ✅ | 沿用 R13 四处 sha256 结论，未重算 |
| §4.4.2 | TS-005 `load_cn_chart_tree` 每次返回新对象；`__file__` 定位 | `accounting/chart.py:18-32` | ✅ | ✅ | 文件内容 `lru_cache` 后 `deepcopy` |
| §4.4.2；DEC-103 | TS-005 `get_charts_for_country`：中国只多一项，Standard 保留；其它国家与原函数一致 | `accounting/chart.py:39-45` | ✅ | ✅ | 读上游 `chart_of_accounts.py:135-167`：中国在 verified 里无表 → 原函数返回两个 Standard，覆盖后三项，与测试一致 |
| §4.4.2 | TS-005 `get_chart` 找不到返回 `None`；不带 zelin 的 `return chart` | `accounting/chart.py:48-52` | ✅ | ✅ | — |
| §4.4.2 | TS-005 `get_coa` 取表走本模块 `get_chart` | `accounting/chart.py:55-66` | ✅ | ✅ | `chart` 为空时返回 `[]`，比上游（对 None 迭代会崩）更稳 |
| §4.4.2；A4 | TS-005 `hooks.py` 三项覆盖；不覆盖 `get_all_nodes` | `hooks.py:198-202` | ✅ | ✅ | `treeview.py:17` 自行解析覆盖，已核 |
| §4.4.3；RW-07 | TS-006 `_takes_cn_path`；`before_insert` 每家公司显式赋值标志；非中国拒绝；`after_rollback` 复位 | `accounting/company.py:26-44` | ✅ | ✅ | 保存点回滚不触发 `after_rollback`，见 P1-07（观察） |
| §4.4.3 | TS-006 `on_update` 只建一次、`log_error(title=, message=)`、不吞异常、`finally` 复位 | `accounting/company.py:47-65` | ✅ | ✅ | — |
| §4.4.3；A3 | TS-006 `build_cn_company` 编排顺序：科目树→默认科目→仓库→仓库科目→物料组→付款方式→税 | `accounting/company.py:68-83` | ✅ | ✅ | 与 §六 契约一致；`ignore_root_company_validation` 用 `flags.get()` 取原值，比方案更稳 |
| §4.4.4 | TS-006 默认科目按科目号查明细、缺项全部列出后报错、`db_set` 写入 | `accounting/company.py:86-112` | ✅ | ✅ | — |
| §4.4.4；DEC-097 | TS-006 22 个字段映射 | `cn_tax/data/company_defaults.json:3-26` | ✅ | ✅ | 22 项与方案表逐项一致；HDTH 实查一致。**其中 `disposal_account`、`stock_adjustment_account` 两项不满足 ERPNext 字段过滤**，见 P1-02 |
| §4.4.4 | TS-006 仓库科目：仓库名 `_()` 同语言、不存在报错 | `accounting/company.py:115-120` | ⚠️ | ✅ | 仓库不存在会报错；**科目号查不到时静默写 NULL**，见 P1-04 |
| §4.4.4 | TS-006 物料组科目：原文与 `_()` 各查一次、缺组记 warning、有行更新无行追加 | `accounting/company.py:123-154` | ⚠️ | ✅ | 同上，科目查不到时写入空科目，见 P1-04；HDTH 五组实查正确 |
| §4.4.4 | TS-006 `item_group_expense`／`warehouse_account` 数据 | `company_defaults.json:27-38` | ✅ | ✅ | `Products`→5401010 修对 |
| AC-006；SL-003 ⑤④ | TS-006 `Existing Company` 走原生路径 | `accounting/company.py:26-31`；`tests/test_company.py:201-233` | ✅ | ✅ | DEC-120 已裁「只允许多出 VAT」。**原生克隆出的公司被排除在全部中国功能之外、自检报 ok**，DEC-120 没讨论这一面，见 P1-03 |
| HT-008／HT-014；SL-003 ⑤ | TS-006 测试：生命周期打点、逐节点比对、双顺序、残留标志、建账抛错回滚、validate 失败靠 `after_rollback` | `tests/test_company.py:65-190` | ✅ | ✅ | R12 IT-022 剩余的两处已补（`:169-174`、`:176-190`） |
| §4.5；DEC-085 | TS-007 `ChartCheckResult` 字段与 §六 契约一致 | `accounting/selfcheck.py:21-32` | ✅ | ✅ | 11 个字段逐一相同 |
| §4.5 | TS-007 `check_company_chart` 永不抛异常、`.get()` 语义、四种异常输入 | `accounting/selfcheck.py:67-129` | ✅ | ✅ | 「非本表公司 → ok=True」对 Existing Company 克隆出的中国结构公司同样成立，见 P1-03 |
| §4.5 | TS-007 `check_all_cn_companies` 查询失败也不抛 | `accounting/selfcheck.py:132-143` | ✅ | ✅ | 只按 `chart_of_accounts` 筛选，同见 P1-03 |
| §4.5 | TS-007 本 Stage 不注册 `after_migrate` | `hooks.py` | ✅ | — | 全文无 `after_migrate` |
| §4.6.1；DEC-094 | TS-008 9 个税类别、5 个销项与 7 个进项模板、13 条规则数据 | `cn_tax/data/tax_setup.json` | ✅ | ✅ | 与方案表逐项一致；13 条 = zelin `tax_rule.csv` 11 行 + P9／P6。**孤立税类别与漏规则（继承 zelin）**，见 P1-05 |
| §4.6.1 | TS-008 不用 `from_detailed_data`；按科目号精确命中；缺科目报错不建科目；含税标志放税行；不写补偿 SQL | `accounting/taxes.py:17-104` | ✅ | ✅ | 正常 `insert()`，未置 ignore 标志（HT-009） |
| §4.6.1 | TS-008 幂等：类别按 title、模板按 (title, company)、规则按六键判重 | `accounting/taxes.py:46-102` | ✅ | ✅ | — |
| TS-008 | `build_cn_company` 末尾调 `setup_cn_taxes`；`test_company.py` 补税断言 | `company.py:83`；`test_company.py:192-199` | ✅ | ✅ | R13 IT-039：`40200dc` 让两个用例先在事务内删 9 个税类别（`tests/utils.py:37-42`），读码确认之后的计数断言不再靠站上残留；未跑变异复核 |
| AC-003；P-2 | TS-008 端到端：113 含税、100 未税、109 运费 P9 的净额／税额／GL | `tests/test_e2e_minimal.py:8-79` | ✅ | ✅ | 三组都断言了 GL 科目号与金额 |
| BR-007；DEC-116 | SL-004 ⑥ 退货 -0.065 → -0.07；凑整已关、无尾差分录 | `tests/test_e2e_minimal.py:59-79` | ✅ | ✅ | 只测了单行单据；多行时的舍入颗粒度见 P1-06 |
| §4.6.1 末条 | 物料税率走 `Item Tax Template` | — | — | — | 需求写的是使用约束，方案未要求建模板；多税率混开发票的缺口见 P1-05 |
| §4.15 | 不注册 `regional_overrides`／`override_doctype_class`／`update_gl_dict_with_app_based_fields` | `hooks.py` 全文 | ✅ | — | 全文无这三项 |
| 方案外夹带 | Part1 文件中方案没要求的改动 | `hooks.py`、`patches.txt`、`config/`、`templates/pages/`、`public/.gitkeep` | ✅ | — | 都是 bench 生成的骨架；`chart.py:42` 把国别码 `lower()` 后比较，属容错写法。**未见顺手重构、额外功能或注释掉的旧实现** |

## 业务规则合规核

（以下规则均「未经专家确认」）

| 规则条款 | 本片是否涉及 | 结论 | 备注 |
|---|---|---|---|
| BR-001 准则是《小企业会计准则》，「(2024)」只是文件名 | 是（`CN_CHART_NAME`） | 合规 | 代码只把它当科目表名；`README.md` 未称其为准则版本（只抽读了 Part1 部分） |
| BR-002 报表组成与编报期 | 否 | — | Part3／Part4 |
| BR-003 税率 13／9／6／0、征收率 3、小规模 1% | 是（`tax_setup.json`） | 合规；另有一条**草案·待领域专家确认** | 档位齐全，进销项归属合理（9%／6%／1% 只在进项）。**草案**：`P0无税` 一个模板同时承接「出口零税率」与「免税」两种情形，两者的申报口径不同，是否要分开须专家确认。小规模 1% 优惠 2027-12-31 到期，模板没有到期机制，按 BR-003 的失效条件人工处理 |
| BR-004 增值税月末结转 | 否（科目存在，结转在 Part2） | — | — |
| BR-005 城建税与附加 | 否 | — | `build_cn_company` 不设 `cn_urban_construction_tax_rate`，交收口与 Part2 比对 |
| BR-006 资产负债表平衡 | 间接 | — | P1-02 的 `disposal_account` 落资产负债表科目，不影响平衡，但影响利润表 |
| BR-007 价税分离，按分四舍五入 | 是 | 单行合规；多行颗粒度为**草案·待领域专家确认** | 站点 Commercial Rounding，退货 -0.065→-0.07 有测试。**草案**：「税额按发票行逐行四舍五入到分，合计为各行之和」（与增值税发票开具口径一致）。本站 `round_row_wise_tax=0`，多行发票是先合计再舍入，见 P1-06 |

## 集成点登记（交接摘要）

**本片暴露给别片**
- 函数／常量：`chart.CN_CHART_NAME`、`is_cn_chart()`、`load_cn_chart_tree()`（Part2 `closing.py:260`、Part3 `balance_sheet.py:39` 用 `is_cn_chart(Company.chart_of_accounts)` 判定适用范围）；`selfcheck.check_company_chart()`／`check_all_cn_companies()`／`ChartCheckResult`（Part4 TS-021 对 HDTH 调用；S8G-S1 IM-007）；`company.build_cn_company(doc)`；`taxes.setup_cn_taxes(company)`。
- 数据契约：默认科目按科目号（`company_defaults.json`）；税模板名 `"{title} - {abbr}"`；9 个税类别名；销项 `2221005`、进项 `2221001`；仓库科目 `1405`／`1409`；物料组费用科目。
- 测试工具：`FrappeChinaTestCase`、`make_cn_company`、`make_std_company`、`clear_cn_tax_categories`、`CN_TAX_CATEGORIES`、`TEST_PREFIX`、`pdf_text_and_fonts`（Part4 TS-017）。
- 站点状态：`Global Defaults.disable_rounded_total=1` 与 8 类单据 Property Setter；45 个 UOM。

**本片依赖别片**
- `translations/zh.csv`（Part4 TS-020）提供本片报错的中文（已核 `zh.csv:96-110` 有 Part1 的 6 条）。
- `hooks.py` 的 fixtures（Part2／Part4 的 Custom Field、Cash Flow Code）与本片共用一个文件。

**事件／共享状态**
- 共享进程标志：`frappe.local.flags.ignore_chart_of_accounts`（上游 `company.py:346,362` 读取）、`frappe.local.flags.ignore_root_company_validation`、`doc.flags.frappe_china_build`、`frappe.db.after_rollback` 回调队列。
- **交收口比对**：① P1-03 的「克隆公司 `chart_of_accounts` 为空」使 Part2 结转与 Part3 报表拒绝该公司，请 Part2／Part3 片确认各自的拒绝提示是否明确（不静默）；② `cn_urban_construction_tax_rate` 由谁在建公司时赋值，Part1 不赋值；③ P1-02 的 `1606` 是否进了 Part3 资产负债表映射，以及 Part2 结转是否把它当损益处理。

## 自证复核

| 被审产物声称 | 实际复核结果 | 一致否 |
|---|---|---|
| D 回执 TS-004：「连续安装幂等且不改 System Settings」「System Settings 前后 sha256 相同」 | `tabSingles` 层面属实；但安装时的 `Global Defaults.save()` 删掉了 `tabDefaultValue` 的 `country`，两站 `get_default("country")` 实测为空（见 P1-01） | 部分不一致 |
| D 回执 TS-006：「22 个默认科目」 | 22 项与方案逐项相同，HDTH 实查相同 | 一致（但方案本身有 P1-02） |
| D 回执 HT-005：无公司站点 `save()` 可建 Property Setter | 测试站 Property Setter `modified` 12:12:15 与安装时刻相同 | 一致 |
| D 回执 HT-014：`after_rollback` 能复位 | 读 `database.py:1196-1215`：整笔回滚会执行；保存点回滚不执行 | 一致（适用面窄于字面，见 P1-07） |
| R13：TS-008 ❌ IT-039 | `40200dc` 在 `test_company.py:194`、`test_taxes.py:34` 先删税类别再建公司 | 读码一致，未跑变异 |
| 主会话：全量回归 113/113 | 未复核（硬约束） | — |

## 问题清单

| # | 严重程度 | 定位 | 问题描述 | 违背的标准/意图 | 建议 | 建议档位 | 待裁决点 | 状态 |
|---|---|---|---|---|---|---|---|---|
| P1-01 | 中 | `accounting/install.py:70-77`；上游 `global_defaults.py:45-48`、`frappe/defaults.py:165-173` | **装 app 时删掉了站点的 `country` 系统默认值。** `disable_rounded_total()` 调 `Global Defaults.save()`，其 `on_update` 把 `country` 等 7 个键全部按 Global Defaults 当前值重写 `tabDefaultValue`。两站 `Global Defaults.country` 都是 NULL，于是 `set_default("country", None)` 删掉了 System Settings 保存时写入的 `country=China` 行。实查：两站 `tabDefaultValue` 里 `defkey="country"` 0 行，而 `tabVersion` 显示 System Settings 的 country 曾由空改为 China（测试站 09-30 11:30:26）；测试站此后唯一一次 Global Defaults 保存就是本 app 安装（12:12:15，与 `disable_rounded_total` 默认值行同一时刻）。实测（只读 `bench execute`）：两站 `frappe.db.get_default("country")` 都返回空，`get_single_value("System Settings","country")` 仍是 China。也就是 `sysdefaults.country` 现在就是空的：`boot.py:367` 不加载 Country 文档，`desktop.py:196-209` 的按国别过滤会把所有标了 country 的工作区链接都滤掉，前端 `frappe.sys_defaults.country`（数字缩写等）取不到值。`test_install.py` 的快照只取 `tabSingles`，测不到 | §4.3／DEC-100「装 app 只做两件事」、AC-010「System Settings 未被本 app 改动」的意图 | ① 改用 HT-005 的备选写法：`db.set_single_value` + `db.set_default("disable_rounded_total", 1)` + 显式调 `toggle_rounded_total()`，不走整单 `save()`；② 两站补回 `country` 默认值；③ 安装测试的快照加上 `tabDefaultValue` 的 `__default` 行 | 本Session修 | ① 严重程度在中／低之间：两站现在就生效，但可见的影响面窄（按国别显示的链接、数字格式）；走安装向导建的客户库 Global Defaults.country 有值，不受影响；② 补站点数据是否在本 Round 做 | 待裁决 |
| P1-02 | 中 | `cn_tax/data/company_defaults.json:12,14`；上游 `company.js:307,332`、`depreciation.py:760-771`、`sales_invoice_item.py:128-135` | **zelin 带来的 16 个默认科目没有按 ERPNext 字段过滤核过，两项不满足。** ① `disposal_account`＝`1606 固定资产清理`（Asset／Balance Sheet），上游过滤要求 `report_type = Profit and Loss`。上游把它当资产处置损益科目：卖出固定资产时作收入科目，报废／出售的损益直接记入它。结果是处置损益落在资产负债表科目里，利润表不出现，`1606` 留下余额。② `stock_adjustment_account`＝`400103 生产成本-库存调整`（root_type Asset），上游在永续盘存下要求 `root_type = Expense`。盘盈盘亏因此不进损益。需求 §4.4.4 只对 DEC-097 的 6 项列了「满足 ERPNext 过滤」一栏，其余 16 项照抄 zelin，没做同样的核对。服务端 `validate_default_accounts` 不查这两条，所以不报错，属静默偏差。HDTH 实查两项正是这两个科目 | §4.4.4「csv 里在本表找不到的行删掉或改正」的意图；开发守则「静默失败」 | 交会计定口径（草案·待领域专家确认：`disposal_account` 宜指 `5301 营业外收入`／`5711 营业外支出` 一类损益科目，或保留 `1606` 并在月末结转里把它转出）；之后改 json 并补一条「22 项都满足 company.js 过滤」的测试 | 出方案修 | 科目怎么选须会计确认；中／低之间（演示线上目前没有资产处置与盘点） | 待裁决 |
| P1-03 | 中 | `accounting/company.py:26-31`；`accounting/selfcheck.py:80-83,132-138`；上游 `company.py:535-545,597-601`；`closing.py:260`；`statements/balance_sheet.py:39` | **以本表公司为源的克隆公司和子公司，只拿到一半的中国建账，自检还可能报通过。** ① 选 `Existing Company` 时，上游 `validate_coa_input` 把 `chart_of_accounts` 清空。新公司有完整的中国科目树，但 `is_cn_chart(None)` 为假：没有 P* 税模板（只有原生 17% VAT 和新建的无号 `VAT` 科目）、没有本 app 的默认科目／仓库科目／物料组科目，结转与报表都会拒绝它，`check_company_chart` 返回 `checked=False, ok=True`，`check_all_cn_companies` 也不列出它。② 设了 `parent_company` 时，`chart_of_accounts` 保持为本表，报表与结转认它，但默认科目由上游按 `account_type` 取第一条（如累计折旧可能取到 `1622`，`round_off_account` 为空），也没有 P* 模板；自检会判失败，这一点是对的。DEC-120 只讨论了多出 `VAT`，这些后果没讨论 | RS-014 要求验收覆盖多公司；DEC-103；AC-001「自检对缺科目／缺默认给出告警」的意图 | 定一条规则：克隆或子公司要么也走中国路径（以源公司为本表时补跑默认科目与税），要么在 `before_insert` 明确拒绝；自检对「科目号结构与本表一致但 `chart_of_accounts` 为空」的公司至少给出告警 | 出方案修 | P1 只有 HDTH 一家，可以登记为延迟需求，在多公司立项前定 | 待裁决 |
| P1-04 | 低 | `accounting/company.py:120,142-152` | 仓库科目与物料组科目按科目号查不到时，直接写入 NULL 或空的 `expense_account`，不报错也不告警。默认科目那段（`:98-109`）会先汇总缺项再报错，这两段没有这样做。数据文件和科目表都是静态的，目前不会触发 | 总纲 §十 第 7 条「不静默」 | 与 `set_cn_default_accounts` 一样，先收集缺项再 `frappe.throw` | 新Session修 | 无 | 待裁决 |
| P1-05 | 观察 | `cn_tax/data/tax_setup.json`（`tax_rules` 段）；上游 `tax_rule.py:202-220` | 税类别、模板与规则对不齐（照搬 zelin，方案原样要求）：`P1专票未税` 没有任何模板；销项 `P0无税` 有模板但没有税规则，单据上选这个税类别不会带出模板，税行为空。0% 的金额不受影响，但单据上没有税行可供识别。另：模板都是单一税率，一张单据同时有 13% 货物和 9% 运费时，要靠 `Item Tax Template`（需求 §4.6.1 末条）。本 app 没有建这类模板，用户须手工建 | §4.6.1；开发守则「静默失败」 | 补销项 `P0无税` 规则；删掉或补齐 `P1专票未税`；多税率单据的模板放进 S7 造数据的范围 | 延迟或不修 | 是否偏离 zelin 原样 | 待裁决 |
| P1-06 | 观察 | 演示站 `Accounts Settings.round_row_wise_tax = 0`；上游 `taxes_and_totals.py:455-457` | 多行发票的税额是各行不舍入的税额先合计、再舍入到分。增值税发票按行舍入后再加总，两者可能差 0.01。端到端测试只有单行单据，测不到。**草案·待领域专家确认**：「税额按发票行逐行舍入到分，合计为各行之和」 | BR-007（舍入颗粒度未写明） | 专家确认后，再决定是否在建站脚本中打开 `round_row_wise_tax`，并补一条多行测试 | 延迟或不修 | 规则是否成立 | 待裁决 |
| P1-07 | 观察 | `accounting/company.py:44`；上游 `database.py:1196-1200`、`company.py:362-365` | `after_rollback` 只在整笔回滚时执行，回滚到保存点时不执行（如数据导入逐行失败）。此时标志会留到同一请求结束。下一家**新建**公司由 `before_insert` 覆盖，RW-07 不受影响；但同一请求里随后**保存已有的**公司，上游 `set_default_accounts` 与现金付款方式科目会被跳过。web／rq 每个请求重置 `frappe.local`，影响面限于单个请求或作业 | RW-07 | 可在 `before_insert` 之外再挂一个 `on_trash`／`after_insert` 级的兜底；或接受并在 README 写明 | 延迟或不修 | 是否值得处理 | 待裁决 |
| P1-08 | 观察 | `accounting/chart.py:48-52`（`@frappe.whitelist()`） | 覆盖后的 `get_chart(chart_template, existing_company)` 和上游一样不查权限：任何已登录用户（包括门户网站用户）都可以传 `existing_company` 读出任意公司的科目树。这是上游原有的行为，覆盖照样保留了下来，不是本 app 新引入的 | 安全（whitelisted 方法的权限检查） | 带 `existing_company` 时加 `frappe.has_permission("Company", "read", existing_company, throw=True)`；改了就偏离上游行为，须记进 ADR | 延迟或不修 | 是否在 L4 覆盖里收紧上游的权限 | 待裁决 |

## 本片盲区自述（没往哪个方向找、哪处把握最低、拿不准处）

- **没跑任何东西**：「测试只覆盖 happy path」「变异能否被抓住」都是读码推演，没有实跑变异。P1-01 已用只读调用实测：两站 `get_default("country")` 都为空。「是本 app 安装删掉的」靠时间顺序推断：测试站 `tabVersion` 记有 System Settings 的 country 改动，此后 Global Defaults 唯一一次保存与安装同一时刻；但没有回放验证。演示站的时间线没有逐条核对。
- **把握最低的是 P1-02 的会计口径**：`1606` 作清理科目是国内做法，问题出在 ERPNext 一步记账、不会再结转。正确科目要会计定。Part2 的结转是否已经处理了 `1606`，我没看（属 Part2）。
- **没往这些方向找**：安装向导（setup wizard）路径下选本科目表建公司（需求范围外，只确认了覆盖对 `setup_wizard.js` 同样生效）；`bench migrate` 后 fixtures 是否覆盖 Workspace Sidebar；上游 `allow_unverified_charts` 打开时下拉的样子；HRMS 的 `Company.on_update` 交互（RS-001，归 S5）；非 CNY 币种的中国公司。
- **README 并入登记**只抽读了 Part1 部分，没有逐条与 zelin 的全部差异比对（例如 zelin 默认科目 csv 里被替换的 `round_off_account`、`write_off_account` 等原值是否都有登记）。
- **拿不准处**：P1-03 算「方案外的偏离」还是「方案已允许（DEC-120）」。我判为新发现，理由是 DEC-120 只裁了 VAT 计数，没有裁中国功能的覆盖范围。P1-01 定「中」还是「低」，理由见该行待裁决点。
