# 审核报告 Part1（片 1：译名数据、取词法与质量守卫）

**轮次**：P1-S6-R13 F 复核｜**日期**：2026-10-14｜**执行者**：Claude（Opus 5.5，片 1 子 Agent，只读）
**被审对象**：`frappe_china` `d441e9f..1d0697e`（R12 当场修 `68476a3` ＋ SB `1d0697e`）中本片文件；主仓库 `9657ca8..5775760` 中 `Spike/P1S6R4-baseline.py`、`docs/开发守则.md:103-105`
**依据**：R12 F 审核报告问题清单与用户裁决（FD-008、009、010、012、013、014、015、017、021）；SB 修复回执「用户裁决」表与 SB-3～SB-9 行；`bricks/audit.md`、`F-codeAudit-plannedDev-audit.md`
**证据**：`Spike/P1S6R13-F/p1/`（脚本与 `.out`；`baseline.json` 已删，重跑 `python -I -X utf8 Spike/P1S6R4-baseline.py --out Spike/P1S6R13-F/p1/baseline.json` 即得）

## 覆盖自证

实际查了：

- 本片 7 个文件的 `d441e9f..1d0697e` 全部 hunk，`Spike/P1S6R4-baseline.py` 与 `docs/开发守则.md` 的 `9657ca8..5775760` diff，逐 hunk 归属到 FD 号。
- 宿主复算（`python -I -X utf8`，函数从测试文件抽出 exec，不 import frappe）：
  - 新旧取法的全 app 取词：`extract_probe.py`
  - 三条取法用例、`probe_forms` 12 例：同上
  - 五道守卫全 csv 计数，39 条 QE 按道实测、与登记的守卫集对比：`quality_probe.py`
  - csv 排序、重复键、列数，6 行新增的占用，法定列头宽口径撞名：`csv_checks.py`
  - 基线脚本重跑（27 键）：`baseline.log`
  - 出处索引盲区：`index_blindspot.py`
  - 清场脚本 `--dry-run`：前后 md5 相同
- 判别力：`mutate.py` 在内存里对取法打 6 个变异、对守卫打 8 个，不写盘。
- 上游读码：
  - babel 的 JS 与 Python 取词怎么反转义（`jslexer.unquote_string`、`extract._parse_python_string`）
  - `select.js:82`、`select.js:172` 的 context 传法，`bulk_operations.js:65-69`
  - `print_settings.json`、`navbar_item.json`
  - `Expenses` 在各 app `zh.po` 里的译文
- 两站只读 SELECT（`q_persisted.sql`，经 `bench mariadb`）：`tabAccount`、`tabDesktop Icon`、`tabWorkspace Sidebar` 里有没有「报销管理」，`tabTranslation` 行数。

跳过及原因：

- 没跑 `bench run-tests`，按约束不跑，主会话在跑全量。依赖站点的用例（`test_named_terms`、`test_every_app_source_string_has_chinese`、覆盖清单交集断言）只读了代码，没实跑。
- FD-010 的三个状态、FD-009 的两条 context 行没在站点上实页看。SB 也没有实页截图，本片同样没做。
- FD-016 ② 对 `test_named_terms` 的改动归片外。

## 逐项复核

