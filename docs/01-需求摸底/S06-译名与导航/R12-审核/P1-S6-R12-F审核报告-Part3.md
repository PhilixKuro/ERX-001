# F 审核分片报告 · 片 3（对象：R3 开发方案 Part3 SL-007～009／TS-010～013 的代码落地 / 审核标准：B 需求文档 §4.6、§4.7、§4.8.2、§4.8.3、§4.12、AC-004／005／012／013）

**轮次**：P1-S6-R12｜**步骤**：F 分片 3｜**日期**：2026-10-13｜**执行者**：Claude 子 Agent（只读）
**依据**：[R3 C开发方案-Part3](../R03-开发方案/P1-S6-R3-C开发方案-Part3.md)（全文）；[R3 总纲](../R03-开发方案/P1-S6-R3-C开发方案-总纲.md)（§四 A7～A9、§五 HT-004／005／007／008／009／012／014／015、§六 导航与开账相关行、§九）；[B需求文档](../R02-需求文档/P1-S6-R2-B需求文档.md) §一、§二、§4.6～§4.8、§4.11、§4.12、§七、§八、§十；[R4 D方案补充](../R04-代码/P1-S6-R4-D方案补充.md) DEC-024／025；[R6 C开发方案](../R06-开发方案/P1-S6-R6-C开发方案.md) §六；[R9 C开发方案](../R09-开发方案/P1-S6-R9-C开发方案.md) A28、TS-025、TS-029
**被审范围**：`frappe_china` HEAD `d441e9f`、`git diff 474cd1c..d441e9f` 中属 Part3 的部分——`workspace_sidebar/business_flow.json`、`workspace_sidebar/cn_tax.json`、`desktop_icon/business_flow.json`、`public/icons/desktop_icons/{solid,subtle}/business_flow.svg`、`public/js/opening_ledger.js`、`public/js/desk_patches.js:190-236`、`hooks.py:43-46`、`tests/test_business_flow_navigation.py`、`tests/test_opening_ledger.cjs`、`tests/test_sidebar_header.cjs`、`tests/test_desk_titles.cjs`、`README.md` 相关登记行；主仓库 `Spike/P1S6R4-*`（nav／tree／opening／refresh／ts013）、`Spike/P1S6R5-SB/it017/`、`it018/`

## 覆盖自证

- **读全的依据**：F Spec、`bricks/audit.md`、`bricks/sharding.md`；Part3 全文（接口契约、SL-007～009 验收条件逐条、TS-010～013 每一步）；总纲全文；需求文档 §4.6～§4.8 全节、§4.11、§4.12、§八全表、§十全表、§一与 §二；DEC-024／025 方案补充全文；R6 方案 §六全表；R9 方案 A28 与 TS-025、TS-029 两节；`开发守则.md` 全部长效约定标题与「改 app 级 json 必调大 modified」「断言机制可用前两侧都查」「判据须能区分」三节；`业务规则.md` 全文。
- **当线索读的**：R4 D回执-Part3、D待验表、R5 E确认报告（逐项表与问题详情中 IT-016～019、030、031）、R5 SB修复回执全文、R8／R11 E 报告按关键词（IT-034、IT-054、R11 第 16 行）。
- **逐行读的代码**：上列被审文件全文；`desk_patches.js` 只逐行读了 `:100-140`（R9 `Page.add_inner_button` 包装，与本片按钮交界）与 `:180-244`，其余段属片 2／片 6。
- **对照的上游**（锁定 commit：frappe `c1f1e8e`、erpnext `12cd563`）：`stock_controller.js:114-134`；`journal_entry.js:60-96`；`payment_entry.js:240-250,423-441`；`payment_entry.py:240-276` 与 json `is_opening` 的 `depends_on`；`general_ledger.py:203-305,553-600`；`frappe/ui/page.js:349-358,437-512,545-608,622-684`；`form/form.js:1540-1583`；`sidebar_item.js:1-80`；`sidebar_header.js:95-165,283-390`；`router.js:195-240`；`utils.js:1531-1600`；`boot.py:455-545`；`modules/import_file.py:115-167`；erpnext 全部 `extends erpnext.stock.StockController` 的类与 `show_general_ledger` 调用点（grep）；`frappe/public/icons/` 下 `workflow`、`git-branch`、`organization` 三个图标名是否存在；erpnext `desktop_icons/{solid,subtle}/` 的尺寸与风格。
- **只读查询**（容器 `erx001-frappe-1`，`bench --site X mariadb -e "SELECT…"`、`bench execute frappe.translate.get_all_translations`）：演示站 `tabWorkspace Sidebar`／`tabWorkspace Sidebar Item`／`tabDesktop Icon` 的 `frappe_china` 行与 58 条子项逐列；非 `frappe_china` 的图标 48 条、侧栏 43 条的 `MAX(modified)` 与 2026-10-09 以后改动计数；`tabDesktop Layout` 行数；51 个入口所指 DocType／Report 的存在性、`is_tree`、`default_view`、`issingle`、`disabled`；`Payment Entry`／`Journal Entry` `is_opening=Yes` 与 `Opening Stock` 调账条数；树形对象数据量；合并字典中 51 项与 7 节的中文。测试站只读了 `frappe_china` 两张表的 `modified`。
- **亲自跑的**：宿主 `node --test frappe_china/tests/*.cjs` 71/71；本片三文件 19/19。临时脚本 `Spike/P1S6R12-F/p3/cmp_sidebar.cjs`（json ↔ 方案表 ↔ 演示站库内逐列比对）、`pe_button_repro.cjs`（截取上游 `Page`／`Form` 真实源码 + happy-dom + jQuery 跑 `opening_ledger.js`）、`pe_fix_sim.cjs`（只在内存里替换一行看候选修法，不改 app 文件）。
- **跳过**：没跑 `bench run-tests`（主会话在测试站跑全量），故 `test_business_flow_navigation.py` 只读了断言；没开浏览器，51 项点击、树形两轮、四张凭证实点只核了 R4／SB 留下的 json 与 4 张 PNG（`nav-home`、`nav-sidebar` 实看，其余未看）；SL-009 例 6 的演示站取数请求未复跑；`desk_patches.js` 中不属本片的段落未逐行审。

