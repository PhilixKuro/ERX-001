# P1-S6-R8-E 确认报告（对象：R7 D 代码 / 清单：R6 开发方案 TS-016～024）

**日期**：2026-10-12｜**执行者**：Claude（Opus 5.5）｜**Spec**：`E-verify-plannedDev-confirm.md`＋`bricks/confirm.md`＋`play-confirm.md`，打tag=否
**清单**：[R6 开发方案](../R06-开发方案/P1-S6-R6-C开发方案.md) TS-016～024 与 SL-011～015 验收条件；另按 R6 方案 §八，复核 [R5 报告](../R05-确认/P1-S6-R5-E确认报告.md)的 `本Session修` 8 项与 SB 各项。
**回归范围**：`bench --site test.localhost run-tests --app frappe_china` 全量＋宿主 `node --test frappe_china/tests/*.cjs`。
**核法**：四个切片组各派一个只读子 Agent，逐条对照代码、证据文件、截图核对，能跑的都自己跑。约束：不改项目文件，不对演示站写库，测试站只给主 Session 跑回归。全量回归与 Node 用例由主 Session 实跑。临时脚本与输出在 `Spike/P1S6R8-E/{sl011,sl012,sl013,sl014}/`。[R7 D 回执](../R07-代码/P1-S6-R7-D回执.md)只当线索用。
**编号**：本报告的未通过项接 R5 续编，从 `IT-033` 起。R5 的 SB 余项沿用原号。

## 逐项确认

