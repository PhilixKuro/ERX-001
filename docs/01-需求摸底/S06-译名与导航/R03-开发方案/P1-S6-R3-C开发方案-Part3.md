# P1-S6 开发方案 · Part3：业务流程导航、树形点检、开账凭证跳转、不刷新六例

**来源需求**：[B 需求文档](../R02-需求文档/P1-S6-R2-B需求文档.md) §4.6、§4.7、§4.8.2、§4.8.3（需求 TS-008／009／011／012）＋ [C 讨论记录](P1-S6-R3-C讨论记录.md) DEC-020／021｜**前置依赖**：Part1 TS-004（侧栏要链改名后的底稿）、Part2 TS-006（分节与条目的译名）｜**日期**：2026-10-09｜**编写者**：Claude（Opus 5.5）
**总纲**：[P1-S6-R3-C开发方案-总纲.md](P1-S6-R3-C开发方案-总纲.md)（执行纪律见总纲 §九，本 Part 不重复）

## 接口契约

**自有图标** `frappe_china/desktop_icon/business_flow.json`（文件名 = `scrub(label)`，否则 migrate 当孤儿删掉，`sync.py:244-265`）：

```json
{
 "doctype": "Desktop Icon", "name": "Business Flow", "label": "Business Flow",
 "app": "frappe_china", "standard": 1, "hidden": 0, "idx": -1,
 "icon_type": "Link", "link_type": "Workspace Sidebar", "link_to": "Business Flow",
 "bg_color": "blue", "restrict_removal": 0, "roles": [],
 "modified": "<写入时刻，此后每改一次调大>"
}
```

- **图标 label 必须与侧栏 title 相同**（不区分大小写）：boot 的可见性判断取 `workspace_sidebar_item[label.lower()]`（`desktop_icon.py:195-196`），点击后按 label 找侧栏（`desktop.js:56`），`link_to` 两处都不用。
- `parent_icon` 不写（顶层）；`idx: -1`（总纲 A8）。

**自有侧栏** `frappe_china/workspace_sidebar/business_flow.json`：

```json
{
 "doctype": "Workspace Sidebar", "name": "Business Flow", "title": "Business Flow",
 "app": "frappe_china", "standard": 1, "module": "CN Tax", "header_icon": "<见 TS-010 第 4 步>",
 "items": [ <SidebarItem>… ],
 "modified": "<同上>"
}
```

- `module` **显式写 `CN Tax`**：LG-003 实测时不写 `module` 被自动推成 `Stock`（取条目里出现最多的模块，`workspace_sidebar.py:88-105`）。
- `<SidebarItem>` 两种形态（字段取值照 `erpnext/workspace_sidebar/selling.json`）：
  - 分节：`{"type": "Section Break", "label": "<源词>", "link_type": "DocType", "child": 0, "indent": 1, "collapsible": 1, "keep_closed": 0}`
  - 条目：`{"type": "Link", "label": "<源词>", "link_type": "DocType"|"Report"|"URL", "link_to": "<对象名>"(URL 项不写), "url": "<地址>"(仅 URL 项), "child": 1, "indent": 0, "collapsible": 1, "keep_closed": 0, "icon": "<可省>"}`
- 条目**不写 `filters`、`route_options`**——写了会被强制成 `/view/list`，树形 DocType 就进不了树视图（`sidebar_item.js:59-71`）。

**图标资源**：`frappe_china/public/icons/desktop_icons/solid/business_flow.svg` 与 `…/subtle/business_flow.svg`（两种 variant 都放，`boot.py:531`；侧栏头部固定用 `solid`，`sidebar_header.js:302`）。

```javascript
// ---- frappe_china/public/js/desk_patches.js（续 Part2 TS-008） ----
// 开账凭证跳总账：库存类单据走 StockController 原型，覆盖 show_general_ledger。
// 是开账（purpose === "Opening Stock" 或 is_opening === "Yes"）时，在原 route_options 上加 show_opening_entries: 1；
// 非开账原样调用原方法。
erpnext.stock.StockController.prototype.show_general_ledger = function () {}

// ---- frappe_china/public/js/opening_ledger.js（新增，doctype_js 下发给 Journal Entry、Payment Entry） ----
// refresh 在 erpnext 的 refresh 之后跑（HT-005）：is_opening === "Yes" 且已提交时，
// 移除 erpnext 加的那个总账按钮，加一个同名、同分组、route_options 多带 show_opening_entries: 1 的按钮。
frappe.ui.form.on("Journal Entry", { refresh(frm) {} });
frappe.ui.form.on("Payment Entry", { refresh(frm) {} });
```

