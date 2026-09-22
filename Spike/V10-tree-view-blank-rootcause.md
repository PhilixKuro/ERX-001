# V-10 探针：树形 DocType 侧栏点入空白页的真正根因

- 日期：2026-09-23
- 站点：`erx.localhost`（web 8000），数据已从备份恢复（1 Company / 95 Account / 6 Warehouse）
- 源码：Frappe v16 `D:\ERX-001\frappe-bench\apps\frappe`，ERPNext v16 `D:\ERX-001\frappe-bench\apps\erpnext`
- **未在浏览器实际点击**。本 Round 无浏览器工具，全部判定来自源码（文件+行号）与站点实跑输出（bench console）。凡属推断处均已标注。

## 0. 结论速览



| 命题 | 判定 |
| --- | --- |
| R6「`*_list.js` 缺失致必然空白」 | **已推翻**（V-07 已否，本轮再确认） |
| R6「侧栏生成显式列表路由」 | **已推翻**：侧栏生成的是**裸路由** `/desk/warehouse` |
| V-07「`load_last_view()` 是入口」 | **已推翻**：该函数在本场景**根本不会被调用**，且全站 `__UserSettings` **0 行** |
| 最终判定 (a) 所有用户必然 / (b) 仅 `last_view=List` / (c) 另有原因 | **(c) 另有原因** |

一句话：**当前站点状态下，从侧栏点树形 DocType 的路由解析链路是完整健康的，五个前置条件全部满足，本应正确落到树视图。** 因此 R6 与 V-07 指认的「路由解析产生列表路由」这一类根因均不成立。空白若仍然出现，locus 不在路由解析，而在客户端运行期（见 §6）。

---

## 1. 侧栏链接实际生成的路由：裸路由，不是显式列表路由

### 1.1 关键更正：侧栏走的不是 `Workspace Link`，而是 `Workspace Sidebar Item`

`Workspace Sidebar Item` 的字段表（`frappe/desk/doctype/workspace_sidebar_item/workspace_sidebar_item.json`，实读字段列表）**没有 `doc_view` 字段**。全仓 `doc_view` 只出现在 `Workspace Shortcut` 上：

```
$ grep -rln "doc_view" --include=*.json frappe/
./core/workspace/build/build.json
./desk/doctype/workspace_shortcut/workspace_shortcut.json
./integrations/workspace/integrations/integrations.json
```

侧栏项的渲染入口是 `frappe/public/js/frappe/ui/sidebar/sidebar_item.js`（`generate_route` 调用点在 `:33`、`:48`、`:72`）。

### 1.2 `doc_view` 只在有 filters/route_options 时才被设上

`sidebar_item.js:53-72`（`get_path()` 的 `else` 分支，即 `link_type == "DocType"` 的常规路径）：

```js
let args = {
    type: this.item.link_type,
    name: this.item.link_to,
    tab: this.item.tab,
};
if (this.item.filters) {
    let filters_json = JSON.parse(
        frappe.utils.get_filter_as_json(JSON.parse(this.item.filters))
    );
    filters_json = this.transform_filters(filters_json);
    if (this.item.link_type == "DocType") {
        args.doc_view = "List";          // ← 只有这里
        args.route_options = filters_json;
    }
} else if (this.item.route_options && this.item.link_type == "DocType") {
    args.doc_view = "List";              // ← 和这里
    args.route_options = JSON.parse(this.item.route_options);
}
path = frappe.utils.generate_route(args);
```

**`args.doc_view` 仅在 `item.filters` 或 `item.route_options` 非空时被设为 `"List"`。** 两者都空时 `doc_view` 为 `undefined`。

### 1.3 `generate_route()` 的 `default:` 分支产出裸 slug

`frappe/public/js/frappe/utils/utils.js:1546-1579`：`switch (item.doc_view)` 中 `case "List"` 产出 `${doctype_slug}/view/list`（`:1551`），而 `default:` 产出 **`route = doctype_slug`**（`:1577-1578`）。末尾 `:1620` 返回 `` `/desk/${route}` ``。

`doc_view === undefined` 命中 `default:` → 路径为 **`/desk/warehouse`**（裸路由）。

### 1.4 站点实测：全部树形 DocType 的侧栏项 filters/route_options 均为空

