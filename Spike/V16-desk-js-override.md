# V-16 探针：desk 自带前端 js 能否在自有 app 侧覆盖

**命题**（P1-S2-R4-C待验表 V-16）：desk 自带前端 js 的行为能否在自有 app 侧覆盖而不改上游源码
（判据：`app_include_js` 注入的脚本能否改变已定义的 desk 类/方法的行为，且在 `bench build` 后仍生效）。

**日期**：2026-09-24｜**站点**：`erx.localhost`（容器 `erx001-frappe-1`）
**版本**：frappe `16.34.0` @ `c1f1e8e`，erpnext `16.35.0` @ `12cd563`，Python 3.14.7，Node 24.21.0
**浏览器证据**：Chrome 153.0.8010.53 headless（Windows 宿主），经 CDP 驱动

## 走的哪条路

**建了一次性测试 app**（`erx_spike`），因为「覆盖真的生效」必须有真跑的证据（play-spike 纪律 5，不取推测）。
读码 + curl 只能定**加载顺序**，定不了**覆盖是否生效**——后者需要 JS 引擎。

宿主上有 Chrome 与 Node 24（Node 24 自带全局 `WebSocket`），故用 CDP 直接驱动真浏览器，
无需装任何 npm 依赖。容器内**没有**任何浏览器/jsdom/playwright/selenium（已查）。

测试 app 是**手搓**的，不走 `bench new-app`：后者会 `pip install -e`，而本 bench 连
`flit_core` 都没装。手搓只用 `.pth` 文件进 `sys.path`——这正是 frappe/erpnext 自己在本
bench 里用的机制（`env/lib/python3.14/site-packages/{frappe,erpnext}.pth`）。

两条注入路径同时挂，一次跑答两问：

| 路径 | hooks.py 里写法 | 过不过 esbuild |
|---|---|---|
| A | `erx_spike.bundle.js` | 过，走 assets.json |
| B | `/assets/erx_spike/js/V16-raw-probe.js` | 不过，裸路径 |

同一份 payload（md5 一致）装在两条路径上，各自用 `document.currentScript.src` 自报身份。

## 四档结论

### 第 1 档 追加能力（基线）→ 成立

`app_include_js` 注入的 js **确实被加载并执行**进 desk 页面。两条路径都进：

```
run[0] src=.../assets/erx_spike/dist/js/erx_spike.bundle.7XDLIRIQ.js   （bundle 路径）
run[1] src=.../assets/erx_spike/js/V16-raw-probe.js                     （裸路径）
```

### 第 2 档 覆盖能力（关键）→ 成立

**实测加载顺序：自有 app 的脚本在 desk 自身 bundle 之后。** 这是本次最有价值的产出，详见下节。

因为在后，desk 的类在自有脚本 parse 时**已经定义好了**，所以**直接改原型即可**，
不需要 `frappe.ready`、不需要等事件。四种手法全部实测生效（`calls` 是真实被调用次数，
不是安装成功计数）：

| 手法 | 目标 | installed | calls | 说明 |
|---|---|---|---|---|
| a 换原型方法 | `frappe.ui.SidebarHeader.prototype.get_icon_for_menu_item` | true | **17** | 完全替换实现 |
| b 包命名空间函数 | `frappe.utils.desktop_icon` | true | **2** | 保留原函数再包一层 |
| c 包渲染方法 | `frappe.ui.SidebarHeader.prototype.add_app_item` | true | **26** | 首次被调用在注入后 +54~61ms |
| d 跨路由存活 | `frappe.views.ListView.prototype.setup_defaults` | true | **1** | SPA 路由跳转后仍生效 |

对照组（同一浏览器、同一 session，用 CDP `Page.addScriptToEvaluateOnNewDocument`
预置 `window.__ERX_V16_DISABLE_PATCH=true`，该脚本先于任何页面脚本执行）：
`installed_here=false`、三处 patch 全空、DOM 结果一致——证明上面的 calls 是补丁真被走到，
不是探针自说自话。

### 第 3 档 构建边界 → 成立，但有一条必须知道的前提

`bench build` **不丢注入**，且**必须跑一次**：

