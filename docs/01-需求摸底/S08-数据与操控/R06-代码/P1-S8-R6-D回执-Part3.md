# P1-S8-R6 D 回执 · Part3

**日期**：2026-10-23｜**执行者**：Codex｜**打 tag**：否
**依据**：[R5 开发方案·Part3](../R05-开发方案/P1-S8-R5-C开发方案-Part3.md)及总纲。沿用 R6；Part2 TS-013～017 已完成。

## 逐项执行结果

| 任务 | 对应切片 | 落地位置（文件:行） | 结果 | 完成时间 | 说明 |
|---|---|---|---|---|---|
| TS-018 演示配置格式、校验与演示进度 | SL-012 | `demo/config.py`、`demo/progress.py`、`data/demo.yaml`、`doctype/demo_progress/`、两份测试 | ✅完成 | 2026-10-23 | 测试先红：配置9条、进度5条模块或DocType缺失。迁移退出0；最新全量98/98（273.690秒），配置9/9、进度5/5全部通过。demo.yaml仍为TS-024待补的九幕骨架。 |
| TS-019 desk 运行器 | SL-012 | `public/js/demo/runner.js`、`public/css/demo.css`、`data/demo_selftest.yaml`、`demo/scene_date.py`及测试；`Spike/P1S8R6-D/runner-*.{cjs,py}` | ✅完成 | 2026-10-23 | 13动作35步彩排完成，每步读回进度；场景日期前后端、原生映射与代建链、刷新refs、快捷键/浮窗通过。Node13/13；Python98/98。换库及跨CRM引用按方案在TS-022/020补验，SL-012相应项尚不提前关闭。 |
| TS-020 CRM 驱动与注入 | SL-013 | `demo/crm_inject.py`、`templates/crm_demo.html`、`public/js/demo/crm_driver.js`及测试；`Spike/P1S8R6-D/crm-*.cjs` | ✅完成 | 2026-10-23 | 10/10界面转换；真实API兜底、中英文源码、两路径自动回Desk与引用通过。debug101/101、china466+6+4、Node115+24、Ruff/构建/译名自检通过。 |
| TS-021 快照与换库服务端 | SL-014 | `demo/dbops.py`、`demo/registry.py`、`demo/snapshot.py`、`demo/switch.py`；四份定向测试；`Spike/P1S8R6-D/ts021-snapshot-acceptance.cjs` | ✅完成 | 2026-10-23 | HT-015 go。18/18定向测试、Ruff通过；s8dev真实克隆原始/主用/备用库，拒绝_o，抄会话切入主用、快照库禁止清理、切回基库后删除3库且登记表清空。 |
| TS-022 换库前端 | SL-014 | `demo/{registry,snapshot,switch,progress}.py`、`public/js/demo/runner.js`、`public/demo/transit.html`、`public/css/demo.css`、`frappe_debug/page/demo_rehearsal/`及测试 | ✅完成 | 2026-10-23 | 十次快进均≤10秒；两次重来数据干净，跨库引用可打开。中转页返回基库、12库清理与原进度/条数恢复通过。两个收尾按钮已落地并在s8dev原生页面验证。debug124/124、china466+6+4、Node32+115、两app Ruff/构建与两站译名自检通过。 |
| TS-023 彩排与整场预跑 | SL-015 | [A已批准补充](P1-S8-R6-D彩排方案补充建议.md)、`demo/{workspace,operation}.py`、`scenario/runner.py`、`public/js/demo/rehearsal.js`、`frappe_debug/page/demo_rehearsal/`及测试 | 🔄实施中 | — | 编排、工作库登记/恢复、复合操作锁、刷新续跑及失败停止均已实现；Node36/36、Python定向45/45。s8dev原生工作库创建、经中转切入/回基库、进度与条数保持、删除工作库通过。真实九幕SL-015/016按批准方案留待TS-024后联合验收。 |
| TS-024 九幕演示配置与命名函数 | SL-016 | `data/demo.yaml`、`demo/functions.py`、`demo/config.py`、`public/js/demo/functions.js`、`public/js/demo/{runner,rehearsal}.js`、测试 | 🔄实施中 | 2026-10-23 | 九幕配置初稿仍未验收。本轮先红后绿修复CRM跨页交接，CRM/运行器/彩排与策略区间Node41/41；修复D2订单日期变量与订单建议引用错配，服务端测试2/2；工单提交改为场景日并由原生钩子生成工序卡；策略比较期改按三规则启用边界。`test_demo_config`11/11；三个JS语法、Ruff check及build通过。Ruff format检查覆盖4个Python文件时仅既存修改的`tests/test_demo_config.py`未通过，其它3文件格式通过；未做非必要全文件重排。尚未完成真实报工时间/数量、末道数量、报表日期、交互细节和九幕原生彩排，详见状态值。 |
| TS-025 客户说明 PDF | SL-016 | — | ⬜未开始 | — | 依赖九幕彩排截图。 |
| TS-026 收尾 | SL-017 | — | ⬜未开始 | — | 回归、演示站部署、预跑与用户现场演示。 |