```
$ bench --site erx.localhost console
tree_dts = ('Warehouse','Location','Item Group','Account','Cost Center','Supplier Group','Customer Group')
rows = frappe.db.sql("select parent, label, link_to, ifnull(filters,'NULL') f, ifnull(route_options,'NULL') ro
                      from `tabWorkspace Sidebar Item`
                      where link_type='DocType' and link_to in %(d)s", {"d": tree_dts}, as_dict=True)

TREE_SIDEBAR_ITEMS 12
ANY_WITH_FILTERS_OR_RO []
ALL_BARE True
BY_DT ['Account', 'Cost Center', 'Customer Group', 'Item Group', 'Location', 'Supplier Group', 'Warehouse']
```

逐条明细（`Warehouse` / `Account` / `Cost Center` / 对照组）：

```
{'parent': 'Accounts Setup', 'label': 'Chart of Accounts', 'link_to': 'Account',     'f': 'NULL', 'ro': 'NULL'}
{'parent': 'Invoicing',      'label': 'Chart of Accounts', 'link_to': 'Account',     'f': 'NULL', 'ro': 'NULL'}
{'parent': 'Budget',         'label': 'Cost Center',       'link_to': 'Cost Center', 'f': 'NULL', 'ro': 'NULL'}
{'parent': 'Stock',          'label': 'Warehouse',         'link_to': 'Warehouse',   'f': 'NULL', 'ro': 'NULL'}
{'parent': 'Manufacturing',  'label': 'Warehouse',         'link_to': 'Warehouse',   'f': 'NULL', 'ro': 'NULL'}
{'parent': 'Stock',          'label': 'Brand',             'link_to': 'Brand',       'f': 'NULL', 'ro': 'NULL'}
```

**结论（钉死）**：侧栏对 `Warehouse` / `Account` / `Cost Center` 生成的是 **裸路由 `/desk/warehouse` 等**，不是 `/desk/warehouse/view/list`。

**R6 的第二个前提（"侧栏链接生成了显式的列表路由"）由此推翻。** 既然是裸路由，它恰恰落在 `router.js:223` 兜底的射程之内。

### 1.5 点击不触发整页加载，而是走 SPA push-state

`router.js:26-68` 在 `body` 上全局捕获 `a` 点击：`is_app_route(pathname)` 为真（`:104-112`，判 `path[0] === "desk"`）时执行 `override(target_element.pathname)`，即 `e.preventDefault()` + `frappe.set_route(pathname)`。所以侧栏点击等价于 `frappe.set_route("/desk/warehouse")`，随后进入 `parse()` → `convert_to_standard_route()`。

## 2. `router.js:223-231` 兜底的生效条件

`set_doctype_route()`（`router.js:200-240`）是一条 if/else-if 链，四个分支互斥，判断顺序即优先级：

```js
set_doctype_route(route) {
    let doctype_route = this.routes[route[0]];
    return frappe.model.with_doctype(doctype_route.doctype).then(() => {
        let meta = frappe.get_meta(doctype_route.doctype);
        this.meta = meta;
        if (route[1] && route[1] === "view" && route[2]) {          // ① 显式视图路由
            route = this.get_standard_route_for_list(
                route, doctype_route,
                meta.force_re_route_to_default_view && meta.default_view
                    ? meta.default_view : null                      // ← 关键：不强制则传 null
            );
        } else if (route[1] && route[1] !== "view") {               // ② Form 路由
            ...
            route = ["Form", doctype_route.doctype, docname];
        } else if (frappe.model.is_single(doctype_route.doctype)) { // ③ Single
            route = ["Form", doctype_route.doctype, doctype_route.doctype];
        } else if (meta.default_view) {                             // ④ 裸路由兜底
            if (meta.default_view === "Tree") {
                route = ["Tree", doctype_route.doctype];            // ← 改写为树视图
            } else {
                route = ["List", doctype_route.doctype,
                         this.list_views_route[meta.default_view.toLowerCase()]];
            }
        } else {
            route = ["List", doctype_route.doctype, "List"];
        }
        ...
    });
}
```

### 2.1 生效条件（全部须满足）

