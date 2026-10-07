# F 复核分片报告 · 片 4（对象：R9 已修 FD-001／003／018／019／020 与延迟 FD-030／031／032 / 审核标准：R3 方案 Part4 SL-008～010、TS-013～016，B 需求 §4.8、AC-008／009）

**轮次**：P1-S5-R10｜**步骤**：F 复核分片 4｜**日期**：2026-10-07｜**执行者**：Claude 子 Agent（只读）
**依据**：[R3 开发方案 Part4](../R03-开发方案/P1-S5-R3-C开发方案-Part4.md)（全文）、[R9 F 审核报告](../R09-F审核/P1-S5-R9-F审核报告.md)（FD-001／003／018～020／030～032 行、当场修清单第 4、6、15～17、20 行）、[R9 Part4](../R09-F审核/P1-S5-R9-F审核报告-Part4.md)（全文）、Stage 概况（长效信息 #3／#4、登记册 SH-P1S5005～008）、`docs/项目概况.md:83,104`、`docs/业务规则.md`
**被审范围**：主仓库 `2fb2641..d7b89d6` 中的 `docker/scripts/setup.sh`、`docker/compose.yaml`、`docker/.env.example`、`docker/README.md`（结构、端口、异地终端访问各节）、Stage 概况登记册与长效信息；`frappe_china` `4b21aae..9d53d39` 中的 `frappe_china/realtime_check.py`（对照 `public/js/realtime_check.js`、`hooks.py:30`）

## 覆盖自证

**读全的**：分片通用说明；R9 Part4 全文；R9 收口报告里与本片相关的行（grep 定位后逐行读）；R3 方案 Part4 全文；两仓本轮 diff 中属于本片的文件（`.env.example`、README、compose、setup.sh、Stage 概况、项目概况、开发守则，以及 `realtime_check.py`）；`setup.sh` 全文（466 行）；`up.sh` 全文；`compose.yaml` 全文；`.env.example` 全文；`realtime-proxy/default.conf.template` 全文；README 第 75～230 行（结构、私有仓库末段、端口、异地终端访问、socketio 同号节）；`realtime_check.py` 与 `realtime_check.js` 全文。

**变异窗口**：主会话通知变异期间，`realtime_check.py` 改用 `git show HEAD:` 读。HEAD 版第 23～43、63～86 行与我先前读到的工作区内容逐字相同。收尾时 `git status --short` 两仓都为空。

**对照的上游与工具源码**（只读）：
- frappe `commands/utils.py:897-920`（`set-config`：`-g` 时写 `os.getcwd()/common_site_config.json`；`--parse` 走 `ast.literal_eval`）。
- `installer.py:666-708`（`_update_config_file` 只把 `"0"`／`"1"` 转成整数）。
- `app.py:543-547`（`ProxyFix` 只在 `--proxy` 或 `USE_PROXY` 时启用）。
- werkzeug `sansio.utils.get_host`（`request.host` 取 `Host` 头原值，非标准端口带端口号）。
- 容器内 bench 5.31.0：`cli.py:198-201`（`frappe_cmd` 先 `chdir` 到 `sites/` 再 exec `bench_helper frappe`）；`bench_command.commands` 里没有 `set-config`，所以这条命令会转给 frappe；`config/common_site_config.py:21-30,83-135`（`setup_config` → `make_ports`）；`bench.py:402-408`；`commands/socketio.py`。
- CRM `crm/www/crm.py:75`（`socketio_port` 取 `frappe.conf`）。

**只读查询与实验**：
- `common_site_config.json`：`"socketio_port": 9100`，是整数，不是字符串。`webserver_port` 8000，`default_site` 为 erx.localhost。
- 容器进程：`bench serve --port 8000`，不带 `--proxy`；`USE_PROXY` 为空；`socketio.js` 由 `bench socketio` 起。
- **临时实验**：在容器 `/tmp` 下建一个假的 `sites/`，只放 `apps.txt` 和 `common_site_config.json`。实验后已删，也顺带删了一个更早留下的空 `/tmp/tmp.*`。
  - 用 `bench_helper frappe set-config -g socketio_port 9100 --parse` 写入，得到整数 `9100`。
  - 去掉 `--parse` 写入，得到字符串 `"9100"`。
