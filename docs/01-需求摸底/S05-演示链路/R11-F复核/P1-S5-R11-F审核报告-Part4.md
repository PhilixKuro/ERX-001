# F 复核分片报告 · 片 4（对象：R10 当场修 FD-038／041／042／043／049 / 审核标准：R3 方案 Part4，B 需求 §4.8、AC-008／009）

**轮次**：P1-S5-R11｜**步骤**：F 复核分片 4｜**日期**：2026-10-08｜**执行者**：Claude 子 Agent（只读）
**依据**：[R3 开发方案 Part4](../R03-开发方案/P1-S5-R3-C开发方案-Part4.md)（接口契约 §1／§2、TS-013～015）、[B 需求文档](../R02-需求文档/P1-S5-R2-B需求文档.md) §4.8、AC-008／009、[R10 F 复核收口报告](../R10-F复核/P1-S5-R10-F审核报告.md)（问题清单 FD-038／041／042／043／049 行、当场修清单第 2、5、6、7、11 行、修后验证）、[R10 Part4](../R10-F复核/P1-S5-R10-F审核报告-Part4.md)（全文）、Stage 概况登记册 SH-P1S5005／007／008、`docs/项目概况.md:83`、`docs/业务规则.md`
**被审范围**：主仓库 `d7b89d6..288470b` 中的 `docker/up.sh`、`docker/scripts/setup.sh`（第 2 段与开头变量）、`docker/compose.yaml`、`docker/realtime-proxy/default.conf.template`、`docker/.env.example`、`docker/README.md`（端口、异地终端访问、socketio 同号、故障表各节）、`docs/项目概况.md:83`、Stage 概况登记册；`frappe_china` `9d53d39..052e4c3` 中的 `frappe_china/tests/test_realtime_check.py`（对照 HEAD `realtime_check.py`）

## 覆盖自证

**读全的**：R10 Part4 全文；R10 收口报告与本片相关的行（grep 定位后逐行读）；R3 方案 Part4 接口契约 §2、TS-013～015；B 需求 §4.8 全节与 AC-008／009；两仓本轮 diff 中属于本片的全部 hunk；HEAD 版 `up.sh` 全文、`compose.yaml` 全文、`default.conf.template` 全文、`.env.example` 全文、`setup.sh` 第 1～130 行与第 380～410 行（第 7 段 clear-cache）、README 第 140～235 行、`realtime_check.py` 全文、`test_realtime_check.py` 全文；`start.sh`、`down.sh` 全文，`restore.sh` 第 40～70 行，`backup.sh`／`shell.sh`／`seed-demo.sh`／`set-locale.sh`／`configure-apps.sh` grep。

**读工作区还是 HEAD**：`setup.sh` 一律 `git -C /d/ERX-001 show HEAD:docker/scripts/setup.sh`；`up.sh`、compose、模板、`.env.example`、README、`realtime_check.py` 与测试也用 `git show HEAD:` 读。`configure_apps.py`、`lock-apps.sh` 不在本片，没读。收尾时 `git status --short`：主仓库只有本报告所在的 `R11-F复核/` 目录未跟踪，`frappe_china` 为空。

**对照的上游与镜像源码**（只读）：
- nginx 镜像 `/docker-entrypoint.d/20-envsubst-on-templates.sh` 全文（`docker compose exec realtime-proxy cat`）。
- frappe `commands/utils.py:897-920`（`set-config --parse` 走 `ast.literal_eval`）；`config.py:14-28,109-155`（站点配置在 web 进程里 `site_cache(ttl=60)`）；`boot.py:162-168`（`socketio_port` 进 bootinfo）；`sessions.py:136-147`（bootinfo 按用户缓存在 Redis）；`cache_manager.py:48-50,81-95`（`bootinfo` 属 user cache keys，clear-cache 会清）；`realtime/index.js:7,90-92` 与 `node_utils.js:17-42`（实时服务在模块加载时读一次 `socketio_port`）；`realtime/utils.js:9-12`（开发模式下回访 `webserver_port`）。
- frappe `tests/classes/integration_test_case.py:200-211`（每例 `delattr(frappe.local, "request")`）。
- bench `config/templates/Procfile:6`（`--port {{ webserver_port }}`）。

