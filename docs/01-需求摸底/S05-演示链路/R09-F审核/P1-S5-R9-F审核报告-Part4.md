# F 审核分片报告 · 片 4（对象：方案 Part4 SL-008～010／TS-013～016 的落地 / 审核标准：B 需求文档 §4.8、AC-004／008～010）

**轮次**：P1-S5-R9｜**步骤**：F 分片 4｜**日期**：2026-10-07｜**执行者**：Claude 子 Agent（只读）
**依据**：[开发方案 Part4](../R03-开发方案/P1-S5-R3-C开发方案-Part4.md)（要求层，全文逐条）、[总纲](../R03-开发方案/P1-S5-R3-C开发方案-总纲.md)（A9、A10、A12、HT-008／012／016、§一完成标准、§九）、[B 需求文档](../R02-需求文档/P1-S5-R2-B需求文档.md) §4.3 演示站、§4.8、§4.9、§八（意图层）、[C 讨论记录](../R03-开发方案/P1-S5-R3-C讨论记录.md) DEC-021／022、LG-013、`docs/开发守则.md`、`docs/业务规则.md`
**被审范围**：主仓库 `c372a94..2fb2641` 的 `docker/compose.yaml`（`frappe` 端口段与 `realtime-proxy` 服务）、`docker/realtime-proxy/default.conf.template`、`docker/save-images.sh`、`docker/README.md`「端口」「异地终端访问」「私有仓库」「结构」节、`docker/.env.example` 端口段；`frappe_china`（`03fde72..4b21aae`）的 `realtime_check.py`、`public/js/realtime_check.js`、`hooks.py:30`、`translations/zh.csv:152`、`tests/test_realtime_check.py`；`docs/项目概况.md`「开发环境」「能力」「已知限制」中与本片相关的句子；Stage 概况延迟需求登记册 SH-P1S5005／007／008

## 覆盖自证

**读全的依据**：F Spec、`bricks/audit.md`、`bricks/sharding.md`、流程规范 §2.2／§2.3、开发守则、业务规则、总纲、Part4、D 回执 Part4、SB 修复回执（全文，重点 IT-024、IT-026 两行与「偏离与暂停」节）、Stage 概况（含登记册 SH-P1S5001～008）、需求文档 §4.3、§4.8～§4.11、§八、§十 LG-001／002；C 讨论记录第 1～2 步与两张汇总表。R5 E 报告只读了片 4 那一行、TS-013～016 四行、IT-020～026 细节与当场修清单第 8～14 行；R8 E 报告只读了 IT-024、IT-026 两行。两份 E 报告只当「已核过什么」的索引，结论都自己重核。同目录 Part1 报告只用来对齐节结构。

**逐行读的代码**：`realtime_check.py` 全文（88 行）；`realtime_check.js` 全文（6 行）；`test_realtime_check.py` 全文（74 行，6 例）；`hooks.py` 的 S5 diff；`zh.csv` 的 S5 diff；`compose.yaml` 全文；`default.conf.template` 全文；容器内渲染后的 `/etc/nginx/conf.d/default.conf` 全文（与模板逐行一致，`${SITE_NAME}` 已渲染为 `erx.localhost`，`$http_origin` 等 nginx 变量保留）；`save-images.sh` 全文；`docker/README.md` 全文（416 行）；`.env.example:1-14`；`setup.sh:92-108` 与对 `socketio`／`9100` 的全文 grep；`up.sh:30-46`；`项目概况.md:40-110`、`:136-163`；两仓 S5 区间 diff 中属于本片的文件（compose、save-images、README、.env.example、hooks、zh.csv、README）；IT-024 的留证脚本 `.mjs` 关键段与 `.log` 全文、`frappe-bench/logs/s5-r8-it024.log` 末段、`s5-sb-final-regression.log` 末段。

**对照的上游**（只读）：frappe `realtime/middlewares/authenticate.js` 全文（`:17-24` 命名空间与来源两项校验、`:89-105` `get_site_name` 的认站点顺序）、`realtime/utils.js` 全文（开发模式下按 `Origin` 的主机名＋`webserver_port` 回访）、`realtime/index.js:1-97`（`listen(conf.socketio_port)`）、`frappe/boot.py:163-168`（`socketio_port` 进 `frappe.boot`）、`socketio_client.js:40-131`（`reconnectionAttempts: 3`、`get_host` 取 `window.location` 主机名＋`frappe.boot.socketio_port`）、`frappe/realtime.py:23-110`（`publish_realtime` 默认 `after_commit=False`、`user` → user room）、`frappe/utils/redis_wrapper.py:64-100`（`set_value` 写 `frappe.local.cache`、`get_value` 先读本地副本）、`frappe/commands/utils.py:266-303`（`execute` 以 `eval` 解析 `--kwargs`）；容器内 bench 5.31.0 `config/common_site_config.py:83-135`（`make_ports`：`socketio_port` 缺省 9000，同级目录有别的 bench 时取最大值＋1）、`bench.py:402-408`；CRM 前端 `crm/frontend/src/socket.js:5-12`（只为判断 `/crm` 也走 9100）。

