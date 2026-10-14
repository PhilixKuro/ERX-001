# F 审核分片报告 · 片 4（对象：R3 Part4 中仍有效的部分〔SL-010 ①⑤⑥⑦、TS-015〕及 R9 TS-036／037 的接续、S6 最终状态 / 审核标准：B 需求文档 §4.3／§4.9／§4.10／§七／§八 AC-001／002／009／015 ＋ 路线文档 §三 S6 行、§四 S6 ＋ Stage 概况长效信息）

**轮次**：P1-S6-R12｜**步骤**：F 分片 4｜**日期**：2026-10-13｜**执行者**：Claude 子 Agent（只读）
**依据**：F Spec（`F-codeAudit-plannedDev-audit.md`）、`bricks/audit.md`、`bricks/sharding.md`、`常驻文件契约.md`；[B 需求文档](../R02-需求文档/P1-S6-R2-B需求文档.md) §一、§4.3、§4.9～§4.12、§七、§八、§十；路线文档 §三 S6 行、§四 S6；[R3 总纲](../R03-开发方案/P1-S6-R3-C开发方案-总纲.md) §一、§四 A6／A13／A14、§九；[R3 Part4](../R03-开发方案/P1-S6-R3-C开发方案-Part4.md) 全文；[R6 方案](../R06-开发方案/P1-S6-R6-C开发方案.md) §一、§四 SL-014／015、TS-023／024、§六；[R9 方案](../R09-开发方案/P1-S6-R9-C开发方案.md) §一、§二 A23、SL-022／023、TS-036／037；[S6 概况](../P1-S6-概况.md)「当前进度」「本 Stage 的长效信息」「登记册」
**被审范围**：`frappe_china/README.md` 全文（HEAD `d441e9f`）；`hooks.py` 与 `public/js/*.js` 全部五个文件（反向核登记）；`docs/开发守则.md`、`docs/项目概况.md` 在 `68f8f05..HEAD` 的 S6 改动；`docker/apps.json`、`docker/README.md` 的 S6 改动；演示站 `erx.localhost` 当前状态（只读）；`docker/backups/`；`Spike/P1S6R9-screens/result.json` 与 `Spike/P1S6R9-screens.json`
**线索（不采信，只拿来对照）**：R4 D 回执 Part4、R7 D 回执、R10 D 回执、R11 E 报告。**编号**：本片发现用 `P4-01` 起编，收口时再统一改成 `FD-` 编号。

## 覆盖自证

- **读全的依据**：上列 Spec 与积木全文；R3 总纲、Part4、R6 方案（§一～§六与 TS-023／024 全文）、R9 方案（§一～§四与 TS-036／037 全文）；B 需求文档按任务点名的各节全文（§一、§4.3、§4.9～§4.12、§七～§十）；路线文档 S6 两处；S6 概况全文；R10 D 回执、R11 E 报告全文；R4 Part4 回执、R7 D 回执中 TS-014／015、TS-023／024 与工作量相关的行。
- **逐行读的代码**：`public/js/desk_patches.js`（1-244）、`independent_app_labels.js`（1-177）、`invoice_list.js`、`opening_ledger.js`、`realtime_check.js` 全文；`hooks.py` 有效配置全部；`translation_check.py`（1-51）、`website_translation.py`、`patches/s6_rename_cash_flow_worksheet.py`、`patches.txt`、`realtime_check.py` 的 `run`。
- **README 登记的上游 文件:行**：逐条打开锁定 commit 的源码核过，共 30 处，覆盖 frappe（`button.js`、`sidebar_header.js`、`filter_list.js`、`list_view.js`、`page.js`、`query_report.js`、`dialog.js`、`version_timeline_content_builder.js`、`utils.js`、`indicator.js`、`base_list.js`、`select.js`、`formatters.js`，以及 `frappe-datatable` 1.20.7 的 `rowmanager.js`、`columnmanager.js`）、erpnext（`stock_controller.js`、`sales_invoice.js`、`sales_invoice_list.js`、`purchase_invoice_list.js`、`journal_entry.js`、`payment_entry.js`、`general_ledger.py`）、CRM（`crm_fields_layout.py`、`SidePanelLayout.vue`、`www/crm.html`、`dashboard.py`、frappe-ui `ListFooter.vue`）、Raven（两个 `Profile.tsx`、`useSetAvailability.ts`）。
- **本片实跑**：七个 app HEAD 对 `apps.json`，`status` 全空，`frappe_china` 的 `origin/main`＝`d441e9f`；演示站只读 SELECT 三批，脚本 `Spike/P1S6R12-F/p4/q*.sql`；`translation_check.run`、`find_problems`、`install.check_app_order` 都是纯查询；`list-apps`；8000 发出的 4 个 js 与源码 md5 比对；备份目录与 md5；Python 解析 `result.json` 与 `screens.json`；宿主 `node --test` 五个 `.cjs`。
- **跳过及原因**：
  - 未跑 `bench run-tests`（约束：主会话在测试站跑全量）。Python 用例数只按 `def test_` 计数，共 267，与 R11 声称的 267 一致，未实跑。
  - 未跑译名基线脚本，「六 app 缺口 0」未复核，归片 1／5。
  - 未重跑 `sidebar-dupes`、未截「应收」图：属 R6 SL-014 ⑤，归片 5。本片只读查到演示站叫「应收账款」的科目只有 1 个。
  - R3 SL-010 ②③④⑧ 与 TS-014 已被 R6 取代，归片 5。本片只核最终产物的屏数与通过数。
  - 未开浏览器。