1. `this.routes[route[0]]` 存在 —— 即 slug 已注册。`setup()`（`:116-118`）按 `frappe.boot.user.can_read` 建表：`this.routes[this.slug(doctype)] = { doctype }`。
2. **`route[1]` 为空**（裸路由）—— 否则被分支 ① 或 ② 抢先。
3. 该 DocType **不是 Single** —— 否则被 ③ 抢先。
4. `meta.default_view` 为真值。
5. `meta.default_view === "Tree"`。

### 2.2 什么条件下被绕过

- **显式 `/desk/warehouse/view/list`**：命中分支 ①。此时第三参传的是 `force_re_route_to_default_view && default_view ? default_view : null`；实测 `force_re_route_to_default_view = 0`，故传 **`null`**。进入 `get_standard_route_for_list`（`:242-286`）后 `_route = default_view || route[2] || "" = "list"`，走 else 分支产出 `["List", "Warehouse", "List"]` —— **`default_view=Tree` 被完全忽略**，落列表视图。
- 这正是「裸路由与显式列表路由命运不同」的机制所在：**兜底只保护裸路由**。

### 2.3 站点实测：五个条件全部满足

`can_read` 注册（实跑 `frappe.boot.get_bootinfo()`）：

```
CAN_READ_COUNT 457
TREE_DTS_IN_CAN_READ [('Warehouse', True), ('Account', True), ('Cost Center', True), ('Brand', True), ('Item', True)]
```

DocType 元数据（`tabDocType` 实查）：

```
[{'name': 'Account',     'is_tree': 1, 'default_view': 'Tree', 'force_re_route_to_default_view': 0},
 {'name': 'Cost Center', 'is_tree': 1, 'default_view': 'Tree', 'force_re_route_to_default_view': 0},
 {'name': 'Warehouse',   'is_tree': 1, 'default_view': 'Tree', 'force_re_route_to_default_view': 0},
 {'name': 'Brand',       'is_tree': 0, 'default_view': None,   'force_re_route_to_default_view': 0},
 {'name': 'Item',        'is_tree': 0, 'default_view': None,   'force_re_route_to_default_view': 0}]
```

**且 `default_view` 确实随元数据下发到客户端**（这是兜底能否工作的真正命门，此前两次判断都没验过）。直接调 `get_meta_bundle`（`frappe/desk/form/load.py`，即 `with_doctype` 走的 `getdoctype` 的数据源）：

```
$ bench --site erx.localhost console
from frappe.desk.form.load import get_meta_bundle
[(dt, docs[0].name, default_view, force_re_route, is_tree) ...]
RESULT1 [('Warehouse',   'Warehouse',   "'Tree'", '0', '1'),
         ('Account',     'Account',     "'Tree'", '0', '1'),
         ('Cost Center', 'Cost Center', "'Tree'", '0', '1')]
```

`default_view: "Tree"` 亦是 ERPNext 随包出厂值，不依赖任何 patch：

```
$ grep -n "default_view" stock/doctype/warehouse/warehouse.json
5: "default_view": "Tree",
（account.json:6、cost_center.json:6 同）
```

### 2.4 构建产物与源码一致

实际跑的是打包产物而非源码，故核对 `sites/assets/assets.json` 指向的 `desk.bundle.LHZJYI3U.js`（mtime 09-18 23:04，晚于 `router.js` 源码 22:36），该段逻辑逐字一致：

```js
} else if (meta.default_view) {
  if (meta.default_view === "Tree") {
    route = ["Tree", doctype_route.doctype];
```

**结论（钉死）**：当前站点状态下，裸路由 `/desk/warehouse` **会**被 `router.js:223-231` 改写为 `["Tree", "Warehouse"]`。兜底是生效的。

## 3. `load_last_view()` 与兜底的先后顺序

### 3.1 关键结论：本场景下 `load_last_view()` 根本不会被调用

`load_last_view()` 不是路由解析阶段的钩子，而是 **`ListFactory` 内部**的逻辑。唯一调用点在 `frappe/public/js/frappe/list/list_factory.js:23`：