| | bundle 路径（A） | 裸路径（B） |
|---|---|---|
| build 前 | 模板算出 `/erx_spike.bundle.js`，**HTTP 404**（assets.json 无此条目，`bundled_asset()` 原样返回） | HTTP 200，正常执行 |
| build 后 | `/assets/erx_spike/dist/js/erx_spike.bundle.7XDLIRIQ.js`，**HTTP 200**，执行 | HTTP 200，正常执行 |

`bench build` 退出码 0，assets.json 44 → 45 条：**新增** `erx_spike.bundle.js`，
**零删除**，其余 **44 条哈希全部变化**（全量重建，含 `desk.bundle.js`
`LHZJYI3U`→`OSOIKW5M`）。build 后重跑浏览器探针，四种手法 calls 与 build 前**完全一致**
（17/2/26/1）——bundle 重建没有削弱覆盖。

> 按 MEMORY 里那条教训（历史上只验 login 页 CSS 就宣称修好，`login.bundle` 哈希恰好匹配而
> `desk.bundle` 不匹配），这里是**全量 diff 44 条**逐条比对，不是抽查一个 bundle。

### 第 4 档 没触及的边界

见待验表「复核建议」节。

## 实测的加载顺序（本次核心产出）

拼 include 列表的代码在 `apps/frappe/frappe/www/desk.py:get_context()`：

```python
hooks = frappe.get_hooks()
app_include_js = hooks.get("app_include_js", []) + frappe.conf.get("app_include_js", [])
```

关键事实：**desk 自己的 9 个 bundle 就是 frappe 这个 app 的 `app_include_js` hook 值**
（`apps/frappe/frappe/hooks.py:25-34`：libs / billing / desk / list / form / controls / report
/ telemetry）。所以自有 app 的注入和 desk 自身 bundle **走的是同一个 hook、同一个列表**，
顺序完全由 app 顺序决定：

- `_load_app_hooks()` 按 `get_installed_apps()` 顺序遍历，`append_hook()` 逐个 `extend` 到同一个 list
- `get_all_apps()` 强制把 `frappe` 提到第 0 位（`apps.remove("frappe"); apps.insert(0, "frappe")`）
- 故顺序恒为：**frappe → erpnext → 自有 app**，自有 app 永远在最后

desk 页面 HTML 实测 script 标签顺序（`frappe/www/desk.html` 的
`{% for include in app_include_js %}` 循环，build 后）：

```
 1 /assets/frappe/dist/js/libs.bundle.JEM3HUCP.js
 2 /assets/frappe/dist/js/billing.bundle.H53FAIQO.js
 3 /assets/frappe/dist/js/desk.bundle.OSOIKW5M.js      <- desk 自身
 4 /assets/frappe/dist/js/list.bundle.A7JXYPOT.js
 5 /assets/frappe/dist/js/form.bundle.MMUJRLG3.js
 6 /assets/frappe/dist/js/controls.bundle.PET2W764.js
 7 /assets/frappe/dist/js/report.bundle.RR54Y74O.js
 8 /assets/frappe/dist/js/telemetry.bundle.RXBBNH3H.js
 9 /assets/erpnext/dist/js/erpnext.bundle.CDNUUMVF.js
10 /assets/erx_spike/dist/js/erx_spike.bundle.7XDLIRIQ.js   <- 自有 app（bundle 路径）
11 /assets/erx_spike/js/V16-raw-probe.js                    <- 自有 app（裸路径）
```

全部是**同步** `<script src>`，**无** `defer` / `async` / `type="module"`（实测计数为 0），
故浏览器按文档顺序**顺序执行**，前一个执行完才解析下一个。

自有脚本 parse 那一刻的实测 `typeof`（`document.readyState` 仍为 `loading`）：