| # | 清单项 | 落地否 | 生效否 | 根因消除否 | 验收标准 | 验证方式（本次实做） | 结论 |
|---:|---|---|---|---|---|---|---|
| 1 | TS-016 基线脚本可跑、占用脚本读合并字典、白名单拆模块 | 是 | 是 | 是 | SL-011 ④⑤ | 基线脚本不带开关：`ValueError`，退出码 1。带 `--allow-unlocked`：退出码 0，`commits.unlocked` 为 `frappe_china: cf8a9ba ≠ 1d51db2`。六 app 缺口 0，白名单命中合计 228。占用反例 `"Stock Ledger" "物料凭证"` 报不可用，占用者 `Stock Ledger Entry`；对照组「库存台账」可用。`translation_whitelist.py` 不 import frappe，213 项理由均非空，测试与基线脚本都读它 | ✅ |
| 2 | TS-017 质量守卫与覆盖清单重建 | 是 | 是 | 是 | SL-011 ①～③ | 宿主对当前 csv 5745 行跑四道守卫，全部返回 `[]`；9 个用例 9/9。自构 12 条坏行全部命中，6 条好行无误报。**变异检验**：把四个谓词逐一改为恒假，每次恰好对应那条判别力用例失败，可见判别力是真的。覆盖清单 119 条，与 csv∩官方的交集 119 键完全相等，两个差集都为空。basis 形态不符 0 条，`ours` 命中守卫 0 条。抽 10 组依据回到 S6、S3 原文都找得到。偏离第 1～3 条见下文追认表 | ✅（附 IT-045、IT-046、IT-051） |
| 3 | TS-018 csv 清场与排序 | 是 | 是 | 是 | SL-012 ①②⑥ | `keep_keys()` 与 A15 ①②③ 一致。旧 csv 5852 行，pruned 5628 条（`wc -l` 5742，差在多行字段），5852 − 5628 = 224。被删的 161 个覆盖键：2 个（`Lft`、`old_parent`）已在 TS-019 重回 csv；其余 159 个在演示站合并字典里与官方 0 不符。抽 10 键全部等于官方。`test_csv_sorted` 含对调两行的判别力断言（`test_translations.py:207-215`）；宿主查全表，逆序 0 | ✅（附 IT-043） |
| 4 | TS-019 演示线定词补齐 | 是 | 是 | 部分 | SL-013 ①～④⑥ | 附表 462 键在合并字典中全为中文；抽 15 条读源码，14 条对、1 条措辞存疑。撞名按现合并字典重算：141 组仍撞，与同义表比对后**剩 1 组不在表内**（IT-041）。E 点名的四组都已解开。S3 §1.1、§1.3 共 23 行在 csv 与 `NAMED_TERMS` 中；无 context 的 `Unpaid` 显示官方「未付」；不写的 12 条逐条核过，都成立。75 组对 73 组的差额，D 的解释成立（S3 草案自己数错）。占用重查 7 处的判定都成立。`Dr` 截图实看：下拉有「借方」。**HT-017 截图拍到的是相邻字段**（IT-040） | ❌ IT-040、IT-041 |
| 5 | TS-020 按钮抽检重做 | 是 | 是 | 是 | SL-013 ⑤ | 表 89 行、7 列齐全，「点了即写库」34 个落在 20–40 区间。E 自追 9 个按钮的源码（含点名的 `sales_invoice.js:378/402`、`purchase_invoice.js:155`、`work_order.js:944`），动作描述全对。定稿与合并字典比对 88/89，余 `Inter Company Invoice`。该键在 `purchase_invoice.js:228` 是裸串，分组按钮由 `page.js:622 add_inner_button` 渲染，不调 `__()`，csv 确实无效。`Payment`→收付款在 csv、`OVERRIDES`、`NAMED_TERMS` 都有 | ✅（`Inter Company Invoice` 见 IT-038） |
| 6 | TS-021 批量档整批重译与抽检 | 是 | 是 | 是 | SL-012 ③～⑤ | 用种子 20261011 复现抽样：100 键及其顺序与 D 完全一致。**E 复判**：样本内抽 20 条，与 D 20/20 一致；样本外用种子 20261012 抽 40 条，逐条读出处，不可用 0/40。合计不可用 3/140≈2.1%。回扫 15 条现值都对，`repost_item_valuation` 一族已不含「重过账」。全表：「中文：」0、`???` 0、空译 0、GB2312 外汉字 0；中英混排 37 行全是源词自带的代码、路径、品牌 | ✅ |
| 7 | TS-022 逐屏核 v2 脚本与测试站反证 | 是 | 是 | 部分 | SL-014 ①⑥ | 屏清单 139 屏，映射表对 §4.9 每一**行**都有屏。按行内**子项**对照，有漏屏（IT-039）。DEC-032 的两态已做到。三种反证各报 `pass=false` 并列出该词。恢复证据：csv 哈希与 `deb226f` 相同，造前造后 `git status` 一致（验收写的是「为空」，当时其实有 6 个未提交文件，D 改用「与造前一致」作判据，可接受）。`.form-name-container` 只装 `doc.name`，排除不会漏掉标题区文案 | ❌ IT-039 |
| 8 | TS-023 演示站逐屏核与新基准点 | 是 | 部分 | 否 | SL-014 ②～⑤⑦ | `result.json` 共 139 屏，124 过、15 不过，与回执一致。15 屏逐屏追到源码，归因基本属实，但 `Nov`、`Empty` 两处归因不准，且 15 屏都能在 `frappe_china` 内修（IT-033～IT-037）。确认框 31 屏 `docstatus` 都不变；但 BOM 与 Work Order 截到的是「取消所有单据」对话框，普通取消框没截到，回执未披露（并入 IT-039）。`default_data` 3 词有 REST 存在性校验，但没进延迟需求登记册（IT-042）。7 个预填屏走菜单点击，侧栏都是 `Business Flow`。侧栏重名脚本只读，E 在演示站复跑得 `{}`。「应收」两图实看：Link 下拉中「应收账款」出现 1 次，`account_type` 选项中 0 次，按 IT-022 原意（不出现两个「应收账款」）判通过，见复核建议第 3 条。备份：`20261012_163036` 是根目录最新一套，与 `保留-S6收尾/` sha256 相同；`20261012_160758` 只在 `保留-S6R6测试态/`。演示站只读核：Translation、底稿、GL、SLE 都为 0，`S6R6` 前缀 0，科目 266，`check_app_order` 全真，`find_problems()` 为 `[]` | ❌ IT-033～IT-039、IT-042 |
| 9 | TS-024 全量回归、常驻文件、工作量 | 是 | 是 | 部分 | SL-015 ①～④ | ① 本次实跑见下节。② 六个上游 app status 为空，HEAD 与锁一致；`frappe_china` 的 status 为空，HEAD 为 `cf8a9ba`，锁仍是 `1d51db2`（R5 IT-001 未做）。③ 项目概况与开发守则已按实况写，没有宣称 Stage 完成，守则已补「批量写 csv 前后跑守卫、不取 `zh_TW.po`」。项目概况 `:186` 关于 `Nov`、`Empty` 的归因随 IT-036 一并修正。④ 工作量只有定性结论，没有数字（IT-049） | ⚠ IT-049 |
| 10 | R5 `本Session修` 8 项复核 | 是 | 是 | 是 | R5 当场修清单 | IT-002 断言 `test_translation_check.py:87`、IT-015 用例 `test_translations.py:221`、IT-014／IT-019 README（`:62`、`:84`）、IT-028 开发守则四节、IT-029 项目概况、IT-030 Part4 回执 `:78-79` 都还在。IT-024 测试态备份已在 `保留-S6R4测试态/` | ✅ |
| 11 | R5 SB 余项 | 否 | — | 否 | R5 各项 | 没有 SB 回执。`docker/apps.json:45` 锁仍是 `1d51db2`（IT-001）；`desk_patches.js:33-44` 的 datatable 适配仍未登记进 README（IT-026）。IT-013、IT-017（含 IT-031）、IT-018、IT-027 均无新证据 | ❌ 仍 `待新Session修`（见下文） |

## 问题详情

建议档位、待裁决点、状态三格按流程规范 §2.3，状态初始都为 `待裁决`。

### 15 屏英文（SL-014 ③，TS-023 未做项第 1 行）

D 判「csv 改不了、交 E」，这个判断属实。但实测 15 屏**都能在 `frappe_china` 内修**，不必归为上游缺陷，所以单列六项。建议用同一份 R9 方案统筹：都属 ADR-0009 的前端补丁，须逐处登记 README、写测试。

