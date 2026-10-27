# F 复核报告 Part1（对象：R8 F 审核当场修 12 项 / 依据：R8 F 审核报告＋Part1～3 原证据＋R05 方案＋开发守则）

**轮次**：P1-S8-R11（F 复核）｜**片**：1｜**日期**：2026-10-27｜**执行者**：Claude（Opus 5.5），独立子 Agent，未参与 R8 当场修、SB 与 R10｜**打tag**：否

**代码基线**：`frappe_debug` HEAD `3894c5a`（当场修 `e1fdc14`，其后 `dfc5ffb`、`1f9ba1c`、`3894c5a`）；`frappe_china` HEAD `f0ac818`（当场修 `a8b495f`，其后 `751ae3b`、`ffadacf`、`f0ac818`）；ERPNext fork `a729571`；与 `docker/apps.json:45,51,11` 锁定一致。

**范围**：FD-009、010、014、015、016、017、018、019、022、023、024、028。

## 覆盖自证

**实际查了的**：

- 依据：F 审核 Spec、`bricks/audit.md`、R8 收口报告全文（问题清单、当场修清单、修后回归）、Part2 的 P2-06／07、Part3 的 P3-02／05／08／09／10、Part1 的 P1-04／05／06／08 原条目、SB 修复回执全文（看后续提交改了什么）、`docs/开发守则.md` 侵入度表、源码改动两条义务、覆盖登记节。
- 代码：`git show e1fdc14`、`git show a8b495f` 全部 diff 逐行读；`git diff e1fdc14..HEAD` 和 `git diff a8b495f..HEAD` 按本片涉及的每个文件看（逐文件列提交号，见第 4 节）；HEAD 上通读了 `demo/snapshot.py`、`switch.py`、`operation.py`、`dbops.py`、`progress.py`、`functions.py`（1～300 行）、`public/demo/transit.html`、`demo_rehearsal.js`、`runner.js` 的换库、开播、覆盖段，`README.md` 1～85 行，`scenario/params.py` 的复核起点段，`runner.py` 的计划检查与生成入口段，`quality.py` 的预览标记、指纹、导出段。
- 上游：frappe `utils/response.py:39-64`（`exc_type` 回传）、`app.py:386-455`、`utils/error.py:44-100`（`log_error` 签名与换位逻辑）、`installer.py:357`；ERPNext `accounts_controller.py:1053-1100`、`get_item_details.py:1115-1146,1459-1502,1787-1817`、`setup/utils.py:62-150`（汇率取数），`sales_order_list.js:27`。
- 实测（全部只读）：
  - `erx.localhost` 只读 SQL：基库与工作库 `_2bd5b09209543e8e_work` 的 `tabCompany` 复核起点、`Replenishment Suggestion` 按规则与星期分布、`tabDocField` 计件单价精度、计件明细数值分布；`information_schema` 库名列表。没改任何数据或配置，没切库。
  - `test.localhost` 只读 SQL：`_Test Company` 币种、`Price List`、`tabDefaultValue`、`Currency Exchange`、汇率设置、汇率相关 `Error Log`、`Patch Log`。
  - 各站 `site_config.json` 只查有无 `root_password` 键（不回显值）；`docker/backups/` 下含该键的文件计数。
  - Redis 缓存里汇率键的只读 `scan`／`ttl`／`get`。
  - Node 纯单测：`node --test frappe_debug/tests/test_transit.cjs`，宿主 Node v24.13.1，**7/7 通过**（含 FD-014 新增那条）。
  - 读了主会话正在跑的 R11 门禁日志（`frappe-bench/logs/s8-r11f-*`，非本片所跑），以及 R8 F、R8 F 修后、R8 SB 三轮门禁日志，用来对比 `test_strategy_comparison` 的用时。

**只读码、没实测的**：

- FD-009、010、015、019、024 的 Python 单测没跑（约束：不在 `test.localhost` 跑 bench），用例是否存在、断言写了什么由读码核实；有没有通过只采信主会话 R11 门禁日志（`s8-r11f-full-frappe_debug.log:56-58,112,246,253` 显示相关用例 ✔）。
- FD-014 没做端到端（真实浏览器下补库持锁时按 →）复现，只有 Node 单测和读码。
- FD-016 没在浏览器里看计件汇总单的显示效果，只核了元数据精度和库里的数值。
- FD-028 没跑用例；对它的「仍会访问外网」判断来自读上游代码、原失败堆栈和三轮用时对比，没抓包。

