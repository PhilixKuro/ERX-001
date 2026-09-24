# P1-S2-R2 A 调研：接入机制 — 认证与 CSRF

源码：`D:\ERX-001\frappe-bench\apps\frappe`（Frappe 16.34.0）。行号均为读码所得；凡标「推断」者未实跑验证。

## ① 认证方式表

| 方式 | 请求怎么写 | 实现位置 |
|---|---|---|
| Cookie session | 请求带 `sid=<hash>` cookie；非 GET 还需 CSRF token（见②） | 会话恢复 `frappe/auth.py:130-139`（`LoginManager.__init__`，非 login 路径走 `make_session(resume=True)`）；`frappe/sessions.py:210-317`（`Session`，`resume()`） |
| API key/secret（token 式） | `Authorization: token <api_key>:<api_secret>` | `frappe/auth.py:709-711` → `validate_api_key_secret()` `frappe/auth.py:721-747` |
| API key/secret（basic 式） | `Authorization: Basic <base64(api_key:api_secret)>` | `frappe/auth.py:706-708`（同上 `validate_api_key_secret`） |
| OAuth2 Bearer | `Authorization: Bearer <access_token>` | `frappe/auth.py:655-692`（`validate_oauth`，查 `OAuth Bearer Token` 取 user） |
| 自定义 hook | 由 app 的 `auth_hooks` 决定 | `frappe/auth.py:750-752`（`validate_auth_via_hooks`） |

识别入口统一在 `validate_auth()` `frappe/auth.py:629-652`：切 `Authorization` 头为两段（`auth.py:633`），依次试 OAuth、api key、hooks；若带了 `Authorization` 两段头却仍是 Guest，抛 `AuthenticationError`（`auth.py:644-645`）。被调用点在 `frappe/app.py:141`。

补充两点（读码所得）：
- `validate_api_key_secret` 仅在当前 `login_manager.user in ("", "Guest")` 时才 `frappe.set_user(user)`（`auth.py:743-744`）——即**已有 cookie 会话时，api key 头不会顶替 cookie 身份**。
- 非 User doctype 也可持 key，用 `Frappe-Authorization-Source` 头指定（`auth.py:705`、`auth.py:726`）。

## ② CSRF 结论

**校验点唯一**：`HTTPRequest.validate_csrf_token()` `frappe/auth.py:81-97`。由 `HTTPRequest.__init__` 第 48 行调用（`auth.py:48`），而 `HTTPRequest()` 在 `init_request()` 里构造（`frappe/app.py:242`，`request.method != "OPTIONS"` 时）。

**哪些请求需要**：不看路径，只看方法。`UNSAFE_HTTP_METHODS = {POST, PUT, DELETE, PATCH}`（`auth.py:29`），`SAFE_HTTP_METHODS = {GET, HEAD, OPTIONS}`（`auth.py:28`）。`auth.py:84` 对非 unsafe 方法直接放行。即 **所有路径的 POST/PUT/DELETE/PATCH 都过这一关，GET 全免**。

**任一条件成立即放行**（`auth.py:82-94`，or 链）：
1. 无 `frappe.request`；
2. 方法不在 UNSAFE 集合（`auth.py:84`）；
3. `frappe.conf.ignore_csrf` 为真（`auth.py:85`）；
4. 无 `frappe.session`（`auth.py:86`）；
5. **`frappe.session.data.csrf_token` 为空**（`auth.py:87`）；
6. 头 `X-Frappe-CSRF-Token` 或表单字段 `csrf_token` 等于会话里存的值（`auth.py:89-91`）；
7. Referer/Origin 命中 `site_config.json` 的 `allowed_referrers`（`auth.py:92`、`is_allowed_referrer()` `auth.py:102-118`）。
否则 `frappe.throw(_("Invalid Request"), frappe.CSRFTokenError)`（`auth.py:97`）。

