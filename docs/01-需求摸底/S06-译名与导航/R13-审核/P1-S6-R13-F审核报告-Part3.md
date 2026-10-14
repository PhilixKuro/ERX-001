# 审核报告 Part3（片 3：自检、科目表、版本环境、常驻文件与提交卫生）

**轮次**：P1-S6-R13（F 复核）｜**日期**：2026-10-14｜**执行者**：Claude（Opus 5.5），只读子 Agent
**依据**：[R12 F 审核报告](../R12-审核/P1-S6-R12-F审核报告.md)「问题清单」「用户裁决」「当场修清单」；[SB 修复回执](../R12-审核/P1-S6-R12-SB修复回执.md)；`docs/流程体系/常驻文件契约.md`；`bricks/audit.md`、`F-codeAudit-plannedDev-audit.md`
**被审对象**：`frappe_china` `68476a3`、`1d0697e`（HEAD）；主仓库 `9657ca8`、`5775760`（HEAD）；演示站 `erx.localhost`（只读）
**片内编号**：`P3-xx` 只在本片有效，跨文件引用以收口报告的 `FD-` 号为准。

## 覆盖自证

实际查了：

- R12 当场修 FD-003、006、007、025、026、027、028 与延迟登记（`SH-P1S6002` 补、`SH-P1S6004`～`007`、`PH-P1019`）；SB 的 FD-024。
- 两个 app 提交 `68476a3`（11 文件、23 hunk）与 `1d0697e`（16 文件、37 hunk）逐 hunk 归属；主仓库 `9657ca8`（117 文件）与 `5775760`（90 文件）按文件归属，其中常驻文件、`apps.json`、`Spike/` 受管脚本逐 hunk 读。
- 版本：`docker/apps.json` 锁、`frappe_china` HEAD、`git ls-remote origin main` 三者比对；两仓库 `git status`。
- 自己复算：科目表 sha256（工作区、HEAD blob、`474cd1c` blob 三份）；FD-007 清单 47 个文件逐个 `git ls-files`；26 份「仅本机」逐个查在不在、受不受管；被受管文件引用、却既不受管也不在两份清单里的 `P1S6R4-*` 文件（全量扫描 813 个被排除文件）。
- 演示站：`ps` 与 `/proc/<pid>/fd` 查 `bench start` 输出去向，扫全部进程有无打开 `/workspace/Spike` 下的文件；只读跑 `translation_check.run`、`validate_legal_labels`、取 `frappe.local.lang`。
- 可重生成产物：逐个确认已删、未受管；实跑 `Spike/P1S6R4-baseline.py` 一次，核 SB 回执给的重生成方法（输出已删）。
- 常驻文件：`docs/项目概况.md`、`docs/开发守则.md` 改动段逐句对照代码与现状；`docs/README.md`、`CLAUDE.md`、`AGENTS.md` 只扫了失效指向；`docs/业务规则.md` 只确认 S6 未改。

跳过及原因：

- `bench run-tests` 没跑，主会话在跑全量（`Spike/P1S6R13-F/full-regression.log`）。新增用例是否通过，只看了 SB 全量日志 `Spike/P1S6R12-SB/full-regression.log:245,330`。
- 主仓库 `Spike/P1S6R12-F/`、`Spike/P1S6R12-SB/` 下的证据文件只核了归属与存在，内容不复核（归各片）。
- `zh.csv` 只看 hunk 归属，不逐行（归片 5 口径）。

探针与中间产物在 `Spike/P1S6R13-F/p3/`：`68476a3.diff`、`1d0697e.diff`（提交前已删，`git -C frappe-bench/apps/frappe_china show <提交号>` 可再生）、`untracked-referenced.txt`、`baseline-regen.log`。

## 逐项复核