## 逐项落地核查

| 意图层依据 | 要求层要求（方案任务／验收条款逐条） | 定位（文件:行） | 落地 | 生效否 | 偏差说明 |
|---|---|---|---|---|---|
| §4.6.1 首页图标 | 契约：图标 json 文件名 = `scrub(label)` | `desktop_icon/business_flow.json` | ✅ | ✅ 演示站有该行，未被当孤儿删 | — |
| §4.6.1 | 契约字段：`name`=`label`=`Business Flow`、`app`、`standard:1`、`hidden:0`、`idx:-1`、`icon_type:Link`、`link_type:Workspace Sidebar`、`link_to`、`bg_color`、`restrict_removal:0`、`roles:[]`、`modified`；不写 `parent_icon` | `desktop_icon/business_flow.json:2-15` | ✅ | ✅ 演示站行逐字段一致，`parent_icon` NULL | — |
| A8 排序 | `idx=-1`，首页第一个 | 同上 `:7` | ✅ | ✅ 演示站其余顶层可见图标 `MIN(idx)=0`；`tabDesktop Layout` 0 行（HT-007）；R4 `nav-home.png` 第一个为「业务流程」 | — |
| 契约 | 图标 label 与侧栏 title 相同（不区分大小写） | 图标 `:4` ／ 侧栏 `:4` | ✅ | ✅ R4 `nav-click.out.json` boot 首图标点开即 `sidebar=Business Flow` | 无回归用例守这一条，见 P3-04 |
| §4.6.1 侧栏 | `name`=`title`=`Business Flow`、`app`、`standard:1`、`module` 显式 `CN Tax`、`items`、`modified` | `workspace_sidebar/business_flow.json:2-7,583-584` | ✅ | ✅ 演示站 `module=CN Tax`、`standard=1` | — |
| 契约 | `header_icon` 按 TS-010 第 4 步：优先 `workflow`／`git-branch`，不存在才 `organization` | 同上 `:7` | ⚠️ | — 字段实际不被读 | 两个图标名在 `frappe/public/icons/lucide.svg` 都存在，却用了 `organization`；但有 svg 时侧栏头部走 `desktop_icon_url` 分支，`header_icon` 被覆盖（`sidebar_header.js:299-311`），无可见影响。见 P3-06 |
| 契约 | 分节形态 7 个字段照 `selling.json` | 7 个 Section Break | ✅ | ✅ | `cmp_sidebar.cjs` 逐字段比对 0 差异 |
| 契约 | 条目形态；URL 项不写 `link_to`、DocType／Report 项不写 `url`；**不写 `filters`、`route_options`** | 51 个 Link | ✅ | ✅ 演示站 58 行 `filters`、`route_options` 全为 NULL | 不写 `filters` 是树形能进树视图的前提（`sidebar_item.js:59-71`），已核 |
| DEC-020／A7 | TS-010 第 2 步表：7 节、51 项的 label／link_type／link_to／url 逐项 | `business_flow.json:8-582` | ✅ | ✅ | 脚本按方案表 58 行逐行比对 0 差异；库内 58 行与 json 逐列一致（第 58 行的报差是脚本 `trim()` 剪掉行尾空列，非真差异） |
| §4.6.2 | 51 个入口的对象存在、路由正确 | 演示站 `tabDocType`／`tabReport` 联查 | ✅ | ✅ 36 个 DocType、11 个 Report 全部存在，Report 全 `disabled=0`、均为 Script Report（走 `query-report/` 分支）；`Global Defaults` 为单例 → 表单 | — |
| §4.6.3／完成标志⑤ | 树形 DocType 走树视图 | 路由器 `router.js:223-225` | ✅ | ✅ `Account`／`Cost Center`／`Warehouse` 的 `default_view=Tree`，侧栏不带 filters → `generate_route` 默认分支 → 路由器转 `Tree`；R4 与 SB 两轮实点 `route=["Tree",…]`、节点 6／1／1 | — |
| §4.7 | `is_tree` 集合复核为五个 | 演示站 `is_tree=1` 的侧栏 DocType | ✅ | ✅ 恰为 Company、Account、Cost Center、Warehouse、Employee | — |
| SL-007 ① | 迁移后两张表有记录、字段值对；首页第一个、svg 不是首字母 | 演示站查询；`nav-home.png` | ✅ | ✅ | 首页图标为黑色四方块，与其余蓝色圆角图标风格不一，见 P3-05 |
| SL-007 ② | 分节顺序、条目数与表一致；同一侧栏中文 label 无重名（脚本断言） | 演示站合并字典 | ✅ | ✅ 7 节译为基础资料／销售／采购／库存／生产／财务／报表；51 项中文无重名（本片实算） | 仓内回归用例只查英文源词不重名，见 P3-04 |
| SL-007 ③ | 逐项点击可达；URL 项新标签 | R4 `nav-click.out.json` | ✅ | ✅ 51/51 `pass`；URL 四项 `target=_blank`，`/crm/leads` → `/crm/leads/view/list`（别名可用，方案第 2 步要求两种都试，取能开的） | 证据未进版本，见 P3-07 |
| SL-007 ④／DEC-005 | 原有入口一个不改、一个不藏 | 演示站 | ✅ | ✅ 非 `frappe_china` 图标 48 条、侧栏 43 条 `MAX(modified)` 为 2026-10-07，2026-10-09 以后改动 0 条（侧栏子项同为 0）；4 个 `hidden=1` 均早于 S6 | R5 IT-016 已裁「接受 E 替代证据」，本片补的是现状复核 |
| SL-007 ⑤／TS-011 | 五对象从侧栏点进、刷新前有节点或记录；干净与「进过列表」两轮 | SB `it018/tree-rounds.json` | ✅ | ✅ 10/10 | 需求 §4.7 写「在演示站」，方案改测试站（方案职责内）；演示站当前 Employee 0 条，演示环节 19 才建 |
| SL-007 ⑥⑦ | 二次迁移不重导；旧 `modified` 改 label 不生效、调大生效、恢复 | SB `it017/result.json` | ✅ | ✅ 四轮 `pass`，`others_unchanged`／`cn_tax_unchanged`／`icon_unchanged` 为真 | R4 那次失败原因 SB 已自承没查清，已裁决，不重提 |
| SL-007 ⑧／DEC-025 | `CN Tax` 内容不动，仅补固定 `modified` | `cn_tax.json:8`；diff 只加一行 | ✅ | ✅ 演示站 `modified` 与 json 相等 | — |
| A9／守则 | 每次改 json 调大 `modified` | `git log` 两次提交 | ✅ | ✅ `52f8064` 12:00:00 → `c2b0420` 18:16:09；演示站库值 = json 值 | 测试站库值 2026-10-13 07:54:57 晚于 json（SB 恢复轮所写，已披露），下次改 json 须取更晚时刻 |
| TS-010 第 5 步／HT-009 | 两个 variant 的 svg、boot 资源路径正斜杠 | `public/icons/desktop_icons/{solid,subtle}/business_flow.svg` | ⚠️ | ✅ boot `desktop_icon_urls.frappe_china` 两 variant 各含该路径 | 方案要「三个节点由箭头相连」，实为四个节点、无箭头；`solid` 版连线只有 `fill` 无 `stroke`，零面积不显示。见 P3-05 |
| TS-010 第 8 步／DEC-024 | 侧栏头部无 `/undefined` 请求；包装 `add_app_item` 无容器时返回、有容器委托、幂等、缺类跳过 | `desk_patches.js:190-200` | ✅ | ✅ 上游模板无 `.sidebar-header-menu`，`make()` 后 `dropdown_menu` 为空 jQuery（`sidebar_header.js:295`）；R4 `undefined_requests=0` | `test_sidebar_header.cjs` 5 条有判别力（撤掉包装则「无容器」两条的 `calls.length` 变 1） |
| HT-004／TS-012 第 1 步 | 覆盖 `StockController.prototype.show_general_ledger`：开账判据 `purpose==="Opening Stock"` 或 `is_opening==="Yes"`；非开账调原方法；复刻 114-134 行并加 `show_opening_entries:1` | `desk_patches.js:202-233` | ✅ | ✅ 逐字段对照上游 `:114-134` 一致（`cur_frm` 换成 `me.frm`，等价）；R4 浏览器：期初调账带参数、2 行非零分录；普通库存凭证不带 | 覆盖面大于 HT-004 所写，见 P3-03 |
| SL-008 ④ | 类不存在时 `console.warn` 并跳过、不抛错 | `desk_patches.js:204,234-236` | ✅ | ✅ R4 注入反证告警 1 条；本片跑 `test_sidebar_header.cjs` 时无 `erpnext` 也未抛错 | 无断言该告警的 Node 用例，见 P3-04 |
| HT-005／TS-012 第 2 步 | `hooks.py` `doctype_js` 给 JE、PE 下发 `opening_ledger.js` | `hooks.py:43-46` | ✅ | ✅ | — |
| TS-012 第 2 步 | JE：仅 `is_opening==="Yes" && docstatus>0` 时移除 `查看/会计凭证` 并加回同名按钮，参数照抄原文 + `show_opening_entries:1`，保留 `finance_book` | `opening_ledger.js:4-23` | ✅ | ✅ 本片用上游真实 `Page`／`Form` 代码复现：工具栏只剩 1 个按钮，点后带开账参数与 `finance_book`；R4 浏览器同 | 窄屏「菜单」里残留一条原生项，见 P3-02 |
| TS-012 第 2 步 | PE：`remove_custom_button(__("Ledger"), "fa fa-table")` 后加回 | `opening_ledger.js:7,10-23` | ❌ | ❌ **原问题没消失** | `Form.add_custom_button` 把含 `fa fa-` 的分组置空（`form.js:1542`），原生按钮是工具栏上的独立按钮；本补丁带 `"fa fa-table"` 去删，`remove_inner_button` 按分组找 `.inner-group-button[data-label="fa fa-table"]`，找不到，什么也没删；随后 `add_custom_button` 又把分组置空，`add_inner_button` 见同名按钮已在，直接返回旧按钮（`page.js:651-664`）。复现：点击后 `route_options` 仍是原生那份、无 `show_opening_entries`。见 P3-01 |
| TS-012 第 3 步 | README 登记三行（复刻行号、上游改须同步） | `README.md:96-102` | ⚠️ | — | 库存类一行已按 R5 IT-019、R11 IT-054 改对；PE 一行写「开账收付款表单仅在原分组中保留一个会计凭证按钮」，与实际不符（并入 P3-01） |
| SL-008 ①② | 期初调账、期初日记账跳总账显示分录 | R4 `opening-ledger.out.json` | ✅ | ✅ 两张各 2 行非零；总账读法 `general_ledger.py:564-576` 已核（HT-015 成立） | — |
| SL-008 ③ | 普通库存凭证、普通日记账不带参数、行为不变 | 同上 | ✅ | ✅ | **PE 四种情形都没实测**（方案 SL-008 只点名库存调账与日记账，但 TS-012 第 2 步要 PE），这正是 P3-01 漏过的原因 |
| SL-009 ①～⑤／TS-013 | 六例每例结论；例 1／5 引树形截图；例 2 记 LG-073 不修；复现不了不硬修、步骤可照做 | `Spike/P1S6R4-ts013-report.md`；SB `it018/` | ✅ | ✅ 六例都未复现或不属本类，均未硬修；例 3、4、1／5 的命令序列与实时通道回执由 SB 补齐（R5 IT-018 已裁决） | 例 6 只有 R4 一次演示站记录 |
| §4.12 侵入度 | 前端补丁按 ADR-0009 登记；不改上游源码 | README；上游六 app | ✅ | — | 上游未改（本片未见 diff）；补丁三处都已登记 |
| R9 A28 ③（片 6 交界） | 侧栏、图标 json 的 `title`／`label`／`items[].label` 算本 app 源词 | `tests/test_translations.py:142,296-299` | ✅ | ✅ 本片 4 个新源词 `Business Flow`／`Master Data`／`Finance`／`AI Assistant` 在 csv 中（`zh.csv:323,750,2049,2888`）；四个中文报表名按「去掉含汉字的串」不进清单 | 取法正确与否归片 6 |