- **只读调用 `make_ports("/workspace/frappe-bench-drill")`**：得 `socketio_port 9101`、`webserver_port 8001`。原因是同级目录已有 `frappe-bench`，它取最大值加 1。新机器上没有同级 bench，缺省是 9000。
- `bash -n docker/scripts/setup.sh`：通过。
- 宿主 `netstat -ano`（只读）：在 `0.0.0.0` 和 `[::]` 上监听的端口逐个用 `tasklist` 查了进程。`docker ps` 查了端口映射。

**跳过的及原因**：
- 没跑测试，没跑 `run()`，没开浏览器，没停或重建任何容器（硬约束）。
- 没在真 bench 上重跑 `setup.sh` 第 2 段。它会写 `common_site_config.json`，虽然值不变，也算写。幂等性靠读码加临时目录实验来判。
- `configure_apps.py` 和 README「配置四个 App」节归片 3，本片只看了「结构」节里那一行。
- 外部终端、组网相关的项都已延迟，本片只核登记描述。

## R9 已修项复核

| R9 项 | 修于（当场／SB） | 定位（文件:行） | 落地 | 生效 | 原问题消失 | 说明 |
|---|---|---|---|---|---|---|
| FD-001 | 当场 | `docker/scripts/setup.sh:107-112`；登记册 SH-P1S5008（`P1-S5-概况.md:122`） | ✅ | ✅ | ⚠ 部分 | **生效**：第 2 段不在任何条件分支里，`up.sh` 每次都会执行到。cwd 是 `$BENCH_DIR`；bench 5.31.0 把 `set-config` 转给 frappe，并先 `chdir` 到 `sites/`，于是写的是 `sites/common_site_config.json`。临时实验证实 `--parse` 写成整数，不带它会写成字符串。现在的 bench 值已经是整数 9100，重跑结果不变（幂等）。<br>**原问题**：新机器缺省 9000、同机演练 9101，现在都被改写成 9100，「按缺省值重建会静默断连」这个问题已消失。<br>**没成立的部分**：R9 建议「端口从 `.env` 取，与 compose 同源」，实际写死了 9100，`up.sh` 也不把 `SOCKETIO_PORT` 传进容器。后果是：按 README 改端口的步骤，最后一步要重跑 `up.sh`，这一步会把站点配置改回 9100，又断一次。这是本轮修出的新问题，见 P4-01 |
| FD-003 | 当场 | `realtime_check.py:76-81`（HEAD）；README `:184`；登记册 SH-P1S5007 ③末句 | ✅ | ✅ | ⚠ 部分 | `client` 由 `ack()` 写入，值是 `frappe.local.request.host`（`:39`）。它等于页面请求的 `Host` 头原值：web 不带 `--proxy` 启动，`ProxyFix` 没启用；werkzeug 只在端口是 80／443 时去掉端口。所以本机访问是 `localhost:8000`，局域网终端访问是 `192.168.x.x:8000`，README 的说法与取值来源一致。两处小偏差：本机若用 `erx.localhost:8000` 或 `127.0.0.1:8000` 打开，显示的就是那个值；组网时显示组网地址，不是「局域网地址」。**判别力只有一个方向**：两边页面都开着时，回执会互相覆盖，以后写的为准，`run()` 每 0.5 秒查一次。看到终端地址能证明终端收到了；看到 `localhost:8000` 却证明不了终端没收到。README 写的「或看回执页面」没说清这一点，见 P4-03 |
| FD-018 | 当场 | `compose.yaml:53-54`；`.env.example:8-10`；README `:79,94-95` | ✅ | — | ⚠ 部分 | ① `.env.example` 删掉了「容器内仍是 9000」（错误说法），改成「也监听 9100」，属实；「只改这一项会断连」也属实：宿主发布端口变了，浏览器仍按 `socketio_port`＝9100 去连。② README「结构」节：compose 的五个服务、`docker/` 下全部条目都列上了，已逐项对过目录。③ **「三处」在三份文档里指的不是同一组**：compose 注释写「站点配置、下方 ports、模板」，`.env.example` 写「本项、站点配置、模板」，README 写「站点配置、compose ports、模板（listen 与 proxy_pass）」。三份都没把 `setup.sh` 算进去，而它现在也写死了 9100。compose 注释在 `frappe` 服务的 `ports` 上方，「下方 ports」最先读到的是 `frappe` 自己的端口，而那里并没有实时端口。见 P4-01 |
| FD-019 | 当场 | README `:191`；登记册 SH-P1S5005 | ✅ | — | ⚠ 部分 | `netstat -ano | findstr LISTENING` 的本地地址列能区分 `0.0.0.0` 和 `127.0.0.1`，命令可用。本次只读实测，LiteLLM 的 `7999` 和 `5432` 确实由 `com.docker.backend.exe` 在 `0.0.0.0`／`[::]` 上发布，清单点名属实。**但清单没列全**：`0.0.0.0` 上还有 `445`（SMB）、`135`／`49664-49667`（RPC）、`1666`（`p4s.exe`，Perforce 服务）、`1688`（`kms-server.exe`）、`1714`／`1715`（`hserver`／`sesinetd`）、`2179`（`vmms`）、`5040`、`7680`、`10366`、`23130`／`23132`（Wacom）、`27036`（Steam）、`51010`（SamsungDeX）、`56319`（spoolsv）。另外只说了 `0.0.0.0`，没提 IPv6 的 `[::]`，而 Docker 发布的端口两种都有。见 P4-02 |
| FD-020 | 当场 | 登记册 SH-P1S5007 ①～⑤（`P1-S5-概况.md:121`） | ✅ | — | ✅ | ① SL-008 ⑥ 终端侧与 TS-013 截图，与方案 TS-013 第 7 步、验证方式一致。② 要恢复直通映射，必须改 `frappe` 服务的 `ports`、重建容器，重建后字体会丢（与 README `:214-215` 一致）。③ 协议层探针替代做法与 R9 Part4 覆盖自证里的实测描述一致。④⑤ 见下一节 |

