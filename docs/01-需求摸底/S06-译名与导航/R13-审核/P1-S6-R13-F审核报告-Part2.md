# 审核报告 Part2（片 2：前端补丁、看板覆盖与用例判别力）

**对象**：`frappe_china` `d441e9f..1d0697e` 中属本片的改动（FD-001、FD-002、FD-016、FD-019 为 SB 修；FD-018、FD-020 为 R12 当场修）
**审核标准**：R12 F 审核报告的「建议」与「用户裁决」、R3 Part3／R6／R9 开发方案的任务要求、`docs/开发守则.md`（§「判据必须能区分它要区分的两种情形」「desk 与独立前端的覆盖逐处登记」）
**纪律**：`bricks/audit.md`＋`F-codeAudit-plannedDev-audit.md`（独立第三方视角，不信被审对象自证）
**探针**：`Spike/P1S6R13-F/p2/`（`mutate.cjs`／`.out`、`rename_guard_mutation.py`／`.out`、`nav_compare.py`／`.out`、`nav_test_mutation.py`／`.out`、`nav_label_dup.py`／`.out`、`master_po_scan.py`／`.out`、`timesheet_terms_count.py`／`.out`、`pe_menu_probe.cjs`／`.out`）

## 覆盖自证

**实际查了**：

- 六项改动的 diff 全读：`git diff d441e9f..1d0697e` 与 `68476a3..1d0697e` 两段分开读，确认哪些属 SB、哪些属 R12 当场修。涉及文件 `public/js/opening_ledger.js`、`public/js/desk_patches.js`、`dashboards.py`（新建）、`hooks.py`、`tests/test_opening_ledger.cjs`、`tests/test_dashboards.py`（新建）、`tests/test_invoice_status.cjs`（新建）、`tests/test_desk_patches.cjs`、`tests/test_cash_flow_rename.py`、`tests/test_named_terms.py`、`tests/test_business_flow_navigation.py`、`README.md`，以及主仓库 `Spike/P1S6R6-screen-check.js`、`Spike/P1S6R9/screens-build.py`、`Spike/P1S6R9-screens.json`。
- 上游源码逐处核对（锁定提交 frappe `c1f1e8e`、erpnext `12cd563`）：`form.js:1540-1549,1562-1583`、`page.js:622-684`（含 `add_menu_item`／`add_dropdown_item`／`is_in_group_button_dropdown`）、`payment_entry.js:423-441`、`journal_entry.js:78-95`、`model/meta.py:755-775`（含 `add_doctype_links` 的执行次序）、`workstation_dashboard.py:8`、`desk/form/meta.py:33-70,233-234`、`boot.py:442-510`、`form/templates/form_links.html:8`、`form/dashboard.js:248-285`、`base_timeline.js:10-30,117-140`、`form_timeline.js:95-115,160-520`、`version_timeline_content_builder.js:411-420`、`utils/utils.js:246-273`、`formatters.js:40-54`、`list_view.js:755-766`、`stock_controller.js:114-134`、`desktop.js:45-70`、`desktop_icon.py:185-205`、`redis_wrapper.py:79-99,518-560`、六个 app 的 `locale/*.po`（`Master`／`Master Data` 全语言扫）。
- 实跑：宿主 Node 24.13.1 `node --test frappe_china/tests/*.cjs`（两次，仓库内与仓库外副本）；仓库外副本上 18 个前端变异；宿主桩上 3 个改名补丁守卫变异；侧栏 json 的 7 个结构变异；逐屏核静态校验 `SCREENS_VALIDATE_ONLY=1`；R12 片 3 的 happy-dom 复现脚本 `pe_button_repro.cjs` 复跑；新写 `pe_menu_probe.cjs` 补查窄屏菜单两条项各走哪个回调。
- 读了 R12 报告该六项的全文行（含 Part2、Part3、Part6 的原始分片条目）与 SB 回执对应行、回执的「复验结果」「偏离与暂停」「复核建议」。

**跳过及原因**：