| FD 号 | R12 要求与裁决 | 落地位置 | 落地 / 生效 / 根因 | 复算结果 | 结论 |
|---|---|---|---|---|---|
| FD-008 | 删掉无 context 的 `Expenses,报销管理`，回落官方「费用」。SB 时用户裁定首页图标也随之显示「费用」，不加前端补丁 | `zh.csv`（删行）、`translation_overrides.py`（删登记）、`test_named_terms.py:43`（`Expenses`→「费用」） | 落地✅。生效✅：csv 里 `Expenses` 0 行；erpnext `zh.po:20267` 是「费用」，hrms 没有自带译文，回落 erpnext。根因✅：两站 `tabAccount`、`tabDesktop Icon`、`tabWorkspace Sidebar` 里没有写死的「报销管理」，`tabTranslation` 0 行 | `csv_checks.out` ②：`Expenses rows: []`。`q_persisted.sql` 两站都只有 `translation_rows 0` | ✅ |
| FD-009 | ① 基线脚本另建源码出处索引；② 27 键逐条判。用户裁定：`Ledger`、`Item Type` 两处写 context 行；`Credit Note`／`Debit Note` 登记 `SH-P1S6007` | `P1S6R4-baseline.py`（`source_index`、`pot_refs`、`official_overrides` 加两字段）；`zh.csv:2680`、`:2780`；`test_named_terms.py` 两键 | 落地✅。生效✅：`Print Settings`、`Navbar Item` 的 Select 走 `add_options(..., df.parent)` → `__(v, null, doctype)`（`select.js:82,172`），两行能命中。根因⚠：索引只扫 `_()` 与 json 的 label、options。`Ledger` 作纸型还出现在列表批量打印对话框的「Page Size」下拉（`bulk_operations.js:68` 取 `meta.js:278` 的裸数组；Dialog 没有 doctype，context 为空），那里仍显示「会计账簿」，见 P1-03 | 重跑基线：114 条覆盖，无 context 112 条，有未记出处的 27 条，键集与 SB `hidden.txt` 逐键相同。缺口与 identity 计数全 0 | ⚠（主体完成，残留一处，P1-03） |
| FD-010 | 补 `Partly Paid`、`Unpaid and Discounted`、`Partly Paid and Discounted` 三条 `:Sales Invoice` 行，先跑占用核查，进 `NAMED_TERMS` | `zh.csv:3444-3445`、`:5242`；`test_named_terms.py:48-50` | 落地✅、排序✅。生效：读码与 SB 一致（渲染路径与 `Unpaid:Sales Invoice` 同一条），没有实页 | 三个译文在 csv 里只出现在本行，在五个 app 的 `zh.po` 里 0 处（raven 没有 `zh.po`） | ✅（没有实页，同 SB） |
| FD-012 | 二选一：改守则，或扩取法。SB 选扩取法，并补反例 | `test_translations.py:97-136`（`ast.walk`、JS 整条赋值语句、反引号、第三参 context）；新用例 `test_source_strings_follow_a28_wording`；`开发守则.md:105` | 落地✅、生效✅（清场脚本 exec 的是同一个函数）、根因✅（守则与取法一致）。副作用见 P1-02：JS 认名正则 `\w*sources?` 本来就宽，扩取法后标量、对象值也会被取 | 全 app 取词新旧 280＝280，差集空。`probe_forms` 旧 5/12、新 12/12。三条取法用例 3/3 绿。4 个 FD-012 变异（去 `ast.walk`、去第三参 context、去反引号、不跳过 `${}`）都被新用例杀掉 | ✅ |
| FD-013 | 恢复 `\\.`（两处），补带转义引号的片段，先红后绿 | `test_translations.py:101`、`:134`；`test_source_strings_keep_escaped_quotes` | 落地✅、生效✅（不再截断）。根因⚠：取出的键保留了反斜杠（`Can\'t save`），而运行时键与 babel 取的键都是反转义后的 `Can't save`。所以 R12 说的后果仍在：清场照样删掉那行，覆盖清单照样报一个怪键。见 P1-01 | 变异 `\\.`→`\.` 被杀。转义探针 4 例的提取键与运行时键都对不上。本 app 与 frappe／erpnext／hrms 的 Python 源码里目前 0 处触发 | ⚠（P1-01） |
| FD-014 | 删掉 `source not in NAMED_TERMS` 豁免（R12 当场修） | `test_translations.py:226-229`，并删掉不再用的 import | 三层✅：豁免与 import 都已删，断言恢复完整 | 宽口径 138 个法定列头，csv 撞名 0 行 | ✅ |
| FD-015 | `_duplicate_keys` 计数前先归一字面 `\n`，补反证（R12 当场修） | `test_translations.py:185-192`；`test_duplicate_key_detector_normalizes_escaped_newline` | 三层✅：与清场脚本 `row_key`、`translate.py:204` 同一归一 | 去掉 `.replace` 的变异被杀；全 csv 重复键 0 | ✅ |
| FD-017 | `QUALITY_EXCEPTIONS` 改为「键 →（守卫名, 理由）」；「译文等于源词」进测试；第五道台湾用词表按用户裁决不加 | `test_translation_quality.py:69-111`（新结构）、`:131-140`（`_waived`、`_report`）、`:172-203`（`find_identity`、`GUARDS`、`GUARD_NAMES`）、三条新用例；`开发守则.md:103` | 落地✅、生效✅（`guard_problems` 与 `guard_scan.py` 都走 `GUARDS`）、根因✅（QE 只豁免实测命中的那几道）。判别力缺一处：没有用例断言 identity 在 `GUARDS` 里，见 P1-04 | 五道全 0。39 条 QE：38 条 `{mixed}`、1 条 `{mixed, word_by_word}`，与逐道实测命中完全相同，多登 0、少登 0。旧结构下 39 条都是四道全免，等于每条多免 2～3 道。8 个变异杀掉 7 个，「identity 移出 `GUARDS`」存活 | ✅（判别力缺口记 P1-04，观察） |
| FD-021 | `Stock Ledger Invariant Check` 定新词、进 `OVERRIDES`；`Stock Balance` 不改（R12 当场修） | `zh.csv:4689`；`translation_overrides.py:104` | 三层✅：报表名唯一出处是 `stock_ledger_invariant_check.json` 的 name（main.pot 有记） | 「库存台账一致性检查」在 csv 与 po 里的占用为 0；排序正确 | ✅ |