## 方案要求的验证

| 任务 | 验证方式（方案原文） | 怎么跑的 | 实测结果 |
|---|---|---|---|
| TS-018 | test_demo_config.py：SL-012 ① 五例；合法配置 dates 与 Part2 dates() 一致。test_progress.py：写、读、boot 字段。 | 标准 `bench --site test.localhost run-tests --module ...`；日志 `s8-ts018-{config,progress}-red.log`；全量`s8-ts019-full-debug.log`。 | 配置9/9、进度5/5，最新全量98/98。未知命名函数按总纲§5.3在前端注册表核验（TS-019）。 |
| TS-019 | s8dev测试配置十三动作彩排；③④查库，⑤刷新续跑，⑥⑦手按与截图；scene_date单测。 | `runner-selftest.cjs --rehearsal`、`runner-controls.cjs`、`runner-server-dates.py`；Node测试与测试站全量。 | 35步13动作彩排通过，每步持久化幕/步与refs一致。报表23行，过滤日期D1～D1+7，HTTP已完成且无弹窗。服务端4条日期单测通过；实机结果见下节。 |
| TS-020 | s8dev第1幕转换10次，每次新线索；Node可注入页面函数走界面、重试、接口三分支；两种会话取源码。 | `crm-selftest.cjs`、`crm-paths.cjs`、`crm-return.cjs`；`test_crm_driver.cjs`及`test_crm_inject.py`，日志见下节。 | 10/10界面转换；真实关窗/API兜底、自动回Desk并open_doc引用通过；实际zh/en源码通过。CRM Node11/11、注入Python3/3，debug全量101/101；客户应用466+6+4全部通过。 |
| TS-021 | `tests/test_registry.py`状态机；`test_dbops.py`命令与库名校验；s8dev实跑SL-014③⑥；HT-015须go。 | 四套 `bench --site test.localhost run-tests --module frappe_debug.tests.test_{dbops,registry,snapshot,switch}` 串行；定向 Ruff；`ts021-snapshot-acceptance.cjs`。 | dbops5/5、registry6/6、snapshot2/2、switch5/5；合计18/18。Ruff check/format均通过。s8dev实测原始库保护、会话拷贝切库、回切、当前快照拒清理、删除3库与清空站点私有登记。HT-015已填go。证据：`s8-ts021-native.json/png`。 |
| TS-022 | s8dev：SL-014①②④⑤计时与断言；SL-012⑤换库后save_as仍可用；彩排页两个结束按钮。 | `switch-timing.cjs`严格就绪计时，`ts022-cleanup.cjs`、`ts022-verify-cleanup.py`、`ts022-page.cjs`；Node/服务端测试与切片全量回归。 | 十次快进3.879～4.703秒，目标进度与Administrator身份通过；重来两次单据条数恢复一致。引用打开原生Sales Order；返回基库且12快照库全删除，临时root撤回。页面按钮原生验证通过。全量回归结果见下节。 |
| TS-023 | 编排/状态/失败停止与恢复边界；A批准补充的工作库生命周期、受控切换/清理。完整SL-015①②③与SL-016①～③均待TS-024真实九幕后联合验收。 | Node四套前端测试；`test_workspace`、`test_registry`、`test_dbops`、`test_snapshot`、`test_switch`、`test_scenario_runner`串行；Ruff、JS语法、`bench build --app frappe_debug`；`ts023-workspace-native.cjs`。 | Node36/36、Python45/45；Ruff check及format通过（12文件），JS语法通过，构建退出0。s8dev原生创建并等待工作库ready，经真实中转页切换到工作库及返回基库，Administrator会话、演示进度和ToDo/Sales Order/Purchase Order/CRM Lead数量保持；清理1库、登记为空，information_schema确认工作库不存在，临时root配置已撤回。证据见下节。 |
| TS-024 | SL-016①～③：九幕配置、命名函数、讲解词、原生彩排。 | `test_demo_runner.cjs`、`test_rehearsal.cjs`、`test_crm_driver.cjs`、`test_demo_functions.cjs`；`test_demo_config`和`test_demo_functions`定向测试（`test.localhost`）；JS语法、增量Ruff、构建。 | handoff红测3例失败后绿；Node41/41。Python配置11/11、服务端函数2/2。三个JS `node --check`通过，Ruff check通过；Ruff format覆盖四个Python文件时三份通过，既存修改的`test_demo_config.py`尚有原格式差异；`bench build --app frappe_debug`退出0。没有浏览器业务原生验收；SL-016①～③与SL-015仍待真实九幕完成后联合执行。 |