**跳过的**：

- `docker/` 主仓库层的 FD-024 备份目录只数了文件，没打开看内容。
- SB 回执里记的观察项「回基库那一刻 `snapshot_status` 偶发 500（FileNotFoundError）」本片没查原因：它落在 FD-013 范围；本片只确认 FD-015 给该接口加的 `_authorized()` 不读文件（见第 6 节）。

## 逐项三层核查

| FD | 当场修清单所写位置 | 代码在（含当前 HEAD 行号） | 真被调用 | 原问题消失 | 证据 | 结论 |
|---|---|---|---|---|---|---|
| FD-009 | `params.py:25`、`:410`；`masters.py:610`；`test_params.py` 新用例 | ✅ `params.py:25`（`review_start` 字段）、`:389-395`（`next_workday`）、`:412-415`（取启用日当天或之后第一个工作日；超出场景报参数错）、`:493`（传入 `Scenario`）；`masters.py:618`（`cn_review_start_date = sc.review_start or sc.S`，行号因 `3894c5a` 在上方插入 `customer_names` 下移 8 行，内容未变）；`test_params.py:238-244` | ✅ `build_masters` 是生成器建主数据的唯一入口，`cn_review_start_date` 全仓只在 `masters.py:618` 写；`frappe_china` `replenishment/params.py:66` 读它，`rules.py:151-153` 按它判盘点日 | ✅ erx 工作库实测：复核起点 `2026-06-01`（Monday），`Periodic Review` 建议 17 条，全部落在 Monday，区间 06-01～10-19；按订单 155 条、EOQ 30 条，三规则各段都有建议。本轮 S 不是周日，所以周日场景只靠单测覆盖（E＝2026-06-15 → S＝2025-06-01 周日 → 起点移到 02-02 周一）。`next_workday` 与生成器 `day.py:748` `_is_workday` 用的是同一份 `calendar` 配置（`masters.py:145` 建假日表），两边口径一致 | `SELECT … FROM _2bd5b09209543e8e_work.tabCompany` → `2026-06-01 Monday 14`；`… GROUP BY DAYNAME` → `Monday 17` | ✅ |
| FD-010 | `runner.py:68`；`workspace.py:44,60`；`README.md:47`；`test_workspace.py` 两条 | ✅ `runner.py:68-86` `assert_quality_plan_ready`（核版本＋场景指纹，不符就拒绝并指向 README）；`workspace.py:44,60-66`；`README.md:47-56`；`test_workspace.py:84,111` | ✅ `prepare_work` 由彩排页「开始整场预跑」调用（`public/js/demo/rehearsal.js:56`），在登记工作库、克隆之前检查。`3894c5a` 加了第二个跳过条件 `is_quality_preview_site()`（`workspace.py:60-62`），只在非 erx／s8dev、且站点标了 `frappe_debug_quality_preview` 时成立（`quality.py:22-28`）；erx 上不成立，检查照常生效 | ✅（以 HEAD 为准）erx 的 `quality-plan.json` 指纹是 `295e77a3…`，SB 记录整场预跑以 E＝2026-10-27 一次通过，说明计划和本次 E 对得上。**但 `e1fdc14` 写进 README 的重做步骤本身是错的**（只跑生成器、不演各幕，单据号对不上），SB 实测在第 2 段首日失败后，已在 `3894c5a` 改成「标记预览站上跑带各幕的整场彩排」（`README.md:51-56`）。当场修那一版的 README 没能消除原问题，是后续提交补好的。另有两处残留，见 P1-03、P1-04 | `git diff e1fdc14..HEAD -- README.md`；SB 回执 :62-68 | ✅（当场修版 ⚠️，HEAD 版 ✅） |
| FD-014 | `operation.py:11`；`transit.html:63`；`test_transit.cjs` 一条 | ✅ `operation.py:11-12`（`DemoOperationBusy(ValidationError)`）、`:23`（锁被占时抛它）；`transit.html:55-59`（按 `exc_type` 打 `busy` 标记）、`:63-70`（`requestWhenFree`：每 2 秒重试，最长 120 秒）、`:96`（两条换库请求都走它）；`test_transit.cjs` 末条。这几个文件 `e1fdc14` 之后没再改 | ✅ 换库全部经中转页：`runner.js` `switch_act`／`transit_to_db`／`return_to_base`／`start_show` 都跳 `transit.html`。frappe v1 API 出错时回 `exc_type = 类名`（`utils/response.py:53`），ValidationError 子类回 417，`response.ok` 为假，能进 `busy` 分支 | ✅ 锁被占时，中转页保持转场文字、静默重试，不调 `fail()`。后续 `3894c5a` 让演示中途换库不再补库（`switch.py:106` `claim=False`），抢锁的来源已从根上大幅缩小；剩下的「回基库后补库」与「点开始演示」相撞、「某幕两份都用完时自补本幕」两条路径由本修复兜住。补库每份只在 `drop_db`＋启动后台克隆时持锁（`snapshot.py:60-72`），窗口很短，120 秒上限够用。未端到端复现 | `node --test test_transit.cjs` 7/7；读码 | ✅（只有单测＋读码） |
| FD-015 | `rehearsal.py:14-31`；`snapshot.py:55`；`functions.py` 三方法 POST；`test_demo_auth.py` | ⚠️→✅ `snapshot.py:54-57`（`_authorized()`）；`functions.py:38,259,279`（`methods=["POST"]`）。**`rehearsal.py` 的两个方法已被 `3894c5a` 删掉**（FD-020 挪进生成器），`test_demo_auth.py` 相应去掉两方法 | ✅ 两个越权方法删掉后，原来的功能挪到 `scenario/targets.py:15` `prepare_production_masters`，不带 `@frappe.whitelist`，只由 `prepare_act1`（`targets.py:37-39`）调用，后者只由生成器 `monthly.py:276` 调用；生成器入口 `runner.py:128-133` `start_generate` 校验 Administrator 且只收 POST。`demo.yaml`、`functions.js` 里已经没有对两方法的调用（全仓 grep 只剩 `test_demo_config.py:218` 的「不得出现」断言） | ✅ 原问题（任何登录用户都能改工位费率、换默认 BOM、改公司科目）随删除消失，没有以别的形式出现：替代代码没有对外暴露。`snapshot_status` 已鉴权。三个写库命名函数只收 POST，运行器经 `frappe.call`（默认 POST，`runner.js:122-124`）调用，不受影响。HEAD 上全部 25 个白名单方法逐个核了鉴权（grep 结果见第 5 节 P1-05）。残留：`snapshot_status` 仍接受 GET，且每次调用会改写登记表文件，见 P1-05 | `grep -rn -A3 "@frappe.whitelist" frappe_debug` | ✅ |
| FD-016 | `piece_rate_summary_item.json`（`precision: 4`、`modified`） | ✅ `piece_rate_summary_item.json:53`（`"precision": "4"`）、`:6`（`modified` 2026-10-26 15:00）；`a8b495f` 之后没再改 | ✅ 自有 DocType，migrate 导入。erx 基库与工作库 `tabDocField` 的 `rate` 精度都是 `4` | ✅（元数据层）erx 工作库计件明细 2006 行，单价 0.0020～0.0050，全部 <0.01；精度 4 下应显示为 ¥ 0.0020 一类。**没在浏览器里看实际显示** | `SELECT precision FROM tabDocField …` → 4（两库）；`SELECT COUNT(*),MIN(rate),MAX(rate) …` → `2006 0.0020 0.0050` | ✅（UI 未目视） |
| FD-017 | `zh.csv` 删 7 行、`translation_overrides.py` 删 7 条 | ✅ HEAD 上七个词在 `zh.csv` 中以任意 context 出现的行数都是 0，`translation_overrides.py` 中也都没有。`f0ac818` 改过这两个文件（FD-002），没有加回 | ✅（删行无「调用」可言）七个词改由官方词典供译 | ✅ 官方译文与原覆盖逐字相同：frappe `locale/zh.po`：Field＝字段、New Value＝新值、Reason＝原因、Result＝结果、Skipped＝已跳过、Updated＝已更新、Warehouse＝仓库；crm、insights 中同名词译文也一致；erpnext、hrms 无此 msgid。译名守卫在主会话 R11 门禁中通过（`s8-r11f-gates.summary` frappe_china python exit=0，本片未亲跑） | `grep -c "^Field,"` 等 → 0；`awk` 取各 app `zh.po` 的 msgstr | ✅ |
| FD-018 | `docs/项目概况.md:173` | ✅ `项目概况.md:173`：写了「不用 hook 的原因」「可上游化、暂不提 PR」「上游已修即删本处改动」（提交 `c2ff507`，之后未再改） | ✅（文档，`开发守则.md:35-38` 第 2 条义务指向此处） | ⚠️ 两条义务形式上都满足了，但「为何不用 hook」只排除了 `override_doctype_class`（L4 类覆盖），**没回答 R8 P1-06 原文问的那一种**：「为何不用类方法替换（L4，同 `overproduction.py` 的做法）」。项目里已有运行时替换类方法的先例（`frappe_china/production/overproduction.py:50-55`，在 `before_validate` 里把 `WorkOrder.validate_work_order_against_so` 换成自有函数），它不占类覆盖位，概况给的理由对它不成立。见 P1-02 | `grep -n "不用 hook" docs/项目概况.md`；P1 片报告 :158 | ⚠️ |
| FD-019 | `s8_rename_tax_categories.py:48-51` | ✅ `:48-51`（`log_error(title=…, message=…)`）；`a8b495f` 之后没再改 | ✅ 补丁在 `patches.txt:10`。**说明**：erx（10-24）和 test（10-21）早在修前已执行过该补丁（`tabPatch Log` 有记录），不会再跑；新装站 `install_app` 会把补丁直接标成已执行（frappe `installer.py:357-358`）。所以修后代码只会在「从 S8 之前版本升级上来的站」上执行，而且只走比对不一致那条分支 | ✅ 上游签名是 `log_error(title, message, …)`（`utils/error.py:44-46`）；`title` 不含换行，不会触发 `:58-60` 的换位 hack，Error Log 标题就是固定串 | `Patch Log` 查询；读码 | ✅（分支未实跑） |
| FD-022 | `README.md:15-23` | ✅ `README.md:15`（改为「不注册后端覆盖钩子……前端有一处覆盖」）、`:17-21`（「前端覆盖登记」节）；`runner.js:10-28` 包装仍在，`3894c5a` 对 `runner.js` 的改动不涉及这段 | ✅ `runner.js:27` 加载即安装，`demo.start` 再调一次（幂等） | ✅ 原问题（包装了全局函数却声称「不注册覆盖」）已消除，依赖写对了：`sales_order_list.js:27` 确为 `get_diff(doc.delivery_date) < 0`。小缺口：开发守则要求依赖列写「文件:行与锁定 commit」，登记表只写文件名；另 `crm_inject.py` 换 `/crm` 模板入口没登记，也没说明为何判为追加，见 P1-06 | `grep -n "get_diff(doc.delivery_date" sales_order_list.js` → :27 | ✅ |
| FD-023 | `README.md:60,65,67` | ✅（已被后续改写）`README.md:62`（26 份就绪＋1 份已用）仍在；原 `:65` 的「17/18 即就绪」已被 `3894c5a`（FD-011）改为 `:69`「回基库后 18/18 全部就绪再开讲；预跑刚结束停在第 1 幕主用库时可以不回基库直接开讲」；`:71`「每按一次右方向键走一步」，全文没有「空格」 | ✅（文档） | ✅ 三处不符均已消除：① 26＋1 与实现一致；② 就绪判据改随 FD-011 方案 A，回基库后确为 18/18（SB 实测 161～247 秒补齐），预跑刚结束的例外写明了；③ 空格已删，与 `runner.js` 只绑 `right` 一致。用户裁决「删掉『或空格』」落实了 | `git diff e1fdc14..HEAD -- README.md`；`grep -n 空格` 无结果 | ✅ |
| FD-024 | `dbops.py:25`；`README.md:43`；`s8ts023preview` 撤口令；`test_dbops.py` | ✅ `dbops.py:25-29`（`_connection_args`），在 `:36`（克隆）、`:76`（查库）、`:125`（`drop_db`）三处使用；`README.md:43`；`test_dbops.py:70-77`（`-P 3307` 断言）。`dbops.py` 与测试 `e1fdc14` 后没再改 | ✅ `drop_db` 由 `snapshot.replenish:71`、`drop_snapshots:92` 调用 | ✅ ① `s8ts023preview.localhost/site_config.json` 现在只有 `db_host／db_name／db_password／db_type／db_user／installed_apps`，无 `root_password`；② 当前只有 `erx.localhost` 带该键（演示站本来就要），`s8r9`、`s8verify`、`s8eoqformal`、`test` 都没有；③ 端口三处一致。**附带说明**：`docker/backups/` 下含 `root_password` 的 site_config 备份从 R8 时的 3 份变为 5 份（新增 SB 10-27 的 `20261027_120900` 及其「保留-S8R8SB迁移前」副本），都在 `.gitignore:5` 内，README 已提示勿外传，与裁决一致，不另立发现 | 各站 `grep -q '"root_password"'`；`grep -rl` 计数 5 | ✅ |
| FD-028 | `test_strategy_comparison.py:63-65` | ✅ `:65-67`（`currency: CNY`、`conversion_rate: 1`，带注释「so the INR test company never asks the online exchange service」）；`a8b495f` 之后没再改 | ✅ 用例在全量门禁里跑（R8 修后、SB、R11 三轮均 ✔） | ⚠️ 报错消失了，但**修法没有切断对外网汇率接口的访问**，注释与当场修清单写的「不再向外网取汇率」不成立；用例现在能过，是因为取数失败时上游兜底成 1，验证门仍依赖外网的通断与快慢。证据见 P1-01 | 原失败堆栈 `s8-r8f-full-frappe_china.log:667-877`；用时 SB 4.67 秒 vs R11 36.8 秒 | ⚠️ |

