#!/usr/bin/env bash
# 在容器内首次搭建 bench 与站点。幂等：已存在的步骤会跳过。
#
# 不直接运行本脚本——用宿主机的 docker/up.sh，它会拉起容器后调用这里。
set -euo pipefail

SITE_NAME="${SITE_NAME:-erx.localhost}"
BENCH_NAME="${BENCH_NAME:-bench}"
DB_ROOT_PASSWORD="${DB_ROOT_PASSWORD:-123}"
ADMIN_PASSWORD="${ADMIN_PASSWORD:-admin}"
FRAPPE_BRANCH="version-16"

# frappe v16 声明 requires-python = ">=3.14,<3.15"，是硬要求而非偏好。
# bench init 不读 PYENV_VERSION，须显式传 --python，否则由它自行挑选。
PY_VERSION="${PY_VERSION:-3.14.7}"
PY_BIN="$HOME/.pyenv/versions/$PY_VERSION/bin/python"

WS=/workspace
BENCH_DIR="$WS/$BENCH_NAME"

log() { printf '\n\033[36m==> %s\033[0m\n' "$*"; }
ok()  { printf '\033[32m    %s\033[0m\n' "$*"; }

# ---------- 0. git safe.directory ----------
# bind mount 过来的仓库在容器内看是「别人的」（宿主 Windows 与容器 UID 不对应），
# git 会以 dubious ownership 拒绝操作。容器重建即丢，故每次搭建都设一遍。
log "标记 workspace 内的仓库为 git 可信路径"
git config --global --add safe.directory '*'
ok "已设置"

# ---------- 1. bench init ----------
# 判据用 env/bin/python：bench init 最后才建 venv，故它存在即代表 init 真的跑完了。
if [ -x "$BENCH_DIR/env/bin/python" ]; then
  ok "bench 已存在，跳过 init"
else
  # bench init 拒绝往已存在的目录写，故先清掉上次失败留下的空壳
  if [ -d "$BENCH_DIR" ]; then
    if [ -z "$(ls -A "$BENCH_DIR" 2>/dev/null)" ]; then
      rmdir "$BENCH_DIR"
    else
      echo "错误：$BENCH_DIR 已存在且非空，但没有可用的 env/bin/python。" >&2
      echo "这是上次搭建中断留下的残留。确认里面没有你要保留的东西后删掉它再重跑：" >&2
      echo "  rm -rf $BENCH_DIR" >&2
      exit 1
    fi
  fi

  [ -x "$PY_BIN" ] || { echo "找不到 Python $PY_VERSION（$PY_BIN）。可用版本：$(pyenv versions --bare | tr '\n' ' ')" >&2; exit 1; }

  log "初始化 bench（Python $PY_VERSION，使用本仓库的 apps/frappe submodule）"
  # 用本地 submodule 作为 frappe 源，改源码立即生效
  bench init \
    --skip-redis-config-generation \
    --python "$PY_BIN" \
    --frappe-path "$WS/apps/frappe" \
    --frappe-branch "$FRAPPE_BRANCH" \
    --no-backups \
    "$BENCH_DIR"
  [ -x "$BENCH_DIR/env/bin/python" ] || { echo "bench init 未生成 venv，中止。" >&2; exit 1; }
  ok "bench 初始化完成"
fi

cd "$BENCH_DIR"

# ---------- 1b. frappe 改指 submodule ----------
# bench init 的 --frappe-path 只是「从哪儿取代码」，它会 git clone 出一份独立副本。
# 那样改 apps/frappe/ 的源码不会生效，故换成符号链接指回本仓库 submodule。
if [ -L "apps/frappe" ]; then
  ok "frappe 已指向 submodule"
else
  log "将 frappe 改指本仓库 submodule（使改源码即时生效）"
  if [ -d "apps/frappe/.git" ] && [ -n "$(git -C apps/frappe status --porcelain 2>/dev/null)" ]; then
    echo "错误：bench 内的 apps/frappe 副本有未提交改动，不能直接替换。" >&2
    echo "先把改动挪到 $WS/apps/frappe，再重跑本脚本。" >&2
    exit 1
  fi
  rm -rf apps/frappe
  ln -s "$WS/apps/frappe" "apps/frappe"
  ./env/bin/pip install --quiet --no-cache-dir -e "$WS/apps/frappe"
  ok "frappe 已指向 submodule"
fi

# ---------- 1c. Node 依赖装进 submodule ----------
# bench init 的 yarn install 装在它自己 clone 的那份副本里，随副本一起被删。
# 符号链接指向 submodule 后，node_modules 必须在 submodule 内，否则 socketio
# 启动即 MODULE_NOT_FOUND、bench start 整体退出。
for app in frappe erpnext; do
  if [ -d "$WS/apps/$app/node_modules" ]; then
    ok "$app 的 node 依赖已存在"
  else
    log "安装 $app 的 node 依赖"
    (cd "$WS/apps/$app" && yarn install --check-files)
    ok "$app node 依赖已安装"
  fi
done

# ---------- 2. 指向容器服务 ----------
log "配置数据库与 Redis 主机"
bench set-config -g db_host mariadb
bench set-config -g redis_cache "redis://redis-cache:6379"
bench set-config -g redis_queue "redis://redis-queue:6379"
bench set-config -g redis_socketio "redis://redis-queue:6379"
sed -i '/redis/d' ./Procfile 2>/dev/null || true

