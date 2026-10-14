# F 审核分片报告 · 片 1（对象：R3 开发方案 Part1 SL-001～003／TS-001～005 的代码落地，含 R6 对其的替换 / 审核标准：B 需求文档 §4.3、§4.5、§4.8.1、§4.2.4 `PH-P1052`、§4.11、§4.12、AC-006／008／009／010／011）

**轮次**：P1-S6-R12｜**步骤**：F 分片 1｜**日期**：2026-10-13｜**执行者**：Claude 子 Agent（只读）
**依据**：[B需求文档](../R02-需求文档/P1-S6-R2-B需求文档.md) §4.2.4（`PH-P1052`）、§4.3、§4.5、§4.8.1、§4.11、§4.12、§八 AC-006／008～011；[R3 总纲](../R03-开发方案/P1-S6-R3-C开发方案-总纲.md) §四 A1～A4／A10／A12、§五 HT-006、§九；[R3 Part1](../R03-开发方案/P1-S6-R3-C开发方案-Part1.md)（全文）；[R6 C开发方案](../R06-开发方案/P1-S6-R6-C开发方案.md) §二 A15～A20、SL-011、TS-016／017、§六替换表；`docs/开发守则.md`（「译名自检时机」「站点自检函数的形态」「自有 DocType 改名补丁放 pre_model_sync」「改 app 级 json 必调大 modified」「判据必须能区分」「静默失败」、§跨 Phase 接口契约表）；`docs/业务规则.md`（BR-001～007，全部未经专家确认）
**被审范围**：`frappe_china` `474cd1c..d441e9f` 中属本片的文件——`translation_check.py`、`accounting/statements/labels.py`、`tests/test_translation_check.py`、`tests/test_translations.py`、`tests/translation_overrides.py`、`cn_tax/doctype/cash_flow_worksheet/*`、`patches/s6_rename_cash_flow_worksheet.py`、`patches.txt`、`tests/test_cash_flow_rename.py`、`tests/test_cash_flow.py`、`accounting/closing.py`、`tests/test_s6_closing_separator.py`、`accounting/statements/cash_flow_statement.py`、`accounting/statements/unmapped.py`、`tests/test_unmapped.py`、`cn_tax/chart_of_accounts/cn_smes_chart_of_accounts2024.json`、`month_end_closing_voucher_list.js`、`hr.py`／`test_hr.py`／`dataset.py`／`test_statement_dataset.py` 的 S6 改动；主仓库 `Spike/P1S6R4-baseline.py`（及其消费方 `Spike/P1S6R4-occupancy.py`）；线索 [R4 D回执-Part1](../R04-代码/P1-S6-R4-D回执-Part1.md)、[R5 E确认报告](../R05-确认/P1-S6-R5-E确认报告.md)

## 覆盖自证

- **读全的依据**：F Spec、`bricks/audit.md`、`bricks/sharding.md`；R3 Part1 全文（逐条建要求清单）；R3 总纲全文；R6 方案 §一～§二、§三、SL-011～012 验收、TS-016／017 全文、§六替换表；R4 D回执-Part1 全文；R5 E 报告按关键词读了 TS-001～005 行与 IT-001～004；`业务规则.md` 全文；`开发守则.md` 第 95～130 行、第 187～210 行与契约表（第 243～247 行）。B 需求文档读了 §4.2.4、§4.3、§4.5、§4.8.1、§4.11、§4.12、§八，其余章节只看目录。**未读**：R3 Part2～4、R6 TS-018～024、R7～R11 回执与 E 报告的正文（只按关键词搜「科目表／sha256／chart」确认没有对科目表 json 改动的裁决记录）；S5 Part5 只作格式参考。
- **逐行读的代码**：`translation_check.py`、`labels.py`、`test_translation_check.py`、`test_translations.py` 全文；`translation_overrides.py` 头尾与键集合（用 ast 取全部 114 键）；`cash_flow_worksheet.py` 120-299 行与 `git diff -M` 全部改动；`cash_flow_worksheet.{js,json}` 改动；改名补丁、`patches.txt`、`test_cash_flow_rename.py`、`test_s6_closing_separator.py` 全文；`closing.py`、`unmapped.py`、`cash_flow_statement.py`、`month_end_closing_voucher_list.js`、`dataset.py`、`test_cash_flow.py`、`test_statement_dataset.py`、`test_unmapped.py`、`hr.py`、`test_hr.py` 的 S6 diff；`Spike/P1S6R4-baseline.py` 全文、`P1S6R4-occupancy.py` 前 40 行。
- **对照的上游**（frappe `c1f1e8e`）：`utils/translations.py` `_()`（按 `frappe.local.lang` 取字典）；`__init__.py:201`（`init` 置 `local.lang = conf.lang or "en"`）、`connect`／`set_user`（不改 lang）；`commands/utils.py:262-320` `execute`；`translate.py:135-218`（合并顺序、csv 读法：键只做 `\\n`→换行、译文 strip）；`gettext/translate.py:41-62`；`model/rename_doc.py:401-412、616-667`；`core/doctype/doctype/doctype.py:663-698`（`after_rename` 在 `in_patch` 时不搬文件）；`modules/import_file.py:108-170`；`form/controls/button.js:39-47`。
- **跑过的**（临时脚本全在 `Spike/P1S6R12-F/p1/`）：
  - `PYTHONUTF8=1 python -I ../Spike/P1S6R4-baseline.py --out ../Spike/P1S6R12-F/p1/baseline.out.json`（宿主，只读源码，输出写到本片目录、不覆盖正式输出）。
  - `overrides_vs_baseline.py`（基线 `official_overrides` 与 `OVERRIDES` 键集合比对、csv 是否有 CJK 键）；`dupkey_probe.py` 与一行内联脚本（重复键检测与 Frappe 读法对照）；`patch_guard_mutation.py`（改名补丁两道守卫的函数级变异，假 frappe，不碰被审文件）。
  - 容器内 `env/bin/python -I`：`lang_probe.py`（演示站 `init+connect` 后的 `local.lang`；内存 patch `get_all_translations` 注入「资产→Assets」后分别在默认语言与 zh 下调 `validate_legal_labels`；结束 `rollback`）；`demo_find_problems.py`（演示站默认语言与 zh 各跑一次 `find_problems`）；`legal_alias.py`（csv 译文等于法定列头的行，不连库）。
  - 演示站 `erx.localhost` 只读 SQL：`tabDocType`／`SHOW TABLES like 'tabCash Flow%'`／`tabPatch Log`／`tabTranslation`／`tabDocField.options`／`tabReport`／`tabCompany`／`tabAccount` 按公司计数／`tabWorkspace Sidebar Item.link_to`／`tabSingles` System Settings.language；`sites/assets/locale/zh/LC_MESSAGES/` 与 app 包内 `.mo/.po` 列目录。
  - git 只读：`log`／`diff`／`show`／`blame`；科目表 json 两版逐字节、`json` 语义、科目计数、sha256 比对。
  - 验证门（只做不连站点的部分）：本片 18 个 py 文件 `ast.parse` 全过；`node --check` 两个 js 过；`cash_flow_worksheet.json` 可解析。
