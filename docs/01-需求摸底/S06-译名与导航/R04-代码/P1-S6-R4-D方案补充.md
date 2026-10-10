# P1-S6-R4 D 方案补充

本文件追加执行依据，保留 R3 已冻结方案原文。日期：2026-10-10；执行者：Codex。

## DEC-024：消除旧侧栏菜单的无效图片请求

用户已选择 A：补充方案并修复。原方案 Part3 TS-010 第8步认为提供 SVG 即可消除 `/undefined` 请求；实测 `SidebarHeader.add_app_item` 在不存在的 `.sidebar-header-menu` 上仍构造脱离 DOM 的 `<img src="undefined">`，因此浏览器请求仍发生。原生可见菜单另由 Dropdown 管理。

在 `frappe_china/public/js/desk_patches.js` 包装 `frappe.ui.SidebarHeader.prototype.add_app_item`：`this.dropdown_menu?.length` 为零时返回；有容器时用 `original.apply(this, arguments)` 委托原方法。包装有幂等标记，类或方法不存在时跳过。不得改上游文件。

验收：Node 测试先红后绿，覆盖无容器、空容器、有容器保留参数/this/返回值、重复加载、缺少上游类；README 登记上游依赖与复验法。构建后用新浏览器登录、重复重建业务流程侧栏，`/undefined` 请求为0，SVG与可见下拉菜单仍可用；重新跑51项实际点击。该补充仅修复 TS-010 第8步路径，不降低其他 SL-007 验收条件。

## DEC-025：CN Tax 迁移时间戳

既有 `workspace_sidebar/cn_tax.json` 没有 `modified`；`frappe/modules/import_file.py:131` 用 `get_datetime(None)`（当前时刻）比较，每次迁移重新导入，违反 SL-007⑧ 的时间戳不变。用户选择 A：加固定时间戳，内容仍为空。将最近一次迁移后的库内时间戳 `2026-10-10 13:01:16.080084` 写入自有 JSON，后续相等或更旧时由原生导入器跳过。SL-007⑧ 调整为：仅允许补该字段，空侧栏及其他字段不变，重复迁移库内 modified 不变。原有入口 diff 的取证范围必须如实披露。