## 后续提交对本片修复的影响

| 后续提交 | 改了本片哪项涉及的文件 | 影响 | 本片修复是否仍成立 |
|---|---|---|---|
| `frappe_debug` `3894c5a`（SB） | `scenario/rehearsal.py` | FD-015 的两个方法连同鉴权一起删除（FD-020）；功能移进生成器内部、不再暴露 | ✅ 问题随入口消失；替代函数 `targets.py:15` 未白名单化 |
| 同上 | `tests/test_demo_auth.py` | 去掉两方法的断言，只剩 `snapshot_status` 与三个 POST 方法 | ✅ 与代码一致 |
| 同上 | `demo/workspace.py:60-62`、`scenario/runner.py:184-188`、`scenario/quality.py:19-28` | FD-010 检查多了「SPC 预览站」跳过条件；生成器在预览站自动走预览模式 | ✅ erx／s8dev 上检查不受影响；`quality_preview` 参数变成冗余旁路，见 P1-03 |
| 同上 | `README.md`「重做 SPC 候选计划」 | 当场修写的四步流程被证明错误并重写 | ✅ HEAD 版正确；当场修版本身未消除原问题 |
| 同上 | `README.md`「现场演示」第 1、2、6 条，「运行约束」 | FD-023 的「17/18」被 FD-011 改为「回基库后 18/18」 | ✅ 仍与实现一致 |
| 同上 | `demo/registry.py`、`demo/switch.py:104-111` | 演示中途换库不补库（FD-013），抢锁来源减少 | ✅ FD-014 的静默重试仍兜住剩下的抢锁路径 |
| 同上 | `scenario/masters.py`（上方插入 `customer_names`、`:625-627` 加拒收开关） | FD-009 那行下移到 `:618`，内容未变 | ✅ |
| 同上 | `scenario/params.py:269-271` | 只加了 `crm.open_deal_ratio` 校验 | ✅ 不涉及复核起点 |
| 同上 | `public/js/demo/runner.js` | 开播、回基库、快捷键焦点改动；`install_temporal_indicators` 未动 | ✅ FD-022 登记仍准确 |
| `frappe_debug` `dfc5ffb`、`1f9ba1c` | 不涉及本片文件（`git log e1fdc14..HEAD -- <file>` 逐个核过，只有 `3894c5a` 出现） | — | — |
| `frappe_china` `f0ac818`（FD-002） | `translations/zh.csv`、`tests/translation_overrides.py` | 加 context、删 6 条 CRM 状态登记 | ✅ FD-017 的 7 行没有加回 |
| `frappe_china` `751ae3b`、`ffadacf` | `zh.csv` 加两条新词条（成本分摊提示） | 与 FD-017 七词无关 | ✅ |
| 两 app 其余文件 | `dbops.py`、`operation.py`、`snapshot.py`、`functions.py`、`transit.html`、`s8_rename_tax_categories.py`、`piece_rate_summary_item.json`、`test_strategy_comparison.py` 在当场修之后都没再改 | — | ✅ |