## 逐项落地核查

| 意图层依据（源头要什么） | 要求层要求（依据逐条要求） | 定位 | 落地 | 生效否 | 偏差说明 |
|---|---|---|---|---|---|
| AC-015、完成标志总口径 | R3 总纲 §一④：装序不变，`check_app_order` 为真 | 演示站实跑 `check_app_order` | ✅ | 是 | `ok`、`order_ok`、`overrides_ok`、`translation_ok`、`company_checks_ok` 全真，`problems=[]`；装序 7 个 app 与 `sites/apps.txt`、`list-apps` 一致 |
| 同上 | 总纲 §一④：`HDTH` 科目 266 | SELECT `tabAccount` | ✅ | 是 | 266（全库同为 266，只有一个公司） |
| AC-015、AC-008 | 总纲 §一④：`Translation` 0 行；自检返回空清单 | SELECT；`translation_check.run` | ✅ | 是 | 0 行；`run` 打印「译名自检通过」，退出码 0 |
| AC-015 | 总纲 §一④：无测试数据残留 | SELECT 17 类业务表 | ✅ | 是 | GL、SLE、客户、供应商、物料、销售发票、采购发票、日记账、收付款、物料移动、BOM、工单、底稿、结转凭证、CRM 线索、CRM 商机都是 0；`_S6`／`_FCT` 前缀物料 0 |
| AC-015 | 总纲 §一④：有本 Stage 收尾后的新空账基准点；`20261008_211805` 仍在 | `docker/backups/` | ✅ | 是 | `20261013_030125` 的 4 个文件在根目录，也在 `保留-S6收尾/`，md5 两两相同；它是根目录最新一套（`restore.sh:34` 用 `ls -t` 取，目录不参与）；`20261008_211805` 在根目录（4 个）与 `保留-S5R12后/`；旧基准 `20261012_163036` 在 `保留-S6收尾/R7/`（R9 SL-022 ④） |
| R3 SL-010 ⑥ | `tabCash Flow Worksheet` 存在且 0 行 | SELECT；`information_schema` | ✅ | 是 | 0 行；旧表 `tabCash Flow` 不存在；`Patch Log` 有 `s6_rename_cash_flow_worksheet` |
| R3 SL-010 ⑤（AC-004 后半） | 原有入口 diff 在演示站为空 | SELECT `modified` | ✅（旁证） | 是 | 本片按 S5 基准时刻 `2026-10-08 21:18:05` 之后查：非本 app 的 `Desktop Icon` 48 条、`Workspace Sidebar`、`Workspace Sidebar Item` 改动都是 0 行。R5 IT-023 当时以 834 行逐行比对补过证，结论一致 |
| AC-004 前半 | 首页第一个图标是「业务流程」 | SELECT `tabDesktop Icon` | ✅ | 是 | `Business Flow` 的 `idx=-1`，顶层可见图标中 `idx` 最小的就是它；其余图标最小 `idx` 为 0（A8） |
| 完成标志①、AC-001；R9 §一③ | 演示站逐屏核全部屏 `pass=true` | `Spike/P1S6R9-screens/result.json` | ✅ | 是 | 143 条，`pass` 143；`english` 全空；`sidebar_ok` 无 false；与 `screens.json` 的 143 屏一一对上，无缺；截图文件都在 |
| R6 SL-014 ②、R9 SL-022 ③ | 确认框截后 `docstatus` 不变；两个普通取消框 `dialog_kind=confirm` | 同上 | ✅ | 是 | `stage=确认框` 共 33 屏，`docstatus_ok` 全真；`dialog_kind` 有 31 个 confirm、2 个 other，2 个 other 是标了 `kind_expected: cancel_all` 的那两屏 |
| R6 SL-014 ③ | `default_data` 非空的进延迟需求 | `result.json`；S6 概况登记册 | ✅ | 是 | 3 屏（`Nos`／`Qualification`／`general`），已登记为 `SH-P1S6002` |
| 演示站上线的是当前代码 | （隐含）演示站跑的是锁定 HEAD | curl 8000 | ✅ | 是 | `desk_patches.js`、`independent_app_labels.js`、`invoice_list.js`、`opening_ledger.js` 四个文件，8000 发出的与源码 md5 相同 |
| AC-009 | R3 SL-010 ⑦／R6 SL-015 ①／R9 SL-023 ①：全量只增不减，通过与跳过分开报 | — | ⚠️（本片未跑） | — | 按约束没跑 Python。`def test_` 共 267，与 R11 的 267/267 相符。Node：本片在宿主实跑五个 `.cjs`，**71/71**，0 跳过 |
| 版本锁 | R6 IT-001／R9 SL-023 ⑤：上游 status 为空，HEAD 与锁一致 | `docker/apps.json`；七个 app | ✅ | 是 | 七个 HEAD 都等于锁（frappe `c1f1e8ec`、erpnext `12cd563f`、crm `deedce73`、hrms `6f5ac249`、insights `5447f162`、raven `e890308e`、frappe_china `d441e9f`），`status` 全空；`frappe_china` 已推到 `origin/main` |
| ADR-0009；R3 A6；守则「覆盖逐处登记」 | 每处覆盖登一行：覆盖位置（文件:行）／覆盖了什么／上游依赖（文件:行＋锁定 commit）／失效症状／复验法 | `README.md:54-102` | ⚠️ | 是 | **正向核**：30 处上游 文件:行 逐一打开，都对得上（见「自证复核」第 1 行）；5 个锁定 commit 都与 `apps.json` 一致。**格式缺口**：Desk 表的列是「接入点／覆盖文件／作用／适用范围／依据」，不是守则规定的五列；有 6 行的上游依赖缺行号 → **P4-02** |
| 同上（反向核） | `public/js/*.js`、`hooks.py` 里每处替换或包装上游的地方都有登记 | 五个 js 全文、`hooks.py` | ✅ | 是 | `desk_patches.js` 共 12 处：ControlButton、AwesomeBar、datatable Observer、FilterGroup、ListView、Page、QueryReport、时间线 Observer、Dialog、SidebarHeader、StockController、`formatters.Select`；`invoice_list.js` 2 处；`opening_ledger.js` 换掉 JE／PE 按钮 2 处；`independent_app_labels.js` 5 类；`crm.html` 的 `lang`；`update_website_context`；`override_whitelisted_methods` 的 CRM 一条。**以上全部有登记行**。`realtime_check.js` 只加监听，属追加型，不用登记。三条建账 whitelisted 覆盖是 S4 的后端覆盖，不在守则这条的范围内，README「建账胶水层」节有说明 |
| R3 Part4 TS-015 ③ | README `:120` 那句「只维护自身新增…」按现状改写 | `README.md:172` | ✅ | 是 | 已改为「既维护自身新增键，也按覆盖清单有意覆盖官方译名」 |
| 同上 | 现金流四件套一节的目录路径复核 | `README.md:148-158` | ✅ | 是 | 已是 `cash_flow_worksheet/…` |
| 同上（开放查） | README 其余各节与 S6 后的现状一致 | `README.md:3`、`:19` | ❌ | — | `:19` 写「正式业务导航由后续阶段提供」，`:3` 写译名只是「本 app 自有界面词条的中文翻译」，两处都已失真 → **P4-01** |
| 长效信息 #1；需求 §4.3「何时跑」；§七实施者 10 | 守则写「何时跑译名自检」：四个时机、AI 自动跑、命令 | `开发守则.md:99-101` | ✅ | 是 | 四个时机、命令 `bench --site <站> execute frappe_china.translation_check.run` 都写了，与代码一致（`translation_check.py:44` 的 `run`） |
| R3 Part4 TS-015 ④ | 守则补四条：自检形态、改名补丁放 `pre_model_sync`、改 json 必调 `modified`、前端覆盖必登 README | `开发守则.md:107-121` | ✅ | 是 | 四条都在。`pre_model_sync` 与 `patches.txt`、补丁两道幂等判断一致；`modified` 一条与 `business_flow.json` 的 `modified` 机制一致。「自检形态」一条把 `realtime_check.py` 举为同形态的例子，但它并不符合 → **P4-07** |
| R6 TS-024 ③ | 守则补「批量写 csv 前后跑质量守卫、不取 `zh_TW.po`」 | `开发守则.md:103` | ✅ | 是 | `ALLOW`、`QUALITY_EXCEPTIONS` 两个名字与 `test_translation_quality.py:22,70` 一致 |
| R9 SL-023 ④（A28） | 守则补命名约定 `SOURCE`／`SOURCES` | `开发守则.md:105` | ✅ | 是 | 与 `test_translations.py:112`（Python 用 `SOURCES?$`）、`:117`（JS 用 `\w*sources?\s*=`）一致（IT-053 已修） |
| 长效信息 #2 | 项目概况「数据模型」`Cash Flow` → `Cash Flow Worksheet` | `项目概况.md:123` | ✅ | 是 | — |
| 长效信息 #2 | 「UI 路由结构」里「没有导航入口」按实况改写 | `项目概况.md:129` | ✅ | 是 | 与演示站 `Business Flow` 图标、侧栏一致 |
| R3 Part4 TS-015 ④ | 能力表加「译名自检」「业务流程导航」 | `项目概况.md:105-106` | ✅ | 是 | 「7 个分节、51 个入口」：`business_flow.json` 共 58 项，Section Break 7 个，入口 51 个，对上；含 4 个 URL 项（`/crm/leads`、`/crm/deals`、`/crm/dashboard`、`/raven`） |
| R3 Part4 TS-015 ④；R6／R9 TS-024／037 ③ | 「开发环境」写演示站状态与备份基准点，含 `保留-S6收尾/`，并写明 `restore.sh` 不带参数取哪个 | `项目概况.md:68-88` | ✅（另有观察） | 是 | 演示站状态逐项实查都对：scheduler 关、销项税模板 5 个、进项 7 个、报销类型 5 个、bot `ERX 分析助手`、各类单据 0、`Translation` 0。基准点与 `restore.sh` 的说法正确。根目录另有 S6 期间的 `20261010_174959`、`20261010_220310` 两套没列，`保留-S6收尾/` 里也有一套 `20261010_220310` 未说明 → **P4-09** |
| R3 Part4 TS-015 ④ | 「已知限制」译名条按本 Stage 结果改写：已改造的部分，**仍在演示线外未处理的撞名属 DF-002** | `项目概况.md:188` | ⚠️ | — | 已改造的部分写了，**DF-002 那一半没写**（全文搜 `DF-002` 0 命中）→ **P4-03** |
| 契约 §4 逐出、R7／R10「同节其余子条仍成立」 | 译名条下各子条与现状一致 | `项目概况.md:189-192` | ❌ | — | 有悬空指代、过期数字，「保留 S3 中性词」与 DEC-080／036 相反 → **P4-04** |
| 契约 §4（Stage 收口全量查） | 被 S6 改得失准的其余常驻内容 | `项目概况.md:53`、`:186-187`、`:201` | ⚠️ | — | 模块职责、「不刷新」条、延迟需求开放视图三处 → **P4-05** |
| R3 Part4 TS-015 ⑤；R4 Part4 回执「交 Stage 收口」节 | HT-014、HT-008 列出，交 Stage 收口判去向 | R4 Part4 回执 `:72-79` | ⚠️ | — | 回执里列了（R5 IT-030 补）。但 S6 概况的长效信息表与收口清单都没有 HT-014，路线文档 §四 S7 也没有，收口时会漏掉 → **P4-06**。HT-008 已由 R7 实测，7 个预填屏 `sidebar_ok` 为真，可以关 |
| 需求 §4.10、RW-09；R6 SL-015 ④ | 工作量实耗与增量交 Stage 收口回写 | R7 回执「工作量」节；路线文档 §四 S6 | ⚠️（待收口） | — | 路线文档仍写 11.25–18 人日。R10 回执没有工作量节（R9 没要求）。唯一的口径是 R7 回执的定性说法：截至 R7 用了 5 个日历日、7 个 Round、已超上限。IT-049 已裁为收口时定，见交接摘要，不另计发现 |
| docker 文档 | R11 IT-059：`docker/README.md` 补 6787 实时通道两步 | `docker/README.md:154-159` | ✅ | 是 | `socketio_client.js:120-127`（`get_host` 的 `dev_server` 分支）与 `realtime/utils.js:4-15`（按 origin 回访）对上；`it018-run.sh` 受版本管理 |
| 长效信息 #1、#2 的状态 | 概况与交接写「待移交」 | S6 概况 `:144-145`、`:85` | ⚠️ | — | 两条实际已在 R4／R5 落进常驻文件（见上），概况还写「待移交」→ **P4-08** |

