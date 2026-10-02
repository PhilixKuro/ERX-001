# 审核报告·Part4（对象：frappe_china Part4 范围 / 审核标准：B 需求文档 + R7 开发方案 Part4）

**轮次**：P1-S4-R14｜**日期**：2026-10-02｜**步骤**：`plannedDev` F（play-audit，开放式查漏），第 4 片｜**执行者**：Claude（Opus 5.5），只读子 Agent
**被审代码**：`frappe-bench/apps/frappe_china/`（HEAD `40200dc`）、`docker/`（apps.json、setup.sh、up.sh、backup.sh、restore.sh、README.md）

## 覆盖自证（实际查了哪些、跳过哪些及原因；不写「全部覆盖」）

**读全的依据**：F Spec、`bricks/audit.md`、`bricks/sharding.md`；需求 §4.1／4.2／4.10～4.17、§八、§十；总纲全文；Part4 全文；`业务规则.md`；`开发守则.md`；R13 E 报告全文；R8 D 回执 Part4 全文（含 R11 更正段）；R9／R12 问题清单（IT-001～039，用于去重）。R9～R12 SB 回执只按关键词检索，未通读。

**实际查过的代码与环境**：
- 全文读：`cash_flow.py`、`cash_flow_statement.py`、`ledger.py`、`printing.py`、`bank_import.py`、`labels.py` 前 60 行、四个现金流 DocType JSON（逐字段）、两个银行 DocType 的 JSON／py／js、`templates/statements/cash_flow.html`、`小企业现金流量表.js`、`hooks.py`（接线部分）、app `README.md`、fixture `cash_flow_code.json`。
- zelin 原件对照：`cash_flow.py`、`cash_flow.js`、`cash_flow.json`、`cash_flow_code.js`、`test_cash_flow.py`。
- 上游读码：`frappe/public/js/frappe/form/controls/button.js`、`script_manager.js`、`handler.py:run_doc_method`、`model/naming.py:set_new_name／_set_amended_name`、`desk/query_report.py:get_report_doc`、`app.py`（异常时 rollback）、`utils/jinja.py`、`utils/xlsxutils.py`、erpnext `bank_statement_import.py`（start_import、update_mapping_db）、bench `app.py`／`utils/app.py`（get-app、get_app_name 改目录名）。
- 两站只读 SQL（q.sql～q4.sql）：Cash Flow 的 Button DocField、Client Script、Property Setter、Report 的 ref_doctype 与角色、Company／Bank／BSI／Cash Flow 的 DocPerm、Amend 命名设置、文件与银行残留、FY。
- `git ls-remote`：宿主机对三个 app 的远端核对；容器内无凭据对三个仓库核对。容器内做了一次 `os.rename` 到非空目录的行为实验（在 `tmp_r14_p4/` 内，已删）。

**跳过及原因**：
- 未跑任何测试（硬约束；全量回归 113/113 由主会话实跑）。
- 未在浏览器里实点（无浏览器自动化）。「取明细按钮无效」「Accounts User 打不开现金流量表」两条是**读码＋站点元数据**推出的，没有界面实测。
- 未跑 `up.sh`／`setup.sh`（硬约束）。P4-01 是读脚本与 bench 源码推出的，只在临时目录里实验了 rename 这一步。
- 未重做备份 `gzip -t`，未重核演示站业务单据条数（R13 已核，主会话本轮也已确认）。
- `test_bank_preprocess.py`、`test_bank_reconcile.py`、`test_cash_flow.py`、`test_statement_dataset.py` 只按关键词检索、读了片段，没有通读，也没有逐条核断言判别力（R12／R13 已做过变异）。
- PDF 模板只读了现金流量表那一份；资产负债表、利润表模板没读。

## 逐项落地核查

