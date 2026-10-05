# P1-S5 开发方案 · Part4：局域网连通、组网就绪、重建演练、全量回归与收尾

**来源需求**：[B 需求文档](../R02-需求文档/P1-S5-R2-B需求文档.md) §4.8、§4.3 演示站第 4 条、AC-004／008／010（需求 TS-012）＋[C 讨论记录](P1-S5-R3-C讨论记录.md) DEC-021／022｜**前置依赖**：Part3 全部任务｜**日期**：2026-10-05｜**编写者**：Claude（Opus 5.5）
**总纲**：[P1-S5-R3-C开发方案-总纲.md](P1-S5-R3-C开发方案-总纲.md)（执行纪律见总纲 §九，本 Part 不重复）

## 接口契约

### 1. 实时通道连通检查（总纲 A10）

```python
# frappe_china/realtime_check.py
EVENT: Final = "frappe_china_realtime_check"      # 只供本检查；不复用 erx_demo_step（ADR-0008）
_KEY: Final = "frappe_china:realtime_check:{token}"

def run(user: str = "Administrator", timeout: int = 30) -> dict:
    """bench execute 入口。生成随机 token，缓存写 {status: "pending", user}（过期 timeout+60 秒），
    publish_realtime(EVENT, {"token", "sent_at"}, user=user)（不用 after_commit：bench execute 内要立即发出），
    每 0.5 秒查一次缓存，timeout 内变为 "acked" → {"ok": True, "token", "latency_ms", "acked_by", "client"}；
    超时 → {"ok": False, "token", "reason": "timeout: 页面未在 N 秒内回执——实时通道不通、或目标用户没有打开的桌面页"}。
    结果同时 print 一行「通过／失败」，便于人读。"""

@frappe.whitelist(methods=["POST"])
def ack(token: str) -> dict:
    """页面收到事件后经页面通路回执。token 不存在或已过期 → 抛 frappe.ValidationError；
    当前会话用户 != 缓存里的 user → 抛 frappe.PermissionError；成功则写 {status: "acked", acked_by, client: request.host}。"""
```

```javascript
// frappe_china/public/js/realtime_check.js   —— hooks.app_include_js 引入（不经构建，HT-010）
$(document).on("startup", () => {
    frappe.realtime.on("frappe_china_realtime_check", (msg) => {
        frappe.show_alert({ message: __("Realtime check received: {0}", [msg.token]), indicator: "green" }, 10);
        frappe.call({ method: "frappe_china.realtime_check.ack", args: { token: msg.token } });
    });
});
```

`frappe_china/translations/zh.csv` 加一行：`Realtime check received: {0}` → `实时通道检查已收到：{0}`。

### 2. 实时端口前的转发层（总纲 A9）

```text
docker/compose.yaml
  frappe:          ports 去掉实时端口那一行；监视端口改为只绑本机 "127.0.0.1:${WATCH_PORT:-6787}:6787"
  realtime-proxy:  image docker.io/nginx:1.30.5-alpine（锁版本）
                   ports "${SOCKETIO_PORT:-9100}:9100"
                   environment SITE_NAME=${SITE_NAME:-erx.localhost}
                   volumes ./realtime-proxy:/etc/nginx/templates:ro
                   depends_on frappe；restart unless-stopped
docker/realtime-proxy/default.conf.template     —— 官方镜像启动时以 envsubst 渲染（只替换已定义的环境变量，nginx 自己的 $变量 保留）
```

```nginx
# 来源是本机名时原样透传（实时服务对 localhost/127.0.0.1 取默认站点，*.localhost 即站点本名），
# 其余来源（局域网地址、组网地址）补站点名请求头——实时服务认站点时优先认它（authenticate.js:89-104）。
# 值为空串时 nginx 不发该请求头。
map $http_origin $frappe_site_header {
    default                                                        "${SITE_NAME}";
    ""                                                             "";
    "~^https?://(localhost|127\.0\.0\.1|[^/:]+\.localhost)(:\d+)?$" "";
}
map $http_upgrade $connection_upgrade { default upgrade; "" close; }
server {
    listen 9100;
    location / {
        proxy_pass http://frappe:9100;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;
        proxy_set_header Host $http_host;                     # 实时服务要比对 Host 与 Origin 的主机名（authenticate.js:21）
        proxy_set_header X-Frappe-Site-Name $frappe_site_header;
        proxy_read_timeout 1h;
    }
}
```

容器内实时服务仍监听 9100（站点配置 `socketio_port`），浏览器仍按 `socketio_port` 拼连接地址——两侧同号的约束不变，只是宿主侧那一端由转发层接管。

## 切片划分与验收

