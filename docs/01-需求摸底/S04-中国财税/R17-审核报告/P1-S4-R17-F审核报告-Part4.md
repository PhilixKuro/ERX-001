# 审核报告·Part4（对象：frappe_china Part4 范围＋`docker/` / 审核标准：B 需求文档 ＋ R7 开发方案 Part4 ＋ R14 F 报告各项判定标准）

**轮次**：P1-S4-R17｜**日期**：2026-10-03｜**步骤**：`plannedDev` F（audit，复核轮），第 4 片｜**执行者**：Claude 子 Agent（只读）
**依据**：[R7 Part4](../R07-开发方案/P1-S4-R7-C开发方案-Part4.md)、[总纲](../R07-开发方案/P1-S4-R7-C开发方案-总纲.md)（按需检索）、[B 需求](../R06-需求文档/P1-S4-R6-B需求文档.md) §4.10～§4.13、`docs/业务规则.md`、`docs/开发守则.md`（版本锁定节）、[R14 Part4](../R14-审核报告/P1-S4-R14-F审核报告-Part4.md)、[R14 收口](../R14-审核报告/P1-S4-R14-F审核报告.md)「当场修清单」、[R14 SB 回执](../R14-审核报告/P1-S4-R14-SB修复回执.md)
**被审范围**：`frappe-bench/apps/frappe_china/`（HEAD `21faeb9`，对照 R14 基线 `40200dc`，含 `e55806e`、`48e7933`、`21faeb9` 中与 Part4 相关的部分）；主仓库 `docker/`（`git diff 56f56b2 HEAD -- docker/`，即 `4974230`、`2345991`）

## 覆盖自证

**读全的**：
- 代码：`cn_tax/doctype/cash_flow/cash_flow.py`、`cash_flow.json` 的 diff、`accounting/statements/cash_flow_statement.py`、`printing.py`、`accounting/bank_import.py`、`accounting/ledger.py` 前 130 行、`bank_statement_preprocess.js/.py`、`bank_statement_format.json` 的 diff、`templates/statements/` 下**三份**模板（R14 只读过一份）、app `README.md` 与 `license.txt` 全文和 diff、`translations/zh.csv` 的 diff、`patches/fd004_default_accounts.py`。
- 测试：`test_cash_flow.py`（402 行）、`test_bank_preprocess.py`（168 行）、`test_bank_reconcile.py`（243 行）、`test_statement_output.py`（77 行）**通读**；`test_statement_export.py` 读了 PDF 那一项及常量。
- docker：`apps.json`、`lock-apps.sh`、`restore.sh` 全文；`scripts/setup.sh` 第 1、3、4、5、6 段；`docker/README.md` 的 diff；`compose.yaml` 的 volumes。
- 上游：`frappe/app.py:135-205、386-470`（请求异常路径）、`database/database.py:1170-1225`（commit／rollback 与回调）、`utils/__init__.py` `CallbackManager`、`handler.py`（`execute_cmd`、`run_doc_method`、`is_valid_http_method`）、`api/v1.py:handle_rpc_call`、`public/js/frappe/form/controls/button.js`、`request.js`（`opts.doc`、返回值同步）、`model/sync.js`（`update_in_locals`、`add_to_locals`）、`model/document.py`（`check_if_latest`、`check_docstatus_transition`）、`model/naming.py:_set_amended_name`、`create_new.js:copy_doc`（amend 时不受 `no_copy` 限制）；erpnext `company.py:validate_default_accounts`、`company.js` 两个字段的过滤；容器内 bench `app.py:188-194`（`git clone … --depth 1 --origin upstream`）、`bench.py:shallow_clone`、`config/common_site_config.py:12`。
- zelin：`cash_flow.js`（`set_query` 与 `get_cash_flow_items` 处理器）、`default_accounts.csv` 两个字段。

**做过的只读实验与查询**：
- 两站只读 SQL：Cash Flow 按钮 DocField、DocPerm（含 amend／delete）、Custom DocPerm、Client Script、Property Setter、`Document Naming Settings.default_amend_naming`、`Amended Document Naming Settings`、`Bank Statement Format.summary_keywords` 默认值、四张 Report 的 `ref_doctype`、Cash Flow／预处理／格式条数、`is_opening` GL 条数、FY；演示站 1901／5711010／1001／1002／1012 的科目属性与 HDTH 两个默认科目。
- `bash -n`：`setup.sh`、`restore.sh`、`lock-apps.sh` 均通过。
- 宿主机临时目录（`mktemp -d`，已删）两个纯 git／bash 实验：① 照 bench 的写法 `git clone --depth 1 --origin upstream` 后执行 setup.sh 第 3 段的锁定三步；② `IFS=$'\t' read` 遇空字段的行为。均不碰站点与仓库。
- 一次 WebSearch：小企业准则与企业会计准则应用指南对「购货退回收到的现金」的填列口径。

