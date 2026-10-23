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
| TS-022 换库前端 | SL-014 | — | ⬜未开始 | — | 遮罩、中转页、重来与跳幕。 |
| TS-023 彩排与整场预跑 | SL-015 | — | ⬜未开始 | — | 按方案顺序实施。 |
| TS-024 九幕演示配置与命名函数 | SL-016 | — | ⬜未开始 | — | 按方案顺序实施。 |
| TS-025 客户说明 PDF | SL-016 | — | ⬜未开始 | — | 依赖九幕彩排截图。 |
| TS-026 收尾 | SL-017 | — | ⬜未开始 | — | 回归、演示站部署、预跑与用户现场演示。 |

## 方案要求的验证

| 任务 | 验证方式（方案原文） | 怎么跑的 | 实测结果 |
|---|---|---|---|
| TS-018 | test_demo_config.py：SL-012 ① 五例；合法配置 dates 与 Part2 dates() 一致。test_progress.py：写、读、boot 字段。 | 标准 `bench --site test.localhost run-tests --module ...`；日志 `s8-ts018-{config,progress}-red.log`；全量`s8-ts019-full-debug.log`。 | 配置9/9、进度5/5，最新全量98/98。未知命名函数按总纲§5.3在前端注册表核验（TS-019）。 |
| TS-019 | s8dev测试配置十三动作彩排；③④查库，⑤刷新续跑，⑥⑦手按与截图；scene_date单测。 | `runner-selftest.cjs --rehearsal`、`runner-controls.cjs`、`runner-server-dates.py`；Node测试与测试站全量。 | 35步13动作彩排通过，每步持久化幕/步与refs一致。报表23行，过滤日期D1～D1+7，HTTP已完成且无弹窗。服务端4条日期单测通过；实机结果见下节。 |
| TS-020 | s8dev第1幕转换10次，每次新线索；Node可注入页面函数走界面、重试、接口三分支；两种会话取源码。 | `crm-selftest.cjs`、`crm-paths.cjs`、`crm-return.cjs`；`test_crm_driver.cjs`及`test_crm_inject.py`，日志见下节。 | 10/10界面转换；真实关窗/API兜底、自动回Desk并open_doc引用通过；实际zh/en源码通过。CRM Node11/11、注入Python3/3，debug全量101/101；客户应用466+6+4全部通过。 |
| TS-021 | `tests/test_registry.py`状态机；`test_dbops.py`命令与库名校验；s8dev实跑SL-014③⑥；HT-015须go。 | 四套 `bench --site test.localhost run-tests --module frappe_debug.tests.test_{dbops,registry,snapshot,switch}` 串行；定向 Ruff；`ts021-snapshot-acceptance.cjs`。 | dbops5/5、registry6/6、snapshot2/2、switch5/5；合计18/18。Ruff check/format均通过。s8dev实测原始库保护、会话拷贝切库、回切、当前快照拒清理、删除3库与清空站点私有登记。HT-015已填go。证据：`s8-ts021-native.json/png`。 |

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

## 偏离与暂停

- HT-015已由独立SA会话实测go，详见D待验表及`Spike/P1S8R6-SA/evidence/`；在途任务仍写旧库，go依赖演示期关scheduler、A6分离克隆、A7生成时不换库。SA探针站及其资源均清理；本轮s8dev临时root配置、三个快照库和登记记录均已清理。`demo.yaml`仍仅骨架，完整九幕留TS-024。
- TS-021按冻结方案克隆 detached 进程不连接 Frappe；标记路径须为绝对站点私有路径，因为其 cwd 是 bench 根目录。换库只在源库读取六列会话，再经站点数据库用户连接目标库写入；之后仅改站点配置、清目标Redis前缀并返回常量，避免请求再访问原连接。
- TS-020官方模板名`www/crm.html`在Jinja include时须补app根为`crm/www/crm.html`；中文China包装路径原样保留，未知模板零动作。实机zh/en和Python渲染均通过，这是模板解析路径校正，未改客户app。
- TS-018测试站迁移完成、退出0；旧模型清理时曾等待Docker宿主文件系统`p9_client_rpc`，保留完整日志`s8-ts018-migrate.log`，未终止进程或重建容器。
- 原生快捷键实现的`ignore_inputs: true`实际表示允许输入框内触发（`keyboard.js`），与方案按名称理解相反；运行器保留该参数并在action入口显式屏蔽输入焦点，Node分支已验证。原生实际Desk路由前缀为`/desk`，运行器将方案配置的`/app`前缀转换后传路由API。

## 新增约定

| 约定 | 类别 | 在哪个任务确立 |
|---|---|---|

## 未做项

| 项 | 为什么没做 |
|---|---|

## 状态值

执行中：TS-018～021完成，HT-015经SA填回go；续TS-022。SL-012换库后的`save_as`引用、SL-014快进计时/重来与跳幕仍待TS-022实测，尚未达到D步收口条件。

## 复核建议

提交前复核（2026-10-23）：Node 24/24、debug 全目录 Ruff check 与 format check（61文件）通过。本次是阶段性提交，18条服务端定向测试及单次原生切库不覆盖完整重来链路。已确认 `switch_to_act` 补库直接调用 `clone_detached`，未先删除已存在的 used 库，会与 `CREATE DATABASE` 冲突；连续重来验收前须修正。另须补验预留状态在切换失败后的恢复、复合操作锁范围，以及 `switch_to_db` 对 ready/used 状态的约束。正式中转页、十次计时、连续重来和跨库引用仍待 TS-022；服务端函数末尾不再访问数据库的描述不涵盖框架请求结束阶段。

配置校验的动作键、引用和日期须对照方案及需求逐项核；进度必须逐次读库，不能以缓存boot代替。CRM重点核`driver.convert`的读回重试及`run_pending`保存后导航，API失败/进度拒绝由Node覆盖；原生零金额拒绝不计成功。模板补app根路径偏离见上节。TS-021建议重点复核绝对标记路径、`reserve_snapshot`的主备选择状态以及切库后无 DB 访问；HT-015在途任务仍写旧库，go不表示任意在途业务作业可跨库。