| 项 | 清单项 | 现象 | 定位 | 建议 | 建议档位 | 待裁决点 | 状态 |
|---|---|---|---|---|---|---|---|
| **IT-033** | TS-023／SL-014 ③ | 共 4 屏：<br>- `17-work-order-list` 筛选按钮悬停「1 Filter Applied」；<br>- `17`／`19-job-card-list`／`22-sales-invoice-list` 首列排序提示「点击按Item To Manufacture排序」。label 本身有官方译文，问题出在只有首列把原文 label 拼进去 | `frappe/.../filters/filter_list.js:145` 模板串，不经 `__()`；`list_view.js:763` 首列传原文 label，其它列在 `:781-782` 先翻译 | `desk_patches.js` 包 `FilterGroup.update_filter_button` 与 `ListView.get_header_html`，或限定选择器重写 title；csv 补 1～2 键 | `出方案修` | — | 待详细修复方案 |
| **IT-034** | 同上 | 3 屏（总账、库存台账、开账跳转）：「凭证类型」列显示 `Purchase Receipt`、`Journal Entry` 等 DocType 英文名，正文与 title 都是 | `general_ledger.py:760`、`stock_ledger.py:405` 是 Data 列；`formatters.js:36-48` 对 Data 不调 `__()`；两张报表都是 `add_translate_data: 0` | 不建议开 `add_translate_data`：它对整行字符串都调 `_()`。建议包 QueryReport formatter，只对白名单（报表, `voucher_type`）调 `__()` | `出方案修` | — | 待详细修复方案 |
| **IT-035** | 同上 | 4 屏：修改记录显示「从 **null** 变更为 …」 | `version_timeline_content_builder.js:416` 中 `html2text(null)` 得到字符串 "null"，`:417` 的兜底兜不住。`format_content_for_timeline` 是模块内函数，包不到 | 两种修法：包 `frappe.utils.html2text` 让 null 返回空串（全局行为改动），或用限定于时间线的 MutationObserver 改成「（空）」。同时报上游 | `出方案修` | 本 Stage 修，还是延迟并报上游；若修，取全局还是时间线限定 | 待详细修复方案（本 Stage 修，取时间线限定改法并报上游；E 代裁，用户授权「你决定」） |
| **IT-036** | 同上 | 3 屏：CRM 线索、商机列表翻页处的「of」（同组件另有「Load More」）；看板月份 `Nov`、分组值 `Empty` | frappe-ui `ListFooter.vue:20` 写死。**回执归因不准**：echarts 5.6.0 默认已注册中文，`Nov` 是因为 `crm/www/crm.html:2` 写死 `lang="en"`，echarts 按 `document.documentElement.lang` 取 locale；`Empty` 是 `crm/api/dashboard.py:971/1009/1048` 写死的空值标记，不是用户数据，po 里有「空」 | 在 `frappe_china/templates/independent_apps/crm.html` 现有的 `replace` 上再加一个 `lang="zh"`（1 行，要核对 CSS 有无副作用）；`independent_app_labels.js` 加翻页 region 与 `Empty` 键 | `出方案修` | — | 待详细修复方案 |
| **IT-037** | 同上 | 2 屏：CRM 线索、商机详情侧栏占位「Add Territory...」等 13 个，以及「单选 Lead Owner...」（`Select` 用的是字段类型义「单选」） | `crm/fcrm/doctype/crm_fields_layout/crm_fields_layout.py:180` 写 `"Add " + label + "..."`，不经 `_()`；`SidePanelLayout.vue:157` 拼出 `__('Select')`。改全局 `Select` 会波及字段类型名，不可取 | `override_whitelisted_methods` 包 `get_sidepanel_sections`，对 placeholder 套 `_("Add {0}...")`；User 类型字段的占位在注入脚本里重写 | `出方案修` | — | 待详细修复方案 |
| **IT-038** | TS-020 未做项 | 采购发票「创建」下的 `Inter Company Invoice` 显示英文 | `erpnext/.../purchase_invoice.js:228`；分组按钮经 `page.js:622` 渲染，不调 `__()` | 与 IT-033 同类，前端补丁包一层 `__()` | `出方案修` | — | 待详细修复方案 |

### 屏清单与证据