**只读查询与实测**：
- `docker ps`：`realtime-proxy` 镜像 `nginx:1.30.5-alpine`、发布 `0.0.0.0:9100`；`frappe` 发布 `0.0.0.0:8000` 与 `127.0.0.1:6787`；`nginx -v` 为 1.30.5。
- 宿主 `netstat -ano`：LISTENING 有 `0.0.0.0:8000`、`0.0.0.0:9100`、`127.0.0.1:6787`，另有本项目 compose 之外的 `0.0.0.0:7999`（LiteLLM）、`0.0.0.0:5432`（LiteLLM 的 postgres）。
- 宿主经局域网地址（`ipconfig` 取 `192.168.3.50`）探测：`:8000/api/method/ping` 200；`:9100/socket.io/?EIO=4&transport=polling` 200；`:6787` 连接被拒（curl rc=7）；`127.0.0.1:6787` 能连上、空响应（rc=52，平时无人监听，符合预期）。
- 容器内：`common_site_config.json` 的 `socketio_port=9100`、`webserver_port=8000`、`default_site=erx.localhost`；两站 `developer_mode=1`；`netstat` 见 node 在 `:::9100`、python 在 `0.0.0.0:8000`。容器经宿主局域网地址回访 `192.168.3.50:8000/api/method/ping` 得 200（HT-008 中「实时服务回访页面端口」那一段在局域网成立）。
- **socket.io 握手探针**（只做 Engine.IO 轮询握手与命名空间连接，不带 cookie，不登录、不写库）：
  - 直连容器 9100（绕过转发层），`Host: 192.168.3.50:9100`、`Origin: http://192.168.3.50:8000` → `Invalid namespace`。**这在协议层复现了 LG-007**。
  - 经转发层，同样的局域网来源 → 过了命名空间与来源两项校验，停在 `Missing cookie…`（下一步鉴权，未带 cookie，符合预期）。
  - 经转发层，`localhost`、`erx.localhost` 来源 → 同样停在 `Missing cookie…`；直连容器、`localhost` 来源 → 同样。本机方式不受影响。
  - 经转发层，`Host` 为局域网地址、`Origin` 为 `other.localhost` → `Invalid namespace` 与 `Invalid origin`（`*.localhost` 分支不补头、上游按 Origin 认站点，预期如此）。
  - 客户端自带 `X-Frappe-Site-Name: test.localhost`：经转发层，`localhost` 来源与局域网来源都仍连到 `erx.localhost`。转发层总会覆盖或清掉客户端自带的这个头。
- 演示站只读 SQL：`installed_apps` 库值与 `site_config.json` 镜像都是 `frappe, erpnext, crm, hrms, insights, raven, frappe_china`；公司只有 `华东弹簧有限公司`，科目 266；`_FCT` 前缀公司 0；GL 0；`Raven Bot` 1。
- 备份目录：根目录 `20261004_005331` 4 个文件在；`20261007_011313` 是根目录最新一套；`保留-S5装App后/` 有 `20261007_011313` 的 4 个文件，`保留-S5装App前/` 有 `20261007_003913` 的 4 个文件。
- `git -C frappe-bench/apps/frappe status --short` 为空（上游未改）；`frappe_china` HEAD 为 `4b21aae`；本片五个文件对 HEAD 无差异。

**跳过的及原因**：
- **`run-tests` 未跑**（任务禁止）。Spec 的「验证门亲自实跑」本片做不到。用例是否通过只能读码判断；全量 205 条只读了日志末尾（`Ran 205 … OK`、`EXIT=0`，日志里没有 `skipped` 字样）。
- **没跑 `realtime_check.run()`、没开浏览器**：`run()` 会写 Redis，属写操作。本机基线只读 IT-024 和 R8 的留证日志。
- **没停或重启 `realtime-proxy`**（任务禁止），所以反证 ④ 只能读日志，nginx 在上游换 IP 后会怎样（P4-06）也没实测。
- **SL-008 ②③④⑥ 的终端侧、TS-015 重建演练**：已登记延迟 SH-P1S5007／SH-P1S5008，不报「没做」，只核材料与登记描述（见逐项表与 P4-01、P4-07）。
- `docker/README.md`「配置四个 App」节、`configure_apps.py` 归片 3，本片没细读。
- **`check_app_order()` 没调**：不确定它的自检路径会不会调 `frappe.log_error`，按纪律不调。SL-010 ⑤ 只用只读 SQL 核了顺序、计数与备份。
- **审核期间 `frappe_china` 工作区在变**：第一次 `status` 见 ` M install.py`，之后见 `hr.py` 少了两行，再之后又干净了。多半是别的分片或主会话在做变异测试。本片读的五个文件在审核结束时对 HEAD 零差异，结论以 HEAD `4b21aae` 为准。

## 逐项落地核查