## 业务规则合规核

| 规则条款 | 本片改动是否涉及 | 结论 | 备注 |
|---|---|---|---|
| BR-002（法定报表；列头不得被翻译） | 间接涉及（需求 §4.11 唯一触点） | 合规 | `translation_check.find_problems` 第 4 项调 `validate_legal_labels()`；演示站自检通过，即没有法定列头被翻译 |
| BR-001（小企业会计准则科目表） | 只涉及最终状态的科目数 | 合规 | 演示站 `HDTH` 科目 266，与准则科目表节点数一致 |
| BR-003～007 | 不涉及 | — | 本片是收尾、常驻文件与演示站状态核查，没有产品语义改动；S6 没有新增或变更业务规则（需求 §4.11），`业务规则.md` 在 S6 无提交，与之一致 |

## 集成点登记（交接摘要）

**本片暴露（给收口与他片）**
- 演示站最终状态的实测值：`Translation` 0；17 类业务表 0；科目 266；`check_app_order` 全真；自检通过；`Business Flow` 的 `idx=-1`；S5 基准时刻之后非本 app 导航三表的改动 0 行；8000 发出的四个 js 与 HEAD md5 一致；基准点 `20261013_030125` 在两处、md5 相同。
- README 覆盖登记：正向 30 处上游 文件:行 都对，反向核无漏登；只有格式与缺行号问题（P4-02）。片 2／3（裁渲染点、开账跳转、Desk 补丁）判「登记齐否」时可直接用这个结论。
- 逐屏核产物：143/143，确认框 33／`docstatus_ok` 33，`sidebar_ok` 全真。片 5（R6 SL-014、R9 SL-022）可用作最终状态的对照。
- Node 71/71（本片实跑）。