- 不跑 `bench run-tests`（主会话在跑全量），改读 `Spike/P1S6R13-F/full-regression.log` 与 `Spike/P1S6R12-SB/full-regression.log` 核数；两站点未做任何写操作，`test_dashboards`、`test_business_flow_navigation` 的容器内实跑结果只能取日志。
- 未开浏览器，未重跑逐屏核实页（约束所限）；FD-002 与 FD-019 的实页证据只核了 SB 留档的 `result.json` 与截图。
- 未复核本片之外的 FD（FD-008／009／010／012／013／017／024 属其它片）。

## 逐项复核

| FD 号 | R12 要求与裁决 | 落地位置 | 落地／生效／根因三层 | 复算结果 | 结论 |
|---|---|---|---|---|---|
| **FD-001** | 建议：PE 分支删除时不带分组；Node 桩照上游把 `fa fa-` 分组置空；改写 README `:102`；测试站造开账 PE 实点。裁决「按建议：新Session修」 | `public/js/opening_ledger.js:7-10`（`undefined`）、`tests/test_opening_ledger.cjs:13-43`、`README.md:109` | 落地 ✅ 三处都在。生效 ✅ 上游 `form.js:1542` 对 `fa fa-` 置空、`page.js:668-684` 不置空，两侧逐行核过，补丁按「无分组」寻址与上游一致。根因 ✅ 原症状（点「总账」不带 `show_opening_entries`）消失 | 复跑 R12 的 happy-dom 复现：PE 工具栏 1 个按钮、点击后 `show_opening_entries=1`；JE 分组内 1 个、参数含 `finance_book`。桩的四个变异（PE 回到 `fa fa-table`／JE 也不带分组／去掉 `remove_custom_button`／去掉 `show_opening_entries`）全部变红（fail=2／2／4／4） | ✅ |
| **FD-002** | 裁决选路线 ①：`override_doctype_dashboards` 换工位看板分组标题，`Master` 继续给称呼用；补一屏「工位表单·关联页签」进逐屏核 | `dashboards.py`、`hooks.py:256-258`、`tests/test_dashboards.py`、`README.md:97-101`、`Spike/P1S6R6-screen-check.js`（`forbid`／`require`）、`Spike/P1S6R9-screens.json`（144 屏） | 落地 ✅。生效 ✅ `meta.py:772-773` 确为追加型（逐个 hook 调用、结果传给下一个），L3 定级成立；hrms 的 `override_doctype_dashboards` 不含 Workstation，无叠加冲突；按 items 集合认组在上游 `workstation_dashboard.py:8` 的 `["BOM","Routing","Operation"]` 上命中。根因 ✅ zh 会话下该组标题不再是「少爷」 | `Master Data` 在六个 app 的源码、json、全部 po 里 0 处（只本 app csv `:2889`），占用核查复算一致；逐屏核静态校验 144 屏 `valid`，`forbid`／`require` 只新屏使用、其余 143 屏判定路径不变（`screen-check.js:288-297` 仅在该字段存在时追加判定）。失效登记在 README，但漏一条触发路径（见 P2-03）；非中文会话有退化（见 P2-02） | ⚠ |
| **FD-016 ①** | 新装站用例同时 patch `frappe.db.exists` | `tests/test_cash_flow_rename.py:9-13` | 三层 ✅。补丁两道守卫（`table_exists` 与 `exists`）各自被一条用例唯一覆盖 | 宿主桩变异：删守卫 1 → `new_install` 红；删守卫 2 → `already_renamed` 红；两条都删 → 两条都红。另加 patch 了 `reload_doc`，防变异时真调框架 | ✅ |
| **FD-016 ②** | `assertGreaterEqual(len(terms), 29)`；po 路径用 `frappe.get_app_path` | `tests/test_named_terms.py:104-106,122-128` | 三层 ✅ 空转已堵：路径取不到即 0 条、断言先红 | 独立复算锁定版本下的条数：erpnext 22＋hrms 7＝29（raven 无 zh.po，frappe／crm／insights 该词 0 条），与断言下限严格相等，不是宽松下限 | ✅ |
| **FD-016 ③** | 把片 2 的沙箱脚本改成正式 Node 用例（SL-006 三条出路） | `tests/test_invoice_status.cjs`（12 条） | 三层 ✅。三条出路（列表徽标、状态筛选、表单 Select）各有用例，桩照上游 `sales_invoice_list.js:30`、`purchase_invoice_list.js:20-31`、`formatters.js:52-54` 的形状 | 仓库外副本 10 个变异全部被杀：徽标去 context／判定放宽到 `On Hold`／去幂等标记；筛选不补 context／不清 `last_options`／不调 `set_options`／不委托原 `onload`；Select 去 `df.parent`／去 `doc.doctype` 回退 | ✅ |
| **FD-016 ④** | 补 51 项条目清单、中文不重名、图标 label＝侧栏 title 断言与库存类开账 Node 用例 | `tests/test_business_flow_navigation.py:14-102`、`tests/test_invoice_status.cjs`（库存类 6 条） | 落地 ✅。生效 ⚠ `EXPECTED_LINKS` 不是同源自证（独立核过它与 R3 Part3 TS-010 第 2 步方案表逐项相等），但不记分节归属，条目跨分节移动不变红（P2-01）。根因 ✅ 库存类开账已有 Node 覆盖 | 侧栏 json 7 个结构变异：删条目／换序／改 `link_to`／URL 改 DocType／改 title／改 module 六个被杀，「分节断点后移一位」存活；跨类型中文重名独立复算 58 个标签全不重名；`desktop.js:56` 确以 `label.toLowerCase()` 取侧栏，`icon.label == sidebar.title` 的断言有真实依据 | ⚠ |
| **FD-018** | `html.replace(wrong, () => right)`，Node 用例补含 `$&` 的 label | `public/js/desk_patches.js:107-111`、`tests/test_desk_patches.cjs:101-108` | 三层 ✅。桩的 `translate` 改用 split／join 代入参数，不会自己吃掉 `$&`，反例才有意义 | 变异「replacer 回到字符串」→ 1 条红（`sort title with $& …`）；上游 `list_view.js:762-763` 的 title 字面量与补丁匹配串一致 | ✅ |
| **FD-019** | 选择器排除卡片 `:not(.frappe-card)`，补评论卡片不变的反例 | `public/js/desk_patches.js:158-163`、`tests/test_desk_patches.cjs:289-370`、`README.md:67` | 落地 ✅。生效 ✅ 上游 `base_timeline.js:136` 把 `frappe-card` 加在 `.timeline-content` 自身，`:not` 挂的层级正确。根因 ✅ 评论卡片内用户加粗的 `null` 不再被改 | 变异「去掉 `:not`」与「`:not` 挂到 `.new-timeline`」各杀 2 条用例。漏杀面核查：修改记录项（`form_timeline.js` 的 version／share／assignment／info／attachment／milestone／like／workflow）都不带 `is_card`，不会被 `:not` 误排除；`is_card:true` 的只有通信、自动消息、评论与 erpnext 通话记录（`call_log.py:220`），都是用户内容，排除正确；文档邮件地址那条（`form_timeline.js:104`）非卡片且文字不是 `null`，不受影响 | ✅ |
| **FD-020** | 可选链取值，类型不对时 `console.warn` 后跳过；补缺接点 Node 用例 | `public/js/desk_patches.js:241-252`、`tests/test_desk_patches.cjs:529-535` | 三层 ✅ 与同文件 A23 其它补丁同形 | 变异「回到 `frappe.form.formatters`」与「删掉告警」各杀 1 条。另跑三种缺接点上下文：`frappe` 为空对象、`frappe.form` 缺失都不抛；仅「完全无 `frappe` 全局」仍抛 `ReferenceError`（`desk_patches.js:241` 直接写 `frappe.form?`，不是 `typeof frappe`），但 `app_include_js` 的下发场景不存在该情形，记为盲区不作发现 | ✅ |

