# 开发环境（Docker）

Frappe v16 + ERPNext v16 的容器化开发环境（分支与 commit 见 `apps.json`）。宿主机只需 Docker，其余依赖全在容器里。

## 日常用法

| 做什么 | 跑什么 |
|---|---|
| 首次搭建 / 起容器 | `docker/up.sh` |
| 启动开发服务器 | `docker/start.sh`，然后开 http://localhost:8000 |
| 进容器跑 bench 命令 | `docker/shell.sh` |
| 停容器（数据保留） | `docker/down.sh` |
| 备份站点数据 | `docker/backup.sh` |
| 恢复站点数据 | `docker/restore.sh`（最新一套）／`docker/restore.sh <时间戳>`（指定一套，子目录里的也找得到） |
| 建公司 + 演示数据 | `docker/seed-demo.sh` |
| 清除演示数据 | `docker/seed-demo.sh --clear` |
| **只补 v16 初始化，不建公司不导演示数据** | `docker/seed-demo.sh --bare` |
| 改界面语言 / 默认公司 | `docker/set-locale.sh` |
| **抹掉全部数据重来** | 见下方「重装站点」节——**不是单跑 reinstall，有三个坑** |
| 删容器与数据 | `docker/down.sh --purge` |

登录：`Administrator` / `admin`（密码在 `.env` 的 `ADMIN_PASSWORD`）。

## 新站点为什么界面是空的

`bench new-site` 建出的站点没有公司、会计年度和业务数据，而 ERPNext 的销售/采购/库存/会计模块都依赖这些，所以界面看着比官方演示图简陋得多。跑 `docker/seed-demo.sh` 建公司并导入 ERPNext 自带的演示数据（商品、客户、订单）即可。

公司信息在 `.env` 里改（`COMPANY_NAME` 等）。**含空格的值必须加引号** —— 脚本用 `. ./.env` 载入，不加引号会被当命令执行。

注意 `bench new-site` 会把 `setup_complete` 置为 1，导致 frappe 的 `setup_complete()` 开头就 `if frappe.is_setup_complete(): return` 而静默跳过建公司。故 `seed-demo.sh` 直接建 Company 与 Fiscal Year，不走向导。

## 界面语言与「没有权限」

```bash
docker/set-locale.sh                  # 切中文（.env 的 UI_LANGUAGE，默认 zh）
UI_LANGUAGE=en docker/set-locale.sh   # 切回英文
```

改完按 Ctrl-Shift-R 强制刷新浏览器。

**打开演示单据报「没有权限」多半不是角色问题。** `setup_demo_data()` 会建一个 `(Demo)` 后缀的副本公司，把全部演示单据放在它名下；默认公司若仍指主公司，ERPNext 的跨公司数据隔离会把取不到记录报成权限错误。`set-locale.sh` 会把默认公司对齐到演示数据所在那家；也可显式指定：

```bash
DEFAULT_COMPANY="ERX Demo" docker/set-locale.sh
```

也可以直接在界面里切换当前公司，不必改默认值。

## 换电脑

新电脑只要有 Docker 即可，**不需要装 Python、Node、MariaDB、Redis 或 bench**。

搬迁前在原机器上备份：

```bash
docker/backup.sh          # 备份落在 docker/backups/，随文件夹一起走
docker/save-images.sh     # 仅当新电脑没网时需要（导出约 4.5GB 镜像）
```

拷走整个项目文件夹，在新电脑上：

```bash
docker/load-images.sh     # 仅当没网时需要
docker/up.sh              # 起容器 + 重建 bench 与站点（首次约 10-20 分钟）
docker/restore.sh         # 恢复你的数据
docker/start.sh
```

有网时不需要 save/load —— `up.sh` 会自己 `docker pull`。

**为什么需要 backup/restore**：数据库与 Redis 用 Docker named volume 存（性能远好于 bind mount），而 named volume 存在 Docker 内部、不在项目文件夹里，拷不走。`up.sh` 能重建一个干净环境，但你录入的数据要靠备份带走。

bench 代码、apps、站点文件是 bind mount，本来就在项目文件夹里，直接跟着走。

## 结构