**本片依赖（需他片或收口提供）**
- 全量 Python 用例实跑数：主会话。
- 「六 app 缺口 0」「批量档抽检 97/100」：片 1／片 5（项目概况 `:188` 引了这两个数，本片未复核）。
- §4.9 行到屏 id 的映射是否无空行：片 5。
- R11 清单外「`frappe.form.formatters.Data` 无可选链保护」（`desk_patches.js:238`）：属 SL-006／TS-008 的代码，交片 2 判是否计为发现。本片只确认它在 README `:75` 有登记行。

**交 Stage 收口（流程中枢第 8 步）**
- 长效信息 #1、#2 已在常驻文件里，收口时勾掉即可，不必再写（P4-08）。
- HT-014 补进收口清单，去向是路线文档 §四 S7 执行清单（P4-06）。
- RW-09：路线文档 S6 工作量还是 11.25–18。实耗口径（日历日 10-08～10-13、Round 数 12、折算当量）由收口定；R10、R11 都没给数。
- 契约 §4 全量查逐出：P4-04、P4-05 列出的失真点可以直接当这次逐出的输入。

**事件**：本片不发出也不消费 SSE／realtime 事件。

## 自证复核

| 被审产物声称 | 实际复核结果 | 一致否 |
|---|---|---|
| README 登记的上游 文件:行（R10 TS-037、R11 IT-054 修后） | 30 处都对得上锁定源码。例：`filter_list.js:144-145` 的 title 模板；`list_view.js:763`；`page.js:631,644-646`；`query_report.js:1379` 的 `prepare_columns`；`stock_controller.js:114-134`；`crm_fields_layout.py:113`／`:180-189`；`SidePanelLayout.vue:157`；`ListFooter.vue:12-22`；`dashboard.py:971`；`Profile.tsx:28`；`useSetAvailability.ts:9`；`general_ledger.py:560,562`；`rowmanager.js:360`（datatable 1.20.7）。只有 `journal_entry.js:79` 是 `if (docstatus > 0)`，`add_custom_button` 在 `:80`，差一行，不影响 | 一致 |
| R10「演示站 143/143、`sidebar_ok` 全真」 | 143/143；`sidebar_ok` 无 false | 一致 |
| R11 IT-058 修后「33 个确认框、`docstatus` 全不变」 | 33；`docstatus_ok` 33 个为真 | 一致 |
| R10／R11「清洁基准 `20261013_030125`，根目录最新一套」 | 是；两份 md5 相同 | 一致 |
| R11「`apps.json` 锁推到 `d441e9f`，上游 HEAD 等于锁」 | 七个 app 都一致，`status` 全空，`origin/main` 是 `d441e9f` | 一致 |
| R11「Node 71/71」 | 本片实跑 71/71 | 一致 |
| R7、R10 TS-024／037「项目概况译名条同节其余子条（撞名口径、收付款方向）仍成立，未动」 | 不成立：`:190` 写「本站点 `sites/apps.txt` 只装 frappe＋erpnext」，实际装了 7 个；「747 组／143 组」已被路线文档 v1.9 的 905 组取代；`:192` 写「保留 S3 中性词」，与 DEC-080／036 相反 | **不一致** → P4-04 |
| 项目概况「7 个分节、51 个入口」 | json 58 项 − 7 个分节 = 51 | 一致 |
| 项目概况演示站状态（scheduler 关、税模板 5／7、报销类型 5、bot、全 0） | 逐项 SELECT 都对 | 一致 |
| S6 概况长效信息 #1、#2「待移交」 | 实际已在 `开发守则.md:99-101`、`项目概况.md:123,129` | **不一致**（已做却仍标待做）→ P4-08 |
| 开发守则「自检函数形态，如 `translation_check.py`、`realtime_check.py`」 | `realtime_check.py` 没有 `find_problems`，`run` 返回 dict 而非问题清单（`:46-93`） | **不一致** → P4-07 |

