# SB 修复回执（对象：代码 / 依据：P1-S6-R12 F 审核报告＋R3／R6／R9 开发方案）

**轮次**：P1-S6-R12 附属（SB 不占 Round）｜**开工**：2026-10-14｜**执行者**：Claude（Opus 5.5；workflow 预设 CodeX，S6 概况偏离同 D 步）
**Spec**：[SB-fix-plannedDev-build.md](../../../流程体系/workflows/plannedDev/SB-fix-plannedDev-build.md)＋`bricks/receipt.md`｜`打tag=否`
**依据**：[R12 F 审核报告](P1-S6-R12-F审核报告.md) 裁为 `新Session修` 的 11 项（FD-001、002、008、009、010、012、013、016、017、019、024），证据见分片报告与 `Spike/P1S6R12-F/p{n}/`；原方案 [R3 总纲](../R03-开发方案/P1-S6-R3-C开发方案-总纲.md)＋Part1～4、[R6](../R06-开发方案/P1-S6-R6-C开发方案.md)、[R9](../R09-开发方案/P1-S6-R9-C开发方案.md)
**执行前基线**：`frappe_china` HEAD `68476a3`，工作区干净；`docker/apps.json` 锁 `68476a3`；`zh.csv` 5857 行；全量 270/270、Node 73/73（R12 当场修后）；演示站清洁基准 `20261013_030125`；主仓库只有 ` M Spike/P1S6R9/ts036/bench-start-after.log`（FD-024）

## 用户裁决（本步执行中）

| 项 | 待裁决点（R12 报告原文） | 裁决 | 时间 |
|---|---|---|---|
| FD-008 | 首页「Expenses」图标是否必须显示「报销管理」 | 不必：收回无 context 行，图标随全站回落官方「费用」，不加前端补丁 | 2026-10-14 |
| FD-017 | 第五道守卫（台湾用词表）要不要加 | 不加，只做 QE 分守卫豁免与「译文等于源词」进测试两项 | 2026-10-14 |
| FD-009 | 不在演示线上的两处（`Ledger` 纸型、`Item Type` 导航栏条目）修还是登记接受 | 都修：`Ledger,账簿纸,Print Settings`、`Item Type,条目类型,Navbar Item` | 2026-10-14 |
| FD-009 | 日记账凭证类型显示「红字发票」算不算误伤（会计判断） | 判不了，登记延迟 `SH-P1S6007`，待会计确认 | 2026-10-14 |
| FD-024 | 是否现在重启演示站 `bench start`；`git restore` 须许可 | 许可，现在做 | 2026-10-14 |

## 逐项执行结果