- **跳过**：没跑任何 `bench run-tests`、没做真实变异（只读约束＋主会话在测试站跑全量回归），各用例「通过」采信 R11 回归、只自判判别力；**测试站一概未查**（数据处于测试中），故 SL-002 ① 的迁移后 `parenttype`、HT-006 的改名探针只核了 D 回执与演示站现状；没看截图细节（`P1S6R4-worksheet-search.png` 分辨率低，只确认三项并列可见）；没构造全新装站。

## 逐项落地核查

| 意图层依据 | 要求层要求（方案任务／验收条款逐条） | 定位（文件:行） | 落地 | 生效否 | 偏差说明 |
|---|---|---|---|---|---|
| §4.2.1／AC-006 | TS-001 接口契约：`APPS` 七项、`parse_po`／`parse_csv`／`merged_dict`／`gaps`／`collisions`／`demo_surface`／`official_overrides` | `Spike/P1S6R4-baseline.py:13、28-130、133、181、247` | ✅ | ✅ 本片实跑成功 | `parse_po` 自写、未复用 `P1S6R1-merged-collisions.py` 的 parse（Part1「复用」），行为等价，不报；`merged_dict` 返回 `(merged, plain_keys)` 二元组，与契约签名不同，消费方 `occupancy.py:15` 按二元组用，一致 |
| AC-006 | 缺口算法：`merged.get(key) or merged.get(id)`、译文等于源词也算缺口；raven 无 zh.po 照算 | `baseline.py:110-130` | ✅ | ✅ | 实跑 `gap_counts` 六 app 全 0、`identity_gap_counts` 全 0；白名单命中 228（76/52/27/32/16/25），与 R7 回执「UNTRANSLATED 228」一致 |
| §4.2.2 | 演示线面四部分＋LG-009 差集；`Cash Flow Worksheet` 改名前后自适应 | `baseline.py:181-244`、`:183` | ✅ | ✅ | 实跑 `demo_surface_count` 3055（R4 时 3042，差额来自 Part3 自有侧栏，部分 3 读 `frappe_china/workspace_sidebar`）；`lg009_missing_doctypes` 14 项与 R4 回执一致 |
| A4／§4.3 | 官方覆盖：csv 键 ∩ 六 app `zh.po`（含 msgctxt 键） | `baseline.py:247-254` | ✅ | ✅ | 实跑 114 条，与 `OVERRIDES` 114 键**集合完全相等**（`overrides_vs_baseline.py` 两差集皆空） |
| §4.2.1 第 2 条 | `commits` 与 `docker/apps.json` 比对，不一致拒跑；R6 加 `--allow-unlocked` | `baseline.py:257-271、277` | ✅ | ✅ | 不带参数实跑 `unlocked: {}`（R5 SB 已把锁更新到 `4f75f5a`…；本片看到的 HEAD `d441e9f` 也在锁内，`unlocked` 空） |
| R6 A19 | 基线读 `translation_whitelist.UNTRANSLATED`（按路径载入，不 import frappe） | `baseline.py:101-107、122-124` | ✅ | ✅ | — |
| A1／§4.3 | `find_problems() -> list[str]`、`run() -> list[str]` 放包顶层；纯查询；`run` 打印「译名自检通过」或逐条、不 throw | `translation_check.py:12-51` | ✅ | ⚠️ 见 P1-01 | 演示站 `bench execute` 下第 4 项查的是 **en** 字典，见下一行 |
| §4.3 第 4 项／BR-002 间接触点 | 法定列头未被翻译：`validate_legal_labels()` 的每个列头一行 | `translation_check.py:39-40`；`labels.py:39` | ⚠️ | ❌（bench execute 路径） | `_(label)` 按 `frappe.local.lang` 取字典；`bench execute` 经 `frappe.init` 置 `lang = conf.lang or "en"`（`frappe/__init__.py:201`），两站 `site_config` 无 `lang`、`connect` 不改 lang。实测演示站 `init+connect` 后 `local.lang = en`；内存注入 zh「资产→Assets」后，默认语言下 `validate_legal_labels()` 返回 `[]`、置 `zh` 后返回 `['资产']`（`lang_probe.py`）。测试路径因 `FrappeChinaTestCase` 置 zh 而有效。见 P1-01 |
| §4.3 第 1 项 | `Translation` 全语言、按 `creation` 升序、最多 50 条＋「另有 N 条」＋自定义表单提示 | `translation_check.py:14-28` | ✅ | ✅ | 不依赖语言；`db` 为 None 时整项跳过（契约未写，无害） |
| A2／§4.3 第 2 项 | app 包 `rglob("*.mo")` ∪ `get_locale_dir()/*/LC_MESSAGES/frappe_china.mo`，附「同一 app 内 .mo 覆盖 .csv」 | `translation_check.py:29-36` | ✅ | ✅ | 去重写法正确；演示容器 `assets/locale/zh/LC_MESSAGES/` 只有五个官方 `.mo`，无 `frappe_china.mo`；app 包内无 `.mo/.po` |
| §4.3 第 3 项 | app 包 `rglob("*.po")`，附「bench build 会把它编成 .mo」 | `translation_check.py:37-38` | ✅ | ✅ | — |
| `PH-P1030` | `labels.py` 删 `try/except Exception: pass`；只在 `frappe.local.db is None` 时跳过取 `Cash Flow Code`，其余异常照抛 | `labels.py:31-39` | ✅ | ✅ | `import frappe` 上移到模块顶，模块导入不再依赖库，契约要求达成 |
| TS-002 第 3 步 | 约定「站点自检放包顶层、run 打印返回、不 throw」进回执 | R4 回执「新增约定」；`开发守则.md`「站点自检函数的形态」 | ✅ | — | 已沉淀进开发守则 |
| SL-001 ② | 测试站 `execute … run` 打印通过、返回 `[]`；演示站只读跑一次 | 演示站 `demo_find_problems.py` | ✅ | ⚠️ | 演示站默认语言（en）与 zh 下 `find_problems()` 均 `[]`；测试站未查（约束） |
| A3 | `translation_overrides.py`：`Override(official, ours, basis)`、`OVERRIDES: dict[str, Override]` | `translation_overrides.py:1-11` | ✅ | ✅ | 内容由 R6 TS-017 重建（114 条），`basis` 形态按 R6 SL-011 ③；`本 app 自有源词` 形态是 R7 D 申报的偏离、由 `_misused_own_basis` 约束（`test_translations.py:326-330`） |
| SL-001 ③ | 反证：事务内插 `Translation` → 清单含源词，事后断言已清 | `test_translation_check.py:21-35` | ✅ | ✅ | 方案写 `rollback`，实为 `delete_doc` 后断言不存在，等效；判别力：去掉第 1 项即红 |
| SL-001 ③ | 反证：app 包下临时 `x.mo`／`x.po` → 清单含路径；`finally` 删并断言 | `test_translation_check.py:49-63` | ✅ | ✅ | — |
| SL-001 ③／A2 | 另一例：`get_locale_dir()/zh/LC_MESSAGES/frappe_china.mo`，先断言原本不存在、存在则 `skipTest` | `test_translation_check.py:65-75` | ✅ | ✅ | 容器内该文件不存在，用例不会跳过 |
| SL-001 ③ | 反证：「资产」被译 → 清单含「资产」 | `test_translation_check.py:77-92` | ✅ | ✅ | R5 IT-002 已收窄为只认「法定列头被翻译：资产」前缀，判别力成立 |
| SL-001 ④ | `db is None` 时不抛且不取数；`get_all` 抛 `DoesNotExistError` 照抛 | `test_translation_check.py:94-102` | ✅ | ✅ | 两例都有判别力：恢复旧 `except` → 第二例红；删守卫 → 第一例 `assert_not_called` 红 |
| TS-002 第 1 步 | 50 条上限、全语言 | `test_translation_check.py:37-47` | ✅ | ✅ | 断言 `get_all` 无 `filters`，判别力成立 |
| SL-001 ⑤／R6 SL-011 ③ | 官方交集比对六 app；`交集 − 清单` 与 `清单 − 交集` 都报 | `test_translations.py:210-213` | ✅ | ✅ | R6 已把「⊆」改为「＝」并报两差集 |
| SL-001 ⑤ | `test_overrides_exist_in_csv`、`test_override_officials_are_current`（报「上游改了译文」） | `test_translations.py:248-256` | ✅ | ✅ | — |
| A4／SL-001 ⑤⑥ | `test_csv_has_no_duplicate_keys`（读 csv 文本、纯函数 `_duplicate_keys`）＋喂重复两行的反证 | `test_translations.py:179-181、258-262、280-282` | ⚠️ | ⚠️ | 键不做 Frappe 的 `\\n`→换行归一，「字面 `\n`」与「真换行」两种写法的同一键查不出（`translate.py:204`），见 P1-04。当前 csv 15 个字面 `\n` 键，按 Frappe 读法归一后无重复 |
| A4／SL-001 ⑤ | `test_csv_rows_have_two_or_three_columns` | `test_translations.py:264-268` | ✅ | ✅ | — |
| TS-003 第 4 步 | `test_every_app_source_string_has_chinese` 保留 | `test_translations.py:196-200` | ✅ | ✅ | 已按 R6 A19／IT-024 改为自动取源词并扣 `UNTRANSLATED`，属后续方案裁决 |
| LG-134 | csv 译文不得与法定列头同名 | `test_translations.py:214-221` | ⚠️ | ✅ | `source not in NAMED_TERMS` 豁免（`1779cf0` 加）当前**零命中**（`legal_alias.py`：csv 中译文等于 132 个法定列头的行 0 条），见 P1-06 |
| §4.5／DEC-015 | 目录、三文件、类名 `CashFlowWorksheet`、`frappe.ui.form.on("Cash Flow Worksheet")`、json `name`／`amended_from.options`／`modified` 调大 | `cash_flow_worksheet.json:4-5、17`；`.py:14`；`.js:4` | ✅ | ✅ | 演示站 `tabDocType` 有 `Cash Flow Worksheet`（modified `2026-10-09 12:00:00`），`amended_from.options` 为新名；`.js:1` 注释仍写 `cash_flow.py`，见 P1-07 |
| §4.5 引用 | 全部 `"Cash Flow"` DocType 引用改名：控制器 8 处、`cash_flow_statement.py:120/133/159`、`dataset.py:345`、`test_cash_flow.py`、`test_statement_dataset.py`、README | 各文件 diff；`README.md:148-157` | ✅ | ✅ | SL-002 ② 本片复 grep：除补丁两处与 `test_named_terms.py:19`（原生报表 `Cash Flow`→现金流量表，DEC-015）外零命中 |
| A10／HT-006 | 补丁登 `[pre_model_sync]`；两道幂等；`rename_doc(force=True)`＋`reload_doc` | `patches.txt:2`；`s6_rename_cash_flow_worksheet.py:4-8` | ✅ | ✅ | 演示站 `Patch Log` 有该补丁、无 `tabCash Flow`；上游 `after_rename` 在 `in_patch` 时不搬文件（`doctype.py:691`），`rename_doc` 改子表 `parenttype`（`rename_doc.py:401-402、616-645`） |
| SL-002 ① | 测试站有一条底稿时 migrate 成功；新表有记录、子表 `parenttype` 已改；URL 可打开 | R4 回执、`Spike/P1S6R4-rename-probe.json` | ⚠️ 未亲自复核 | — | 测试站未查；URL 打开那条由 R5 IT-004 裁为接受现有证据，不重报 |
| SL-002 ③／AC-010 | 搜索「现金流量」三者各不同名 | `Spike/P1S6R4-worksheet-search.png`；演示站侧栏 | ✅ | ✅ | 截图三项并列；演示站 `Business Flow` 侧栏 `link_to=Cash Flow Worksheet`、`Financial Reports` 侧栏 `link_to=Cash Flow`（报表），两者分开 |
| SL-002 ⑤ | 补丁在已改名站／新装站直接返回；测试断言 `rename_doc` 未调用 | `test_cash_flow_rename.py:8-18` | ⚠️ | ⚠️ 判别力不足 | 第一例只 patch `table_exists=False`，测试站上第二道守卫（新 DocType 已存在）同样返回，删掉第一道守卫测试照绿（`patch_guard_mutation.py`），见 P1-03 |
| TS-004 第 5 步 | csv 加 `Cash Flow Worksheet,现金流量底稿`；8 条消息逐条判，指底稿的改源词、译文不变；`Cash Flow row {0} is missing` 指报表行不改 | `zh.csv:774、831、834-837、3201、4714、4717` | ✅ | ✅ | 旧源词 7 条已全部不在 csv；代码 `_()` 同步；`REQUIRED_TRANSLATIONS:48` 改键 |
| TS-004 第 7 步 | 约定「改名补丁放 pre 段、两道幂等」 | `开发守则.md:111-113` | ✅ | — | — |
| `PH-P1035`／AC-011 | 取消确认框写公司、财年、月份；csv 换新源词、旧行删 | `month_end_closing_voucher_list.js:48`；`zh.csv:4068` | ✅ | ✅ | 旧源词 `…of month {0}?` 已不在 csv |
| `PH-P1041` | 列 `options: "currency"`；行带 `currency: f.currency` | `unmapped.py:21、128`；`balance_sheet.py:59-65` | ✅ | ✅ | `test_unmapped.py:51、72` 两条断言各有判别力 |
| `PH-P1042` | 按钮 `depends_on` 加 `docstatus==0`（`modified` 调大）；JS 同名处理器 `frm.call` 后 `dirty()`、`refresh_fields()`；测试断言改新串、注释改写 | `cash_flow_worksheet.json:14`；`.js:5-10`；`test_cash_flow.py:100-105` | ✅ | ✅ | 上游 `button.js:41-42` 有同名处理器即走处理器；`options` 保留，`run_server_script` 退路仍在 |
| `PH-P1063` | 明细空且余额不符时报新提示；明细不空报原句；csv 加译文 | `cash_flow_worksheet.py:285-288`；`zh.csv:3103`；`test_cash_flow.py:179-189` | ✅ | ✅ | 新分支条件是原报错条件的子集，只换提示、不改校验语义；两例判别力成立（删分支→第一例红；去掉 `not self.items`→第二例红） |
| `PH-P1052`／A12 | `_join` 逐对用 `_("{0}; {1}", context="Month End Closing Voucher")`；`_incomplete_detail` 与成功消息两处改用；csv 第 25 行改三列；`REQUIRED_TRANSLATIONS` 键改 | `closing.py:163-170、179、402`；`zh.csv:5855`；`test_translations.py:72` | ✅ | ✅ | 方案伪代码用 `reduce`，实现用循环并补空列表守卫，等价；csv 两列 `"{0}; {1}"` 已无；六 app 官方 `zh.po` 无该 msgid，故 zh 下去掉 context 即回落英文分号，用例有判别力 |
| SL-003 ⑤ | zh／en 各断言分隔符（`_incomplete_detail` 与成功消息） | `test_s6_closing_separator.py:12-52` | ✅ | ✅ | 成功消息例 patch 了 13 个依赖，只验拼接；方案写「`test_closing` 加两例」，实际另起新文件，无害 |
| SL-003 ⑥ | 未填公司或月份时按钮不显示 | `cash_flow_worksheet.json:14` | ✅ | ✅ | 原三条件保留 |
| 方案外夹带 | — | `git diff 474cd1c..d441e9f` 本片文件 | ⚠️ | — | ① 科目表 json 8 行 CRLF→LF＋补文件尾换行（`52f8064`），字节与 sha256 变了，见 P1-02；② `hr.py:141`、`test_hr.py:56` 仅补文件尾换行（同一提交，无语义）；③ `test_translations.py:218` 的 `NAMED_TERMS` 豁免（P1-06）。其余改动均能对上 Part1 任务或 R5／R6／R8／R11 的裁决（`git log` 提交信息可辨） |