**只读查询与实验**：
- `docker compose config --hash "*"`：缺省值下 `frappe` 为 `2d6181f5…`，`realtime-proxy` 为 `27e0ca9f…`；`SOCKETIO_PORT=9200` 时 `frappe` 仍是 `2d6181f5…`，只有 `realtime-proxy` 变成 `2845d136…`。`docker inspect` 两容器的 `com.docker.compose.config-hash` 标签分别等于缺省值下的这两个值。
- `SOCKETIO_PORT=<值> docker compose config`：`9200` → `published "9200"`、`target 9200`、环境 `"9200"`；`""` → 三处都回落 9100；`09100` → 端口规整成 9100，但环境原样传 `"09100"`；`0` → 退出 1，`missing a target port`；`99999`、`65536` → 退出 1，`invalid containerPort`；`65535`、`80` → 退出 0；`" 9100"` → 退出 1。
- 容器内 `python3 -c ast.literal_eval`：`'09100'` 抛 `SyntaxError: leading zeros in decimal integer literals are not permitted`；`'0'`→0，`'99999'`→99999。
- 一次性容器 `docker run --rm --network none docker.io/nginx:1.30.5-alpine`（与项目容器无关，跑完即删）：`listen 09100; proxy_pass http://127.0.0.1:09100;` 时 `nginx -t` 通过；`listen 0;` 时 `nginx -t` 失败。
- `realtime-proxy` 容器内渲染结果 `/etc/nginx/conf.d/default.conf`、`env` 变量名列表（只有大写名字）。
- 宿主 `curl …:9100/socket.io/?EIO=4&transport=polling` → 200。`netstat -ano | findstr LISTENING` 中本地地址不是 `0.0.0.0`／`127.*`／`[::]`／`[::1]` 的行：`192.168.3.50:139`、`172.22.208.1:139`、`172.22.144.1:139`（PID 4）。
- 仓库根执行 `docker compose config --services` → `no configuration file provided: not found`。
- `frappe-bench/sites/common_site_config.json`：`"socketio_port": 9100`（整数）。`docker/.env` 只读第 7～11 行（端口段，不含口令）。
- 容器 `ip_unprivileged_port_start` 为 0。

**跳过的及原因**：没跑测试、没跑变异（FD-043 只读码，变异由主会话做）、没跑 `up.sh`／`setup.sh`／`run()`、没停或重建任何项目容器（硬约束）。没开浏览器。没在 9100 以外的端口上端到端通一次实时。没有建临时文件，`.claude/r11-tmp/p4/` 未创建。

## R10 已修项复核