## 自证复核

| 声称（SB 回执／R12 当场修清单） | 实测 | 一致否 |
|---|---|---|
| 114 条覆盖，无 context 112 条，有未记出处的 27 条（SB-4） | 重跑基线：114／112／27，键集与 `hidden.txt` 相同 | 一致 |
| 基线出处索引耗时约 40 秒 | 本机全程 5.4 秒（有文件缓存，与测量口径有关） | 不影响结论 |
| 改前改后全 app 取词都是 280 键、差集空（SB-6、SB-7） | 280＝280，差集空（对比的是 `d441e9f` 版取法） | 一致 |
| `probe_forms` 12/12 OK，原 5/12（SB 复验表）；SB-6 行写的是「改前 7 例 MISS」 | 旧 5/12、新 12/12，两个数自洽 | 一致 |
| 全 csv 五道守卫均 0（SB-9） | 五道全 0 | 一致 |
| 39 条 QE：38 条 `mixed`，1 条 `mixed`＋`word_by_word`（SB-9） | 相同，且与逐道实测命中一一对应 | 一致 |
| 全 csv 只有 `JAN,JAN` 一行译文等于源词，且它在 `UNTRANSLATED` 里（SB-9） | 相同 | 一致 |
| 新词在 csv 与六个 po 里的占用为 0（SB-4、SB-5、FD-021） | 6 个新译文在 csv 里都只出现在本行；po 里 0 处（raven 没有 `zh.po`） | 一致 |
| `test_translations` 20 条、`test_translation_quality` 12 条 | 数 `def test_` 得 20、12 | 一致 |
| 「取出的键保留反斜杠，与 `main.pot` 取词口径一致」（SB-7） | babel 取 JS 时用 `unquote_string`，取 Python 时用 `compile` 求值，两者都反转义：`'Can\'t save'` 取成 `Can't save`。本函数取成 `Can\'t save`。**口径不一致** | **不一致**（P1-01） |
| 清场脚本「AST 摘取不受影响」（SB-6） | `--dry-run` 跑通：原 5756 行，保留 323，删 5433，与 R12 FD-035 的数相同；csv md5 前后相同 | 一致 |
| R12 当场修 FD-014：「删掉豁免后仍绿，说明豁免没放过任何行」 | 宽口径撞名 0 | 一致 |

## 新发现