**方案外夹带**：本片六项涉及的 diff 逐行读过，没有不属上述 FD 的改动。`68476a3..1d0697e` 段里 `desk_patches.js` 只有 FD-019 一处、`hooks.py` 只有 `override_doctype_dashboards` 一处、`test_desk_patches.cjs` 只有 FD-019 的桩与两条断言改动。逐屏核工具加 `forbid`／`require` 属工具扩展（回执已自报偏离 2），实现确为「不写则不查」，不构成夹带。

**已裁延迟项未重开**：FD-022（窄屏菜单残留一条原生「会计凭证」，裁为延迟或不修）本次核过范围未变——`pe_menu_probe.cjs` 实测 JE 与 PE 的菜单都是 2 条、第一条走原生回调；修前 PE 也是 2 条（`form.js:1540-1542` 先把 `fa fa-` 分组置空，再由 `page.js:631-632` 无条件追加菜单项），本修既未扩大也未缩小该缺口，不作新发现。

## 自证复核

| 被审产物声称 | 实际复核结果 | 一致否 |
|---|---|---|
| SB 回执：`node --test frappe_china/tests/*.cjs` **86/86** | 宿主 Node 24.13.1 实跑两次（仓库内、仓库外副本）：`tests 86 / pass 86 / fail 0` | 一致 |
| SB 回执：FD-016「5 个前端变异全被杀」 | 本步另设 18 个变异（含那 5 个的等价变体），18/18 全被杀；侧栏 json 另设 7 个结构变异，6 杀 1 存活（P2-01） | 一致，但变异集不足以覆盖「分节归属」 |
| SB 回执：逐屏核「只有新屏用到，其余 143 屏行为不变」 | 读 `screen-check.js:288-297` 与 `P1S6R9-screens.json`：只有 `05-workstation-connections` 带 `forbid`／`require`；静态校验 144 屏 `valid` | 一致 |
| SB 回执：`Master Data` 在六个上游 app 源码与 po 里 0 处 | 独立全扫 py／js／json／vue／ts／tsx／html 与全部 po：0 处；`Master Data` 在任何语言的 po 里都没有译文 | 一致（但由此产生 P2-02） |
| SB 回执：`EXPECTED_LINKS` 由当前 json 生成 | 确认不止于此：它与 R3 Part3 TS-010 第 2 步方案表的 51 行三列逐项相等（独立脚本比对），不是「拿 json 自证 json」 | 一致，且比声称更强 |
| SB 回执：FD-016 ②「锁定版本下为 29 条」 | 独立复算 29 条（erpnext 22＋hrms 7） | 一致 |
| SB 回执：FD-002「按 items 认分组，上游改了 items 就不再命中，失效症状已登记在 README」 | README 确有该句；但使 items 变化的还有本站自定义 DocType Link（`meta.py:768` 在 hooks 之前并入），README 未登记 | **不完全一致**（见 P2-03） |
| SB 回执复验表：FD-002「实页接钩 `pass=true`、`forbidden=[]`、`missing_required=[]`」 | 读 `Spike/P1S6R12-SB/fd002/{unhooked,hooked}/result.json` 与截图：撤钩 `forbidden=[少爷]`、接钩全空，截图可见「基础资料／交易」两组 | 一致 |
| SB 回执：`require` 的作用是「防该区域没渲染而空过」 | 该屏 `require` 的两个词（基础资料、工艺路线）在左侧业务流程侧栏即出现（截图可见），取词范围是整个 body（该屏未设 `extract_root`），所以挡不住「关联页签没渲染」 | **不一致**（见 P2-04；实际由该屏 `steps.wait_for` 的 `.form-dashboard .document-link` 兜住） |