| 任务 | 报告项号 | 落地位置（文件:行） | 结果 | 完成时间 | 说明 |
|---|---|---|---|---|---|
| SB-1 收付款凭证开账总账按钮 | FD-001 | `frappe_china/public/js/opening_ledger.js:5-11`（PE 分组由 `"fa fa-table"` 改为不带分组）；`frappe_china/tests/test_opening_ledger.cjs:13-43`（桩照上游：添加时置空 `fa fa-` 分组、删除时不置空、同名已在不挂新回调）；`frappe_china/README.md:103`；`Spike/P1S6R12-SB/fd001/`（`red.log`、`repro-after.json`、`pe-setup.py`、`pe-click.cjs`、`old-code/`、`patched/`） | ✅完成 | 2026-10-14 | 先改桩：PE 两条用例红（`red.log`），JE 照旧绿；改补丁后 8/8。R12 的 happy-dom 复现 `pe_button_repro.cjs` 改后 PE 只剩 1 个工具栏按钮、点击带 `show_opening_entries=1`。测试站实点见复验。探针 PE 与公司开关已还原 |
| SB-2 工位看板分组标题 | FD-002 | `frappe_china/dashboards.py`（新建，`workstation_dashboard`）；`frappe_china/hooks.py:256-258`（`override_doctype_dashboards`）；`frappe_china/tests/test_dashboards.py`（新建，4 条）；`frappe_china/README.md:97-101`（看板覆盖登记）；`Spike/P1S6R6-screen-check.js`（每屏可选 `forbid`／`require`）；`Spike/P1S6R9/screens-build.py`（加 `05-workstation-connections`，144 屏）；`Spike/P1S6R9-screens.json`（重生成）；`Spike/P1S6R12-SB/fd002/` | ✅完成 | 2026-10-14 | 按用户裁决路线 ①。占用核查：`Master Data` 在六个上游 app 源码与 po 里 0 处，只有本 app 侧栏分节用它（「基础资料」），复用不改 csv。按 items 集合认分组，不按 label：label 在 `get_data()` 里已被 `_()` 过、随语言变。逐屏核原只拦英文与繁体，「少爷」是中文、拦不住，故给检查脚本加每屏 `forbid`（不得出现）与 `require`（必须出现，防该区域没渲染而空过），只有新屏用到，其余 143 屏行为不变。L3 定级沿用审核报告的读码结论 |
| SB-3 `Expenses` 收回无 context 行 | FD-008 | `frappe_china/translations/zh.csv`（删 `Expenses,报销管理`）；`frappe_china/tests/translation_overrides.py`（删该条登记）；`frappe_china/tests/test_named_terms.py`（`Expenses`→「费用」进 `NAMED_TERMS`，守住不再被覆盖）；`Spike/P1S6R12-SB/fd008/`（`red.log`、三个模块的绿日志、`check.py`、`check.out`） | ✅完成 | 2026-10-14 | 待裁决点「首页图标是否必须显示『报销管理』」开工时问用户，用户 2026-10-14 选「收回，图标显示『费用』」：不另走 `Desktop Icon` label 或前端补丁，全站回落官方。占用核查（六个 app 源码）：`Expenses` 出处有 Standard 科目表两处根节点、HRMS 首页图标与侧栏标题、报销单明细子表、HR 设置页签、HRMS 移动端两处，回落后都显示「费用」，意思都通 |
| SB-4 基线脚本源码出处索引、27 键逐条判 | FD-009 | `Spike/P1S6R4-baseline.py`（新增 `source_index`、`pot_refs`；`official_overrides` 每条无 context 覆盖加 `source_refs` 与 `hidden_refs`）；`frappe_china/translations/zh.csv`（加 `Ledger,账簿纸,Print Settings`、`Item Type,条目类型,Navbar Item`）；`frappe_china/tests/test_named_terms.py`（两键进 `NAMED_TERMS`）；S6 概况登记册 `SH-P1S6007`；`Spike/P1S6R12-SB/fd009/`（`baseline.json`、`baseline.log`、`hidden.txt`、`judgement.md`、红绿日志） | ✅完成 | 2026-10-14 | ① 索引扫六个上游 app 的 py／js／vue／ts／tsx／html 的 `_()`／`__()` 字面量与 json 的 label、Select 选项，跳过 `node_modules`、`locale`、`dist`、测试；出处口径与 main.pot `#:` 相同（相对 `apps/<app>/`），`hidden_refs` 即 main.pot 没记的那些。实跑：114 条覆盖中无 context 112 条，有未记出处的 27 条，与 R12 片 5 的数一致。② 27 键逐条判（`judgement.md`）：同义或可用 22 键不改；`Master` 已由 FD-002 处置；`Ledger`（打印纸型）、`Item Type`（导航栏条目）两处误伤按用户裁决写 context 行，渲染点 `df.parent` 分别是 `Print Settings`、`Navbar Item`（`select.js:82`、`grid_row.js:593`）；`Credit Note`／`Debit Note` 在日记账凭证类型里属会计判断，按用户裁决登记 `SH-P1S6007`。两个新词在 csv 与六个 po 里占用 0；带 context 的键不与官方无 context 键相交，不进 `OVERRIDES`。基线脚本出处索引耗时约 40 秒，用 `os.walk` 先剪目录（`rglob` 在 CRM 的 `node_modules` 断链上直接抛 `OSError`） |
| SB-5 销售发票其余三状态 context 行 | FD-010 | `frappe_china/translations/zh.csv`（按 A20 排序插入 3 行：`Partly Paid,部分收款,Sales Invoice`、`Partly Paid and Discounted,已贴现部分收款,Sales Invoice`、`Unpaid and Discounted,已贴现未收款,Sales Invoice`）；`frappe_china/tests/test_named_terms.py:42-45`（3 键进 `NAMED_TERMS`）；`Spike/P1S6R12-SB/fd010/` | ✅完成 | 2026-10-14 | 占用核查：三个译文在 csv 与六个 po 里 0 处。词形照已定的 `Unpaid:Sales Invoice`「未收款」与官方「已贴现未付」「已贴现部分付款」的结构，只换收付方向。`Overdue and Discounted`（官方「已贴现逾期」）不带方向，不改。带 context 的行不进 `OVERRIDES`（键带 context，不与官方无 context 键相交）。三处渲染点已由 SL-006 带上 context，本项只补行；测试站没有部分收款的发票，没有实页截图，渲染路径与 R5 SB IT-013 实测过的 `Unpaid` 同一条 |
| SB-6 取法与守则 A28 对齐 | FD-012 | `frappe_china/tests/test_translations.py` 的 `_source_strings_from_text`：Python 常量值改用 `ast.walk` 收全部 str 常量；JS 常量取整条赋值语句里的全部引号串与无插值反引号串（不再只看方括号内）；`_()`／`__()`／`translate(` 认反引号字面量、JS 第三位置参数作 context；同文件新增 `test_source_strings_follow_a28_wording`（8 例＋2 反例）；`docs/开发守则.md:105`（补形态与 context 写法）；`Spike/P1S6R12-SB/fd012/`（`run.py`、`red.log`、`green.log`、`app-diff.log`、`probe_forms-after.txt`） | ✅完成 | 2026-10-14 | 报告给两条路、二选一交 SB 定：选 ②「扩取法」——守则原文「其中的字符串字面量都算」是 R9 A28 定的约定，取法向约定靠，不把约定改窄；守则只补一句写明形态与 context，不改原意。取法仍在函数体内 import，清场脚本 AST 摘取不受影响。Python dict 的键也被取（如 `{"k": "Lambda"}` 取到 `k`），按守则原文这是对的。改前新用例红（`Alpha` 取不到），改后绿；R12 分片 6 的 `probe_forms.py` 12 例改前 7 例 MISS，改后 12 例全 OK；对本 app 全部源文件取词改前改后都是 280 键、差集空 |
| SB-7 取词正则恢复 `\\.` | FD-013 | `frappe_china/tests/test_translations.py:100`（`_()`／`__()`／`translate(` 取词）、`:129`（JS `SOURCES` 数组内取词），`(?:\.|…)` 恢复为 `474cd1c` 的 `(?:\\.|…)`；同文件新增 `test_source_strings_keep_escaped_quotes`（3 例）；`Spike/P1S6R12-SB/fd013/`（`run.py`、`red.log`、`green.log`、`diff_app.py`、`app-diff.log`） | ✅完成 | 2026-10-14 | 函数不 import frappe，宿主上抽出直接跑：改前 3 例全红（截断成 `Can\'`、`Say \`、`Don\'`），改后 3 例全绿。取出的键保留反斜杠，与 `main.pot` 取词口径一致，不在取法里反转义。恢复前后对本 app 全部源文件取词：都是 280 键、差集为空（现有代码没有转义引号源词，清场结果不变）。容器内 `test_translations` 随全量回归跑 |
| SB-8 四处用例判别力 | FD-016 | ① `frappe_china/tests/test_cash_flow_rename.py`（新装站用例同时 patch `frappe.db.exists=False`、`reload_doc`）；② `frappe_china/tests/test_named_terms.py`（`assertGreaterEqual(len(terms), 29)`；po 路径改 `frappe.get_app_path`）；③④ `frappe_china/tests/test_invoice_status.cjs`（新建 12 条：发票徽标带 context、`On Hold` 不改、重复下发不叠包装、筛选补 `df.context` 并委托原 `onload`、无 status 控件不抛；Select 取 `df.parent`／`doc.doctype` 与回退；库存类开账带参、`is_opening` 调账同路、非开账委托原方法、草稿不加按钮、缺类告警、重复加载不叠）；④ `frappe_china/tests/test_business_flow_navigation.py`（新增 `EXPECTED_LINKS` 51 项与三条用例：清单逐项相等、zh 下分节与条目中文不重名、图标 label＝侧栏 title 且 link_to＝侧栏 name）；`Spike/P1S6R12-SB/fd016/` | ✅完成 | 2026-10-14 | 报告点名的四处都补。① 每条都做了变异：删第一道守卫后新装站用例红（`rename-red.log`）。② po 路径改坏后 `0 not greater than or equal to 29`（`timesheet-red.log`）。③④ 前端：`mutate.cjs` 在临时目录对 js 打 5 个变异（报告列的三处删 context、库存类开账判定恒假、去 `show_opening_entries`），5 个都被杀。④ 导航：删 BOM 一项红；csv 追加 `Supplier,客户`（与 `Customer` 撞）红，还原后 md5 与原文件相同。`EXPECTED_LINKS` 由当前 json 生成，R12 片 3 已核过 json 与方案表、演示站库零差异。`test_opening_ledger.cjs` 桩的问题（报告 ⑤）已在 FD-001 一并修 |
| SB-9 `QUALITY_EXCEPTIONS` 分守卫豁免 | FD-017 | `frappe_china/tests/test_translation_quality.py`：`QUALITY_EXCEPTIONS` 改为「键 →（`frozenset` 守卫名, 理由）」，39 条按实测命中填（38 条 `mixed`，1 条 `mixed`＋`word_by_word`）；`_report` 只跳过该键登记的那道；新增第五道 `find_identity`（译文等于源词且源词不在 `UNTRANSLATED`）与 `GUARD_NAMES`；新增 `test_exception_waives_only_its_registered_guard`、`test_no_untranslated_rows`、`test_identity_guard_reports_constructed_row`，`test_every_exception_has_a_reason` 随新结构改；`frappe_china/tests/test_translations.py:242`（docstring）；`docs/开发守则.md:103`、`docs/项目概况.md:189`（四道改五道、QE 只写实测命中）；`Spike/P1S6R12-SB/fd017/`（`which_guard.py`／`.out`、`convert_qe.py`、`red.log`、两个模块绿日志、`guard_scan-after.txt`） | ✅完成 | 2026-10-14 | 第五道守卫（台湾用词）开工时问用户，用户 2026-10-14 选不加。守卫名由 `which_guard.py` 按 39 键在当前 csv 上逐道实测得出、`convert_qe.py` 机械改写（断言键、理由、顺序不变），不手填。「译文等于源词」原只在基线脚本里，现进测试：全 csv 只 `JAN,JAN` 一行相等，它在 `UNTRANSLATED`，不报。`test_translations` 的覆盖清单 `ours` 过守卫那条随 `guard_problems` 一并多查 identity，仍绿。`Spike/P1S6R7/guard_scan.py`、`apply_rows.py` 只用 `GUARDS`／`guard_problems`，接口未变，复跑 `guard_scan.py` 五道全 0 |
| SB-10 时间线选择器排除 `.frappe-card` | FD-019 | `frappe_china/public/js/desk_patches.js:158-163`（选择器改为 `.new-timeline .timeline-content:not(.frappe-card) b`）；`frappe_china/tests/test_desk_patches.cjs`（DOM 桩每段支持一个 `:not(.类)`；时间线桩加一张评论卡片；新增 `comment card bold null is user content and untouched`，原两条断言补上卡片那一项）；`frappe_china/README.md:67`；`Spike/P1S6R12-SB/fd019/`（`red.log`、`green.log`、`timeline-check.cjs`、`old-code/`、`patched/`） | ✅完成 | 2026-10-14 | `frappe-card` 加在 `.timeline-content` 自身上（`base_timeline.js:136`），不是外层，所以 `:not` 挂在 `.timeline-content` 上。先改桩与用例：旧选择器下 2 条红（卡片里的 `null` 被改成「（空）」）；改选择器后 Node 74/74（原 73，+1）。测试站实页见复验 |
| SB-11 受管日志改路径与还原 | FD-024 | 演示站 `bench start` 重起，输出改写到 `frappe-bench/logs/bench-start.log`（不受管）；主仓库 `Spike/P1S6R9/ts036/bench-start-after.log` 经 `git restore` 回到提交时的 27 行；重起前的 668 行另存 `frappe-bench/logs/bench-start-before-fd024.log`（本机）；`docs/开发守则.md`「长跑进程的日志不写进受管目录」（新增一节）；`Spike/P1S6R12-SB/fd024/`（`demo-translation-check.txt`、`demo-js-md5.txt`） | ✅完成 | 2026-10-14 | 动演示站进程、`git restore` 开工时问用户，用户 2026-10-14 许可。重起前先 `docker/backup.sh` 取一套 `20261014_162407`（演示站仍为清洁态，内容同 `20261013_030125`，只作重起前保险）。顺带完成 SB 收尾的演示站上线：`clear-cache` 后演示站发出的 `desk_patches.js`／`opening_ledger.js`／`invoice_list.js` md5 与源码相同，`translation_check.run`「译名自检通过」。约定「长跑进程日志不进受管目录」按报告建议写进开发守则（写前已载入常驻文件契约，同节其余内容仍成立）。**环境观察**：本机 `127.0.0.1:8000` 现被 `UnrealEditor.exe` 占着、`localhost` 回的是 Epic 的 404，演示站经 `0.0.0.0` 映射仍可从局域网 IP（`192.168.3.50:8000`）与组网 IP 访问，属本机进程冲突、非本项目改动 |