| 目标 | typeof | 能否 parse 时改 |
|---|---|---|
| `frappe.ui.SidebarHeader` | `function` | 能 |
| `frappe.ui.SidebarHeader.prototype.get_icon_for_menu_item` | `function` | 能 |
| `frappe.views.ListView` | `function` | 能 |
| `frappe.ui.form.Form` | `function` | 能 |
| `frappe.views.QueryReport` | `function` | 能 |
| `frappe.views.KanbanView` / `CalendarView` / `GanttView` | `function` | 能 |
| `frappe.ui.FileUploader` | `function` | 能 |
| `frappe.utils.desktop_icon` | `function` | 能 |
| `frappe.router` | `object` | 能 |
| `erpnext` | `object` | 能 |
| **`frappe.app`** | **`undefined`** | **不能**（实例，尚未构造） |
| **`frappe.ready`** | **`undefined`** | **不能**（desk 页无此 API） |
| **`frappe.form_builder` / `frappe.ui.FormBuilder`** | **`undefined`** | **不能**（未被 require） |
| **`frappe.PrintPreview`** | **`undefined`** | **不能**（未被 require） |

**由此定手法**：

- 改**类 / 原型方法 / 命名空间函数** → 直接在注入脚本顶层改原型，最简单，实测生效
- 改**实例**（`frappe.app`、`frappe.app.sidebar` 等） → parse 时 `undefined`，**必须等**；
  但**不能用 `frappe.ready`**（desk 页 `frappe.ready` 是 `undefined`，实测该回调从未触发，
  `ready_fired_dt_ms` 恒为 `null`）。可用的替代：`DOMContentLoaded`（实测 +8~12ms 触发）、
  轮询、或 `frappe.router.on("change")`（实测注入后 +1ms 即可挂上）
- 改**懒加载模块**（form builder / print preview 等未被 `frappe.require` 拉进来的） → parse
  时 `undefined`，改原型改不到；须等其 bundle 真被加载后再打。实测这类确实会晚到：强制
  `frappe.set_route('List','Item','Kanban')` 后 `frappe.views.KanbanView` 才由 `undefined` 变 `function`

## SPA 路由边界（架构类命题必须验的一条）

desk 是单页应用，CR-008 的演示操控必须在**路由跳转后仍然生效**，不能只在首屏成立。实测：

- 注入脚本里挂 `frappe.router.on("change")`，注入后 **+1ms** 挂上
- 客户端跳 `frappe.set_route('List','Item')` → `route_changes` 计数增长，patch d
  （`ListView.prototype.setup_defaults`）被调用，`last_doctype = "Item"`
- 再跳 `frappe.set_route('List','Account')` → 实际落到 **`Tree/Account`**（`is_tree=1` 的
  DocType 被重定向到树视图，即 EN-001 那个现象的路由侧表现）
- 三次路由变更后 patch 仍在（未被重置）

## 顺手发现的事实（不写建议，纪律 5）

1. **LG-074 的根因位置与待验表所记不一致。** 待验表写的是
   `frappe/public/js/frappe/views/workspace/sidebar_header.js:145/:160`，该路径**不存在**；
   实际文件是 `frappe/public/js/frappe/ui/sidebar/sidebar_header.js`，
   `item.icon_html = ...` 两处确实在 **145** 与 **160** 行（行号对得上，目录不对）。
2. **「全仓 `icon_html` 零读取点」不成立。** 排除 dist / node_modules / .map 后，源码里
   读 `item.icon_html` 的至少有两处：`frappe/public/js/frappe/ui/menu.js:96-97`
   与 `frappe/public/js/frappe/ui/settings_dialog.js:255-258`。而
   `sidebar_header.js:351-375` 的 `add_app_item()` 确实只读 `item.icon` / `item.icon_url`，
   不读 `icon_html`——待验表对**这一处**的描述是对的，"全仓零读取"是过头了。
3. **`/desk/undefined` 这个 404 不是 `get_icon_for_menu_item` 产生的。** 探针把该方法整个换掉、
   实测被调用 17 次，`/desk/undefined` 仍然出现**一次**；且**未打补丁的对照组也是一次**，
   数量相同。所以那条 404 另有来源。指向 `set_header_icon()`
   （`sidebar_header.js:299-316`）：四个分支都拼 `` `<img src=${this.header_icon}></img>` ``，
   **属性值没加引号**，一旦取到 `undefined` 就落成 `/desk/undefined`。其中
   `get_default_icon()` 返回 `frappe.boot.app_data[0].app_logo_url`。
   **注意**：本站点实测该值是 `/assets/frappe/images/frappe-framework-logo.svg`（有值），
   且实测 DOM 里 `.header-logo` 渲染出的是
   `<img src="/assets/erpnext/icons/desktop_icons/solid/stock.svg">`，
   `imgs_with_undefined_src` 为**空数组**——即那个 `<img>` 已被后续重渲染覆盖掉，
   404 发生在中间态。CDP 抓到该请求的 `initiator.type = "script"` 但
   **`stack` 为空**（异步初始化，调用栈已丢），故**具体是哪一行发出的，本次没有定论**。