| 意图层依据 | 要求层要求（方案任务／验收条款逐条） | 定位（文件:行） | 落地 | 生效否 | 偏差说明 |
|---|---|---|---|---|---|
| §4.8 验法、A10 | 契约 §1：`EVENT`、`_KEY` 两个常量；不复用 `erx_demo_step` | `realtime_check.py:16-17` | ✅ | ✅ | grep 全 app 无 `erx_demo_step` |
| 同上 | `run(user="Administrator", timeout=30)`，只供 `bench execute`、不 whitelist | `realtime_check.py:46-50` | ✅ | ✅ | R5 IT-020 去掉的 whitelist 没有回来 |
| 同上 | 随机令牌；缓存写 `{status: pending, user}`，过期 `timeout+60` | `:52-57` | ✅ | ⚠️ | `secrets.token_urlsafe(18)`。多存了一个 `expires_in_sec` 给 `ack` 沿用。但 `finally` 无条件删键（`:79-80`），所以「+60 秒」的宽限在 `run` 退出后不起作用（P4-05） |
| 同上 | `publish_realtime(EVENT, {token, sent_at}, user=user)`，不用 `after_commit` | `:60` | ✅ | ✅ | 上游默认 `after_commit=False`、`user` 进 user room（`frappe/realtime.py:31,64-66`） |
| 同上 | 每 0.5 秒查一次；轮询带 `use_local_cache=False`（开发守则「轮询别的进程写进缓存的值」） | `:20,:64-78` | ✅ | ✅ | 上游 `set_value` 写本地副本（`redis_wrapper.py:74`）、`get_value` 先读副本（`:91`），这一行就是 SB 修的根因 |
| 同上 | 通过返回 `{ok, token, latency_ms, acked_by, client}`；超时返回契约原文的 reason；各打一行「通过／失败」 | `:69-77,:82-88` | ✅ | ⚠️ | 字面一致。判据只认用户：执行者本机若开着同一用户的桌面页，它也会回执，`run()` 照样报通过（P4-01） |
| 同上 | `ack` 限 POST；token 不存在或过期 → `ValidationError`；用户不符 → `PermissionError`；成功写 `acked/acked_by/client=request.host` | `:23-43` | ✅ | ✅ | IT-024 留证里 `client` 为 `localhost:8000`，即页面的 Host 头，不是终端地址 |
| 同上 | 前端：`startup` 时监听事件、弹提示 10 秒、`frappe.call` 回执 | `public/js/realtime_check.js:1-6` | ✅ | ✅ | 与契约逐行一致。IT-024 留证：资源 200、提示为中文。只在桌面页（desk）加载，`/crm` 等独立前端不加载（P4-08） |
| HT-010 | `hooks.app_include_js` 引入，不经构建 | `hooks.py:30` | ✅ | ✅ | 写成字符串而不是方案里的列表，框架两种都接受 |
| 同上 | `zh.csv` 加一行译文 | `translations/zh.csv:152` | ✅ | ✅ | — |
| SL-008 ⑤ | TS-013-1 单测：不存在的 token、别的用户、同一用户置 acked、另一线程 ack 时 ok、不 ack 时 `timeout=1` 为假 | `tests/test_realtime_check.py:18-74` | ✅ | ✅ | 6 例，比方案多 1 例（模拟别的进程写）。「另一线程」改成在 `publish_realtime` 的 side_effect 里同线程调 `ack`，理由写在 `:37-38`（`frappe.local` 按线程隔离），成立。读码推断：去掉 `use_local_cache=False` 后 `:52-64` 会超时失败，与 SB 的变异结果一致 |
| SL-008 ① | TS-013-2 本机基线：桌面页加载了 `realtime_check.js`，`run()` 报通过 | SB IT-024 留证 `.log`；`frappe-bench/logs/s5-r8-it024.log` | ✅ | ✅ | 两份日志都是「失败 0 项」：通过 575.2 ms（R8 重跑 584.6 ms），页面未开 → 失败。「转发层上线前」那一次没做（上线前的现场已经没有了），见 P4-07 |
| LG-007、SL-008 ② | TS-013-3 转发层上线前局域网终端实测 → 预期失败 | — | ⏸ | — | 已登记 SH-P1S5007。本片在协议层补了一份旁证：直连容器 9100、局域网 Host／Origin → `Invalid namespace`，读码结论在协议层成立 |
| §4.8 第 1、3、4 条，A9 | TS-013-4：`frappe` 服务去掉实时端口；6787 只绑本机 | `compose.yaml:49-58` | ✅ | ✅ | `docker ps` 与宿主 `netstat` 都对得上。经局域网地址访问 6787 连接被拒 |
| 同上 | `realtime-proxy`：镜像锁 `nginx:1.30.5-alpine`；宿主 `${SOCKETIO_PORT:-9100}:9100`；`SITE_NAME` 环境变量；模板目录只读挂载；依赖 frappe；`unless-stopped` | `compose.yaml:68-81` | ✅ | ✅ | `nginx -v` 为 1.30.5 |
| 同上 | 注释写明原因；「两侧同号直通」那段改写 | `compose.yaml:50-55,:68-69` | ✅ | — | `:53` 写「两处一起改」，README `:203` 写三处（另有模板），见 P4-03 |
| A9 | `default.conf.template` 按契约 §2：`map`（本机名不补头、空 Origin 不补头、其余补 `${SITE_NAME}`）；`Upgrade`／`Connection`；`Host $http_host`；`X-Frappe-Site-Name`；`proxy_read_timeout 1h` | `realtime-proxy/default.conf.template:1-24`；渲染后的 `conf.d/default.conf` | ✅ | ✅ | 正则与契约逐字相同。契约里的两行解释注释没进模板（README `:152` 有说明）。**与上游对得上**：`authenticate.js:92-93` 先读 `x-frappe-site-name` 再取主机名；Host 原样转发，所以 `:21` 比对的是局域网地址对局域网地址。协议层实测见覆盖自证：局域网来源经转发层能过两项校验，本机来源不受影响，客户端自带的头会被覆盖或清掉。WebSocket 升级经转发层返回 101 |
| §4.8 第 3 条 | 只对实时端口生效，不多开端口，不改本机访问 | 同上；`compose.yaml:73` | ✅ | ✅ | 只 `listen 9100`；宿主新增的监听只有 9100（原来也是它）；本机来源走 `""` 分支、不加头。nginx 只在启动时解析一次 `frappe` 主机名（P4-06） |
| TS-013-4 | `save-images.sh` 的 `IMAGES` 加 nginx | `save-images.sh:12` | ✅ | — | — |
| 同上 | README「端口」节同步 | `README.md:144-227` | ✅ | — | 端口表、为什么加转发层、改端口三处、自查命令都对。`README.md:79` 的「结构」没列 `realtime-proxy`，`.env.example:8-9` 的注释与实情不符（P4-03） |
| 总纲「两侧同号」 | 9100 在 compose 发布端口、容器内监听、站点配置 `socketio_port` 三处同号 | `compose.yaml:73`；模板 `:13,:16`；`common_site_config.json`；容器 `netstat` | ✅ | ⚠️ | 本机现状三处都是 9100（另外 `frappe.boot.socketio_port` 也来自这个配置）。**但 `setup.sh` 从不写 `socketio_port`**，bench 缺省是 9000，所以按 `up.sh` 从空重建的环境不满足这一条（P4-02） |
| SL-008 ③④ | TS-013-5／6：局域网终端复测通过；停 proxy 后失败、起 proxy 后通过 | — | ⏸（终端侧）／✅（本机版） | — | 终端侧已登记 SH-P1S5007。本机版反证在 IT-024 留证里：停 proxy → 失败；起 proxy、刷新页面后 → 通过。前端只重连 3 次（`socketio_client.js:56`），断开几秒后须刷新，已写进项目概况 |
| SL-008 ⑥ | TS-013-7：局域网访问 6787 连不上；本机能连 | `compose.yaml:58` | ✅（宿主侧）／⏸（终端侧） | ✅ | 宿主经局域网地址 → rc=7（被拒）；`127.0.0.1` → 能连上（平时无人监听）。另一台设备上的实测不在 SH-P1S5007 描述里（P4-07） |
| §4.8 第 4 条 | 不改上游：`git -C apps/frappe status --short` 为空 | — | ✅ | — | 本片实测为空 |
| TS-013 验证方式 | 终端截图 `Spike/P1-S5-R4-TS013-*.png` | — | ⏸ | — | 不存在，随终端实测延迟 |
| DEC-022、SL-009 ① | TS-014-1 README「异地终端访问」：局域网段（地址、转发层一句、查地址命令） | `README.md:162-166` | ✅ | — | — |
| DEC-021 | 组网段：两端装客户端、加入同一网络、用组网地址访问、规则同样生效 | `README.md:168-172` | ✅ | — | — |
| A10 | 连通检查段：命令、通过／失败的含义、失败先查桌面页 | `README.md:174-184` | ✅ | ⚠️ | 命令可用（`bench execute` 用 `eval` 解析 `--kwargs`，JSON 里只有字符串和整数，能解析）。没提醒「同一用户的任何桌面页都算回执」（P4-01） |
| AC-009、LG-008 | 准备清单 ①～④（改口令命令、口令只记 `.env`；探测 8000／9100 通、6787／3306／6379 不通；客户端只在演示时开；④ 指向待验点） | `README.md:186-191` | ✅ | ⚠️ | 四条齐、按顺序。② 只列本项目的端口：本机还有别的服务（LiteLLM `7999`、其 postgres `5432`）监听 `0.0.0.0`，按清单探测「通过」也证不了 AC-009（P4-04） |
| LG-013 | 已知待验点三条，含 `realtime/utils.js` 回访与 `extra_hosts: host-gateway` 备用做法 | `README.md:193-197` | ✅ | — | 回访机制与上游 `utils.js:8-13` 一致（开发模式下用 Origin 的主机名加 `webserver_port`）。容器经局域网地址回访 8000 实测 200 |
| SL-009 ② | 登记 SH-P1S5005 | `P1-S5-概况.md:115` | ✅ | — | 与 TS-014-2 拟的行逐列一致，另补了 AC-009 与 LG-013 的指针 |
| SL-009 ③ | `map` 不含具体 IP；`run()` 不依赖终端地址 | 模板 `:1-5`；`realtime_check.py:46-88` | ✅ | ✅ | — |
| AC-008、SL-010 ①～③ | TS-015 空目录重建演练（含 `.git/info/exclude`、核 HEAD／顺序／`check_app_order`／remote、预检、`lock-apps.sh` 零 diff、清理） | — | ⏸ | — | 已登记 SH-P1S5008。材料：`setup.sh:14,27` 支持 `BENCH_NAME`；README「私有仓库」节（`:125-138`）补了登记里写的凭据前置；`.git/info/exclude` 没有演练行，与「未开始」相符。登记的判据里没有实时端口，演练做了也查不出 P4-02。② 预检归片 1 |
| SL-010 ④、完成标准 2 | TS-016-1 全量回归 ≥160 条，回执分报通过与跳过 | `frappe-bench/logs/s5-sb-final-regression.log` 末尾；SB 回执「全量验证」 | ✅ | ❔ | 日志：`Ran 205`、`OK`、`EXIT=0`，没有 skipped 字样。SB 回执写「205 条全 ✔」，没单列「跳过 0」。本片没重跑 |
| SL-010 ⑤、AC-010 | TS-016-2 演示站复核：`check_app_order` 为真、业务计数 0、无 `_FCT`、Raven 配置在 | 只读 SQL | ✅ | ⚠️ | 顺序（库与镜像）、GL 0、`_FCT` 公司 0、科目 266、`Raven Bot` 1 都自己查过。`check_app_order` 没调（见覆盖自证），以 SB 与 R8 的日志为准 |
| A12 | TS-016-3 新基准点另存 `保留-S5装App后/`；`20261004_005331` 仍在根目录 | `docker/backups/` | ✅ | ✅ | 实测 4＋4 个文件；`20261007_011313` 是根目录最新一套，`restore.sh` 不带参数就取它 |
| §九第 7 条 | TS-016-4 方案外改动自查 | — | ✅ | — | 本片范围内没有方案外的代码；工作区在变的现象见覆盖自证 |
| §5.2 项目文档 | TS-016-5 常驻文件回写：`项目概况.md` 模块表、已知限制、开发环境（基准点、端口）；`开发守则.md` 新约定；长效信息 #2～#4 进路线文档 | `项目概况.md:53,68-79,83,104,162-163`；`开发守则.md:75-97`；路线文档 v1.7 `:23,:189,:198,:232-233` | ✅ | ⚠️ | 都在，也与现状一致。两处说法偏强：`:104`「区分『通』与『不通』」（P4-01）、`:83`「必须同号（均 9100）」只对现有 bench 成立（P4-02） |