**跳过及原因**：
- 未跑测试、未 migrate、未写站点、未跑 `up.sh`／`restore.sh`／`backup.sh`（硬约束；主会话在测试站跑全量回归）。
- 未在浏览器实点、未发真实 HTTP 请求（硬约束）。FD-001、FD-024 的「真实请求下是否生效」是**读上游源码**得出，验证步骤见文末。
- `setup.sh` 未实跑；P4-01 的结论来自 bench 源码＋临时目录里的 git 实验（只模拟了 clone 与锁定三步，没有跑 `bench get-app` 本体）。
- 总纲只按需检索，未通读（上轮已读全，本轮改动不涉及总纲条款）。
- R15 方案与 R16 回执只按关键词读了与 README、1901、5711010 有关的段落。

## 已修项复核表

三层：落地（代码在）→ 生效（真被调用、未被绕过）→ 原问题消失。

| FD 号 | R14 判定标准 | 定位（文件:行） | 落地 | 生效否 | 原问题消失否 | 自证一致否 | 说明 |
|---|---|---|---|---|---|---|---|
| FD-001 | 界面点「取现金流明细」能取回明细 | `cash_flow.json:13`（`options:"get_cash_flow_items"`）；`cash_flow.py:174-197`（`@frappe.whitelist()`）；两站 `tabDocField.options` 均为 `get_cash_flow_items` | ✅ | ✅（读码） | ⚠ 服务端✅、浏览器未实点 | ✅ | 调用链逐段核过：`button.js:39-50` 无 JS 处理器 → `df.options` 非空 → `run_server_script` 以 `docs=frm.doc` 调 `run_doc_method`（新单的 `docname` 是 `new-cash-flow-…`，非空，可进入）→ `handler.py:290-293` `get_doc(docs, check_permission=True)` 只查 read（两个会计角色有）；新单 `__islocal=1`，`check_if_latest` 不比时间戳 → `is_whitelisted` 通过（`test_cash_flow.py:105` 断言在 `frappe.whitelisted` 中）→ `frappe.response.docs` 带回 → `sync.js:update_in_locals` 用新行覆盖子表 → `refresh_fields`。两站无 Client Script／Property Setter 干扰。README:97 现在与事实相符。连带问题见 P4-06 |
| FD-002 | ① 提交与出表时核 yearly 22 ＝月末余额；② 取明细排除 `is_opening='Yes'`，月初与年初余额口径一致；③ 测试含开账凭证 | `cash_flow.py:185`（排除开账）、`:127-140`（`_cash_balance_before`／`_opening_entries`）、`:254-255`（月初、年初同口径）、`:290-292`（提交时 yearly 断言）；`cash_flow_statement.py:150-152、178`（出表核本年累计列） | ✅ | ✅ | ✅ | ✅ | 推演三种情形：1 月 1 日开账 10000 ＋1 月收 500 → 1 月 21＝(10000,10000)、22＝(10500,10500)；2 月 21＝(10500,10000)，22 年额＝0＋500＋0＋10000＝10500 ✅；年中 3 月 1 日开账 8000 → 3 月月初＝0＋8000、年初＝0＋8000 ✅；上年 12 月 31 日开账 → 落在 `_cash_balance_before(year_start)` 内 ✅。`gl_sums(fy_opening_of=)` 本片已不再调用（只剩资产负债表用），跨片拼装缺口消失。测试 `test_opening_entry_is_opening_balance_not_cash_flow`、`test_mid_year_opening_entry_joins_that_month_opening`、`test_year_to_date_ending_balance_is_checked` 有判别力（R14 变异 M1–M3）。口径是**草案·待领域专家确认** |
| FD-006 | 取消后会计角色能重做该月 | `cash_flow.json:18`（两角色 `amend:1`）；两站 DocPerm `amend=1`、`delete=0`；两站 `default_amend_naming=Amend Counter`、无按单据覆盖 | ✅ | ✅ | ✅（修订路径） | ✅ | `naming.py:178` 修订单先走 `_set_amended_name`（`XJ-…-1`），不进 `autoname`，不撞名；`_validate_period` 唯一性排除 `docstatus=2`，已取消单不挡。界面「修订」走 `create_new.js:copy_doc(from_amend=true)`，`no_copy` 不生效，子表一并带过去，会计再点取明细即可。「新建同月」仍撞已取消单的名字——R14 裁决只补 `amend`，属预期；但提示文字没指向「修订」，见 P4-08 |
| FD-010 | `_` 不被遮蔽，非法报表名报原提示 | `printing.py:73`（`*_rest`）、`:96`（具名变量）；`closing.py:341` 同形修复 | ✅ | ✅ | ✅ | ✅ | 全 app 非测试代码再 grep `_` 解包形式，只剩两处注释。`test_unsupported_statement_reports_its_name` 有判别力（R14 M5） |
| FD-026 | README 四处与事实相符；license 填实 | `README.md:25、97、106、134`；`license.txt:3` | ✅ | — | ✅（四处本身） | ✅ | 四处逐条核过：远端只有 `main`（`git branch -vv` 跟踪 `origin/main`）；按钮承载与 FD-001 一致；zelin 测试确未带入；LG-152 已补。**但 README 未跟上 R14 SB 与 R16 的后续改动**，见 P4-04 |
| FD-009 | 按 `apps.json` 重建能锁到指定 commit；重跑 `up.sh` 不失败；私有仓库有凭据办法 | `docker/apps.json`（三条带 `app_name`）；`setup.sh:126-176`；`lock-apps.sh:53`；`docker/README.md`「私有仓库」节 | ✅ | ⚠ | ⚠ 一半 | ❌ | **已解决**：目录判断改用 `app_name`，重跑不再二次克隆；去掉 `--resolve-deps`；克隆前 `ls-remote` 探测并指向 README。**未解决**：新机器上的锁定。bench 克隆用 `--depth 1 --origin upstream`（容器内 bench `app.py:190-194`，`shallow_clone` 默认 true），而第 3 段锁定时 `fetch origin`（`setup.sh:162-163`）——remote 要到第 4 段才改名为 origin。临时目录实验：浅克隆＋只有 upstream 时两次 fetch 都失败、`reset --hard` 取不到旧 commit，只打一行警告、停在分支最新。SB 回执情形 ① 用的是自写的假 get-app，没有复现 `--origin upstream` 与浅克隆，**「锁到指定的 40200dc」这条声称在真实 bench 下不成立**。见 P4-01 |
| FD-021 | 方向不符、选公式行都被拒；预填不预出会被拒的代码 | `cash_flow.py:93-114`（两条校验）、`:199-228`（预填跳过）、`:295-301` `_direction_fits`；`zh.csv:148-149` | ✅ | ✅ | ✅ | ✅ | fixture 核过：公式行为 7／13／19（type_subtotal）、20／22（above_subtotal）、21（last_period_balance），全被 `formula` 判到；流入项目 8、9、10、14、15 的 `is_outflow` 为空，`not None` 判为流入，正确。内部转账行豁免。测试断言了行号与报错文字。方向约束是**草案·待领域专家确认**，与通行口径的冲突见 P4-07；README 未登记，见 P4-04 |
| FD-023 | 日期写错且摘要含关键字的真实明细不被吞；`NaN`／`Infinity`／`1e5` 报金额无效 | `bank_import.py:20-22、106-123、171-181`；`bank_statement_format.json:30`；两站 DocField 默认值已是 `合计|总计|小计|本页` | ✅ | ✅ | ✅ | ✅ | 合计行只看日期格且要求无流水号；正则只收普通十进制；xlsx 数字格走单独一支，`bool` 先排除，非有限值拒收。`test_summary_row_rule_does_not_swallow_real_rows` 覆盖了「摘要含关键字」「日期格含关键字但有流水号」「真合计行」三类。新判据的副作用见 P4-10 |
| FD-024 | 经界面调用失败时 Failed 与 log 落库 | `bank_import.py:277、320-337、392`；上游 `app.py:181-184`、`database.py:1196-1215` | ✅ | ✅（读码） | ⚠ 服务端✅、前端看不到 | ✅ | 真实请求路径逐段核过：`/api/method/…` → `api.handle` → `handle_rpc_call` → `handler.handle` → `execute_cmd`，中间没有自己的 rollback；异常落到 `app.py:181` 的 except，`handle_exception` 之后 `db.rollback(chain=True)` → `rollback` 先 `before_commit.reset()`、执行 SQL rollback，最后 `after_rollback.run()` → `_persist_failure` 在新事务里 `set_value`＋`commit`。`commit` 会 `after_rollback.reset()`，但它在 `run()` 的 popleft 循环里只清掉排在它后面的回调；本函数在两条失败分支里都是最后一个登记的，不会吞掉别的回调。GET 请求同样走 except 分支，结论不变。**仍有一处没闭环**：表单按钮 `.then(() => frm.reload_doc())` 只在成功时刷新，失败时界面仍显示 Draft、log 空，直到手动刷新，见 P4-05。未经真实 HTTP 验证（SB 回执复核建议 1 维持） |
| FD-027（脚本那半） | 子目录里的基准备份用脚本恢复得到 | `restore.sh:18-51`；`docker/README.md` 三处 | ✅ | ✅（读码＋`bash -n`） | ✅ | ✅ | 带时间戳时根目录与 `*/` 子目录都找，三件套取同一目录；含中文的路径在 `bash -c` 里用单引号包住。不带参数行为不变。`docs/项目概况.md:67`「须显式指定」现在有脚本支撑。项目概况三节按裁决留到 S4 收口，不算缺陷 |
| FD-022／025／042／043（延迟） | 确认未被改得更糟 | `bank_statement_preprocess.json`（无改动）；`bank_import.py:46-56`（`_cell` 无改动）；`printing.py:55-65`（无改动）；`labels.py:31-44`（无改动） | — | — | 未变 | — | 四项代码均未改动。FD-023 新增的数字格分支只管金额，不碰流水号，FD-025 不受影响 |