## 延迟／不做项登记核对

| R9 项 | 裁决去向 | 登记位置 | 描述与实情一致否 | 说明 |
|---|---|---|---|---|
| FD-030 | 延迟，并入 SH-P1S5007 ④ | `P1-S5-概况.md:121` | ✅ | HEAD `:84-85` 的 `finally` 无条件删键；`ack` 的 `:28-29` 在键不存在时 `frappe.throw` 英文文案，没有用 `_()`，`frappe.call` 默认会弹报错框。描述与代码一致。另有一个登记里没写的触发途径：两边页面都开着、`run()` 已返回时，后到的那个回执同样会弹报错框（与 P4-03 相关） |
| FD-031 | 延迟，并入 SH-P1S5007 ⑤ | 同上 | ✅ | 模板 `:16` `proxy_pass http://frappe:9100`，没有 `resolver`，描述属实，也标了「读码推断」。补充一点：这件事不只在 SH-P1S5007 的实测里会碰到，README `:214` 改端口步骤里的 `docker compose up -d`、IT-028 那种重建都会碰到，但只登记在 SH-P1S5007，没回写 README。这与「延迟」裁决一致，不另立项 |
| FD-032 | 延迟，记进长效信息 #3 交 S7 | `P1-S5-概况.md:106` | ✅ | `hooks.py:30` 只有 `app_include_js`，只在 desk 页加载；`crm/www/crm.py:75` 用的是同一个 `socketio_port`，「也走 9100」成立。描述属实。去向有个风险：路线文档 v1.7 已经记了「长效信息 #2～#4 已移交」，R9 往 #3、#4 里追加的 FD-027／032／002 还不在路线文档里（grep `debug_mode`、`FD-032` 都是 0 条），Stage 收口时容易被当成已移交而漏掉，见 P4-05 |

## 业务规则合规核

| 规则条款 | 本轮改动是否涉及 | 结论 | 备注 |
|---|---|---|---|
| BR-001 小企业会计准则 | 否 | 合规 | 本片改动只涉及端口配置、连通检查输出和文档 |
| BR-002 报表构成 | 否 | 合规 | — |
| BR-003 增值税税率 | 否 | 合规 | — |
| BR-004 未交增值税结转 | 否 | 合规 | — |
| BR-005 附加税 | 否 | 合规 | — |
| BR-006 资产负债表恒等 | 否 | 合规 | — |
| BR-007 价税分离 | 否 | 合规 | — |

## 集成点登记（交接摘要）

