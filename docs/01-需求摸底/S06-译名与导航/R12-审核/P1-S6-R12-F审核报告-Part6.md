# F 审核分片报告 · 片 6（对象：R9 开发方案 TS-025～034 的前端补丁、CRM 侧栏覆盖与取法 / 审核标准：R2 B 需求文档 §4.2.6、§4.12、§八 ＋ R9 C 讨论记录 DEC-039～041 ＋ ADR-0009）

**轮次**：P1-S6-R12｜**步骤**：F 分片 6｜**日期**：2026-10-13｜**执行者**：Claude 子 Agent（只读）
**依据**：[R9 C开发方案](../R09-开发方案/P1-S6-R9-C开发方案.md)（全文：A23～A28、HT-021～027、SL-016～023、TS-025～037）；[R9 C讨论记录](../R09-开发方案/P1-S6-R9-C讨论记录.md)（DEC-039～041、LG-011）；[R2 B需求文档](../R02-需求文档/P1-S6-R2-B需求文档.md) §4.2.6、§4.11、§4.12、§八；[ADR-0009](../../0-P1文档/ADR-0009-desk前端改造追加加有限覆盖.md)；`docs/开发守则.md`「译名自检时机」第三段、「desk 与独立前端的覆盖逐处登记」；`docs/业务规则.md`
**线索（不采信）**：[R10 D回执](../R10-代码/P1-S6-R10-D回执.md)、[R11 E确认报告](../R11-确认/P1-S6-R11-E确认报告.md)（IT-052～059 当场修后状态）
**被审范围**：`frappe_china` HEAD `d441e9f`，`git diff 3f9511a..d441e9f` 中除 `4f75f5a`（R5 SB）以外的部分：`public/js/desk_patches.js:70-188`（TS-027～031）、`public/js/independent_app_labels.js`（TS-032～034）、`templates/independent_apps/crm.html`、`crm_sidepanel.py`、`hooks.py:30-33,226-232`、`website_translation.py`、`tests/test_translations.py:87-176,289-308`（A28）、`tests/test_desk_patches.cjs`、`tests/test_independent_app_labels.cjs`、`tests/test_crm_sidepanel.py`、`tests/test_website_translation.py`、`zh.csv` R9 的 16 增 1 改、`README.md:61-66,82-85,94`

## 覆盖自证

- **读全的依据**：F Spec、`bricks/audit.md`、`bricks/sharding.md`；R9 方案全文（逐条建要求清单，见下表）；R10 D 回执、R11 E 报告全文；R2 需求文档 §4.2.6、§4.11、§4.12、§八与目录；R9 C 讨论记录 DEC-039～041 段与决策表；ADR-0009 全文；开发守则第 99-121 行与契约表表头；业务规则全文。**未读**：R3 总纲与 R6 方案（只用 R9 方案对其的引用）、R9 C 讨论记录 DEC-039～041 以外的段落。
- **逐行读的代码**：`desk_patches.js` 全文（1-244）、`independent_app_labels.js` 全文（1-177）、`crm_sidepanel.py`、`website_translation.py`、三个 `independent_apps/*.html` 与 `injection.html`、`hooks.py` 相关段、`test_translations.py` 第 87-176、289-308 行、`test_crm_sidepanel.py`、`test_website_translation.py` 全文，两个 `.cjs` 只读了用例名与载入方式；`zh.csv` 的 R9 diff 全部。
- **对照的上游**（锁定 commit 与 `docker/apps.json` 一致，六个上游 `git status` 为空）：frappe `filter_list.js:130-147`、`list_view.js:752-800`、`page.js:545-700`、`query_report.js:1379-1452`、`dialog.js:1-60`、`formatters.js:40-56`、`base_timeline.js:10-140`、`form_timeline.js:329-370`、`version_timeline_content_builder.js:410-419`、`utils.js:269-273`、`www/desk.html:65`、`hooks.py:25-34`；erpnext `sales_invoice.js:303-337`、`purchase_invoice.js:228`、`general_ledger.py:556-562,760-810`、`stock_ledger.py:405-412`、`stock_ledger.js:127-136`、`workstation_dashboard.py:1-20`；CRM `crm_fields_layout.py:113-191`、`SidePanelLayout.vue:2,95-165`、`translation.js`、`www/crm.py:83-84`、`api/dashboard.py:971`、frappe-ui `ListFooter.vue:1-27`、echarts `core/locale.js:55-58`；Raven `Profile.tsx:28`、`useSetAvailability.ts:9`；六个 app 的 `main.pot`／`zh.po` 中 `Master`／`Madam`／`Miss`／`Mrs`／`JAN` 的出处。
- **自己跑的**（临时脚本都在 `Spike/P1S6R12-F/p6/`）：宿主 `node --test frappe_china/tests/*.cjs`；`scan_keys.py`（取法一致性全扫）、`ast_vs_regex.py`（Python `_()` 字面量 AST 对照正则）、`r9_rows.py`（R9 各行归类）、`probe_forms.py`（A28 边界写法 12 例）、`replace_probe.cjs`（`String.replace` 替换模式）、`perf_probe.cjs`（happy-dom 量 CRM 注入脚本耗时）；`Spike/P1S6R6-csv-prune.py --dry-run`、`Spike/P1S6R9/own-keys.py`；演示站只读探针 `site_probe.py`、`site_check.py`、`master_probe.py`（`docker cp` 进容器跑，结束 `rollback`，容器内临时文件已删）；curl 演示站静态资源比 md5、拉 `/raven`、`/insights` 页。
- **跳过**：没跑 `bench run-tests`（主会话占用测试站），Python 用例只读码；没做浏览器实页（演示站无线索数据，且只读约束下不登录操作），Desk 补丁的实页效果只用 R10／R11 的截图读数当线索；没做变异（R11 已做 37 个，IT-056 已裁不做）。

