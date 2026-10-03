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
#
# app_name 字段 = 克隆后 apps/ 下的目录名。不能拿仓库名代替：bench get-app 会按
# pyproject.toml 的 name 给目录改名（FrappeChina → frappe_china），按仓库名判断
# 「已存在」永远为假，重跑时会再克隆一次、改名撞上已有目录而中止（R14 FD-009）。
# 缺省时退回仓库名（frappe、erpnext 两者相同）。
#
# 不用 --resolve-deps：apps.json 本身就是按装载顺序排好的完整清单；而依赖解析遇到
# 已装的依赖（如 erpnext）会用 click.confirm 问要不要删掉重装，无输入时 Abort，
# 答 y 则把整个依赖目录 rmtree（R14 FD-009）。
while IFS=$'\t' read -r app_url app_branch app_commit app_name; do
  [ -z "$app_url" ] && continue
  [ "$app_commit" = "-" ] && app_commit=""
  [ "$app_name" = "-" ] && app_name=""
  [ -n "$app_name" ] || app_name=$(basename "$app_url" .git)

  if [ -d "apps/$app_name" ]; then
    ok "$app_name 已存在"
  elif [ "$app_name" = "frappe" ]; then
    # frappe 由上面的 bench init 装，不能走 get-app
    ok "frappe 由 bench init 装（跳过 get-app）"
  else
    # 先探一次能否访问：私有仓库在容器里没有凭据时，克隆只报一句 could not read
    # Username 就中止，看不出原因。这里提前响亮失败，并指明办法。
    if ! GIT_TERMINAL_PROMPT=0 timeout 25 git ls-remote --heads "$app_url" "$app_branch" >/dev/null 2>&1; then
      echo "错误：容器内访问不了 $app_url（分支 $app_branch）。" >&2
      echo "若是私有仓库，先给容器配凭据再重跑 docker/up.sh，办法见 docker/README.md「私有仓库」节。" >&2
      exit 1
    fi
    log "获取 $app_name（$app_branch）"
    bench get-app --branch "$app_branch" "$app_url"
    [ -d "apps/$app_name" ] || {
      echo "get-app 后找不到 apps/$app_name：apps.json 里这一条的 app_name 与该 app 的 pyproject.toml name 不一致？" >&2
      exit 1
    }
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
      # 此时 remote 还没归位（第 4 段才做）：bench get-app 克隆出的仓库只有 upstream、没有 origin，
      # 且是 --depth 1 浅克隆。按实际存在的 remote 取回该 commit（R17 FD-045）
      remote=$(git -C "apps/$app_name" remote get-url origin >/dev/null 2>&1 && echo origin || echo upstream)
      git -C "apps/$app_name" cat-file -e "$app_commit^{commit}" 2>/dev/null \
        || git -C "apps/$app_name" fetch -q --depth 1 "$remote" "$app_commit" 2>/dev/null \
        || git -C "apps/$app_name" fetch -q --unshallow "$remote" 2>/dev/null \
        || true
      # 用 reset --hard 而非 checkout <sha>：后者进入 detached HEAD，你之后
      # 改代码无法直接 commit 到分支。这样仍停在 $app_branch 上。
      if git -C "apps/$app_name" reset --hard -q "$app_commit" 2>/dev/null; then
        ok "已对齐到 ${app_commit:0:12}（仍在 $app_branch 分支）"
      else
        # 不只打警告往下跑：停在分支最新就不是 apps.json 锁定的版本，两台机器会拿到不同代码
        echo "错误：$app_name 取不到锁定的 commit ${app_commit:0:12}（remote=$remote），当前停在 ${current:0:12}。" >&2
        echo "检查该 commit 是否已推送到 $app_url；要解除锁定，按 docker/lock-apps.sh 末尾的说明删掉 commit 字段。" >&2
        exit 1
      fi
    fi
  fi