| 切片 | 功能点 | 验收条件 |
|---|---|---|
| **SL-008** 局域网异地终端连通 | 需求 TS-012；DEC-017；LG-007；RS-003／008；AC-004（局域网） | ① 本机浏览器以 `http://localhost:8000` 打开桌面页，`run()` 报通过（转发层上线前、后各一次——本机方式不受影响）。② **LG-007 实测**：转发层上线**前**，局域网异地终端以 `http://<本机局域网地址>:8000` 登录、打开一张单据（页面正常），`run()` 报**失败**；终端浏览器控制台可见实时连接被拒（`Invalid namespace`）。③ 转发层上线后，同一终端打开一张单据，`run()` 报通过，终端界面弹出「实时通道检查已收到」提示。④ **反证**：`docker compose stop realtime-proxy` 后同一终端、同一操作，`run()` 报失败；`start` 后再报通过。⑤ `ack` 的异常路径：过期 token 报错；用户不符报无权限（单测）。⑥ 监视端口只绑本机：从局域网终端访问 `http://<局域网地址>:6787` 连不上；本机 `http://localhost:6787` 仍可用（另起测试站服务的既有做法不受影响） |
| **SL-009** 组网就绪 | DEC-021／022；LG-008／013 | ① `docker/README.md` 有「异地终端访问」一节：局域网用法；组网用法（两端装客户端、加入同一网络、终端用组网地址访问）；连通检查工具用法；**外网实测前的准备清单**（见 TS-014）。② 延迟需求 `SH-P1S5005` 已登记于 Stage 概况。③ 转发层的规则不依赖具体地址（组网地址与局域网地址走同一分支）；`run()` 不依赖终端地址（只认用户）——静态核对配置与代码 |
| **SL-010** 重建演练与收尾 | AC-008／010；需求 TS-001～003 的端到端；总纲 §一 完成标准 | ① 在另一个 bench 目录按 `apps.json` 从空重建成功：七个 app 的 HEAD 与 `apps.json` 一致（Insights 为 `5447f162`）；站点 `installed_apps` 为目标顺序；`check_app_order()["ok"]` 为真。② 预检命令对不存在的 tag 返回非零、对 `v3.14.2` 返回零。③ 主 bench 跑 `lock-apps.sh --show` 与写入后，`git diff docker/apps.json` 为空。④ `frappe_china` 全量测试全过，收集条数 ≥ 160 且回执分报通过与跳过条数。⑤ 演示站：`check_app_order()["ok"]` 为真；业务数据为 0（同 SL-004 ⑥）；无 `_FCT` 前缀记录；新空账基准点备份另存于 `docker/backups/保留-S5装App后/`，`20261004_005331` 仍在根目录。⑥ 常驻文件按实况回写（TS-016 第 5 步清单） |

**执行每个切片前，对照该切片验收条件检查方案覆盖性——如发现按方案写出的代码无法通过验收条件，暂停反馈，不硬写。**

## 任务清单

| 任务 | 对应切片 | 可并行否 |
|---|---|---|
| TS-013 连通检查工具、转发层、局域网实测 | SL-008 | 否 |
| TS-014 组网就绪文档与延迟需求 | SL-009 | 否 |
| TS-015 空目录重建演练 | SL-010 | 否 |
| TS-016 全量回归、新基准点、常驻文件回写 | SL-010 | 否（最后一个任务） |

---

## 任务 TS-013：连通检查工具、转发层、局域网实测（对应 SL-008）

### 目标
完成标志④（DEC-022 改写后的局域网部分）：异地终端页面与实时通道都通，检查分得清通与不通。

### 具体改动

1. **检查工具**：按接口契约 §1 写 `frappe_china/realtime_check.py`、`public/js/realtime_check.js`；`hooks.py` 加 `app_include_js = ["/assets/frappe_china/js/realtime_check.js"]`；`zh.csv` 加一行。单测 `tests/test_realtime_check.py`：`ack` 对不存在的 token 抛 `ValidationError`、对别的用户抛 `PermissionError`、对正确用户把状态置 `acked`；`run()` 在 `patch("frappe.publish_realtime")` 下、由测试在另一线程里调 `ack` 时返回 `ok`，不调时 `timeout=1` 返回 `ok=False`。
2. **本机基线**（SL-008 ①前半）：清缓存、浏览器硬刷新桌面页，确认 `realtime_check.js` 已加载（开发者工具网络面板）；`bench --site erx.localhost execute frappe_china.realtime_check.run --kwargs "{'user': 'Administrator'}"` → 通过。
3. **LG-007 实测**（SL-008 ②，转发层上线前）：请用户在同一局域网的另一台设备上打开 `http://<本机局域网地址>:8000`（地址由执行者在宿主 `ipconfig` 查出告诉用户）、以 Administrator 登录、打开任意一张单据并保持页面打开。执行者跑 `run()`：
   - 报**失败** → LG-007 成立，继续第 4 步；
   - 报**通过** → LG-007 不成立：**暂停反馈**（转发层可能不必要，交用户定是否仍上线）；
   - 终端连页面都打不开 → 多半是 Windows 防火墙拦了入站（HT-016）：**暂停反馈**，由用户决定是否为 8000 与实时端口加入站规则（属本机安全设置，不由执行者自行改）。
