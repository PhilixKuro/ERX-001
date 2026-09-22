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
| 恢复站点数据 | `docker/restore.sh` |
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
├── lock-apps.sh        把各 app 当前 commit 写进 apps.json
├── save-images.sh      导出镜像供离线迁移
├── load-images.sh      导入镜像
├── apps.json           装哪些 app、哪个分支、锁到哪个 commit
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

**版本记录**：`apps.json` 记 url + branch + commit。合并上游或确认版本可用后跑 `docker/lock-apps.sh` 更新它，换机器时 `up.sh` 按它对齐（用 `reset --hard`，仍停在分支上，不进 detached HEAD；有未提交改动时跳过，不会丢代码）。

**在 VS Code 里看这三个仓库的改动**：`.vscode/settings.json` 已用 `git.scanRepositories` 显式列出（它们在 gitignore 内，编辑器默认不扫）。源代码管理面板会并列显示主仓库、frappe、erpnext。新增自有 app 后在那里追加一行。

**自己要排除的临时文件**写进该仓库的 `.git/info/exclude`，别改上游的 `.gitignore`——那是上游文件，改了会成为每次合并的冲突点。

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

教学实操、演示前重置这类场合要一个干净站点。**跑之前先 `docker/backup.sh`**，并把那份备份另存一个子目录——`backup.sh` 每类只保留最新一份，下次备份会覆盖它。

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