## 复验结果

| 报告项号 | 报告的判定标准 | 怎么复验的 | 实测结果 |
|---|---|---|---|
| FD-001 | PE 删除时不带分组；Node 桩照上游置空 `fa fa-` 分组；README 改回已生效；测试站开「预收预付记入单独科目」造开账 PE 实点（README 复验法：只剩一个会计凭证按钮且带开账参数） | `_S6R6 测试公司` 临时开 `book_advance_payments_in_separate_party_account`，脚本造并提交开账收款 `ACC-PAY-2026-00013`（`is_opening=Yes`，记入 `2203 预收账款`）；6787 起服务（`DEV_SERVER=1`）；`pe-click.cjs` 开表单数按钮、点「会计凭证」、读总账筛选与行数。两轮：临时换回 `68476a3` 的 `opening_ledger.js`＋`clear-cache`（old-code），放回修后版本＋`clear-cache`（patched）；同轮带开账日记账 `ACC-JV-2026-00002` 作对照 | **old-code**：PE 工具栏 1 个按钮，点后 `show_opening_entries=0`，本单 0 行（原症状复现）；JE 分组内 1 个，`=1`、2 行。**patched**：PE 工具栏 1 个、分组内 0 个，点后 `show_opening_entries=1`、本单 2 行；JE 不变。清理后 PE 与其 GL 均 0 条，公司开关回 0 |
| FD-002 | 选 ①：`override_doctype_dashboards` 换工位看板分组标题，`Master` 继续给称呼用；补一屏「工位表单·关联页签」进逐屏核，在测试站实页截图 | `test_dashboards` 先红后绿：临时换回 `68476a3` 的 `hooks.py`＋`clear-cache` 跑（`red.log`），放回后跑（`green.log`）；6787 上以 `_S6R6 验收工站` 跑新屏，撤钩与接钩各一轮 | **红**：4 条中 3 条失败（钩子未注册；zh 下分组为「少爷」；en 下为 `Master`）。**绿**：4/4，含 `_("Master")` 仍为「少爷」。**实页撤钩**：`pass=false`，`forbidden=[少爷]`（`unhooked/`）。**实页接钩**：`pass=true`，`forbidden=[]`、`missing_required=[]`，截图 `hooked/05-workstation-connections.png` |
| FD-013 | 恢复 `\\.`（两处），补一个带转义引号的片段，先红后绿 | `fd013/run.py` 从 `test_translations.py` 抽出 `_source_strings_from_text`，跑新用例的 3 例；再用 `diff_app.py` 比对恢复前后的全 app 取词 | 改前 3/3 红，改后 3/3 绿；全 app 取词 280＝280，差集空 |
| FD-010 | 补 `Partly Paid,部分收款,Sales Invoice` 等三行（先跑占用核查），进 `NAMED_TERMS` | 先加 `NAMED_TERMS` 三键跑 `test_named_terms`（`red.log`），再写 csv、`clear-cache` 后跑（`green.log`）；连带跑 `test_translations`（排序、覆盖清单、取词）、`test_translation_quality`（四道守卫）、`test_translation_check` | **红**：`None != '部分收款' : Partly Paid:Sales Invoice`。**绿**：`test_named_terms` 2/2、`test_translations` 19/19、`test_translation_quality` 9/9、`test_translation_check` 9/9 |
| FD-019 | 选择器排除卡片 `:not(.frappe-card)`，补评论卡片不变的反例 | Node 先红后绿；6787 上对 `MFG-WO-2026-00001`（修改记录里有 4 条含 null 的 Version）用脚本加一条正文含 `<b>null</b>` 的评论，开表单读卡片内与修改记录里的加粗文字；两轮：临时换回 `68476a3` 的 `desk_patches.js`＋`clear-cache`（old-code），放回修后版本＋`clear-cache`（patched）；读完删评论 | **Node**：红 2 条 → 绿 74/74。**old-code**：评论卡片里显示「（空）」（复现）；修改记录 null 0 条、「（空）」9 条。**patched**：评论卡片里是 `null`；修改记录 null 0 条、「（空）」9 条，原功能不变。探针评论两轮都已删，库里 0 条 |
| FD-008 | 删掉无 context 行，回落官方「费用」（首页图标按用户裁决随之显示「费用」）；先跑占用核查 | 先加 `NAMED_TERMS` 键跑 `test_named_terms`（红），删 csv 行与覆盖登记、`clear-cache` 后跑三个译名模块；容器内 zh 下取 Standard 科目表根节点 | **红**：`'报销管理' != '费用'`。**绿**：`test_named_terms` 2/2、`test_translations` 19/19（覆盖清单交集断言随之成立）、`test_translation_quality` 9/9。根节点 `['资金(资产)使用', '费用', '收入', '资金来源（负债）', '权益']`（R12 报告实取时第二项是「报销管理」） |
| FD-012 | 二选一（改守则或扩取法），写进 SB 回执；都要在取法用例里补反例 | `fd012/run.py` 抽出取法与三条取法用例（A28 新增、FD-013、原 `literal_key_forms`）在宿主跑；复跑 R12 分片 6 的 `probe_forms.py`；`fd013/diff_app.py` 比对全 app 取词 | 选 ②。改前 1 红（`red.log`），改后 3/3 绿；`probe_forms` 12/12 OK（原 5/12）；全 app 280＝280、差集空 |
| FD-017 | `QUALITY_EXCEPTIONS` 改为「键 →（守卫名, 理由）」，只豁免登记的那一道；把「译文等于源词」的判断搬进测试（第五道台湾用词表按用户裁决不加） | 先写新用例跑 `test_translation_quality`（红），再改结构与守卫跑该模块与 `test_translations`；复跑 `guard_scan.py` | **红**：4 个 error（旧结构解包失败、`find_identity` 未定义）。**绿**：`test_translation_quality` 12/12、`test_translations` 20/20。新用例实证：QE 行混进「帳戶」被 `find_traditional` 报出，同一行的英文混排仍被豁免；`Upload Photo => Upload Photo` 被 `find_identity` 报出。全 csv 五道守卫均 0 |
| FD-016 | 逐处补断言：① 同时 patch `exists`；② `assertGreaterEqual(len(terms), 29)`，路径用 `frappe.get_app_path`；③ 片 2 沙箱脚本改正式 Node 用例；④ 条目清单、中文不重名、title＝label 断言与库存类 Node 用例 | 每处补完后对被守护的代码或数据做一次变异，看新断言是否变红，再还原 | ① 去第一道守卫：1 红；还原 2/2。② po 路径改坏：`0 not >= 29`；还原 2/2。③④ 前端 5 个变异全被杀（`mutate.out`），`test_invoice_status.cjs` 12/12。④ 导航删一项：1 红；中文撞名：`['客户'] != []`；还原 5/5 |
| FD-009 | ① 基线脚本另建「源码出处」索引，占用核查不再只靠 `main.pot`；② 27 个键逐条判，意思不对的写 context 行或收回；会计判断判不了就登记 | 跑基线脚本出 `baseline.json`，数有未记出处的键；逐条读出处判语义；两条 context 行先进 `NAMED_TERMS` 跑红，再写 csv 跑绿 | ① 27 键（`hidden.txt`），含报告点名的 `Ledger`、`Item Type`、`Master`。② 判定见 `judgement.md`。**红**：`None != '账簿纸' : Ledger:Print Settings`。**绿**：`test_named_terms` 2/2、`test_translations` 20/20、`test_translation_quality` 12/12 |
| FD-024 | 演示站下次重启 `bench start` 时，日志改写到不受管路径；之后把受管那份 `git restore`；约定长跑进程的日志不写进受管目录 | 停旧进程、按新路径重起，查五个进程在、各自打开的文件里无受管路径；`git restore` 后隔 20 秒再看 `git status` | 重起后 web／socketio／worker／schedule／watch 五进程在；`bench start` 进程打开的文件里无 `/workspace/Spike` 路径；受管日志 27 行，20 秒后 `git status` 仍不显示它；守则已写 |