```
docker/
├── compose.yaml        服务定义（mariadb / redis×2 / frappe / realtime-proxy）
├── .env                本机配置（端口、密码），不进 git
├── .env.example        模板
├── up.sh               起容器 + 首次搭建（幂等）
├── start.sh            bench start
├── shell.sh            进容器
├── down.sh             停容器
├── backup.sh           备份到 backups/
├── restore.sh          从 backups/ 恢复（可带时间戳参数）
├── seed-demo.sh        建公司 + 导演示数据
├── set-locale.sh       设界面语言与默认公司
├── lock-apps.sh        把各 app 当前 commit 写进 apps.json
├── save-images.sh      导出镜像供离线迁移
├── load-images.sh      导入镜像
├── apps.json           装哪些 app、哪个分支、锁到哪个 commit
├── configure-apps.sh   配置四个官方 App（CRM 集成、Raven bot 与工具）
├── realtime-proxy/     实时端口前的转发层配置（nginx 模板）
├── scripts/            容器内执行的逻辑（由上面的脚本调用）
├── backups/            备份文件，不进 git
└── images/             导出的镜像，不进 git
frappe-bench/           bench 本体（首次 up.sh 时生成），整个不进 git
```

容器内 `/workspace` 就是项目根。

## 源码在哪、怎么管版本

遵循 frappe_docker 官方模型：**bench 自己 clone 各 app，`frappe-bench/` 整个不进主仓库版本管理**（官方文档原话："The `development` directory is ignored by git"）。

```
frappe-bench/apps/frappe     ← 独立 git 仓库
frappe-bench/apps/erpnext    ← 独立 git 仓库
frappe-bench/apps/<自有app>  ← bench new-app 建的，同样独立
```

每个 app 各自是完整仓库，remote 分工：

| remote | 指向 | 用途 |
|---|---|---|
| `origin` | 自有 fork | 推改动 |
| `upstream` | 官方 | 只读拉更新（push URL 已设为无效值防误推） |

所以改源码、commit、push、合并上游都在那三个目录里各自进行，主仓库的 `git status` 看不到它们。

**版本记录**：`apps.json` 记 url + `branch` 或 `tag` + commit + `app_name`；文件顺序就是安装顺序。`official: true` 表示直接使用官方仓库，重建时只保留只读 `upstream`；`tag` 与 `branch` 二选一，`tag` 优先。合并上游或确认版本可用后跑 `docker/lock-apps.sh` 更新它，换机器时 `up.sh` 按它对齐（用 `reset --hard`：`branch` 条目仍停在该分支上；`tag` 条目克隆出来就是 detached HEAD，对齐后仍是）。**不会丢代码的两条保护**：有未提交改动时跳过；HEAD 上有锁定值不含的提交（你刚 commit、还没跑 `lock-apps.sh`，或两边分叉）时也跳过，并列出这些提交——是新版本就跑 `lock-apps.sh`，确实要退回就照提示手动 `reset`。只有本次刚克隆的、或 HEAD 只是落后于锁定值时才自动对齐。**锁不上会中止 `up.sh`**：本地没有锁定的 commit 就按 SHA 去远端取（浅克隆只取这一个，完整克隆不会被变成浅克隆），取不到即退出并打出 git 的原话——多半是代理、凭据，或那个 commit 没推送。

`app_name` 是该 app 在 `frappe-bench/apps/` 下的**目录名**，不一定等于仓库名：`bench get-app` 会按 app 的 `pyproject.toml` 把目录改名（仓库 `FrappeChina` → 目录 `frappe_china`）。`setup.sh` 靠它判断 app 是否已经装好；缺了这个字段，重跑 `up.sh` 会再克隆一次并在改名时中止。`lock-apps.sh` 会自动写入它；手工往 `apps.json` 加 app 时也要写上。`apps.json` 的顺序就是安装顺序（`setup.sh` 不让 bench 自己解析依赖），新 app 加在末尾。

### 私有仓库

`frappe_china` 的仓库（`PhilixKuro/FrappeChina`）是私有的。容器里没有你宿主机的 git 凭据，`up.sh` 在新机器上克隆它时会报「容器内访问不了…」并停下。给容器配一次凭据再重跑 `docker/up.sh`：

```bash
docker/shell.sh
git config --global credential.helper store
printf 'https://<GitHub 用户名>:<个人访问令牌>@github.com\n' > ~/.git-credentials
chmod 600 ~/.git-credentials
exit
docker/up.sh
```