```js
frappe.views.ListFactory = class ListFactory extends frappe.views.Factory {
    make(route) {
        const doctype = route[1];
        let view_name = frappe.utils.to_title_case(route[2] || "List");
        ...
        let view_class = frappe.views[view_name + "View"];
        if (!view_class) view_class = frappe.views.ListView;
        if (view_class && view_class.load_last_view && view_class.load_last_view()) {
            return;
        }
```

### 3.2 执行顺序（源码链条）

1. `router.route()`（`router.js:129-152`）：`this.current_route = await this.parse();` —— **路由解析先跑**，`set_doctype_route()` 的兜底在这一步完成，裸路由已变成 `["Tree", "Warehouse"]`。
2. 然后 `this.render()` → `render_page()`（`:305-325`）：
   ```js
   const factory = frappe.utils.to_title_case(route[0]);   // "Tree"
   if (route[1] && frappe.views[factory + "Factory"]) {
       frappe.view_factory[factory].show();                // TreeFactory
   }
   ```
3. `route[0]` 已是 `"Tree"` → 派发 **`TreeFactory`**（`views/treeview.js:8`），**不是 `ListFactory`**。`load_last_view()` 从不进入调用栈。

### 3.3 即便进入，它也只在 `route.length === 2` 时动作

`list_view.js:7-22`：

```js
static load_last_view() {
    const route = frappe.get_route();
    const doctype = route[1];
    if (route.length === 2) {                    // ← 仅裸的 ["List", dt]
        const user_settings = frappe.get_user_settings(doctype);
        const last_view = user_settings.last_view;
        frappe.set_route("list", frappe.router.doctype_layout || doctype,
            frappe.views.is_valid(last_view) ? last_view.toLowerCase() : "list");
        return true;
    }
    return false;
}
```

注意 `frappe.views.is_valid`（`list/base_list.js:1439-1451`）的 `view_modes` **包含 `"Tree"`**，所以 `last_view="Tree"` 是合法值、会被采纳；但前提是根本进不到这里。

**顺序小结**：兜底（解析期）在前，`load_last_view()`（渲染期、且仅 ListFactory 内）在后。**后者原则上能覆盖前者的结果**——但只有当路由已经是 `["List", dt]` 形态时才有机会，而兜底恰好把树形 DocType 的裸路由改成了 `Tree`，使其永不落入 `ListFactory`。**V-07 的猜测据此推翻。**

## 4. `__UserSettings` 的 `last_view` 读写时机与实测值

### 4.1 站点实测：全站 `__UserSettings` 0 行

这是本轮最有判定力的一条输出。**我没有做任何写操作**，只读：

```
$ bench --site erx.localhost console
print("TOTAL_ROWS", frappe.db.sql("select count(*) from `__UserSettings`")[0][0])
TOTAL_ROWS 0

print("DISTINCT_USERS", frappe.db.sql("select distinct user from `__UserSettings`"))
DISTINCT_USERS ()

LAST_VIEW_ANY: []
```

针对三个树形 DocType 单独查，同样 0 行：

```
select user, doctype, data from `__UserSettings`
where doctype in ('Warehouse','Account','Cost Center')
COUNT 0
```

### 4.2 这一条直接终结了 V-07 的假设

V-07 的推测是「`last_view=List` 导致重定向到列表视图」。但：

- 表里 **一行都没有**，`last_view` 对任何用户、任何 doctype 都不存在；
- 即便存在，§3 已证明 `load_last_view()` 在树形 DocType 的侧栏路径上**不进入调用栈**。

因此 **`last_view` 既无状态、也无机会** 参与本现象。判定 (b) 被排除。

### 4.3 读写时机（源码）

- **读**：`frappe.model.with_doctype` → `getdoctype` 响应里带 `user_settings`（`load.py:75` `frappe.response["user_settings"] = get_user_settings(...)`），客户端在 `model/model.js:238-242` 存入 `frappe.model.user_settings[doctype]`。
- **写**：服务端 `frappe/model/utils/user_settings.py`。写入由列表视图侧的交互触发（切换视图、改筛选/排序/列宽等）。
- **全新用户（从未点过这些页面）**：`__UserSettings` 无该行，`user_settings.last_view` 为 `undefined`。在 `load_last_view()` 中 `is_valid(undefined)` 为假 → 回退 `"list"`。但如上，树形 DocType 走不到这一步。
- **重要机制**：`__UserSettings` 在**服务端**，所以清浏览器缓存 / `Ctrl+Shift+R` 都不影响它 —— R3 观察到的「强刷无效」与该表一致，但**不等于**该表是成因（本轮实测它是空的）。强刷无效另有更贴合的解释，见 §6.1。