## 业务规则合规核

| 规则条款 | 是否涉及 | 结论 | 备注 |
|---|---|---|---|
| BR-001～BR-007 | 不涉及 | — | 本片只有连通检查工具、转发层、文档与收尾，没有产品语义改动 |
| 本片是否新增或变更领域不变量 | 否 | — | 「`socketio_port` 三处同号」「轮询跳过本地副本」都是工程约定，前者在项目概况，后者在开发守则 `:95-97`，不进业务规则 |

## 集成点登记（交接摘要）

**本片发出／消费的事件**：
- `frappe_china_realtime_check`，载荷 `{token, sent_at}`。发出方：`realtime_check.run` 经 `publish_realtime(..., user=user)` 发到 user room，不用 `after_commit`。消费方：`public/js/realtime_check.js`，只在 desk 页加载（`hooks.app_include_js`）。与 `erx_demo_step`（S7 契约，ADR-0008）无关、不共用。

**本片暴露的接口**：
- `frappe_china.realtime_check.run(user="Administrator", timeout=30) -> {ok, token, latency_ms, acked_by, client} | {ok: False, token, reason}`。没有 whitelist，只能经 `bench execute` 调。消费方：README `:176-180`、项目概况 `:83,:104`、SB／R8 的 IT-024 留证脚本、将来的 SH-P1S5005／007。
- `frappe_china.realtime_check.ack(token)`，`@whitelist(methods=["POST"])`，要求登录。
- 宿主端口面：`0.0.0.0:8000`（frappe）、`0.0.0.0:9100`（realtime-proxy）、`127.0.0.1:6787`（frappe）。