| # | 严重程度 | 定位 | 问题描述 | 证据 | 建议 | 建议档位 | 待裁决点 |
|---|---|---|---|---|---|---|---|
| P1-01 | 低 | `tests/test_translations.py:101`、`:134`、`:335-340`（`test_source_strings_keep_escaped_quotes`） | FD-013 恢复 `\\.` 后不再截断，但取出的键带着源码里的反斜杠（`Can\'t save`、`Say \"hi\"`）。Frappe 运行时查的键、babel 写进 `main.pot` 的 msgid、csv 里该写的键，都是反转义后的 `Can't save`。所以 R12 FD-013 说的后果没有消除：清场脚本的 `row_key` 对不上，照样删掉那行；`test_every_app_source_string_has_chinese` 照样报一个带反斜杠的怪键，只是从截断键换成了转义键。新用例把错误的键形写成了期望值，SB 回执里「与 main.pot 口径一致」的说法不成立。目前 0 处触发 | `extract_probe.out` ④：4 例的提取键与运行时键都不相同。`csv_checks.out` ④：`kept by prune: False`。babel 的 `jslexer.py:94-150` 反转义；`extract.py:628-645` 用 `compile` 求值 | 取法里反转义：Python 侧对匹配到的字面量 `ast.literal_eval`（或直接用 AST 里 `_()` 调用的 `Constant`），JS 侧按 JS 规则去掉转义反斜杠；新用例的期望值改成运行时形态，另加一例断言清场能保住 csv 里 `Can't save` 那行 | 新Session修（或延迟或不修：现状 0 触发） | 修，还是记为潜在风险登记 |
| P1-02 | 观察 | `tests/test_translations.py:121`（JS 认名正则 `(?:const\|let\|var)\s+\w*sources?\s*=`，`re.I`）；`开发守则.md:105` | 认名正则把凡以 source／sources 结尾的 JS 变量都当源词常量，例如 `let source = frm.doc.source \|\| "Manual"`、`const resources = {url: "/api/…", method: "GET"}`。FD-012 之前只取方括号里的串，这类写法大多取不到东西；现在标量、对象值都取，就会把 `Manual`、`GET`、URL 当成本 app 源词。后果是偏向多留（清场多保留），以及 `test_every_app_source_string_has_chinese` 要求这些串有中文。Python 侧的 `DATA_SOURCES = {"mysql": …}` 连 dict 键也取，SB 已申报，按守则原文成立。本 app 现有代码只有 `independent_app_labels.js:3` 的 `const sources = {…}` 命中，取词不变 | `extract_probe.out` ⑤：新取法取到 `['Manual']`、`['/api/method/frappe.client.get', 'GET']`、`['MariaDB', 'PostgreSQL', 'mysql', 'pg']`，旧取法都是空 | 下次写这类变量时注意命名；或把 JS 认名收窄到「标识符整体以 `SOURCE(S)` 结尾、且前面有前缀或全大写」，与 Python 侧 `SOURCES?$` 对齐 | 延迟或不修 | 是否收窄 JS 认名 |
| P1-03 | 低 | `Spike/P1S6R4-baseline.py` `source_index`；上游 `frappe/public/js/frappe/list/bulk_operations.js:65-69`、`model/meta.js:250-283` | FD-009 的索引只认 `_()`／`__()` 字面量与 json 的 label、options（R12 建议的范围就是这些）。不经 `__()` 的裸数组没收进来，例如 `frappe.meta.get_print_sizes()`。列表视图「批量打印」对话框的「Page Size」下拉用的就是它，Dialog 没有 doctype，context 为空，于是走无 context 键：`Ledger` 在这里仍显示「会计账簿」。`Ledger,账簿纸,Print Settings` 只修好了打印设置表单一处。同类没进索引的形态还有 json 的 `name`（报表、打印格式、DocType 名）、`description`、`link_to`。逐项看过，除 `Ledger` 外都同义（`Stock Ledger Invariant Check` 的出处正是报表 name）。另外 Raven 的 emoji 数据里有 `"name": "Ledger"`，是否经翻译显示没查 | `index_blindspot.out`：json 非 label 出处 19 个键，裸 JS 数组命中 11 个键；`select.js:82` 的 context 取 `df.context \|\| df.parent \|\| this.doctype`，Dialog 里三者皆空 | 二选一：批量打印的纸型登记接受（不在演示线上）；或在 `frappe_china` 的前端补丁里给该对话框的 Select 补 `df.context="Print Settings"`。另外，索引是否扩到 json name／description 与裸数组，由用户定 | 延迟或不修（或出方案修） | 批量打印对话框的纸型显示「会计账簿」接受不接受 |
| P1-04 | 观察 | `tests/test_translation_quality.py:198`（`GUARDS`）、`:3`（docstring） | 没有用例断言 `find_identity` 在 `GUARDS` 里：把它移出 `GUARDS`，12 条用例全绿，而 `guard_problems`（覆盖清单 ours 的检查、`guard_scan.py`、`apply_rows.py`）会悄悄少查一道。`test_no_untranslated_rows` 直接调 `find_identity`，不经 `GUARDS`，所以拦不住。另外模块 docstring 第 3 行还写着「这四个用例」 | `mutate.out`：`FD-017: identity 移出 GUARDS: 8 run, all green` | 加一行 `assertEqual({g.__name__ for g in GUARDS}, {...五个...})`，或用 `guard_problems([["Upload Photo","Upload Photo"]])` 断言非空；docstring 改成「五道」 | 延迟或不修 | — |
| P1-05 | 观察 | `tests/translation_whitelist.py:112`（`JAN`）；R12 FD-036 | R12 FD-036 判白名单里的 `JAN` 多余，建议「下次动白名单时删掉」，裁为「不做」。FD-017 加了 identity 守卫，它靠 `UNTRANSLATED` 放过 `JAN,JAN`，这条登记就不再多余：照 FD-036 的建议删掉，`test_no_untranslated_rows` 会变红。这次修复改变了 FD-036 的前提 | `mutate.out`：`FD-036 连带: 白名单删 JAN: … red=['test_no_untranslated_rows']` | FD-036 的「建议」作废，`JAN` 留在白名单里，在登记处注明它是 identity 守卫的放行依据 | 延迟或不修 | FD-036 结论是否改为「保留」 |