## 5. 最终判定

**判定为 (c)：另有原因。** (a) 与 (b) 均被证伪。

### 5.1 五个前置条件在当前站点全部满足，链路健康

把整条链路逐环实测一遍，没有一环是断的：

| 环节 | 需要成立 | 实测 | 证据 |
| --- | --- | --- | --- |
| 侧栏产出裸路由 | `filters`/`route_options` 皆空 | ✅ 12 项全空 | §1.4 |
| slug 已注册 | doctype ∈ `can_read` | ✅ 457 项含三者 | §2.3 |
| 非 Single | — | ✅ `is_tree=1` 普通表 | §2.3 |
| `default_view` 抵达客户端 meta | `get_meta_bundle` 带该字段 | ✅ `'Tree'` | §2.3 |
| `TreeFactory` 已加载 | 在 eager 包里 | ✅ 见下 | §5.2 |
| 树视图可用性检查 | `treeview_settings` 或 `is_group` 字段 | ✅ 两者都有 | §5.3 |
| 树数据可取 | `get_children` 返回非空 | ✅ | §5.4 |

**在当前（数据已恢复的）站点状态下，从侧栏点 `Warehouse` 本应正确落到树视图。** 这与 R6 的「必然空白」直接矛盾。

### 5.2 `TreeFactory` 不是懒加载，这条曾看似可疑的路径已排除

`TreeFactory` 只存在于 `list.bundle.js`（`public/js/list.bundle.js:32` `import "./frappe/views/treeview.js";`），而非 `desk.bundle.js`：

```
$ grep -rln "TreeFactory" apps/frappe/frappe/public/dist/js/ | grep -v .map
apps/frappe/frappe/public/dist/js/list.bundle.N2HVYS25.js
```

曾怀疑「解析完成时 `frappe.views.TreeFactory` 尚未定义 → `render_page()` 落到 `else` 分支 `pageview.show("Tree")` → 空白」。但 `frappe/hooks.py:25-33` 显示 `list.bundle.js` 在 `app_include_js` 里**与 desk 同批同步加载**：

```python
app_include_js = [
    "libs.bundle.js", "billing.bundle.js", "desk.bundle.js",
    "list.bundle.js", "form.bundle.js", ...
]
```

故该竞态不成立，此路径排除。

### 5.3 `TreeFactory.make()` 的可用性检查能通过

`views/treeview.js:11-26`：

```js
if (!frappe.treeview_settings[route[1]] && !frappe.meta.get_docfield(route[1], "is_group")) {
    frappe.msgprint(__("Tree view is not available for {0}", [route[1]]));
    return false;
}
```

两个条件任一满足即可，实测两者都满足：

- `treeview_settings` 注册齐全：`erpnext/stock/doctype/warehouse/warehouse_tree.js:1`、`accounts/doctype/account/account_tree.js:3`、`accounts/doctype/cost_center/cost_center_tree.js:1`。
- `is_group` 字段存在：`IS_GROUP [('Warehouse', True), ('Account', True), ('Cost Center', True)]`
- `*_tree.js` 确实随 meta 下发（机制：`desk/form/meta.py:105` `self._add_code(_get_path(self.name + "_tree.js"), "__tree_js")`，客户端 `model/model.js:255-259` 用 `new Function(meta[asset_key])()` 求值）：
  ```
  RESULT2 [('Warehouse', True, 878), ('Account', True, 8259), ('Cost Center', True, 2220)]   # (has __tree_js, 字节数)
  ```
  同时 `__list_js` 全为 `False` —— 再次印证 V-07：**缺 `_list.js` 与空白无关**。

### 5.4 树数据可正常取得

```
$ bench --site erx.localhost console
co = frappe.db.get_default("company")     # '华东弹簧'
from erpnext.stock.doctype.warehouse.warehouse import get_children as wh_children
wh_children(doctype="Warehouse", parent=None, company=co, is_root=True)
→ [{'value': '所有仓库 - HDS', 'expandable': 1}]
```