| R10 项 | 修于（当场／SB） | 定位（文件:行，HEAD） | 落地 | 生效 | 原问题消失 | 说明 |
|---|---|---|---|---|---|---|
| FD-038 | 当场 #2（改判取 (a) 同源） | `up.sh:42`；`setup.sh:17,108-116`；`compose.yaml:50-56,74,77`；`default.conf.template:13-17`；`.env.example:8-10`；README `:151,156,205-225,288`；`项目概况.md:83`；登记册 SH-P1S5008 | ✅ | ✅ | ✅（文档余项见 P4-01／02／08） | **落地**：清单所列九处都改了。**生效**：`up.sh` 把 `SOCKETIO_PORT` 传进容器，`setup.sh` 用它写 `socketio_port`（`--parse`，整数）；compose 两侧端口与 proxy 环境都取它；nginx 的 envsubst 只替换容器里已定义的环境变量（`defined_envs` 取自 `ENVIRON`），变量名全为大写，模板里的 `$http_upgrade`、`$connection_upgrade`、`$http_origin`、`$frappe_site_header`、`$http_host` 都是小写，没被替换。容器内渲染结果与 `curl` 200 都已核。`SOCKETIO_PORT=9200` 渲染时 compose 三处都变。四个入口的缺省都写成 `${SOCKETIO_PORT:-9100}`，空值时一致回落到 9100。**原问题**：照 README 改端口后再跑 `up.sh`，现在写入的是 `.env` 的值，不会再改回 9100。**改端口时会不会丢字体**：配置哈希实测，改 `SOCKETIO_PORT` 只改变 `realtime-proxy` 的哈希，`frappe` 不变，而且现有两容器的标签哈希等于缺省配置，所以 `docker compose up -d` 只重建 proxy，不动 frappe。**全仓有没有别处写死**：`restore.sh`、`start.sh`、`backup.sh`、`shell.sh`、`seed-demo.sh`、`set-locale.sh`、`configure-apps.sh`、另起测试站服务的命令（`serve --port 6787`）、`frappe_china` 代码与测试都不写 `socketio_port`，也没写死 9100；`realtime_check` 的输出里没有端口。仍写着 9100 的只有文档：README `:168,199,221,223`，`项目概况.md:83`「转发到容器内 9100」，SH-P1S5007 ③⑤，以及本机不进 git 的 `docker/.env` 注释（P4-02、P4-08）。**实时服务只在启动时读端口**：`realtime/index.js:7` 在模块加载时 `get_conf()`，说法成立。**三处是否同一组**：compose 注释、README `:205`、`.env.example`、`setup.sh` 注释四处说的都是「站点配置、proxy 发布端口、模板」，这一组已统一；只有 `项目概况.md:83` 列的是「proxy 宿主端口、容器内监听端口、站点配置」，而且还留着「改一处会断连」（P4-02）。README 改端口代码块里的命令工作目录不一致，另外缺「刷新已开的页面」一步（P4-01）。`setup.sh` 的校验放过前导 0（P4-07） |
| FD-041 | 当场 #5 | README `:191`；登记册 SH-P1S5005（`P1-S5-概况.md:121`） | ✅ | — | ⚠ 部分 | README 与 SH-P1S5005 的判据逐字对过，意思一致：「除页面与实时两端口外，凡监听 `0.0.0.0`／`[::]` 的都从终端探测不通或被防火墙挡住」。点名已改为举例，IPv6 和防火墙也补上了。可以执行：`netstat` 列出、逐项判。**没覆盖到的**：只绑在某块网卡地址上的监听不在「`0.0.0.0`／`[::]`」里，但对那块网卡所在网络同样可达。本机此刻就有 `192.168.3.50:139`、`172.22.*:139`，组网网卡起来后同类监听会绑到组网地址上（P4-03） |
| FD-042 | 当场 #6 | README `:184`；登记册 SH-P1S5007 ③末句（`P1-S5-概况.md:123`） | ✅ | — | ⚠ 部分 | 单向判读的方向与代码相符：`ack()` 每次都 `set_value` 覆盖同一个键（`realtime_check.py:33-42`），所以看到终端访问用的地址，能证明终端那页回执了；看到 `localhost:8000`，证明不了终端没回执。**两处说法比代码宽**：①「以后到的回执为准」不准确。`run()` 每 0.5 秒查一次，第一次读到 `acked` 就返回（`:64-82`）。若本机回执先到、在终端回执之前被读到，显示的是**先到**的那次。②「终端地址」其实是 `request.host`，即终端访问时用的**本机**局域网（或组网）地址，不是终端自己的 IP。本机浏览器若也用局域网地址打开，显示的值与终端一样，单向判读也就不成立了（P4-04） |
| FD-043 | 当场 #7 | `tests/test_realtime_check.py:46-57` | ✅ | ✅（R10 修后验证：K7 复跑 1 例失败） | ⚠ 部分 | `redirect_stdout` 能接住 `run()` 的 `print`。断言 `assertIn(f"回执页面 {result['client']}", …)` 能抓到删掉或改掉「回执页面」字样（K7）、拿别的字段替换 client 这类变异。**判别力的缺口**：期望值取自被测结果本身。测试基类每例都 `delattr(frappe.local, "request")`，所以 `ack` 里 `client` 恒为 `"unknown"`。`ack` 不写 `client`（结果为 `None`，输出「回执页面 None」，断言照样成立），或改成恒写 `"unknown"`、不再取 `request.host`，这两种变异都抓不到。FD-003 的要点「回执页面取的是页面的 Host」没有任何测试守着（P4-05） |
| FD-049 | 当场 #11 | 登记册 SH-P1S5008（`P1-S5-概况.md:124`） | ✅ | — | ⚠ 部分 | 补句的事实部分属实：演练 bench 的 `webserver_port` 由 `make_ports` 定为 8001（R10 Part4 只读实测），compose 只发布 8000；演练用的 `setup.sh` 命令（方案 TS-015 第 2 步）不传 `SOCKETIO_PORT`，于是写成缺省 9100，与主 bench 同号，两边的 `bench socketio` 不能同时起。**补句的两个出路都不好照做**：「演练 bench 替换主 bench」在方案和 README 里都没有操作定义，TS-015 第 6 步是删演练目录。「改用 SH-P1S5007 ③ 的协议层探针」目的不同：③ 是证明会被**拒绝**（`Invalid namespace`），不是证明能通过；而且要探演练 bench，它的实时服务仍得占 9100，还是要先停主 bench。另外，判据改成了「等于 `.env` 的 `SOCKETIO_PORT`」，可演练命令不传这个变量，`.env` 一旦不是 9100，这条判据就必然不成立（P4-06） |

