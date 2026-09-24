# P1-S2-R2-A 调研：接入机制 — hook 合并顺序与多 app 冲突规则

源码：frappe 16.34.0 / erpnext 16.35.0（本机只读）。标注「读码」＝直接读到；「推断」＝由读码推出但未实跑。

## ① 合并顺序机制

**合并入口**（读码）

- `frappe/__init__.py:962-985` `_load_app_hooks()`：`:966` 取 `apps = get_installed_apps(_ensure_on_bench=True)`，`:968` **按该 list 的顺序**逐个 app import `<app>.hooks`，`:982-984` 把每个模块级变量交给 `append_hook`。**顺序完全等于 `installed_apps` 的列表顺序**，无任何排序/优先级字段。
- `frappe/__init__.py:1017-1035` `append_hook()`：
  - **dict 型**（`regional_overrides` / `doc_events` / `override_doctype_class` 等）`:1025-1029`：`setdefault(key, {})` 后对每个内层 key **递归**，即按 key 逐层深合并，最内层仍落到 list。
  - **list/标量型** `:1032-1035`：`setdefault(key, [])` 后 `extend` → **append，追加到尾部**。绝不 prepend。
- 故：**先装的 app 在前，后装的 app 在后；同一 key 多 app 注册即为一条列表，末位＝installed_apps 中最靠后的那个 app。**
- `frappe/__init__.py:992-1014` `get_hooks()`：只做缓存分流与取 key，不重排。

**app 顺序的来源**（读码）

- `frappe/__init__.py:924-942` `get_installed_apps()`：`:936` 顺序**唯一来源是数据库全局值** `installed_apps`（`db.get_global("installed_apps")`，实体是 `DefaultValue` 行，见 `installer.py:397-398`）。`:938-940` 的 `_ensure_on_bench` 只是**用 apps.txt 做成员过滤**，用列表推导，**保持原顺序**。
- 因此 **`apps.txt` 不决定顺序**。`get_all_apps()`（`:904-920`）里把 frappe 强插到 index 0（`:916-918`）只影响那个"全集"，不影响 hook 顺序。
- `site_config.json` 里的 `installed_apps` 只是镜像：`installer.py:658-663` `_sync_installed_apps_to_site_config()` 注释自称 "Mirror ... for fast reads"，**`get_installed_apps()` 并不读它**（读码）。
- **装新 app → 追加到尾部**：`installer.py:379-383` `add_to_installed_apps()` 用 `installed_apps.append(app_name)` 后整表写回。**新 app 永远排最后。**
- 卸载：`installer.py:393-398` `remove_from_installed_apps()` 用 `.remove()`，其余元素相对顺序不变。

## ② 「自有 app 会不会被挤出 regional_overrides 末位」

接入点 `erpnext/__init__.py:145`（读 hook）、`:152`（`overrides[function_path][-1]`）。

**结论：装 CRM / Raven / Flow / Insights / Helpdesk 不会挤掉你。**（读码 + 推断）

关键在于 `[-1]` 取的是 **`overrides[function_path]` 这一条**列表，而非全体 app 列表。该列表**只包含真正注册了「同一 region key 下同一 function_path」的 app**。未声明 `regional_overrides` 的 app 对这个 dict 零贡献，排在你后面也进不了那条 list。

- CRM / Raven / Flow / Insights：无 `regional_overrides`（由调用方提供，未重查）→ **完全无关**。
- HRMS：只在 `India` 键下注册 3 个 HRA/税函数。`append_hook` 是**按 key 深合并**（`:1025-1029`），`China` 键与 `India` 键互不相干；且 `:145` 按 `get_region()` 单键查找 → **China 场景下 HRMS 不参与**。
- **真正的风险条件（三者同时成立才出事）**：某 app ① 声明 `regional_overrides`，② 用**同一 region key**（`China`），③ 覆盖**同一 function_path**，④ 且装在你后面。目前已知 app 无一满足。

