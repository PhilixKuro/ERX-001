# P1-S2-R2 调研报告：realtime 能否驱动界面（接入机制之一）

**调查者**：Claude（主 Session 亲自查证）
**日期**：2026-09-23
**源码**：`frappe-bench/apps/frappe`（Frappe Framework 16.34.0）

> **⚠ 产出方式**：本块原派出子 Agent 三次、均在"写报告"这一步中断（全批七个 Agent 里五个同型失败：调查完成、报告未落盘）。第五次同型失败后判定不再派 Agent，**由主 Session 亲自查证**。故本报告全部结论为直接读码所得。
> **范围**：只覆盖「realtime 能否驱动界面」这一问。API v2、认证与 CSRF、hook 合并顺序三块**本次未查**，见 §5。

---

## 一、结论先行（六档判定）

**服务端 publish 一个事件，能让已打开的 desk 页面做到哪一档**：

| 档 | 能力 | 现成机制 | 依据 |
|---|---|---|---|
| (a) | **弹提示消息** | **✅ 开箱即用** | `socketio_client.js:76-77` 内置 `socket.on("msgprint", msg => frappe.msgprint(msg))` |
| (b) | **刷新当前列表/表单数据** | **✅ 开箱即用** | 列表：`list_view.js:1757` 的 `list_update` → `debounced_refresh()`；表单：`model.js:154` 的 `doc_update` → `cur_frm.debounced_reload_doc()` |
| (c) | **跳转路由** | **⚠ 仅一种窄情形内置** | `form.js:339-344` 的 `doc_rename` 会 `frappe.set_route("Form", doctype, data.new)`，**但只在"当前表单被后台改名"时触发**。**无通用的"跳到 X"事件** |
| (d) | **打开指定单据** | **❌ 无内置** | 15 个订阅点中无一个做此事 |
| (e) | **往表单字段填值** | **❌ 无内置** | 同上 |
| (f) | **点按钮 / 触发动作** | **❌ 无内置** | 同上 |

**故现成机制到 (b) 为止**，(c) 只在改名这一种窄情形下存在。

### ⭐ 但有一条关键的使能事实：`realtime.on` 接受任意事件名

`socketio_client.js:12-17` 实读：

```js
on(event, callback) {
    if (this.socket) {
        this.connect();
        this.socket.on(event, callback);
    }
}
```

**它只是 socket.io 原生 `socket.on` 的薄包装，对事件名无白名单、无校验。** 服务端 `publish_realtime(event=...)` 的 `event` 也是自由字符串（`realtime.py:23-41`，`event: str | None`）。

**故 (d)(e)(f) 三档不是"框架不支持"，而是"框架没预置这个用途的处理器"** —— 自己注册一个自定义事件的监听器即可，不必改 frappe 源码。

**这一条把选项甲的性质从"要改框架"降为"要写一段监听"。**

---

## 二、15 个内置订阅点全清单

`grep -rn "realtime\.on(" --include=*.js frappe/public/js/` 实测 **15 处**：

| 事件名 | 位置 | 收到后做什么 |
|---|---|---|
| `doc_update` | `model.js:154` | 当前表单未脏 → `debounced_reload_doc()`；已脏 → 标 `__needs_refresh` 并 `show_conflict_message()` |
| `list_update` | `list_view.js:1757` | 过滤 doctype、跳过勾选态与 `avoid_realtime_update()`，然后 `debounced_refresh()` |
| `list_update` | `report_view.js:72` | `this.on_update(data)` |
| `list_update` | `toolbar.js:156` | （工具栏内） |
| **`doc_rename`** | **`form.js:339-344`** | **`frappe.set_route("Form", doctype, data.new)` —— 唯一的内置路由跳转** |
| `docinfo_update` | `form.js:2166` | 按 `{doc, key, action}` 更新 docinfo |
| `doc_viewers` | `form_viewers.js:49` | 更新"谁在看这张单"的头像 |
| `version-update` | `desk.js:169` | 提示有新版本 |
| `update_user_permissions` | `desk.js:316` | debounce 500ms 后 `update_user_permissions()` |
| `notification` | `notifications.js:442` | 刷新通知 |
| `indicator_hide` | `notifications.js:449` | 隐藏指示点 |
| `report_generated` | `query_report.js:115` | 报表生成完毕后取结果 |
| `build_event` | `build_events.bundle.js:9` | 开发模式的构建提示 |
| `task_complete:{id}` | `bulk_operations.js:129` | 批量操作完成 |
| （图表） | `chart.js:21` | 按 `socketEvent` 刷新图表 |