## 业务规则合规核

| 规则条款 | 本 Round 改动是否涉及 | 结论 | 备注 |
|---|---|---|---|
| BR-001～BR-007（会计准则、报表构成、增值税与附加税、资产负债恒等式、价税分离） | 导航（图标、侧栏、svg、侧栏头部包装）不涉及任何产品语义 | 合规（不涉及） | 只改「从哪里进」，不改任何单据、报表的取数与计算 |
| BR-002 法定报表 | 侧栏「报表」节链到四张小企业报表 | 合规 | 只是入口；报表名本身是中文，不经 csv（需求 §4.11 的唯一触点由片 1 自检守） |
| 「总账显示开账分录」（SL-008） | 涉及会计总账的显示参数，但不在 BR 清单内 | 合规；不构成新增规则 | 补丁只在跳转时多带一个上游已有的筛选项 `show_opening_entries`，不改总账的计算与汇总口径（`general_ledger.py:564-576` 原逻辑）；普通凭证路径不变。「开账凭证跳总账应直接显示其分录」是界面行为要求，不是领域不变量，本片未检出需送审的规则新增或变更 |

## 集成点登记（交接摘要）

| 类型 | 落点 | 本片暴露／依赖 | 两端一致否（本片所见） |
|---|---|---|---|
| 共享状态：译名 | 侧栏 51 项、7 节与图标的显示名全部靠合并字典（`boot.py:465` 的 `_(item.label)`） | **依赖**片 1／片 2／片 6 的 `zh.csv`：新起 4 键（`Business Flow`／`Master Data`／`Finance`／`AI Assistant`）与沿用的官方键。**暴露**：同一侧栏 51 个中文名当前无重名（演示站实算），任何 csv 改词可能打破这一条，仓内无回归用例守中文重名（P3-04） | 一致（当前） |
| 接口契约：源词取法 | `workspace_sidebar/*.json`、`desktop_icon/*.json` 的 `title`／`label`／`items[].label` | **暴露**给片 6（R9 A28 ③）：这些串算本 app 源词；含汉字的 4 个报表名被排除 | 一致 |
| 跨模块数据流：对象存在 | `link_to: "Cash Flow Worksheet"` | **依赖**片 1（Part1 TS-004 改名补丁）先把 DocType 改好；另依赖 S4 的 4 张中文名报表 | 一致（演示站均存在） |
| 接口契约：图标 ↔ 侧栏 | 图标 `label` 必须等于侧栏 `title`（`desktop_icon.py:195-196`、`desktop.js:56`）；svg 文件名 = `scrub(label)` | 本片自洽；改名须三处同改 | 一致 |
| 共享状态：`modified` | 演示站两张表的 `Business Flow` 行 = json；测试站侧栏行 2026-10-13 07:54:57 **晚于** json 2026-10-10 18:16:09 | **暴露**：下次改 `business_flow.json` 必须把 `modified` 取晚于 2026-10-13 07:54:57 的当时时刻，否则测试站静默不导入 | 演示站一致；测试站库新于 json（已在 SB 回执披露） |
| 共享文件：`desk_patches.js` | 本片占 `:190-236`（侧栏头部、开账库存类），同一 IIFE 内还有片 2 的 Select formatter（`:238-243`）与片 6 的 R9 诸包装（`patch_method` 等） | **依赖**：IIFE 前段任何一处抛错都会让本片两段不执行。**交界**：R9 TS-028 `Page.add_inner_button` 包装（`:118-124`）对带分组按钮先 `__()` label；本片按钮 label 已是译文，再译不变，与 `remove_inner_button` 的 `__()` 也对得上 | 一致（JE 复现通过） |
| 事件／钩子 | `doctype_js` 给 `Journal Entry`、`Payment Entry` 的 `refresh`；依赖其在 erpnext `refresh` 之后跑（HT-005） | 本片独占 `doctype_js`；别片无同 DocType 的 `doctype_js` | JE 一致；PE 时机对、移除失败（P3-01） |
| 接口契约：总账报表 | `frappe.route_options.show_opening_entries=1` → `general_ledger.js:186` 筛选 → `general_ledger.py:554-576` | **暴露**给片 6：同一张总账屏上还有 R9 TS-029 `QueryReport.prepare_columns` 改凭证类型列显示 | 一致 |
| 接口契约：原型覆盖范围 | `erpnext.stock.StockController.prototype.show_general_ledger` 被 SI／PI（经 `TransactionController→taxes_and_totals→payments`）、DN、PR、Stock Entry、Stock Reconciliation、LCV、Asset Capitalization 继承 | **暴露**：所有这些单据 `is_opening==="Yes"` 时都带开账参数（P3-03） | — |
| 交 Part4／片 4 | 侧栏 `Business Flow` 的 `sidebar_title` 是逐屏核 `screens.json` 判「侧栏是否保持」的键；HT-008 换侧栏路径归片 4 | 暴露 | 未核（归片 4） |