令牌在 GitHub「Settings → Developer settings → Personal access tokens」生成，只需该仓库的 Contents 只读权限。凭据存在容器的家目录里，`down.sh` 删掉容器后会丢失，重建后再配一次即可。**凭据文件不在项目目录内，不会进 git。**

**在 VS Code 里看这三个仓库的改动**：`.vscode/settings.json` 已用 `git.scanRepositories` 显式列出（它们在 gitignore 内，编辑器默认不扫）。源代码管理面板会并列显示主仓库、frappe、erpnext。新增自有 app 后在那里追加一行。

**自己要排除的临时文件**写进该仓库的 `.git/info/exclude`，别改上游的 `.gitignore`——那是上游文件，改了会成为每次合并的冲突点。

## 端口

| 用途 | 宿主机 | 由谁发布 | 容器内 |
|---|---|---|---|
| Frappe web | 8000 | `frappe` 服务 | 8000 |
| Realtime (socketio) | 9100 | **`realtime-proxy` 服务**（nginx，转发到 `frappe:9100`） | **9100**（两侧同号） |
| 资源监视／另起测试站服务 | 6787，**只绑 `127.0.0.1`** | `frappe` 服务 | 6787 |

**为什么实时端口前多一层转发**（S5 LG-007、需求 §4.8）：实时服务按请求的来源认站点，本机名（`localhost`、`127.0.0.1`、`*.localhost`）认得出，局域网地址、组网地址认不出，连接会被拒（`Invalid namespace`）。`realtime-proxy` 对非本机名来源补一个 `X-Frappe-Site-Name` 请求头，值取 `.env` 的 `SITE_NAME`；本机来源原样透传。规则不写任何具体地址，局域网与组网走同一条分支。配置在 `realtime-proxy/default.conf.template`，官方镜像启动时用 `envsubst` 渲染。不改上游源码。

Windows 上 9000 常落在 Hyper-V 保留端口段（本机实测 8995-9094），故 socketio 用 9100。查保留段：

```bash
netsh interface ipv4 show excludedportrange protocol=tcp
```

### 异地终端访问

#### 局域网

1. 在宿主查本机局域网地址：`ipconfig`（Windows），取当前网卡的 IPv4 地址。
2. 终端浏览器访问 `http://<本机局域网地址>:8000`，登录后打开任意桌面页面。实时连接由 `realtime-proxy` 转发，不用改配置。
3. 终端连页面都打不开时，多半是 Windows 防火墙拦了入站。是否为 8000、9100 加入站规则属本机安全设置，自己决定。

#### 组网（外网）

1. 本机与终端各装组网客户端（DEC-021 选的 Tailscale），登录同一网络。
2. 终端访问 `http://<本机组网地址>:8000`。`realtime-proxy` 的规则对组网地址同样生效，不用改配置。
3. 外网实测尚未做（延迟需求 `SH-P1S5005`）。实测前先做完下面的「准备清单」。

#### 连通检查

```bash
docker compose exec -T -w /workspace/frappe-bench frappe \
  bench --site erx.localhost execute frappe_china.realtime_check.run \
  --kwargs '{"user":"Administrator","timeout":30}'
```

本机发一条只供本检查的事件给 `user`，终端页面收到后弹出提示「实时通道检查已收到」，并经页面通路回执。在 `timeout` 秒内收到回执，返回 `ok: true` 并打印「通过」；否则返回 `ok: false` 和原因并打印「失败」。检查只认用户、不认终端地址：本机若以同一用户开着桌面页，终端不通也会报通过。测终端时本机不要以该用户开桌面页，或看「通过」那行的「回执页面」——本机是 `localhost:8000`，终端是 `<局域网地址>:8000`。

**失败时先查**：终端是否以 `user` 登录，并且正打开着一个桌面页。没有打开的页面同样会报失败，这不代表实时通道不通。

#### 外网实测前的准备清单（按顺序）

1. **改管理员口令**为非缺省值：`docker compose exec -T -w /workspace/frappe-bench frappe bench --site erx.localhost set-admin-password '<新口令>'`。新口令只记在 `docker/.env` 的 `ADMIN_PASSWORD`，不进 git。
2. **只开两个端口**：在宿主 `netstat -ano | findstr LISTENING` 列出全部监听 `0.0.0.0` 的端口逐个判，不只看本项目的——同机的 LiteLLM（`7999`）与它的 postgres（`5432`）也监听 `0.0.0.0`，组网后同样对网内设备可达。再从终端探测：`8000`、`9100` 应该通，`6787`、`3306`、`6379`、`7999`、`5432` 应该不通。
3. **组网客户端只在演示时段开**。
4. **页面能开而连通检查失败**：按下面的「已知待验点」逐条查。