## 业务规则合规核

| 规则条款 | 本片改动是否涉及 | 结论 | 备注 |
|---|---|---|---|
| BR-001 小企业会计准则科目表 | 涉及（科目表 json 有 16 行 diff） | 合规（未经专家确认） | 只是 8 行换行符 CRLF→LF 与文件尾换行：两版 `json.loads` 结果相等，科目数两版都是 266，演示站 `HDTH` 科目 266；无任何科目名、号、类型、`root_type` 变化。字节层面违背 S4 的「逐字节＝zelin」工程约定，记 P1-02，不是领域违规 |
| BR-002 法定报表构成与列头（§4.11 间接触点） | 涉及（自检第 4 项守法定列头不被译） | 合规（未经专家确认），守卫有缺口 | 当前 zh 字典里 132 个法定列头无一被译（测试路径与演示站 zh 下均 `[]`）；但 `bench execute` 路径下第 4 项查的是 en 字典，见 P1-01 |
| BR-003 增值税税率 | 不涉及 | — | 本片未改税率与税模板 |
| BR-004 应交增值税月末转出 | 涉及（`closing.py`） | 合规（未经专家确认） | 改动只限结转原因与成功消息的拼接（`_join`），`_vat_transfer_rows` 等计算未动（diff 只有 `:163-179`、`:402`） |
| BR-005 城建税与教育费附加 | 涉及（`closing.py` 同上） | 合规（未经专家确认） | 同上，`_surtax_rows` 未动 |
| BR-006 资产负债表平衡 | 不涉及 | — | `unmapped.py` 只加列 `options` 与行 `currency`，不改取数 |
| BR-007 价税分离 | 不涉及 | — | — |
| 本片总体 | — | 无新增或变更的领域不变量 | `PH-P1063` 新提示是原校验条件的子集，现金流量底稿的余额校验语义不变；无需触发规则送审 |