| FD 号 | R12 要求与裁决 | 落地位置 | 三层 | 复算 | 结论 |
|---|---|---|---|---|---|
| FD-003 | 第 4 项固定按 zh 判，补「会话 en 时注入 zh 译名仍能报出」用例；裁决按建议 | `accounting/statements/labels.py:40` `_(label, lang="zh")`；`translation_check.py:40` 输出取 zh；`tests/test_translation_check.py:94-111` | 在 ✅；生效 ✅：上游 `frappe/utils/translations.py:4,15-25` 传了 `lang` 就不读 `frappe.local.lang`；原问题消失 ✅ | 演示站 `bench execute` 下 `frappe.local.lang` 实测 `en`，两站 `site_config` 都没有 `lang`；`translation_check.run` 输出「译名自检通过」，`validate_legal_labels()` 返回空（`bench execute` 不打印空返回值）。用例在 SB 全量里绿（`:330`） | ✅ |
| FD-006 | 用 `474cd1c` 的字节还原科目表，加 sha256 断言，推进锁；裁决同意 | `cn_tax/chart_of_accounts/cn_smes_chart_of_accounts2024.json`；`tests/test_scaffold.py:19-27` | 在 ✅；生效 ✅：`.gitattributes:2` `-text`，`git check-attr` 显示 `text: unset`；原问题消失 ✅ | 工作区、HEAD blob、`474cd1c` blob 三份 sha256 都是 `539d12f5d4099116ea3f8b86c78f1c4000e9d3c0b4367083f26d1c3a5c867972`，与 `CHART_SHA256` 一致；用例在 SB 全量里绿（`:245`） | ✅ |
| FD-007 | cdp.cjs 纳入版本（exclude 加例外）；被引证据逐份定纳入与否，不纳入的注明仅本机；裁决同意 | `git add -f` 47 个文件（`Spike/P1S6R12-F/fix/fd007-add.txt`）；`.git/info/exclude` 末尾三行注释；仅本机 26 份见 `fd007-local-only.txt` | 在 ✅；生效 ⚠；原问题部分消失 | 47/47 受管，与 `9657ca8` 新增的 `Spike/P1S6R4-*` 逐个相同；`Spike/P1S6R4-cdp.cjs` 受管。26 份「仅本机」都在本机、都不受管。**但**：exclude 没加 `!` 例外行，只加了注释（已受管的文件不受 exclude 影响，效果等同，属措辞偏差）；另有 5 份被受管文件引用的 `P1S6R4-*` 文件既没纳入、也不在仅本机清单里，其中 `P1S6R4-screens.json` 是受管脚本的输入，见 P3-01；26 份的引用文档本身没有注明「仅本机」，只靠清单文件，见 P3-01 | ⚠ |
| FD-025 | 改 README `:3`、`:19`；补 commit 与行号；守则 `:121` 改「文件＋函数名或文件:行」；`:66` 注明主仓库；裁决按建议 | `frappe_china/README.md:3,19-20,62-67,90-92,109`；`docs/开发守则.md:121` | 在 ✅；生效 ✅；原问题消失 ✅ | 抽核上游行号：`button.js:78` 是 `set_label`，`desktop.html:13` 是搜索按钮，`crm/www/crm.html:2` 是 `lang="en"` 的 html 标签，`raven/www/raven.html:259` 注入 boot，`form.js:1542` 置空 `fa fa-` 分组，`meta.py:772-773` 逐个调看板钩子，`workstation_dashboard.py:8` 是 `_("Master")` 分组，全部对得上。README 里的导航 json 说法与实物一致：侧栏 7 个分节、51 个入口，图标 `label`＝侧栏 `title`＝`Business Flow`，`idx=-1` | ✅ |
| FD-026 | 项目概况多处改写；裁决本 Session 改、排在最后 | `docs/项目概况.md:53,89,188-194` | 在 ✅；生效 ✅；原问题消失 ✅（R12 当时） | R12 列的过期数字 747／143 组、apps.txt 说法、「保留 S3 中性词」都已删；`Unpaid`／`Paid` 的官方译文「未付」「已付款」与 `erpnext/locale/zh.po:59192,35518` 一致；备份 `20261010_174959`、`20261010_220310` 在 `docker/backups/` 根目录，`保留-S6收尾/` 有 `20261010_220310`，属实；「无 context 行波及他 app」一条只写约定、无过程句。**SB 之后又失准两处**（模块表漏 `dashboards.py`；`:194`「待补 context 行」已过时），见 P3-02 | ✅（R12 范围内）；SB 后失准记 P3-02 |
| FD-027 | 长效信息加 #3 HT-014，#1、#2 标已落地，HT-008 注明关闭；裁决按建议 | S6 概况「本 Stage 的长效信息」`:174-176`；收口清单 `:107` | 在 ✅；生效 ✅（`:87`、`:107` 两处收口清单都列了 HT-014）；原问题消失 ✅ | #1 落在开发守则「译名自检时机」`:99-105`，#2 的现状在项目概况，都属实 | ✅ |
| FD-028 | 例子只留 `translation_check.py`，注明 `realtime_check` 另一类；裁决按建议 | `docs/开发守则.md:109` | 在 ✅；生效 ✅；原问题消失 ✅ | `realtime_check.py:46` `def run(...) -> dict`，与守则说法一致；「`bench execute` 进程语言是 en」与演示站实测一致 | ✅ |
| 延迟登记 | FD-005 补进 `SH-P1S6002`；FD-011／022／023 登记；FD-029 并入 `PH-P1019`；SB 的 FD-009 登记 `SH-P1S6007` | S6 概况 `:185-190`；P1 概况 `PH-P1019` 行 | 在 ✅ | `SH-P1S6002` 引的 `crm/install.py:97-115` 里确有 `Demo/Making` 等 4 个阶段，`:45-70` 有 `Contacted`、`Nurture`、`Junk`；七列齐全，原始记录都定位到 FD 号与 Part 号 | ✅ |
| FD-024 | 下次重启 `bench start` 时日志改到不受管路径；`git restore` 受管那份；约定写进守则；裁决按建议，SB 时用户许可动进程 | 演示站 `bench start`；`Spike/P1S6R9/ts036/bench-start-after.log`；`docs/开发守则.md:156-158` | 在 ✅；生效 ✅；原问题消失 ✅ | 容器内 `bash -c nohup bench start > /workspace/frappe-bench/logs/bench-start.log`（pid 30903），honcho（30909）的 fd1 指向同一文件；扫全部进程 fd，没有打开 `/workspace/Spike` 下任何文件；`git status` 不显示 `bench-start-after.log`，它是 27 行；`frappe-bench/` 被 `.gitignore:12` 排除；重起前另存的 `bench-start-before-fd024.log` 有 668 行，与回执相符。守则新段与 SB 做法一致。**但**受管的可照做序列 `it018-run.sh`、`it013-run.sh` 仍把测试站 `serve` 的输出写进受管目录，与新约定冲突，见 P3-03 | ✅（演示站）；脚本残留记 P3-03 |