**本片依赖的接口**：
- 上游 `authenticate.js:92-93` 认 `x-frappe-site-name`；`:21` 比对 Host 与 Origin 的主机名；`utils.js:8-13` 开发模式下按 Origin 主机名加 `webserver_port` 回访。转发层原样转发 Host，是这条链能成立的前提。
- `frappe.cache` 的 Redis（`redis_cache`）由 bench execute 进程与 web 进程共用，键前缀为站点的 `db_name`。
- `socketio_client.js:120-131` 用 `frappe.boot.socketio_port` 拼宿主端口；`reconnectionAttempts: 3`。CRM 前端 `socket.js:5-8` 读 `window.socketio_port`，也走 9100。

**跨片共享状态**：
- **`socketio_port`（站点公共配置）**：本机是 9100，`setup.sh`（片 1 范围）不写它，bench 缺省是 9000（P4-02）。**请收口时与片 1 比对**：片 1 的重建脚本要不要负责这个值。
- **转发层把 `SITE_NAME` 写死成一个站**：从局域网来的实时连接一律补 `erx.localhost`。测试站只经 `127.0.0.1:6787` 访问，不受影响；以后若要从局域网看测试站的实时，须另想办法。
- **`installed_apps` 与基准点**：演示站库与镜像都是七个 app 的目标顺序；`20261007_011313` 为当前空账基准点（S7 造数起点），`20261004_005331` 在根目录。片 2 的 `check_app_order` 与片 1 的归位以它为准。
- **`frappe_china` 工作区在审核期间被别的会话改动过**（覆盖自证）。收口时请确认各片读的都是 HEAD `4b21aae`。
- **约定**：开发守则 `:95-97`「轮询别的进程写进缓存的值时跳过本地副本」出自本片 IT-024。别的轮询缓存的代码（若有）请各片对照。