## 集成点登记（交接摘要）

**本片暴露**
- 接口：`frappe_china.translation_check.find_problems() -> list[str]`、`run() -> list[str]`（消费方：`test_translation_check`、`开发守则.md`「译名自检时机」、R6 SL-015 ②、多个 `Spike/*` 演示站核查脚本——那些脚本都**自己先置 `frappe.local.lang = 'zh'`** 再调 `find_problems`，`run()` 本身不置）。
- 接口：`accounting.statements.labels.validate_legal_labels() -> list[str]`、`LEGAL_LABELS`（132 项）——消费方 `translation_check`、`test_translations`、`test_statement_output`、`Spike/P1S6R7/merge_check.py`／`apply_rows.py`。**行为依赖调用时的 `frappe.local.lang`**。
- 数据模块：`tests/translation_overrides.py` 的 `Override`／`OVERRIDES`（114 条，内容属 R6 TS-017 片）；`tests/test_translations.py` 的 `REQUIRED_TRANSLATIONS`、`_app_source_strings()`／`_source_strings_from_text()`（R9 A28 取法）、`_duplicate_keys`、`_BASIS_FORM`、`_tokens`。
- 脚本：`Spike/P1S6R4-baseline.py` 的 `merged_dict() -> (merged, plain_keys)`（消费方 `Spike/P1S6R4-occupancy.py:15`，按二元组用，一致）；输出 json 键 `commits.{heads,unlocked}`／`gaps`／`gap_counts`／`whitelisted`／`collisions`／`demo_collisions`／`demo_surface`／`official_overrides`／`lg009_*`（Part2 TS-006／007、R6 TS-019／021 消费）。本片实跑：缺口 0、撞名 1195、演示撞名 188、官方覆盖 114、`unlocked {}`。
- DocType 名 `Cash Flow Worksheet`（消费方：Part3 `workspace_sidebar/business_flow.json:455-461`、`test_named_terms.py:18`、`cash_flow_statement.py`、`dataset.py`）；子表 `Cash Flow Item`／`Cash Flow Subtotal` 名不变。
- csv 键：`Cash Flow Worksheet`、`{0}; {1}:Month End Closing Voucher`、`Reverse all Month End Closing Vouchers of {0}, fiscal year {1}, month {2}?`、`No cash flow items yet. Click Get Cash Flow Items first, then save.` 及 7 条改名后的底稿消息（都在 `REQUIRED_TRANSLATIONS` 或 `_app_source_strings` 内，csv 清场 A15 ① 会保留）。
- 迁移状态：`patches.txt [pre_model_sync]` 的 `frappe_china.patches.s6_rename_cash_flow_worksheet`（演示站 `Patch Log` 已记）；Part4／R6 TS-023 的演示站 migrate 依赖它幂等。