## 提交 hunk 归属表

| 提交 | 文件／hunk | 归属 | 方案外夹带 |
|---|---|---|---|
| `68476a3`（app，11 文件） | `labels.py`、`translation_check.py`、`test_translation_check.py` | FD-003 | 无 |
| 同上 | 科目表 json（8 行换行字节）、`test_scaffold.py` | FD-006 | 无 |
| 同上 | `test_translations.py`：删 `NAMED_TERMS` import 与豁免 | FD-014；`_duplicate_keys` 归一与新用例归 FD-015 | 无 |
| 同上 | `desk_patches.js` `:110-111`、`:239-250`；`test_desk_patches.cjs` 三个 hunk | FD-018、FD-020 | 无 |
| 同上 | `zh.csv:4686`、`translation_overrides.py:105` | FD-021 | 无 |
| 同上 | `README.md` 4 个 hunk | FD-025；PE 行改「已知未生效」归 FD-001 的标注 | 无 |
| `1d0697e`（app，16 文件） | `opening_ledger.js`、`test_opening_ledger.cjs`、README PE 行 | FD-001 | 无 |
| 同上 | `dashboards.py`（新）、`hooks.py:256-258`（把模板里注释掉的示例换成真钩子）、`test_dashboards.py`（新）、README 看板节 | FD-002 | 无 |
| 同上 | `zh.csv` 删 `Expenses`、`translation_overrides.py` 删一条、`test_named_terms.py` `Expenses` 键 | FD-008 | 无 |
| 同上 | `zh.csv` `Ledger`／`Item Type` 两行 context、`NAMED_TERMS` 两键 | FD-009 | 无 |
| 同上 | `zh.csv` 3 行 `Sales Invoice` context、`NAMED_TERMS` 三键 | FD-010 | 无 |
| 同上 | `test_translations.py` 取法 3 个 hunk 与两条新用例 | FD-012、FD-013 | 无 |
| 同上 | `test_cash_flow_rename.py`、`test_named_terms.py` 防空转与路径、`test_invoice_status.cjs`（新）、`test_business_flow_navigation.py` | FD-016 | 无 |
| 同上 | `test_translation_quality.py` 全部 hunk；`test_translations.py:242` docstring | FD-017 | 无 |
| 同上 | `desk_patches.js:158-163`、`test_desk_patches.cjs` DOM 桩与用例、README 时间线行 | FD-019 | 无 |
| `9657ca8`（主仓库） | `Spike/P1S6R12-F/`（56 个） | R12 审核证据与 `fill_rulings.py` | 无 |
| 同上 | `Spike/P1S6R4-*`（47 个） | FD-007，与 `fd007-add.txt` 逐个相同 | 无 |
| 同上 | `docker/apps.json` 一行 | 锁 `68476a3` | 无 |
| 同上 | `docs/开发守则.md` 两个 hunk | FD-028（`:109`）、FD-025（`:121`） | 无 |
| 同上 | `docs/项目概况.md` 三个 hunk | FD-026 | 无 |
| 同上 | P1 概况两个 hunk | 级联指针；`PH-P1019` 补 FD-029 | 无 |
| 同上 | S6 概况 | Round 表 R12 行、SB 交接、FD-027、延迟登记 | 无 |
| `5775760`（主仓库） | `Spike/P1S6R12-SB/`（82 个） | SB 证据 | 无 |
| 同上 | `Spike/P1S6R4-baseline.py` | FD-009 | 无 |
| 同上 | `Spike/P1S6R6-screen-check.js`、`Spike/P1S6R9/screens-build.py`、`Spike/P1S6R9-screens.json` | FD-002（`forbid`／`require` 与新屏，回执偏离第 2 条已申报） | 无 |
| 同上 | `docker/apps.json` 一行 | 锁 `1d0697e` | 无 |
| 同上 | `docs/开发守则.md` 三个 hunk | FD-017（`:103`）、FD-012（`:105`）、FD-024（`:156-158`） | 无 |
| 同上 | `docs/项目概况.md` 三个 hunk | 演示站状态 `:68`（FD-002、FD-024）、备份 `20261014_162407`、`:190` 五道守卫（FD-017） | 无 |
| 同上 | P1 概况、S6 概况 | 级联指针；R13 交接；`SH-P1S6007` | 无 |