## 自证复核

| 被审产物声称 | 实际复核 | 一致否 |
|---|---|---|
| D 回执 Part4：TS-014「完成」、TS-016「完成（按现有结果收口）」 | R5 E 已核出不符（IT-023／025／026），SB 与 R5 当场修过；本片复核修后的 README 四段、登记册、基准点、常驻文件都在 | 原声称不一致（已由 R5 立项，不重复立项）；修后一致 |
| SB IT-024：`run()` 轮询改 `use_local_cache=False` 后本机基线通过；停 proxy 失败、起 proxy 刷新后通过 | 代码 `:67` 在；两份留证日志「失败 0 项」，数值与回执相同；上游 `redis_wrapper.py:74,91` 证实根因 | 一致 |
| SB：`test_realtime_check` 6/6，去掉 `use_local_cache=False` 的变异 → 1 例失败 | 6 例在；读码推断 `:52-64` 在变异下会超时。没重跑 | 用例数一致；变异未复核 |
| R5 当场修 IT-020：默认 30 秒、`timeout+60`、0.5 秒、reason 用原文、`run` 去掉 whitelist | 逐项对上 | 一致；`+60` 被 `finally` 删键架空（P4-05） |
| README `:182`、项目概况 `:104`：检查「区分『通』与『不通』」「只认用户、不认终端地址」 | 只认用户属实；正因为只认用户，本机同一用户开着的页面会让终端测试报假通过 | **部分不一致**（P4-01） |
| 项目概况 `:83`、README `:199-203`：三处必须同号（均 9100） | 本机现状三处都是 9100；从空重建时 `socketio_port` 是 bench 缺省 9000 | **对现状一致，对重建不成立**（P4-02） |
| `compose.yaml:53`「两处一起改」 | 还要改模板的 `proxy_pass`（README 写的是三处） | **不一致**（P4-03） |
| `.env.example:8-9`「容器内仍是 9000」 | 容器内监听 9100 | **不一致**（P4-03，S5 前就有，S5 加转发层后更容易误导） |
| SB 全量：205 条全过，≥160 | 日志末尾 `Ran 205`、`OK`、`EXIT=0`，没有 skipped | 一致（没重跑） |
| SB IT-026：基准点 `20261007_011313` 另存，`005331` 仍在根目录 | 实测 4＋4＋4 个文件 | 一致 |
| R8 E：IT-024 重跑通过 584.6 ms | `logs/s5-r8-it024.log` 末段相同 | 一致 |
| 登记册 SH-P1S5007 的范围 | 没写 SL-008 ⑥ 终端侧与 TS-013 截图；「恢复直通映射」要改 compose、重建 frappe 容器，代价没写；上线前对照其实可以不动 compose 做 | **描述不全**（P4-07） |
| 登记册 SH-P1S5005 | 与 TS-014-2 拟的行逐列一致 | 一致 |
| 登记册 SH-P1S5008 的判据 | 没有实时端口这一项，演练做了也查不出 P4-02 | 描述与范围一致，判据有漏（并入 P4-02） |

## 问题清单