**安装顺序能否人为控制**

- 能（推断，未实跑）：`installed_apps` 就是一个有序 list，`add_to_installed_apps` 只 append。**最省事的办法是把自有 app 放在最后 `bench install-app`**。
- 也可直接改 DB 里那条 `DefaultValue`（defkey=`installed_apps`）重排顺序 + `bench clear-cache`（推断：读码看顺序确实只由这条值决定，但属于改数据库全局值，未实跑，且 `_sync_installed_apps_to_site_config` 的镜像需同步）。
- **后续再装 app 会不会打乱**：不会重排已有项，新 app 一律追加到尾 → 你会从"最后"变成"倒数第 N"。**对 regional_overrides 无影响**（见上），但**对下面 ③ 里"后者胜出"类 hook 有影响**。
- **卸载再装自有 app**：`.remove()` 后再 `.append()` → **反而回到末位**，更安全。

**规避办法（按推荐度）**

1. **不依赖 `[-1]`**：中国本地化的关键覆盖不走 `regional_overrides`，改用 `override_doctype_class`（也是 `[-1]`，同样问题）或直接用 `doc_events`（**累加执行，不存在被覆盖**，见 ③.1）。对"算 GL 分录/算税"这类**替换**语义的点，`doc_events` 不合适，建议保留 `regional_overrides` + 下面第 2 条自检。
2. **启动自检 + 告警**（推荐，成本低）：自有 app 挂 `after_migrate` / `boot_session` / 定时任务，调 `frappe.get_hooks("regional_overrides", {}).get("China", {})`，逐条断言 `list[-1]` 落在自己的模块前缀上，否则 `frappe.log_error` + 在 System Console/Notification 告警。这是对 `[-1]` 语义的直接校验，不依赖对 app 顺序的假设。
3. **安装顺序纪律**：写进部署脚本——自有本地化 app 永远最后装；每次新装 app 后跑一次第 2 条自检。

## ③ 四类 hook 的多 app 冲突规则

| hook | 规则 | 实现位置（读码） | 顺序由什么决定 |
|---|---|---|---|
| `doc_events` | **全部累加执行**，无覆盖 | `model/document.py:1651-1663` composer 把 `doc_events[doctype][method]` **＋** `doc_events["*"][method]` 全部收进 `hooks`；`:1633-1648` `compose` 先跑原方法 `fn`，再 `for f in hooks` 逐个跑 | installed_apps 顺序；**同 DocType 的具体 handler 全部先于 `"*"` 通配 handler** |
| `override_whitelisted_methods` | **后者胜出** | `frappe/__init__.py:1577-1581` `return overrides[-1] if overrides else original_method` | installed_apps 末位胜 |
| `override_doctype_class` | **后者胜出** | `model/base_document.py:110` 取 hook，`:116-117` `import_path = class_overrides[doctype][-1]` | installed_apps 末位胜 |
| `app_include_js` / `app_include_css` | **累加，无覆盖** | `www/desk.py:38-39` `hooks.get("app_include_js", []) + frappe.conf.get("app_include_js", [])` | installed_apps 顺序，`site_config` 里的追加在最后 |

**关于 `app_include_js`（本项目 realtime 注入）**：累加、按 app 顺序全量下发，**不会被其它 app 覆盖或挤掉**（读码）。唯一注意点是执行时序——你的脚本在其它 app 的 bundle 之后或之前加载取决于 app 顺序，故监听代码应自带"DOM/`frappe.realtime` 就绪判断"，别假设自己最先或最后跑（推断）。

**三组 `override_doctype_class` 有无实际冲突：无。**（读码）三组 DocType 集合两两无交集：CRM `Contact`/`Email Template`；HRMS `Employee`/`Timesheet`/`Payment Entry`/`Project`；Helpdesk `Email Account`/`Assignment Rule`/`User Invitation`。另：`grep override_doctype_class erpnext/hooks.py` **无命中**，erpnext 本体不覆盖任何 DocType，故与 erpnext 也不冲突。