另有 `socketio_client.js` 里**不经 `realtime.on` 的直接订阅**：`msgprint`（`:76`）、`progress`（`:80`）、`task_status_change`（`:181`）、`task_progress`（`:184`）、`connect_error`（`:72`）。

**全部 20 个订阅点的共性：都是"刷新数据"或"提示消息"，没有一个是"执行操作"。** 这与 (d)(e)(f) 无内置的判定一致——**数据层（事件抵达）与渲染层（处理器实现）两层都查过**，不是靠间接推断。

---

## 三、推送侧的定向能力（对演示脚本很关键）

`publish_realtime` 签名实读（`realtime.py:23-41`）：

| 参数 | 语义 |
|---|---|
| `event` | 事件名，**自由字符串** |
| `message` | JSON 消息体 |
| `room` | 推到哪个房间，**默认整站** |
| **`user`** | **推给指定用户** —— 演示脚本需要的正是这个 |
| `doctype` + `docname` | 推给某张单据的订阅者 |
| `task_id` | 异步任务用 |
| `after_commit` | 默认 `False`；为 `True` 则当前事务提交后才发 |

**故演示脚本可以精确推给"正在演示的那个浏览器会话所属用户"**，不会惊动其它人。**`after_commit=True` 对演示尤其重要**——否则可能事件先到、数据后落库，界面刷新时取到旧数据。

---

## 四、可靠性：realtime 断连是静默的

本项目已知坑（S1 全程实操都在 realtime 死掉的环境下做的，后来才发现）：站点 `socketio_port` 必须与 compose 端口映射同号（现用 9100，因 9000 落在 Windows 保留段）。

**对选项甲的意味**：

| 项 | 判断 |
|---|---|
| 断连时的症状 | **不报错**。`socketio_client.js:72` 有 `connect_error` 处理器，但**断连后界面只是不再自动更新** |
| **演示现场若断了，客户会看到什么** | **脚本在跑、界面不动。** 且因为没有报错，**演示者当场分不清是"脚本没跑"还是"realtime 断了"** —— 这是选项甲最大的现场风险 |
| 演示前能否自检 | **能**。本项目已有两标签页验法（一个标签改数据、另一个标签看是否自动更新）。**应做成演示前的必检项** |

**⚠ 故选项甲必须配一条"心跳自检"**：演示开始前推一个事件、前端收到后回显，确认链路通了再开始。否则风险是"演示到一半发现界面从头就没动过"。

---

## 五、甲乙两选项的重新评估

**R1 摆出的两个选项**：甲＝服务端推事件驱动（宣称代价约百行前端监听，好处是 MCP 与 React 可复用）；乙＝浏览器侧驱动（略简单，但控制权在 desk 内，复用不到驱动界面那部分）。

### 甲还成立吗：**成立，且代价估计基本准确**

| 项 | 基于源码的重新判断 |
|---|---|
| 要不要改 frappe 源码 | **不要**。`realtime.on` 对事件名无白名单（§1），自定义事件可直接注册 |
| 监听代码写在哪 | **自有 app 的 `app_include_js`** —— 与 Flow 的做法同型（Flow 就是靠 `app_include_js` 注入一个 desk 覆盖面板） |
| **要写多少** | **"约百行"这个估计基本准确**，但要分档看：<br>• 只做 (c) 跳转 + (d) 开单据：**很少**，`frappe.set_route()` 一个调用就够，约 20-30 行含事件分发；<br>• 加 (e) 填字段：还要 `cur_frm.set_value()`，约 +20 行；<br>• 加 (f) 点按钮：**最麻烦**，要么调 `cur_frm.save()`/`cur_frm.savesubmit()` 这类 API（可行），要么模拟点击 DOM（脆）。走 API 则约 +30 行 |
| 复用性 | **MCP 与 React 确实能复用推送侧**（`publish_realtime` 与事件协议），但**前端监听那部分 React 要重写一遍**——因为那段代码是针对 desk 的 `cur_frm`/`frappe.set_route` 写的，React 前端有自己的路由与表单状态 |

