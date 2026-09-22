# V-07 探针：四例「不刷新即不显示」是否同源

> 待验表：`docs/01-需求摸底/S02-演示蓝图/R01-图谱讨论/P1-S2-R1-A待验表.md` V-07
> 源码基线：本地 `frappe-bench/apps/frappe`、`frappe-bench/apps/erpnext`（v16）
> 站点：`erx.localhost`（容器在跑，**0 Item / 0 BOM / 0 Work Order / 0 Job Card**，85 Warehouse）
> 结论：**no-go——四例分属三条互不相干的路径，没有"修一处即四例同修"的公共点。**

---

## 一、逐例的路径归属

| 例 | 现象 | 实际路径 | 与其它例的关系 |
|---|---|---|---|
| 1 | 仓库列表空白 | **路由/视图选择**（`router.js` + `generate_route`），与缓存、重载无关 | **与第五例（树形 DocType）完全同源**，不与 2/3/4 同源 |
| 2 | 工作区侧栏卡片缺失 | **v16 架构变更 + 死代码**：侧栏改由独立 DocType `Workspace Sidebar` 驱动，`add_card()` 全仓无调用者 | 独立，**不是"不刷新"，刷新也永远不出现** |
| 3 | BOM 保存后「提交」按钮不出现 | **表单 dirty 状态管理**（`toolbar.can_submit` 读 `__unsaved`） | 独立 |
| 4 | `Job Card` `time_logs` 残留空行 | **服务端子表写入**（`add_start_time_log` 的 `row.db_update()`） | 独立，**根本不是前端问题** |

分组：**{1, 5} / {2} / {3} / {4}**——四例落在三条路径上（第 1 例并入已处理的第五例）。

---

## 二、逐例取证

### 例 1：仓库列表空白 —— 与第五例同源，且 v16 已有 `default_view` 兜底

**（1）结构与第五例一致（`Account`）：**

`frappe-bench/apps/erpnext/erpnext/stock/doctype/warehouse/warehouse.json:287` → `"is_tree": 1`，`:293` → `"nsm_parent_field": "parent_warehouse"`。

目录下**只有 `warehouse_tree.js`（765 字节），无 `warehouse_list.js`**（`ls` 实测）。与 `Account`（只有 `account_tree.js` 8149 字节）完全相同的结构。

**（2）侧栏链接为何生成列表路由 —— 精确到行：**

`frappe-bench/apps/frappe/frappe/public/js/frappe/utils/utils.js:1531` `generate_route(item)`，DocType 分支按 `item.doc_view` 分派：

- `:1552-1555` `case "List"` → `${doctype_slug}/view/list`
- `:1556-1558` `case "Tree"` → `${doctype_slug}/view/tree`
- **`:1576-1577` `default:` → `route = doctype_slug`**（裸 DocType 路由，不带 `/view/*`）

侧栏项的数据源 `Workspace Sidebar Item`（`frappe/desk/doctype/workspace_sidebar_item/workspace_sidebar_item.json`）字段清单实测为：
`type, label, link_type, link_to, icon, child, indent, collapsible, details_section, column_break_krzu, display_section, collapsible_column, keep_closed, column_break_jexf, url, show_arrow, section_break_whjq, filters, route_options, navigate_to_tab, filter_area`
—— **没有 `doc_view` 字段**。故侧栏 DocType 项必然走 `default:` 分支，生成裸路由。这是 R6 判定「侧栏链接生成显式列表路由」的确切代码位置。

**（3）⚠ 但 v16 有一层 R6 未提到的兜底，判据与 R6 的描述有偏差：**

`frappe-bench/apps/frappe/frappe/public/js/frappe/router.js:200` `set_doctype_route(route)`，裸 DocType 路由（`route[1]` 为空）落到 `:223-231`：

```js
} else if (meta.default_view) {
    if (meta.default_view === "Tree") {
        route = ["Tree", doctype_route.doctype];      // :224-225
    } else {
        route = ["List", doctype_route.doctype,
                 this.list_views_route[meta.default_view.toLowerCase()]];
    }
} else {
    route = ["List", doctype_route.doctype, "List"];   // :232
}
```

实测 `default_view`（站点 DB `tabDocType`，非仅 json）：