## 全量验证

| 门 | 执行前（R12 当场修后） | 本步修后 | 说明 |
|---|---|---|---|
| `bench --site test.localhost run-tests --app frappe_china`（先 `clear-cache`） | 270/270 | **integration 277/277 ＋ 旧式类 5/5 ＝ 282/282**，0 失败，1850 秒，`exit=0`（`Spike/P1S6R12-SB/full-regression.log`） | +12。integration 268→277（+9）：`test_dashboards` 4、`test_translations` 2（FD-012、013）、`test_translation_quality` 3（FD-017）。旧式类 2→5（+3）：全是 `test_business_flow_navigation`（用 `FrappeTestCase`），FD-016 新增 3 条 |
| `node --test frappe_china/tests/*.cjs` | 73/73 | **86/86**（`Spike/P1S6R12-SB/node-after.log`） | +13：`test_invoice_status.cjs` 12（FD-016）、`test_desk_patches.cjs` 1（FD-019） |
| 演示站译名自检 `translation_check.run` | 通过 | **通过**（`fd024/demo-translation-check.txt`） | 已 `clear-cache`；R12 FD-003 后第 4 项固定按 zh 判 |
| 演示站发出的 js 与源码 | — | `desk_patches.js`／`opening_ledger.js`／`invoice_list.js` md5 均相同（`fd024/demo-js-md5.txt`） | R12 当场修的两处与本步 FD-001、FD-019 都已上线 |
| 逐屏核脚本静态校验 | 143 屏 | **144 屏** `valid`（`SCREENS_VALIDATE_ONLY=1`） | 新屏 `05-workstation-connections` 只在测试站实跑过；演示站整轮逐屏核未跑，见「未做项」 |