补充一条与 R3 情境相关的观察（R3 当时站点只有骨架、可能无默认 Company）：company 缺失时该接口**不抛异常，返回空列表**：

```
WH_COMPANY_NONE  -> []
WH_COMPANY_EMPTY -> []
```

空列表会渲染成「有页框但树是空的」，而非整页空白 —— 形态上区别于本现象，但在肉眼上容易被记成「空白页」。**这是 R3「偶发」印象的一个可能来源（推断，未在浏览器确认）。**

## 6. 剩余候选机制（空白仍可能来自这里）

既然路由解析链路健康，空白的 locus 只能在**客户端运行期**。以下按证据强度排序。前两条能同时解释 R3 的两个观察，但**均未在浏览器验证**，属推断。

### 6.1 页面缓存 + 首次构造失败（最能解释 R3 的两个观察）

`views/factory.js:11-29` 的 `show()`：

```js
show() {
    this.route = frappe.get_route();
    this.page_name = frappe.get_route_str();       // "Tree/Warehouse"
    if (this.before_show && this.before_show() === false) return;
    if (frappe.pages[this.page_name]) {
        frappe.container.change_to(this.page_name); // 命中缓存：直接切过去
        if (this.on_show) this.on_show();
    } else {
        if (this.route[1]) this.make(this.route);   // 未命中：构造
        else frappe.show_not_found(this.route);
    }
}
```

`TreeFactory.make()` 内部是 `frappe.model.with_doctype(route[1], function () {...})` 的**异步回调**（`treeview.js:9`），页面在回调里才由 `TreeView.make_page()` 建出（`treeview.js:86-100`：`frappe.container.add_page(this.page_name)` + `frappe.container.change_to(...)`）。

由此形成的解释链：

- **首次**点侧栏：`frappe.pages["Tree/Warehouse"]` 不存在 → 走 `make()`。若回调内任一步抛异常（`with_doctype` 失败、`__tree_js` 求值抛错、`locals.DocType[me.doctype].module` 为空导致 `breadcrumbs.add` 抛错等），`add_page`/`change_to` 未完成 → **容器停在空壳，表现为空白页**。
- **敲过一次树视图地址之后再点侧栏就正常**：因为那次成功构造留下了 `frappe.pages["Tree/Warehouse"]`，此后 `show()` 命中缓存分支，只做 `change_to`，绕过了会抛错的构造路径。**这与 R3 观察完全吻合。**
- **`Ctrl+Shift+R` 无效**：`frappe.pages` 是内存态，强刷会清掉它 —— 所以强刷后本该复现，而 R3 说强刷「无效」（即仍旧正常）。这指向另一层持久缓存：`desk.js:324-329` `check_metadata_cache_status()` 仅在 `metadata_version` 变化时清 localStorage；`assets.js:58-68` 的驱逐策略是「两天过期」或「10 秒内重复刷新」。**localStorage 跨强刷存活**，所以「强刷无效」与服务端 `__UserSettings` 并非唯一解释，localStorage 资产缓存同样能解释，且不需要 `__UserSettings` 有数据（实测它是空的）。

**可疑点（未验证）**：`treeview.js:98-101` 的 `locals.DocType[me.doctype].module` 是无保护解引用。若该时刻 `locals.DocType[doctype]` 尚未同步，会抛 `TypeError`，恰好落在 `make_page()` 中段 —— `add_page` 已执行但 `change_to` 之后的 `set_title`/按钮未完成，形态上就是「有路由、无内容」。

### 6.2 `__tree_js` 求值期抛错

`model/model.js:255-259` 用 `new Function(meta["__tree_js"])()` 同步求值，**无 try/catch**。一旦抛错，`init_doctype` 中断，`frappe.treeview_settings[doctype]` 不会被设上。

`warehouse_tree.js` 在**求值时刻立即调用** `erpnext.utils.get_tree_options("company")` 与 `get_tree_default("company")`（对象字面量的 `options:`/`default:` 是 eager 求值，不是惰性）：

```js
frappe.treeview_settings["Warehouse"] = {
    ...
    filters: [{ fieldname: "company", ...,
        options: erpnext.utils.get_tree_options("company"),
        default: erpnext.utils.get_tree_default("company") }],
```