## 切片划分与验收

| 切片 | 功能点 | 验收条件 |
|---|---|---|
| **SL-007** 业务流程导航 | 需求 TS-008／009；DEC-004～007／009／018／020／021；`PH-P1022`／`1059`；LG-001／002；需求 §4.6、§4.7 | ① 测试站 `migrate` 后：`tabDesktop Icon` 有 `Business Flow`（`app=frappe_china`、`idx=-1`、`hidden=0`）、`tabWorkspace Sidebar` 有 `Business Flow`（`module=CN Tax`）；首页第一个图标显示「业务流程」且图标是 svg 不是首字母（截图）。② 点图标进入侧栏，分节依次为「基础资料／销售／采购／库存／生产／财务／报表」，条目数与 TS-010 第 2 步的表一致（脚本取 boot 的 `workspace_sidebar_item["business flow"]` 计数＋截图）；同一侧栏内中文 label 无重名（脚本断言）。③ 逐项点击可达：DocType 项打开列表或树、Report 项打开报表、URL 项在新标签打开 `/crm/leads`、`/crm/deals`、`/crm/dashboard`、`/raven`（CDP 脚本逐项点、记最终 URL 与页面标题，零失败）。④ 原有入口不动：改前改后导出 `tabDesktop Icon`、`tabWorkspace Sidebar`、`tabWorkspace Sidebar Item` 中 `app != 'frappe_china'` 的全部行（`name, modified, hidden, idx`），逐字相同（脚本 diff 为空）。⑤ 树形点检：`Account`／`Warehouse`／`Cost Center` 从自有侧栏点进，刷新前显示树视图且有节点；`Company`／`Employee` 显示列表且有记录（各一张截图；测试站先确保各有数据）。⑥ 第二次 `migrate` 不重复导入、不报错（`modified` 未变时跳过）。⑦ 异常路径：把侧栏 json 的 `modified` 调回旧值后改一个 label 再 migrate——库里 label **不变**（证明 A9 的「必调 `modified`」不是多余）；恢复后再 migrate，库里变成新 label。⑧ `CN Tax` 空侧栏 json 不改，库里该记录 `modified` 不变 |
| **SL-008** 开账凭证跳转 | 需求 TS-011；`PH-P1061`；需求 §4.8.2 | ① 测试站提交一张 `purpose=Opening Stock` 的库存调账，点「查看 → 会计凭证」：总账显示该凭证的分录行（非全零；截图＋报表接口返回行数 ≥ 2）。② 提交一张 `is_opening=Yes` 的日记账凭证，点其总账按钮：同上。③ 普通（非开账）库存凭证与日记账凭证点同一按钮：`route_options` 不含 `show_opening_entries`（CDP 读 `frappe.route_options`）、总账显示与改前一致。④ 异常路径：`desk_patches.js` 加载时 `erpnext.stock.StockController` 不存在（如未来 erpnext 改名）——补丁不抛错、在控制台 `console.warn` 一句并跳过（代码路径用一次 CDP 注入 `delete erpnext.stock.StockController` 后重载 `desk_patches.js` 验） |
| **SL-009** 不刷新六例 | 需求 TS-012；`PH-P1002`；LG-008；需求 §4.8.3 | ① 六例每例一行结论：现象／复现步骤／环境（站点、浏览器、实时通道是否通）／复现或未复现／处置（已修＋修法与登记、或不修＋理由）。② 例 1、5 的结论引 SL-007 ⑤ 的截图。③ 例 2 记「不属不刷新一类，图谱 LG-073 死代码，不修」。④ 复现了的例：修后按同一步骤再走一遍不再出现（截图或录屏帧）；修法若是前端覆盖，README 登记表有该行。⑤ 异常路径：复现不了的例，复现步骤写到可照做的程度（含数据准备），**不硬修** |