版本与环境：`docker/apps.json:45` 锁 `1d0697ec88ac868a2c41ddab3dd81a768babbef8`，等于 `frappe_china` HEAD，也等于 `git ls-remote origin main`。`frappe_china` 工作区干净，只有被忽略的 `__pycache__`、`.ruff_cache`。主仓库只有本轮新产物 `Spike/P1S6R13-F/`。

## 自证复核

| 被审产物声称 | 实际复核结果 | 一致否 |
|---|---|---|
| R12：科目表还原后 sha256 回到 `539d12f5…867972` | 三份字节都是这个值 | 一致 |
| R12：FD-007 纳入 47 个，含 cdp.cjs | 47/47 受管，与提交逐个相同 | 一致 |
| R12：exclude 加例外 | 只加了注释，没有 `!` 行；已受管文件不受影响，效果等同 | 措辞不一致，效果一致（并入 P3-01） |
| R12：「被 S6 文档引用的顶层文件」都已纳入，其余 26 份列为仅本机 | 另有 `P1S6R4-screens.json`（受管脚本的输入）、`refresh-{bom,job,tax}.json`、`form-residuals.json` 共 5 份被受管文件引用，两份清单都没有 | **不一致**（P3-01） |
| R12 FD-026：模块表补了 S6 新增模块 | R12 当时属实；SB 新增 `dashboards.py` 后没补 | SB 后失准（P3-02） |
| SB：演示站 `bench start` 日志在 `frappe-bench/logs/bench-start.log`，进程不再打开受管路径 | `/proc` 实查一致 | 一致 |
| SB：受管日志 `git restore` 回 27 行，`git status` 不再显示 | 一致 | 一致 |
| SB：演示站 `translation_check.run` 通过 | 本片复跑通过 | 一致 |
| SB：提交前删了 `fd009/baseline.json`，重跑 `python -I -X utf8 Spike/P1S6R4-baseline.py --out <路径>` 即得 | 文件已删、不受管；实跑约 5 秒，114 条官方覆盖，27 条有未记出处，与 `hidden.txt`、回执的数一致（输出已删） | 一致 |
| R12：可重生成产物删了，并给出重生成方法 | 9 份都已删、不受管。基线、脚本输出、diff 都有方法；**`p3/zh_merged.json` 只写了「合并字典快照」，没给方法**，仓库里也没有写这个文件的脚本 | 部分不一致（P3-05） |
| SB 回执的行号引用：`README.md:103`（FD-001）、`docs/项目概况.md:189`（五道守卫） | 现行是 `README.md:109`、`项目概况.md:190`，被同一次 SB 在前面插入的行推后了 | 不一致（P3-04，观察） |

