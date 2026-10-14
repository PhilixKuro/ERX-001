# F 审核分片报告 · 片 7（横切片，对象：经确认报告裁决落地的代码改动＋全 Stage 方案外夹带 / 审核标准：R5／R8／R11 E 报告已裁决项＋R3／R6／R9 开发方案任务清单）

**轮次**：P1-S6-R12｜**步骤**：F 分片 7｜**日期**：2026-10-13｜**执行者**：Claude 子 Agent（只读）
**依据**：F Spec 预设提示词第 7 条「查方案外的夹带」；`bricks/audit.md`、`bricks/sharding.md`；[R5 E确认报告](../R05-确认/P1-S6-R5-E确认报告.md)（问题详情、用户裁决、当场修清单）；[R5 SB修复回执](../R05-确认/P1-S6-R5-SB修复回执.md)；[R8 E确认报告](../R08-确认/P1-S6-R8-E确认报告.md)；[R11 E确认报告](../R11-确认/P1-S6-R11-E确认报告.md)；R3 方案 Part1～4、R6 方案、R9 方案的任务清单与 TS 节（作「改动属于哪个任务」的映射）；R4 回执 Part1～4 与三份方案补充（DEC-024～027）、R7 D 回执、R10 D 回执；`docs/开发守则.md`；`docs/业务规则.md`；S4 [R7 开发方案 Part1](../../S04-中国财税/R07-开发方案/P1-S4-R7-C开发方案-Part1.md) TS-005 与 S4 R12 SB 回执 IT-035（只读了科目表字节一致那两行）
**被审范围**：`frappe_china` `474cd1c..d441e9f` 共 14 个提交；主仓库 `D:\ERX-001` 自 2026-10-08 起改到 `docker/`、`.gitignore`、`Spike/` 脚本的提交（`4de6d93`、`bdf2667`、`a626c04`、`d43dc77`、`862d131`、`498bd8a`、`48f1939`、`03dd823`、`a32e852`、`a9dfa71`、`8d58387`）；主仓库 `.git/info/exclude` 与当前工作区状态

## 覆盖自证

- **逐 hunk 看完的提交**：`af015fa`、`3f9511a`、`4f75f5a`、`d441e9f`（四个裁决落地提交，全部文件，含 csv 的 11 行改动）；`db9541a`、`52f8064`、`c2b0420` 的全部非 csv 文件（`52f8064` 的 `workspace_sidebar/business_flow.json` 585 行只看了结构与 `modified`，条目逐行对照归片 3／R5 已做）；`1779cf0` 的 README、`hooks.py`、两个 JS、`test_translations.py`；`35b5b77` 的 `hooks.py`、`desk_patches.js`、四个模板、`website_translation.py`、`test_desk_titles.cjs`、README 的增删行；`06cbf4f` 的 `crm_sidepanel.py`、`desk_patches.js`、`independent_app_labels.js`（取 `474cd1c..d441e9f` 全文 diff）、`crm.html`、`test_translations.py`、`test_website_translation.py`、`test_named_terms.py`、`translation_overrides.py`、`translation_whitelist.py`、`website_translation.py`；`86538ba` 的增删行；`1d51db2` 的 `translation_overrides.py`。
- **只看了 stat 或开头的**：`zh.csv` 全程只看 hunk 归属与行数（任务说明归片 5），另查了冲突标记（0 处）与文件头；`1779cf0` 的 `translation_overrides.py`（211 行乱码依据，已被 R5 IT-003／R7 TS-017 整份重建，不再复核）与 `test_named_terms.py` 后半；`deb226f` 的 `translation_overrides.py`（348 行）、`translation_whitelist.py`（220 行）只看 stat，`test_translation_quality.py` 只看前 40 行，内容归 TS-016／017 所在片；`06cbf4f` 的 `test_desk_patches.cjs`（398 行）、`test_crm_sidepanel.py`、`test_independent_app_labels.cjs` 只看 stat；`cf8a9ba` 只有 csv 2 行。
- **主仓库**：`docker/` 自 S5 收口 `68f8f05` 到 HEAD 全量 diff（只有 `README.md` +7 行与 `apps.json` 一行）；`.gitignore` 在 S6 无改动；`Spike/` 只看了文件清单、`8d58387` 里 `it018-run.sh` 与 `own-keys.py` 的 diff、受管脚本对未受管文件的引用、受管 `.log` 清单。主仓库 `docs/` 的改动不在本片。
- **实跑（只读）**：宿主 `node --test frappe_china/tests/*.cjs` 71/71；`Spike/P1S6R12-F/p7/` 下四个 `python -I` 脚本（缩进与 BOM 扫描、科目表字节比对、取词正则转义比对、按 `_app_source_strings` 口径抽 R9 自有键、csv 译文与法定列头撞名）；`git diff --check 474cd1c d441e9f`（非 csv，无输出）。**未跑**：`bench run-tests`（主会话在跑全量）；ruff（宿主与 bench 环境都没有装，见开发守则「工具链索引」）。