## 问题清单

| # | 严重程度 | 定位 | 问题描述 | 违背的标准/意图 | 建议 | 建议档位 | 待裁决点 | 状态 |
|---|---|---|---|---|---|---|---|---|
| P4-01 | 低 | `frappe_china/README.md:3`、`:19` | `:19` 写 `cn_tax.json` 是空侧栏、「正式业务导航由后续阶段提供」。但 S6 已提供 `workspace_sidebar/business_flow.json` 与 `desktop_icon/business_flow.json`，「模块边界」节两者都没提。`:3` 把译名写成「本 app 自有界面词条的中文翻译」，但现在 csv 约 5800 行，补的是六个 app 的缺口，并有意覆盖官方。TS-015 第 3 步只点名改 `:120`，这两处漏了 | 常驻文件契约 §5.5「发现失真即修」（README 随 app 走，是覆盖登记的宿主）；需求 §4.6 | `:19` 改为写明自有 `Business Flow` 图标与侧栏（指向两个 json，与 `cn_tax.json` 分工）；`:3` 改为「六个 app 界面缺口的补译与按覆盖清单的有意覆盖」 | `本Session修` | — | 待裁决 |
| P4-02 | 低 | `开发守则.md:121`；`README.md:56-67`、`:58`、`:59`、`:81`、`:84`、`:86` | 守则规定登记五列：覆盖位置（文件:行）／覆盖了什么／上游依赖（文件:行＋锁定 commit）／失效症状／复验法。README 的 Desk 表是另一套列（接入点／覆盖文件／作用／适用范围／依据），后四项挤在「作用」列里；IT-054 起覆盖位置改用函数名锚点，守则没跟着改。另有 6 行的上游依赖缺行号：ControlButton 只写 `button.js`（应为 `:78` `set_label`）；AwesomeBar 写「`desktop.html` 与 `setup_awesomebar`」（应为 `desktop.html:13`、`desktop.js:621`）；CRM 入口行 `www/crm.html`（应为 `:2`）；Raven 行 `www/raven.html`、`main.tsx`；Insights 行 `www/insights.html`、`DemoDataBanner.vue`，都没有行号 | ADR-0009；R3 A6；守则「desk 与独立前端的覆盖逐处登记」 | ① 守则那句改为「覆盖位置（文件＋函数名，或文件:行）」，与 IT-054 的裁决一致；② 补上 6 行的上游行号；③ 列格式维持现状还是统一成五列，交用户定 | `本Session修` | ③ README Desk 表要不要统一成守则的五列 | 待裁决 |
| P4-03 | 低 | `项目概况.md:188` | R3 Part4 TS-015 第 4 步明文要求译名条写「仍在演示线外未处理的撞名属 DF-002」。现状只写了已改造的部分，全文搜 `DF-002` 为 0。合并字典撞名共 905 组，演示线外的部分仍未处理，这是真实存在的已知限制，没写进来 | 要求层：Part4 TS-015 ④；常驻文件契约「已知限制」节的职责 | 在译名条末补一句：演示线外的撞名未逐组处理，属 DF-002（S8G，全量精确档）；同时并掉 `:190` 的旧数字（见 P4-04） | `本Session修` | — | 待裁决 |
| P4-04 | 低 | `项目概况.md:189-192` | 译名条的子条在 S6 改写母条后失真：① `:189`「`context` 解决不了**上述前两条**」——母条已不再列 Setup／Settings、应收两条，指代悬空；② `:190`「本站点 `sites/apps.txt` 只装 frappe＋erpnext」与实际 7 个 app 不符，「747 组／143 组」已被路线文档 §四 S6 第 3 条的 905 组取代；③ `:192`「四张共享子表那一处无解，**保留 S3 中性词**」与事实相反：S3 中性词（未结／已付讫）在 DEC-080 时就没被采纳，无 context 的 `Unpaid` 按 DEC-036 显示官方「未付」（csv 只有 `Unpaid`／`Paid` 带 context 的 4 行，见 `zh.csv:3422-3423,5236-5237`；官方 `zh.po:59192` 为「未付」）。同句「`Unpaid` → 未付款」也与官方现值「未付」不符（DEC-036 已指出这是 S3 记错）。另 `:188` 里的「S6 R7 整批重译过，抽检 97 条可用」属过程信息。R7、R10 回执写这些子条「仍成立，未动」，与实际不符 | 常驻文件契约 §1 判据 A、§4「所述现状已被改掉 → 改写」、§5.1；DEC-036、DEC-080 | 子条改写为现状：撞名形态的说明保留，指代改为具体源词；口径改为七 app 合并字典 905 组，演示线已逐组判；`:192` 改为「共享子表那一处没有 context，显示官方『未付』『已付款』（DEC-036）」；过程句移到 S6 概况 | `本Session修` | 现在改，还是并入 Stage 收口时的契约 §4 全量逐出 | 待裁决 |
| P4-05 | 低 | `项目概况.md:53`、`:186`、`:201` | 被 S6 改得失准、而 S6 没有一次写入落在这里的三处：① 模块结构表 `frappe_china` 行「现有：…（S4 建）…（S5 建）。其余各块由后续 Stage 加」，没列 S6 新增的 `translation_check.py`、`website_translation.py`、`crm_sidepanel.py`、`public/js/` 前端补丁、`workspace_sidebar`／`desktop_icon`；② `:186`「前端多处改动后不刷新即不显示…客户演示前必须闭环」，S6 TS-013（AC-013）已逐例复现并处置（例 2 按 LG-073 不修）；③ 延迟需求开放视图写 `PH-P1001`、`PH-P1002` 唤醒已触发、演示前必做，S6 已承接 | 常驻文件契约 §4 触发点 2（Stage 收口全量查）；判据 A | 收口时改写：① 补 S6 的模块；② 改为六例的结论与仍未解决的部分（原有侧栏的树形路由是否仍空白，本片未核）；③ 随 P1 概况登记册里 S6 承接各条的状态一并更新（本片抽查 4 条，仍是「延期」） | `本Session修` | 现在改，还是并入 Stage 收口 | 待裁决 |
| P4-06 | 低 | S6 概况「本 Stage 的长效信息」`:142-145` 与 `:85` 收口清单；路线文档 §四 S7 | R3 Part4 TS-015 第 5 步要把 HT-014（侧栏 URL 项 `/crm/…`、`/raven` 对非 Administrator 是否可见）交 Stage 收口判去向。R4 Part4 回执 `:76-79` 列了，建议去向是路线文档 S7。但 S6 概况长效信息表与收口清单都没有它，路线文档 S7 也搜不到。收口照清单做就会漏掉。SB IT-027 只核了非管理员的 CRM 页面渲染，没核 desk 侧栏 URL 项是否可见 | 要求层：Part4 TS-015 ⑤；sharding「暴露什么」不应丢；需求 §七演示者流程（演示用户归 S7） | 在 S6 概况长效信息表加第 3 条「HT-014 → 路线文档 §四 S7 执行清单」，并写进 `:85` 的收口清单；HT-008 注明 R7 已实测通过、关闭 | `本Session修` | — | 待裁决 |
| P4-07 | 观察 | `开发守则.md:109` | 「站点自检函数的形态」把 `realtime_check.py` 举为同形态的例子。实际上它没有 `find_problems()`，`run()` 返回 dict（`ok`／`token`／`reason`），也不返回问题清单（`realtime_check.py:46-93`）。照这个例子写新自检的人会被误导 | 常驻文件契约 §5.5 | 例子只留 `translation_check.py`；或注明 `realtime_check` 是要等页面回执的另一类，不适用本形态 | `本Session修` | — | 待裁决 |
| P4-08 | 观察 | S6 概况 `:144-145`；R12 交接 `:85` | 长效信息 #1（守则「何时跑自检」）在 R4 已写进 `开发守则.md:99-101`，#2（数据模型、UI 路由）在 R5 已写进 `项目概况.md:123,129`。概况还标「待移交」，收口清单也写「第 1、2 条移交」，容易让收口的人重写一遍，写出重复段落 | 契约 §5.1「改写优先于追加」 | 收口时把两条标为「已在 R4／R5 落地」并删行，不再写 | `延迟或不修` | — | 待裁决 |
| P4-09 | 观察 | `项目概况.md:69-88`；`docker/backups/` | 备份列表没列根目录的 `20261010_174959`、`20261010_220310`（S6 R4 期间所出）；`保留-S6收尾/` 里还有一套 `20261010_220310`，也没有说明。`restore.sh` 默认取最新一套，取到的仍是 `20261013_030125`，没有误恢复的风险 | 契约「开发环境」现状描述完整性 | 补两行「S6 R4 中途备份，仅供回溯」，或从 `保留-S6收尾/` 移走那套 | `延迟或不修` | — | 待裁决 |