done < <("$BENCH_DIR/env/bin/python" - "$APPS_JSON" <<'PY'
import json, sys
# 空字段写成 "-"：tab 属于 IFS 空白字符，read 会把连续两个 tab 合并成一个，
# 删掉 commit 解锁后 app_name 会被读进 app_commit（R17 FD-049）
for a in json.load(open(sys.argv[1], encoding="utf-8")):
    print(a["url"], a.get("branch") or "version-16", a.get("commit") or "-", a.get("app_name") or "-", sep="\t")
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

# ---------- 6.5 中文字体（PDF 打印用，P1-S4 DEC-095） ----------
# wkhtmltopdf 靠 fontconfig 找字形；镜像只带 dejavu 等西文字体，汉字会出方块。
# apt 不走 GIT_PROXY，故有代理时显式传给 apt。离线时只告警，不中断搭建。
if fc-list :lang=zh family | grep -q . && command -v pdffonts >/dev/null; then
  ok "中文字体与 PDF 检查工具已安装"
else
  log "安装中文字体 fonts-noto-cjk"
  apt_proxy=()
  [ -n "${GIT_PROXY:-}" ] && apt_proxy=(-o "Acquire::http::Proxy=$GIT_PROXY" -o "Acquire::https::Proxy=$GIT_PROXY")
  # poppler-utils 提供 pdftotext／pdffonts，供测试核对 PDF 里的文字与嵌入字体。
  if sudo apt-get "${apt_proxy[@]}" update -qq && \
     sudo apt-get "${apt_proxy[@]}" install -y -qq fonts-noto-cjk poppler-utils; then
    fc-cache -f >/dev/null && ok "中文字体已安装"
  else
    echo "  警告：中文字体安装失败（网络不通？）。PDF 里的汉字会显示为方块，联网后重跑 up.sh 即可补装" >&2
  fi
fi

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
# 判据看 dist 下有无实际文件——assets.json 在构建开始时就写好了，不能作准。
# 只查有构建源的 app：esbuild 只收 public/**/*.bundle.*，没有这类文件的 app（如只有
# public/.gitkeep 的 frappe_china）build 后也不会有 dist，不能要求它有（R18 FD-080）。
# 有样式 bundle 的查 dist/css，只有脚本 bundle 的查 dist/js。
assets_missing() {
  local pub="$1/$2/public" kind dir
  for kind in css js; do
    if [ "$kind" = css ]; then
      find "$pub" \( -path "$pub/dist" -o -name node_modules \) -prune -o -type f \
        \( -name '*.bundle.css' -o -name '*.bundle.scss' -o -name '*.bundle.sass' -o -name '*.bundle.less' \) -print 2>/dev/null | grep -q . || continue
    else
      find "$pub" \( -path "$pub/dist" -o -name node_modules \) -prune -o -type f \
        \( -name '*.bundle.js' -o -name '*.bundle.ts' -o -name '*.bundle.jsx' -o -name '*.bundle.tsx' -o -name '*.bundle.vue' \) -print 2>/dev/null | grep -q . || continue
    fi
    dir="$pub/dist/$kind"
    [ -n "$(ls -A "$dir" 2>/dev/null)" ] || { echo "$kind"; return 0; }
  done
  return 1
}
log "校验前端资源"
missing=""
for d in apps/*/; do
  app_name=$(basename "$d")
  [ -d "$d/$app_name/public" ] || continue
  assets_missing "$d" "$app_name" >/dev/null && missing="$missing $app_name"
done
if [ -n "$missing" ]; then
  log "以下 app 缺前端产物，重新构建：$missing"
  bench build
fi
for d in apps/*/; do
  app_name=$(basename "$d")
  [ -d "$d/$app_name/public" ] || continue
  if kind=$(assets_missing "$d" "$app_name"); then
    echo "bench build 后 $app_name 仍无 dist/$kind，中止。" >&2; exit 1
  fi
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