**token 从哪来**：生成在 `frappe/sessions.py:197-207`（`get_csrf_token()` / `generate_csrf_token()`，值是 `frappe.generate_hash()`，存在 session data 里）。下发有两条：
- desk：`frappe/www/desk.py:35` 取 token，`www/desk.py:57` 塞进模板 context 的 `csrf_token`；前端以 `frappe.csrf_token` 读到，请求时挂头 `frappe/public/js/frappe/request.js:267`（还有 `public/js/frappe/microtemplate.js:243`）。
- 网站页：`frappe/website/page_renderers/base_template_page.py:18-25`，把 HTML 里的 `<!-- csrf_token -->` 占位替换成 `<script>frappe.csrf_token = "..."</script>`；网站侧挂头在 `frappe/website/js/website.js:89`。
- OAuth 授权页另有一处 `frappe/integrations/oauth2.py:156`。
（**不是 meta 标签，是内联 script 全局变量**。）

**⭐ api_key/api_secret 是否豁免 CSRF —— 豁免。** 两条行号依据合起来构成直接证据：
1. **执行顺序**：CSRF 校验发生在 `app.py:242`（`init_request` 内），`validate_auth()` 在 `app.py:141` 之后才跑。校验时 api key 还没被识别，会话仍是 cookie/Guest 那个。
2. **Guest 会话没有 csrf_token**：外部脚本不带 `sid` cookie 时会话是 Guest（`sessions.py:401-404` `start_as_guest`）；`start()` 只给非 Guest 写 session data（`sessions.py:272-281`），`csrf_token` 只由 `generate_csrf_token()`（`sessions.py:204-207`）写入，而它唯一被 `get_csrf_token()` 调用（`sessions.py:197-201`），调用方是 desk.py / billing.py / oauth2.py 这些需登录页面，Guest 走不到；且 `Session.update()` 对 Guest 直接 return（`sessions.py:409-410`），token 也无从持久化。于是 `auth.py:87` 的条件 5 成立 → 放行。

**⚠ 反面情形（重要）**：若脚本所在环境**同时携带了有效 `sid` cookie**（例如在浏览器里、或 requests.Session 复用了登录 cookie），条件 5 不成立，**CSRF 会被强制校验**，而此时 api key 头也不会改变身份（`auth.py:743-744`）。**所以脚本必须保持「不带 cookie」的干净客户端**。

**关掉 CSRF 的配置项**：`site_config.json` 里 `ignore_csrf: 1`（`auth.py:85` 直读 `frappe.conf.ignore_csrf`，全站生效）。另有 `allowed_referrers` 列表（`auth.py:109`）按来源域放行。
安全代价：`ignore_csrf` 关掉后，任何第三方页面都能借用户浏览器里的登录 cookie 发起写操作（建单、改权限、删数据），是站点级 CSRF 洞。**演示环境尚可，绝不要带进客户正式站**。且如下文所述，走 api key 本就不需要它。

## ③ 外部脚本可行性（可操作结论）

**结论 A：外部 Python 脚本拿 `api_key:api_secret` 可以直接调 API 建单据，无需处理 CSRF。**
只要客户端不带 `sid` cookie，`auth.py:87` 条件成立即豁免（依据见②）。请求形如：
```
POST /api/resource/<DocType>
Authorization: token <api_key>:<api_secret>
Content-Type: application/json
```
路由在 `frappe/api/__init__.py:23-62`（`handle()`，`/api/v1|v2` 与兼容路径），`/api/method/<dotted.path>` 调白名单方法。权限按该 api_key 绑定的 User 的角色走，与普通登录用户同待遇（`auth.py:738-744` 设的就是真实 user）。

**结论 B(i)：脚本以自己的身份调 `publish_realtime(user="演示用户")` —— 通，且服务端 publish 不做调用者身份校验。**
`publish_realtime` `frappe/realtime.py:23-83`：给了 `user` 就取 `room = get_user_room(user)`（`realtime.py:64-66`，房间名 `user:<user>`，见 `realtime.py:167-168`），然后 `emit_via_redis` 直接 `r.publish("events", {...})`（`realtime.py:100-115`）。**整个函数体内没有任何 `has_permission` / `only_for` / 调用者与目标 user 的比对**——读码所得，不是推断。
但注意：`publish_realtime` **本身没有 `@frappe.whitelist()` 装饰器**（`realtime.py:23` 上方仅注释，模块内被装饰的只有 `has_permission`（`realtime.py:118`）和 `get_user_info`（`realtime.py:142`））。**所以外部不能直接 `/api/method/frappe.realtime.publish_realtime` 调它**，必须包一层（见④）。