### TS-019 实机证据（s8dev.localhost，6787）

- `s8-ts019-rehearsal.log`：一次`demo.next()`连续完成35步13动作，退出0。原生保存并查库：销售订单`SAL-ORD-2026-00343`（已提交）、采购订单`PUR-ORD-2026-00313`（已提交）、映射采购入库`MAT-PRE-2026-00309`（草稿）、付款单`ACC-PAY-2026-00631`（草稿），业务日期均2026-01-07；入库set_posting_time=1。付款单与销售订单原生无该字段，按方案“字段存在则置1”，不虚造字段。无OB-075确认框。`s8-ts019-{native-actions,saved-docs,report}.json`、`s8-ts019-native-actions.png`。
- `runner-server-dates.py`退出0：服务端映射入库`MAT-PRE-2026-00308`、物料需求`MAT-MR-2026-00310`→采购订单`PUR-ORD-2026-00312`、生产计划`MFG-PP-2026-00333`→工单`MFG-WO-2026-00333`→3张工序卡均带2026-01-07；工单保留08:30时间，未写生成器标志。证据`s8-ts019-server-dates.{json,log}`。
- `runner-controls.cjs`退出0：刷新后boot refs与步号保留；引用销售订单可打开；输入焦点时→不动；一次→连续执行2步后停于presenter，再按执行第3步；Alt+H两次显隐；Alt+R及Alt+1～9均到预期回调（换库本身留TS-022）。12键各一个handler，Sales Order页可见Alt字母无h/r；原生Alt组的is_taken亦会避开全局快捷键。截图`s8-ts019-controls.png`已目视复核，浮窗不挡主按钮。
- 新发现先红后绿：分组按钮用原生data-label；页面路由先拆查询参数再set_route；映射表单等待异步onload结束后推进，避免早读日期。红日志`s8-ts019-{group,route,render}-red.log`，最终Node13/13。
- 验收fixture只写s8dev命名单据，不改原生校验。挑选prevent_pos=0且warn_pos=0的已有供应商；早期因评分禁止下单及重复客户PO号而失败的记录留日志，不算运行器通过证据。

### TS-020 实机证据（s8dev.localhost，6787）