## 逐项落地核查

| 意图层依据 | 要求层要求（方案任务／验收条款） | 定位（文件:行） | 落地 | 生效否 | 偏差说明 |
|---|---|---|---|---|---|
| ADR-0009、A23 | 共用包装：完整委托 receiver／实参／返回值；缺方法只告警；幂等标记 | `desk_patches.js:73-83`（`patch_method`） | ✅ | ✅ 演示站 8000 发出的 js 与源码 md5 同为 `e29a87f5…` | `wrapped[mark]` 打在包装函数上，重复加载看到标记即返回；`owner` 缺失与方法缺失走同一告警 |
| HT-021 | `app_include_js` 在 frappe 各 bundle 之后加载 | `hooks.py:30-33`；frappe `hooks.py:25-34`、`www/desk.html:65` | ✅ | ✅ | frappe_china 装在末位，`app_include_js` 按 app 序累加 |
| SL-016 ①、TS-027 | `update_filter_button` 委托后 zh 写 title，n>1 复数、0/1 单数，0 也写 | `desk_patches.js:89-99` | ✅ | ✅ | 与上游 `filter_list.js:143-146` 分支一致；IT-052 修后每个 `translate()` 只放一个字面量 |
| SL-016 ②、TS-027 | 首列排序 title 改为带父 DocType 的译名；找不到错误 title 原样返回 | `desk_patches.js:103-112` | ✅ | ✅ | `html.replace(wrong, right)` 用字符串作替换参数，见 P6-03 |
| SL-016 ③、TS-028、HT-027 | 带分组时先 `__()` 再按原实参委托 | `desk_patches.js:118-124` | ✅ | ✅ | 上游 `remove_inner_button` 先译再查（`page.js:673`），`change_inner_button_type` 按原 label 查（`page.js:692`），全 bench 带分组的 change 调用 0 处；`sales_invoice.js:282`、`stock_entry.js:634`、`payment_order.js:62` 的带分组 remove 走先译分支，结果一致。IT-055 变量 label 的代价已裁定接受 |
| SL-016 ④ | 英文不变、缺类只告警、重复加载不叠加 | 同上；`test_desk_patches.cjs:115-133,180-189` | ✅ | ✅ | Node 71/71 实跑 |
| SL-017、TS-029、A24 | 白名单（报表，字段）包 `column.format`，只改显示值，`data` 不动 | `desk_patches.js:132-151` | ✅ | ✅ | `format.call(this, …)` 保留 receiver；`report_name` 取自 `query_report.js:166`；Stock Ledger 自带 formatter 在原 `format` 内部调用（`query_report.js:1436-1446`），不受影响 |
| SL-018、TS-030、A25 | 只改 `.new-timeline .timeline-content` 内恰为 `null`／`undefined` 的 `<b>`；Observer 一个 | `desk_patches.js:158-167` | ✅ | ✅ | 选择器同样命中评论、邮件卡片（见 P6-04）；每批变更扫整个文档（见 P6-05）；`document.body` 缺失时静默跳过、不告警（A23 只要求上游缺失告警，本处属观察，并入 P6-05） |
| SL-018 ④ | 上游缺陷报告草稿，不外发 | `Spike/P1S6R9/upstream-it035.md` | ✅ | — | 根因行号 `version_timeline_content_builder.js:416`、`utils.js:269-273` 对得上 |
| SL-020 ①、TS-031 | 包 `Dialog.prototype.make`，标题为 `__("Fetch Timesheet")` 时只改 Date 型 `from_time`／`to_time` 标签 | `desk_patches.js:173-188` | ✅ | ✅ | 上游 `sales_invoice.js:305` 传的就是 `__("Fetch Timesheet")`；`From Date`／`To Date` 合并字典为「起始日期」「截止日期」（演示站实测） |
| SL-020 ②③、TS-032、A27 | Raven 页在 `bridgeMessages` 成功后把 `_messages["Available"]` 换成 context 行；缺行告警 | `independent_app_labels.js:36-46,74-77` | ✅ | ✅ | 演示站合并字典 `Available:Raven User`＝「有空」、`Available`＝「工位可用」；`/raven` 页含注入脚本 |
| SL-019 ①、TS-033 | CRM 页 `lang="zh"`；上游标签变了用例失败 | `crm.html:3`；`test_website_translation.py:36-47` | ✅ | ✅ 演示站渲染恰一处 `<html class="h-full" lang="zh">` | — |
| SL-019 ②③、TS-033 | `Empty` 进 chart 区；两数之间的 `of` 改「/」，同容器 `Load More` 改「加载更多」 | `independent_app_labels.js:5,15,50-53,115-136` | ✅ | ✅ happy-dom 实跑：20／100／500 行三档翻页均为「N / 2N」「加载更多」 | D 偏离第 2 条（从按钮往上找）已由 R11 追认；500 行首轮 227 ms，见 P6-05 |
| SL-019 ④、TS-034、A26 | `override_whitelisted_methods` 包 `get_sidepanel_sections`，只改自动生成的占位与只读提示 | `crm_sidepanel.py:17-38`；`hooks.py:231` | ✅ | ✅ 演示站 `get_hooks` 该键末项为本 app；CRM Lead 12 个占位全中文 | 只读提示服务端改写与 CRM 前端 `__(field.tooltip)`（`SidePanelLayout.vue:102`）重复，无害；`Select` 分支走不到（R11 已记）。CRM 的 8 个页面（含 Contact、Organization 与移动端）都调原路径，覆盖面大于 IT-037 点名的两屏，属方案原意 |
| SL-019 ⑤、TS-034 | 侧栏内 User 型占位按 `Select {0}...` 重建，侧栏外不变 | `independent_app_labels.js:58-66,137-151` | ✅ | ✅ | 正则由 `messages['Select']` 转义构造；只改 `nodeValue`／`placeholder` 属性 |
| SL-021 ①、TS-025、A28 | 取法拆两层，认 `translate(`、`*SOURCE(S)` 常量、侧栏 json | `test_translations.py:87-160` | ⚠️ | ✅ 对现有代码 | 现有代码全部取到（见「取法一致性」）；按开发守则原文写的几种形态仍取不到，见 P6-02 |
| SL-021 ①（IT-052 修后） | 25 键＋`CN Tax`＋6 个 R9 自有键 ⊆ `_app_source_strings()` | `test_translations.py:164-176,300-306` | ✅ | ✅ `own-keys.py` 32 键全在，退出码 0 | — |
| SL-021 ③④、TS-026、DEC-039～041 | 10 行定词、`NAMED_TERMS`、`OVERRIDES`、`UNTRANSLATED` | `zh.csv` 第 75,287,602-603,997,2490,2698,2842,2877,2887,2983,3037,4375,4950,5053,5761,5762 行；`test_named_terms.py:76-88`；`translation_overrides.py`；`translation_whitelist.py` | ✅ | ⚠️ | 无 context 的 `Master`→「少爷」波及 ERPNext 工作站关联页签分组标题，见 P6-01 |
| §4.12、ADR-0009、SL-023 ③ | 每处补丁 README 一行：接入点／覆盖文件／上游依赖（文件:行与锁定 commit）／失效症状／复验法 | `README.md:61-66,82-85,94` | ⚠️ | — | 上游文件:行、失效症状、复验法齐；`:62-64,66` 四行没写锁定 commit，见 P6-06 |
| §4.11 | 法定报表中文列头不被 csv 翻译 | `translation_check.py` | ✅ | ✅ 演示站 `find_problems()`＝`[]`，`Translation` 0 行 | — |