## 当场修与 SB 逐项核

每个 hunk 都归到了一条已裁决项，没有归不上的。

| 提交 | 文件:行 | 对应 IT | 裁决档位与日期 | 改法与报告「建议」一致否 | 三层生效 | 越界否 |
|---|---|---|---|---|---|---|
| `af015fa` | `tests/test_translation_check.py:86-87` | R5 IT-002 | 本Session修，2026-10-11「按建议来」 | 一致（只认「法定列头被翻译：资产」前缀） | 代码在；用例在全量里跑（R11 266/266）；第 1 项的「资产」不再能顶替第 4 项 | 否 |
| `af015fa` | `tests/test_translations.py` `_tokens`／`_PLACEHOLDER`／`_HTML_TAG`，新用例 `test_token_check_detects_reordered_html_tags` | R5 IT-015 | 同上 | 一致（占位符比多重集合，标签按序列比） | 在；在跑；根因消除。当时 `_PLACEHOLDER` 还会吞掉未闭合的 `{{`，后由 R8 IT-044 修 | 否 |
| `af015fa` | `README.md:55-69`（删旧三行，新增 SL-006 五栏表） | R5 IT-014 | 同上 | 一致（五栏齐） | 在。行号 `desk_patches.js:97-102` 当时是对的（核过 `git show af015fa:…desk_patches.js` 第 97-102 行就是 Select formatter），`06cbf4f` 插入 119 行后失效，R11 IT-054 改成函数名锚点 | 否 |
| `af015fa` | `README.md` SL-008 表第一行 | R5 IT-019 | 同上 | 一致（`:61-95`，并补「复刻 114-134 行」） | 同上：当时对，R10 后失效，IT-054 修 | 否 |
| `3f9511a` | `tests/test_translations.py:332` `_PLACEHOLDER`；新用例 `test_placeholder_requires_closing_brace`；`zh.csv` +1 行（Naming series）；`translation_whitelist.py` −1 行 | R8 IT-044 | 本Session修，2026-10-12「其它建议来」 | 基本一致。建议栏写的是 `\{\{\s*[^{}]+?\s*\}\}`，实际是 `\{\{?\s*[^{}]+?\s*\}\}?`（单花括号 `{label}` 也要认），当场修清单里如实写了实际正则 | 在；在跑；该键已移出白名单、csv 有译文 | 否 |
| `3f9511a` | `test_translations.py` `_misused_own_basis` 与新用例 | R8 IT-045 | 同上 | 一致 | 在；在跑（`test_override_basis_forms` 调用它） | 否 |
| `3f9511a` | `tests/translation_overrides.py`：4 条依据 DEC-026 改 DEC-027，删 10 条；`zh.csv` 删同样 10 行 | R8 IT-046 | 同上 | 现象栏写「3 条」，实际改了 4 条，多出的是同族按钮 `Get Items for Purchase Only`。当场修清单写的是 4 条，已申报 | 删的 10 键与 csv 删的 10 行逐个对上 | 轻微：比现象多改 1 条同类项，已申报（P7-10） |
| `4f75f5a` | `public/js/desk_patches.js:33-69`（datatable 段） | R5 IT-026 | 新Session修（R5 2026-10-11）；收窄方式由用户 2026-10-13 裁决 | 与裁决一致：只听 `childList`、只扫 `addedNodes`、选择器收为 `.datatable input.dt-filter`、前缀不符告警一次、`body` 缺失告警 | Node 8 条新用例在 71/71 里；SB 做了实页撤钩与接回 | 否 |
| `4f75f5a` | `tests/test_desk_patches.cjs:319-320`（时间线用例改为按回调认 Observer） | R5 IT-026（连带） | 同上 | SB 回执已申报，期望值没动 | — | 否（已申报的连带改动） |
| `4f75f5a` | `README.md` datatable 行；独立前端引言（三个锁定提交与 `bridgeMessages` 偏离） | R5 IT-026、IT-027 | 新Session修 | 一致。CRM `deedce73…`、Raven `e890308e…`、Insights `5447f162…` 与 `docker/apps.json` 逐个对上 | 文档项 | 否 |
| `d441e9f` | `public/js/desk_patches.js:94-95` | R11 IT-052 ① | 本Session修，2026-10-13「按建议来」 | 一致 | 本片用 `own_keys_check.py` 按 `_app_source_strings` 口径扫全 app：`R9_OWN_KEYS` 6 键全部取到 | 否 |
| `d441e9f` | `crm_sidepanel.py:13-14,37-38` | R11 IT-052 ② | 同上 | 一致（改名 `READ_ONLY_TOOLTIP_SOURCE`） | 同上（只读提示键取到了） | 否 |
| `d441e9f` | `tests/test_translations.py` `R9_OWN_KEYS`、`test_r9_own_keys_are_app_sources` | R11 IT-052 ③ | 同上 | 一致（3 键加 `(Empty)`、`Add {0}...`、`Select {0}...`） | 先红后绿日志 `Spike/P1S6R11-E/fix/red.log`／`green.log` 在 | 否 |
| `d441e9f` | `tests/test_translations.py:117` JS 正则 `sources?`；单数用例 | R11 IT-053 | 同上 | 一致 | 本片实测 `const FOO_SOURCE = ["H"]` 取到 `{'H'}` | 否 |
| `d441e9f` | `README.md:63-65,75,100` | R11 IT-054、IT-055 | 同上（IT-055 取「接受代价」） | 一致。核了 `general_ledger.py:560,562` 确实对 `against_voucher_type`、`party_type` 做了 `_()`；ERPNext `12cd563f…` 与锁一致 | 文档项 | 否 |
| `8d58387`（主仓库） | `Spike/P1S6R9/own-keys.py`、`Spike/P1S6R5-SB/it018-run.sh:15-16`、`docker/README.md:154-160`、`docker/apps.json` | R11 IT-052 ④、IT-057、IT-059；锁推进 | 同上 | 一致 | — | 否 |