- 配置与测试先红：`s8-ts020-inject-red.log`、`s8-ts020-driver-red.log`；实现后Python注入3条及Node界面/重填/API/失败/未激活5条通过。后续读回空金额与非有限值两例先红（`s8-ts020-readback-red.log`）后绿；API导航顺序先红（`s8-ts020-navigation-red.log`）后绿。最终CRM11条＋运行器13条＝24/24。
- `s8-ts020-conversions.{log,json}`：10条新线索`CRM-LEAD-2026-00336`～`00345`分别转换为同序商机，10/10走ui；金额1000～1009、关闭日2026-01-14，查库核对线索converted=1，回Desk后步号与商机ref已保存，原有销售订单ref保留。
- 原彩排脚本曾以`?lang=en`误判语言，两页均实际中文，不作英文通过证据；已改为`?_lang=`并核html lang。`crm-paths.cjs`最终实跑`s8-ts020-paths-final.log`：zh/en各HTTP200、脚本各一次，只有zh保留China注入。真实弹窗故意两次读回不符后关闭，原生转换API创建`CRM-DEAL-2026-00348`（线索00350），金额2077、日期2026-01-14；`s8-ts020-api.{json,png}`。
- `s8-ts020-return-valid.log`：合法金额2088经ui转换为`CRM-DEAL-2026-00347`，自动回Desk，Single进度step=1且保留既有refs；运行器open_doc经已保存CRM引用打开商机，金额日期读回一致。`s8-ts020-return.{json,png}`，截图已目视复核，浮窗不挡主按钮。
- 零金额探索失败保留`s8-ts020-return.log`、`s8-ts020-return-retry.log`及`return-failure.json/png`：CRM原生接口417并显示预期商机价值必填，驱动等商机路由后定位超时，进度不前移；该次未走API兜底，也不计为成功。Node中的零只验证显示值匹配，不表示原生CRM接受零金额。
- API兜底成功后先持久化进度、写结果、清pending，再跳转；缺Vue router时整页导航亦在持久化后，防止页面卸载重跑。进度保存拒绝保留pending、显示幕/步、不回Desk，Node分支通过。Desk命名函数`crm_convert_lead`仍按冻结方案留TS-024，不提前计完成。

### TS-021 实机证据（s8dev.localhost，6787）

- 首次 detached 克隆探针发现标记路径相对 bench 根目录，克隆完成后无法写 `.ok/.fail`；修为绝对站点私有路径并加回归测试。首次探针的三库由已登记 `drop_snapshots` 清理，随后重新克隆三库并全部进入 `ready`。
- `ts021-snapshot-acceptance.cjs` 先断言 `frappe.boot.sitename === s8dev.localhost`、当前用户 Administrator、DB 为原基库；拒绝切换 `_o`；切入 `_m` 后 `switch_status` 读回 Administrator；在快照库调用清理被拒；切回基库后成功删除3库，登记表变为 `{"base_db":null,"acts":{}}`。脚本退出0；截图 `s8-ts021-native.png` 已复核，停在业务流程页且演示浮窗无覆盖冲突。
- 实测前临时设置 s8dev `root_password`，验后通过 `bench set-config root_password None` 删除；站点配置恢复未配置状态。当前 s8dev DB 指针保持原基库，快照库与登记记录均已清理。本段原生验收未访问 `test.localhost` 或 `erx.localhost`；定向自动测试只运行在 `test.localhost`。

## 全量验证

### TS-022 实机证据（s8dev.localhost，6787）

- `s8-ts022-backend-red.log`、`s8-ts022-session-order-red.log`保留补库、预留恢复及回调次序的红灯；`s8-ts022-backend-final.log`为switch模块9/9（2.427秒）。补库先删used库再克隆，框架session.update结束后才关闭旧连接并补库；切换失败调用预留恢复。
- `s8-ts022-timing.log`与`s8-ts022-native.json`仅作首轮诊断：只等配置加载即计时，route=null，不用于≤10秒验收。早期报表500保留日志，不算通过；严格重跑的各次切换均检查API响应无HTTP≥400。
- `switch-timing.cjs`严格重跑用真实→键，等待目标路由、列表data或报表控件及结果/提示、ajax_count=0且无可见弹窗。报表入口骨架允许显示“请设置过滤条件”；此处证明目标起始页可用，完整业务筛选与出数仍由TS-024验收，不混记。每次同时核目标boot和直接读库进度act/step=0、refs及Administrator身份。中转页首个switch_status请求身份为Administrator且db为目标，未经登录页。

| 次数 | 第5→6幕（秒） | 第7→8幕（秒） | 结果 |
|---|---:|---:|---|
| 1 | 3.879 | 4.703 | 通过 |
| 2 | 3.901 | 4.103 | 通过 |
| 3 | 4.375 | 4.226 | 通过 |
| 4 | 4.242 | 4.287 | 通过 |
| 5 | 4.054 | 4.433 | 通过 |