### 取法一致性（任务第 2 项）

- `_app_source_strings()` 实跑 279 键；`keep_keys()` own 281（含 `REQUIRED_TRANSLATIONS`）、named 75、override 114；`csv-prune.py --dry-run`：原 5751 行，保留 318（own 187），与 R11 修后数相同。
- **R9 新增或改动的 17 行 csv 全部被保留规则认出**：`(Empty)`、`Add {0}...`、`Select {0}...`、只读提示、`{0} Filter Applied`、`{0} Filters Applied` 归 own；`Available` 归 override；`Available:Raven User`、`Inter Company Invoice`、`Manufacturing Setup`、`To:UOM Conversion Factor` 归 named；称呼 4 词与 `JAN` 同在 named 与 override；`CN Tax` 同在 own 与 named（`r9_rows.py`）。
- **自有代码里仍不被取法认出、但 csv 有行的自有键：0 个**。宽口径把 100 个文件里的全部字符串字面量与 csv 键求交，再去掉三类保留键，剩 9 个，都不是译名键：`in`、`item`、`items`、`reason`、`string` 是代码里的字典键或 `typeof` 值，`From`、`Contact`、`Total` csv 无行，`Raven User` 是 `RAVEN_CONTEXT_KEYS` 的 context 名（csv 那行是 R7 批量档的旧行）。Python 侧另用 AST 抽所有 `_()`／`__()` 字面量调用（含 `context=`）与正则结果比对，漏 0 个。
- **非字面量调用点**（`scan_keys.py` 列出 26 处，去掉 7 处注释里的误命中后）：JS 9 处、Python 10 处，实参都是变量（上游 label、DocType 名、`company_defaults.json` 的键、`PENDING_LOSS_ISSUE`、`LEGAL_LABELS`），对应的键要么是上游词，要么另有 `REQUIRED_TRANSLATIONS`／`LEGAL_LABELS` 守住，没有因此丢的自有 csv 行。`PENDING_LOSS_ISSUE`（`closing.py:32`）不守 A28 命名约定，靠 `REQUIRED_TRANSLATIONS` 第 76 行保留——约定不是唯一保护，但守则读者看不出这一点。
- **csv 有行、三类都不认的行**：5433 行，就是 R7 批量档。方案 TS-025 第 4 步已写明清场脚本不认批量档、只看能否跑通。所以「下次清场会被删」对整个批量档都成立，脚本现在不能直接对 csv 落盘运行。R9 没有让这个缺口变大，本片不另立发现，记在集成点里。