`docs/开发守则.md` 末节「跨 Phase 接口契约表」只有「演示操控的事件协议」一条，本片不涉及。

## 自证复核

| 被审产物声称 | 实际复核结果 | 一致否 |
|---|---|---|
| R4 回执 TS-010「7 个分节、51 个链接」；R5 E「58 行全部一致」 | 脚本逐行对方案表与演示站库内：58 行 0 差异 | 一致 |
| R4 回执 TS-012「Node 8/8」；「Part3 focused 13 Node tests」 | `test_opening_ledger.cjs` 8 条、`test_sidebar_header.cjs` 5 条，本片实跑全过；全套 71/71（SB 回执声称 71） | 一致 |
| R4 回执 TS-012「修正 Payment Entry 的原生 `fa fa-table` 分组」「HT-004/005/015 均成立」 | PE 的原生按钮根本不在 `fa fa-table` 分组里（`form.js:1542` 置空），修正前后都删不掉；浏览器验证没包含 PE | **不一致**（P3-01） |
| README `:102`「开账收付款表单仅在原分组中保留一个会计凭证按钮」 | 实际保留的是原生那个按钮、原生处理函数 | **不一致**（P3-01） |
| R4 回执 TS-010「`/undefined` 请求 0」 | R4 `nav-click.out.json` `undefined_requests` 为空；读码确认包装逻辑成立 | 一致（未亲自开浏览器） |
| R4／SB「树视图两轮 10/10」 | SB `tree-rounds.json` 10 条，三个树形 `route=Tree` 且节点数 >0，两个列表记录数 >0 | 一致 |
| SB IT-017「四轮 pass，其余 app 三表不变」 | `it017/result.json` 四轮与三个 `*_unchanged` 均真；演示站现状另核：原有入口 2026-10-09 后零改动 | 一致 |
| 方案 HT-004「库存凭证、库存调账打开时生效（子类无同名方法）」 | 生效面更大：发票、发货、收货、到岸成本、资产资本化都继承该方法 | 部分一致（P3-03） |
| 验证门：本片相关 Node | 声称 13 → 实测 19（含 `test_desk_titles.cjs` 6 条，非本片新增）；全套声称 71 → 实测 71 | 一致 |
| 验证门：`test_business_flow_navigation.py` | 未跑（约束），读断言：只查 `module`、分节顺序、英文 label 不重复、URL 项 4 个、图标 `idx`／`hidden`／`link_*` | 未复跑 |