R12 观察项状态有变的，除 P1-05（FD-036）外还有一项：FD-035 的 `NAMED_SOURCES`（36 个）与 `NAMED_TERMS` 的差距，从 75 扩大到 81（本次 +6，其中 FD-008 +1、FD-009 +2、FD-010 +3）。属同一问题加重，已裁「不做」，不另编号。清场 `--dry-run` 仍删 5433 行，与 R12 相同。

方案外夹带：本片文件的 hunk 都能归到 FD-008、009、010、012、013、014、015、017、021，或片外的 FD-016 ②（`test_named_terms.py:113-128`）、FD-024（`开发守则.md` 新节）。没有发现夹带。

## 交接摘要

依赖：

- 全量回归的实测数（主会话）。
- 片外 FD-016 ② 的 `_official_timesheet_terms` 改动。
- SL-006 让 Select／徽标带上 context 这一前提：FD-010 的三行、FD-009 的两行都靠它生效，本片只读了 `select.js`。

暴露：

- 取法 `_source_strings_from_text` 被清场脚本 exec，P1-01、P1-02 会直接影响清场判据。
- `GUARDS`／`guard_problems` 的接口没变，多了 identity 一道，供 `test_translations.test_override_basis_forms`、`Spike/P1S6R7/guard_scan.py`、`apply_rows.py` 复用。
- `official_overrides[]` 多了 `source_refs`、`hidden_refs` 两个字段。
- P1-03 的纸型残留涉及前端补丁的片，如果选「补 context」，归那片的文件。

## 盲区自述

- 没在站点上实跑任何用例，也没看实页。依赖站点合并字典的结论（`Expenses` 回落「费用」、三状态与两条 context 行生效），只有读码与 SB 日志支撑。
- P1-03 只沿「裸数组」和「json 的几个常见键」两个方向扫。Vue／TSX 里的非 `__()` 取值、`frappe.ui.form.make_control` 以外的渲染路径没有穷举。`Ledger` 在批量打印对话框里的显示是读码推断，没有实页截图。
- P1-01 只看了 frappe、erpnext、hrms 的 Python 和 JS 里有没有转义引号源词，CRM、Insights、Raven 的前端没扫。
- FD-009 的 22 个「同义不改」只抽读了几条出处，没有逐条重判；会计判断类没有能力判。
- 变异实验都在内存里改源码文本，只跑了不依赖站点的用例。对 csv 数据本身的变异（如删一行 context 行）没做，那要站点上的 `test_named_terms` 才能判。