**本片依赖**
- 共享状态 ①：`frappe.local.lang`。自检第 4 项与全部 `_()` 断言依赖它为 `zh`：测试由 `FrappeChinaTestCase`（`tests/utils.py:36`）置 zh；`bench execute` 路径下为 `en`（P1-01）。
- 共享状态 ②：`sites/assets/locale/*/LC_MESSAGES/` 下没有 `frappe_china.mo`（`bench build` 产物位置，A2）。
- 跨片：`tests/test_translation_quality.guard_problems`（R6 TS-017，`test_override_basis_forms` 用）；`tests/test_named_terms.NAMED_TERMS`（Part2，交集与法定列头断言用）；`tests/translation_whitelist.UNTRANSLATED`（R6 A19，测试与基线脚本共用）。
- 主仓库 `docker/apps.json` 的提交锁（基线脚本拒跑判据；R5 SB IT-001 已更新）。
- 上游契约：`frappe/translate.py:196-218` csv 读法（键只做 `\\n` 归一、不 strip）；`button.js:41-42` 同名处理器优先；`rename_doc.py` 改 `parenttype`；`import_file.py` 只比 `modified`／`migration_hash`。
- `balance_sheet._validate_filters` 返回 `currency`（`unmapped.py` 用）。

**事件**：本片不发出、也不消费 SSE／realtime 事件。
**§13 跨 Phase 契约**：表中只有一条「演示操控的事件协议」，本片不涉及。