| 项 | 清单项 | 现象 | 定位 | 建议 | 建议档位 | 待裁决点 | 状态 |
|---|---|---|---|---|---|---|---|
| **IT-039** | TS-022／SL-014 ①、TS-023／SL-014 ②；HT-020 | **屏清单按行都有映射，但行内子项有漏**：<br>- 环节 12：经原有入口打开的试算表；<br>- 环节 13：采购收货「菜单→会计凭证」那一屏；<br>- 环节 16、18、20：工单、领料、完工入库三个「由上游创建」单据缺预填态；<br>- 环节 19、20：「完成」填完工数对话框、完工入库必填报错框（R5 IT-020 已点名）；<br>- 表二 `/crm`：线索新建、「转换为商机」、商机产品表与 Add Row、Create Quotation；<br>- 表二 `/raven`：Ctrl+K、设置→AI→Agents；<br>- 表二 `/insights`：查询编辑与 Group & Summarize。<br>另外，BOM 与 Work Order 截到的是「取消所有单据」对话框（`dialog_kind=other`），普通取消框没截到；HT-020「都经 `frappe.confirm`」对这两类不成立，回执没披露 | `Spike/P1S6R6-screens.json`、`P1S6R6-screens-map.md`；`Spike/P1S6R6-screens/confirm-cancel-{bom,work-order}.png` | 补屏后在演示站按 A14 再走一轮：备份→造数→核屏→恢复。BOM、WO 另造一张无下游的已提交单截普通取消框 | `出方案修` | §4.9 的「每行至少一屏」按行读，还是按行内子项读 | 不做（按行读法判通过；BOM／WO 普通取消框随 R9 演示站复核补截） |
| **IT-040** | TS-019／SL-013 ⑥（HT-017） | 回执说 `ht017-accounts-settings.png` 显示「可超额开票的角色」，实际截到的是相邻字段「可超信用额度的角色」。目标字段 `depends_on: over_billing_allowance > 0`，测试站该值为 0，字段被隐藏，`result.json` 的读数取自隐藏节点。键已配上（合并字典 `'Role Allowed to over bill '`→可超额开票的角色），但「界面上看得到」没有证到 | `Spike/P1S6R7/ht017-it011/`；`accounts_settings.json` | 测试站临时把超额开票比率设为 > 0，截图后恢复原值 | `本Session修` | — | 已修复 |
| **IT-041** | TS-019／SL-013 ② | 撞名仍有 1 组既不在异义定词里，也不在同义表里：`From`（`sales_invoice.js:308`，「Fetch Timesheet」对话框的日期起点）与 `Sender` 都显示「发件人」。同一对话框的 `To` 显示「至」。无 context 的 `From` 另有邮件发件人义，csv 拆不开 | 附表 [演示线定词](../R07-代码/P1-S6-R7-D附表-演示线定词.md) §3 | 附表补一行「不可分」，写明代价；或并入 R9 前端补丁，按对话框限定改 | `出方案修` | 记为不可分了结，还是并入 R9 改对话框（该对话框是否算演示线必经屏） | 待详细修复方案 |
| **IT-042** | TS-023／SL-014 ③ | 方案要求 `default_data` 非空的屏「进延迟需求」，DEC-033 定唤醒于 S7 造数。但 3 词（`Nos`、`general`、`Qualification`）没进 S6 登记册。另外，`general` 按整词剥离时作用于全部屏，作用域偏宽 | [S6 概况](../P1-S6-概况.md)登记册只有 `SH-P1S6001`；`P1S6R6-visible-text.cjs:76-90` | 登记 `SH-P1S6002` | `本Session修` | — | 已修复（登记 SH-P1S6002） |

### 译名测试与覆盖清单