## 问题清单

| # | 严重程度 | 定位 | 问题描述 | 违背的标准/意图 | 建议 | 建议档位 | 待裁决点 | 状态 | 用户裁决 |
|---|---|---|---|---|---|---|---|---|---|
| P3-01 | 中 | `frappe_china/public/js/opening_ledger.js:7,10`；`tests/test_opening_ledger.cjs:39-40,54-60`；`README.md:102` | 收付款凭证的开账总账按钮没被替换。上游 `Form.add_custom_button` 把含 `fa fa-` 的分组置空（`frappe/public/js/frappe/form/form.js:1542`），原生「会计凭证」是工具栏独立按钮；补丁 `remove_custom_button(__("Ledger"), "fa fa-table")` 去分组里找，找不到就什么也没删；随后 `add_custom_button` 见同名按钮已存在，直接返回旧按钮（`page.js:651-664`），新回调丢掉。结果：开账收付款凭证点「会计凭证」仍不带 `show_opening_entries`，总账仍把它记入期初、明细空（`general_ledger.py:564-574`），即 `PH-P1061` 原症状。复现：`node D:/ERX-001/Spike/P1S6R12-F/p3/pe_button_repro.cjs`（截取上游真实源码运行），PE 点击后 `route_options={"native":true}`，JE 正常。Node 用例用的桩把 `fa fa-table` 当真分组，与上游行为不符，测不出来；R4 浏览器只验了四张凭证，没有 PE；README 那行的复验说法也随之不实。触达面有限：PE 只有在公司开了「预收预付记入单独科目」时 `is_opening` 才可见、可为 Yes（`payment_entry.json:732`、`payment_entry.py:240-276`），演示站当前 0 张 | Part3 TS-012 第 2 步（PE 照做）；需求 §4.8.2「从开账凭证跳过去时直接显示其分录」；守则「断言机制可用前写入端与读取端两侧都查」 | PE 分支删除时不带分组：`frm.remove_custom_button(__("Ledger"))`（本片在内存里替换这一行模拟，`pe_fix_sim.cjs` 显示 PE 按钮只剩 1 个且带开账参数）；Node 桩改为照上游 `add_custom_button` 置空 `fa fa-` 分组；README 第 102 行改写；测试站开该公司设置造一张开账 PE 实点 | 新Session修 | 定级在中／低之间：方案明确要求、回执与 README 声称已做（按中）；但演示线不走开账收付款、且需特定公司设置才出现（可按低）。另：是否接受 HT-005「该单据记不可行」作为替代处置 | 待裁决 | |
| P3-02 | 低 | `opening_ledger.js:10-11`；上游 `form.js:1562-1583`、`page.js:449-450,474-481` | 日记账凭证替换后，窄屏（`lg` 断点以下，`.hidden-xl`）页面「菜单」里有两条「查看 > 会计凭证」，第一条是原生处理函数（不带开账参数）。原因在上游：菜单项的 `span` 没有 `data-label`，`remove_custom_button` 与 `add_dropdown_item` 用 `span[data-label=…]` 查找永远查不到，既删不掉旧项也不去重。复现：同 P3-01 脚本输出 `mobile_menu` 两条。宽屏工具栏只有 1 个按钮，不受影响 | Part3 TS-012 第 2 步「移除 erpnext 加的那个总账按钮」 | 演示用宽屏可不修；要修就在补丁里按菜单项文字删掉原生那条 `li` | 延迟或不修 | 是否在意窄屏菜单的重复项 | 待裁决 | |
| P3-03 | 观察 | `desk_patches.js:202-233`；上游 `payments.js:4`、`taxes_and_totals.js:11`、`transaction.js:37`、`sales_invoice.js:89`、`purchase_invoice.js:83`、`delivery_note.js:318`、`purchase_receipt.js:189`、`landed_cost_voucher.js:7`、`asset_capitalization.js:6` | 原型覆盖的生效面大于 HT-004 所写：销售／采购发票、发货单、采购收货、到岸成本、资产资本化都继承 `StockController.show_general_ledger`，凡 `is_opening==="Yes"`（如期初发票）都会带开账参数。与需求意图同向（开账凭证都该看到分录），无副作用，但未实测，README 的失效症状与复验法只写了库存调账 | 总纲 HT-004 的读码范围；守则「覆盖逐处登记」要写清影响面 | README 该行补一句影响面；或下次碰期初发票时顺带实点 | 延迟或不修 | 是否需要补登影响面 | 待裁决 | |
| P3-04 | 低 | `tests/test_business_flow_navigation.py:14-27`；`desk_patches.js:202-236` 无 Node 用例 | 回归用例判别力弱：① 只断言英文源词不重名，SL-007 ② 要的是「中文 label 无重名」，两个不同源词译成同一中文不会报；② 不断言 51 项、不比对方案表，删一项或改 `link_to` 都不报；③ 不断言图标 `label` 等于侧栏 `title`（契约硬约束）；④ 开账库存类补丁（含缺类告警分支）没有 Node 用例，只靠 R4 一次浏览器取证；⑤ `test_opening_ledger.cjs` 的桩把 `fa fa-table` 当真分组（P3-01 的成因之一）。方案对 SL-007 ② 只要求脚本断言，Python 用例属额外，故按技术债定级 | Part3 SL-007 ②、SL-008 ④；守则「判据必须能区分它要区分的两种情形」 | 用例补：条目数与 `(label, link_type, link_to/url)` 清单、图标 label＝侧栏 title、zh 合并字典下中文不重名；为库存类补丁补 Node 用例（开账带参、非开账委托原方法、缺类告警） | 新Session修 | 是否值得为导航 json 补回归用例 | 待裁决 | |
| P3-05 | 低 | `public/icons/desktop_icons/solid/business_flow.svg`；`subtle/business_flow.svg`；`Spike/P1S6R4-nav-home.png` | 首页第一个图标与其余图标风格不一：erpnext `solid/` 图标是 54×54、蓝色圆角底（如 `solid/stock.svg`），本图标是 24×24、`currentColor`（作为 `<img>` 加载时为黑色）四方块。另 `solid` 版的连线段只有 `fill`、没有 `stroke`，零面积不渲染，实际只显示四个方块；方案要的「三个节点由箭头相连」也没做到（四节点、无箭头）。方案自己写的「与 erpnext `solid/` 同尺寸（24×24）」前提就不对 | Part3 TS-010 第 5 步；需求 §4.6.1 首页图标 | 照 erpnext `solid/` 的 54×54 圆角底重画（`subtle` 同理）；或至少给 `solid` 连线补 `stroke` | 延迟或不修 | 图标观感是否在演示前要改 | 待裁决 | |
| P3-06 | 观察 | `workspace_sidebar/business_flow.json:7` | `header_icon` 用了 `organization`，而方案第 4 步优先的 `workflow`、`git-branch` 在 `frappe/public/icons/lucide.svg` 都存在；回执没记这一取舍。该字段在有 svg 时被侧栏头部覆盖（`sidebar_header.js:299-311`），当前无可见影响 | Part3 TS-010 第 4 步 | 不修；svg 缺失时它才会露出 | 延迟或不修 | — | 待裁决 | |
| P3-07 | 观察 | 主仓库 `.git/info/exclude` 的 `/Spike/P1S6R4-*` | SL-007 ①②③⑤ 与 SL-008 ①～④ 的取证（`P1S6R4-nav-click.out.json`、`opening-ledger.out.json`、`tree-rounds.json`、`refresh-tax.json` 与全部 PNG）都被排除在版本外，只在本机；`ts013-report.md` 例外已入库。SB 把 IT-017／018 重做进了入库目录，但 51 项点击与四张凭证实点的证据没有入库副本 | 需求 §八「凡验收都须有正向证据」；可复核性 | 收口时把这几份 json 复制进已入库目录，或在 S6 概况写明证据只在本机 | 延迟或不修 | 本机留存是否足够 | 待裁决 | |
| P3-08 | 观察 | `frappe_china/README.md:19` | 「正式业务导航由后续阶段提供」已过时：S6 已交付 `Business Flow` 图标与侧栏；README 目录说明也没提这两个 json、svg 与「改 json 必调 `modified`」 | README 随代码走的定位（总纲 A6） | 改写这一条，补一句导航文件位置与 `modified` 约定 | 延迟或不修 | — | 待裁决 | |

