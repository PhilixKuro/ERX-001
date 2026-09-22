# V-12 探针：侧栏 app 菜单的 `GET /undefined` 404

**命题**：侧栏头部 app 切换菜单拼图片 URL 时拿到 `undefined`（`sidebar_header.js:352` `add_app_item`），致每次加载侧栏即发一个 `GET /undefined` 404 请求——成因与影响面。

**判定**：`go`（命题成立）。**根因是上游 Frappe v16 的一处渲染遗漏：`icon_html` 有写入点、无读取点。**

**验证方式**：纯源码取证（读 frappe v16 源码）+ 用户浏览器实测的 Console 调用栈。**未改任何代码。**

---

## 根因

三条图标路径，模板只认两条。

**设值侧**（`frappe/public/js/frappe/ui/sidebar/sidebar_header.js`）有两处，逻辑相同：

```javascript
// :138-146（fetch_related_icons 内）与 :153-161（get_icon_for_menu_item 内）
if (frappe.utils.get_desktop_icon(icon.label, frappe.boot.desktop_icon_style)) {
    item.icon_url = frappe.utils.get_desktop_icon(icon.label, frappe.boot.desktop_icon_style);
} else {
    item.icon_html = frappe.utils.desktop_icon(icon.label, "gray", "sm");   // ← 走这里就出事
}
```

**渲染侧**（同文件 `:351-375` `add_app_item`）只处理 `icon` 与 `icon_url`：

```javascript
${
    item.icon
        ? frappe.utils.icon(item.icon)
        : `<img class="logo" src="${item.icon_url}">`     // ← icon_url 为 undefined 时输出 src="undefined"
}
```

**故当某菜单项既无 `icon`、又拿不到 `get_desktop_icon()` 的结果时**：走 else 分支设了 `icon_html`，但模板不读它，`item.icon_url` 是 `undefined`，模板内插值成字符串 `"undefined"` → 浏览器请求 `/undefined` → 404。

**决定性证据**：全仓 `icon_html` **只有那两个写入点、零个读取点**。

```bash
grep -rn "icon_html" frappe-bench/apps/frappe/frappe/public/js/frappe/ui/sidebar/
# → 只有 :145 与 :160 两行，均为赋值；无任何读取
```

## 用户浏览器实测的调用栈（与上述路径一致）

```
undefined:1  GET http://localhost:8000/undefined 404 (NOT FOUND)
    add_app_item          @ sidebar_header.js:352
    populate_dropdown_menu@ sidebar_header.js:346
    constructor           @ sidebar_header.js:103
    setup                 @ sidebar.js:290
    set_workspace_sidebar @ sidebar.js:682
```

`:103` 是 `this.dropdown_items.push(item)`——即出问题的是**动态加进来的那些项**（`sibling_workspaces` 一类），不是 `:9` 那批硬编码项（`desktop`/`workspaces`/`website` 等都自带 `icon`，故走 `frappe.utils.icon()` 分支、不受影响）。

## 影响面

| 项 | 判定 |
|---|---|
| 功能是否受损 | **否**。图标不显示（`<img src="undefined">` 渲染为破图占位），菜单项本身可点、路由正常 |
| 每次加载侧栏的额外请求 | 1 个 404（每个走 `icon_html` 路径的菜单项各一个） |
| 客户演示时是否可见 | **图标位置会显示浏览器的破图占位符**。可见性取决于 CSS——`.sidebar-item-icon` 若有固定尺寸与背景，破图可能不明显 |
| 是否属本项目引入 | **否，是上游 Frappe v16 的缺陷**。本项目未改过 `sidebar_header.js` |

## 与其他命题的关系

- **与 V-11a（socketio）无关**：修好 socketio 后该 404 仍在（用户第二次实测确认），证明两者独立。
- **与 V-07 例 2（侧栏卡片缺失）同属 `sidebar.js` 一带**，但机制不同：例 2 是 `add_card()` 全仓零调用者（卡片机制是死代码），本条是 `icon_html` 有写无读。**两者形态相似——都是"写入端与消费端脱节"**，可能同源于 v16 侧栏重构时的遗漏，但这一点未验证。

## 复核建议

1. **未验证的一点**：具体是哪些菜单项走了 `icon_html` 路径。要钉死须在浏览器里看 `dropdown_items` 的实际内容，或查 `get_desktop_icon()` 对哪些 label 返回空。**本探针只证明了"存在这条会产生 undefined 的路径"且调用栈与之吻合，未逐项枚举受影响的菜单项。**
2. **未验证破图的实际可见程度**——取决于 CSS，须浏览器目视。
3. **修法有两个方向**（属事实陈述，非建议）：① 模板补一个 `item.icon_html ? item.icon_html : ...` 分支；② 设值侧统一成 `icon_url`。前者改动小，后者与既有两条路径一致。**选哪个是 C 步架构讨论的事。**
4. **本条是上游缺陷**，故改法牵涉"改上游还是在自有 app 覆盖"——与 V-01 确立的 `regional_overrides` 不同，前端 js 的覆盖机制是另一套（`app_include_js`），未在本 Round 验证过。