| 意图层依据 | 要求层要求（方案任务/验收条款逐条） | 定位（文件:行） | 落地 | 生效否 | 偏差说明 |
|---|---|---|---|---|---|
| §4.10.1 | TS-015 四个 DocType 并入，module `CN Tax` | `cn_tax/doctype/cash_flow*` | ✅ | ✅ | — |
| §4.10.1 | `month` 改 Int 1–12、`XJ-{abbr}-{yyyymm}` 控制器命名、保留 `amended_from` | `cash_flow.py:15-19`、`cash_flow.json` | ✅ | ⚠ | 命名本身正确。但取消后重做的路径不通，见 P4-03 |
| §4.10.1「按钮取现金流明细」 | 取明细入口（zelin 由 `cash_flow.js` 承载） | `cash_flow.json` Button `get_cash_flow_items`（`options` 为空，两站 DocField 同）；app 内无 `cash_flow.js` | ⚠ | ❌ | 按钮在界面上点了没有反应，见 **P4-02** |
| G1b | `evel`→`eval` 两处；`against` 改 Small Text；新增 `is_internal_transfer` | `cash_flow_item.json` | ✅ | ✅ | — |
| G1b | 小计金额字段改 Currency | `cash_flow_subtotal.json` | ✅ | ✅ | — |
| G1b | 过滤键改 `company`；取 Cash／Bank；排除 finance_book；标内部转账 | `cash_flow.py:141-158` | ✅ | ⚠ | 没有排除 `is_opening='Yes'` 的开账分录，见 **P4-04** |
| 验收 SL-007 ③ | 期初用 `gl_sums`；21 月额＝月初、年额＝年初；22 月额＝年额＝月末余额，**另断言** monthly == yearly == 月末余额 | `cash_flow.py:197-232` | ⚠ | ⚠ | 只断言了 monthly＝月末（`:230-232`），yearly 没断言，见 **P4-04** |
| §4.10.1 跨月依赖 | validate：同公司同月唯一；提交时 ① 缺代码列出行号 ② 有流水月份未提交 | `cash_flow.py:26-72、84-87` | ✅ | ✅ | ① 一次列出全部行号；② 与「按月顺序」两条报错可区分（R13 M4） |
| 同上 | `before_cancel`：更晚月份已有有效底稿时拒绝取消 | `cash_flow.py:132-135` | ✅ | ✅ | — |
| 方案 TS-015 | 内部转账：凭证全部分录都在现金类科目 ⇒ 标记、不要求代码；同凭证内部转账行借贷合计为 0 | `cash_flow.py:93-97、112-127` | ✅ | ✅ | 按凭证判，与方案相同。混合凭证（转账加手续费）不会被识别，规则见合规核表 |
| 验收 ⑤ ⑤ | 拆分行合计与原总账分录不符时报错 | `cash_flow.py:98-103` | ✅ | ✅ | — |
| 方案 TS-015 | 测试基类改 `FrappeChinaTestCase` | `tests/test_cash_flow.py` | ✅ | ✅ | zelin 的 `test_cash_flow.py` 并没有带进来，本 app 测试是另写的。README 第 106 行写成「基类改为」，与事实不完全相符（P4-12） |
| SL-007 ① | fixture 22 条；第 2、6、21 条改正 | `fixtures/cash_flow_code.json` | ✅ | ✅ | 22 条行名已对；R12／R13 已在两站核过 |
| LG-148 | 不带 `allow_all_party_type`；三个 `cash_flow_code` Custom Field 带入 | `hooks.py:204-221` | ✅ | ✅ | — |
| §4.10.2 | TS-016 `CF_LINES` 22 行＋3 个标题，`CF_CHECKS` 5 条 | `cash_flow_statement.py:15-43` | ✅ | ✅ | 流出项按正数存、勾稽式以减号计，口径一致 |
| §4.10.2 | 没有已提交底稿 → 报错；年报取 12 月、上年无数据要有说明；⑦ 底稿后又有流水；出表时对月末余额再核一次 | `cash_flow_statement.py:110-192` | ✅ | ⚠ | 出表时只核了「本月」那一列的 22，本年累计列的 22 没核（与 P4-04 同根） |
| §4.10.2 | Report 记录各字段「同 TS-013」（⇒ `ref_doctype = GL Entry`） | `小企业现金流量表.json` `ref_doctype: Company`（自 `ad4362b` 起） | ❌ | ❌ | 偏离方案，Accounts User 打不开这张表，见 **P4-05** |
| AC-004 ①② | TS-017 `printing.py`：STATEMENTS／EXECUTORS 同源、模板路径、方向、`has_permission("GL Entry")`、文件名 | `printing.py:16-99` | ✅ | ✅ | 年份取自 FY 名称前 4 位（`:60、64`），见 P4-11。`:70/72` 的 `_` 被遮蔽由主会话记 |
| AC-004 ① | 三张表 `.js` 加 `Print Statutory Format` 按钮 | `小企业现金流量表.js:3-7` | ✅ | ✅ | 前端只传写死的报表名 |
| LG-134 | 守卫 `_(x)==x`、判别力测试 | `labels.py:31-43` | ✅ | ⚠ | 读 fixture 名称时 `except Exception: pass`（`:42-43`），出错时静默缩小守卫范围；因 CF_LINES 已经收进集合，影响很小，只记观察（P4-13） |
| SL-008 ⑤ | 四个 Report `disable_prepared_report_automation=1`、`prepared_report=0` | 四个 Report json | ✅ | ✅ | — |
| §4.12 | TS-018 `Bank Statement Format`：字段、编码、二选一校验、不发 fixture | `bank_statement_format.*` | ✅ | ✅ | 两站 Format 都是 0 条，符合「不发 fixture」 |
| §4.12 | `Bank Statement Preprocess`：字段、只读状态、按钮 | `bank_statement_preprocess.*` | ✅ | ⚠ | 给会计两个角色建、写的权限，但按钮要 BSI create（只有 System Manager 有），见 P4-07 |
| §4.12 ①②⑤ | `_read` 三种格式两种编码、按原始字节读 | `bank_import.py:53-84、215-222` | ✅ | ✅ | 按原始字节从 `get_full_path()` 读，符合开发守则 |
| SL-009 ⑤ | 坏行报错：日期、金额、表头、重复流水号、存支都为 0 | `bank_import.py:125-212` | ✅ | ⚠ | 合计行判据会吞掉真实坏行；金额接受 `NaN`／`Infinity`／`1e5`，见 P4-08 |
| 方案 TS-018 | 出错：`status=Failed`、写 log、保存后抛错 | `bank_import.py:258-264、356-360` | ✅ | ❌ | 经 HTTP 调用时整个请求回滚，Failed 和 log 都不会落库，见 P4-09 |
| SL-009 ③ | 去重：同 bank_account、docstatus<2 的流水号；无流水号行告警 | `bank_import.py:266-279` | ✅ | ✅ | xlsx 里数字型流水号会变成 `…0.0`，见 P4-10 |
| V-22 ④ | 导入前后清空 Bank 映射 | `bank_import.py:325、347-350` | ✅ | ⚠ | 同步模式下成立；后台模式下 job 会在第二次清空之后重建映射。下次导入前会先清一次，故只记观察（P4-13） |
| AC-009 | TS-019 导入 → `auto_reconcile_vouchers` → 重复导入 → xlsx | `tests/test_bank_reconcile.py` | ✅ | ✅ | R11～R13 已核，本片没有重复 |
| AC-014 | TS-020 README 各节 | `README.md` | ⚠ | ⚠ | 已知限制缺 LG-152；安装节写的分支 `version-16` 在远端不存在（远端只有 `main`）；第 97 行「按钮由 `cash_flow.py` 承载」与事实不符，见 P4-12 |
| A9 | `zh.csv` 自有词条 | `translations/zh.csv` | ✅ | ✅ | R13 已全量比对，本片只抽查了 2 条按钮词 |
| §4.13 | TS-021 清站、建 HDTH、站点设置、`项目概况` 开发环境节 | 演示站；`docs/项目概况.md:60-77` | ✅ | ✅ | 主会话本轮确认：唯一公司 HDTH、266 科目、各类单据 0。项目概况其它节有过期描述，见 P4-14 |
| SL-010 ⑥ | TS-022 全量回归 | 主会话 113/113 | ✅ | ✅ | 本片没跑 |
| 开发守则「版本锁定」 | `apps.json` 三个 commit 与远端一致 | `docker/apps.json` | ✅ | ❌ | commit 与远端一致；但 `up.sh` 没法据它重建 frappe_china，见 **P4-01** |