### 安全性与性能（任务第 3 项）

- **HTML 注入**：两份脚本没有 `innerHTML`／`.html(`／`insertAdjacentHTML`（grep 0 处）。改写都走 `textContent`、`nodeValue`、`setAttribute`。两处值会进入上游拼的 HTML：`Page.add_inner_button` 交给上游的 `__(label)`，`get_header_html` 的 `right`。上游对同一位置本来就输出未转义的 `__(label)`（`page.js:647,660`、`list_view.js:783`），译文来自 csv／po／管理员维护的 Translation，没有引入新的注入源。CRM 侧栏占位以 JSON 返回、由 Vue 属性绑定渲染，也是安全的。
- **`String.replace` 替换模式**：`get_header_html` 的 `html.replace(wrong, right)` 第二参是字符串，译名里的 `$&`／`` $` ``／`$'` 会被当作替换模式（P6-03）。
- **MutationObserver 范围**：Desk 时间线 Observer 挂 `document.body`（`subtree`＋`childList`），每批变更都对整个文档跑一次 `querySelectorAll`；R5 IT-026 已把 datatable 那个 Observer 收窄成只扫新增子树，这个还没收（P6-05）。CRM 注入脚本对每个变更目标都调 `processListFooter`，遍历目标下全部 `div` 并逐个取 `textContent`；happy-dom 量首轮：689／3409／17009 个 div 分别耗时 12.6／32.3／227.5 ms（P6-05）。自写回的 `characterData` 由 `changed` WeakMap 跳过，不会自激循环。