## 偏离与暂停

1. **三处待裁决点开工时问了用户**（报告留给 SB 的 FD-008、FD-017、FD-009 各一处，加 FD-024 动演示站的许可），裁决见上「用户裁决」表。FD-012 报告写明「二选一、写进 SB 回执」，由本步选 ②，理由见 SB-6 行。
2. **FD-002 改了逐屏核工具**：原脚本只拦英文与繁体，「少爷」是中文、拦不住，为补报告要的那一屏，给 `Spike/P1S6R6-screen-check.js` 加了每屏可选的 `forbid`／`require`。只新屏用到，其余 143 屏判定不变。属工具扩展，不是方案外功能。
3. **FD-009 改了基线脚本的输出结构**：`official_overrides` 每条无 context 覆盖多两个字段 `source_refs`／`hidden_refs`，原有字段不变。消费它的只有本仓库的核查脚本，都只读原字段。
4. **FD-016 ③④ 的前端用例另建文件** `test_invoice_status.cjs`，不塞进已 500 多行的 `test_desk_patches.cjs`；它同时覆盖 `invoice_list.js` 与 `desk_patches.js` 的两段。
5. **执行中两次对文件做了临时改动再还原**（先红后绿与变异）：`opening_ledger.js`、`hooks.py`、`desk_patches.js`、`s6_rename_cash_flow_worksheet.py`、`test_named_terms.py`、`business_flow.json`、`zh.csv`。每次还原后都以 `git diff` 或 md5 核过与改前一致。
6. **本机端口**：`127.0.0.1:8000` 被 `UnrealEditor.exe` 占着（见 SB-11 行），演示站经局域网 IP 可访问。不属本项目，未处置。