#### 已知待验点（LG-013，外网实测时验）

- **国内能否稳定连上**组网服务。
- **容器能否以组网地址回访本机页面端口**：实时服务鉴权时，会按请求来源回访页面端口（`realtime/utils.js`）。回访不通时的备用做法：终端改用组网提供的本机主机名访问，再在 `compose.yaml` 的 `frappe` 服务加 `extra_hosts: ["<该主机名>:host-gateway"]`，让容器把这个主机名解析到宿主。
- **Windows 防火墙**是否对组网网卡放行 8000、9100。

### ⚠ socketio 端口必须两侧同号，且与站点配置一致

**`socketio_port` 这一个值同时管两头**：容器内 `realtime/index.js` 据它 `listen`；浏览器经 `boot.py` → `frappe.boot.socketio_port` → `socketio_client.js` 据它拼连接 URL。**浏览器连的是宿主，用的却是站点配置里的端口号**，所以 `realtime-proxy` 发布的宿主端口必须与该配置同号，否则浏览器会去连一个没人监听的宿主端口。

**改 socketio 端口要同时改三处**（只改一处，realtime 会静默断连——不报错，只是界面再也不自动更新）：

```bash
# 1. 站点配置（--parse 不可省，否则写成字符串 "9100" 而非整数）
docker compose exec -T -w /workspace/frappe-bench frappe   bench set-config -g socketio_port 9100 --parse

# 2. compose.yaml 的 realtime-proxy 服务：ports 改成同号
#    - "${SOCKETIO_PORT:-9100}:9100"
# 3. realtime-proxy/default.conf.template：listen 与 proxy_pass 的端口一起改
docker compose up -d     # 端口映射变更须重建容器
docker/up.sh             # 重建容器后必跑：中文字体与 pdftotext 装在容器里，重建即丢（P1-S5-R5 IT-028）
```

**自查是否断连**：浏览器按 F12 打开 Console，若反复出现 `socketio_client.js` 的 `ERR_CONNECTION_REFUSED` 与 `xhr poll error`，就是端口没对上。

```bash
# 宿主侧该通（须先 docker/start.sh；bench start 没跑时 nginx 回 502）
curl -s -o /dev/null -w '%{http_code}\n' "http://localhost:9100/socket.io/?EIO=4&transport=polling"   # 期望 200
# 容器内监听端口
docker compose exec -T frappe bash -c 'netstat -tlnp | grep 9100'
```

**最直接的验法**：开两个浏览器标签，打开同一张单据。在其中一个里改字段并保存，另一个应自己更新。

**曾经踩过**：环境从 v15 时期起，compose 映射一直是 `9100:9000`，而站点配置是 `9000`，所以 realtime 全程断连、界面从不自动刷新。P1-S1 的全部实操都是在这个状态下做的（P1-S2-R1 第 15、16 步查明并修复）。

## 配置四个 App

`docker/configure-apps.sh` 把 CRM 集成、Raven 连接、演示 bot 和 15 条只读工具配到站点上。各段可重复跑，某个 App 没装时跳过该段。

**何时跑**：站点装完四个 App 之后（新机器 `up.sh` 后、演示站接入后、重建测试站后）。

**先在 `docker/.env` 填三个值**（`.env` 不进 git，`.env.example` 只有键名）：

| 键 | 用途 |
|---|---|
| `RAVEN_LLM_URL` | LiteLLM 的 OpenAI 兼容地址，如 `http://host.docker.internal:7999/v1` |
| `RAVEN_LLM_KEY` | LiteLLM 密钥（不写进任何文档、日志） |
| `RAVEN_LLM_MODEL` | bot 用的模型别名。不填时 bot 的 `model` 是 Raven 自带缺省 `gpt-4o`，接 LiteLLM 时会拿它去请求，故须与 `URL`／`KEY` 一起填 |