| DocType | `default_view` | `is_tree` |
|---|---|---|
| `Warehouse` | **Tree** | 1 |
| `Account` | **Tree** | 1 |
| `Cost Center` | **Tree** | 1 |
| `Item Group` / `Customer Group` / `Supplier Group` / `Location` | Tree | 1 |
| `Company` / `Department` / `Employee` / `Task` / `Territory` / `Sales Person` / `Quality Procedure` | `None` | 1 |

`warehouse.json:5` / `account.json:6` / `cost_center.json:6` 均写有 `"default_view": "Tree"`，`force_re_route_to_default_view` 实测为 `0`。

**即：裸路由 `/desk/warehouse` 按 `router.js:224-225` 应被改写成 `["Tree","Warehouse"]`，而不是落到列表视图。** 另一条通道 `list_view.js:7-22` `load_last_view()` 在 `route.length === 2` 时按 `user_settings.last_view` 重定向，`frappe.views.is_valid(last_view)` 为假时退为 `list`——**这条通道不看 `default_view`，是"曾经进过列表视图"后空白会复现的入口**（与 R3 观察到的"敲过树视图地址后就正常了"方向一致，`__UserSettings` 在服务端，故 `Ctrl+Shift+R` 不影响）。

**故例 1 的成因收窄为：路由/视图选择 + `last_view` 用户设置，不是缓存也不是文档重载。** 列表查询本身是好的——实测 `frappe.desk.reportview.get` 对 `Warehouse` 返回 **20 行**（`page_length=20`，站内共 85 条，17 条 `is_group=1`、0 条 `disabled`），首三条 `Goods In Transit - _TCSV` / `Finished Goods - _TCSV` / `Work In Progress - _TCSV`。**数据层无问题，空白纯是视图选错。**

> 附带更正一条既有判据：R6 曾以「`*_list.js` 缺失 ⇒ 列表视图空白」作因果。该前提不足以支撑——erpnext 全仓 641 个 doctype json 只有 **79 个 `*_list.js`**，`Brand` 等既无 `_list.js` 也无 `_tree.js`，列表照常渲染。`*_list.js` 只是列表视图的**可选定制钩子**，不是列表视图的实现。真正的成因是上面的路由分派。

---

### 例 2：工作区侧栏卡片缺失 —— v16 架构变更 + 一处死代码，与"刷新"无关

**（1）v16 侧栏不再由 Workspace 页面内容驱动，而是独立 DocType：**

`frappe-bench/apps/frappe/frappe/boot.py:170-173`：

```python
def load_desktop_data(bootinfo):
    allowed_pages = [d.name for d in bootinfo.workspaces.get("pages")]
    bootinfo.workspace_sidebar_item = get_sidebar_items(allowed_pages)
```

`boot.py:442-515` `get_sidebar_items()` 读的是 **`Workspace Sidebar` / `Workspace Sidebar Item`**，与 `Workspace` 页面的 `content` JSON 是两套数据。前端 `frappe/public/js/frappe/ui/sidebar/sidebar.js:14` 与 `:31-33` 只吃 `frappe.boot.workspace_sidebar_item`，从不读 Workspace 的 `content`。

erpnext 侧的 fixture 在 `frappe-bench/apps/erpnext/erpnext/workspace_sidebar/*.json`（`buying.json`、`stock.json`、`selling.json` 等 21 个）。

**（2）「物料与价格」这张卡在侧栏 fixture 里本就不存在：**

- `erpnext/buying/workspace/buying/buying.json` 的 `content` 含 8 张卡：`Buying` / **`Items & Pricing`** / `Settings` / `Supplier` / `Supplier Scorecard` / `Key Reports` / `Other Reports` / `Regional`。
- `erpnext/workspace_sidebar/buying.json` 的 32 个 item **无任何 `Items & Pricing`**，只有一个 `Section Break` 名 `Setup`，其下平铺 `Item` / `Price List` 等 Link。

站点实测（`frappe.boot.get_bootinfo()` 取 `workspace_sidebar_item["buying"]`，32 项）：
`数据面板 / 物料需求 / 询价 / 供应商报价 / 采购订单 / 采购发票 / [Section Break] 设置 / 供应商 / 供应商组 / Item / 价格表 / 地址 / 联系人 / 供应商评分卡 ... / [Section Break] 报表 / ... / 设置`
—— **无「物料与价格」，也无任何"卡片"概念。**

**（3）侧栏卡片机制在 v16 是死代码：**