- 计时证据`s8-ts022-timing-strict.log`、`s8-ts022-native-strict.json/png`。准备源列表的跳幕8.944～13.842秒另记，不声称所有跳幕均≤10秒。第7幕首次跳入主用库，回跳选择已补好的干净副本，数据库名见逐次JSON。
- 换库后以已保存refs打开真实Sales Order `SAL-ORD-2026-00343`，完成SL-012⑤跨库引用补验。
- 第8幕连续两次重来前各新建1条ToDo，重来后逐类型核对原快照：ToDo=0、Sales Order=343、Purchase Order=313、CRM Lead=351。第一次等待干净副本137.004秒，切换4.400秒；随后补库等待73.562秒。第二次前等0.026秒，切换13.802秒，随后补库等待75.553秒。两次均干净；重来不套用快进≤10秒判据。
- 清理期间detached克隆可能重建目标库，新增拒绝清理cloning快照的保护；`s8-ts022-cleanup-red.log`先红，`s8-ts022-cleanup-green.log` snapshot3/3（0.177秒）转绿。
- 验后确认无cloning，再经真实中转页返回原基库`_784d783aa8860455`。清理12库请求约62秒超过CDP60秒上限，客户端超时但服务端最终200；没有盲目重发。`ts022-verify-cleanup.py`另查information_schema证明12库全不存在、登记为空、基库进度和四类条数均与fixture一致，正向证据`s8-ts022-cleanup.json`。临时root配置已撤回并查配置确认；未写erx站。
- 补齐`demo-rehearsal`页两个结束按钮（仅System Manager）：返回调用运行器中转路径，清理调用受保护服务并显示数量/错误。页面3条测试先红后绿；`ts022-page.cjs`原生核页面注册/角色、清理0库回执、返回按钮委托，截图`s8-ts022-page.png`。实际跨库返回由前述cleanup脚本验证。此页尚无TS-023预跑功能。
- 最新debug全量`s8-sl014-full-debug.log`124/124（353.653秒）OK；随后串行执行china全量`s8-sl014-full-china.log`：466/466（2547.521秒）＋旧类6/6（0.281秒）＋未分类4/4（0.005秒），三个分类均OK，容器退出0；含翻译测试20条和质量测试13条。Node debug32/32、china115/115；两app Ruff check与format check通过，分别63/185文件；最终构建退出0。test及s8dev两站译名自检均通过，日志`s8-sl014-translation-{test,s8dev}.log`；test检查在全量结束后串行执行。
- TS-023最新代码增量回归按序执行：`s8-ts023-test_{workspace,registry,dbops,snapshot,switch,scenario_runner}-final.log`分别14/14、6/6、5/5、4/4、9/9、7/7，合计45/45；四套Node为36/36（含生成段后刷新不重演前序幕），Ruff check/format 12文件通过，两个JS运行器语法检查通过，`bench build --app frappe_debug`退出0。原生正向证据为`s8-ts023-workspace-native.json/png`；独立数据库查询确认`_784d783aa8860455_work`不存在，站点登记为空，root配置未设置。TS-023整场九幕联合验收尚未执行。

### TS-023 工作库生命周期实机验证（s8dev.localhost，6787）

- `ts023-workspace-native.cjs`开场断言站点名、Administrator、登记为空；记录基库`_784d783aa8860455`的原进度（act=1、step=35及4项refs）与四类单据数量（ToDo=0、Sales Order=343、Purchase Order=313、CRM Lead=351）。
- `prepare_work`登记并克隆`_784d783aa8860455_work`，轮询至`work_state=ready`。通过实际中转页切入工作库，Administrator会话、进度与四类数量均与基库一致；再次经中转页回基库，原进度保持。
- `drop_snapshots`返回`dropped=1`，登记表回到`{"base_db":null,"acts":{}}`；之后从MariaDB `information_schema.SCHEMATA`核对工作库不存在。临时`root_password`在测试前从本机配置载入，测试结束后用`bench set-config ... None`撤回并验证未配置。演练没有启动生成器，也未连接`erx.localhost`或`test.localhost`。