## 延迟／不做项登记核对

| 项 | 裁决去向 | 登记位置 | 描述与实情一致否 | 说明 |
|---|---|---|---|---|
| R9 FD-030（R10 未动） | 延迟，SH-P1S5007 ④ | `P1-S5-概况.md:123` | ✅ | 本轮 `realtime_check.py` 没改（`9d53d39..052e4c3` 只动了 README 与测试），`finally` 删键、`ack` 抛英文错的描述仍然属实 |
| R9 FD-031（R10 未动） | 延迟，SH-P1S5007 ⑤ | 同上 | ⚠ 字面过时 | ⑤ 引的是 `proxy_pass http://frappe:9100`，模板现在写的是 `${SOCKETIO_PORT}`。不过它在 nginx 启动前由 envsubst 换成字面量，不是 nginx 变量，「只在启动时解析一次主机名」的结论不变。只是引文过时，并入 P4-02 |
| R10 FD-046 | 延迟到 Stage 收口 | 收口报告与 Stage 概况 R10 行 | ✅ | 路线文档 grep `debug_mode`、`FD-032` 仍为 0 条，与「收口时同步」一致，没有提前或遗漏的迹象 |
| R10 FD-047 | 延迟，`SH-P1S5011` | `P1-S5-概况.md` 登记册末行 | — | 不属本片依据，只确认登记行存在 |

## 业务规则合规核

| 规则条款 | 本轮改动是否涉及 | 结论 | 备注 |
|---|---|---|---|
| BR-001 小企业会计准则 | 否 | 合规 | 本片改动只涉及端口配置、文档与一条测试断言 |
| BR-002 报表构成 | 否 | 合规 | — |
| BR-003 增值税税率 | 否 | 合规 | — |
| BR-004 未交增值税结转 | 否 | 合规 | — |
| BR-005 附加税 | 否 | 合规 | — |
| BR-006 资产负债表恒等 | 否 | 合规 | — |
| BR-007 价税分离 | 否 | 合规 | — |

## 集成点登记（交接摘要）

- **本片依赖**：
  - 片 1：`setup.sh` 第 2 段与开头变量、`up.sh:42` 是 FD-038 的落点，与片 1 的 `setup.sh` 范围重叠。请片 1 确认第 3 段及之后的改动没有挪动第 2 段，`up.sh` 的 `-e` 列表也没有被别的修复删改。
  - 主会话的变异：本片读的 `setup.sh` 是 HEAD 版。若变异窗口里改过第 2 段，请以 HEAD 为准。
- **本片暴露**：
  - 环境变量契约：`SOCKETIO_PORT` 由 `up.sh` 传给 `setup.sh`，由 compose 传给 `realtime-proxy`。凡是绕过 `up.sh`、直接 `docker compose exec … setup.sh` 的调用（方案 TS-015 第 2 步的演练命令就是），都要自己带上 `-e SOCKETIO_PORT`，否则写成 9100。
  - `setup.sh` 第 2 段只拦空值和非数字。0 和超过 65535 的值先在 `up.sh:17` 的 `docker compose up -d` 报错退出，到不了第 2 段。前导 0 能过校验，然后在 `set-config --parse` 处以 traceback 退出（P4-07）。
  - `run()` 的输出格式和返回字段本轮都没变。
  - 改 `SOCKETIO_PORT` 只会让 `realtime-proxy` 重建，`frappe` 容器不重建（配置哈希实测）。

## 自证复核