## 新发现

| # | 严重程度 | 定位(文件:行) | 问题描述 | 违背的标准 | 建议 | 建议档位 | 待裁决点 | 状态 |
|---|---|---|---|---|---|---|---|---|
| P1-01 | 低 | `frappe_china/tests/test_strategy_comparison.py:65-67`；上游 `erpnext/controllers/accounts_controller.py:1068-1077`、`stock/get_item_details.py:1466-1469,1804-1811`、`setup/utils.py:107-128` | **FD-028 的修法没有切断外网请求，注释写的「never asks the online exchange service」不成立。**test 站全局缺省 `buying_price_list＝Standard Buying`（`tabDefaultValue`），该价目表币种 CNY，`_Test Company` 是 INR，`Currency Exchange` 表 0 行。插入采购单时：① `set_price_list_currency` 见 `plc_conversion_rate` 为空，按价目表币种取 CNY→INR；② `get_item_details` 的 `validate_conversion_rate` 见 `conversion_rate == 1` 且币种不同，又取一次（`or 1.0` 兜底）；③ `get_price_list_currency_and_exchange_rate` 再取一次。原失败堆栈里的 ctx 正好是 `buying_price_list: 'Standard Buying'、plc_conversion_rate: 0.0、conversion_rate: 0.0`，报错在 `conversion_rate` 为 0。修法只是让 `conversion_rate` 不再为 0，取数失败时上游返回 0 后兜成 1，所以不再报错；但每张单、每行仍在请求 `api.frankfurter.dev`（`requests.get` 不带 timeout）。旁证：该用例 SB 门禁 4.67 秒、R11 门禁 36.8 秒，两轮日志里抽看的其余 12 条带计时用例用时相差都不到 1.2 秒；R11 门禁期间 Redis 里出现过 `currency_exchange_rate_2026-10-27:CNY:INR＝14.2708`，说明容器此刻外网时通时不通。后果：用例用时随外网波动，外网卡住时没有超时，可能拖住整个门禁；网络通时 `plc_conversion_rate` 会取到真实汇率，用例的输入随外网变化（现有断言不受它影响） | 验证门须可重复（R8 FD-028 原判定）；修复回执如实 | 照 R8 原建议的第一种做法：`setUp` 里插一条 CNY→INR、`for_buying=1`、日期早于 `self.start` 的 `Currency Exchange`（上游先查本地记录，`setup/utils.py:92-96`），或采购单显式 `buying_price_list` 设为 INR 价目表；改掉不实的注释 | `本Session修` | 选「插汇率记录」还是「换价目表」；是否补一条断言（如 patch `requests.get` 断言未被调用）锁住 | 待裁决 |
| P1-02 | 观察 | `docs/项目概况.md:173`；对照 `frappe_china/production/overproduction.py:50-55` | **FD-018 补的「不用 hook 的原因」没回答 R8 P1-06 原文的问题。**原条目要求说明「为何不用类方法替换（L4，同 `overproduction.py` 的做法）」；概况只论证了不用 `override_doctype_class`（占类覆盖位）。项目已有在 `doc_events` 里运行时替换类方法的先例，不占覆盖位、不改源码；对 `StockEntry.validate_fg_completed_qty` 用同法是否可行、为什么没用，概况没写。改源码（L5）在开发守则里是「本项目禁止，除非无路可走」 | 开发守则「确须改源码时两条义务」第 1 条（注明为何 hook 不可行）；侵入度表 L5 | 概况:173 补一句：同 `overproduction.py` 的运行时替换为何不可行（或承认可行、列为将来改法）；改前按 CLAUDE.md 先载入常驻文件契约 | `延迟或不修` | 是否需要补；若认定运行时替换可行，要不要把 fork 改动换成该做法（那就是改代码、要重跑） | 待裁决 |
| P1-03 | 观察 | `frappe_debug/demo/workspace.py:44,60-66` | **`prepare_work(quality_preview=1)` 在 `3894c5a` 后成了冗余旁路。**README 已不再用它（改为站点标记 `frappe_debug_quality_preview`），但参数还在；任何 Administrator 在 erx 上带这个参数调用，都能跳过 FD-010 的开播前计划检查。后果有限：erx 上生成器不是预览模式，SPC 窗口起点会报「缺少完整候选计划」或指纹不符（`runner.py:299-320`、`quality.py:143-147`），但工作库已经登记、开始克隆 | FD-010 意图（开播前拦住）；方案外残留 | 删掉参数，只认 `is_quality_preview_site()`；或参数只在预览站上生效 | `延迟或不修` | — | 待裁决 |
| P1-04 | 观察 | `frappe_debug/scenario/runner.py:68-86` | **FD-010 的开播前检查只核版本和场景指纹，不核计划日程能否对上实际单据号。**SB 实测（回执 :62-64）：指纹相符、但计划由「只跑生成器」的隔离站产出时，演示站整场预跑在第 2 段首日才报「缺少已筛选SPC候选」，此时第 1～5 幕已演完、已拍 15 份快照（约 20 分钟）。HEAD README 已写明计划必须来自带各幕的整场彩排，并要求同日；但这是流程约束，代码检查拦不住 | FD-010 原问题「第一段一开跑即报错」的同类：失败点仍在预跑中途 | 记录即可；要代码保证，可让导出的计划附带来源标记（如「带各幕整场彩排」与基库 `tabSeries` 起点），`assert_quality_plan_ready` 一并比对 | `延迟或不修` | — | 待裁决 |
| P1-05 | 观察 | `frappe_debug/demo/snapshot.py:54-57`；`demo/registry.py:150-182` | **`snapshot_status` 仍接受 GET，每次调用都会改写登记表文件**（`refresh()` 把 cloning 改成 ready／failed 后写回、删 marker）。FD-015 只给它补了鉴权，没按 R8 建议第 ③ 条把「写状态的白名单方法」改成只收 POST。仅限 Administrator，写回动作幂等（同步 marker 状态），实际风险很低；全部调用方（`transit.html:87` fetch POST、`demo_rehearsal.js:23,27`、`runner.js:453`、`rehearsal.js:50,174,194` 经 `frappe.xcall`／`frappe.call`，均为 POST）改成只收 POST 都不受影响 | R8 FD-015 建议 ③（写状态的方法限 POST） | 改 `methods=["POST"]`，`test_demo_auth.py` 的 POST 断言加上它 | `延迟或不修` | — | 待裁决 |
| P1-06 | 观察 | `frappe_debug/README.md:17-21`；`demo/crm_inject.py:4-9`（`update_website_context`） | **前端覆盖登记两处小缺口**：① 依赖列只写了 `sales_order_list.js`，没写开发守则要求的「文件:行与锁定 commit」（实为 `:27`，ERPNext `a729571`）；② `crm_inject.py` 把 `/crm` 的模板入口换成 `frappe_debug/templates/crm_demo.html`（包住原模板、在 `</body>` 前插脚本），README 却写「前端有一处覆盖」。它可以判为「只追加脚本」而免登记，但开发守则要求那样判时在回执里说明，没找到这一说明 | 开发守则「desk 与独立前端的覆盖逐处登记」 | 登记表补行号与 commit；`update_website_context` 补一行登记，或在 README 写明判为追加的理由 | `延迟或不修` | 模板入口替换算覆盖还是追加 | 待裁决 |