三个值都不填也能跑：CRM、bot 与工具照配，Raven Settings 的连接字段跳过并打一行说明（LiteLLM 实测是延迟需求 SH-P1S5006）。`URL` 与 `KEY` 只填一个时报错退出。

**用法**（宿主上跑，自动载入 `.env`）：

```bash
docker/configure-apps.sh                                   # 站点取 .env 的 SITE_NAME
docker/configure-apps.sh --site test.localhost
docker/configure-apps.sh --site erx.localhost --company 华东弹簧有限公司
```

- `--company` 是 CRM 生成报价单时用的公司，填公司全名（`HDTH` 是缩写，按缩写查不到）。缺省取站上唯一一家「小企业会计准则(2024)」公司；零家或多家时报错，要求显式传。
- 除 CRM 集成本身，还会把 `CRM Settings.enable_frappe_crm_data_synchronization` 置 1：不开它，CRM 由 Deal 建客户时报错（`validate_frappe_crm_sync`），销售漏斗那条链走不通。
- 输出逐字段列出「旧值 → 新值」；密钥只报「已改」，不打印值。第二次跑输出「无改动」。
- 站上已有本脚本 15 条之外的写数据类 Raven 工具（建、改、删、提交等）时报错退出，不删它，交人处理。
- 实际逻辑在 `docker/scripts/configure_apps.py`（容器内、`sites/` 目录下运行）。

## 版本与解释器

本环境用 **ERPNext / Frappe v16**（分支与 commit 见 `apps.json`）。

镜像 `frappe/bench:latest` 自带 Python 3.12 / 3.14 与 Node 22 / 24，两套分别服务两个大版本：

| | 声明的要求 |
|---|---|
| frappe v15 | `requires-python = ">=3.10,<3.15"`，`node >= 18` |
| frappe v16 | `requires-python = ">=3.14,<3.15"`，`node >= 24` |

v16 **强制** Python 3.14，故 `setup.sh` 锁 3.14.7。`bench init` 不读 `PYENV_VERSION`，须显式传 `--python`，否则由它自行挑选。

## Windows 上的几处适配

脚本里有几段专为 Windows + Docker Desktop 环境而写，注释已就地说明原因，**别当冗余删掉**：

| 现象 | 原因 | 处理 |
|---|---|---|
| `Connection was reset` / 连不上 GitHub | 宿主机 git 用 libcurl、不读注册表里的系统代理，流量绕过 Clash 直连 | 每个仓库各自 `git config http.https://github.com/.proxy`（`.git/config` 独立，换机器须重配） |
| `bench init` 报 `Invalid frappe path` | 容器内 `127.0.0.1` 指容器自己；而 `/workspace` 即主仓库根、其仓库级代理配置优先于 global | `setup.sh` 用 `GIT_CONFIG_*` 环境变量注入 `host.docker.internal:7897`（见 `.env` 的 `GIT_PROXY`） |
| `Cwd must be an absolute path` | Git Bash（MSYS）把 `-w /workspace` 改写成 Windows 路径 | 脚本开头 `export MSYS_NO_PATHCONV=1` |
| `dubious ownership in repository` | bind mount 进容器的仓库所有者对不上 | `setup.sh` 设 `safe.directory '*'`（容器重建即丢，故每次搭建都设） |
| 端口绑定被拒 | Hyper-V 保留了 9000（本机为 8995-9094） | socketio 宿主侧用 9100，见「端口」节 |
| 源代码管理面板一打开就几十个假改动 | Windows 不保存 Unix 执行位，git 报成 mode 变更（内容零改动） | `setup.sh` 给各 app 设 `core.fileMode false` |
| `.sh` 报 `bad interpreter` | 被 checkout 成 CRLF | `.gitattributes` 强制 `*.sh` 为 `eol=lf` |

另有一条与平台无关但同样会重现：**`bench init` 不读 `PYENV_VERSION`**，不显式传 `--python` 就会自行挑选。v16 强制 Python 3.14，故 `setup.sh` 锁 3.14.7。

### 中文字体

法定财务报表的 PDF 由容器内的 wkhtmltopdf 生成，它依赖 fontconfig 查找中文字形。`docker/scripts/setup.sh` 第 6.5 段会安装 `fonts-noto-cjk` 与 PDF 检查工具 `poppler-utils`；安装失败只告警，不会中断整个开发环境搭建。