## 新发现

| # | 严重程度 | 定位 | 问题 | 证据 | 建议 | 建议档位 | 待裁决点 |
|---|---|---|---|---|---|---|---|
| P3-01 | 低 | `Spike/P1S6R4-screens.json`（不受管）；受管的 `Spike/P1S6R6-screens-build.py:19`、`Spike/P1S6R4-screen-check.js:4`、`Spike/P1S6R4-capture-state.cjs:2`；`Spike/P1S6R12-F/fix/fd007-add.txt`、`fd007-local-only.txt` | FD-007 的分类没做全。`P1S6R4-screens.json` 是受管脚本 `P1S6R6-screens-build.py` 的输入，这个脚本生成 `P1S6R6-screens.json`，后者又是 `P1S6R9/screens-build.py` 的输入，即逐屏核屏单生成链的起点。它既没纳入，也不在仅本机清单里，换机器后屏单链从第一步就断。同类的还有被受管 `P1S6R4-ts013-report.md` 引用的 `refresh-{bom,job,tax}.json`（`bom`、`job` 在 `Spike/P1S6R5-SB/it018/` 有重做的受管副本，`tax` 没有），以及被 `P1S6R8-E/fix/origin.txt` 引用的 `form-residuals.json`。另外，26 份仅本机证据只在清单文件里注明，引用它们的 R4 Part4 回执、R5 E 报告里没有标 | `Spike/P1S6R13-F/p3/untracked-referenced.txt`（11 条，扣除清单里已有的 6 条后剩 5 条）；`git ls-files` 0 条 | `P1S6R4-screens.json` 用 `git add -f` 纳入（4.7 KB，不含口令），并补进 `fd007-add.txt`；其余 4 份补进 `fd007-local-only.txt`；引用文档是历史产物，不改，以清单文件为准 | `本Session修` | ① 纳入 `P1S6R4-screens.json` 要提交许可；② 仅本机只记在清单文件里、不改历史文档，是否接受 |
| P3-02 | 低 | `docs/项目概况.md:53`（模块表 `frappe_china` 行）；`docs/项目概况.md:194` 末句 | SB 之后项目概况又失准两处。① 模块表列了 S6 新建的模块，漏了 SB 新增的 `dashboards.py`（看板覆盖，`hooks.py` `override_doctype_dashboards`）；同文件 `:68` 已写「工位看板的服务端覆盖已上线」，模块表没跟上。② `:194` 仍写「销售发票其余三个状态（`Partly Paid` 等）仍是『付』的方向，待补 context 行」，而 SB FD-010 已补了这三行（`zh.csv:3444-3445,5242`）。SB 在同一提交里改过 `:190`，没按契约 §5.6「写入即查逐出」顺带查同节 | `git show 5775760 -- docs/项目概况.md` 只有 `:68`、备份、`:190` 三处；`zh.csv` 三行在 | ① 模块表补「工位看板分组标题覆盖（`dashboards.py`）（S6 建）」；② `:194` 末句改为现状：「销售发票的 `Partly Paid`、`Partly Paid and Discounted`、`Unpaid and Discounted` 也按收款方向取 context 行」。写前载入常驻文件契约 | `本Session修`（也可并入 Stage 收口的契约 §4 全量逐出） | 现在改，还是并入收口时改 |
| P3-03 | 低 | `Spike/P1S6R5-SB/it018-run.sh:21`（`OUT=Spike/P1S6R5-SB/it018`）；`Spike/P1S6R5-SB/it013-run.sh:12` | FD-024 新约定写明「测试站 `serve`」的输出写到 `frappe-bench/logs/`，但两条受管的可照做序列仍把 6787 `serve` 的输出重定向到受管目录。`it018-run.sh` 写的 `Spike/P1S6R5-SB/it018/serve-6787.log` 正是受管文件，`it013-run.sh` 写的 `serve-6787-{dev,restored,unhooked}.log` 也受管。照 R5 IT-018 的复现序列跑一次，主仓库就会出现 ` M`。这两个 serve 有 trap 停掉、不是常驻，影响比 FD-024 小 | `git ls-files` 四个 `serve-6787*.log` 都受管；`git grep` 只有这两处脚本 | 两个脚本把 serve 输出改到 `/workspace/frappe-bench/logs/serve-6787-<标签>.log`，需要留证据时在取证当时另存定长副本（与守则同口径）；或者守则把「测试站 `serve`」收窄为「常驻不停的」 | `新Session修`（或 `延迟或不修`） | 改脚本，还是收窄守则措辞 |
| P3-04 | 观察 | SB 回执 SB-1 行「`frappe_china/README.md:103`」；SB-9 行「`docs/项目概况.md:189`」 | 回执引用的行号被同一次 SB 在前面插入的行推后：README PE 行现为 `:109`（FD-002 在 `:97-102` 插了看板节），项目概况五道守卫现为 `:190`（`:89` 插了备份行）。指的是哪一处不难认，不影响复核 | 本片 `sed -n` 实读 | 以后回执的行号在全部改完后再取；本条不改历史回执 | `延迟或不修` | — |
| P3-05 | 观察 | R12 报告「提交前删掉的可重生成产物」第 2 条 `p3/zh_merged.json` | 其余几类都给了重生成方法，这一份只写了「合并字典快照」。仓库里没有任何脚本写这个文件（`Spike/P1S6R12-F/p2/merged.py` 只在内存里建合并字典），也没有文档引用它，所以删掉不影响任何结论，只是「可重生成」这个说法没有落到方法上 | `grep -rn zh_merged Spike docs` 只命中 R12 报告本身 | 不改；以后删产物时每份都写方法，写不出的就算不可重现证据，留着 | `延迟或不修` | — |