4. **转发层上线**：按接口契约 §2 改 `docker/compose.yaml`（注释写明原因：S5 LG-007、需求 §4.8；原「两侧同号直通」那段注释改写为「宿主侧由转发层接管、容器内仍 9100」）、新建 `docker/realtime-proxy/default.conf.template`；`docker/save-images.sh` 的 `IMAGES` 加 `nginx:1.30.5-alpine`；`docker/README.md`「端口」节同步。然后：
   ```text
   docker/up.sh            # compose 变更会重建 frappe 容器（端口映射变了）；setup.sh 各段幂等，第 6.5 段会重装中文字体
   docker/start.sh         # 重新拉起 bench start
   ```
   **跑 `up.sh` 前**确认：TS-007 已做完（演示站已装四个 App，第 6 段只会报「已安装」）。镜像拉不下来（网络）即暂停反馈。
5. **复测**：本机（SL-008 ①后半）→ 通过；局域网终端刷新页面后（SL-008 ③）→ 通过，并请用户确认终端界面弹出了提示。
6. **反证**（SL-008 ④）：`docker compose stop realtime-proxy` → 终端页面保持打开 → `run()` 报失败；`docker compose start realtime-proxy` → 终端页面重连（必要时刷新）→ `run()` 报通过。
7. **监视端口**（SL-008 ⑥）：请用户在终端浏览器打开 `http://<局域网地址>:6787` → 连不上；本机 `http://localhost:6787`（按项目概况的做法另起测试站服务时）可用。

### 验证方式
第 2、3、5、6 步每次 `run()` 的输出原样贴进回执；第 3、5 步附终端截图（存 `Spike/P1-S5-R4-TS013-*.png`）。全程不改上游源码（需求 §4.8 第 4 条）：`git -C frappe-bench/apps/frappe status --short` 为空。

## 任务 TS-014：组网就绪文档与延迟需求（对应 SL-009）

### 目标
外网一段交付到「理论上就绪」：到时只做实测、不再设计（DEC-022）。

### 具体改动

1. **`docker/README.md` 新增「异地终端访问」一节**，含四段：
   - **局域网**：终端访问 `http://<本机局域网地址>:8000`；转发层的作用一句话；查本机地址的命令。
   - **组网（外网）**：本机与终端各装组网客户端、登录同一网络；终端访问 `http://<本机组网地址>:8000`；转发层规则对组网地址同样生效、无需改配置。
   - **连通检查**：`bench --site <站点> execute frappe_china.realtime_check.run --kwargs "{'user': '<终端登录的用户>'}"`；通过与失败的含义；失败时先查「终端是否打开了桌面页」。
   - **外网实测前的准备清单**（B 文档 AC-009 与 LG-008 的内容，按顺序）：① 改管理员口令为非缺省值（`bench --site <站点> set-admin-password`，新口令只记在 `docker/.env` 的 `ADMIN_PASSWORD`，不进 git）；② 确认只有页面与实时两个端口对组网可达——从终端探测 `8000`、`9100` 通，`6787`、`3306`、`6379` 不通；③ 组网客户端只在演示时段开；④ 若终端页面能开而 `run()` 失败，按下面「已知待验点」逐条查。
   - **已知待验点**（LG-013）：国内能否稳定连上；容器能否以组网地址回访本机页面端口——实时服务鉴权时按来源地址回访页面端口（`realtime/utils.js`），不可达时的备用做法：终端改用组网提供的本机主机名访问，并在 `compose.yaml` 的 `frappe` 服务加 `extra_hosts: ["<该主机名>:host-gateway"]` 让容器把它解析到宿主；Windows 防火墙是否对组网网卡放行两个端口。
2. **Stage 概况延迟需求登记册**加一行（若 C 步收尾时尚未登记）：`SH-P1S5005`｜组网（外网）环境下按 DEC-017 三条实测演示终端连通性，含准备清单①②｜用户（DEC-022）｜2026-10-05｜S7 或 S8G 收口后｜P1-S5-R3 C 讨论记录第 2 步｜延期。