| 项 | 清单项 | 现象 | 定位 | 建议 | 建议档位 | 待裁决点 | 状态 |
|---|---|---|---|---|---|---|---|
| **IT-043** | TS-018（D 偏离第 0 条） | `_app_source_strings()` 只认 `_()`／`__()` 字面量调用和 json，认不出本 app 以字面量**按键**取用的键：`website_translation.SOURCES` 元组、`independent_app_labels.js` 的 Set、`desk_patches.js` 的 `translate()` 别名、`install.PROBE_SOURCE`，共 25 键。这些键现在都有中文，但再按 A15 清场会重犯误删 15 行的错误 | `frappe_china/tests/test_translations.py:86-117` | 取法补这一类，或改为这些键集中登记、测试断言其在 csv 中。属于改既有测试判据 | `出方案修` | — | 待详细修复方案 |
| **IT-044** | TS-021 未做项第 3 行 | `_PLACEHOLDER` 把含未闭合 `{{` 的源词从 `{{` 吞到句末，任何中文译文都过不了占位符检查。该源词 `Naming series '{0}' … '{{' separator…` 因此在演示站显示英文。E 实测：改成要求闭合的 `\{\{\s*[^{}]+?\s*\}\}` 后两边一致，csv 里没有别的源词被旧正则误吞 | `test_translations.py:236`；`translation_whitelist.py:144` | 改正则，补译该键并移出白名单，加一条判别力用例 | `本Session修` | — | 已修复 |
| **IT-045** | TS-017（D 偏离第 1 条） | 第五种依据形态「本 app 自有源词」只有 `Formula`、`Yearly Amount` 两条在用，判为合理。但正则只看前缀，任何条目写上这几个字都能过形态检查 | `test_translations.py:235` | 补断言：用这种形态的键必须属于 `_app_source_strings()` | `本Session修` | 追认偏离第 1 条 | 已修复 |
| **IT-046** | TS-017（D 偏离第 2 条） | 依据 DEC-026 的 11 条里，`Get Sub Assembly Items`、`Get Items for Purchase…`、`Update Rate and Availability` 实出于 DEC-027 的补充方案；全清单 119 条里有 10 条 `ours == official`，是无效覆盖（无害） | `translation_overrides.py`；`R04-代码/P1-S6-R4-D方案补充-Desk悬停提示.md:7` | 3 条依据改为 DEC-027；10 条无效覆盖从 csv 与清单删掉，回落官方，显示不变 | `本Session修` | 无效覆盖删掉，还是保留 | 已修复 |
| **IT-047** | TS-017／SL-011 ③ | csv 有 178 行带 context，其中 165 行与官方无 context 译文不同（例如 `Accepted Warehouse:Purchase Receipt` 官方「仓库」，我方「验收仓库」）。官方 po 没有同键 context，按方案「键交集」的定义不进覆盖清单，字面合规。但它们在渲染点上实际改变了官方显示，覆盖清单的依据守卫管不到 | `zh.csv`；`test_translations.py:154-156` | 要么扩大清单口径（context 行也须写依据），要么明确不管、登延迟 | `延迟或不修` | 是否把 context 行纳入依据守卫 | 延迟（SH-P1S6003） |
| **IT-048** | TS-019（DJ-001） | DJ-001 的三处已知代价都属实：<br>- `Available`→工位可用：波及 Raven `Profile.tsx:28`、`useSetAvailability.ts:9` 的个人状态；<br>- `Operations`→工序清单：波及 `company.py:473` 新建公司时的部门名；<br>- `Finish`→完工：波及 CRM `Questionnaire.vue:96`。<br>都不在演示面上，但 Raven 状态显示「工位可用」错得明显 | D 讨论记录 DJ-001 | 接受代价；或把 Raven 一处并入 R9，用独立前端限定适配修 | `出方案修` | 三处是否都接受；Raven 那处是否修 | 待详细修复方案（只修 Raven 一处；其余两处接受代价） |
| **IT-051** | TS-017／TS-019 | `Lft`／`Rgt`／`rgt`／`old_parent`／`Idx` 五条在 TS-017 判删，TS-019 又以「DEC-001 演示线档补缺」回到覆盖清单。方案只许以「演示撞名」重进，口径不一，回执没记这处偏离 | `translation_overrides.py:56,64,74,95,96` | 依据本身成立（演示面树字段，官方是原样英文），追认 | `延迟或不修` | 追认 | 不做（追认） |

### 回执与工作量

| 项 | 清单项 | 现象 | 定位 | 建议 | 建议档位 | 待裁决点 | 状态 |
|---|---|---|---|---|---|---|---|
| **IT-049** | TS-024／SL-015 ④ | 回执只说 S6「已超过」11.25–18 人日，没有实耗数字，也没有增量数字。理由是 AI 执行没有人日实测 | D 回执「工作量」节 | Stage 收口回写路线文档时定口径（日历日、Round 数、折算当量） | `延迟或不修` | 接受定性结论、留到收口定口径，还是现在补数 | 不做（Stage 收口按 RW-09 回写时定口径） |
| **IT-050** | 全部 | 回执表述与实测不一致，数字与判断都不受影响，详见下节 | D 回执 | 以本报告为准，不改 D 回执 | `延迟或不修` | — | 不做（以本报告为准） |

## 与 D 回执声称不一致处（Spec 复核建议第 2 类）

| 回执声称 | 实测 |
|---|---|
| TS-017：旧 csv 全表红「混排 3095，合计 5370 行」 | 混排 2974，合计 5324。差额应来自 ALLOW 此后从约 9 个扩到 44 个；TS-017 时点的守卫文件不在 git 里，无法复现 |
| TS-017、偏离第 1 条：`_BASIS_FORM` 在 `test_translations.py:217` | 现在在 `:235`（TS-018 加用例后下移） |
| 偏离第 2 条：`Lft` 判删 | 现在在覆盖清单里（IT-051） |
| TS-018：161 个被删键「全部等于官方」 | 当时成立；现在其中 2 键已由 TS-019 重新覆盖 |
| TS-019：同义 59 组、异义 19 组；「两者之外」0 组 | 同义 60 组（另有机械同义 80 组），异义 18 组（写 19 行 csv）；两者之外剩 1 组（IT-041） |
| TS-019：演示面无中文键「剩 40 个，全是代码值，进白名单」 | 现基线 47 个，只有 23 个在 `UNTRANSLATED`；编号规则类不在 main.pot，不需要进白名单；另有 `JAN`→「01」是官方错译（见清单外发现） |
| TS-019：HT-017 截图显示「可超额开票的角色」 | 截到的是相邻字段（IT-040） |
| TS-021：「例外只在 `UNTRANSLATED`（228 条）」 | `UNTRANSLATED` 实为 213 键；228 是按 app 累加的命中数 |
| TS-022：§4.9「全部有映射」 | 行级成立，子项级有漏（IT-039） |
| TS-022：反证后 `git status` 为空 | 实际按「与造前一致」核，当时并不为空 |
| TS-023：确认框 31 屏全过，HT-020 成立 | BOM、WO 截到的是 `_cancel_all` 对话框（IT-039） |
| 未做项第 1 行：`Nov` 因 ECharts 未注册中文；`Empty` 属数据；③ 类属上游缺陷 | 根因是 `crm.html` 的 `lang="en"`；`Empty` 是代码写死的标记；两者都能在本 app 修（IT-036） |
| 复核建议第 1 条：「`.form-details` 在 v16 不命中」 | 它仍在 `form_sidebar.html:34`，装的是侧栏标题 |
| TS-024：「`frappe_china` 只改了 zh.csv」 | 当时未提交，现在已提交为 `cf8a9ba` |