R12 已裁「不做／延迟」的项（FD-029、FD-038 等）这次修复没有改变，不重提。

## Stage 收口待办清单

S6 概况 `:107` 列的三件事，加按规范 §12.2 收口必做的两件。只评估现状、列改动，本片不动手。

**一、HT-014 移交路线文档 §四 S7**

- `docs/01-需求摸底/0-P1文档/路线文档.md` §四 S7「执行清单」末条 18 之后加第 19 条：侧栏 URL 项（`/crm/…`、`/raven`）对非 Administrator 是否可见没验证过（`desk_views.py` 对 URL 类型的判定没读完，S6 只用 Administrator 验过）；S7 若用非 Administrator 演示用户，须先实测这两个入口显不显示。来源注「v1.10，S6 长效信息 #3、R12 FD-027」。
- 同文件头部版本号 `v1.9` 改 `v1.10`，「版本变更记录」表加一行（「S6 收口：HT-014 进 S7 清单；按 RW-09 回写 S6 工作量；Stage 划分、次序、依赖未动」）。
- S6 概况长效信息 `:176` #3 的类别改为「已移交（路线文档 v1.10 §四 S7 第 19 条）」。

**二、按 RW-09 回写路线文档工作量**（口径按 R8 IT-049 的裁决在收口时定：日历日、Round 数、折算当量）

- 素材：R7 D 回执「工作量」节（`:74-76`，10-08～10-12 共 5 个日历日、7 个 Round、已超 11.25–18 上限，主因 DEC-038 整批重译）；收口时补到 R13 为止的日历日（10-08～10-14）与 Round 数（13 个，另有附属 SB 两次）。
- 要改的位置，同一个数字五处同步：§三 Stage 表 S6 行工作量列（`:67`）；§四 S6「工作量」行（`:186`）；ASCII 依赖图 S6 格（`:321`「11.25–18」）；「阶段 A 小计」（`:71`）；「P1 剩余总计」（`:73`）。
- RW-09 行（`:375`）本身不改，它是规则。

**三、常驻文件契约 §4 全量逐出**（五个常驻文件逐一过，本片已查到的触发点如下）