## 业务规则合规核

本 Round 本片的改动只涉及界面译名与显示，不涉及产品语义（会计准则、税率、价税分离、结转），BR-001～007 都不触及。唯一的间接触点是 BR-002 所定报表的法定中文列头不得被 csv 翻译：演示站 `find_problems()` 返回 `[]`，合规。本片没有检出新增或变更的领域不变量。

| 规则条款 | 本 Round 改动是否涉及 | 结论 | 备注 |
|---|---|---|---|
| BR-002（法定报表列头） | 间接（csv 新增 17 行） | 合规 | 演示站 `translation_check.find_problems()`＝`[]`（`site_check.py`） |
| BR-001、003～007 | 否 | — | 本片无会计与税务逻辑改动 |

## 集成点登记（交接摘要）

**本片暴露**

| 类型 | 落点 | 写实 |
|---|---|---|
| 接口契约 | `override_whitelisted_methods["crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_sidepanel_sections"] = "frappe_china.crm_sidepanel.get_sidepanel_sections"`（`hooks.py:231`） | 签名 `(doctype: str) -> list`，照原样委托上游，只在 `frappe.local.lang == "zh"` 时改 `placeholder`／`tooltip`。CRM 前端 8 个页面都调这个原路径（`Lead.vue:615`、`Deal.vue:819`、`Contact.vue:324`、`Organization.vue:342` 与 4 个移动端页面）。`check_app_order` 不查这一项 |
| 共享状态 | `frappe.ui.FilterGroup／Page／Dialog`、`frappe.views.ListView／QueryReport` 的原型方法，各带 `__frappe_china_*` 标记 | 其它片或以后的补丁再包同一方法时，必须在本包装之外再包，不能拿标记判断是否已包 |
| 共享状态 | `document.__frappe_china_timeline_nulls`、`document.__frappe_china_datatable_titles` 两个 Observer | 都挂 `document.body` |
| 共享状态 | Raven 页的 `window.frappe._messages["Available"]` 被改写成「有空」 | 只在 Raven 页、只在 `bridgeMessages` 成功之后 |
| 数据流 | `website_translation.SOURCES` → `context.china_labels` → `#china-ui-labels` JSON → `independent_app_labels.js` 的 `config.messages` | 已核两端一致：JS 用到的键与 `SOURCES` 双向差集都为空 |
| 约定 | A28 命名约定（开发守则第 105 行） | 取法对其中几种写法不认，见 P6-02 |

**本片依赖**

| 类型 | 落点 | 写实 |
|---|---|---|
| 共享状态 | `zh.csv` 的 17 行（csv 片、取法片） | 演示站合并字典逐键核过；`Master`、`Available` 两个无 context 键的波及面属于 csv 定词片 |
| 接口契约 | `Spike/P1S6R6-csv-prune.py` exec `test_translations.py` 的两个 FunctionDef | 拆层后靠「两个函数体内各自 import」才能单独 exec；以后若把 import 移到模块级，脚本会 `NameError` |
| 数据流 | CRM `www/crm.py:84` 的 `translated_messages = get_messages_for_boot()` | 前端 `__('Select')` 与注入脚本的 `messages['Select']`（「单选」）同源，`rewriteSelectPlaceholder` 的正则前提靠这一点成立 |
| 事件 | 无 | 本片不发出、也不消费 realtime 事件 |

## 自证复核