`sidebar.js:305-309` `add_card(card)` 只往 `this.cards` 推；`:311-316` `add_sidebar_cards()` 遍历 `this.cards` 造 `frappe.ui.Card`。而 `this.cards` 在 `:22` 初始化为 `[]`——**`frappe-bench/apps/` 全仓（frappe + erpnext，js/py/html）grep `.add_card(` 除 kanban 的同名无关函数外零命中**，即 `add_card()` 没有任何调用者，`this.cards` 永远为空，`add_sidebar_cards()` 永远渲染 0 张卡。

**故例 2 不是"不刷新即不显示"——它刷新也不会出现，主页那 8 张卡是 Workspace 页面内容，侧栏从来就不显示卡片。** R3 当时查的「47 条 Workspace Link 结构对称、页面 content JSON 含该 card」查的是 Workspace 页面这套数据，而侧栏读的是另一套，所以"数据层三查正常"与"侧栏不显示"并不矛盾。这也解释了为何清服务端缓存与无痕窗口都无效。

---

### 例 3：BOM 保存后「提交」按钮不出现 —— 表单 dirty 状态

**判定依赖的开关：** `frappe-bench/apps/frappe/frappe/public/js/frappe/form/toolbar.js:680-689`

```js
can_submit() {
    return (
        frappe.model.is_submittable(this.frm.doc.doctype) &&
        this.get_docstatus() === 0 &&
        !this.frm.doc.__islocal &&
        !this.frm.doc.__unsaved &&     // ← 这一项
        this.frm.perm[0].submit &&
        !this.has_workflow()
    );
}
```

`:764-770` `get_action_status()` 按 `can_submit()` → `"Submit"` 分派；R3 已在服务端排除 `is_submittable` / `validate` / submit 权限 / Workflow 四项，故剩下**只能是 `__unsaved` 未清**。

**`__unsaved` 被谁置上 —— 精确链路：**

1. `form.js:283-289` 对主 doc 注册 `frappe.model.on(doctype, "*")`，回调里 `:290-292`：`if (!skip_dirty_trigger) { me.dirty(); }`；`:1495-1496` `dirty()` 即 `this.doc.__unsaved = 1`。子表同理见 `form.js:316-330`。
2. `model/model.js:506-546` `set_value()` 在 `doc[key] !== value` 时改值并 `tasks.push(() => frappe.model.trigger(key, value, doc, skip_dirty_trigger))`——**`skip_dirty_trigger` 默认 `false`**，故任何 `set_value` 都会 `dirty()`。
3. BOM 的成本重算全部走 `set_value`：`erpnext/manufacturing/doctype/bom/bom.js:853-854`（`raw_material_cost` / `base_raw_material_cost`）、`:863-864`（`total_cost` / `base_total_cost`）、`:810-813`（`BOM Operation` 的 `operating_cost` / `base_operating_cost`）、`:834-845`（`BOM Item` 的 `base_rate` / `amount` / `base_amount` / `qty_consumed_per_unit`）。
4. `bom.js:866-868`：`cur_frm.cscript.validate = function (doc) { erpnext.bom.update_cost(doc); }`，`:796-800` `update_cost()` = `calculate_op_cost` + `calculate_rm_cost` + `calculate_total`。

**时序：** `form.js:865-878` 的 `run_serially([ trigger("validate"), trigger("before_save"), () => frappe.ui.form.save(...) ])`——`validate` 里的 `update_cost()` 在**保存请求发出前**跑，这些 `set_value` 造成的 `dirty()` 本应被随后的保存清掉；保存回来后 `form.js:843` `me.refresh()` 重画工具栏。所以本例的失效点是 `validate` 阶段的 `set_value` 与 `after_save` 的 `refresh()` 之间的 `__unsaved` 清除时序，**属表单 dirty 状态管理，与例 1 的路由、例 2 的侧栏数据源、例 4 的服务端子表写入毫无公共代码**。

**⚠ 未能实际复现**（站点 0 Item / 0 BOM，无法建 BOM），判定基于上述源码链路。具体是哪一次 `set_value` 在保存响应之后又跑了一遍，需有数据后实测才能钉死。

---

### 例 4：`Job Card` `time_logs` 残留空行 —— 服务端写入，不是前端问题

**（1）空行由服务端 `db_update()` 直接入库：**

`erpnext/manufacturing/doctype/job_card/job_card.py:680-685`：

```python
def add_start_time_log(self, args):
    if args.from_time and args.to_time:
        args.time_in_mins = time_diff_in_minutes(args.to_time, args.from_time)

    row = self.append("time_logs", args)
    row.db_update()
```