两个附带发现（读码）：

- `installer.py:325-331`：`bench install-app` 时会检测"该 app 覆盖的 DocType 已被别的 app 覆盖"，但**只 `click.secho(..., fg="yellow")` 打一行黄字警告，不阻断安装**。
- `base_document.py:120-126`：覆盖类**必须是原类的子类**，否则 `frappe.throw("Invalid Override")`。这是硬校验，多 app 串联覆盖时后者只会基于**原始类**校验，不会自动继承前一个覆盖 → 前一个 app 的覆盖被**静默丢弃**。

## ④ hooks 缓存与生效时机

**有缓存，三层**（读码）：

1. `get_hooks()` `:1003-1004` — `developer_mode` 开启时走 `_site_cached_load_app_hooks`（`:989` `site_cache`，**进程内**持久缓存）。
2. `get_hooks()` `:1006-1009` — 非 developer_mode 走 `client_cache.get_value("app_hooks")`（进程内 LRU + redis，`redis_wrapper.py:478` 默认 `ttl=10*60`，跨进程失效"不保证亚秒级"，见 `:465-467` 注释）。
3. 指定 `app_name=` 时走 `_request_cached_load_app_hooks`（`:988`，仅单请求内）。
4. `doc_events` 另有一层：`frappe/__init__.py:945-959` 缓存在 `frappe.local.doc_events_hooks`（单请求内）。

**失效路径**（读码）：`"app_hooks"` 列在 `cache_manager.py:24` 的 `global_cache_keys` 里，`clear_global_cache()`（`:103-110`）会删。`install_app` 在 `installer.py:303` 和 `:313` 各调一次 `frappe.clear_cache()`，尾部还调 `frappe.client_cache.erase_persistent_caches()`（`redis_wrapper.py:615-628`，向 worker 广播 `clear_persistent_cache` 清进程内 `@site_cache`）。

**可操作结论**：

- **改了 `hooks.py` 之后必须 `bench clear-cache`**（非 developer_mode 下 redis 里那份 `app_hooks` 不会自己过期到位，最坏等 10 分钟 TTL）。
- **developer_mode 下 `clear-cache` 可能不够**——那层是进程内 `site_cache`，靠 redis 广播清理；稳妥做法是 `bench restart`（或重启 web/worker 进程）（推断：读到广播机制存在，但未实跑验证 `clear-cache` 命令是否触发该广播）。
- **装新 app 后不需要手动清**：`install_app` 自己清了（读码）。但**已在跑的 worker 进程**是否立刻看到新顺序，取决于广播是否到达——实测时建议顺手 `bench restart`。

## ⑤ 拿不准 / 未实跑

1. **未实跑任何 bench 命令**（按要求），以上全部为静态读码 + 标注的推断。
2. **改 DB 里 `installed_apps` 顺序来强制排位**：机制上成立（顺序唯一来源已读实），但未验证改完后 `Installed Applications` DocType 的 `update_versions()`（`installer.py:385`）与 site_config 镜像会不会把顺序改回去。**建议优先用"自有 app 最后装"而非改库。**
3. **CRM/Raven/Flow/Insights 无 `regional_overrides`、HRMS 只有 India 键**：采用调用方给的结论，本次未重查各 app 的 hooks.py。
4. `get_region()` 对"中国"返回的字符串究竟是 `China` 还是别的（取决于 Company.country / System Settings 里的国家名），未在本机站点里核对实际值。**自有 app 的 region key 必须与之逐字匹配**，这是实测第一步该确认的。
5. `doc_events` 里 `"*"` 通配与具体 DocType handler 的相对顺序（具体在前）是从 `document.py:1655-1657` 的 `+` 拼接读出的，未实跑打印验证。
6. 未核查 Frappe 是否还有别的地方（如 `boot`/`sessions`）对 `app_include_js` 做二次去重或裁剪；只读了 `www/desk.py` 这条主路径。
