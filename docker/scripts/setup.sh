#!/usr/bin/env bash
# 在容器内搭建 bench 与站点。幂等：已完成的步骤会跳过。
#
# 不直接运行本脚本——用宿主机的 docker/up.sh，它会拉起容器后调用这里。
#
# 遵循 frappe_docker 官方模型：bench 自己 clone 各 app，不用符号链接。
# bench 目录整个不进主仓库 git（官方文档：development directory is ignored by
# git）；版本由 docker/apps.json 声明，换机器按它重建。
# 各 app 在 frappe-bench/apps/ 下是独立 git 仓库，remote 指自有 fork，
# 改源码就在那里改、commit、push，合并上游用 fetch upstream && merge。
set -euo pipefail

SITE_NAME="${SITE_NAME:-erx.localhost}"
BENCH_NAME="${BENCH_NAME:-frappe-bench}"
DB_ROOT_PASSWORD="${DB_ROOT_PASSWORD:-123}"
ADMIN_PASSWORD="${ADMIN_PASSWORD:-admin}"
FRAPPE_REPO="${FRAPPE_REPO:-https://github.com/PhilixKuro/frappe.git}"
FRAPPE_BRANCH="${FRAPPE_BRANCH:-version-16}"
FRAPPE_UPSTREAM="${FRAPPE_UPSTREAM:-https://github.com/frappe/frappe.git}"

# frappe v16 声明 requires-python = ">=3.14,<3.15"，是硬要求而非偏好。
# bench init 不读 PYENV_VERSION，须显式传 --python，否则由它自行挑选。
PY_VERSION="${PY_VERSION:-3.14.7}"
PY_BIN="$HOME/.pyenv/versions/$PY_VERSION/bin/python"

WS=/workspace
BENCH_DIR="$WS/$BENCH_NAME"
APPS_JSON="$WS/docker/apps.json"

log() { printf '\n\033[36m==> %s\033[0m\n' "$*"; }
ok()  { printf '\033[32m    %s\033[0m\n' "$*"; }

# ---------- 0. git safe.directory ----------
# bind mount 过来的仓库在容器内看是「别人的」（宿主 Windows 与容器 UID 不对应），
# git 会以 dubious ownership 拒绝操作。容器重建即丢，故每次搭建都设一遍。
log "标记 workspace 内的仓库为 git 可信路径"
git config --global --add safe.directory '*'
ok "已设置"

# ---------- 0b. 容器内 git 代理 ----------
# bench init / get-app 要从 GitHub clone。宿主机的代理在容器里不可直接引用——
# 容器内的 127.0.0.1 是容器自己，须用 host.docker.internal 指向宿主。
# 容器重建即丢，故每次搭建都设。GIT_PROXY 为空则跳过（无需代理的网络环境）。
GIT_PROXY="${GIT_PROXY:-}"
if [ -n "$GIT_PROXY" ]; then
  log "配置容器内 git 代理"
  git config --global "http.https://github.com/.proxy" "$GIT_PROXY"
  # 用 GIT_CONFIG_* 环境变量注入，优先级高于任何配置文件。
  # 必须这样做：/workspace 就是主仓库根目录，宿主机为它配的代理是
  # 127.0.0.1:7897——在容器里那指向容器自己。而仓库级配置优先于 global，
  # 会盖掉上面那行。不改那个文件，因为它同时被宿主机的 git 使用。
  export GIT_CONFIG_COUNT=1
  export GIT_CONFIG_KEY_0="http.https://github.com/.proxy"
  export GIT_CONFIG_VALUE_0="$GIT_PROXY"
  if timeout 25 git ls-remote --heads "$FRAPPE_REPO" "$FRAPPE_BRANCH" >/dev/null 2>&1; then
    ok "代理可用：$GIT_PROXY"
  else
    echo "错误：经 $GIT_PROXY 仍无法访问 $FRAPPE_REPO。" >&2
    echo "检查宿主机代理端口，或在 docker/.env 里改 GIT_PROXY（留空表示不用代理）。" >&2
    exit 1
  fi
else
  git config --global --unset-all "http.https://github.com/.proxy" 2>/dev/null || true
  ok "未设代理（GIT_PROXY 为空）"
fi

# ---------- 1. bench init ----------
# 判据用 env/bin/python：bench init 最后才建 venv，故它存在即代表 init 跑完了。
if [ -x "$BENCH_DIR/env/bin/python" ]; then
  ok "bench 已存在，跳过 init"