| 被审产物声称（R10 报告／文档） | 实际复核 | 一致否 |
|---|---|---|
| 当场修 #2：`up.sh` 传、`setup.sh` 读并在非数字时报错退出、compose 两侧与 environment、模板 `listen`／`proxy_pass`，文档同步 | 逐处都在 HEAD 中 | 一致 |
| 修后验证：缺省值渲染 `listen 9100`，宿主 200 | 容器内渲染文件与 `curl` 200 本次都复核了 | 一致 |
| 修后验证：`SOCKETIO_PORT=9200` 时 compose 发布与容器端口都是 9200 | 本次重跑 `docker compose config` 一致 | 一致 |
| README `:205`、compose 注释、`.env.example`：三处都取 `.env` | 这三份文档与 `setup.sh` 注释说的是同一组；`项目概况.md:83` 列的不是这一组 | 部分一致（P4-02） |
| README `:207-212`：「改端口只改 `.env` 一处」，然后执行三步 | 只改 `.env` 这一点成立（`up.sh` 不会再撤回）。第一步与 `up.sh:17` 重复，而且在仓库根执行会失败；没说要刷新已开的页面 | 部分一致（P4-01） |
| README `:212`：「实时服务只在启动时读端口」 | `realtime/index.js:7` 在模块加载时读一次 | 一致 |
| README `:215`：「下次 `up.sh` 会按 `.env` 写回去」 | `setup.sh:114` 每次都执行 | 一致 |
| `.env.example:10`：「改它之后要 `docker compose up -d` 再跑 `docker/up.sh`」 | 能走通，第一步多余（同 P4-01） | 一致（有冗余） |
| 当场修 #5：准备清单 ② 改判据式，SH-P1S5005 同步 | 两处一致；漏了绑在具体网卡地址上的监听 | 部分一致（P4-03） |
| 当场修 #6：「以后到的回执为准」 | 代码是「轮询第一次读到的那次」 | 部分一致（P4-04） |
| 当场修 #7：断言输出含「回执页面 <client>」，K7 被抓到 | 能抓 K7；期望值来自被测结果本身，`client` 的取值来源没人守 | 部分一致（P4-05） |
| 当场修 #11：须在演练 bench 替换主 bench 后做，或改用协议层探针 | 事实属实；两个出路都没有可照做的步骤 | 部分一致（P4-06） |

## 问题清单