## 新发现

| 编号 | 严重程度 | 定位 | 问题描述 | 证据 | 建议 | 建议档位 | 待裁决点 |
|---|---|---|---|---|---|---|---|
| P2-01 | 低 | `frappe_china/tests/test_business_flow_navigation.py:14-66,81-85` | `EXPECTED_LINKS` 只记（label, link_type, link_to/url），不记条目属哪个分节。把 `Selling` 的分节断点往后移一位（`Quotation` 落进「基础资料」组）时，五条断言全绿——`links_match_plan` 的列表顺序没变、分节顺序没变、URL 计数没变。R3 Part3 的方案表本身是带分节列的，FD-016 ④ 的用意是「核 51 项清单」 | `Spike/P1S6R13-F/p2/nav_test_mutation.out`：7 个变异里 6 杀 1 存活，存活的是「分节断点后移一位」 | 断言改成四元组 `(section, label, link_type, target)`，`EXPECTED_LINKS` 补分节列（方案表已有，`nav_compare.py` 已验证四列也逐项相等） | `本Session修` | 是否现在补（只动测试文件，不动产品代码） |
| P2-02 | 低 | `frappe_china/dashboards.py:14-19` | 覆盖没有语言守卫，对所有语言都把分组标题的键从 `Master` 换成 `Master Data`。`Master Data` 在六个 app 的任何 po 里都没有译文，而 `Master` 在 18 种语言里有译文（de `Meister`、ru `Мастер`、th `ข้อมูลหลัก`、nl `Stam`、zh.po `主表`…）。所以德语等会话的工位「关联」页签标题从已译词退回英文 `Master Data`。本项目只交付中文，影响面在演示与验收之外，但这是本修引入的新行为，且 `test_english_session` 只断言了 en 这一种 | `Spike/P1S6R13-F/p2/master_po_scan.out`（18 条 `Master` 译文、0 条 `Master Data` 译文）；`dashboards.py` 无 `frappe.local.lang` 判断，对比同仓 `crm_sidepanel.py:20`、`website_translation.py:22` 都带 zh 守卫 | 二选一：① 加 `if frappe.local.lang != "zh": return data`（与本仓其它覆盖同形），`test_dashboards` 的 `test_english_session` 随之改成「en 下仍是 `Master`」；② 接受，并在 README 该行的「失效症状／影响面」里写明非中文会话会显示未译的 `Master Data` | `本Session修` | 走 ① 加语言守卫，还是 ② 接受并登记 |
| P2-03 | 低 | `frappe_china/README.md:101`；上游 `frappe/model/meta.py:768,771-773,800-814` | README 的失效条件只写「上游改了 items 时本覆盖不再命中」。实际还有一条本站触发路径：`add_doctype_links` 在 hooks **之前**执行，它按 `_(group.label) == _(link.group)` 匹配，zh 下 `_("Master")`＝「少爷」，所以站上用 Customize Form 给 Workstation 加一条 `group="Master"` 的 DocType Link，会把该 DocType 并进 items，`WORKSTATION_MASTER_ITEMS` 的集合相等判定随即失配，标题回到「少爷」。按守则「覆盖逐处登记」要求失效症状可自查，这条该登 | 读 `meta.py:768`（`self.add_doctype_links(data)`）与 `:771-773`（hooks 循环）的先后；`:805` 的 `_(group.label) == _(link.group)` | README 该行失效症状补一句「本站给 Workstation 加 `group=Master` 的 DocType Link 也会使 items 变化而失配」；或把判定从「集合相等」改为「包含 `{BOM, Routing, Operation}`」（后者改代码，需另判风险） | `本Session修`（只改 README） | 只补 README，还是同时把判定放宽为「包含」 |
| P2-04 | 观察 | `Spike/P1S6R9-screens.json` 的 `05-workstation-connections`；`Spike/P1S6R6-screen-check.js:291-297` | 回执称 `require` 是「必须出现的译文，防该区域没渲染而空过」。但该屏取词范围是整个 body（未设 `extract_root`），而 `require` 的两个词「基础资料」「工艺路线」在左侧业务流程侧栏本就出现（分节名与条目名），所以关联页签完全没渲染时 `require` 也会满足、`forbid` 空过。该屏的真实保护来自 `steps[0].wait_for` 的 `!!document.querySelector('.form-dashboard .document-link')`，判定没真被削弱，故定观察 | `Spike/P1S6R12-SB/fd002/hooked/05-workstation-connections.png`（左侧栏可见「基础资料」「工艺路线」）；`nav_label_dup.out`（侧栏分节 `Master Data`→基础资料、条目 `Routing`→工艺路线） | 给该屏加 `extract_root: ".form-dashboard"`，让 `forbid`／`require` 只在看板容器内判；或把 `require` 换成只在该页签出现的词 | `延迟或不修`（判定实际由 `wait_for` 兜住） | 是否在 S6 收口前把 `require` 收窄到容器内 |
| P2-05 | 观察 | `frappe_china/tests/test_named_terms.py:122-128` | po 路径从「按本文件位置推算」改为 `frappe.get_app_path(app, "locale", "zh.po")`，修掉了空转；但 `get_app_path` 走 `get_pymodule_path` → `import`（`frappe/__init__.py:886-896`），bench 里缺某个 app 时会 `ModuleNotFoundError`，而原来的 `path.exists()` 是静默跳过。六个 app 当前都在本 bench（raven 只是没有 `zh.po`，被 `exists()` 正常跳过），不触发 | 读 `frappe/__init__.py:861-896`；`timesheet_terms_count.out` 显示 raven 无 `zh.po` 而其余五个都有 | 可不动；若要稳，`get_app_path` 外包一层 `if app not in frappe.get_installed_apps(): continue` | `延迟或不修` | — |
| P2-06 | 观察 | `frappe/desk/form/meta.py:33-46,233-234`（上游）；`frappe_china/tests/test_dashboards.py:17-21` | 真实 Desk 走 `FormMeta.load_dashboard()`，把**已译**的分组标题塞进 `__dashboard`，缓存键是 `doctype_form_meta::<doctype>`，**不含语言**。非 `developer_mode` 的站上，先访问的会话语言决定其它语言会话看到的标题（上游 `_("Master")` 本就如此，本修不新增该缺陷）。但两站 `developer_mode=1`（`sites/*/site_config.json`）走的是不缓存分支，所以 SB 的实页取证与 `test_dashboards` 都没覆盖生产缓存路径；用例直接调 `frappe.get_meta(...).get_dashboard_data()`，绕过了 `FormMeta` 缓存 | 读 `desk/form/meta.py:36`（key 无 lang）、`:233-234`；`grep developer_mode sites/*/site_config.json` 两站均为 1 | 记录即可：上线到非 developer_mode 环境前，另核一次多语言会话下的看板标题 | `延迟或不修` | 是否值得进登记册（本项目单一 zh 交付） |
| P2-07 | 观察 | `frappe_china/tests/test_dashboards.py:11-19,33-35` | 两点小瑕疵：① `setUp`／`tearDown` 没调 `super()`（与同仓 `test_crm_sidepanel.py` 同形），丢掉 `IntegrationTestCase.setUp` 的卡死看门狗（`faulthandler.dump_traceback_later`）；② `frappe.local.lang_full_dict = None` 在 v16 没有任何消费方（全仓 grep 只命中本文件与 `translate.py` 的一句注释），是无效赋值——译名其实靠 `get_all_translations(lang)` 按语言分键，不需要它 | `grep -rn lang_full_dict` 全 apps 只两处；`tests/classes/integration_test_case.py:80-88` | `setUp`／`tearDown` 补 `super()`；删掉 `lang_full_dict` 两行（或改注释说明是历史遗留的无害清理） | `本Session修` | 是否顺手清掉 |