小结：四个提交没有越出裁决范围。唯一多出的是 IT-046 的第 4 条按钮依据，属同类，已在当场修清单申报。

## 夹带扫描

`474cd1c..d441e9f` 每个文件的每个 hunk 都做了归属。下表只列**归不上**或**归得上但带了额外改动**的 hunk；其余都对得上 TS 或 IT（归属清单见「集成点登记」）。

| 提交 | 文件:行 | 改了什么 | 归属 | 类别 | 申报否 | 对应问题 |
|---|---|---|---|---|---|---|
| `52f8064` | `cn_tax/chart_of_accounts/cn_smes_chart_of_accounts2024.json` 首 4 行与末 4 行 | CRLF 改成 LF，并补了文件尾换行；sha256 从 `539d12f5…867972`（zelin 原件，S4 TS-005／S4 R12 IT-035 的验收值）变成 `e9238dec…`；index 里成了 `i/mixed` | 无（S6 没有任务碰科目表） | 编辑器或脚本顺手改（同 R4 Part1 回执自述的「批量误写 BOM 和文件尾空行」） | 没有（R4 Part1 回执第 54 行只泛泛写了「仍有文件尾换行差异」，而且是在 Part1 时点） | P7-01 |
| `52f8064` | `accounting/hr.py:141`、`tests/test_hr.py:56` | 只补了文件尾换行 | 无（S5 文件） | 顺手格式化，没有语义 | 没有 | P7-01（同因） |
| `db9541a` | `cash_flow_worksheet.py:1`、`tests/test_translation_check.py:1`、`tests/translation_overrides.py:1` | 写进了 UTF-8 BOM | TS-004／003 | 工具残留 | R4 Part1／Part3 回执已披露。`1779cf0`、`c2b0420` 已清掉，HEAD 全仓 0 个 BOM 文件（`scan_style.py`） | 已消除，不另立 |
| `db9541a` | `patches/s6_rename_cash_flow_worksheet.py`、`translation_check.py`、`tests/test_translation_check.py`、`tests/test_cash_flow_rename.py`、`tests/test_s6_closing_separator.py` | 整个文件用 4 空格缩进；`pyproject.toml` `[tool.ruff.format] indent-style = "tab"` | TS-002～005 | 格式不合项目约定 | 没有 | P7-05 |
| `1779cf0` | `tests/test_translations.py:218` | 法定列头撞名断言加了 `and source not in NAMED_TERMS` 豁免 | 无。R3 方案 Part2 TS-006／007、需求 §4.2.5 ④ 都只要求「不与法定列头同名」，没有豁免 | 放宽测试判据 | 没有（S6 各回执与报告里搜 `NAMED_TERMS` 与此相关，0 处命中） | P7-04 |
| `06cbf4f` | `tests/test_translations.py:101`、`:130` | 取词正则 `(?:\\.\|(?!\1).)*`（反斜杠转义）变成 `(?:\.\|(?!\1).)*`（字面点号），引号内的 `\"` 不再算转义 | TS-025 要求拆函数、补三类写法，「现有 `_()`／`__()` 字面量调用」照旧 | 顺手改动引入的回退 | 没有；R11 E 没检出 | P7-03 |
| `06cbf4f` | `public/js/desk_patches.js:140`（注释）、`README.md:66` | 指向 `Spike/P1S6R9/upstream-it035.md` | TS-030 | 引用了另一个仓库里的路径 | — | P7-08 |
| `db9541a` | `tests/test_s6_closing_separator.py`（新文件） | TS-005 ⑥ 方案写「`test_closing` 加两例」，实际另建了一个文件 | TS-005 | 位置偏离 | 回执列了文件名，没写成偏离 | P7-09 |
| `c2b0420` | `cash_flow_worksheet.py:1`、`tests/test_translation_check.py:1` | 去掉 BOM（Part1 的残留） | 修 `db9541a` 的残留 | 跨 Part 混进导航提交 | R4 Part3 回执已披露 | P7-07 |