字体装在开发容器内，不在项目目录里。容器被 `down.sh` 删除后字体也随之丢失，下次 `docker/up.sh` 会自动补装；离线时先完成其余搭建，联网后重跑 `docker/up.sh` 即可补齐。

## v16 全新安装需要的额外初始化

v16 把一批初始化搬到了界面上的配置向导里，而 `bench new-site` 会把 `setup_complete` 置 1 使向导不再出现。于是全新安装比 v15 需要更多显式步骤，`seed-demo.sh` 已覆盖：

| 缺什么 | 症状 |
|---|---|
| `install_fixtures` 未被调用 | 建公司报 `LinkValidationError: Warehouse Type: Transit` |
| `frappe.defaults` 的 `stock_uom` | 建商品报 `MandatoryError: stock_uom`（注意：设 `Stock Settings.stock_uom` 无效，v16 已不引用该字段） |
| Price List 表为空 | 建订单报 `MandatoryError: selling_price_list, price_list_currency, plc_conversion_rate` |
| 全局 `currency` 仍是镜像默认的 INR | 单据汇率校验失败 |
| `Installed Application` 的 `is_setup_complete` | 登录被强制跳到 `/desk/setup-wizard`（v16 的判据是这张表，不是 `System Settings.setup_complete`） |

`setup_demo_data()` 的签名也变了（v16 需传公司名），脚本按函数签名分派以兼容两版。

**排查时注意**：v16 的 `setup_demo_data()` 把异常吞进 Error Log 后正常返回（v15 会 `raise`），所以「跑完没报错」不等于成功。`seed-demo.sh` 因此在每步落库后加断言，并在失败时摘出 Error Log。

## 重装站点（抹掉全部数据重来）

教学实操、演示前重置这类场合要一个干净站点。**跑之前先 `docker/backup.sh`**，并把那份备份另存一个子目录——`backup.sh` 每次都新增一套带时间戳的文件、不会覆盖旧的，但 `restore.sh` 不带参数时按修改时间取根目录最新一套，新备份会成为默认恢复对象，故仍要另存一份才稳妥。要恢复另存的那套，带上它的时间戳：`docker/restore.sh 20261001_110222`（根目录与各子目录都会找；找不到时列出全部可用时间戳）。

```bash
docker/backup.sh
cp docker/backups/<时间戳>-* docker/backups/保留-某个名字/

docker/shell.sh
bench --site erx.localhost reinstall --yes --admin-password admin --db-root-password 123
bench --site erx.localhost install-app erpnext     # 见下方坑一，这一步不能省
exit

docker/seed-demo.sh --bare      # 只补 v16 缺的初始化，不建公司、不导演示数据
docker/set-locale.sh            # 补回中文，见坑三
```

**⚠ 坑一：`--admin-password` 必须显式传，否则 drop 完数据库才失败，并把 erpnext 弄丢。**

不传时报 `EOFError`。成因：`frappe/commands/site.py` 的 `_reinstall()` 把 `admin_password=None` 原样传给 `_new_site()`，而 `frappe/utils/install.py` 的 `get_admin_password()` 是 `frappe.conf.get("admin_password") or getpass.getpass(...)`——站点 `site_config.json` 里**没有** `admin_password` 字段（`up.sh` 建站时经命令行传入、不落盘），而 `docker compose exec -T` 无 TTY，`getpass` 遂抛异常。

**真正的代价在失败点的位置**：`_reinstall()` 先读旧库的 `get_installed_apps()` 拿到 `["frappe","erpnext"]`，然后 drop 库、按序装 app。它在**装完 frappe、装 erpnext 之前**死掉，此时 `installed_apps` 已被改写成只剩 frappe。**故第二次 reinstall 只会装 frappe**——它读的是已被污染的那份清单。必须 `install-app erpnext` 单独补装。

判据：`bench --site erx.localhost list-apps` 应同时列出 frappe 与 erpnext。

**⚠ 坑二：`--bare` 是给"骨架由人手工建"的场合用的。** 它跑 `seed-demo.sh` 的第 1、5、6 段（v16 前置数据 / `is_setup_complete` 标记 / 清缓存），跳过建公司、演示数据、默认公司对齐。**不能简化成"只跑第 1 段"**——缺第 5 段那个标记，登录会被强制跳配置向导。