- **本片依赖**：
  - 片 1：`setup.sh` 第 2 段是本片 FD-001 的落点。片 1 若在 `setup.sh` 里查到别的改动（如第 3 段预检），请确认没动第 2 段、`up.sh` 传进容器的环境变量也没变。若裁决 P4-01 取「同源」，要改 `up.sh`、`compose.yaml`（给 `realtime-proxy` 加 `SOCKETIO_PORT`）、模板、`setup.sh` 四个文件，与片 1 的范围重叠。
  - 片 3：README `:94`「配置四个官方 App」的说法（见 P4-06），请片 3 一并看。
- **本片暴露**：
  - `run()` 通过时打印的格式为 `实时通道检查：通过（N ms，回执用户 U，回执页面 H）`，返回值字段没变（`{ok, token, latency_ms, acked_by, client}`）。若有测试或脚本解析这行输出（没查到这样的代码），它们要跟着改。
  - `common_site_config.json` 的 `socketio_port` 由 `setup.sh` 每次 `up.sh` 都强制写成 9100。任何手工改这个值的做法，下次跑 `up.sh` 都会被覆盖回去。
  - 在同一容器里另建 bench 目录做演练时，bench 会把 `webserver_port` 定为 8001，`socketio_port` 先定为 9101，随后被 `setup.sh` 改成 9100（见 P4-04）。

## 自证复核

| 被审产物声称（R9 报告／SB 回执／文档） | 实际复核 | 一致否 |
|---|---|---|
| 当场修清单第 4 行：`setup.sh:107-110` 加 `set-config … 9100 --parse` 并注明三处同号 | 在 `:107-112`，内容一致 | 一致；但 FD-001 建议里的「端口从 `.env` 取，与 compose 同源」被悄悄去掉了，清单与裁决栏都没说明这一偏离（P4-01） |
| `setup.sh:107-108` 注释：「bench init 缺省写 9000」「compose 的 realtime-proxy 与模板都按 9100 写死」 | 新机器上是 9000；同级目录已有 bench 时是 9101（`make_ports`）。compose 宿主侧取的是 `${SOCKETIO_PORT:-9100}`，不是写死的，只有容器侧 9100 写死 | 部分不一致（措辞，并入 P4-01） |
| 第 6 行：`realtime_check.py:76-81` 打出回执页面 | HEAD `:76-81` 一致；`client` 来自 `request.host` | 一致 |
| README `:184`：「本机是 `localhost:8000`，终端是 `<局域网地址>:8000`」 | 取值来源一致；判别只在一个方向成立 | 部分一致（P4-03） |
| 第 15 行：compose、`.env.example`、README 结构三处 | 都落地了；「三处」所指不统一 | 部分一致（P4-01） |
| 第 16 行：准备清单 ② 点名 7999／5432 | 点名属实；实测还有十多个 `0.0.0.0` 监听没点到 | 部分一致（P4-02） |
| 第 17 行：SH-P1S5007 ①～⑤ | 逐条对过代码与 README | 一致 |
| SH-P1S5008 判据：「重建后 `socketio_port` 为 9100（整数）……且本机实时通道检查通过」 | 前半句可以静态核；后半句按方案 TS-015 的演练方式（同一容器、另一 bench 目录）没法直接做 | 部分可执行（P4-04） |
| `.env.example:10`、compose 注释：「只改这一项会断连」 | 读码属实（浏览器按站点配置的 9100 去连宿主） | 一致 |

## 问题清单