**往哪些方向找过、没发现问题的**：FD-014 修复是否会吞掉非锁错误（只认 `exc_type === "DemoOperationBusy"`，其余照常 `fail`，不会）；`DemoOperationBusy` 继承 ValidationError，原先按 ValidationError 捕获的调用方不受影响（全仓无 `except frappe.ValidationError` 针对锁的分支）；`_connection_args` 的注入面（主机 `shlex.quote`、端口 `int()`，与修前同）；`review_start` 缺省 None 时的回退（`test_monthly.py:203` 手工构造 `Scenario` 走 `or sc.S`，行为与修前同）；`review_start >= finish` 校验与 `rule_periodic_from < finish` 是否冲突（不冲突，前者更严）；FD-017 删行后官方 context 词条是否被误伤（七词在 csv 中任意 context 皆为 0，未误删别的行）。

## 交接摘要

**本片依赖（需别片／主会话提供或核对）**：

- 主会话 R11 门禁的通过结论：本片对 FD-009、010、015、017、019、024 用例「通过」的判断采信 `s8-r11f-*` 日志，本片没亲跑。另：`s8-r11f-gates.summary` 记 `frappe_debug 3894c5a dirty=21`，而本片 `git -C frappe_debug status --short` 为 0 行（忽略文件不计）；请主会话确认门禁测的是否就是 `3894c5a`、那 21 处是什么。
- FD-014 的端到端证据只能来自 FD-013 的真实浏览器两场连演（SB 回执 :79-82）。那次演示中途已不补库，「补库持锁时按 →」这条路径在实测里可能根本没被触发，请负责 FD-013 的片确认有没有实际走到 `requestWhenFree` 的重试分支（看 `s8-r8sb-fd013.json` 有没有 `switch_to_act` 返回 417 的记录）。