## 自证复核

| 被审产物声称 | 实际复核 | 一致否 |
|---|---|---|
| R4 回执 TS-002：测试站与演示站 `execute` 自检均通过、返回 `[]` | 演示站默认语言与 zh 下 `find_problems()` 均 `[]`；但 `execute` 下第 4 项查的是 en 字典，「通过」对第 4 项不构成证据 | 部分一致（P1-01） |
| R5 E 报告 TS-002 ✅「两站只读跑都打印通过」 | 同上，E 未发现语言问题 | 部分一致 |
| R4 回执 TS-003：自检 8/8 | 测试文件正好 8 个 `test_` 方法；未亲自跑 | 结构一致 |
| R4 回执 TS-001：缺口 5513／撞名 905／演示撞名 185／覆盖 2（Part1 时点） | 未复算 Part1 时点（R11 E 已核另存输出 sha256）；HEAD 上实跑缺口 0、撞名 1195、演示撞名 188、覆盖 114，与 R7 之后的 csv 状态相符 | 当前态一致 |
| R4 回执 TS-004：补丁 2/2、幂等；R5 E「两个补丁用例都断言 `rename_doc` 未被调用」 | 断言确在；但第一例在测试站上不能区分第一道守卫 | 部分一致（P1-03） |
| R4 回执 TS-004 消息改名判定 8 条 | csv 与代码逐条对上；`Cash Flow row {0} is missing` 保留（`cash_flow_statement.py:74` 指报表行） | 一致 |
| R4 回执 TS-005：四处修改与 context 分隔符已落地、`test_s6_closing_separator` 2/2 | 代码与 csv 逐处对上，用例 2 个、判别力成立 | 一致 |
| R4 回执「偏离」：「仍有无业务语义的文件尾换行差异，未以 reset/restore 清理」 | 科目表 json 的换行改动在后来的 `52f8064`，不只是文件尾，也改了文件头 4 行；`.gitattributes` 明写该文件 `-text`、保留 CRLF 以维持 S4 TS-005 的 sha256（S4 R9 E 实测 `539d12f5…`），现为 `e9238dec…`。各 R4～R11 文档未见申报或裁决 | **不一致**（P1-02） |
| R4 回执：D 回执「新增约定」两条 | 都已进开发守则 | 一致 |