## 业务规则合规核

| 规则条款 | 本片是否涉及 | 结论（合规/违规/草案·待专家确认） | 备注 |
|---|---|---|---|
| BR-001 小企业会计准则 | 涉及（README、现金流量表表号会小企 03 表） | 合规（未经专家确认） | README 第 70 行写明「(2024)」只是文件名 |
| BR-002 三表＋附注；月报、年报 | 涉及（现金流量表月报＋年报） | 合规（未经专家确认） | 附注不在本 Stage 交付范围（需求 §4.1） |
| BR-003／004／005／007 | 不涉及 | — | 本片不碰税率、结转、价税分离 |
| BR-006 资产负债表平衡 | 不涉及 | — | Part3 |
| 推断：现金只含 `1001＋1002＋1012`（Cash／Bank 类型） | 涉及 | **草案·待领域专家确认** | 需求与方案的口径；小企业准则「现金」是否含其他货币资金未经会计确认 |
| 推断：现金类科目之间的转移不是现金流量，按「凭证全部分录都在现金类科目」识别 | 涉及 | **草案·待领域专家确认** | 带手续费的混合凭证不会被识别，会把转账两腿当成流入、流出各计一次（总额虚增、净额不变） |
| 推断：开账分录（期初余额录入）不是现金流量 | 涉及（P4-04） | **草案·待领域专家确认**（本片推断，代码未体现） | 当前代码把它当作本月流水，要求编码 |
| 推断：借方现金行只能选流入项目，贷方只能选流出项目 | 涉及（P4-06） | **草案·待领域专家确认** | zelin `cash_flow.js` 的 `set_query` 按此过滤，本 app 未带入，也没有校验 |
| 推断：本年累计期末现金余额＝月末现金余额 | 涉及 | **草案·待领域专家确认**（方案已写成断言） | 代码只断言了本月列 |