**全 app grep**（`git grep` 于 `d441e9f`，排除 csv）：
- `console.log`、`debugger`、`TODO`、`XXX`、`FIXME`、`HACK`：0 处。
- `print(` 7 处：`translation_check.py:48,50` 是 TS-002 ③ 约定的「`run()` 打印并返回」；其余 5 处（`install.py:167`、`patches/fd004_default_accounts.py:29`、`realtime_check.py:78,92`、`tests/test_statement_dataset.py:28`）都是 S6 之前就有的（`git log -S` 起点为 `1193f94`、`21faeb9`、`7c7145b` 等），不在本 Stage 改动面。
- 写死的站点名或路径：只有 `README.md:34-39` 的 `test.localhost` 用法说明，属文档。
- S6 新增行里被注释掉的代码块：0 处（扫 `^\+\s*(#|//)` 后跟代码形态，命中的都是说明性注释）。`hooks.py` 里的 `# app_include_css = …` 等是上游脚手架原有行。

## 业务规则合规核

| 规则条款 | 本 Stage 改动涉及否 | 结论 | 备注 |
|---|---|---|---|
| BR-001 小企业会计准则科目表 | 涉及：`52f8064` 改了科目表 json 的换行字节 | 合规（内容未变） | `coa_cmp.py`：两版 `json.loads` 相等，去掉 CR 与文件尾换行后逐字节相同。科目、编号、类型都没变；变的是 S4 的「逐字节复制」可追溯性，见 P7-01 |
| BR-002 财务报表构成 | 涉及：法定列头守卫（P7-04 的豁免会放过「现金流量表」「应收账款」） | 合规（现状） | `legal_collide.py`：csv 5751 行里，译文等于三份报表文件中任一汉字字面量（宽口径 138 个）的行为 0；豁免目前没有放过任何一行 |
| BR-003～BR-007（税率、价税分离、增值税结转、附加税、恒等式） | 不涉及 | — | `closing.py` 只改了提示语分隔符（TS-005 PH-P1052），没动结转计算；`unmapped.py` 只给列加了币种 |
| 本片总体 | — | 没有新增或变更的领域不变量 | 本片涉及的都是译名、导航、测试与版本卫生，不触发规则送审 |

## 集成点登记（交接摘要）

**hunk 归属清单（本片暴露，供收口比对）**
- R4：`db9541a` → TS-002（`translation_check.py`、`labels.py`）、TS-003（`test_translation_check.py`、`test_translations.py` 前半、`translation_overrides.py`）、TS-004（改名、补丁、引用、`dataset.py` 等）、TS-005（`closing.py`、`unmapped.py`、底稿 js／json／py 的按钮与空明细提示、结转确认框）；`1779cf0` → TS-006（`test_named_terms.py`）、TS-007（`_tokens`、csv）、TS-008（`invoice_list.js`、Select formatter、`hooks.py`）；`1d51db2` → TS-007（DEC-023 修复批）；`52f8064` → TS-010（图标、svg、侧栏 json、导航测试）、TS-012（`doctype_js`、`opening_ledger.js`、StockController 包装）；`c2b0420` → DEC-024（SidebarHeader）、DEC-025（`cn_tax.json` 的 `modified`）、TS-012 修正、TS-010 `modified`；`35b5b77` → DEC-026（独立前端）、DEC-027（ControlButton、AwesomeBar）、方案外 datatable 段（R5 IT-026 已追认）、IT-032 stub（已追认）。
- R7：`deb226f` → TS-016～021；`cf8a9ba` → TS-023。R10：`06cbf4f` → TS-025～034；`86538ba` → TS-037。
- 当场修／SB：见上节表。