4. **「修它只要 app 侧三行」这个判断本次给不出。** 覆盖机制本身成立（第 2 档），但 LG-074 那
   条 404 的确切产生点没定到（上一条），所以覆盖哪个方法能消掉它，没有实测依据。
5. **测试 app 必然出现在 app switcher 里。** 装上后 `frappe.boot.app_data` 从 2 条变 3 条，
   且手搓 app 的 `app_logo_url` 回来的是**数组** `["/assets/frappe/images/frappe-framework-logo.svg"]`
   而非字符串（`boot.py:221-223` 取 `frappe.get_hooks(...)` 的结果，hooks 值天然是 list，
   正规 app 靠 `add_to_apps_screen` 的 `logo` 字段避开），`app_route` 为空串。
   这是**手搓 app 的产物**，不是 LG-074 的一部分。卸载后 `app_data` 回到 2 条，
   而 `/desk/undefined` **依旧出现**——故那条 404 是站点既有现象，与测试 app 无关。

## 复现步骤

```bash
cd /d/ERX-001
export MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*'

# 0. web 服务得在跑（本次接手时容器内只有 sleep infinity，bench serve 并未起）
docker exec -d -w /workspace/frappe-bench erx001-frappe-1 bash -c "bench serve --port 8000 >> /tmp/v16-serve.log 2>&1"

# 1. 建测试 app 并装站（幂等）
docker exec -w /workspace/frappe-bench erx001-frappe-1 bash /workspace/Spike/V16-setup-test-app.sh

# 2. 重启 serve —— .pth 只在解释器启动时读，不重启则 ModuleNotFoundError
docker exec erx001-frappe-1 bash -c "ps -eo pid,args | grep '[b]ench_helper frappe serve' | awk '{print \$1}' | xargs -r kill -9"
docker exec -d -w /workspace/frappe-bench erx001-frappe-1 bash -c "bench serve --port 8000 >> /tmp/v16-serve.log 2>&1"

# 3. 浏览器实测（宿主跑，Chrome + Node 24，无需 npm 装包）
node D:\ERX-001\Spike\V16-cdp-run.js prebuild-patched
node D:\ERX-001\Spike\V16-cdp-run.js prebuild-baseline --baseline   # 对照组

# 4. 构建边界
docker exec -w /workspace/frappe-bench erx001-frappe-1 bench build
node D:\ERX-001\Spike\V16-cdp-run.js postbuild-patched

# 5. 边界细查
node D:\ERX-001\Spike\V16-cdp-inspect.js            # 懒加载模块 / app_data
node D:\ERX-001\Spike\V16-cdp-trace-undefined.js    # /desk/undefined 初始化者

# 6. 卸载并核验
docker exec -w /workspace/frappe-bench erx001-frappe-1 bench --site erx.localhost uninstall-app erx_spike --yes --no-backup
docker exec -w /workspace/frappe-bench erx001-frappe-1 ./env/bin/python /workspace/Spike/V16-cleanup-check.py
docker exec -i -w /workspace/frappe-bench erx001-frappe-1 bench --site erx.localhost mariadb < /workspace/Spike/V16-cleanup-check.sql
```

## 本次踩到的坑（给后续探针省时间）

1. **`bench serve` 当时没在跑**——容器 PID 1 是 `sleep infinity`，`curl` 得 `HTTP 000`。
   `docker compose` 命令须在 `docker/` 目录下跑（compose.yaml 在那儿），或直接 `docker exec`。
2. **宿主 curl 写不出 cookie jar**（MSYS 路径），且宿主**解析不了 `erx.localhost`**
   （`getaddrinfo ENOTFOUND`）。对策：HTTP 交互放进容器里做；浏览器侧靠 Chrome 的
   `--host-resolver-rules=MAP erx.localhost 127.0.0.1`；Node 的 `fetch` 用
   `127.0.0.1` + 显式 `Host` 头。