**⚠ 故"MCP 与 React 都能复用"这个说法要收窄**：复用的是**事件协议与推送侧**，不是前端监听代码。R1 的表述略宽。

### 一条本次查出的第三条路

**(f) 点按钮那一档不必真的"点"。** `cur_frm` 暴露了 `save()` / `savesubmit()` 等方法，故"提交单据"可以是**监听器直接调 API**，而非模拟 DOM 点击。这使甲的脆性大幅降低——**演示脚本驱动的是表单对象的方法，不是像素位置**。

但这也意味着一件事要跟用户说清：**这样客户看到的是"界面自己完成了操作"，而不是"鼠标自己在动"。** 若用户期待的是后者（光标移动、按钮高亮），那要另外做，且脆性高得多。

### 乙的重新评估

乙（浏览器侧驱动）**在"可从任一节点起跑"这个硬要求上有短板**：浏览器侧脚本要靠某种方式被注入并保持状态，而演示要从任意节点起跑就意味着要能"跳到第 7 步的状态"——这需要服务端先把数据造到那个状态。**故乙实际上仍需要一个服务端造数据的部分**，它并不比甲少一半工作。

**判断**：**甲更优，且差距比 R1 估计的更大** —— 因为乙省下的只是那 20-30 行监听，却失去了推送侧的复用性。

---

## 六、未查实的（本次范围外，须补）

**本报告只覆盖 realtime 一问。** 原计划的六问里，以下**本次完全未查**：

1. **REST API v2 的实际路径与形态** —— `/api/v2/document/...` vs `/api/resource/...`、v1 与 v2 的能力差异、白名单规则。
2. **"建一张销售订单并提交"的最小 API 调用序列** —— 含 `sales_order.json` 里哪些字段是 `reqd: 1`。
3. **认证与 CSRF** —— cookie session / api_key / OAuth2 各自实现位置；**用 api key 时是否豁免 CSRF**；**外部脚本能否影响一个已在浏览器里打开的 desk 会话**（这一条与演示脚本直接相关，是重要缺口）。
4. **SPA 挂载链路的框架侧实现** —— `website_route_rules` 在框架哪里被读取、`www/` 的 renderer 优先级、`/assets/{app}/` 由谁服务。（**但"挂载机制与前端框架无关"这个结论已由四个 app 样本支持**，见官方三 App 报告第十一节。）
5. **⭐ `frappe.get_hooks()` 的合并顺序** —— **装新 app 会不会把自有 app 挤出 `regional_overrides` 的 `[-1]` 末位**。这一条是本项目的具体风险，**优先级最高的未查项**。
   - **但已有一条间接缓解证据**（官方三 App 报告第五节）：六个候选 app 里**只有 hrms 有 `regional_overrides`，且只注册 `India` 键下 3 个函数**，而 `erpnext/__init__.py:145-152` 是先按区域取 dict、再对同名 function_path 取 `[-1]`，**区域键与函数路径两层都不相交** → 就这六个 app 而言不争末位。**但"合并顺序由什么决定"这个机制本身仍未查清**，故无法排除将来装别的 app 时的风险。
6. **多 app 并存时 `doc_events` / `override_whitelisted_methods` / `override_doctype_class` 的冲突规则**（累加还是后者胜出）。
7. **本报告全部结论均为静态读码，无一条实跑。** 六档判定尤其应实测验证——尤其 (f) 档调 `cur_frm.savesubmit()` 是否真能成功提交。