| # | 严重程度 | 定位 | 问题描述 | 违背的标准／意图 | 建议 | 建议档位 | 待裁决点 | 状态 |
|---|---|---|---|---|---|---|---|---|
| P4-01 | 中（中／低边界） | `docker/scripts/setup.sh:107-110`；`docker/up.sh:35-46`（不传 `SOCKETIO_PORT`）；`docker/README.md:205-216`；`compose.yaml:53-54`；`.env.example:10` | **修复写死了 9100，README 的改端口步骤因此走不通。** README 要求先 `set-config socketio_port <新值>`，最后「`docker/up.sh` 重建容器后必跑」（`:215`）。`setup.sh` 第 2 段每次都执行，会把它改回 9100。结果是浏览器按 9100 去连，而宿主发布的已是新端口，实时通道又静默断开，正是 FD-001 要消除的那种症状。同时，三份文档列的「三处」不是同一组（compose：站点配置、下方 ports、模板；`.env.example`：本项、站点配置、模板；README：站点配置、compose ports、模板），哪份都没提 `setup.sh`。compose 注释写在 `frappe` 服务的 ports 上方，「下方 ports」容易被读成 `frappe` 服务的端口。R9 的建议本来是「端口从 `.env` 取，与 compose 同源」，这次落地没照做，也没说明为什么 | FD-001 建议原文；AC-008；开发守则「判据必须能区分」（文档引导人改错地方） | (a) 同源：`up.sh` 加 `-e SOCKETIO_PORT`；`setup.sh` 用 `"${SOCKETIO_PORT:-9100}"`；compose 给 `realtime-proxy` 加 `SOCKETIO_PORT` 环境变量，模板 `proxy_pass` 改为 `http://frappe:${SOCKETIO_PORT}`。这样只改 `.env` 再跑 `up.sh`（并重建 proxy）就能换端口，三份文档统一改成「只改 `.env`」。(b) 保留写死：README、compose 注释、`.env.example` 统一列出同一组地方，并把 `setup.sh:110` 列进去 | 本Session修 | 取 (a) 还是 (b)；(a) 要动 `up.sh`／compose／模板，须 `bash -n` 并在现有 bench 上重跑一次第 2 段（写入值不变） | 待裁决 |
| P4-02 | 低 | `docker/README.md:191`（准备清单 ②）；登记册 SH-P1S5005 | 清单点名的端口不全。宿主 `netstat -ano` 只读实测，`0.0.0.0` 上除了本项目和 LiteLLM，还有 `445`（SMB，PID 4）、`135`／`49664-49667`（RPC）、`1666`（`p4s.exe`，Perforce 服务）、`1688`（`kms-server.exe`）、`1714`／`1715`（`hserver.exe`／`sesinetd.exe`）、`2179`（`vmms.exe`）、`5040`、`7680`（svchost）、`10366`（services.exe）、`23130`／`23132`（Wacom）、`27036`（Steam）、`51010`（SamsungDeX）、`56319`（spoolsv）。「逐个判」这句是有的，但后面「从终端探测：……应该不通」只列了 7 个端口，照着打勾会以为查全了。另外 `[::]` 上的监听没提，Docker 发布的端口两种都有，组网客户端会分配 IPv6 地址。能否真的访问到，还取决于 Windows 防火墙，清单没把它列为判据 | AC-009「只有页面与实时两条可达」；LG-008 | 清单 ② 改为：`netstat -ano \| findstr LISTENING` 中凡本地地址为 `0.0.0.0` 或 `[::]` 的都要判；从终端扫组网地址的全部端口（如 `nmap -p-`），只应见 8000、9100。点名清单只作举例，不作判据。SH-P1S5005 同步补一句 | 本Session修（文档）或延迟到 SH-P1S5005 唤醒时 | 现在改文档，还是并入 SH-P1S5005 唤醒时再定 | 待裁决 |
| P4-03 | 低 | `docker/README.md:184`；登记册 SH-P1S5007 ③末句；`realtime_check.py:33-41,64-68`（HEAD） | 「或看『通过』那行的『回执页面』」只在一个方向上能下结论。本机与终端都以同一用户开着页面时，两个 `ack` 都会写同一个键，以后写的为准；`run()` 每 0.5 秒才查一次，显示哪个地址取决于先后。显示终端地址，能证明终端收到了；显示 `localhost:8000`，证明不了终端没通。若 `run()` 已经返回、键已删掉，后到的那个回执还会在页面上弹英文报错框（FD-030 的又一个触发途径）。README 现在的写法会让人看到 `localhost` 就判「终端不通」，或反过来把一次本机回执当成终端通过 | 开发守则「判据必须能区分它要区分的两种情形」；FD-003 的意图 | README 与 SH-P1S5007 的写法改为：「回执页面为终端地址才算终端通过；为本机地址时不能下结论，关掉本机页面后重测」。同时注明组网时显示的是组网地址 | 本Session修 | — | 待裁决 |
| P4-04 | 观察 | 登记册 SH-P1S5008 新增判据（`P1-S5-概况.md:122`）；方案 Part4 TS-015 第 2 步 | 新增判据「且本机实时通道检查通过」，按 TS-015 的演练方式没法直接做。演练在同一容器的 `frappe-bench-drill/` 里进行，`make_ports` 给它定 `webserver_port` 8001（只读调用实测），compose 没发布这个端口；它的 `socketio_port` 被 `setup.sh` 改成 9100，与主 bench 的实时服务抢同一个端口。在开发模式下，实时服务鉴权时按 `webserver_port` 回访页面端口。要在演练目录跑检查，得先停主 bench，用 8000 起演练目录的 web，或者改它的 `webserver_port`。判据没写这些 | 流程规范 §12（登记描述须能照做）；开发守则「判据必须能区分」 | 判据拆成两条：①静态核 `socketio_port` 为整数 9100（任何时候都能核）；②实时通道检查写明前置条件（停主 bench、演练目录以 8000 起 web），或改到「换机器后的主 bench」上做 | 延迟或不修（随 SH-P1S5008 唤醒） | 是否现在改登记描述 | 待裁决 |
| P4-05 | 观察 | Stage 概况长效信息 #3、#4（`P1-S5-概况.md:106-107`）；路线文档 v1.7（`路线文档.md:23`） | R9 往 #3 加了 FD-027、FD-032，往 #4 加了 FD-002，都还不在路线文档里（grep `debug_mode`、`FD-032` 都是 0 条）。路线文档 v1.7 的版本记录写的是「长效信息 #2～#4 已移交」，Stage 收口时容易被当成已经移交过。这本身符合「收口时才移交」的做法，不算错 | 流程规范 §4.3（长效信息去向） | 收口时按 #3、#4 的现状再移交一次；或者现在在 #3、#4 的追加部分标「未移交」 | 延迟或不修 | — | 待裁决 |
| P4-06 | 观察 | `docker/README.md:94`（本轮新加的「结构」节条目） | 「配置四个官方 App（CRM 集成、Raven bot 与工具）」：脚本只配 CRM 和 Raven（`configure_apps.py` 只有 `configure_crm`／`configure_raven`／`ensure_bot_and_functions`），HRMS、Insights 不经它配置。括号里写得对，「四个」说多了。这个说法沿用的是 README 原有的「## 配置四个 App」标题 | FD-018 的意图（结构节与实情一致） | 改为「配置官方 App（CRM 集成、Raven bot 与工具）」，标题一并改；交片 3 统一处理 | 延迟或不修 | — | 待裁决 |