## 交接摘要（跨片）

**本片依赖什么**：

- 片 4（README／守则反向核）：本片只核了与自身六项相关的 README 行（`:3`、`:19`、`:63`、`:67`、`:76`、`:97-101`、`:107-109`），行号与锁定源码逐一对过——`workstation_dashboard.py:8`、`meta.py:772-773`、`base_timeline.js:136`、`version_timeline_content_builder.js:416`、`utils.js:269-273`、`payment_entry.js:423`、`journal_entry.js:79`、`list_view.js:762-763`、`formatters.js:52-54`、`stock_controller.js:114-134` 全部命中。README 的覆盖登记是否**完整**（有无漏登的覆盖点）由片 4 收口。
- 片 1／3（译名与 csv）：FD-016 ③ 的 Node 用例用自建词典桩，不读 csv；`Partly Paid:Sales Invoice` 等三行是否真在合并字典里生效，归 FD-010 所在的片。
- 片 5（基线与占用核查）：`Master Data` 的占用核查我独立复算过（0 处），但 `Master` 本身仍是「少爷」这一遗留风险由 FD-009 的 `hidden.txt` 一侧跟踪。

**本片暴露什么**：

- 共享状态：`frappe.form.formatters.Select` 的全局替换现在带缺接点保护（FD-020），缺 `frappe.form` 时只告警、跳过；它仍是 IIFE 的最后一段，前面任一段抛错仍装不上（R12 原判未变）。
- 共享状态：时间线 `MutationObserver` 的选择器收窄为 `.timeline-content:not(.frappe-card)`，凡依赖「时间线里所有 `<b>null>` 都被改」的下游判据都要随之改（README `:67` 已改）。
- 接口契约：新增 `override_doctype_dashboards["Workstation"]`，L3 追加型，不占覆盖位；消费方只有工位表单「关联」页签。csv 键 `Master Data` 现在被两处共用（业务流程侧栏分节 ＋ 工位看板分组），改这个词会同时动两处。
- 工具契约：逐屏核每屏可带 `forbid`／`require`，共 144 屏；`result.json` 对不带这两个字段的屏不输出 `forbidden`／`missing_required` 键，下游读 `result.json` 的脚本要容许键缺失。