else
  if [ -d "$BENCH_DIR" ]; then
    if [ -z "$(ls -A "$BENCH_DIR" 2>/dev/null)" ]; then
      rmdir "$BENCH_DIR"
    else
      echo "错误：$BENCH_DIR 已存在且非空，但没有可用的 env/bin/python。" >&2
      echo "这是上次搭建中断留下的残留。确认无需保留后删掉再重跑：" >&2
      echo "  rm -rf $BENCH_DIR" >&2
      exit 1
    fi
  fi

  [ -x "$PY_BIN" ] || { echo "找不到 Python $PY_VERSION（$PY_BIN）。可用：$(pyenv versions --bare | tr '\n' ' ')" >&2; exit 1; }

  log "初始化 bench（Python $PY_VERSION，frappe $FRAPPE_BRANCH）"
  bench init \
    --skip-redis-config-generation \
    --python "$PY_BIN" \
    --frappe-path "$FRAPPE_REPO" \
    --frappe-branch "$FRAPPE_BRANCH" \
    --no-backups \
    "$BENCH_DIR"
  [ -x "$BENCH_DIR/env/bin/python" ] || { echo "bench init 未生成 venv，中止。" >&2; exit 1; }
  ok "bench 初始化完成"
fi

cd "$BENCH_DIR"

# ---------- 2. 指向容器服务 ----------
log "配置数据库与 Redis 主机"
bench set-config -g db_host mariadb
bench set-config -g redis_cache "redis://redis-cache:6379"
bench set-config -g redis_queue "redis://redis-queue:6379"
bench set-config -g redis_socketio "redis://redis-queue:6379"
sed -i '/redis/d' ./Procfile 2>/dev/null || true
ok "已指向 mariadb / redis-cache / redis-queue"

# ---------- 3. 按 apps.json 装 app ----------
log "按 docker/apps.json 安装 app"
if [ ! -f "$APPS_JSON" ]; then
  echo "找不到 $APPS_JSON" >&2; exit 1
fi

# 逐条读取。用 python 解析而非 jq——镜像里不一定有 jq。
# commit 字段可选：有则 checkout 到该 commit（精确锁定，保证多机一致），
# 无则停在分支最新。由 docker/lock-apps.sh 写入。
while IFS=$'\t' read -r app_url app_branch app_commit; do
  [ -z "$app_url" ] && continue
  app_name=$(basename "$app_url" .git)

  if [ -d "apps/$app_name" ]; then
    ok "$app_name 已存在"
  elif [ "$app_name" = "frappe" ]; then
    # frappe 由上面的 bench init 装，不能走 get-app
    ok "frappe 由 bench init 装（跳过 get-app）"
  else
    log "获取 $app_name（$app_branch）"
    bench get-app --branch "$app_branch" --resolve-deps "$app_url"
    ok "$app_name 已获取"
  fi

  # 锁定到指定 commit。已是该 commit 则跳过；有未提交改动时不动，避免丢改动。
  if [ -n "$app_commit" ] && [ -d "apps/$app_name/.git" ]; then
    current=$(git -C "apps/$app_name" rev-parse HEAD)
    if [ "$current" = "$app_commit" ]; then
      ok "$app_name 已在锁定的 commit ${app_commit:0:12}"
    elif [ -n "$(git -C "apps/$app_name" status --porcelain)" ]; then
      echo "  警告：$app_name 有未提交改动，跳过 checkout 到 ${app_commit:0:12}" >&2
    else
      log "$app_name 对齐到锁定的 ${app_commit:0:12}"
      # shallow clone 可能不含该 commit，先取回
      git -C "apps/$app_name" fetch --depth 1 origin "$app_commit" 2>/dev/null \
        || git -C "apps/$app_name" fetch origin 2>/dev/null || true
      # 用 reset --hard 而非 checkout <sha>：后者进入 detached HEAD，你之后
      # 改代码无法直接 commit 到分支。这样仍停在 $app_branch 上。
      if git -C "apps/$app_name" reset --hard -q "$app_commit" 2>/dev/null; then
        ok "已对齐到 ${app_commit:0:12}（仍在 $app_branch 分支）"
      else
        echo "  警告：取不到 commit ${app_commit:0:12}，保持当前 ${current:0:12}" >&2
      fi
    fi
  fi
done < <("$BENCH_DIR/env/bin/python" - "$APPS_JSON" <<'PY'
import json, sys
for a in json.load(open(sys.argv[1], encoding="utf-8")):
    print(a["url"], a.get("branch", "version-16"), a.get("commit", ""), sep="\t")
PY
)