## 本片盲区自述

- **没开浏览器**：点击可达、树形两轮、四张凭证、首页图标都只核了 R4／SB 的留档与 4 张截图里的 2 张；P3-01／P3-02 是用截取的上游真实源码在 happy-dom 里复现的，不是在真实 Desk 页面上点出来的。真实页面若有别的脚本先改了 `custom_buttons` 或工具栏，结论可能有出入；建议修 P3-01 时在测试站补一次实点。
- **没跑 Python 用例**：`test_business_flow_navigation.py` 是否全过未复核（主会话在跑全量）。
- **没往这几个方向找**：非 Administrator 用户看侧栏（HT-014，交 S7）；从顶部搜索进单据时侧栏被换走（HT-008／LG-001，归片 4）；侧栏在英文会话下的显示；`desk_patches.js` 里不属本片的段落是否会在本片两段之前抛错（只读了交界的 `add_inner_button` 包装）；CRM 别名 `/crm/leads` 在 CRM 升级后是否仍重定向。
- **SL-009 六例**：只核了结论表与 SB 序列的结构，没有复跑；例 6 只有 R4 一次演示站观察。
- **拿得最不准的一处**：P3-01 的定级。代码缺陷本身证据确凿，但「开账收付款凭证」在本项目演示与客户场景里多常见，本片判断不了。