（严重程度：高＝阻断或根因偏离 · 中＝需修 · 低＝技术债 · 观察＝可容许的偏差，留个记录）

## 本片盲区自述

- **定级在边界上的**：P4-04 在「低／中」之间。`:192` 的「保留 S3 中性词」是对用户可见结果的错误陈述，下一个读项目概况的 Stage 可能据此去找「未结」一词；但它不影响代码与演示，所以定为低。P4-06 若 S7 演示用户不是 Administrator，会直接关系到演示时侧栏里 CRM／Raven 入口的显隐，可以改判为中。
- **没往这些方向找**：
  - 没核 erpnext 原有侧栏的树形 DocType 现在是否仍落到列表路由。P4-05 ② 怎么改写取决于它，本片未验。
  - 没核 CRM `node_modules` 里的 frappe-ui 版本是否等于 `package.json` 锁的 `1.0.0-beta.29`。README 的「frappe-ui 随 CRM 锁定」只按 package.json 判断。
  - HT-014 本身没读码，`workspace_sidebar.py:96` 只看到 URL 项不参与模块推断，可见性的判定未读完。
  - 项目概况 S6 之前写的各段（S1～S5 内容）没逐句核，只核了 S6 改过的行及与 S6 结果直接相关的行。
- **拿不准处**：P4-02 里 README Desk 表的列格式与守则不一致，算不算发现。IT-054 用户已追认用函数名锚点，内容上五要素大多在「作用」列里都能找到，所以只把守则与实践不一致、以及 6 处缺行号判为发现，列格式本身留作待裁决点，没有单列一条。