本 Round 没有发现新增或改写的已生效规则；上表的「推断」行均由 AI 拟定，按触点 ③ 待送审。

## 集成点登记（交接摘要）

- **本片暴露给别片**：
  - `cash_flow_statement.execute` 与 `CF_LINES`，由 `printing.EXECUTORS` 与 `labels._CASH_FLOW_LABELS` 消费（同源，已核）。
  - Report `小企业现金流量表` 的 `ref_doctype = Company`。**`漏科目检查`（Part3）也是 `Company`**，同样会让 Accounts User 打不开（P4-05 的同类项，请 Part3／收口核）。
  - `bank_import.run_preprocess_and_import`（whitelisted），只有 System Manager 能成功调用。
- **本片依赖别片**：
  - Part3 `ledger.gl_sums`（`fy_opening_of`、`exclude_pl_closing`、空列表返回 `{}`）。签名与语义已核，调用方用法一致。`fy_opening_of` 会把本年 `is_opening='Yes'` 的分录算进年初，与 `get_cash_flow_items` 不排除开账分录合在一起，导致 P4-04，属于**跨片拼装问题**。
  - Part1 `docker/scripts/setup.sh` 第 3 段与 `apps.json` 的约定（P4-01）。
- **共享状态**：`tabCash Flow Code` fixture（两站 22 行一致）；`Bank.bank_transaction_mapping`（导入前后清空）；`zh.csv`（Part2／Part4 共用）；`docker/backups/` 与 `restore.sh` 取最新一套的规则。
- **事件**：本片没有发出或消费 SSE、realtime 事件。上游 BSI 的 `data_import_refresh` 本 app 不监听。
- **主会话 printing.py:72 的 `_` 遮蔽**：调用面我看过。三个报表的 `.js` 只传写死的合法报表名（`小企业现金流量表.js:5` 等），只有手工拼 URL 调 `download_statement_pdf`／`render_statement_html` 传非法名时才会触发；`download_statement_pdf` 第 95 行另有一处 `legal_title, _, _, orientation = …` 同样遮蔽 `_`，但该函数后面没有再用 `_()`。

## 自证复核

| 被审产物声称 | 实际复核结果 | 一致否 |
|---|---|---|
| README:97「按钮由 `cash_flow.py` 的 `get_cash_flow_items` 承载」 | Button 字段 `options` 为空，app 内也没有 JS 处理器。`button.js:39-50` 在两者都没有时什么也不做 | 否（P4-02） |
| R13 IT-038「① 恢复两处 `depends_on`」 | 已恢复，两站 DocField 一致；但按钮本身点了无效，`depends_on` 只是让一个无效的按钮按条件显示 | 部分 |
| `docker/README.md:9、64`、`up.sh:4-5`「新电脑上跑这一条就得到可用环境；重跑安全（幂等）」 | frappe_china 条目会因目录名与仓库名不一致、仓库需凭据而失败或锁版本失效（读码推断） | 否（P4-01） |
| R13「`apps.json` 已在远端」 | 宿主机 `ls-remote`：FrappeChina `main`＝`40200dc`，frappe／erpnext `version-16` 与锁定值相同 | 一致 |
| 方案 TS-015「另断言 monthly == yearly == 月末现金余额」与 D 回执「已完成」 | 代码只断言了 monthly（`cash_flow.py:230-232`） | 否（P4-04） |
| 方案 SL-007 ⑦ 说明行「请取消后重取明细」 | 取消后，会计两个角色没有 amend 权限；新建同月底稿又会与已取消单撞名（读码推断） | 否（P4-03） |
| README:25 安装命令 `--branch version-16` | 远端 FrappeChina 只有 `main` | 否（P4-12） |
| 方案 TS-018「Failed 时写 log」 | 经 HTTP 时回滚，不落库 | 否（P4-09） |
| 主会话：演示站唯一 HDTH、GL／Cash Flow／BT 为 0 | 本片只读 SQL：Company 1（HDTH、CNY、China）、GL 0、Cash Flow 0、File 0、Bank 0、Bank Statement Format 0 | 一致 |