## D 偏离与执行判断的追认（交接点名 ③④）

| 项 | 内容 | E 意见 |
|---|---|---|
| 偏离第 0 条 | TS-018 误删 15 行，已恢复 | 恢复属实，15 行都在。方案缺口另立 IT-043 |
| 偏离第 1 条 | `_BASIS_FORM` 加第五种形态 | 可追认。只有 2 条用到，删 `Formula` 会打掉 S5 的装序检查。补强见 IT-045 |
| 偏离第 2 条 | 「留」的依据映射 | 可追认。抽 10 组都能回到原文。DEC-026 那组偏弱，见 IT-046 |
| 偏离第 3 条 | TS-017 没守先红后绿 | 可追认。git 里只有一次提交，次序无从证；变异检验证明判别力用例在守卫失效时确实失败，预期值也取自方案原文，不是照实现反推 |
| DJ-001 | S3 改词按渲染点落：字段写 context 行，裸渲染点写无 context 行 | 可追认。方案没规定行形态，这种落法影响面更小。代价见 IT-048 |
| DJ-002 | 撞名按渲染点重算，分机械同义、人工同义、异义 | 可追认。E 重算结果与 D 的分类对得上；机械同义 80 组全看过，没有误合并。要补闭环 IT-041，计数更正见上节 |

## R5 SB 余项（复核结果：未执行）

R6 方案 §七 ④ 允许它们与 R7 并行做，但实际没有起 SB，各项状态不变：

| 项 | 内容 | 状态 |
|---|---|---|
| IT-001 | `docker/apps.json` 的 `frappe_china` 锁 `1d51db2`，HEAD 为 `cf8a9ba` | 待新Session修 |
| IT-013 | 发票裸渲染点补实测（两条原定做法、筛选下拉与表单截图、撤钩反证，撤钩预期「未付」，DEC-036） | 待新Session修 |
| IT-017（含 IT-031） | 导航 `modified` 实验重做，并披露直接改库的操作及时序 | 待新Session修 |
| IT-018 | 不刷新六例补命令序列，例 1、5 先验实时通道 | 待新Session修 |
| IT-026 | datatable title 适配：追认或撤掉，补告警、缺接点用例与实页取证 | 待新Session修 |
| IT-027 | 独立前端覆盖表补锁定 commit、记 `bridgeMessages` 偏离，做非管理员 CRM 渲染级复核 | 待新Session修 |

## 清单外发现（不计入状态值，交用户定去向）

核对中顺带看到的问题，不在 R6 方案的验收条件里。按 confirm 纪律，本步不开放查漏，也不修，只列出来，供用户决定并入 R9 方案、交 F 审核，还是进延迟需求。

| 键／位置 | 现状 | 问题 | 建议 |
|---|---|---|---|
| `JAN`（`Item Barcode.barcode_type` 选项，在演示面上） | 01 | 官方错译，大概是与月份 JAN 混了 | csv 写回原样，并登记覆盖 |
| `To`（`UOM Conversion Factor.to_uom`） | 至 | 同一张表的 `From` 已改为「原单位」，两边不对称 | 补 context 行，例如「目标单位」，先查占用 |
| `Manufacturing Setup`（批量档） | 生产设置 | 与 `Manufacturing Settings` 官方译名撞；同族的 Stock／Selling 等 Setup 都译「…初始化」 | 生产初始化 |
| `CN Tax`（本 app `workspace_sidebar/cn_tax.json:4` 的 title） | 无译文 | `_app_source_strings` 跳过 Workspace Sidebar 类 json，测试抓不到 | 补一行，例如「中国财税」 |
| 称呼 `Master`／`Mrs`／`Ms`／`Miss`／`Madam` | 主表／女士×4 | 官方错译；称呼下拉里四个「女士」分不开 | 交用户定词 |

**去向（用户裁决「其它按建议来」）**：五条都并入 R9 方案。前四条按上表建议改；称呼一条由 C 步给候选词，交用户定。

## 用户裁决

2026-10-12，用户对四个待裁决点逐条作答，其余按建议来（流程规范 §2.3 执行规则 2）：