| 门 | 结果 |
|---|---|
| 执行前基线 | Part2 回执：frappe_debug 80/80、策略报表 7/7；本次不重复已完成全年场景。 |
| TS-018首轮全量 | 94条，93通过、1失败（310.724秒）；新增配置9/9、进度5/5全过。失败为旧日期测试硬编码2026-10-22作为未来/今天，2026-10-23失效。已把测试输入改为当前日次日，生产逻辑未改；待复跑。 |
| TS-018/019 Python复跑 | `s8-ts019-full-debug.log`：98/98（273.690秒），OK；日期旧测试及场景日期4/4均通过。 |
| SL-012 frappe_china全量 | `s8-sl012-full-china.log`：466/466（2205.821秒）＋旧类6/6＋未分类4/4，容器退出0；含译名20条与质量13条。Part1基线465条，本轮含Part2新增策略回归增加1条，无删减。 |
| SL-012 Node / Ruff | china115/115、debug13/13；两app Ruff check通过，format check分别185/51文件通过。 |
| SL-012 译名自检 | test.localhost及s8dev.localhost的`translation_check.run`均输出“译名自检通过”。未操作erx.localhost。 |
| SL-013 debug Python | `s8-ts020-full-debug.log`：101/101（269.086秒），OK。 |
| SL-013 Node / Ruff | china115/115、debug24/24；两app Ruff check及format check通过，共238文件（china185＋debug53）。`frappe_china`工作树无改动。 |
| SL-013 客户应用全量 | `s8-sl013-full-china-serial.log`：466/466（2225.724秒）＋6/6＋4/4，三个分类均OK。宿主PowerShell外层退出1，日志有stderr空行的NativeCommandError包装；无失败断言。首次误并行启动的china套件已终止，不计通过；本次在debug完成后串行执行。 |
| SL-013 构建 / 译名自检 | `s8-ts020-build-final.log`构建退出0；test及s8dev两站均“译名自检通过”（`s8-sl013-translation-{test,s8dev}.log`）。 |
| TS-021 定向全量 | `s8-ts021-test_dbops-final4.log`、`test_registry-final4.log`、`test_snapshot-final4.log`、`test_switch-final4.log`，按序执行；Ruff针对8个新增/改动文件。 | 四模块18/18；Ruff check通过、format check 8文件通过。 |
| SL-014 最终回归 | debug124/124、china466+6+4全部通过；Node32+115全过，两app Ruff check/format通过，共248文件；构建退出0；test/s8dev译名自检通过。较SL-013 debug101增至124、Node24增至32，china测试无删减；frappe_china工作树无改动。 |

## 偏离与暂停

- TS-023开工前发现的工作库、原始快照保护与续跑、验收依赖冲突，用户已明确裁决A；以[批准补充](P1-S8-R6-D彩排方案补充建议.md)作为R5 Part3的实施补充，不改冻结文件。先实现编排与恢复，再与TS-024联合验真实九幕；没有提交授权。
- TS-022中转请求不把csrf放URL，按sessionStorage读取；路由引用在目标库读取进度后展开，防止带入来源库的旧单号。补库延迟到框架会话写回之后，关闭旧连接并刷新配置后才删除被消费的副本；这是请求收尾生命周期的实现补齐。
- HT-015已由独立SA会话实测go，详见D待验表及`Spike/P1S8R6-SA/evidence/`；在途任务仍写旧库，go依赖演示期关scheduler、A6分离克隆、A7生成时不换库。SA探针站及其资源均清理；TS-023原生验收后s8dev临时root配置、工作库和登记记录均已清理。`demo.yaml`九幕初稿进行中，完整业务验证留TS-024。
- TS-021按冻结方案克隆 detached 进程不连接 Frappe；标记路径须为绝对站点私有路径，因为其 cwd 是 bench 根目录。换库只在源库读取六列会话，再经站点数据库用户连接目标库写入；之后仅改站点配置、清目标Redis前缀并返回常量，避免请求再访问原连接。
- TS-020官方模板名`www/crm.html`在Jinja include时须补app根为`crm/www/crm.html`；中文China包装路径原样保留，未知模板零动作。实机zh/en和Python渲染均通过，这是模板解析路径校正，未改客户app。
- TS-018测试站迁移完成、退出0；旧模型清理时曾等待Docker宿主文件系统`p9_client_rpc`，保留完整日志`s8-ts018-migrate.log`，未终止进程或重建容器。
- 原生快捷键实现的`ignore_inputs: true`实际表示允许输入框内触发（`keyboard.js`），与方案按名称理解相反；运行器保留该参数并在action入口显式屏蔽输入焦点，Node分支已验证。原生实际Desk路由前缀为`/desk`，运行器将方案配置的`/app`前缀转换后传路由API。