## 问题清单

| # | 严重程度 | 定位 | 问题描述 | 违背的标准/意图 | 建议 | 建议档位 | 待裁决点 | 状态 |
|---|---|---|---|---|---|---|---|---|
| P4-01 | 中 | `docker/scripts/setup.sh:117-121、133`；`docker/apps.json` 第 3 条；bench `utils/app.py:281`（`get_app_name` 改目录名） | **`up.sh` 已无法据 `apps.json` 重建或重跑 frappe_china**（读码推断，未执行）。① setup.sh 用 `basename url .git` 得到 `FrappeChina` 来判断 `apps/FrappeChina` 是否存在，而 bench 克隆后会按 pyproject 把目录改名为 `frappe_china`，所以判断永远为假。② 在本机重跑：会再次 `get-app` 并克隆到 `apps/FrappeChina`，再改名到已存在的非空 `apps/frappe_china`，必然失败（容器内实验：`os.rename` 到非空目录报 `OSError [Errno 39]`）。`set -e` 下 setup.sh 中止，后面的建站、字体、开发模式、default_site 都不会执行。③ 在新机器上：改名能成功，但第 133 行用 `apps/FrappeChina/.git` 判断，锁定的 commit 被**静默跳过**，拿到的是 `main` 最新。④ 容器内无凭据时，`ls-remote PhilixKuro/FrappeChina` 报 `could not read Username`，同一命令下 frappe、erpnext 正常。仓库需要认证，而 `exec -T` 没有 TTY 输入用户名，克隆会直接失败 | 开发守则「版本锁定」（换机器按 apps.json 重建）；`docker/README.md:9、64`；`up.sh:4-5`「重跑安全」 | setup.sh 改为按「克隆后的实际目录名」取 app 名（如读 pyproject，或在 apps.json 加 `app_name` 字段）；锁定判断用实际目录；README 写明私有仓库在容器内的凭据办法（或把仓库设为公开） | 新Session修 | 仓库是否本就打算私有（决定是写凭据说明还是改公开）；修前能否实跑一次 `up.sh` 验证（会碰演示站） | 待裁决 |
| P4-02 | 高 | `cn_tax/doctype/cash_flow/cash_flow.json` Button `get_cash_flow_items`（两站 `tabDocField.options` 为 NULL）；app 内没有 `cash_flow.js`；`frappe/public/js/frappe/form/controls/button.js:39-50` | **界面上的「取现金流明细」按钮点了没有任何反应**（读码＋站点元数据，未在浏览器实点）。Button 控件被点击时：先找 JS 处理器（无），再看 `df.options` 有没有方法名（为空），两者都没有就什么也不做。zelin 是靠 `cash_flow.js` 的 `get_cash_flow_items(frm)` 调后端的；本 app 没带这个 js，也没有给字段填 `options`。后果是用户在界面上建不出底稿明细，只有测试与脚本里直接调 Python 方法才能取数。现有测试都直接调 `doc.get_cash_flow_items()`，测不到这一层；TS-019 截图只覆盖银行，现金流从来没在界面上走过 | 需求 §4.10.1「按钮『取现金流明细』从 GL Entry 拉……」；S7 演示依赖 | 最小改法：给该 Button 字段设 `options: "get_cash_flow_items"`（框架会经 `run_doc_method` 调用已 whitelisted 的方法并刷新字段）；或补一个只含该处理器的 `cash_flow.js`。补一条元数据测试，并在测试站界面实点取证。改 DocType 须两站 migrate | 本Session修 | 用 `options` 还是补 js；演示站 migrate 须当场许可 | 待裁决 |
| P4-03 | 中 | `cash_flow.json` permissions（两站 DocPerm `amend=0`、`delete=0`）；`cash_flow.py:15-19`；`frappe/model/naming.py:177-189`；`cash_flow_statement.py:143` | **底稿一旦取消，会计两个角色就没法重做这个月**（读码推断）。说明行⑦叫用户「取消后重取明细」。但：① 修订（Amend）要 amend 权限，两个角色都没有；② 新建同月底稿时，唯一性检查虽然排除了已取消单，`autoname` 却仍生成 `XJ-{abbr}-{yyyymm}`，与已取消的那张同名，插入时报 `DuplicateEntryError`；③ 删除权限也没有。测试只测到取消为止（`test_cash_flow.py:176-179`），没测重做。R13 已登记「7 项权限 D 步少带、是否补回另定」，但**没有分析它让 ⑦ 的补救路径走不通**，所以这里另报 | SL-007 ⑦ 的补救动作；§4.10.1「须每月按序提交」（取消后必须能重做） | 至少补回 `amend`（命名走框架的 `-1` 后缀）；或在 `autoname` 里对已取消的同名单加后缀。补一条「取消→重做→提交」的测试 | 本Session修 | 补 amend 还是改 autoname；是否顺带补回其余 6 项权限（R13 遗留） | 待裁决 |
| P4-04 | 高 | `cash_flow.py:141-148`（取数没过滤 `is_opening`）、`:199`（月初用 `to_date`）与 `:201`（年初用 `fy_opening_of`）口径不同、`:226`、`:230-232`（只断言 monthly）；`cash_flow_statement.py:175、144-149`（出表只核 monthly 列） | **期初余额以开账分录录入的公司，本年累计「期末现金余额」会被重复计算，且没有任何校验报出来**。推演：2026-01-01 一张 `is_opening='Yes'` 的 JE，借 1002 10000、贷 3001 10000。1 月取明细会把这一行当作流水，要求编码（比如编 15）→ 月额 20＝10000，月初＝0，月额 22＝10000＝月末余额，校验通过；年初余额走 `fy_opening_of`，把本年开账分录算进去＝10000 → 年额 21＝10000，年额 22＝0＋10000＋10000＝**20000**，实际只有 10000。勾稽式 22＝20＋21 仍成立；提交时只比 monthly，出表时也只比本月列，所以**静默出错**。根因是两个口径不一致：明细把开账分录当流水，年初又把它当期初；加上方案要求的「yearly＝月末余额」断言没写。HDTH 将来在 S7 录期初余额时就会命中。测试与数据集里没有任何 `is_opening` 数据 | AC-004 ⑤；SL-007 ③「本月金额与本年累计金额**都**等于月末余额」；TS-015「另断言 monthly == yearly == 月末现金余额」；总纲 §十第 7 条「不静默」 | ① 补上 yearly 22 的断言（提交时）和出表时本年累计列的核对；② 取明细排除 `is_opening='Yes'`（会计口径草案：开账分录不是现金流量），月初余额与年初余额用同一口径；③ 数据集加一张开账 JE | 本Session修 | 开账分录不计现金流量的规则须会计确认（草案）；① 能否先修、② 等会计确认 | 待裁决 |
| P4-05 | 中 | `cn_tax/report/小企业现金流量表/小企业现金流量表.json` `ref_doctype: "Company"`（自 `ad4362b` 起，两站同）；`frappe/desk/query_report.py:49-53`；两站 `tabDocPerm` Company / Accounts User `report=0` | **Accounts User 打不开现金流量表**（读码＋站点权限，未用该角色实登）。`get_report_doc` 要求对 `ref_doctype` 有 report 权限；Company 只给 Accounts User `read`、不给 `report`。资产负债表、利润表是 `GL Entry`（Accounts User 有 report），所以只有现金流量表被挡。同一用户却能经 `download_statement_pdf`（只查 GL Entry read）下载 PDF，屏幕与 PDF 的权限不一致。测试都以 Administrator 跑，测不到。`漏科目检查`（Part3）同样是 Company | Part4 TS-016「Report 记录的字段……同 TS-013」⇒ Part3 TS-012 表 `ref_doctype = GL Entry`；Report 角色列出了 Accounts User | 改为 `GL Entry`（四张表一致），两站 migrate；补一条以 Accounts User 身份 `query_report.run` 的测试 | 本Session修 | 是否连同 `漏科目检查` 一起改（属 Part3）；演示站 migrate 须许可 | 待裁决 |
| P4-06 | 低 | `cash_flow.py:88-92`（只校验代码存在）；zelin `cash_flow.js:5-15`（`set_query` 按借贷过滤 `is_outflow`、排除公式行） | **明细行可以选错方向的项目，不报错**。贷方（流出）行选了流入代码 1 → 第 1 行出负数，勾稽仍成立，静默。选到 7、13、19～22 这些公式行时，会在期末校验那里报「ending balance does not match」，报错文字与原因对不上。zelin 用 `set_query` 在界面挡住，README:97 把它归为「界面便利」不带入，实际上它承担了方向约束 | 需求 §4.10.1「预填后人工可改」须改得对；总纲 §十第 7 条 | validate 里加两条：明细行不得用 `formula` 行；借方行只能用流入项目、贷方行只能用流出项目（规则草案）。或补回 `set_query` | 新Session修 | 方向约束是否成立（草案·待会计确认）；校验放后端还是只放界面 | 待裁决 |
| P4-07 | 低 | `bank_statement_preprocess.json` permissions（Accounts User／Manager 可建、可写）；`bank_import.py:314`（要求 BSI create）；erpnext BSI／Bank DocPerm 只有 System Manager | **会计两个角色能建预处理单、看得到按钮，点了就是权限错误**。真正能跑通的只有 System Manager（还要写 Bank 清映射）。方案伪码就是这样写的，代码照写；问题在于 DocType 权限与入口权限不一致 | §4.12 用原生工具对账（会计操作）；可用性 | 二选一：预处理单只给 System Manager；或经 Custom DocPerm 给会计角色 BSI create、Bank write，并写进 README | 延迟或不修 | 由谁来做银行导入（S7 演示角色） | 待裁决 |
| P4-08 | 低 | `bank_import.py:160-162`（合计行判据）、`DEFAULT_SUMMARY_KEYWORDS` 含单字「共」；`:101-110` | **坏行有两种情况不会响亮失败**。① 日期解析失败的行，只要整行任一格含「共」「合计」等字就当合计行跳过；一条日期写错、摘要是「公共水电费」「共享服务费」的真实明细会被静默丢掉，条数校验也发现不了（被跳过的行不计入）。② 金额：`NaN` 会让后面的 `deposit < 0` 抛 `InvalidOperation`，不是 ValidationError，状态不会标 Failed，前端看到的是 500；`Infinity`、`1e5` 会被接受并写进 csv。方案伪码规定了按关键字判合计行，属方案设计的缺口 | SL-009「坏行响亮失败」；开发守则「静默失败」 | 合计行判据收紧：只看日期列或首列，或要求该行没有流水号；关键字去掉单字「共」。金额只接受有限的十进制数（`d.is_finite()`），拒绝科学计数法 | 出方案修 | 合计行识别规则；是否保留「共」 | 待裁决 |
| P4-09 | 低 | `bank_import.py:258-264`、`:356-360`；`frappe/app.py:181-184`（异常时 `db.rollback`） | **`status=Failed` 与 `log` 经界面调用时永远不落库**。代码先 `doc.save()` 再抛错，但 HTTP 请求一抛异常就整体回滚，保存也被撤销。用户只在弹窗里看到报错，单据仍是 Draft、log 为空。测试在同一事务里断言，看不出这一点（测试里也没有断言 Failed） | 方案 TS-018 伪码「status=Failed；log；save；throw」的意图（留痕）；开发守则「没报错≠成功」的反面——写了没落库 | 失败分支改用 `frappe.db.set_value(...)` 后 `frappe.db.commit()`，或用 `frappe.enqueue` 之外的独立连接记录；或者删掉这个 Failed 分支，明确「失败只看弹窗」 | 新Session修 | 要不要在单据上留失败痕迹 | 待裁决 |
| P4-10 | 低 | `bank_import.py:45-50、188`（xlsx 单元格原值 `str()`） | **xlsx 里数字型的流水号会变成 `2026010500001.0`**，与收付款 `reference_no` 对不上：去重失效，自动核销也不命中，而且都不报错。测试样本用的是字母开头的字符串流水号，测不到。真实网银 xlsx 的流水号是否存成数字未知（LG-147） | AC-009；LG-129（流水号须完全一致） | 流水号列遇到 int／整数值 float 时转成不带小数的整数字符串；遇到科学计数法报错 | 延迟或不修 | 等 LG-147 拿到真实样本再定 | 待裁决 |
| P4-11 | 观察 | `printing.py:60、64` | 年份取 `fiscal_year[:4]`（FY 名称），现金流量表与利润表的 execute 用的是 `year_start_date`。FY 名称不以 4 位年份开头时 PDF 表头的年份会出错或报错。两站 FY 名称都是 `2025`～`2027`，当前不触发 | 同源（A7） | 改用 `year_start_date.year` | 延迟或不修 | — | 待裁决 |
| P4-12 | 低 | app `README.md:25、97、106、125-131` | **README 与事实有四处不符**（AC-014）。① 安装命令写 `--branch version-16`，远端只有 `main`；② 第 97 行「按钮由 `cash_flow.py` 承载」不成立（P4-02）；③ 第 106 行「zelin 测试：测试基类改为 FrappeChinaTestCase」，实际 zelin 测试没有带入、是另写的；④「已知限制」缺方案点名的 LG-152（各类单据各自编号）——第 131 行写的是结转凭证分四张，不是同一件事。另：`license.txt` 仍是模板占位 `[year] [fullname]` | Part4 TS-020 README 各节；AC-014 | 逐条改正；`license.txt` 填实 | 本Session修 | — | 待裁决 |
| P4-13 | 观察 | `labels.py:42-43`；`bank_import.py:347-350` 与 erpnext `bank_statement_import.py:286` | ① 守卫读 fixture 时 `except Exception: pass`，查询失败会静默缩小守卫范围（CF_LINES 已覆盖同一批行名，实际影响很小）。② 非 developer_mode 下，`finally` 里的第二次清空发生在后台 job 重建映射**之前**，导入后 Bank 映射不为空；下次导入前会先清一次，所以 V-22 ④ 不会复发，但 SL-009 ⑥「导入后为空」只在同步模式下成立 | 开发守则「静默失败」；SL-009 ⑥ | ① 改为让异常抛出或记录；② README「银行对账」节补一句 | 延迟或不修 | — | 待裁决 |
| P4-14 | 低 | `docs/项目概况.md:51、67、79-85`；`docker/restore.sh:16`（不接受参数） | 常驻文件有过期描述：第 51 行 frappe_china「待创建（S4 建）」；「能力」「数据模型」两节仍写「待确立、尚未开始功能开发」「自有 DocType 待确立」。第 67 行「要恢复下列某一个须显式指定」，但 `restore.sh` 不接受参数，只取 `backups/` 根目录最新的一套；`20261001_110222` 只在子目录里，用这个脚本恢复不到 | 需求 §5.2（项目概况同步）；常驻文件准确性 | 按常驻文件契约改这三节；restore.sh 加「可选指定时间戳」参数，或在文档里写出手工 `bench restore` 命令 | 新Session修 | 是否在 S4 收口时一并改 | 待裁决 |