**本片暴露（给别片／收口）**：

- **FD-015 的两个方法已被 FD-020（`3894c5a`）删除**：本片已核替代函数 `targets.py:15` `prepare_production_masters` 不对外暴露、只经 Administrator 限定的生成器入口执行，原越权问题没有以别的形式重现。请复核 FD-020 的片确认第 4、5 幕效果确实来自生成器 D1−1 段（本片没查第 4 幕默认 BOM、第 5 幕运营成本科目在 erx 快照里的值）。
- **FD-010 当场修的 README 流程错误**，由 SB 在 `3894c5a` 重写。收口时 FD-010 宜写「当场修不完整、后续提交补齐」，不宜写「当场修一次到位」。
- **FD-028 结论 ⚠️**（P1-01）：「470→471」的回归数字成立，但验证门仍依赖外网；R11 门禁里该用例 36.8 秒，是同类用例里最慢的。
- **FD-018 结论 ⚠️**（P1-02）：形式满足，实质论证漏了项目里已有的运行时替换方案。
- **SB 观察项「`snapshot_status` 回基库时偶发 500（FileNotFoundError）」**：FD-015 加的 `_authorized()`（`snapshot.py:9-12`）只调 `frappe.only_for` 并比对用户名，不读文件，可以排除它是起因；原因请 FD-013 片查（`registry.refresh` 读写 marker／登记表，换库时 `update_site_config` 改写 `site_config.json`）。
- 本片不发、不收 realtime 事件；不涉及 §13 跨 Phase 契约。