**结论 B(ii)：复用浏览器已登录会话的 cookie —— 技术上可行但不该走。**
`sid` cookie 就是会话全部凭据（`sessions.py:317` 起 `resume()` 按 sid 取会话），脚本若拿到 sid 即可冒用。障碍有三：
- **CSRF 会被触发**：带上 sid 后条件 5 不成立，非 GET 请求必须同时带上该会话的 `X-Frappe-CSRF-Token`（`auth.py:89`），而 token 只在页面 HTML 内联 script 里（`www/desk.py:57` / `base_template_page.py:18-25`），脚本要么扒页面、要么让人从浏览器里抄出来；
- **cookie 取不到**：HttpOnly/浏览器隔离下外部进程拿不到 sid，得靠手工复制或浏览器扩展；
- **会话侧信息比对**：会话记录里存了 `session_ip` 与 `user_agent`（`sessions.py:261-264`）——**是否用于拒绝换 IP 复用，本次未查实**。
另有 `restrict_ip` 的说明见 `auth.py:647-652`（cookie 路径在 `Session.resume` 里校验）。

**推荐路径（落地）**：演示脚本用**专用 API 用户 + `Authorization: token key:secret`**，**不复用浏览器 cookie，不开 `ignore_csrf`**。要驱动界面就走结论④那层自有 whitelisted 方法，内部 `publish_realtime(event=..., user="<演示用户>")`。这条路无 CSRF、无 cookie 依赖、身份可审计（Sessions/API Request Log 都记 user）。

## ④ whitelisted 方法包一层触发 publish_realtime

**可行，无额外权限障碍**（读码所得 + 一处推断）：
- `/api/method/<app>.<module>.<fn>` 经 `frappe/api/__init__.py:23-62` 分发到白名单方法；自有 app 写 `@frappe.whitelist()` 的函数，函数体内 `frappe.publish_realtime(event="demo_step", message={...}, user="demo@x.com")` 即可。
- `publish_realtime` 内部无权限检查（依据同 B(i)），故不会因「目标 user 不是调用者」被拦。
- 白名单方法自身的门槛就是「调用者已认证且不是 Guest」（未加 `allow_guest=True` 时）——api key 认证已满足（`auth.py:743-744` 设了真实 user）。
- **推断**：该方法用 POST 调用时同样享受②的 CSRF 豁免（同一个 `validate_csrf_token`，不分路径）；用 GET 调用则本来就免。
- 若需即时送达，不要设 `after_commit=True`（`realtime.py:73-82` 会压到事务提交后才 flush）；默认 `False` 即直发 redis。

## ⑤ 拿不准 / 未实跑的

1. **全部结论均为静态读码，未实际发过一次 HTTP 请求**——尤其「api key 免 CSRF」建议用一次真实 POST 建单据实测确认（这是本项目硬教训所指的那类验证）。
2. 会话里的 `session_ip` / `user_agent`（`sessions.py:261-264`）是否参与 cookie 复用的拒绝判定 —— **未查实**。
3. socket.io 服务端（`frappe/socketio.js` 或 realtime 子模块）如何把 redis `events` 频道的消息投递到 `user:<user>` 房间、以及它对订阅端的鉴权（`get_socketio_secret` `realtime.py:124-139`、`get_user_info` `realtime.py:142` 有涉及）—— **本次未展开**，属「realtime 侧已查明」的范围。
4. `/api/v1` 与 `/api/v2` 在 CSRF 或认证上是否有差异 —— 只读了 `api/__init__.py` 的分发，`api/v1.py` / `api/v2.py` **未逐行核对**；按校验点唯一（`auth.py:81`）推断无差异。
5. Frappe 是否对 api key 请求另设速率限制 / IP 白名单（`auth.py:651-652` 的 `validate_ip_address` 会对 key 认证生效）—— 若演示用户设了 `restrict_ip`，脚本所在机器 IP 需在其中，**未实测**。