# ---------- 4. 各 app 的 remote 命名归位 ----------
# bench init / get-app 用 `git clone --origin upstream` 建仓库，于是「自有 fork」
# 被命名为 upstream、且没有 origin——与惯例相反，容易把改动推错地方。
# 这里归位成：origin = 自有 fork（推改动），upstream = 官方（只读拉更新，
# push URL 设为无效值以防误推）。
log "归位各 app 的 remote 命名"
for d in apps/*/; do
  app_name=$(basename "$d")
  [ -d "$d/.git" ] || continue

  case "$app_name" in
    frappe)  official="$FRAPPE_UPSTREAM" ;;
    erpnext) official="https://github.com/frappe/erpnext.git" ;;
    *)       official="" ;;   # 自有 app 无上游
  esac

  # 自有 fork 的 URL：优先取现有 origin，否则取 bench 建的那个 upstream
  fork=$(git -C "$d" remote get-url origin 2>/dev/null || true)
  if [ -z "$fork" ]; then
    fork=$(git -C "$d" remote get-url upstream 2>/dev/null || true)
    # 若现有 upstream 已是官方地址，说明命名已正确，不是待归位的 fork
    [ "$fork" = "$official" ] && fork=""
  fi

  if [ -n "$fork" ]; then
    git -C "$d" remote remove origin 2>/dev/null || true
    git -C "$d" remote add origin "$fork"
  fi

  if [ -n "$official" ]; then
    git -C "$d" remote remove upstream 2>/dev/null || true
    git -C "$d" remote add upstream "$official"
    git -C "$d" remote set-url --push upstream DISABLED_use_origin_instead
  fi

  # Windows 文件系统不保存 Unix 执行位，git 会把上游几十个文件报成
  # "old mode 100755 / new mode 100644"（内容零改动）。不关掉的话
  # VS Code 源代码管理面板一打开就是几十个假改动，真改动被淹没。
  git -C "$d" config core.fileMode false

  ok "$app_name  origin=$(git -C "$d" remote get-url origin 2>/dev/null || echo 无)  upstream=$(git -C "$d" remote get-url upstream 2>/dev/null || echo 无)"
done

# ---------- 5. 建站点 ----------
# 判据不能只看目录存在——建站中途失败会留下有 site_config.json 但数据库未建成的
# 残缺站点。以「能否真正连上库」为准。
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

# ---------- 6. 在站点上装 app ----------
for d in apps/*/; do
  app_name=$(basename "$d")
  [ "$app_name" = "frappe" ] && continue   # frappe 随建站自动装
  if bench --site "$SITE_NAME" list-apps 2>/dev/null | grep -qx "$app_name"; then
    ok "$app_name 已安装在站点上"
  else
    log "在站点上安装 $app_name"
    bench --site "$SITE_NAME" install-app "$app_name"
    ok "$app_name 已安装"
  fi
done

# ---------- 7. 开发模式 ----------
log "开启开发模式"
bench --site "$SITE_NAME" set-config developer_mode 1
bench --site "$SITE_NAME" clear-cache
ok "开发模式已开启"

# ---------- 8. 默认站点 ----------
# Frappe 按 HTTP Host 头选站点。浏览器访问 localhost:8000 而站点名是
# erx.localhost，没有 default_site 兜底就整站 404「localhost does not exist」。
log "设默认站点"
bench use "$SITE_NAME"
grep -q "\"default_site\": \"$SITE_NAME\"" sites/common_site_config.json \
  || { echo "default_site 未写入 common_site_config.json，中止。" >&2; exit 1; }
ok "默认站点为 $SITE_NAME（改动后须重启 bench start 才生效）"

# ---------- 9. 校验前端资源 ----------
# bench init / get-app 会各自构建。这里只校验产物确实在，不重复构建。
# 判据看 dist/css 下有无实际文件——assets.json 在构建开始时就写好了，不能作准。
log "校验前端资源"
missing=""
for d in apps/*/; do
  app_name=$(basename "$d")
  pub="$d/$app_name/public/dist/css"
  [ -d "$d/$app_name/public" ] || continue
  [ -n "$(ls -A "$pub" 2>/dev/null)" ] || missing="$missing $app_name"
done
if [ -n "$missing" ]; then
  log "以下 app 缺前端产物，重新构建：$missing"
  bench build
fi
for d in apps/*/; do
  app_name=$(basename "$d")
  [ -d "$d/$app_name/public" ] || continue
  [ -n "$(ls -A "$d/$app_name/public/dist/css" 2>/dev/null)" ] \
    || { echo "bench build 后 $app_name 仍无 dist/css，中止。" >&2; exit 1; }
done
ok "前端资源齐备"

cat <<EOF

\033[32m搭建完成。\033[0m

  站点:     $SITE_NAME
  用户:     Administrator
  密码:     $ADMIN_PASSWORD
  Python:   $PY_VERSION

启动开发服务器（在宿主机执行）:
  docker/start.sh
然后访问 http://localhost:${WEB_PORT:-8000}

下一步（可选）：docker/seed-demo.sh 建公司与演示数据
EOF