## 新增约定

| 约定 | 类别 | 在哪个任务确立 |
|---|---|---|
| 长跑进程的日志写 `frappe-bench/logs/`，不写进受管目录（已写进 `docs/开发守则.md`） | 位置 | SB-11（FD-024） |
| `QUALITY_EXCEPTIONS` 的值是「(豁免的守卫名集合, 理由)」，只写该行实测命中的那几道（已写进 `docs/开发守则.md:103`） | 命名 | SB-9（FD-017） |
| A28 取法：`SOURCE(S)` 常量的值任何形态都取；JS `translate(`／`__(` 的第三参是 context；含 `${}` 的反引号串不算源词（已写进 `docs/开发守则.md:105`） | 命名 | SB-6（FD-012） |
| 撞名改不动 csv 时用 `override_doctype_dashboards` 换看板分组标题，按 items 认组、不按 label（已登记 `frappe_china/README.md`） | 跨层调用 | SB-2（FD-002） |
| 逐屏核每屏可写 `forbid`（不得出现的中文误译）与 `require`（必须出现的译文） | 命名 | SB-2（FD-002） |

## 未做项

| 项 | 为什么没做 |
|---|---|
| 演示站整轮逐屏核（144 屏，含新屏 `05-workstation-connections`） | SB 的判定标准是各项报告条目，FD-002 只要求「在测试站实页截图」，已做。整轮逐屏核要造数、恢复、出新基准点，属演示站复核，交 F 复核（R13）定是否要跑 |
| `Credit Note`／`Debit Note` 在日记账凭证类型里的用词 | 用户裁决登记延迟 `SH-P1S6007`，待会计确认 |
| FD-017 第五道守卫（台湾用词表） | 用户裁决不加 |