| 被审产物声称 | 实际复核结果 | 一致否 |
|---|---|---|
| R11：Node 71/71 | 宿主实跑 71 条，71 过，0 失败 | 一致 |
| R11 IT-052 修后：`csv-prune --dry-run` kept 318、own 187；`own-keys.py` 32 键全在 | 实跑 `{"original": 5751, "kept": 318, "own": 187, …}`；`expected=32 … missing=[]`，退出码 0 | 一致 |
| R11 IT-053 修后：开发守则 A28 那段与实现一致 | 只对「数组字面量里的字符串」一致；守则写的是「其中的字符串字面量都算」，JS 标量、JS 对象值、Python dict／`frozenset(...)`／嵌套 tuple 都取不到（`probe_forms.py` 12 例里 7 例 MISS） | **不一致**，见 P6-02 |
| R11：演示站 8000 发出的 `desk_patches.js` md5 `e29a87f5…` | 两个 js 都与源码 md5 相同 | 一致 |
| R9 C 讨论记录第 39 行：五个称呼源词「在 `frappe/locale/main.pot` 中都只有 `install_fixtures.py` 一处出处」 | 对 frappe 的 pot 成立；但 ERPNext `workstation_dashboard.py:8` 也以无 context 的 `_("Master")` 取词（ERPNext 的 pot 不重复收 frappe 已有的 msgid，所以只查 frappe 的 pot 看不出来）。演示站 zh 下该看板分组为 `["少爷", "交易"]` | **不一致**，见 P6-01 |
| R10 D 回执 TS-034：「只读提示改中文」靠服务端覆盖 | CRM 前端本来就渲染 `__(field.tooltip)`，有 csv 行就够；服务端改写是冗余，结果相同 | 结论一致，理由不完整（观察，不立项） |
| R11 清单外：`formatters.Data` 无可选链 | 补证据：`desk_patches.js:238` 是 IIFE 的最后一条语句，前面各补丁已经装好；`frappe.form.formatters` 缺失时抛出的 TypeError 只会让 Select formatter 装不上，不影响其它补丁 | 补证 |
| R11 清单外：`it026-check.cjs:23` 无效字段 | 补证据：`!x?.mark === false` 按优先级是 `(!x?.mark) === false`，等价于 `Boolean(mark)`；节点没被替换、和被替换后又打上标记两种情况都得 `true`，区分不了 | 补证 |

## 验证门实跑结果

| 门 | 声称值 | 实测值 | 与基线对比 | 一致否 |
|---|---|---|---|---|
| `node --test frappe_china/tests/*.cjs`（宿主 Node v24.13.1） | 71/71（R11） | 71/71 | 基线 29，只增不减 | 一致 |
| `bench run-tests --app frappe_china` | 267/267（R11 修后） | 未跑（约束：主会话在测试站跑全量） | — | 未核 |
| 语法 | — | `node --check` 两个 js 通过；`ast.parse` 6 个 py 通过 | — | — |
| 清场脚本 dry-run | kept 318 | kept 318 | — | 一致 |
| 演示站 `find_problems()` | `[]` | `[]`，`Translation` 0 行 | — | 一致 |

## 问题清单