## 盲区自述

- **只对照了 R12 报告条目＋方案任务＋上游源码，没交叉核历史遗留行为**：例如 `opening_ledger.js` 的 PE 分支在 R4 之前是什么形态、JE 那条分组是否也曾被改过，没回溯。
- **没开浏览器、没动站点**：FD-002 的「关联」页签、FD-019 的评论卡片、FD-001 的开账 PE，我核的都是 SB 留档的 `result.json`／截图与宿主上的源码级复现，没有本步独立的实页取证。凡「真实 Desk 与 happy-dom／极简 DOM 桩的差异」（守则 §12 点名的高风险类）本步无法排除。
- **jsdom 类替代物的固有限制**：极简 DOM 桩的 `querySelectorAll` 只支持「标签／.类＋一个 `:not(.类)`」，真实浏览器的 `:not()` 语义（如 `:not` 内多选择器、优先级）没被测到；`pe_button_repro.cjs` 用的是上游源码按行号截取拼成的类，不含 jQuery 事件委托与真实 DOM 的全部行为。
- **没往「其它语言」之外的多会话方向找**：P2-06 只读了缓存键，没在非 developer_mode 站上实证。
- **没核 `<strong>` 一路**：时间线里 `frappe.utils.bold()` 产出的是 `<strong>`（如 milestone 日志），不在 `b` 选择器范围内；SL-018 的范围是 `version_timeline_content_builder.js:419` 的 `String.prototype.bold()`（`<b>`），所以未深究 `<strong>` 里是否也会出现 `null`。
- **没核 FD-016 ③ 用例与真实 csv 的对齐**：用例的 `MESSAGES` 是自建桩，若 csv 哪天少了 `Unpaid:Sales Invoice`，这些 Node 用例仍全绿（守 csv 的是 `test_named_terms`，属别片）。
- **没核移动端**：`page.js:631-632` 的 `hidden-xl` 菜单项、CRM／HRMS 移动端页面不在本片范围（FD-022 已裁延迟）。