**执行每个切片前，对照该切片验收条件检查方案覆盖性——如发现按方案写出的代码无法通过验收条件，暂停反馈，不硬写。**

## 任务清单

| 任务 | 对应切片 | 可并行否 |
|---|---|---|
| TS-010 业务流程图标、svg 与侧栏 | SL-007 | 否 |
| TS-011 树形点检 | SL-007 | 否（依赖 TS-010） |
| TS-012 开账凭证跳转 | SL-008 | 与 TS-010／011 文件不相交，可并行；但都在测试站上操作，单人时按序 |
| TS-013 不刷新六例 | SL-009 | 否（依赖 TS-010） |

---

## 任务 TS-010：业务流程图标、svg 与侧栏（对应 SL-007）

### 目标
需求 §4.6：首页最前一个「业务流程」图标，进入后一张侧栏走完演示，原有入口一个不动。

### 具体改动
1. **改前快照**：测试站导出 SL-007 ④ 所列三张表 `app != 'frappe_china'` 的行到 `Spike/P1S6R4-nav-before.json`。
2. **条目表**（DEC-020、总纲 A7）——label 列是写进 json 的英文源词，「显示」列是 Part2 TS-006 之后合并字典的预期值，**以执行时 `get_all_translations` 实取为准**、回执记差异：

   | 节（源词） | label（源词） | link_type | link_to／url |
   |---|---|---|---|
   | `Master Data` | `Company` | DocType | `Company` |
   | | `Global Defaults` | DocType | `Global Defaults` |
   | | `Fiscal Year` | DocType | `Fiscal Year` |
   | | `Chart of Accounts` | DocType | `Account` |
   | | `Cost Center` | DocType | `Cost Center` |
   | | `Warehouse` | DocType | `Warehouse` |
   | | `Unit of Measure (UOM)` | DocType | `UOM` |
   | | `Item` | DocType | `Item` |
   | | `Item Price` | DocType | `Item Price` |
   | | `Workstation` | DocType | `Workstation` |
   | | `Operation` | DocType | `Operation` |
   | | `Routing` | DocType | `Routing` |
   | | `BOM` | DocType | `BOM` |
   | | `Customer` | DocType | `Customer` |
   | | `Supplier` | DocType | `Supplier` |
   | | `Employee` | DocType | `Employee` |
   | `Selling` | `Leads` | URL | `/crm/leads` |
   | | `Deals` | URL | `/crm/deals` |
   | | `Dashboard` | URL | `/crm/dashboard` |
   | | `Quotation` | DocType | `Quotation` |
   | | `Sales Order` | DocType | `Sales Order` |
   | | `Delivery Note` | DocType | `Delivery Note` |
   | | `Sales Invoice` | DocType | `Sales Invoice` |
   | `Buying` | `Material Request` | DocType | `Material Request` |
   | | `Supplier Quotation` | DocType | `Supplier Quotation` |
   | | `Purchase Order` | DocType | `Purchase Order` |
   | | `Purchase Receipt` | DocType | `Purchase Receipt` |
   | | `Purchase Invoice` | DocType | `Purchase Invoice` |
   | `Stock` | `Stock Reconciliation` | DocType | `Stock Reconciliation` |
   | | `Quality Inspection` | DocType | `Quality Inspection` |
   | `Manufacturing` | `Production Plan` | DocType | `Production Plan` |
   | | `Work Order` | DocType | `Work Order` |
   | | `Stock Entry` | DocType | `Stock Entry` |
   | | `Job Card` | DocType | `Job Card` |
   | `Finance` | `Payment Entry` | DocType | `Payment Entry` |
   | | `Journal Entry` | DocType | `Journal Entry` |
   | | `Accounts Receivable` | Report | `Accounts Receivable` |
   | | `Accounts Payable` | Report | `Accounts Payable` |
   | | `Month End Closing Voucher` | DocType | `Month End Closing Voucher` |
   | | `Cash Flow Worksheet` | DocType | `Cash Flow Worksheet` |
   | | `Bank Statement Preprocess` | DocType | `Bank Statement Preprocess` |
   | `Reports` | `小企业资产负债表` | Report | `小企业资产负债表` |
   | | `小企业利润表` | Report | `小企业利润表` |
   | | `小企业现金流量表` | Report | `小企业现金流量表` |
   | | `漏科目检查` | Report | `漏科目检查` |
   | | `General Ledger` | Report | `General Ledger` |
   | | `Stock Ledger` | Report | `Stock Ledger` |
   | | `Stock Balance` | Report | `Stock Balance` |
   | | `Stock and Account Value Comparison` | Report | `Stock and Account Value Comparison` |
   | | `BOM Variance Report` | Report | `BOM Variance Report` |
   | | `AI Assistant` | URL | `/raven` |

   - 四张自有报表的名字本身是中文（子 Agent 查实），label 直接写中文，无需 csv。
   - `Dashboard` 源词现译「数据面板」，在本侧栏内不与其它条目重名；若执行时发现与侧栏头部或其它固定文案同名，改用新起源词 `Sales Dashboard`（未占用）并加 csv 行，回执记。
   - URL 项一律新标签打开（`sidebar_item.html:26`，模板写死），不可配置——回执注明这是框架行为。
   - **CRM 的 URL 先实点确认**：`/crm/leads`、`/crm/deals` 是别名、正式路径带 `/view/:viewType?`（`crm/frontend/src/router.js:35-58`）；两种都试，取能直接打开列表的那个。