## 开放查漏新发现

| 片内编号 | 严重程度 | 定位 | 问题 | 违背的标准 | 建议修法 | 建议档位 | 待裁决点 | 证据 |
|---|---|---|---|---|---|---|---|---|
| P4-01 | 中 | `docker/scripts/setup.sh:158-176`（第 3 段锁定）对比 `:180-221`（第 4 段才把 remote 改名为 origin）；bench `app.py:190-194`；bench `config/common_site_config.py:12` | **新机器上锁定 commit 仍然不生效**（FD-009 的另一半）。bench 克隆时 remote 叫 `upstream`，而且默认浅克隆（`--depth 1`）。第 3 段锁定时 `fetch … origin`，origin 还不存在，两次 fetch 都失败；`reset --hard <锁定值>` 在浅克隆里找不到这个提交，于是只打一行「取不到 commit，保持当前」的警告，继续往下跑，停在分支最新。锁定值等于分支最新时碰巧对；不等时就失效——**当前就是这种情况**：`apps.json` 锁 `48e7933`，`main` 最新是 `21faeb9`。这是 R14 之前就有的写法，FD-009 没改到；SB 回执的情形 ① 用假 get-app 模拟，没有复现 `--origin upstream`＋浅克隆，所以「已锁到 40200dc」那条声称在真实 bench 下不成立 | 开发守则「版本锁定」（换机器按 apps.json 拿到同一版本）；R14 FD-009 判定标准第 1 条；不静默（警告后继续，结果仍是错的版本） | 锁定时不写死 remote 名：先 `git -C … remote` 取第一个 remote，或 `fetch "$app_url" "$app_commit"` 直接按 URL 取；取不到时 `exit 1`（响亮失败），不要只警告。另一种做法：把第 4 段（改名）挪到第 3 段之前 | 新Session修 | 锁定失败时是中止 `up.sh` 还是警告后继续；修后能否在临时目录用真 `bench get-app` 跑一次 | 临时目录实验输出：`remotes: upstream` / `both fetches failed` / `lock FAILED, stays at 1272aaf (wanted 16976bd)`。`docker compose exec frappe` 读 bench 源码：`args = f"{self.url} {branch} {shallow} --origin upstream"`、`shallow = "--depth 1" if self.bench.shallow_clone` |
| P4-02 | 中 | `docker/apps.json` 第 3 条 `commit: 48e7933…`；frappe_china `HEAD = origin/main = 21faeb9`、工作区干净；`setup.sh:158-176` | **`apps.json` 没有随 R16 重新锁定，此时在本机重跑 `up.sh` 会把 frappe_china 退回 R14 SB 的代码**。第 3 段的判断是「当前 ≠ 锁定值、且工作区干净」就 `reset --hard` 到锁定值。本机现在正好满足：会把 `main` 分支指针从 `21faeb9` 拉回 `48e7933`，R16 的默认科目改动与 `fd004_default_accounts` 补丁从代码里消失，而两站数据库里已经跑过那个补丁。提交都在远端，可以找回，但运行中的代码会悄悄变成旧版本，脚本只打一行「已对齐到」 | 开发守则「版本锁定」；R13、R14 每轮都锁到当轮提交的惯例（S4 概况 R13、R14 行） | ① 本轮或 S4 收口时跑 `docker/lock-apps.sh` 锁到 `21faeb9`（主仓库提交须用户许可）；② `setup.sh` 加一道保护：锁定值是当前 HEAD 的祖先时（`git merge-base --is-ancestor`）不往回退，只警告「apps.json 比本地旧，请跑 lock-apps.sh」 | ① 本Session修（只是重锁）；② 新Session修 | R16 不重锁是有意（留到收口）还是遗漏；是否加「不回退」保护 | `git -C frappe_china branch -vv`：`main 21faeb9 [origin/main]`；`git status` 干净；`merge-base --is-ancestor 48e7933 21faeb9` 成立；`docker/apps.json` 最后一次改动是 `2345991` |
| P4-03 | 低 | `docker/scripts/setup.sh:126`（`IFS=$'\t' read -r app_url app_branch app_commit app_name`）、`:173-176`；`lock-apps.sh:65`（「解除锁定：删掉 commit 字段」） | **照 `lock-apps.sh` 的说明删掉 `commit` 解锁后，`app_name` 会被读进 `app_commit`**。tab 属于 IFS 空白字符，连续两个 tab 被当成一个分隔符：`url⇥branch⇥⇥frappe_china` 读出来 `app_commit=frappe_china`、`app_name` 为空。于是 `app_name` 退回仓库名 `FrappeChina`，FD-009 的原问题（重跑时二次克隆、改名撞目录而中止）复现；锁定那步再拿 `frappe_china` 当 commit 去 reset，只打警告 | R14 FD-009 判定标准第 2 条（重跑不失败）；`lock-apps.sh` 自己给出的解锁办法应当可用 | Python 那段对空值输出占位符（如 `-`），bash 里再把 `-` 当空；或改用非空白分隔符（如 `$'\x1f'`） | 新Session修 | — | 实验：`printf 'u\tb\t\tn\n' \| { IFS=$'\t' read -r a b c d; … }` 输出 `[u][b][n][]` |
| P4-04 | 低 | app `README.md:72-75`（默认科目那几行）、`:97`、`:109`、`:111` | **README 的「相对 zelin 的修改」没跟上 R14 SB 与 R16 的改动**（AC-014 要求逐条登记每处修改及原因）。① FD-021：zelin 用 `cash_flow.js` 的 `set_query` 在界面上按借贷过滤项目、排除公式行，本 app 改为后端 validate 拒绝；README:97 对 `cash_flow.js` 只说「下载按钮与批量填属界面便利」，没提 `set_query` 这项被后端校验取代。② FD-021 连带：预填现在跳过方向不符或公式行的候选，README:109、111 仍写「顺序同 zelin」，没写这处不同。③ R16：zelin 的 `stock_adjustment_account`＝「生产成本-库存调整」、`disposal_account`＝「固定资产清理」，现改为 `1901`、`5711010`；只在「已知限制」里写了，「科目表、税与默认科目」那张 zelin 对照表里没登记这两处改动与原因（DEC-122／123）。FD-026 的四处本身都已改对 | Part4 TS-020；AC-014 | 三处各补一行：`set_query` → 后端校验（原因：界面与脚本都要挡；方向约束为草案）；预填跳过方向不符候选；两个默认科目相对 zelin 的改动与 DEC 号 | 本Session修 | — | `git diff 40200dc HEAD -- README.md`；zelin `cash_flow.js:5-15`；zelin `default_accounts.csv:21、30` |
| P4-05 | 低 | `cn_tax/doctype/bank_statement_preprocess/bank_statement_preprocess.js:7-12`；上游 `request.js`（`frappe.call` 返回 jQuery 的 `$.ajax` 链，失败时不执行 `.then` 的成功回调） | **FD-024 补写的 Failed 在界面上看不到**。按钮的回调是 `.then(() => frm.reload_doc())`，只在成功时刷新。失败时弹窗报错，表单仍显示 Draft、log 为空，要用户自己刷新才看到 Failed。更糟的一点：`_persist_failure` 的 `set_value` 会更新 `modified`，用户若在这张没刷新的表单上改附件再保存，会碰到「打开后已被修改」的时间戳冲突 | 方案 TS-018「Failed 时写 log」的意图（让用户看到失败原因）；R14 FD-024 判定标准 | 改为成功、失败都刷新：传 `callback` 与 `error` 两个回调都调 `frm.reload_doc()`，或用 `.always(...)` | 新Session修 | — | 读码；未在浏览器验证 |
| P4-06 | 观察 | `cash_flow.json:13` `depends_on`；上游 `button.js`、`handler.py:290-293`、`document.py:1119-1157` | 「取现金流明细」按钮的两处界面行为与 zelin 不同。① 显示条件只看公司、年度、月份，**已提交和已取消的底稿上也显示**：已提交单上点它，服务端在内存里重取明细（不保存），返回后表单显示的明细与已提交内容不同；已取消单上点它报「Cannot edit cancelled document」。② 已保存的草稿上点它，明细换了但表单**不标脏**（zelin 的处理器调了 `frm.dirty()`，`run_server_script` 不调），用户离开页面不会被提醒，新取的明细直接丢掉。新单不受影响（新单本来就未保存） | 需求 §4.10.1「按钮取现金流明细」的可用性；不静默 | `depends_on` 加 `doc.docstatus===0`。标脏一项要补 JS 处理器才做得到，与 FD-001「用 options、不补 js」的裁决冲突，可只登记 | 延迟或不修 | 是否为第 ② 点补一个最小 `cash_flow.js` | 读码 |
| P4-07 | 观察（业务口径） | `cash_flow.py:102-114、295-301`；`test_cash_flow.py:134-137` | **FD-021 的方向约束与通行填列口径有冲突**。《企业会计准则应用指南》第三十二章写明「购买商品、接受劳务支付的现金」要「减去本期发生的购货退回收到的现金」，销售退回同理冲减流入项目；《小企业会计准则》会小企 03 表第 3 行只说「分析填列」，没有明文。按现在的约束，收回供应商退款（借方）只能选流入项目（如 2「收到其他与经营活动有关的现金」），流入、流出两边各虚增一笔，净额不变。算法本身支持冲减（第 3 行展示值＝−(借−贷)，借方行会把它减小），是校验把这种做法挡住了。另：拆分时手工填负数的行，借贷都不 > 0，`_direction_fits` 直接放行 | 规则本身是草案；SB 回执「拿不准处」已提过退款场景，本条补上口径出处 | 随草案规则一并送领域专家：若确认要按冲减处理，改为「按项目放行反向」（如 1、3 允许反向），不是取消校验；负数行至少按符号折算后再判方向 | 延迟或不修（等专家） | 退货／退款按冲减还是按总额列示 | WebSearch：[企业会计准则应用指南第三十二章](https://docs.maoyanqing.com/accounting/ent/casg/31.html)；[小企业会计准则附录（会小企 03 表填列说明）](https://docs.maoyanqing.com/accounting/se/cass/appendix.html)，财政部原文 [PDF](http://kjs.mof.gov.cn/zhengcefabu/201111/P020111118325852734144.pdf) |
| P4-08 | 观察 | `cash_flow_statement.py:143`（说明行「请取消后重取明细」）；`cash_flow.py:15-19` | FD-006 修好的是「修订」这条路；会计若照说明行字面「取消后重取明细」去**新建**同月底稿，仍会撞已取消单的名字，报框架的重名错误，看不出该点「修订」。不静默，只是提示不准 | SL-007 ⑦ 的补救动作要能照着做 | 说明行改为「请取消该月底稿，点『修订』后重取明细」；或 `_validate_period` 发现同月有已取消单且本单不是修订单时，报一句指向「修订」的话 | 延迟或不修 | — | 读码；两站 `default_amend_naming=Amend Counter` |
| P4-09 | 观察 | `templates/statements/balance_sheet.html:15`（`td:nth-child(n+3){text-align:right}`）；三份模板只差 `@page` 一行 | 右对齐选择器按「第 3 列起」写，对利润表、现金流量表（第 3、4 列是金额）正确；对**资产负债表 8 列**，第 5 列「负债和所有者权益」的行名和第 6 列行次也被右对齐，而左栏的行名、行次是左对齐，左右两栏版式不一致。`table-layout: fixed` 又没给列宽，各列等宽，长行名多处折行（`test_statement_export.py` 为此专门写了 `_contains_wrapped`）。方案只要求「金额右对齐、千分位」，字串层面不违规 | Part4 TS-017「金额右对齐」；法定报表的可读性 | 改为按 `fieldtype` 给单元格加 class（`_table_rows` 已拿得到列的 fieldtype），金额列右对齐；给行名列一个较宽的 `<col>` 宽度 | 延迟或不修 | 是否在 S6 版式统一时一并做 | 三份模板 `diff` 只有第 6 行不同 |
| P4-10 | 观察 | `bank_import.py:171-181` | FD-023 收紧后，**把「合计」写在日期列以外的网银文件会整份报错**。常见的另一种版式是合计行日期为空、「合计」写在摘要或「交易类型」列；按新判据它不算合计行，按日期无效报错，整份文件导不进。这是「响亮失败」，符合 SL-009；只是 `summary_keywords` 配置项现在只对日期格起作用，没有办法改配哪一列，到时只能改代码 | SL-009「坏行响亮失败」（满足）；§4.12「真实版式到现场再调」（LG-147） | 等 LG-147 拿到真实样本再定；若要提前，可在格式上加「合计行判据列」 | 延迟或不修 | — | 读码；`test_summary_row_rule_does_not_swallow_real_rows` 第 6 行用例 |
| P4-11 | 观察 | `docker/README.md`「私有仓库」节 | 示例命令 `printf 'https://<用户名>:<令牌>@github.com\n' > ~/.git-credentials` 会把令牌留在容器 shell 历史里；凭据明文存放（README 已写明不进 git、随容器删除而丢）。影响限于本机容器 | 安全卫生 | 改为 `read -rs TOKEN` 再写入，或提示用 `git credential approve` | 延迟或不修 | — | 读文档 |

**定级说明**：P4-01、P4-02 定「中」：都只影响环境重建，不影响产品代码；但两者都会让 bench 里跑的代码与锁定值不一致，而脚本只打警告或一行「已对齐」。若近期不换机器、不重跑 `up.sh`，可降为「低」。

## 业务规则合规核表

七条均「未经专家确认」，以下结论在此前提下成立。

| 规则条款 | 本片是否涉及 | 结论 | 备注 |
|---|---|---|---|
| BR-001 小企业会计准则 | 涉及（现金流量表表号、README） | 合规 | PDF 表号「会小企 03 表」、README:70 说明「(2024)」只是文件名，未变 |
| BR-002 三表＋附注，月报与年报 | 涉及（现金流量表月报、年报） | 合规 | 年报「上年金额」取上年 12 月本年累计，未变；附注不在本 Stage |
| BR-003／004／005／007 | 不涉及 | — | 本片不碰税率、结转、价税分离 |
| BR-006 资产负债表平衡 | 不涉及 | — | Part3；PDF 模板只排版 |
| 草案：开账分录（`is_opening='Yes'`）不是本期现金流量，并入所在月份的期初余额（FD-002） | 涉及 | **草案·待领域专家确认** | 代码、测试、README:135 三处一致；年初开账、年中开账两种情形期末都等于科目余额 |
| 草案：本年累计期末现金余额＝月末现金余额（FD-002） | 涉及 | **草案·待领域专家确认**（对自然年会计年度在算术上成立） | 提交时与出表时都核。非自然年会计年度下 `year_start` 写死为 1 月 1 日（`cash_flow.py:249`，R14 前就是这样），不成立，属既有限制 |
| 草案：借方现金行只能选流入项目，贷方只能选流出项目；明细不得选公式行（FD-021） | 涉及 | **草案·待领域专家确认**；方向约束与通行口径有冲突（P4-07） | 公式行约束无争议（公式行由系统算出）；方向约束挡住了退货冲减的做法 |
| 草案：现金只含 `1001＋1002＋1012`（Cash／Bank 类型） | 涉及 | **草案·待领域专家确认** | 未变；演示站三个科目的 `account_type` 为 Cash／Bank／Bank |
| 草案：内部转账按「凭证全部分录都在现金类科目」识别 | 涉及 | **草案·待领域专家确认** | 未变（混合凭证不识别，R14 已登记） |
| 库存调整默认科目 `1901`、资产处置 `5711010`（DEC-122／123／125，R16） | 部分涉及（README 一致性） | README 与站点事实一致 | 演示站 1901：Asset、`account_type` 空；5711010：Expense、Profit and Loss——与 README:127 所述相符；上游 `company.js:307、332` 的两条过滤与 README 说法相符；`validate_default_accounts` 不查 root_type／account_type，「服务端不校验」成立。zelin 对照表未登记，见 P4-04 |

本片没有发现新增或改写、已生效的业务规则；上表「草案」行均由 AI 推断，按触点 ③ 待送审，本步不改 `业务规则.md`。

## 交接摘要

**本片依赖别片**：
- Part3：`ledger.gl_sums`（`to_date`、`exclude_pl_closing`，空列表返回 `{}`）。本片改用两个私有方法组合月初、年初余额，不再调 `fy_opening_of`；该参数现在只剩资产负债表在用（`balance_sheet.py:123`、`engine.py:31-34`），其开账口径归 Part3 判断。
- Part1：`setup.sh` 第 1、4 段（bench init、remote 改名），P4-01 的修法牵涉第 3、4 段的先后顺序。
- R16（Part1／Part3 范围）：`company_defaults.json` 两个默认科目与 `fd004_default_accounts` 补丁。本片只核了 README 与站点属性是否一致。

**本片暴露给别片**：
- `docker/apps.json` 锁定值 `48e7933` 落后于 frappe_china `21faeb9`（P4-02），收口时请主会话定是否重锁。
- `5711010 非流动资产处置净损失` 在源科目表里 `account_type = Fixed Asset`（演示站实查）。损益类科目带「Fixed Asset」类型，可能出现在按 `account_type=Fixed Asset` 过滤的下拉里（如资产类别的固定资产科目）。不在本片范围，请 Part1／Part3 判断是否需要登记。
- `bank_import._mark_failed` 确立的「after_rollback 补写」约定（SB 回执「新增约定」第 1 条）：本片读码确认它在真实请求异常路径上会执行；但前端不刷新（P4-05），别处若照搬这条约定，前端也要成功、失败都刷新。
- `cash_flow_statement` 说明行措辞新增「本年累计期末现金余额…不符」（中文硬写，非 `_()`，与原「期末现金余额…不符」同一写法），S6 若引用措辞需知道。

## 盲区自述与把握最低处

- **界面层仍是读码**：FD-001 按钮、FD-024 失败留痕、P4-05、P4-06 都没有在浏览器或真实 HTTP 下验证。FD-001 的调用链里，我最没把握的是 `sync.js:update_in_locals` 对「服务端新增、尚无 name 的子表行」的处理：读码看它会为这些行补本地名并挂进 `locals`，但没有实测表单是否正常刷新出明细。
- **P4-01 只模拟了 git 层**：临时目录里复现的是「浅克隆＋只有 upstream remote」下的 fetch 与 reset；没有跑真的 `bench get-app`，也没核 frappe（由 `bench init --frappe-path` 克隆）是否同样是浅克隆。若 bench init 对 frappe 不做浅克隆，frappe 那一条只受「fetch origin 失败」影响，`reset --hard` 仍可能成功。
- **P4-02 的后果是推断**：`reset --hard` 会把分支往回拉，这一点由 `setup.sh:163-168` 的写法与当前 git 状态确定；但我没核「代码退回 `48e7933` 后，站点上已跑过的 `fd004` 补丁与 R16 测试」会出什么具体问题。
- **业务口径**：P4-07 的出处是企业会计准则应用指南；小企业会计准则原文对退货没有明文，是否必须冲减是会计判断，我只能标为待专家确认。
- **没往这些方向找**：多币种、非自然年会计年度、带账簿的现金分录（`_opening_entries` 与取数都排除了非空账簿，口径一致，但没推演）；`restore.sh` 时间戳参数含通配符字符时的行为；`Bank Transaction Rule` 与两张原生对账报表。
- **把握最低处**：FD-024 我判「服务端生效」依据的是 v16 `app.py` 与 `database.py` 的现行代码。`/api/v2/method/…` 入口也核过：`api/v2.py:45、155` 两处 `except` 只是改写报错再 `frappe.throw`，不自行 rollback，异常仍落到 `app.py:181` 统一回滚，结论相同。没核的是 server script 包装同名方法（`_api` 映射）这一路径，本 app 不用它。