**⚠ 坑三：reinstall 抹掉语言设置，界面回英文。** `Language` 记录与 `System Settings.language`、`User.language` 都要重设，跑 `set-locale.sh` 即可。不补的话按中文写的操作文档全部对不上。

**重装后的核验**（别只看脚本输出）：

```bash
docker/shell.sh
cd sites && ../env/bin/python -c "
import frappe; frappe.init(site='erx.localhost'); frappe.connect()
print('Company:', frappe.db.count('Company'))              # 应为 0
print('setup_complete:', frappe.is_setup_complete())       # 应为 True
print('Warehouse Type Transit:', bool(frappe.db.exists('Warehouse Type','Transit')))
print('UOM:', frappe.db.count('UOM'))                      # 应为 239
print('Price List:', frappe.db.count('Price List'))        # 应为 2
print('lang:', frappe.db.get_single_value('System Settings','language'))
"
```

再验 web 层：登录 + `/app` 返 200 + desk 页全部静态资源均 200（脚本见本文末「界面完全没有样式」节，**要测全部资源不能抽查**）。

## 路由前缀是 /desk/ 不是 /app/

v16 把 desk 的路由前缀改成了 `/desk/`，`hooks.py` 里 `/app/(.*)` 已降为到 `/desk/\1` 的**重定向**（实测 `/app/...` 返 301）。旧写法还能用，所以不会立刻报错，但写文档与脚本时一律用 `/desk/`。

**树形 DocType 要走树视图**：`Account` / `Warehouse` / `Cost Center` 等 `is_tree=1` 的，落到列表路由会显示空白（它们的 `*_list.js` 是空文件，实现在 `*_tree.js`）。地址形如 `http://localhost:8000/desk/account/view/tree`。

## 出问题时

```bash
docker compose -f docker/compose.yaml logs -f frappe    # 看日志
docker compose -f docker/compose.yaml ps                # 看状态
docker/down.sh && docker/up.sh                          # 重启
```

数据库连不上先确认 mariadb 是 healthy。站点起不来时进 `docker/shell.sh` 跑 `bench doctor`。

### 整站 404「localhost does not exist」

Frappe 按 HTTP Host 头选站点。浏览器访问的是 `localhost:8000`，而站点名是 `erx.localhost`，靠 `common_site_config.json` 的 `default_site` 兜底。该值缺失时**所有路径**都 404，包括 `/api/method/ping`。

```bash
docker/shell.sh
bench use erx.localhost      # 重设
exit
# 然后 Ctrl-C 停掉 start.sh 再重跑——web 进程只在启动时读这个配置
```

判断依据：带 Host 头能通就说明只是 `default_site` 的问题。

```bash
curl -H 'Host: erx.localhost' -o /dev/null -w '%{http_code}\n' http://localhost:8000/app
```

也可以直接用 http://erx.localhost:8000 访问，绕过这个设置（Windows 对 `.localhost` 域名默认解析到 127.0.0.1，无须改 hosts）。

### 界面完全没有样式

症状是页面结构和交互都在（JS 正常），但没有样式、图标失去尺寸约束后变得很大。原因是 CSS 404：HTML 引用的文件名带内容哈希，与磁盘上的不一致就取不到。

```bash
docker/shell.sh
bench build
exit
```

浏览器需 Ctrl-Shift-R 强制刷新——它会缓存 404 响应。

**验证要测全部资源，不能抽查**。曾出现过 `login.bundle` 哈希恰好匹配、`desk.bundle` 不匹配的情况，只看登录页会误判为正常：

```bash
curl -s -c /tmp/ck -o /dev/null -X POST -H 'Content-Type: application/json' \
  -d '{"usr":"Administrator","pwd":"admin"}' http://localhost:8000/api/method/login
curl -sL -b /tmp/ck -o /tmp/dk.html http://localhost:8000/app
for u in $(grep -oE '/assets/[^"]+\.(css|js)' /tmp/dk.html | sort -u); do
  c=$(curl -s -b /tmp/ck -o /dev/null -w '%{http_code}' "http://localhost:8000$u")
  [ "$c" != 200 ] && echo "$c $u"
done
```

无输出即全部正常（desk 页约 55 个资源）。

另外 `sites/assets/assets.json` 在构建**开始时**就写好，它存在不代表构建成功——判据要看 `frappe-bench/apps/frappe/frappe/public/dist/css/` 下有没有实际文件。