3. **写 json**：按接口契约手写两个文件（总纲 A9）；`modified` 取写入时刻。
4. **header_icon**：从 frappe 已有图标名里选一个（`erpnext/workspace_sidebar/*.json` 用过的 `sell`、`stock`、`organization` 等之外，取一个表达「流程」的，如 frappe 图标集中存在的 `workflow` 或 `git-branch`；执行时在 `frappe/public/icons/` 下核实存在再用，不存在则取 `organization`）。
5. **svg**：画一个 24×24、单色、与 erpnext `solid/` 下图标同尺寸同风格的流程图标（三个节点由箭头相连），`solid/` 填充版、`subtle/` 线框版；文件名 `business_flow.svg`。`bench build --app frappe_china` 后核 `frappe.boot.desktop_icon_urls.frappe_china` 两个 variant 都含该路径（HT-009）。
6. **migrate 与核对**：`bench --site test.localhost migrate`、`clear-cache`；按 SL-007 ①～③、⑥、⑦、⑧ 逐条做。③ 的 CDP 脚本放 `Spike/P1S6R4-nav-click.js`（沿用 `Spike/V16-cdp-run.js` 的启动与登录写法），输出 `Spike/P1S6R4-nav-click.out.json`。
7. **改后快照**并与第 1 步 diff（SL-007 ④）。
8. LG-002 处置：自有图标有 svg，侧栏头部下拉不出 `src="undefined"`（CDP 记录页面请求，无 `/undefined` 请求）。

### 验证方式
SL-007 ①～④、⑥～⑧。

---

## 任务 TS-011：树形点检（对应 SL-007 ⑤）

### 目标
EN-001／DEC-009：五个对象从自有侧栏点进不空白。

### 具体改动
1. 再 grep 一次侧栏全部 DocType 的 json 里 `"is_tree": 1`（需求 §4.7），确认集合为 `Account`／`Warehouse`／`Cost Center`／`Company`／`Employee`；多出来的一并点检。
2. 测试站确保各有数据：用测试公司的科目、仓库、成本中心；`Employee` 若为 0 条，建一条 `_FCT` 前缀员工，点检后删。
3. 新浏览器档案（清空 `localStorage` 与 `__UserSettings` 中这几个 DocType 的 `last_view`）从首页图标进侧栏逐个点，**不刷新**截图；再在「曾经进过列表视图」的状态下（先手动打开 `/desk/account/view/list`，再从侧栏点）重复一次——这是 V-07 指出的 `last_view` 通道。
4. 空白则按 V-07 的路径查（`router.js:223-231`、`list_view.js:7-22`）并修；修法若是前端覆盖，登记 README。

### 验证方式
SL-007 ⑤；两轮截图（干净状态／进过列表视图）共 10 张以上。

---

## 任务 TS-012：开账凭证跳转（对应 SL-008）

### 目标
需求 §4.8.2：开账凭证点总账按钮直接显示其分录；普通凭证不变。