3. **`docker exec` 不带 `-i` 时 heredoc 写文件得到 0 字节**（stdin 未接）。对策：文件写宿主
   项目目录（bind mount），容器里用 `/workspace/...` 读。
4. **`sites/apps.txt` 结尾没有换行符**。`echo >> ` 会拼成 `erpnexterx_spike`，
   `install-app` 报 `App erx_spike not in apps.txt`。
5. **`.pth` 只在解释器启动时读**。装完 app 不重启 `bench serve`，整站 500
   （`ModuleNotFoundError: No module named 'erx_spike'`）。
6. **`pkill -f 'bench serve'` 匹配不到**——真实 cmdline 是
   `python -m frappe.utils.bench_helper frappe serve --port 8000`。旧 worker 没死，
   新进程 `Address already in use` 静默退出，看起来像"改了没生效"，实际是旧进程在应答。
7. 容器内 PID 1 是 `sleep infinity`，不回收子进程，`ps` 里会堆 `<defunct>` 僵尸，属正常。
8. **本次容器是共用的**——中途看到一个我没起的 `bench --site erx.localhost migrate`
   在跑（V-15 探针）。杀进程务必按 PID 精确杀，不要 `pkill` 一片。

## 文件清单

| 文件 | 用途 |
|---|---|
| `V16-desk-js-override.md` | 本文 |
| `V16-desk-js-override.probe.js` | 注入 payload（四种覆盖手法 + parse 时 typeof 采集） |
| `V16-setup-test-app.sh` | 手搓测试 app 并装站 |
| `V16-cdp-run.js` | CDP 主探针（含 `--baseline` 对照组、SPA 路由跳转） |
| `V16-cdp-inspect.js` | 懒加载模块边界 / `app_data` 实况 |
| `V16-cdp-trace-undefined.js` | 追 `/desk/undefined` 的初始化者 |
| `V16-cleanup-check.py` | 卸载后核验 + 清 assets.json 残留 |
| `V16-cleanup-check.sql` | 卸载后核验数据库残留 |
| `V16-out/*.json` | 四次跑的原始输出（prebuild-patched / prebuild-baseline / postbuild-patched / postbuild-boundary 等） |

## 环境收尾

- 测试 app `erx_spike`：**已从站点卸载**（`bench uninstall-app`，`list-apps` 只剩 frappe/erpnext）
- **目录也删了** `frappe-bench/apps/erx_spike`，连同 `.pth`、`sites/assets/erx_spike` 符号链接
- `sites/apps.txt` 还原为原始字节 `b'frappe\nerpnext'`（原文件结尾无换行，已逐字节核对）
- `sites/assets/assets.json` 里 `bench build` 写入的 `erx_spike.bundle.js` 条目**已清**
  （45 → 44 条；`uninstall-app` 不管这个文件，会残留并被塞进每个 desk 页的 boot 负载）
- 数据库残留核验：Module Def / Desktop Icon / Workspace Sidebar / Workspace Sidebar Item /
  DocType / installed_apps / DefaultValue **全部无 `erx_spike` 行**
- **上游源码未改**（纪律 8）：`apps/frappe` 工作区 `git status --porcelain` 为空。
  `apps/erpnext` 有两个文件显示改动（`banking/yarn.lock`、
  `erpnext/stock/number_card/total_stock_value/total_stock_value.json`），**不是本次造成的**：
  两者 mtime 均为 **2026-09-18 16:10**（本 Session 为 09-24），diff 是纯行尾符差异
  （3741 增 / 3741 删，逐行等量）
- **`bench build` 跑过一次**（第 3 档必需），故 `sites/assets/` 下**所有** 44 个 bundle
  哈希都变了。这是 bench 的正常产物、不进版本管理（`frappe-bench/` 在 .gitignore 内），
  但若别处记录过旧哈希，那些记录已过期
- `bench serve` 现仍在运行（端口 8000，站点可用，desk 页 HTTP 200、script 标签回到 9 个）