调用链：`job_card.js:557-568` `make_time_log()` → `frappe.call("...job_card.make_time_log")` → `job_card.py:1823-1831` `make_time_log(kwargs)` → `doc.add_time_log(kwargs)`（`:643-678`）→ `add_start_time_log`。

**（2）`append` + `db_update()` 为何让临时 ID 入库：**

- `frappe/model/base_document.py:440-467` `_init_child()`：`:463-465` —— 新行无 `name` 时置 `__islocal = 1` 并给 `__temporary_name = frappe.generate_hash(length=10)`。
- `base_document.py:804-807` `db_update()`：`if self.get("__islocal") or not self.name: self.db_insert(); return` —— **对 `__islocal` 的行直接 `db_insert()`**，`:736-738` `if not self.name: set_new_name(self)`。

即 `add_start_time_log` 用 `db_update()`（绕过 `self.save()` 的完整校验与 idx 重排）把行单独插库。前端侧 `frappe/public/js/frappe/model/create_new.js:78-80` `get_new_name()` 产的正是 `new-{doctype}-{hash}` 形式的临时名，`model.js:631` 判前缀——**R3 在 DB 里看到的 `new-job-card-time-log-yhzvnltfwr` 与 idx 重复（1,1,2,2），正是"前端未保存行 + 服务端 `db_update` 旁路插入"两条写入路径并存的产物**，`self.save()` 那条路会重排 idx，`db_update()` 这条不会。

**（3）状态错乱的读取侧（与空行是两件事）：**

`erpnext/manufacturing/doctype/job_card/job_card.js:615-622`：

```js
const last_log_complete = time_logs?.length && time_logs[time_logs.length - 1].to_time;
const is_on_hold = status === "On Hold";
const is_actively_running = !!(
    time_logs?.length && !last_log_complete && !is_on_hold && !doc.is_paused
);
```

只看最后一行有没有 `to_time`，**不检查该行是否为有效行**，故一个空行即让 `is_actively_running = true`（R3 已定位到此，本次复核该行号与逻辑无误）。`:609-613` 的 `should_show_start` 三条件同样以 `!time_logs?.length` 为"还没开始"的判据，空行同样骗过它。

**⚠ 未能实际复现**（站点 0 Job Card / 0 Work Order，无法造单），判定基于源码。

**这一例的写入侧在 Python，与例 1/2/3 全在前端 —— 连"同一层"都不是。**

---

## 三、为何不能"修一处四例同修"

四例涉及的代码互不相交：

| 例 | 要动的文件 |
|---|---|
| 1（+5） | `frappe/public/js/frappe/utils/utils.js`（`generate_route` 的 `default:`）或 `router.js` / `list_view.js:7-22`，或给 `Workspace Sidebar Item` 加 `doc_view` |
| 2 | `frappe/public/js/frappe/ui/sidebar/sidebar.js`（补 `add_card` 的调用者）或 erpnext 的 `workspace_sidebar/*.json` fixture |
| 3 | `frappe/public/js/frappe/form/toolbar.js` + `form.js` 的 dirty 时序，或 `erpnext/.../bom.js` 的 `set_value` 用法 |
| 4 | `erpnext/.../job_card.py:680-685`（写入侧）+ `job_card.js:615-622`（读取侧） |

唯一的"公共点"只是"用户感知为不刷新就看不到"，**不是共用的缓存或文档重载路径**。例 1 是路由、例 2 是 v16 架构变更下的死代码（刷新也无效）、例 3 是表单 dirty、例 4 的写入侧在服务端。

**判定：`no-go`。**

---

## 四、本次探针的验证手段与边界

| 项 | 情况 |
|---|---|
| 例 1 | 源码取证 + **站点实测**（85 Warehouse、`reportview.get` 返 20 行、DB `default_view=Tree`），未在浏览器点过侧栏 |
| 例 2 | 源码取证 + **站点实测**（`get_bootinfo()` 取出 buying 侧栏 32 项，确认无该卡）+ 全仓 grep 确认 `add_card` 零调用者 |
| 例 3 | **纯源码**——站点 0 BOM，未能复现 |
| 例 4 | **纯源码**——站点 0 Job Card，未能复现 |

未改 `frappe-bench/apps/` 下任何文件。临时脚本落在容器 `/tmp/`（`chk2.py`/`chk3.py`/`wh.py`/`lv.py`/`meta2.py`/`meta3.py`），未入库、未进项目树。