### 具体改动
1. `desk_patches.js` 加库存类覆盖（HT-004）：
   ```
   const SC = erpnext?.stock?.StockController;
   if (!SC) { console.warn("frappe_china: erpnext.stock.StockController 不存在，开账凭证跳总账补丁未生效"); }
   else {
       const orig = SC.prototype.show_general_ledger;
       SC.prototype.show_general_ledger = function () {
           const doc = this.frm.doc;
           if (doc.purpose !== "Opening Stock" && doc.is_opening !== "Yes") return orig.call(this);
           // 复刻原方法（stock_controller.js:114-134），route_options 多一项 show_opening_entries: 1
       };
   }
   ```
   复刻而非「调原方法后改按钮」：原方法内联构造 `route_options`，无法在外面插参数。复刻的字段逐一照抄原方法，README 登记时写明「复刻了原方法第 114-134 行，上游改该方法须同步」。
2. 新增 `opening_ledger.js`，`hooks.py` 加 `doctype_js = {"Journal Entry": "public/js/opening_ledger.js", "Payment Entry": "public/js/opening_ledger.js"}`（HT-005）：
   - `Journal Entry`：erpnext 按钮为 `__("Ledger")`、分组 `__("View")`（`journal_entry.js:79-96`）。
   - `Payment Entry`：erpnext 按钮为 `__("Ledger")`、第三参 `"fa fa-table"` 被当作分组（`payment_entry.js:423-441`）——`remove_custom_button(__("Ledger"), "fa fa-table")` 后同样加回。
   - 两者 `route_options` 照抄各自原文、多一项 `show_opening_entries: 1`；仅当 `frm.doc.is_opening === "Yes" && frm.doc.docstatus > 0` 时替换。
3. README 登记三行（库存类原型覆盖、日记账凭证按钮替换、收付款凭证按钮替换）。
4. 测试站造：一张 `Opening Stock` 库存调账、一张 `is_opening=Yes` 的日记账凭证（借贷各一行）、一张普通库存凭证、一张普通日记账凭证；`bench build --app frappe_china` 后按 SL-008 ①～④ 验。④ 的注入验法写进 `Spike/P1S6R4-opening-ledger.js`。

### 验证方式
SL-008 ①～④。HT-004／005／015 的验证结论写回执。

---

## 任务 TS-013：不刷新六例（对应 SL-009）

### 目标
需求 §4.8.3：六例在当前环境下各复现一次，给结论与处置。

### 具体改动
| 例 | 做法 |
|---|---|
| 1、5 | 并入 TS-011，引其截图 |
| 2 | 只记结论（V-07；图谱 LG-073），不复现 |
| 3 | 测试站建两个物料、一张 BOM（≥1 行原料、≥1 道工序以触发 `update_cost`），保存后**不刷新**看工具栏是否出「提交」；复现时用 CDP 读 `cur_frm.doc.__unsaved` 与保存前后的 `set_value` 调用（在页面里临时包 `frappe.model.set_value` 计数） |
| 4 | 测试站建工单与生产任务单，点「开始」（选员工）→「暂停」→「继续」→「完成」，每步后读库里 `tabJob Card Time Log` 行（`name` 是否 `new-` 开头、`idx` 是否重复）与界面计时器状态 |
| 6 | **演示站只读**复现：登录后会话中首次进「销售税费模板」列表（`/desk/sales-taxes-and-charges-template`），看是否发取数请求（CDP 记 `frappe.desk.reportview.get` 请求）、是否空白；不写演示站 |

- 每例先确认实时通道通（`frappe_china.realtime_check.run` 报通过）再复现——S1 的观察是在实时通道不通时做的（图谱 LG-071）。
- 复现了的：按该例路径定修法，**修法若需改 erpnext 或 frappe 源码，暂停报用户**；能在 `frappe_china` 内修的修、登记 README；例 4 的写入侧在 erpnext Python（`job_card.py:680-685`），`frappe_china` 内只能用 `doc_events` 之类兜底，兜底方案先报用户再做。
- 结论表随 D 回执交付；`PH-P1002` 的登记册更新留 Stage 收口。

### 验证方式
SL-009 ①～⑤。