| # | 待裁决点 | 用户裁决 | 落到哪 |
|---|---|---|---|
| 1 | IT-039：§4.9「每行至少一屏」按行读，还是按子项读 | **按行算** | IT-039 判通过，状态改「不做」。BOM／WO 普通取消框未截、HT-020 有例外这两点，留作 R9 演示站复核时顺带补截，不单列 |
| 2 | IT-035：`null` 本 Stage 修还是延迟；若修，取哪种改法 | **由 E 定，取长远更好的** | E 定：**本 Stage 修，取时间线限定改法**（MutationObserver 只作用于修改记录的 `<b>null</b>`，改成「（空）」），并向上游报缺陷。不取「包 `frappe.utils.html2text`」，因为那是全局行为改动，副作用难验，而且上游修好后不会自动退场 |
| 3 | IT-041：`From`（Fetch Timesheet 日期）记不可分，还是并入 R9 | **放进 R9 前端补丁去改** | IT-041 改档 `出方案修` |
| 4 | IT-048：Raven 个人状态「工位可用」要不要修 | **修** | IT-048 改档 `出方案修`，只修 Raven 一处（独立前端限定适配）；`Operations`、`Finish` 两处接受代价 |
| 5 | 其余各项 | **按建议来** | 各项取建议档位；IT-047 进登记册 `SH-P1S6003`；IT-049、IT-050、IT-051 不做；清单外发现并入 R9 |

## 当场修清单