| # | 严重程度 | 定位 | 问题描述 | 违背的标准／意图 | 建议 | 建议档位 | 待裁决点 | 状态 |
|---|---|---|---|---|---|---|---|---|
| P4-01 | 低 | `docker/README.md:209-213`、`:219-226`；`docker/.env.example:10` | **改端口代码块的工作目录对不上，还少一步。** ① `docker compose up -d` 只能在 `docker/` 下跑（仓库根执行 `docker compose config` 实测报 `no configuration file provided`），紧接着的 `docker/up.sh` 却是相对仓库根写的。照块里的顺序，哪个目录下都有一条跑不通。自查块同样混用：`:221,223` 要在 `docker/` 下，`:225` 的 `grep … frappe-bench/sites/…` 要在仓库根。② 第一条本来就多余：`up.sh:17` 自己会执行 `docker compose up -d`，而且只重建 proxy（配置哈希实测）。③ 少了「刷新已开着的桌面页」：页面上的 `frappe.boot.socketio_port` 是加载时取的，已开的页面会一直连旧端口。`setup.sh` 第 7 段的 clear-cache 只清服务端的 bootinfo。报错是显式的，不会静默出错，所以定低 | FD-038 意图（改端口只改 `.env` 一处、照做能通）；开发守则「判据／步骤可照做」 | 代码块改为两步：`docker/up.sh`（仓库根执行，它已含 `docker compose up -d`，只重建 `realtime-proxy`），然后停掉并重跑 `docker/start.sh`，再刷新已开的页面。`.env.example:10` 改成「改它之后跑 `docker/up.sh`、重启 `start.sh`」。自查块统一注明在哪个目录下跑，或者都改成 `docker compose -f docker/compose.yaml …`（README `:371` 已用这种写法） | 本Session修 | — | 待裁决 |
| P4-02 | 观察 | `docs/项目概况.md:83`；README `:168,199,221,223`；登记册 SH-P1S5007 ③「直连 `9100`」、⑤「`proxy_pass http://frappe:9100`」 | **常驻文件那句与另外三份说的不是同一组，还留着自相矛盾的半句。** `项目概况.md:83` 列的是「`realtime-proxy` 发布的宿主端口、**容器内监听端口**与站点配置」，另外三份列的是「站点配置、proxy 发布端口、**模板**」。同一句先说「改端口只改那一处」，紧接着又说「**改一处会让 realtime 静默断连**」，现在两句是冲突的（README `:205` 已改成「不同号时」）。开头的「转发到容器内 9100」也还写死。README 防火墙两处、自查命令两处，以及 SH-P1S5007 ③⑤ 仍写 9100：自查命令有一句「9100 换成 .env 的 SOCKETIO_PORT」的提示，防火墙两处和 ⑤ 的引文没有提示 | FD-038 意图（各处说同一组）；常驻文件契约（失效内容顺带清掉） | `项目概况.md:83` 改成「转发到容器内同号端口」，三处改成与 README 相同的一组，「改一处会…」改成「不同号会…」（写前按常驻文件契约判）。README `:168,199` 写成「8000、实时端口（缺省 9100）」。SH-P1S5007 ⑤ 的引文改成「`proxy_pass http://frappe:<实时端口>`（envsubst 渲染后是字面量）」 | 本Session修 | 常驻文件那一句是否本轮改 | 待裁决 |
| P4-03 | 低 | README `:191`（准备清单 ②）；登记册 SH-P1S5005 | **判据只覆盖 `0.0.0.0`／`[::]`，漏了绑在具体网卡地址上的监听。** 本机 `netstat` 实测有 `192.168.3.50:139`、`172.22.208.1:139`、`172.22.144.1:139`（PID 4，NetBIOS），它们对各自网卡所在的网络可达，但照判据不用判。组网客户端起来后，这类按网卡绑定的服务会绑到组网地址上，而那正是 AC-009 要守的入口 | AC-009「从外部探测只有页面与实时两条可达」；FD-041 意图 | 判据改为「本地地址为 `0.0.0.0`、`[::]` 或**组网网卡地址**的监听」，并在组网客户端连上之后再跑一次 `netstat`。SH-P1S5005 同步 | 本Session修（文档）或延迟到 SH-P1S5005 唤醒时 | 现在改，还是唤醒时一并改 | 待裁决 |
| P4-04 | 观察 | README `:184`；登记册 SH-P1S5007 ③末句；`realtime_check.py:33-42,64-82`（HEAD） | **两处说法比代码宽。** ①「两个页面都开着时以后到的回执为准」：`run()` 每 0.5 秒轮询，第一次读到 `acked` 就返回。若本机回执先到，又在终端回执之前被读到，显示的是先到的那次。结论方向（本机地址不能判不通）不受影响，理由写错了。②「终端地址（`<局域网地址>:8000`）」：值取自 `request.host`，是终端访问用的**本机**局域网或组网地址，不是终端的 IP。本机浏览器若也用局域网地址打开，显示的值与终端相同，「显示该地址即判终端通」就不成立了 | FD-042 意图；开发守则「判据必须能区分」 | 改为「显示的是页面访问用的地址：为本机局域网／组网地址，且本机只用 `localhost` 打开，即可判终端通；为 `localhost` 时不能判不通（哪次回执被读到取决于轮询时刻），关掉本机桌面页重跑」。SH-P1S5007 同步 | 本Session修 | — | 待裁决 |
| P4-05 | 观察 | `frappe_china/tests/test_realtime_check.py:57`；`realtime_check.py:32,39`（HEAD） | **新断言的期望值取自被测结果本身。** 测试里没有 request（`integration_test_case.py:210-211` 每例都删 `frappe.local.request`），所以 `client` 恒为 `"unknown"`，断言实际比的是 `run()` 自己返回的值。读码推出的漏网变异有两个：M1 `ack` 里去掉 `"client"` 键，输出「回执页面 None」、`result['client']` 为 None，断言成立；M2 改成恒写 `"unknown"`、不再取 `request.host`，断言成立。FD-003「回执页面取页面的 Host」这个核心取值没有测试守着 | FD-043 意图（守住 FD-003 的输出）；开发守则「判据必须能区分」 | 在 `page_receives` 里调 `ack` 前设 `frappe.local.request = frappe._dict(host="192.0.2.10:8000")`（`test_closing_voucher.py:150-156` 已有同类写法，用完还原），然后断言 `result["client"] == "192.0.2.10:8000"`，输出含「回执页面 192.0.2.10:8000」 | 本Session修 | — | 待裁决 |
| P4-06 | 观察 | 登记册 SH-P1S5008 补句（`P1-S5-概况.md:124`）；方案 Part4 TS-015 第 2 步 | **补句给的两个出路都不好照做，新判据和演练命令也对不上。** ①「演练 bench 替换主 bench」在方案和 README 里都没有操作步骤，TS-015 第 6 步是删演练目录。②「改用 SH-P1S5007 ③ 的协议层探针」：③ 证明的是来源被**拒绝**，不是检查通过；要探演练 bench，它的 `bench socketio` 照样要占 9100，仍得先停主 bench。③ 判据「`socketio_port` 等于 `.env` 的 `SOCKETIO_PORT`」与 TS-015 第 2 步的命令对不上：命令没有 `-e SOCKETIO_PORT`，`setup.sh` 按缺省写 9100。`.env` 不是 9100 时这条判据必然不成立 | 流程规范 §12（登记描述须能照做）；FD-049 意图 | 补句改成「须先停主 bench 的 `start.sh`，在演练目录以 `bench start` 起服务后，在容器内用协议层探针以 `localhost` 来源握手、得到 sid；或改到换机器后的主 bench 上做」。另加一句：演练命令须补 `-e SOCKETIO_PORT="<.env 的值>"`（方案文本不改，在登记行里写明即可） | 延迟或不修（随 SH-P1S5008 唤醒） | 现在改登记描述，还是唤醒时再改 | 待裁决 |
| P4-07 | 观察 | `docker/scripts/setup.sh:111-114`（HEAD） | **校验放过前导 0。** `case ''|*[!0-9]*` 只拦空值和非数字。`0`、`99999` 先在 `up.sh:17` 的 `docker compose up -d` 报错（实测 `missing a target port`、`invalid containerPort`），到不了这里。`09100` 一路都能过：compose 把端口规整为 9100，nginx `listen 09100` 也能过 `nginx -t`（实测）。到 `set-config "09100" --parse` 时，`ast.literal_eval` 抛 `SyntaxError`，`setup.sh` 以 traceback 退出，没有给出「须是端口号」这句提示。会报错，不会静默出错 | FD-038 校验的本意（给出可读的报错） | `case` 加一条 `0*)` 分支，报同一句提示；或者用 `[ "$SOCKETIO_PORT" -ge 1 ] && [ "$SOCKETIO_PORT" -le 65535 ]` 并拒绝前导 0 | 延迟或不修 | — | 待裁决 |
| P4-08 | 观察 | 本机 `docker/.env:8-9`（不进 git） | **本机 `.env` 的注释还是 R9 以前的旧话**：「故默认用 9100。容器内仍是 9000。」README 现在让人「只改 `.env` 一处」，打开 `.env` 最先读到的就是这句错话。`.env.example` 已经改对，但 `up.sh:13` 只在 `.env` 不存在时才复制，已有的 `.env` 不会更新 | FD-038 意图；R9 FD-018（删掉「容器内仍是 9000」） | 由用户手工把本机 `.env` 第 8～9 行换成 `.env.example:8-10` 的注释（不改值） | 本Session修（用户本机文件，不进 git） | 由主会话改，还是交用户自己改 | 待裁决 |