| # | 严重程度 | 定位 | 问题描述 | 违背的标准/意图 | 建议 | 建议档位 | 待裁决点 | 状态 |
|---|---|---|---|---|---|---|---|---|
| P4-01 | 中（中／低边界） | `frappe_china/realtime_check.py:68-77`；`docker/README.md:182-184`；`docs/项目概况.md:104` | 判据分不清「终端收到了」和「本机页面收到了」。`run()` 发给 user room，**这个用户任何一个打开着的 desk 页**回执都算通过。方案的局域网实测（SL-008 ③④）用的就是 Administrator，执行者本机一般也以 Administrator 开着桌面页。这时终端的实时通道不通，`run()` 照样报通过；反证 ④ 停 proxy 时本机页面也断，所以反证能失败，但「上线后通过」那一半没有判别力。回执里其实有区分用的值：`client` 记的是页面的 Host（本机 `localhost:8000`，终端是 `<局域网地址>:8000`），但 `run()` 不判它，打印的那一行也不显示它 | 开发守则「判据必须能区分它要区分的两种情形」；需求 §4.8 验法 2「**异地终端界面上**实收到」 | ① 打印行带上 `client`；② README 连通检查段写明：测终端时本机不要开同一用户的页面，或终端用专门的用户登录；③ 可选：加 `expect_client` 参数，回执的 `client` 不匹配就不算通过，并补一例单测 | 本Session修 | 只改输出与说明（①②），还是同时加参数按 `client` 判（③） | 待裁决 |
| P4-02 | 中 | `docker/scripts/setup.sh:101-108`（第 2 段不写 `socketio_port`）；bench `config/common_site_config.py:90-103`（缺省 9000）；`docker/compose.yaml:73`；模板 `:16` | 「三处同号」只是本机现状，重建时不成立。`setup.sh` 从不写 `socketio_port`，`bench init` 在新机器上写入缺省 9000。按 `up.sh` 从空重建后：实时服务监听 9000，转发层 `proxy_pass frappe:9100` 返回 502；浏览器按 `frappe.boot.socketio_port=9000` 去连宿主 9000（Windows 保留段，也没人发布）。实时**静默断连**，页面照常，项目概况 `:83` 写明的正是这种症状。9100 是 P1-S2-R1 手工 `set-config` 进去的，从没进脚本。S5 前就有这个缺口，但 S5 的 AC-008「新机器按 `apps.json` 重建得到同一个站」与转发层都依赖它；SH-P1S5008 的判据里也没有这一项，演练做了也查不出 | AC-008、总纲 §一完成标准 3 与 A9 的前提；开发守则「判据必须能区分」（演练判据） | `setup.sh` 第 2 段加 `bench set-config -g socketio_port "${SOCKETIO_PORT:-9100}" --parse`，`up.sh` 把 `SOCKETIO_PORT` 传进容器；SH-P1S5008 的判据补「`socketio_port` 为 9100，经宿主 9100 握手 200」。验证：`bash -n`，在现有 bench 上重跑第 2 段（幂等，值不变） | 本Session修 | 是否同时补 SH-P1S5008 的判据（改登记册） | 待裁决 |
| P4-03 | 低 | `docker/compose.yaml:53`；`docker/.env.example:8-9`；`docker/README.md:79,94` | 端口文档三处与实情不符：① compose 注释写「两处一起改」，还要改模板的 `proxy_pass`（README `:203` 写的是三处）；② `.env.example` 写「容器内仍是 9000」，实际是 9100，而且只改 `SOCKETIO_PORT` 会断连，注释却暗示可以单改（S5 前就有，S5 加转发层后更容易误导）；③ README「结构」节写 `compose.yaml 服务定义（mariadb / redis×2 / frappe）`，目录树里没有 `realtime-proxy/` | 方案 TS-013-4「README 端口节同步」；开发守则「判据必须能区分」（文档引导人改错地方） | 三处措辞对齐 README `:199-214`；`.env.example` 注明改它必须同时改另外两处 | 本Session修 | — | 待裁决 |
| P4-04 | 低 | `docker/README.md:189`（准备清单 ②） | 准备清单只探测本项目的五个端口，证明不了 AC-009 的「**只有**页面与实时两条可达」。本机实测还有项目 compose 之外的服务监听 `0.0.0.0`：`7999`（LiteLLM，后面接着模型密钥）、`5432`（LiteLLM 的 postgres）。组网后它们对网内设备同样可达。按清单逐条打勾会得出「只开两个端口」的错误结论 | AC-009；LG-008「对外只放页面与实时两条」；开发守则「判据必须能区分」 | ② 改为「在宿主 `netstat -ano` 列出全部 `0.0.0.0` 监听，逐个判；从终端对组网地址扫端口，只应见 8000、9100」，并点名 7999／5432 这类同机服务；登记册 SH-P1S5005 补一句 | 本Session修 | 同机其它服务（LiteLLM）组网时是关掉、改绑 `127.0.0.1`，还是只记风险 | 待裁决 |
| P4-05 | 观察 | `realtime_check.py:41,54,79-80`；`:29,31` | ① `run()` 的 `finally` 无条件删键，`timeout+60` 的宽限期在 `run` 退出后不起作用。超时后晚到的回执会抛 `ValidationError`，终端页面会弹一个英文错误框（`frappe.throw` 的文案没加 `_()`）。演示中晚到一次，观众会看到报错。② `ack` 重写时按原始总时长重设过期时间，不是剩余时长，无害 | 方案契约 §1（「过期 timeout+60」的本意） | 不删键、留给过期；或者前端回执失败时静默。两段报错文案加 `_()` 与译文 | 延迟或不修 | 是否改为不删键 | 待裁决 |
| P4-06 | 观察 | `docker/realtime-proxy/default.conf.template:16` | `proxy_pass http://frappe:9100` 用的是固定主机名，nginx 只在启动时解析一次。`frappe` 容器重建后若换了 IP（IT-028 那种 `compose up -d` 重建），转发层仍连旧 IP，返回 502，要重启 proxy 才恢复。**读码推断，未实测**（不得重启容器）。compose 会不会顺带重建 `depends_on` 它的服务也没核 | 需求 §4.8 第 1 条（异地可达的稳定性）；静默失败 | 加 `resolver 127.0.0.11 valid=10s;` 并用变量写 `proxy_pass`；或在 README 改端口那段补「重建 frappe 后 `docker compose restart realtime-proxy`」 | 延迟或不修 | 改配置，还是只补一句说明 | 待裁决 |
| P4-07 | 低 | `docs/01-需求摸底/S05-演示链路/P1-S5-概况.md:117`（SH-P1S5007） | 登记描述不全：① 没写 SL-008 ⑥ 的终端侧（另一台设备访问 6787 连不上）和 TS-013 的终端截图；② 「恢复直通映射」要改 compose、重建 frappe 容器，会丢字体、要重跑 `up.sh`（IT-028），代价没写；③ 本片已证明「上线前对照」可以不动 compose 做：在容器内直连 9100、用局域网 Host／Origin 握手，得到 `Invalid namespace`（覆盖自证）。本机版的「转发层上线前」一次（SL-008 ①前半）同样不再可做，也没记 | 流程规范 §12（登记描述与实情一致） | 登记描述补 ①②，把 ③ 写成可选的替代做法 | 本Session修 | 上线前对照是否接受协议层探针作替代、不再要求真终端 | 待裁决 |
| P4-08 | 观察 | `frappe_china/hooks.py:30`；`docker/README.md:165,184` | 回执脚本只在 desk 加载。终端开着 `/crm` 等独立前端时实时其实是通的，`run()` 却报失败。README 写了「打开桌面页」，本 Stage 的验收够用；但 S7 演示要在 `/crm` 与 `/app` 之间切（路线文档 v1.7 S7 第 14 条），`/crm` 一侧的实时连接（`crm/frontend/src/socket.js`，也走 9100）从局域网一次都没验过 | 需求 §5.2「连通机制是 CR-008／CR-009 在异地终端成立的前提」 | 交 S7：CR-009 心跳自检覆盖 `/crm`，或 SH-P1S5007 实测时顺带在终端开一次 `/crm` 看 socket 状态 | 延迟或不修 | — | 待裁决 |