**定级说明（供改判）**：
- P4-02 定「高」：需求点名的唯一界面取数入口失效，S7 造演示数据会直接撞上。若认为 S4 只要求「能经 URL 打开」、界面操作留给 S6／S7，可降为「中」。
- P4-04 定「高」：法定报表的本年累计期末现金余额会静默出错。触发条件是「本年有开账分录」；若裁定期初余额一律用上年末日期录入（不用 `is_opening`），可降为「中」，但方案要求的 yearly 断言缺失仍应修。
- P4-01 定「中」：不影响产品代码，但环境重建与 `up.sh` 重跑都会失败，且锁版本静默失效；若近期不换机器、不重跑 `up.sh`，可降为「低」。
- P4-03、P4-05 在「中／低」之间：两条都是权限面问题，Administrator 下都不出现，演示若一律用 Administrator 登录则影响较小。

## 本片盲区自述

- **没往这些方向找**：
  - 浏览器层：两条最重要的界面结论（P4-02 按钮无效、P4-05 Accounts User 被挡）都是读码推出，没实点、没用非管理员账号实登。
  - 资产负债表、利润表的 PDF 模板没读（Part3 的表在 Part4 的 TS-017 里出 PDF）。
  - `test_bank_*`、`test_cash_flow.py` 的断言判别力没逐条核，依赖 R12／R13 的变异结论。
  - 多币种、finance book 非空、跨会计年度（非自然年 FY）的现金流取数没推演。
  - `Bank Transaction Rule`、两张原生对账报表、`Bank Reconciliation Tool` 的界面流程没核。
- **把握最低处**：P4-01 第 ②③ 步的 bench 行为（`--resolve-deps` 路径下 `check_existing_dir` 用的是仓库名还是 app 名）是读 bench 源码推出，只实验了 rename 那一步；私有仓库这一点，只从「容器内无凭据时 ls-remote 被要求用户名」推断，没有核 GitHub 仓库的可见性设置。另有一处没核实：若仓库是公开的，`--resolve-deps` 会解析出 `erpnext` 依赖，而 `apps/erpnext` 已存在，于是走到 bench `app.py:852` 的 `click.confirm`；在 `exec -T` 无输入的情况下，它大概会以 Abort 失败。这是第三条可能的失败路径，未验证。
- **拿不准处**：
  - P4-08 ① 按关键字判合计行是方案伪码原样规定的，算「方案缺口」还是「代码问题」——这里按方案缺口给了「出方案修」。
  - P4-06 的方向约束是会计规则推断（草案），也可能有合法的反向情形（如退款冲减流入），因此只定「低」。
  - P4-03 与 R13 遗留的「7 项权限是否补回」部分重叠，我认为后果分析是新的；若收口判为重报，可并入 R13 遗留项。