`erpnext.utils.get_tree_options` 定义在 `erpnext/public/js/utils.js:429`（`$.extend(erpnext.utils, {...})`，`:173` 起），由 `erpnext.bundle.js`（`hooks.py:25 app_include_js`）加载。

- 函数体本身对空数据是安全的：`$.map(locals[":Company"], ...)` 在 `undefined` 上返回 `[]`，不抛错（已读源码 `:429-445`）。
- 但 **`erpnext.utils` 这个命名空间必须在求值时已存在**。若 `__tree_js` 的求值早于 `erpnext.bundle.js` 执行（例如 meta 被提前拉取），`erpnext.utils` 为 `undefined` → `TypeError` → §6.1 的失败链被触发。
- 这是**跨 app 的加载顺序依赖**，与「站点数据多少」无关，但可能与页面首载时序有关 —— 这类时序敏感恰好会呈现为 R3 所说的「偶发」。

**这是我认为最值得下一步在浏览器里验证的一条。** 验证方法：首次点侧栏时开 DevTools Console，看是否有 `TypeError`，以及 `frappe.treeview_settings["Warehouse"]` 与 `frappe.pages["Tree/Warehouse"]` 是否存在。

### 6.3 已排除的候选（不必再查）

| 候选 | 排除依据 |
| --- | --- |
| 缺 `*_list.js` | `__list_js` 为空但 `Brand` 列表正常；且树形路由不进 ListFactory（§5.3） |
| 侧栏生成显式列表路由 | 12 项实测全为裸路由（§1.4） |
| `default_view` 未下发 | `get_meta_bundle` 实测为 `'Tree'`（§2.3） |
| `force_re_route` 干扰 | 实测 `0`，且裸路由分支不读该字段（§2.1） |
| `load_last_view` / `last_view=List` | 不进调用栈 + 全站表 0 行（§3、§4.1） |
| `TreeFactory` 懒加载竞态 | `list.bundle.js` 在 `app_include_js` 中同步加载（§5.2） |
| 构建产物与源码不一致 | 逐字核对 `desk.bundle.LHZJYI3U.js`（§2.4） |
| `setup_complete` 导致重定向到 setup-wizard | `router.js:138` 读 `frappe.boot.setup_complete`，由 `desk.js:293` 从 `sysdefaults` 赋值；实测 `System Settings.setup_complete = 1`（`bootinfo` 顶层为 `None` 属正常，值在 `bootinfo.sysdefaults`，见 `boot.py:52`） |
| 树数据取不到 | `get_children` 返回 `[{'value': '所有仓库 - HDS', 'expandable': 1}]`（§5.4） |

## 7. 若根因是 X，可能的修改点（事实陈述，不含修法建议）

仅列文件与行号，不评价该不该改。

- **若根因是 §6.1（首次构造失败）**：`frappe/public/js/frappe/views/treeview.js:86-101`（`make_page()`，含 `locals.DocType[me.doctype].module` 无保护解引用）；`frappe/public/js/frappe/views/factory.js:11-29`（`show()` 的缓存/构造分支）。
- **若根因是 §6.2（`__tree_js` 求值抛错）**：`frappe/public/js/frappe/model/model.js:255-259`（`new Function(...)()` 无 try/catch）；`erpnext/stock/doctype/warehouse/warehouse_tree.js:6-14` 与 `accounts/doctype/cost_center/cost_center_tree.js`、`accounts/doctype/account/account_tree.js` 的 eager `erpnext.utils.*` 调用；`erpnext/public/js/utils.js:429-453`。
- **若要绕过显式列表路由不吃兜底这件事**（§2.2，本项目当前不触发，但若将来侧栏项被加上 filters 就会触发）：`frappe/public/js/frappe/router.js:207-214`（第三参的 `force_re_route_to_default_view` 条件）；或数据侧把三个 DocType 的 `force_re_route_to_default_view` 置 1（`tabDocType`）。
- **若走数据侧**：`tabWorkspace Sidebar Item` 中 12 条树形 DocType 项（§1.4 列出 parent/label），给它们加 filters 会把裸路由变成显式列表路由，**方向相反，会引入问题而非修复**。