## 本片盲区自述

- **没跑任何测试，没跑 `run()`，没开浏览器，没停 proxy**（受任务约束）。「测试会过」「变异会失败」全凭读码；本机基线、反证只看了留证日志。协议层握手探针是本片唯一的实测，它证明的是「命名空间与来源两项校验能过」，没有带 cookie 走完鉴权与回访。HT-008 的最后一段（经局域网 Origin 回访 `get_user_info` 成功）只证到「容器能访问 `192.168.3.50:8000`」。
- **没往这些方向找**：nginx 的 WebSocket 长连接在 1 小时 `proxy_read_timeout` 前后的行为（只验了握手返回 101）；HTTPS 或反向代理到 443 的场景（本 Stage 不涉及）；Tailscale 的 MagicDNS 主机名会走哪个分支（读正则判断会走补头分支，未实测）；`test.localhost` 经 6787 访问时的实时通道（6787 不经转发层，浏览器按 `socketio_port` 连 9100，`localhost` 来源取 `default_site`，即演示站，测试站页面的实时多半一直连错站。S5 前就这样，未立项）。
- **查得最浅的一处**：SL-010（TS-015／016）。TS-015 整体延迟，只核了材料；TS-016 的 `check_app_order` 没调，演示站只做了只读 SQL 抽查。
- **定级拿不准**：P4-01 定「中」，理由是方案指定的实测流程（同一 Administrator）正好落在误判区；若用户认为执行者自会关掉本机页面，可降为低。P4-02 定「中」而非「高」：现有环境不受影响，新机器重建前还有 SH-P1S5008 一道关；但它是静默失败，演练判据又查不出来，若换机器在 S7 之前，应升为高。P4-02 严格说是 S5 前就有的缺口，记作本片发现，是因为 Part4 的重建演练与「三处同号」都以它为前提。
- **拿不准处**：P4-04 里 LiteLLM 不属本项目 compose，算不算本项目的暴露面，我按 AC-009 的字面「从外部探测只有两条可达」判为算。