# apps/frappe 是符号链接，node_utils.js 用 path.resolve(__dirname,"..","..")
# 会算出 /workspace 而非 bench 根，socketio 遂读不到 common_site_config.json、
# 回落连 127.0.0.1:6379 并退出。FRAPPE_BENCH_ROOT 是 frappe 自带的覆盖口。
# 逐进程注入而非设成容器环境变量——后者只能指一个 bench，v15/v16 并存会互相串。
if ! grep -q 'FRAPPE_BENCH_ROOT' ./Procfile 2>/dev/null; then
  sed -i "s|^socketio: |socketio: FRAPPE_BENCH_ROOT=$BENCH_DIR |" ./Procfile
  sed -i "s|^watch: |watch: FRAPPE_BENCH_ROOT=$BENCH_DIR |" ./Procfile
fi
ok "已指向 mariadb / redis-cache / redis-queue"

# ---------- 3. 挂接 erpnext submodule ----------
if [ -d "apps/erpnext" ]; then
  ok "erpnext 已在 bench 中"
else
  log "挂接 apps/erpnext（复用本仓库 submodule）"
  ln -s "$WS/apps/erpnext" "apps/erpnext"
  ./env/bin/pip install --no-cache-dir -e "$WS/apps/erpnext"
  # apps.txt 末行常无换行符，直接 >> 会拼成 "frappeerpnext"。
  # sed 先补上缺失的尾换行，再追加。
  if ! grep -qx 'erpnext' sites/apps.txt 2>/dev/null; then
    [ -s sites/apps.txt ] && sed -i -e '$a\' sites/apps.txt
    echo 'erpnext' >> sites/apps.txt
  fi
  ok "erpnext 已挂接"
fi

# ---------- 4. 建站点 ----------
# 判据不能只看目录存在——建站中途失败会留下有 site_config.json 但数据库未建成的
# 残缺站点。以「能否真正连上库并查到表」为准。
site_is_healthy() {
  [ -f "sites/$SITE_NAME/site_config.json" ] || return 1
  bench --site "$SITE_NAME" list-apps >/dev/null 2>&1
}

if site_is_healthy; then
  ok "站点 $SITE_NAME 已存在且可用，跳过创建"
else
  if [ -d "sites/$SITE_NAME" ]; then
    log "发现残缺站点 $SITE_NAME（连不上数据库），重建"
    bench drop-site "$SITE_NAME" --db-root-password "$DB_ROOT_PASSWORD" --force --no-backup 2>/dev/null \
      || rm -rf "sites/$SITE_NAME"
  fi
  log "创建站点 $SITE_NAME"
  bench new-site \
    --db-root-password "$DB_ROOT_PASSWORD" \
    --admin-password "$ADMIN_PASSWORD" \
    --mariadb-user-host-login-scope=% \
    --no-mariadb-socket \
    "$SITE_NAME"
  ok "站点已创建"
fi

# ---------- 5. 装 erpnext ----------
if bench --site "$SITE_NAME" list-apps 2>/dev/null | grep -qx 'erpnext'; then
  ok "erpnext 已安装在站点上"
else
  log "在站点上安装 erpnext"
  bench --site "$SITE_NAME" install-app erpnext
  ok "erpnext 已安装"
fi

# ---------- 5b. /workspace/sites 兼容链接 ----------
# erpnext 的 banking 子应用在 proxyOptions.ts 顶层就 readFileSync
# '../../../sites/common_site_config.json'——从 apps/erpnext/banking 往上三级。
# 正常布局下那是 frappe-bench/sites，但 apps/erpnext 是指向 submodule 的符号
# 链接，往上三级成了 /workspace/sites，于是 bench build 以 ENOENT 失败。
# 该文件是模块顶层代码，import 即执行，构建也绕不过，故补一个兼容链接。
if [ -L "$WS/sites" ]; then
  ok "/workspace/sites 链接已存在"
else
  log "建立 /workspace/sites -> $BENCH_DIR/sites 兼容链接"
  rm -rf "$WS/sites"
  ln -s "$BENCH_DIR/sites" "$WS/sites"
  ok "已建立"
fi

# ---------- 6. 构建前端资源 ----------
# 必须做，且必须在 1b 之后：bench init 的构建产物写在它自己 clone 的那份
# apps/frappe 副本里（产物落在 app 源码目录的 public/dist/，不在 bench 目录），
# 1b 把副本换成符号链接后那些产物就没了。漏掉这步的表现是页面能打开但
# 所有 CSS/JS 都 404、界面完全没有样式。
# 判据用 dist/css 下有无文件——assets.json 在构建开始时就写好了，不能作准。
if [ -n "$(ls -A "$WS/apps/frappe/frappe/public/dist/css" 2>/dev/null)" ]; then
  ok "前端资源已构建"
else
  log "构建前端资源（需数分钟）"
  bench build
  [ -n "$(ls -A "$WS/apps/frappe/frappe/public/dist/css" 2>/dev/null)" ] \
    || { echo "bench build 未产出 dist/css，中止。" >&2; exit 1; }
  ok "前端资源已构建"
fi

# ---------- 7. 开发模式 ----------
log "开启开发模式"
bench --site "$SITE_NAME" set-config developer_mode 1
bench --site "$SITE_NAME" clear-cache
bench use "$SITE_NAME"
ok "开发模式已开启"

cat <<EOF

\033[32m搭建完成。\033[0m

  站点:     $SITE_NAME
  用户:     Administrator
  密码:     $ADMIN_PASSWORD

启动开发服务器（在宿主机执行）:
  docker/start.sh

然后访问 http://localhost:${WEB_PORT:-8000}
EOF