## 8. 复核建议

### 8.1 已钉死（有直接证据）

| 结论 | 证据类型 |
| --- | --- |
| 侧栏对树形 DocType 生成裸路由 `/desk/warehouse` | 源码 `sidebar_item.js:53-72` + `utils.js:1546-1579` ＋ 站点实测 12 项 filters/route_options 全空 |
| `Workspace Sidebar Item` 无 `doc_view` 字段 | 字段表实读 + 全仓 grep |
| `router.js:223-231` 兜底对裸路由生效，改写为 `["Tree", dt]` | 源码 + 构建产物逐字核对 |
| 兜底只保护裸路由；显式 `view/list` 在 `force_re_route=0` 时忽略 `default_view` | 源码 `router.js:207-214` + `242-286` |
| `default_view='Tree'` 确实抵达客户端 meta | `get_meta_bundle` 实跑输出 |
| `force_re_route_to_default_view = 0` | `tabDocType` 实查 |
| `load_last_view()` 在本场景不进调用栈 | `list_factory.js:23` 唯一调用点 + `render_page()` 派发 `TreeFactory` |
| 全站 `__UserSettings` 0 行 | `select count(*)` 实跑 |
| `__tree_js` 下发、`__list_js` 为空 | `get_meta_bundle` 实跑 |
| `TreeFactory` 非懒加载 | `hooks.py:25-33` |
| 树数据接口可用 | `get_children` 实跑 |
| **R6 两个前提均不成立；V-07 的 `last_view` 假设不成立** | 上述各条 |

### 8.2 仍是推断（未钉死）

1. **§6.1 与 §6.2 都未在浏览器验证。** 我没有浏览器工具，**没有实际点过侧栏**。这两条是「路由链路健康 ⟹ 故障必在运行期」的演绎，加上与 R3 两个观察的吻合度排序，**不是直接证据**。
2. **空白页的确切 DOM 形态未知。** 「整页空白」与「有页框但树为空」在现象描述里无法区分，而两者根因不同（§5.4）。建议复核时明确这一点。
3. **R3 当时的站点状态无法回溯。** 当时是骨架站（可能无默认 Company），与现在数据已恢复的状态不同。R3 的「偶发」是否与当时 company 为空有关，无法用今天的站点验证。
4. **本轮判定的作用域限于当前站点状态。** 我证明的是「当前状态下链路健康、本应正常」，而**不是**「现象不存在」。若现象今天仍能复现，则§6 的运行期候选成立；若今天已不复现，则 R6 的「必然」判定被现象本身否证。**这两种情况需要一次浏览器实点来分辨，这是下一步唯一的关键动作。**

### 8.3 我做的写操作：无

- **未执行任何写操作。** 全部 bench console 调用均为读（`frappe.db.sql` 的 SELECT、`frappe.get_all`、`frappe.db.get_default`、`frappe.db.get_single_value`、`get_meta_bundle`、`frappe.boot.get_bootinfo`、两个 `get_children` 只读查询）。
- **未按任务书建议去改 `__UserSettings`**：因为实测该表 0 行且 `load_last_view()` 不进调用栈，(b) 分支已被否证，改写实验无判定价值 —— 省掉了一次不必要的写入。
- **未新建测试用户**（同上，无需要）。
- **未 import 任何 `erpnext.tests` 下模块。**
- **未修改 `frappe-bench/apps/` 下任何文件**，未修改 `docs/` 下任何文件。
- 唯一落盘产物：本文件 `D:\ERX-001\Spike\V10-tree-view-blank-rootcause.md`。
- 数据未受污染，可自查：Company 仍为 1（`['华东弹簧']`）、Account 95、Warehouse 6。

### 8.4 方法论备注

本项目前两次判错的共同模式是**拿间接证据当直接证据**：R3 凭现象推「偶发」，R6 凭文件存在性推「必然」。V-07 纠正了 R6，但自己又提出了一个未验证的 `last_view` 假设 —— 本轮用一条 `select count(*)` 就否掉了。**本轮的主要增量是把「`default_view` 是否真的抵达客户端 meta」这一真正的命门验了**（此前三次都没验），它成立，所以路由解析这一层可以整体结案，排查范围收窄到客户端运行期。