## 提交与推送

用户 2026-10-14 许可「提交并推送」：
- `frappe_china` `1d0697e` 已推送（16 个文件）。
- `docker/lock-apps.sh` 把 `docker/apps.json` 的 `frappe_china` 锁从 `68476a3` 推进到 `1d0697e`，其余六条不变。
- 主仓库随本回执一并提交推送。
- 提交前删掉的可重生成产物：`Spike/P1S6R12-SB/fd009/baseline.json`（1.2 MB），重跑 `python -I -X utf8 Spike/P1S6R4-baseline.py --out <路径>` 即得；`hidden.txt` 是它的摘录，留着。

## 状态值

**`修复已落地`**——裁为 `新Session修` 的 11 项（FD-001、002、008、009、010、012、013、016、017、019、024）全部改完，每项按报告的判定标准复验（见「复验结果」），全量 282/282、Node 86/86 无回归，演示站已上线并自检通过。按出口路由交回唤起方 F 复核（R13）。

## 复核建议

1. **修得最勉强的那项是 FD-002**：它绕开了撞名而不是消除撞名——无 context 的 `Master` 仍是「少爷」，只是工位看板不再用它。上游哪天别处再用 `_("Master")`，还会冒出来。查法：读 `frappe_china/dashboards.py` 与 `Spike/P1S6R12-SB/fd009/hidden.txt` 里 `Master` 那行（当前未记出处只有工位看板一处）。另：按 items 集合认组，上游改了 items 就不再命中，失效症状已登记在 README。
2. **连带影响**：
   - FD-012 扩了取词范围（Python dict 的键、JS 对象值、反引号串也取），清场脚本靠同一函数决定哪些行保留。对当前代码改前改后都是 280 键、差集空，但以后写 `*_SOURCES = {...}` 时，dict 的键也会被当成源词。查法：`python -I -X utf8 Spike/P1S6R12-SB/fd013/diff_app.py <旧> <新>`。
   - FD-017 的 identity 守卫也作用于 `test_translations` 里「覆盖清单 ours 过守卫」那条（`guard_problems`）。
   - FD-008 收回后，HRMS 报销单明细子表、HR 设置页签、HRMS 移动端也一起回到「费用」，不只首页图标。
3. **拿不准处**：
   - FD-009 的 22 个「同义不改」是本步逐条读出处判的（`judgement.md`），不是专家判定；`Setup` 的 25 处侧栏分节「基础设置」与 `Payment`「收付款」（hrms 报销单按钮）都算可用，但措辞可再议。
   - FD-010 三个新状态词在测试站没有现成单据，没有实页截图；渲染路径与 R5 实测过的 `Unpaid` 相同，由 Node 用例与 `NAMED_TERMS` 守。
   - FD-002 的 L3 定级沿用审核报告的读码结论，本步没另行实测「两个 app 同时注册时的叠加顺序」。