- `docs/项目概况.md`
  - `:53` 模块表补 `dashboards.py`（P3-02 ①，若本 Session 未修）。
  - `:194` 末句「待补 context 行」改现状（P3-02 ②，若本 Session 未修）。
  - `:190`「演示站逐屏核 143 屏全部通过（S6 R10）」：现行屏单是 144 屏（`Spike/P1S6R9-screens.json`），新屏 `05-workstation-connections` 只在测试站跑过。按 R13 是否跑演示站整轮逐屏核，改成「144 屏全部通过」或补一句「工位关联页签一屏只在测试站核过」。
  - `:68` 演示站状态的日期与限定语（「S6 R12 SB 后」）随收口时的实际状态改；`:89-90` 备份列表里 `20261014_162407` 的说明随收口时是否再出基准点改。
  - `:6`「其 74 条」与 `PH-P1001`～`PH-P1074` 的范围：S6 七条 `SH-P1S6001`～`007` 上交后要改（见下第四项）。
  - `:8` `PH-P1001`～`1003`「唤醒已触发」：`PH-P1001` 中文译名改造随 S6 收口是否算已实现、`PH-P1002` 不刷新六例（四例没复现、一例不是刷新问题、树形入口只修了自有侧栏）是否关闭，由用户定，再按定论改这一句，同时改 P1 概况登记册 `:133-134` 两行的状态。
- `docs/开发守则.md`：本片没查到失效条目。`:156-158` 长跑日志一节若 P3-03 选「收窄措辞」，在此改。
- `docs/README.md`、`CLAUDE.md`、`AGENTS.md`：本片只扫了失效指向，没有命中（README 唯一不在本地的链接是 SPS 的 GitHub 地址，属外链）。收口时仍须按契约逐条过一遍。
- `docs/业务规则.md`：S6 没有新增或改动不变量（R12 合规核），收口时只需确认不改。

**四、延迟需求逐级上交**（规范 §12.2 第 2、3 条，S6 收口必做）

- `SH-P1S6001`～`007` 七条现均为「未做／延期」，逐条判做没做；没做的推进 P1 概况登记册，换发 `PH-P1075`～`PH-P1081`，行内注明原号；S6 登记册各行状态改为「已上交 PH-P10xx」。
- 随之改项目概况 `:6` 的条数与号段。

**五、级联指针**

- P1 概况「当前 Stage」改为 S6 已收口（末轮 R13）＋下一步 S7；S6 概况顶部写「Stage 已收口」。

## 交接摘要

- **本片依赖**：主会话 R13 全量回归（`Spike/P1S6R13-F/full-regression.log`）的结果。本片对 FD-003、FD-006 用例「仍绿」的判断只采信了 SB 全量日志。
- **本片暴露**：
  - P3-01 牵涉片内其它管逐屏核的片：屏单生成链的起点文件不受管。
  - P3-02 与收口清单第三项重叠，裁决时二选一，别做两次。
  - 「演示站整轮逐屏核 144 屏没跑」由主会话定，它决定收口时 `:190` 怎么写。
- **演示站**：本片只读（`ps`、`/proc` 查询，`bench execute` 三次纯查询），没有 `clear-cache`、没有重启、没有写入。

## 盲区自述

- **没往哪找**：
  - 没核 `Spike/P1S6R12-F/`、`Spike/P1S6R12-SB/` 各证据文件的内容是否支撑结论，只核了归属与存在。
  - 没逐份打开 26 份仅本机证据看内容。
  - 主仓库两个提交里非常驻文件的 `docs/` 改动（S6 概况、P1 概况）只按 hunk 归属读，没逐句对照契约，它们不受常驻文件契约约束。
  - `CLAUDE.md`、`AGENTS.md`、`docs/README.md` 只做了失效指向扫描。
- **边界上的定级**：
  - P3-01 定低：屏单链断只在换机器时发生，本机全部可用；若用户把「换机器可复现」看得重，可升中。
  - P3-03 在低与观察之间：脚本只在复现 IT-018 时跑，且 trap 会停服务。
- **拿不准处**：FD-007 裁决原文是「exclude 加例外」，实际只加了注释。已受管的文件不受 exclude 影响，本片判为措辞偏差、不单列发现。若用户要求字面落实，可补一行 `!/Spike/P1S6R4-cdp.cjs`。
