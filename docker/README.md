# 开发环境（Docker）

Frappe v15 + ERPNext v15 的容器化开发环境。宿主机只需 Docker，其余依赖全在容器里。

## 日常用法

| 做什么 | 跑什么 |
|---|---|
| 首次搭建 / 起容器 | `docker/up.sh` |
| 启动开发服务器 | `docker/start.sh`，然后开 http://localhost:8000 |
| 进容器跑 bench 命令 | `docker/shell.sh` |
| 停容器（数据保留） | `docker/down.sh` |
| 备份站点数据 | `docker/backup.sh` |
| 恢复站点数据 | `docker/restore.sh` |
| 建公司 + 演示数据 | `docker/seed-demo.sh` |
| 清除演示数据 | `docker/seed-demo.sh --clear` |
| 改界面语言 / 默认公司 | `docker/set-locale.sh` |
| 删容器与数据 | `docker/down.sh --purge` |

v16 并行环境另有一套：`up-v16.sh` / `start-v16.sh` / `shell-v16.sh`（见下方「两套版本并存」）。

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
├── compose.yaml        服务定义（mariadb / redis×2 / frappe）
├── .env                本机配置（端口、密码），不进 git
├── .env.example        模板
├── up.sh               起容器 + 首次搭建（幂等）
├── start.sh            bench start
├── shell.sh            进容器
├── down.sh             停容器
├── backup.sh           备份到 backups/
├── restore.sh          从 backups/ 恢复
├── seed-demo.sh        建公司 + 导演示数据
├── set-locale.sh       设界面语言与默认公司
├── save-images.sh      导出镜像供离线迁移
├── load-images.sh      导入镜像
├── scripts/            容器内执行的逻辑（由上面的脚本调用）
├── backups/            备份文件，不进 git
└── images/             导出的镜像，不进 git
frappe-bench/           bench 本体（首次 up.sh 时生成），不进 git
```

容器内 `/workspace` 就是项目根。bench 的 `apps/frappe` 与 `apps/erpnext` 都是**指向本仓库 submodule 的符号链接**：

```
frappe-bench/apps/frappe  -> /workspace/apps/frappe
frappe-bench/apps/erpnext -> /workspace/apps/erpnext
```

所以**你改 `apps/` 下的源码立即生效**，不需要复制或重装。

注意 `bench init --frappe-path` 只表示「从哪儿取代码」，它会 clone 出独立副本；`setup.sh` 在 init 后会把那份副本换成符号链接。改 setup.sh 时别把这步删掉，否则改源码不生效。

## 端口

| 用途 | 宿主机 | 容器内 |
|---|---|---|
| Frappe web | 8000 | 8000 |
| Realtime (socketio) | 9100 | 9000 |
| 资源监视 | 6787 | 6787 |

Windows 上 9000 常落在 Hyper-V 保留端口段，故宿主机侧用 9100。端口冲突时改 `.env`，不改 `compose.yaml`。查保留段：

```bash
netsh interface ipv4 show excludedportrange protocol=tcp
```

## 版本与解释器

本环境用 **ERPNext / Frappe v16**（`apps/` 两个 submodule 锁 `version-16`）。

镜像 `frappe/bench:latest` 自带 Python 3.12 / 3.14 与 Node 22 / 24，两套分别服务两个大版本：

| | 声明的要求 |
|---|---|
| frappe v15 | `requires-python = ">=3.10,<3.15"`，`node >= 18` |
| frappe v16 | `requires-python = ">=3.14,<3.15"`，`node >= 24` |

v16 **强制** Python 3.14，故 `setup.sh` 锁 3.14.7。`bench init` 不读 `PYENV_VERSION`，须显式传 `--python`，否则由它自行挑选。

## 符号链接带来的三处必需修补

`apps/frappe` 与 `apps/erpnext` 是指向本仓库 submodule 的符号链接（这样改源码即时生效），代价是有三处路径推导会失准。三者都已在 `scripts/setup.sh` 里处理，**改脚本时别当冗余删掉**：

| 症状 | 原因 | 修法 |
|---|---|---|
| `bench start` 起不来，socketio 报连 `127.0.0.1:6379` | `node_utils.js` 用 `path.resolve(__dirname,"..","..")` 算 bench 根，符号链接下算出 `/workspace` | Procfile 的 `socketio` / `watch` 行前注入 `FRAPPE_BENCH_ROOT` |
| 页面能打开但 CSS/JS 全 404、完全没有样式 | `bench init` 的构建产物写在它自己 clone 的 `apps/frappe` 副本里，该副本随后被换成符号链接 | 符号链接建好后补跑一次 `bench build`（步骤 6） |
| `bench build` 报 `ENOENT: /workspace/sites/common_site_config.json` | erpnext 的 `banking` 子应用在 `proxyOptions.ts` 顶层读 `../../../sites/...`，符号链接下算出 `/workspace/sites` | 建 `/workspace/sites -> frappe-bench/sites` 兼容链接（步骤 5b） |

第二条尤其容易漏：`sites/assets/assets.json` 在构建**开始时**就写好了，所以它存在并不代表构建成功。判据要看 `apps/frappe/frappe/public/dist/css/` 下有没有实际文件。

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

CSS/JS 全 404 时是前端资源没构建。见上文「符号链接带来的三处必需修补」第二条：

```bash
docker/shell.sh
bench build
```

浏览器需 Ctrl-Shift-R 强制刷新——它会缓存 404 响应。