**本片发现需要别的片交叉核的点**
- 管 TS-025 的片：P7-03 的正则回退在 `_source_strings_from_text` 里，清场脚本 `Spike/P1S6R6-csv-prune.py` 会 exec 同一个函数，所以清场判据也受影响。
- 管 TS-003／006 的片：P7-04 的豁免改变了 SL-001／需求 §4.2.5 ④ 的判别力。
- 管 TS-022／023／036 逐屏核与 SB IT-018 的片：它们的证据脚本都 `require` 未受管的 `Spike/P1S6R4-cdp.cjs`（P7-02）。换机器之后，「可照做」只在本机成立。

**本片依赖**
- 片 5：csv 内容质量（本片只看了 hunk 归属）。
- 跨片共享状态：`docker/apps.json` 七条锁与各 app HEAD 一致（本片核了 `frappe_china` = `d441e9f`，其余六条只取锁值用来对照 README）；主仓库 `.git/info/exclude` 的 `/Spike/P1S6R4-*` 规则（不进版本，换机器会丢）。

**事件**：本片不发出、也不消费 SSE／realtime 事件。

## 自证复核

| 被审产物声称 | 实际复核 | 一致否 |
|---|---|---|
| R11：「`frappe_china` 的 `3f9511a..4f75f5a` 只改了 TS-025～034、TS-037 的 README、SB 的 IT-026／027 三类文件，没有方案外的代码文件」 | 按文件看成立；按 hunk 看，`06cbf4f` 在方案内的文件里带了一处方案外的正则行为改动（P7-03） | 部分一致 |
| R11 当场修：「`frappe_china` 只改了上表 4 个文件」 | `d441e9f` 正好 4 个文件 | 一致 |
| R8 当场修 IT-046：「4 条依据改 DEC-027，删 10 条无效覆盖」 | `3f9511a` 逐条对上；R8 现象栏写的是 3 条 | 一致（现象与修法差 1 条，P7-10） |
| SB：「本步实际改动的文件只有 `desk_patches.js`、`test_desk_patches.cjs`、README（两处）、`docker/apps.json`」 | `4f75f5a` 3 个文件，`a9dfa71` 里的 `apps.json` 一行，其余都是 `Spike/P1S6R5-SB/` | 一致 |
| SB IT-027：README 补三个锁定提交 | 与 `docker/apps.json` 逐个相同 | 一致 |
| R10 D TS-037 ⑤：「`frappe_china` 只改了 `README.md`」 | `86538ba` 只有 README | 一致 |
| R7 D TS-024 ②：「`frappe_china` 只改了 zh.csv（+2 行）」 | `cf8a9ba` 只有 csv 2 行 | 一致 |
| R4 Part1：「`git diff --check` 均通过；七处文件尾空行已清理」「仍有无业务语义的文件尾换行差异」 | `git diff --check 474cd1c d441e9f`（非 csv）无输出。但 `52f8064` 改的是科目表的行尾字节，打破了 S4 的 sha256 验收值，回执没提到 | 部分一致（P7-01） |
| R10 D 偏离第 3 条：`P1S6R4-cdp.cjs` 退出删临时目录，「不改产品代码，各调用方不用改」 | 修改只在本机：该文件被 `.git/info/exclude` 排除（`git check-ignore -v` 命中第 8 行），而受管的 `Spike/cdp-cleanup-selftest.cjs` 依赖它 | 不一致（版本层面，P7-02） |
| Node 71/71（SB、R11） | 本片宿主实跑 71/71，0 跳过 | 一致 |
| R11 IT-054 README：`general_ledger.py:560,562` 已 `_()` | 读上游第 558-562 行，属实 | 一致 |

## 问题清单