| # | 严重程度 | 定位 | 问题描述 | 违背的标准/意图 | 建议 | 建议档位 | 待裁决点 | 状态 |
|---|---|---|---|---|---|---|---|---|
| P6-01 | 中 | `zh.csv:2887`（`Master,少爷`）；上游 erpnext `manufacturing/doctype/workstation/workstation_dashboard.py:8` `{"label": _("Master"), …}`；前端 `form_links.html:8` `__(transactions[i].label)` | DEC-039 把无 context 的 `Master` 定为「少爷」，波及 ERPNext 工作站表单「关联」页签的分组标题（官方「主表」，含 BOM／工艺路线／工序三项）。演示站只读实测：zh 下 `get_data()["transactions"]` 的分组为 `["少爷", "交易"]`（`master_probe.py`）。工作站是演示线环节 5 的表单（`05-workstation`、`05-workstation-saved` 两屏）。逐屏核只拦英文、繁体与 title，中文但词义错的拦不住，所以 143/143 通过不能证明没问题。DEC-039 的出处核查只查了 frappe 的 pot（讨论记录第 39 行），漏了 ERPNext 的调用。与 IT-048（`Available` 波及 Raven）同类 | 需求 §4.2.4「点名用词表」的用意是定词不误伤别处；DEC-039 的「六个称呼互不重名」只考虑了称呼下拉 | 交用户在两条路里选：① 用 `override_doctype_dashboards` 包 Workstation 看板，把该分组标题换成另一个键（如 `Master Data:Workstation`）；② 接受代价并在 DEC-039 的失效条件里补记。顺带用 ERPNext、HRMS 的源码（不只看 pot）复查 `Mrs`／`Miss`／`Madam`、`JAN` 有没有别的无 context 调用（本片已查 `_()`／`__()` 字面量调用：只有 `Master` 有第二处） | `出方案修` | 改看板覆盖还是接受「少爷」 | 待裁决 |
| P6-02 | 低 | `tests/test_translations.py:111-130`；`docs/开发守则.md:105` | A28 的取法只认这几种形态：Python 模块级常量的值是 str，或 tuple／list／set 里直接放 str；JS 是 `(const\|let\|var) \w*sources? =` 之后方括号里的引号串。开发守则原文是「常量名以 `SOURCE` 或 `SOURCES` 结尾……其中的字符串字面量都算」。`probe_forms.py` 按守则原文构造 12 例，7 例取不到：JS `const X_SOURCE = "a"`（标量）、JS `const X_SOURCES = {a: "b"}`（对象值）、Python `X_SOURCES = {"k": "v"}`（dict）、`frozenset({...})`、嵌套 tuple。另外 JS `translate("k", null, "ctx")` 被取成无 context 的 `k`，带 context 的 csv 行会被清场删掉；`` __(`k`) `` 模板字符串取不到。IT-053 只补了 JS 单数数组一种。现有代码没有命中这些写法（本片全扫，漏 0），属潜在风险；但这是 IT-043、IT-052、IT-053 同一根因第四次露头 | 开发守则 A28 段；R9 A28「约定比逐个点名更稳，新增的取用点只要守约定就自动被认出」 | 二选一：① 守则改写成取法真实支持的形态（「值为字符串，或字符串的 tuple／list／set；JS 只认数组字面量」），并写明 JS 带 context 必须用 `__()`；② 取法 Python 侧改用 `ast.walk(node.value)` 收全部 str 常量，JS 侧认 `{...}` 与标量，正则补第三参 context。都要在 `test_source_strings_literal_key_forms` 补上反例 | `新Session修` | 改守则措辞还是扩取法 | 待裁决 |
| P6-03 | 低 | `public/js/desk_patches.js:110` | `html.replace(wrong, right)` 的第二参是字符串，`right` 里出现的 `$&`、`` $` ``、`$'`、`$$` 会被当作替换模式。`replace_probe.cjs` 构造译名含 `$&` 的 label，结果把原 title 整段塞回新 title 中间，HTML 属性被拆坏。现 csv 与六个上游 `zh.po` 的 msgstr 里这类序列都是 0 条，但字段 label 可由用户自建（Custom Field、Translation），不受本 app 控制 | A23「原样返回／完整委托」；SL-016 ②「其余部分与原方法逐字相同」 | 改成 `html.replace(wrong, () => right)`，Node 用例补一个含 `$&` 的 label | `本Session修` | — | 待裁决 |
| P6-04 | 低 | `public/js/desk_patches.js:160`；上游 `base_timeline.js:136`、`form_timeline.js:350` | 选择器 `.new-timeline .timeline-content b` 不只命中修改记录：评论卡片与邮件卡片（`timeline-content frappe-card`，由 `timeline_message_box` 渲染用户写的内容）也在 `.timeline-content` 里。用户评论里加粗的 `null`／`undefined` 也会显示成「（空）」，改的是用户数据的显示。这是方案 SL-018 ① 原文给的选择器，D 照做 | A25「只作用于时间线修改记录」；SL-018 标题「修改记录 `null`」 | 选择器排除卡片：`.new-timeline .timeline-content:not(.frappe-card) b`，Node 用例补一个评论卡片内 `<b>null</b>` 不变的反例 | `新Session修` | 是否收窄到非卡片项 | 待裁决 |
| P6-05 | 观察 | `public/js/desk_patches.js:164-167`；`public/js/independent_app_labels.js:115-136,168-175` | ① Desk 时间线 Observer 挂 `document.body`，每批 `childList` 变更都对整个文档 `querySelectorAll` 一次，在所有 Desk 页面常驻；R5 IT-026 已把 datatable Observer 收窄成只扫 `addedNodes` 子树，这个没收。`document.body` 缺失时静默不建，不像 datatable 段那样告警。② CRM 的 `processListFooter` 对每个变更目标遍历其下全部 `div` 并逐个取 `textContent`（上层 div 的 `textContent` 覆盖整棵子树）。happy-dom 首轮实测：689／3409／17009 个 div 分别 12.6／32.3／227.5 ms。CRM 默认每页 20 行，现在没有实际问题 | ADR-0009（覆盖是技术债）；R5 IT-026 的收窄口径 | 时间线 Observer 改成只扫 `addedNodes`，与 datatable 段同形，并补缺 body 告警；CRM 翻页处理限定在 `.flex.items-center` 翻页容器内，或先用 `textContent.trim() === 'of'` 的叶子节点过滤 | `延迟或不修` | 现在收窄还是留到上游升级复验时 | 待裁决 |
| P6-06 | 低 | `frappe_china/README.md:62,63,64,66` | A23 与开发守则「覆盖逐处登记」都要求上游依赖写「文件:行与锁定 commit」。ListView、Page、QueryReport、时间线 4 行只写了文件:行，没写锁定 commit；第 61 行用「同一 commit」指代上文，第 58、60 行写了 Frappe `c1f1e8ec…`。R11 IT-054 只给 Dialog 行补了 ERPNext commit。读者能从上下文推出 commit，但单看一行查不到 | 开发守则第 119-121 行；A23 | 4 行各补 Frappe `c1f1e8ec3708750d7254f7f99d869ffb9886f19f`，或在表格上方写一句「本表未注明者均为 Frappe `c1f1e8ec…`」 | `本Session修` | — | 待裁决 |