## 新增约定

| 约定 | 类别 | 在哪个任务确立 |
|---|---|---|
| 本任务未新增工具管不了的长效工程约定；中转页与补库次序属于当前演示实现细节。 | — | TS-022 |

## 未做项

| 项 | 为什么没做 |
|---|---|
| TS-023整场联合验收、TS-024余下业务修复及原生验收、TS-025～026 | 按A批准范围，SL-015/016待真实九幕可跑后联合执行；PDF、收尾和部署尚未开始。TS-024配置初稿仍有未解决/未验证的业务细节，详见下方状态值，不声称九幕通过。 |

## 状态值

执行中：TS-018～022完成，HT-015经SA填回go。SL-012跨库引用已补验，SL-014实测与全量回归通过。TS-023代码及增量验证完成，工作库生命周期原生验证通过；按A批准范围，完整九幕SL-015/016联合验收待TS-024完成后执行。TS-024进行中：九幕配置初稿在`frappe_debug/data/demo.yaml`；本轮先红后绿修复CRM跳转handoff，相关Node40/40通过、三个JS语法检查通过；修复了D2订单查询日期变量、订单建议引用键，工单按场景日提交并使用原生工序卡生成。仍未解决/未验证：SlotAllocator场景日期排工与BOM工时、工序顺序/数量/员工、末道良品数、报工确认弹窗实取、推荐BOM确认与计划数量呈现、三段策略真实比较区间、各报表筛选/先填后等、D2付款方式、末幕有效采购价/供应商评分/采纳数量、完整九幕原生彩排与27快照。TS-023 SL-015/016未验收，TS-024～026未完成；D步尚不能标记“代码已落地”。

## 复核建议

换库最需复核的是`demo/switch.py::_schedule_replenish`：它利用after_response队列追加回调，等框架session.update之后才关闭旧连接、刷新配置并补库；请对照当前Frappe请求收尾顺序和`s8-ts022-session-order-red.log`复核，上游升级后须重验。`snapshot.replenish`已先删used库再克隆，连续两次真实重来和数据条数验证通过；原先“未删旧库”的缺口已修。

失败路径比主路径薄：`test_failed_switch_restores_reserved_snapshot_states`验证调用预留恢复，尚未做真实会话复制失败后的持久登记恢复及配置更新后异常注入。`demo/operation.py`以站点路径上的FileLock串行准备、恢复、切换、清理及生成任务登记；请对照`workspace.restore_work`的分步删库/克隆失败状态复核可重试性，当前该恢复路径主要由自动测试覆盖，本轮原生实测只覆盖工作库创建、切入、返回和清理。`switch_to_db`只允许基库或ready工作库，幕主/备副本须经`switch_to_act`消费。HT-015的go依赖关scheduler、生成期间不换库，在途任务仍写旧库，不能解读为任意后台作业可跨库。

十次≤10秒证据只覆盖第5→6、第7→8幕快进，起始报表可显示“请设置过滤条件”；不代表TS-024九幕业务已通过，也不代表所有跳幕/重来≤10秒。补库实际有137秒等待。彩排页现含整场开始、当前幕续跑、返回演示前及清理快照库入口；实际九幕业务仍待TS-024，之后联合验SL-015/016。

TS-024当前增量验证：先红日志`s8-ts024-handoff-red.log`复现交接时提前推进、现场继续执行和彩排提前完成；实现后`s8-ts024-handoff-green.log`CRM/运行器/彩排共40/40。最后一次JS改动后复跑`s8-ts024-runner-final.log`仍40/40，`functions.js`、`runner.js`、`rehearsal.js`的`node --check`通过。`test.localhost`定向`test_demo_config` 11/11通过；`test_demo_functions`首次执行中测试断言引用错误（保留`s8-ts024-functions-final.log`），修正测试后2/2通过（`s8-ts024-functions-redo.log`）。Ruff check/format覆盖`functions.py`与新增测试均通过；`bench build --app frappe_debug`退出0（`s8-ts024-build-final.log`）。本轮未执行浏览器业务写入、场景生成、切库或部署。