| # | 严重程度 | 定位 | 问题描述 | 违背的标准/意图 | 建议 | 建议档位 | 待裁决点 | 状态 |
|---|---|---|---|---|---|---|---|---|
| P7-01 | 中 | `frappe_china` 提交 `52f8064`：`cn_tax/chart_of_accounts/cn_smes_chart_of_accounts2024.json` 首 4 行、末 4 行；同提交 `accounting/hr.py:141`、`tests/test_hr.py:56` | S6 没有任何任务碰科目表，这个导航提交却把它 8 行的 CRLF 改成 LF，并补了文件尾换行。复现：`git cat-file -p 474cd1c:<file> \| sha256sum` 得 `539d12f5…867972`，`d441e9f` 得 `e9238dec…`；`git ls-files --eol` 为 `i/mixed`。这个值是 S4 TS-005「逐字节复制、sha256 相同」的验收值，S4 R12 SB IT-035 还专门建了 `.gitattributes`（`-text`，注释写着「保留原始 CRLF 字节」）来守它。这次等于悄悄撤销了一条已关闭的裁决。功能没受影响：`coa_cmp.py` 显示两版 JSON 解析结果相等。同一提交还给两个 S5 文件补了文件尾换行。R5、R8、R11 三次 E 都没检出 | 方案外夹带（F 预设提示词第 7 条）；S4 TS-005／IT-035；`.gitattributes` 的意图 | 按 `474cd1c` 的字节还原科目表（`-text` 下不做换行转换，还原后 sha256 应回到 `539d12f5…`），提交、推送 `frappe_china`，再跑 `lock-apps.sh`。可选：在 `test_scaffold` 加一条 sha256 断言，防止下次再被编辑器改掉。`hr.py`、`test_hr.py` 的文件尾换行无害，可以不动 | 本Session修 | ① 是否许可还原并提交推送 `frappe_china`、推进锁；② 是否加 sha256 守卫用例（属新增测试） | 待裁决 |
| P7-02 | 中 | 主仓库 `.git/info/exclude:8` `/Spike/P1S6R4-*`；`Spike/P1S6R4-cdp.cjs`（未受管）；受管的 `Spike/cdp-cleanup-selftest.cjs:13`、`Spike/P1S6R6-screen-check.js:18`、`Spike/P1S6R5-SB/it013-check.cjs:4`、`it018-refresh-check.js:6`、`it018-tree-rounds.js:2`、`it026-check.cjs:3`、`it027-check.cjs:4`、`Spike/P1S6R9/test-site-check.cjs:8`、`Spike/P1S6R7/ht017-it011.cjs:5`、`P1S6R7/ts023/{locale-probe,null-probe,receivable-shots}.cjs`、`P1S6R8-E/fix/ht017.cjs:6`、`P1S6R11-E/crm-csv/crm_live.cjs:5`（另有 `demo-readonly.cjs` 按参数传入） | R11 已把 cdp.cjs 列为清单外，本片补三条证据：① 15 个受管脚本依赖这个未受管文件，其中 14 个直接 `require`。所以换机器重建后，正式逐屏核工具 `P1S6R6-screen-check.js`、SB IT-018 交付的「可照做序列」`it018-run.sh`（它调 `it018-refresh-check.js`），以及 R10 新加的自测 `cdp-cleanup-selftest.cjs` 都跑不起来，IT-018 判通过所依据的「照着做」只在本机成立。② exclude 规则比方案授权的宽：R3 Part4 TS-014 只许把截图目录 `Spike/P1S6R4-screens/` 写进 exclude，实际规则排除了全部 `P1S6R4-*`。这条规则在 R4 中途加入（`exclude` 文件时间 10-10 16:27；此前 83 个 R4 文件已受管），没有留档。③ S6 文档引用了 33 份被排除的 R4 文件当证据，例如 R5 IT-017／031 引的 `P1S6R4-set-nav-modified.py`、`P1S6R4-nav-current-before.json`，SB 引的 `P1S6R4-migration-acceptance.json`，它们都只在本机。另外，`P1S6R4-cdp.cjs:102` 写死了开发站登录口令；`docker/README.md` 本就写了同一个默认口令，纳入版本不新增泄露面，但要知情 | 「每个发现须可复现」；开发守则「`.git/info/exclude` 不随 push 走，换机器会丢」；R3 Part4 TS-014 的排除范围；R5 IT-018「写到可照做」 | ① exclude 里加一行 `!/Spike/P1S6R4-cdp.cjs`（或把规则收窄为 `/Spike/P1S6R4-screens*/`），然后 `git add` 该文件；② 被 S6 文档引用的 33 份证据，逐份定纳入还是不纳入；不纳入的在文档里注明「仅本机」 | 本Session修（①）；延迟或不修（②） | ① 是否纳入版本（含写死的默认口令）；② exclude 收窄还是只加例外；③ 33 份被引证据的去向 | 待裁决 |
| P7-03 | 低 | `frappe_china/tests/test_translations.py:101`、`:130`（`06cbf4f` 引入） | `_source_strings_from_text` 的取词正则把 `474cd1c` `:85` 的 `(?:\\.\|…)`（反斜杠加任意字符，用来认转义引号）改成了 `(?:\.\|…)`（字面点号）。方案 TS-025 只要求「现有 `_()`／`__()` 字面量调用」照旧、另补三类写法，没要求改转义处理。复现：`python -I Spike/P1S6R12-F/p7/regex_escape.py <app>`，对 `_("Say \"hi\" now")` 旧版取 `Say \"hi\" now`，新版只取 `Say \`。目前 app 里没有带转义引号的源词（`lost_total: 0`），属潜在风险。触发时，截断的键会让 `test_every_app_source_string_has_chinese` 报一个怪键；清场脚本 exec 的是同一个函数，会认不出真键而删掉那行 csv，与 IT-043、IT-052 同类 | 方案 TS-025 第 1 步「现有…照旧」；方案外夹带 | 恢复 `\\.`（两处），并在 `test_source_strings_literal_key_forms` 补一个带转义引号的片段，先红后绿 | 新Session修 | — | 待裁决 |
| P7-04 | 低 | `frappe_china/tests/test_translations.py:218`（`1779cf0` 引入） | 「csv 译文不得与法定列头同名」的断言加了 `source not in NAMED_TERMS` 豁免，方案与需求 §4.2.5 ④ 都没有这条，S6 各回执与 E 报告也没有披露。当时为的是 `Cash Flow`→「现金流量表」、`Accounts Receivable`／`Debtors`→「应收账款」这几个定词（`labels.py:9`、`mapping.py:43` 里是法定列头）。R8 IT-046（`3f9511a`）已经把这三行从 csv 删掉、回落官方，所以豁免现在什么都没放过：`legal_collide.py` 宽口径核，撞名 0 行。但它照样放宽了判据，以后 `NAMED_TERMS` 里任何键的 csv 译文撞上法定列头都不会报 | 需求 §4.2.5 ④（LG-134）；方案外夹带（放宽测试判据） | 删掉这条豁免，恢复完整守卫（现状 0 行撞名，删掉不会变红），复跑 `test_translations`。若要保留，就在开发守则「译名自检时机」登记理由 | 新Session修 | 删掉还是追认登记 | 待裁决 |
| P7-05 | 低 | `patches/s6_rename_cash_flow_worksheet.py`、`translation_check.py`、`tests/test_translation_check.py`、`tests/test_cash_flow_rename.py`、`tests/test_s6_closing_separator.py`（都在 `db9541a` 新建） | 这 5 个 S6 新文件整个用 4 空格缩进，而 `pyproject.toml` `[tool.ruff.format] indent-style = "tab"`，其余 S6 文件都用制表符。`scan_style.py` 扫全仓，4 空格文件只有这 5 个，加上 S5 的 `tests/raven_dataset.py`。ruff 没装，`ruff format --check` 未实跑，按配置推断会报。没有功能影响 | 项目格式约定（README「`ruff format --check frappe_china`」） | 并入 P1 登记册 `PH-P1019`（ruff 全量基线），清基线时一并改；或下次改这几个文件时顺手转成制表符 | 延迟或不修 | — | 待裁决 |
| P7-06 | 低 | 主仓库 `Spike/P1S6R9/ts036/bench-start-after.log`；`.gitignore` 不管 `*.log` | 这份日志在 `a32e852` 以 27 行提交，演示站的 `bench start` 一直往里写，现在 541 行（`git diff --stat` +514，最后一行是容器时间 11:21:49，即本机 19:21）。主仓库共有 68 个受管 `.log`（合计 4.8 MB），其中 11 个是 `serve`／`bench-start` 这类长跑进程的日志，别的现在不再增长。风险：`git status` 一直有 ` M`，「前后 `git status` 逐字相同」这类核对一直有噪声；有人 `commit -a` 时会把不断增长的日志带进去。grep 过没有口令或 sid | 版本卫生；R11 清单外第 1 条 | ① 演示站下次重启 `bench start` 时，日志改写到不受管的路径（如 `frappe-bench/logs/`）；② 之后把受管那份 `git restore` 回 `a32e852` 定格；③ 约定长跑进程的日志不写进受管的 `Spike/` 目录 | 新Session修 | 是否现在重启演示站 `bench start`（会碰演示站进程）；`git restore` 须许可 | 待裁决 |
| P7-07 | 观察 | R4 六个提交与 R4 回执 Part1～4 | 提交卫生：① R4 四份回执都没写提交号（S6 文档里搜 `db9541a` 0 处，`52f8064`、`1779cf0` 只出现在 R12 Part1）；② `52f8064` 的提交信息「continue S6 business flow navigation」没提 TS-012 开账跳转，也没提科目表与两个 S5 文件；③ `1779cf0`、`52f8064`、`c2b0420`、`35b5b77` 的提交信息没带 Round／TS 编号；④ `c2b0420`（导航与开账）顺带清了 Part1 留下的 BOM。R7 起都写了提交号与 Round，改善明显 | 可追溯性 | 以后回执写提交号；不同 Part 的残留清理单独提交 | 延迟或不修 | — | 待裁决 |
| P7-08 | 观察 | `frappe_china/public/js/desk_patches.js:140`（注释）、`README.md:66` | app 代码与 README 写着「上游报告草稿 `Spike/P1S6R9/upstream-it035.md`」，这是主仓库的路径。`frappe_china` 是单独推送的 fork，从 app 仓库看是一条死引用 | 可追溯性 | 改写为「见 ERX-001 主仓库 `Spike/P1S6R9/upstream-it035.md`」，或在草稿外发后换成 issue 链接 | 延迟或不修 | — | 待裁决 |
| P7-09 | 观察 | `frappe_china/tests/test_s6_closing_separator.py`；R3 Part1 TS-005 第 6 步 | 方案写「`test_closing` 加 zh／en 两种语言下的分隔符两例」，D 另建了文件。R4 Part1 回执第 24 行列了这个文件名，但没写成偏离。用例内容与方案等价 | 方案文件清单 | 接受；以后偏离文件清单的要写进「偏离」节 | 延迟或不修 | — | 待裁决 |
| P7-10 | 观察 | `frappe_china/tests/translation_overrides.py` `Get Items for Purchase Only`（`3f9511a`）；R8 IT-046 | R8 IT-046 现象栏点名 3 条依据应改 DEC-027，当场修改了 4 条，多出同族按钮 `Get Items for Purchase Only`。DEC-027 补充方案原文只写了「获取半成品、获取采购/调拨物料、更新单价与可用量」。修法合理，当场修清单如实写了 4 条，只是现象与修法不一致 | 当场修只修裁决项 | 接受；R8 报告现象栏不改 | 延迟或不修 | — | 待裁决 |

## 本片盲区自述

- **没往这些方向找**：主仓库 `docs/` 在 S6 的改动（常驻文件、概况）不在本片；主仓库 `Spike/` 受管脚本只查了互相依赖与日志，没逐个读有没有写死的路径或口令（`cdp.cjs` 只查了它自己）；`zh.csv` 只看了 hunk 归属，没看内容（片 5）；六个上游 app 的工作树与 HEAD 没有重核（R11 已核，本片只取锁值）；`frappe_china` 远端 `origin/main` 是否等于 `d441e9f` 没查；`35b5b77`、`06cbf4f` 的 Node 用例文件与 `test_crm_sidepanel.py` 只看 stat，测试本身有没有夹带没逐行看。
- **把握最低的一处**：P7-01 定「中」。功能零影响，但它悄悄撤销了 S4 一条已关闭、专门守过的裁决（IT-035），又没有任何一次 E 检出。如果用户认为「字节一致」只是 S4 入库时的一次性验收、不是长期约束，就可以降为「低」。
- **定级在边界上的**：P7-02（中／低）。产品代码不受影响，但它让 SB IT-018 与逐屏核工具在换机器后跑不起来，所以取「中」。P7-03、P7-04 都是现状零触发的潜在风险，取「低」。
- **拿不准处**：P7-04 的豁免算不算方案外夹带。从语义看，「Cash Flow」译成报表名「现金流量表」本就该与法定列头相同，豁免有道理；但方案与需求都没开这个口，也没有披露，所以按夹带记，处置留给用户。
- **跳过的验证**：没跑 ruff（环境没有），P7-05 是按配置推断；没跑 `bench run-tests`，P7-03、P7-04 的「删掉豁免不会变红」「恢复转义不影响现有键」靠宿主纯函数脚本推出，没在站点上实跑。