（严重程度：高＝阻断／根因偏离 · 中＝需修 · 低＝技术债 · 观察＝可容许偏差记录）

## 总体判断

- 结果是否真满足源头意图：**部分满足**。TS-027～034 的补丁、CRM 侧栏覆盖与 A28 取法对现有代码都落地且生效：Node 71/71、演示站静态资源与源码一致、R9 新增 17 行 csv 全部被保留规则认出、自有代码里没有漏认的键。关键缺口两处：P6-01，`Master`「少爷」误伤工作站看板，逐屏核拦不住这类问题；P6-02，开发守则 A28 的表述宽于取法实际能认的范围，同一根因第四次露头。
- 状态：`有发现`（中 1、低 4、观察 1）。

## 本片盲区自述

- **没做实页**：Desk 补丁与 CRM DOM 改写的实效只用 R10／R11 的截图读数和 happy-dom 结构模拟。happy-dom 与真实浏览器在 `textContent`、MutationObserver 批次上可能有差异（开发守则 §12 所列风险）。P6-01 只证了服务端 `get_data()` 的返回值，没有截工作站「关联」页签。
- **没往哪个方向找**：没交叉核 R7 批量档里其它无 context 定词对上游别处调用的波及（P6-01 只查了 R9 新定的 5 个键）；没核 Insights 页（R9 未改）；没核 `invoice_list.js`、`opening_ledger.js`（不在 R9 范围）；没核移动端 CRM 侧栏的 DOM 选择器是否同为 `.sections.flex.flex-col.overflow-y-auto`（服务端覆盖对移动端同样生效，前端 User 型占位改写在移动端是否命中未查）。
- **最拿不准**：P6-01 定「中」还是「低」。定「中」的理由：在演示线环节 5 的表单上，而且是 DEC-039 出处核查的漏项；可降为「低」的理由：只在「关联」页签显示，页签默认不展开，逐屏核的两屏截的是详情页签。P6-02 在「低」与「中」之间：现有代码零命中，但同类根因已经连续出现。