| # | 对应未通过项 | 改动位置（文件:行） | 复核 | 用户确认于 |
|---|---|---|---|---|
| 1 | IT-040 | `Spike/P1S6R8-E/fix/ht017.cjs`（新）→ `Spike/P1S6R8-E/fix/ht017/ht017-accounts-settings.png`、`result.json` | 测试站表单只在内存里把超额开票比率设为 10，让字段显示出来；红框内显示「可超额开票的角色」（实看截图）。随即 `reload_doc` 丢弃改动，库里值前后都是 `0.0`（`obill.py` 读两次），没有保存 | 2026-10-12「其它建议来」 |
| 2 | IT-042 | [S6 概况](../P1-S6-概况.md)登记册新增 `SH-P1S6002`（默认数据 3 词，唤醒于 S7 造数）；同处另登记 IT-047 → `SH-P1S6003` | — | 同上 |
| 3 | IT-044 | `frappe_china/tests/test_translations.py`：`_PLACEHOLDER` 改为必须闭合（`\{\{?\s*[^{}]+?\s*\}\}?`），新增用例 `test_placeholder_requires_closing_brace`；`zh.csv` 补译 `Naming series '{0}' … '{{' separator…`；`tests/translation_whitelist.py` 删去该键 | 新旧正则对 csv 全表比对（`fix/regex_diff.py`）：差异只有 5 行 Jinja `{{ … }}`，新正则抓得更完整；新正则下源词与译文不一致 0 行。判别力：旧正则下新用例的两条断言都为假，新正则下都为真（`fix/discrim.out`）。`format` 实跑后，译文显示「不含标准分隔符「.」或「{」」 | 同上 |
| 4 | IT-045 | `test_translations.py`：新增 `_misused_own_basis()`，`test_override_basis_forms` 加断言，新增用例 `test_own_basis_requires_app_source` | 构造的「Other」条目被报出；现清单 0 条误用 | 同上 |
| 5 | IT-046 | `tests/translation_overrides.py`：4 条 Button 字段 label（`Get Items for Purchase / Transfer`、`Get Items for Purchase Only`、`Get Sub Assembly Items`、`Update Rate and Availability`）依据由 DEC-026 改为 DEC-027；10 条 `ours == official` 的无效覆盖从清单与 `zh.csv` 删除（`Accounts Receivable`、`Add Row`、`Cash Flow`、`days`、`Deals`、`Debtors`、`Global Defaults`、`Leads`、`Send`、`Value`），回落官方后显示不变 | 先核 10 键：`NAMED_TERMS`、`website_translation.SOURCES`、`independent_app_labels.js` 都按键读合并字典，官方值与原 csv 值相同，取到的译文不变。脚本 `fix/it046.py`；csv 5745 → 5735 → 5736 行（+1 为 IT-044） | 同上 |

**当场修后复跑全量**：integration **255/255**、导航 **2/2**，合计 **257/257、0 跳过**（比修前 255 多 2 条，即新增的两条用例），1824 秒，日志 `Spike/P1S6R8-E/fix/full-regression-after-fix.log`；Node **29/29**。

**复核**：测试站 `clear-cache` 后五个译名相关模块 `test_translations` 14/14（原 12 条，新增 2 条）、`test_named_terms` 2/2、`test_translation_quality` 9/9、`test_translation_check` 8/8、`test_website_translation` 3/3（`fix/tests-after-fix.log`）。演示站 `clear-cache` 后 `translation_check.run`：通过。全量回归复跑结果见下节。

## 全量回归 + 未执行项

- **全量回归（本次实跑）**：测试站 `clear-cache` 后跑 `run-tests --app frappe_china`，integration **253/253**，导航 **2/2**，合计 **255/255、0 跳过**，2068 秒，日志 `Spike/P1S6R8-E/full-regression.log`。比 R5 基线 242 多 13 条，与 R7 终跑同数。
- **Node 用例（本次实跑）**：宿主 `node --test frappe_china/tests/*.cjs`，**29/29**，基线 29。
- **译名自检**：演示站 `translation_check.find_problems()` 为 `[]`（只读）。
- **未执行项反向确认**：
  - 六个上游 app 的 `status` 为空，HEAD 与锁一致；
  - SB 余项相关的文件（`docker/apps.json` 的锁、`desk_patches.js` 的 datatable 段、README 独立前端表）R7 没动；
  - 本步没改 csv 与代码。主仓库只多了未跟踪的 `Spike/P1S6R8-E/`。子 Agent 在宿主按路径载入测试模块，生成了 `frappe_china/tests/__pycache__/*.cpython-310.pyc`，这些文件被 git 忽略；容器用 cpython-314，不受影响。

## 复核建议

1. **最该先看：15 屏英文能不能在本 Stage 修完（IT-033～IT-038）**。完成标志第 1 条是「全程无未译英文词」，这几项不修，S6 就收不了口。D 把其中 4 屏归为「上游缺陷」，实测不对。
   - 查法 1：`crm.html` 那一行，看 `frappe-bench/apps/crm/crm/www/crm.html:2` 的 `lang="en"`，对照 `echarts/lib/core/locale.js:55-58` 取 locale 的逻辑。
   - 查法 2：`list_view.js:763` 对比 `:781-782`，确认首列 label 是在拼串时漏了翻译，而不是没有译文。
2. **屏清单的「每行」读法（IT-039）**。按行读，D 已经达标；按子项读，要补十余屏，还要在演示站再走一轮 A14。这是 C 方案验收条件本身的歧义：SL-014 ① 写的是「每行至少一屏」，而 §4.9 行内列了多个交互点。本报告按子项读判了不通过，用户若取行级读法，该项可改判。
3. **验收条件读法可疑的另一处：IT-022「应收账款各只出现一次」**。`Account.account_type` 选项因 S3 改词，本来就没有「应收账款」（0 次）。本报告按原意（防出现两个「应收账款」）判通过。查法：`Spike/P1S6R7/ts023/it022/` 两张图。
4. **拿不准处**：
   - 样本外复判 40 条，不可用 0 条，是零事件，95% 上界约 7.5%。批量档可用率的结论靠的是 D 的 100 条加 E 的 60 条，不是全量；
   - IT-041 中的「Fetch Timesheet」对话框是否在演示线上，本步没有查证；
   - IT-035 若取「包 `html2text`」修法，那是全局行为改动，副作用未实测。

## 总体结论

**状态值：`有未通过项`**（裁决后仍是：`本Session修` 5 项已修复，其余去向见文末「交出去向」）

- 9 个任务中，TS-016、TS-017、TS-018、TS-020、TS-021 通过（其中 TS-017、TS-018 附带补强项）；TS-019、TS-022、TS-023 有未通过项；TS-024 只差工作量数字。
- 本报告新增未通过项 19 个（IT-033～IT-051），另有 R5 SB 余项 6 个仍未做。
- 全量回归 255/255、Node 29/29，无回归。

**按建议档位分组**（供裁决时对照）：

| 建议档位 | 项 |
|---|---|
| `本Session修` | IT-040、IT-041、IT-042、IT-044、IT-045、IT-046 |
| `新Session修` | （R5 SB 余项）IT-001、IT-013、IT-017（含 IT-031）、IT-018、IT-026、IT-027 |
| `出方案修` | IT-033、IT-034、IT-035、IT-036、IT-037、IT-038、IT-039、IT-043 |
| `延迟或不修` | IT-047、IT-048、IT-049、IT-050、IT-051 |

按 `plannedDev` 出口路由，本步暂停，由用户逐项裁决。`本Session修` 当场修完回本步复核；`新Session修` 唤起 SB；`出方案修` 回 C（R9）；判延迟的进登记册。

## 交出去向（流程规范 §2.3 执行规则 4；按裁决后档位）

| 去向 | 项 | 下一步 |
|---|---|---|
| `出方案修` → 步骤 C | IT-033～IT-038（15 屏英文与 `Inter Company Invoice`）、IT-035（时间线限定改法，E 已代裁）、IT-041（Fetch Timesheet 的 `From`）、IT-043（清场取法补字面量按键一类）、IT-048（Raven「工位可用」一处）；清单外发现 5 条（`JAN`、`To` 单位、`Manufacturing Setup`、`CN Tax`、称呼词）；R9 演示站复核时顺带补截 BOM／WO 普通取消框 | 新 Session 起 C（R9），以本报告为依据出方案，再 D 执行、回 E 复核 |
| `新Session修` → 唤起 SB | R5 余项 IT-001、IT-013、IT-017（含 IT-031）、IT-018、IT-026、IT-027 | 新 Session 起 SB（附属 R5，`P1-S6-R5-SB修复回执`）。这些项都不碰 csv。IT-026 动 `desk_patches.js`，与 R9 前端补丁改同一文件，建议排在 R9 的 D 之前或之后，不要并行 |
| 已修复 | IT-040、IT-042、IT-044、IT-045、IT-046 | — |
| 延迟／不做 | IT-047 → `SH-P1S6003`；IT-039（按行读法判通过）、IT-049、IT-050、IT-051 不做 | — |