## 问题清单

| # | 严重程度 | 定位 | 问题描述 | 违背的标准/意图 | 建议 | 建议档位 | 待裁决点 | 状态 |
|---|---|---|---|---|---|---|---|---|
| P1-01 | 中 | `translation_check.py:39-40`；`labels.py:39`；上游 `frappe/__init__.py:201`、`commands/utils.py:274-275` | `bench --site X execute frappe_china.translation_check.run`（开发守则规定的演示站跑法）下 `frappe.local.lang` 为 `en`：`init` 取 `conf.lang or "en"`，两站 `site_config` 无 `lang`，`connect` 不改语言（演示站 System Settings 的 `language=zh` 不起作用）。第 4 项的 `_(label) != label` 于是查的是**英文字典**，zh 字典里法定列头被译时照样报「译名自检通过」。复现：`docker exec … env/bin/python -I /workspace/Spike/P1S6R12-F/p1/lang_probe.py` → `local.lang after init+connect: en`；内存注入 zh「资产→Assets」后 `default lang -> []`、`lang=zh -> ['资产']`。测试路径（`FrappeChinaTestCase` 置 zh）有效；E／D 的核查脚本都自己先置 zh，所以一直没暴露。目前的实际漏网面有限（`Translation` 记录由第 1 项兜住、csv 由测试站用例兜住），但这正是 `PH-P1030` 要消灭的「静默缩小检查范围」 | 需求 §4.3 第 4 项与「两种跑法」第 2 条（演示站单独跑不可省）；AC-008；`开发守则`「静默失败」；BR-002 间接触点 | `find_problems` 第 4 项固定按 `zh` 判（如 `validate_legal_labels(lang="zh")`，内部 `_(label, lang="zh")`），或 `run()` 开头置 `frappe.local.lang = "zh"` 并在 `finally` 复原；补一条用例：`frappe.local.lang = "en"` 时注入 zh 译名仍报出 | 新Session修 | 按 zh 固定判，还是按站点 System Settings 语言判；定「中」还是「低」（见盲区自述） | 待裁决 |
| P1-02 | 低 | `cn_tax/chart_of_accounts/cn_smes_chart_of_accounts2024.json:1-4、1600-1603`；提交 `52f8064`；`.gitattributes` | S6 提交 `52f8064`（「feat: continue S6 business flow navigation」）把科目表 json 头 4 行与尾 4 行的 CRLF 改成 LF，并补了文件尾换行：sha256 由 `539d12f5…`（S4 R9 E 实测、S4 TS-005「与 zelin 逐字节相同」）变为 `e9238dec…`。`.gitattributes` 为此文件专设 `-text` 并注明「保留原始 CRLF 字节」。语义不变：两版 `json.loads` 相等、科目 266、演示站 `HDTH` 266。没有任何 S6 方案要求动这个文件，回执与 E 报告也没有申报或裁决——属方案外夹带（同一提交的 `hr.py:141`、`test_hr.py:56` 只补文件尾换行，无语义） | S4 R7 方案 TS-005「逐字节复制、sha256 相同」；`.gitattributes` 注释；F Spec 预设提示词 7（方案外夹带） | 用 `474cd1c` 的字节还原该文件（`git show 474cd1c:<path> > <path>`，属工作区写操作、提交另问），并查清是哪个编辑工具改的换行，避免再犯；`hr.py`／`test_hr.py` 的文件尾换行可留 | 本Session修 | 是否还原（还原后重算 sha256 应回到 `539d12f5…`）；是否需要补一条测试断言该文件 sha256 | 待裁决 |
| P1-03 | 低 | `tests/test_cash_flow_rename.py:8-11`；`patches/s6_rename_cash_flow_worksheet.py:5` | 「新装站无旧表」用例只 patch `table_exists=False`，`frappe.db.exists` 未 patch；测试站上 `DocType Cash Flow Worksheet` 真实存在，第二道守卫照样让函数返回。删掉第一道守卫（`not frappe.db.table_exists("Cash Flow")`）后两例仍全绿——函数级变异 `python -I Spike/P1S6R12-F/p1/patch_guard_mutation.py` → `no_guard1: …=GREEN …=GREEN`；删第二道守卫则第二例变红，有判别力。产品行为无问题（两道守卫都在） | SL-002 ⑤「全新装站路径上直接返回」；`开发守则`「判据必须能区分它要区分的两种情形」 | 第一例同时 `patch("frappe.db.exists", return_value=False)`，使只有第一道守卫能让它返回 | 新Session修 | — | 待裁决 |
| P1-04 | 低 | `tests/test_translations.py:179-181`；上游 `frappe/translate.py:204` | `_duplicate_keys` 直接用 csv 原文作键；Frappe 读 csv 时先把键里的字面 `\n` 换成真换行。同一源词一行写字面 `\n`、一行写真换行时，Frappe 会让后行静默盖前行，而用例查不出（复现：喂 `['a\\nb','x']` 与 `['a\nb','y']` 两行 → 返回 `[]`）。R7 回执记过这类撞键（main.pot 抽 TSX 串），当时靠合并脚本按 Frappe 读法判重处理，但测试侧守卫没跟上。当前 csv 15 个字面 `\n` 键，归一后无重复，未触发 | A4「重复键是译名被静默盖掉的第四种形态」；SL-001 ⑥ | `_duplicate_keys` 先对 `row[0]` 做 `.replace("\\n", "\n")` 再计数，并加一条两种写法的反证 | 新Session修 | — | 待裁决 |
| P1-05 | 观察 | `accounting/statements/unmapped.py:129`；`accounting/statements/engine.py:157` | 本 app 另有两处写死的分隔符：漏科目检查的 `issue` 列用 `"; ".join`（zh 界面中文原因之间是半角分号），报表引擎报错用 `"；".join`（en 界面是全角分号）。需求 `PH-P1052` 与 A12 只点名 `closing.py`，故不算漏做，但同类问题未收口 | 需求 §4.2.4 `PH-P1052` 的意图（分隔符随语言） | 下次动这两个文件时改用同一个 `_join`（或把 `_join` 提到公共模块） | 延迟或不修 | 是否登记延迟需求 | 待裁决 |
| P1-06 | 观察 | `tests/test_translations.py:218`（`1779cf0` 引入） | 「csv 译文不得与法定列头同名」断言加了 `source not in NAMED_TERMS` 豁免，方案没有要求。当前 csv 中译文等于 132 个法定列头的行为 0 条（`legal_alias.py` → `total 0`），豁免是空转的；它留着的效果是：以后任何点名用词只要进了 `NAMED_TERMS`，就能把译文设成法定列头而不报 | 需求 §4.2.5 第 4 条（LG-134）；F Spec 预设提示词 7 | 删掉豁免；真有需要时逐键列白名单并写理由 | 新Session修 | 该豁免当初为哪个键加的（推测是曾在 csv 的 `Cash Flow`→现金流量表），是否仍需要 | 待裁决 |
| P1-07 | 观察 | `cn_tax/doctype/cash_flow_worksheet/cash_flow_worksheet.js:1` | 改名后的注释仍写「按整数比较（cash_flow.py）」，指向已不存在的文件名 | 可读性 | 下次改这个文件时顺手改为 `cash_flow_worksheet.py` | 延迟或不修 | — | 待裁决 |