## 本片盲区自述

- 没跑测试，没跑 `run()`，没开浏览器，没重跑 `setup.sh`，没停或重建容器。「`setup.sh` 第 2 段在真 bench 上幂等」「改端口后跑 `up.sh` 会被改回 9100」两条都是读码加临时目录实验推出的，没在真 bench 上复现。P4-01 后果链的后半段（浏览器去连哪个端口），沿用的是 R9 Part4 已核过的上游读码（`boot.py`、`socketio_client.js`），本轮没重读。
- P4-03「两次 ack 先后不定」是读码推断。实际上本机页面的回执多半先到，但会不会被终端的回执覆盖，取决于轮询的时间点，没实测。
- P4-02 只列了本机此刻的监听情况。演示时宿主上开着哪些程序会变，Windows 防火墙对组网网卡的规则也没查（`netsh advfirewall` 本轮没跑）。
- 没细查 README「配置四个 App」节、`configure_apps.py`（归片 3），也没查 `lock-apps.sh`（归片 1）。
- 定级拿不准：P4-01 定「中」，是因为它是本轮修复新带进来的，而且照 README 做一定会断连。但只有在用户真要换实时端口时才会碰到，默认配置下不受影响，若按这一点看可以降为「低」。

## 需要主会话补跑的实测

1. **P4-01 复现**（可选，要写测试 bench 配置）：在测试环境的 `common_site_config.json` 里先把 `socketio_port` 设为 9200（带 `--parse`），再跑一次 `setup.sh` 第 2 段，或者直接跑 `bench set-config -g socketio_port 9100 --parse` 模拟。**预期**：值回到 9100。复现完把值还原为 9100。不复现也行，读码已经确定。
2. **P4-03**（随 SH-P1S5007 实测时做）：本机与终端同时以 Administrator 开着桌面页，连跑三次 `run()`，记下每次的「回执页面」。**预期**：多数时候显示 `localhost:8000`；终端偶尔会弹英文报错框（FD-030）。
3. 其余各项不需要补跑。