## 本片盲区自述

- 没跑测试和变异。P4-05 的 M1、M2 漏网是读码推断，需要主会话实跑确认。
- 没在 9100 以外的端口上端到端通一次实时，没跑 `up.sh`。「改 `.env` 后照 README 能通」靠的是读码、`docker compose config` 渲染和配置哈希。frappe 不重建这一点用哈希比对确认过，但 `docker compose up -d` 的实际重建行为没有实跑。
- P4-03 只看了本机此刻的监听，组网网卡起来以后会多出哪些按网卡绑定的监听，没实测。Windows 防火墙规则（`netsh advfirewall`）也没查。
- `SOCKETIO_PORT` 与 `WEB_PORT`、`WATCH_PORT` 撞号这类情形，以及宿主保留段内的端口，没逐个渲染验证。
- P4-04 的「先到被读到」是读码推断，没实测两个页面同时回执时的情况。
- 定级拿不准：P4-01 定「低」，理由是照 README 做至少有一条命令必然报错。若按「报错显式、换个目录就能过」来看，可以降为观察。

## 需要主会话补跑的实测

1. **P4-05 变异**（读码已定，建议实跑确认）：M1 删掉 `realtime_check.py` `ack` 里的 `"client": …` 一行；M2 把它改成 `"client": "unknown"`。各跑 `test_realtime_check`，**预期**：6 例全过（漏网）。跑完按原字节还原。
2. **P4-01**（可选）：在仓库根依次执行 README `:210-211` 的两条命令。**预期**：第一条报 `no configuration file provided`。只渲染、不起容器的话，可以用 `docker compose config` 代替 `up -d`。
3. 其余各项不需要补跑。