## 本片盲区自述

- **没有实跑测试与真实变异**：判别力全靠读断言与 `Spike/P1S6R12-F/p1/` 下的函数级模拟；`test_cash_flow` 两例 `PH-P1063` 用例的判别力是按 `sync_subtotal` 代码推的，没有在站点上验证 `_validate_items` 不会先抛别的错（R11 回归通过反推它不会）。
- **测试站完全没查**：SL-002 ①（迁移后子表 `parenttype`、URL 打开）与 HT-006 探针只核了 D 回执与演示站现状；演示站底稿 0 条，`parenttype` 无从查起。
- **没往这些方向找**：`bench build` 实际会不会给 `frappe_china` 产 `.mo`（本 app 无 `locale/` 目录，推断不会）；后台任务（`frappe.local.job`）下 `_()` 的语言；全新装站跑 `install-app` 时补丁被标记已跑的路径（只读了 HT-006 引的上游码）；`frm.call` 在**未保存**的新底稿上取明细的行为（D 截图只覆盖已保存草稿）。
- **拿不准处**：
  - P1-01 定「中」还是「低」在边界上：演示站上能让法定列头被译、又不经 `Translation` 表的来源，只有与测试站不同的 app 集合或 `.mo`，目前两站一致，实际漏网面小；但它让开发守则规定的那条命令对第 4 项给出无效的「通过」，且与 `PH-P1030` 同类，所以定「中」。改判「低」也说得通。
  - P1-02 是否算「方案外夹带」：改动无语义，但违背了 S4 专门立的字节约定和 `.gitattributes` 的明文意图，且提交信息与此无关、无人申报，按 F Spec 第 7 条记为发现；建议档位给「本Session修」是因为还原只需取回旧字节，但这一步涉及工作区写入、提交仍须另问。
  - P1-06 的豁免是 Part2 提交加的，文件在本片范围内才在这里报；收口时若 Part2 片也报了，按一条合并。