### 验证方式
SL-009 ①～③：README 一节存在且四段齐；登记册有该行；`default.conf.template` 的 `map` 不含任何具体 IP。

## 任务 TS-015：空目录重建演练（对应 SL-010）

### 目标
AC-008：新机器按 `apps.json` 重建得到同一个站（需求 §4.2.1 五条的端到端验证，RS-004）。

### 具体改动（操作步骤）

1. `.git/info/exclude` 加一行 `frappe-bench-drill/`（开发守则「自己要排除的文件写进 .git/info/exclude」）。
2. 在容器内以另一套 bench 目录与站点名跑重建脚本（数据库与缓存共用现有容器，新站点建新库，不碰两个现有站点）：
   ```bash
   docker compose exec -T -w /workspace \
     -e BENCH_NAME=frappe-bench-drill -e SITE_NAME=drill.localhost \
     -e DB_ROOT_PASSWORD=<.env 的值> -e ADMIN_PASSWORD=<任意> -e GIT_PROXY=<.env 的值> \
     -e HOST_GIT_AUTOCRLF=<同 up.sh 取法> \
     frappe bash /workspace/docker/scripts/setup.sh
   ```
   （在宿主 Git Bash 下执行时先 `export MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*'`。）
3. 核 SL-010 ①：七个 app 的 `git rev-parse HEAD` 对 `apps.json`；`bench --site drill.localhost execute frappe_china.install.check_app_order` 的 `order_ok`、`overrides_ok`、`translation_ok` 为真（无公司，`company_checks_ok` 按设计为真）；官方 App 的 remote 只有只读 `upstream`。
4. 核 SL-010 ②：在宿主跑 `git ls-remote --exit-code --heads --tags https://github.com/frappe/insights.git refs/heads/v3.14.999 refs/tags/v3.14.999`（退出码非零）与同一命令换成 `v3.14.2`（退出码零）——这正是 `setup.sh` 第 3 段的预检命令。
5. 核 SL-010 ③：主 bench（非演练目录）跑 `docker/lock-apps.sh --show`、`docker/lock-apps.sh`，`git diff docker/apps.json` 为空。
6. 清理：`bench drop-site drill.localhost --db-root-password <值> --no-backup`；演练目录 `frappe-bench-drill/` **列出大小后报用户、获准再删**（递归删除，总纲 §九第 4 条的精神）；`.git/info/exclude` 那一行随目录删除后去掉。

### 验证方式
第 3～5 步输出写进回执。重建失败时贴失败段的输出，按失败性质暂停反馈或回 Part1 修脚本（修后从第 2 步重跑）。

## 任务 TS-016：全量回归、新空账基准点、常驻文件回写（对应 SL-010）

### 目标
确认全部改动无回归、演示站处于可交 S6／S7 的干净状态，并把实况写回常驻文件。

### 具体改动（操作步骤）

1. **全量回归**：`bench --site test.localhost run-tests --app frappe_china`，全部通过；回执写收集条数、通过、跳过各几条，与 S4 收口的 160 条对比。
2. **演示站复核**：`check_app_order()["ok"]` 为真；SL-004 ⑥ 的计数为 0；`_FCT` 前缀查无记录；`Raven Settings` 与 bot 存在（配置保留，属基准点的一部分）。
3. **新空账基准点**（总纲 A12）：`docker/backup.sh`；新出的 4 个文件另存到 `docker/backups/保留-S5装App后/`；核 `20261004_005331` 那 4 个文件仍在根目录。
4. **自查方案外改动**：`git status --short`（主仓库）与 `git -C frappe-bench/apps/frappe_china status --short` 的文件清单，逐个对上本方案的任务；四个官方 App 与 frappe、erpnext 目录 `status` 为空。
5. **常驻文件回写**（先载入 `docs/流程体系/常驻文件契约.md`，按其判据定写哪个文件）：
   - `docs/项目概况.md`：技术栈与模块结构表（四个 App 的来源与锁定方式、`frappe_china` 新增的 `hr.py`／`realtime_check.py`／`ai/`）；「已知限制」里「hrms app 未安装」一条改写；「开发环境」节的演示站当前状态与备份基准点（新增 `保留-S5装App后/`）；端口一条（转发层）。
   - `docs/开发守则.md`：本 Stage 新约定（D 回执「新增约定」节汇总；至少含 Stage 概况长效信息 #1 两条与 Part1 TS-005 的可选依赖写法）。
   - Stage 概况长效信息 #2～#4 的去向按长效信息表判，交 S6／S7 的写进路线文档对应 Stage 的「本议题执行所需的清单」。

### 验证方式
SL-010 ④～⑥ 逐条；常驻文件改动在回执「改动清单」里逐文件列出。