## 复核建议

1. **最拿不准的结论：P1-01（FD-028）。**「仍在请求外网」来自读上游代码、原失败堆栈的 ctx 和用时对比，没抓包、没跑用例。查法：等主会话门禁结束后，在 test 站或另一隔离站上用 `patch("requests.get")` 包住该用例，看调用次数；或看下一轮门禁该用例的用时是否随外网波动。严重程度在「低／观察」之间：现有断言不受汇率影响，只有门禁用时与可重复性受影响，所以定「低」。
2. **查得最浅处：FD-014 与 FD-016。**FD-014 只有 Node 单测（mock fetch）加读码，换库与补库真实抢锁的场景没复现；FD-016 只核了元数据精度，没目视第 6 幕计件汇总单。查法：FD-014 在隔离站「回到演示前」后几秒内点「开始演示」，看中转页有无报错文字；FD-016 打开 erx 工作库任一计件汇总单看单价列。
3. **没往这些方向找**：
   - FD-019 修后的分支没有任何站会再执行（补丁已跑过、新装站直接标记完成），正确性只有读码。
   - FD-009 的周日场景没在整年数据上出现过（本轮 S 是 2025-10-01 周三，复核起点是周一），整年层面只验证了「非周日」这一支。
   - 没查 FD-024 的 `docker/backups/` 文件内容，也没查 `s8r9` 留下的工作库与快照库是否另有口令落点（SB 记 `s8r9` 已撤回 `root_password`，本片核了其 site_config 无该键）。
   - 没审 `3894c5a` 中与本片无关的大改动（`day.py`、`verify.py`、`targets.py` 等），只看了它们对本片 12 项的影响。
4. **拿不准处**：P1-06 的 `update_website_context` 模板入口替换算「覆盖」还是「追加」，两种读法都通，取决于把「包一层模板、插脚本」视为改了上游行为与否。
