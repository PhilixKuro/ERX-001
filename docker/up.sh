#!/usr/bin/env bash
# 一键起环境：拉起容器 → 首次搭建 bench 与站点。
#
# 新电脑上只要有 Docker，跑这一条就得到可用的开发环境。
# 已搭好的环境重跑本脚本是安全的（各步幂等），相当于「起容器」。
set -euo pipefail

# Git Bash (MSYS) 会把 -w /workspace 这类参数改写成 Windows 路径，导致
# "Cwd must be an absolute path"。禁掉路径转换。
export MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*'

cd "$(dirname "$0")"
[ -f .env ] || { cp .env.example .env; echo "已从 .env.example 生成 .env"; }
set -a; . ./.env; set +a

echo "==> 拉起容器"
docker compose up -d

echo "==> 等待 MariaDB 就绪"
for i in $(seq 1 60); do
  if docker compose exec -T mariadb healthcheck.sh --connect --innodb_initialized >/dev/null 2>&1; then
    echo "    MariaDB 已就绪"; break
  fi
  [ "$i" = 60 ] && { echo "MariaDB 启动超时，查看日志: docker compose logs mariadb"; exit 1; }
  sleep 2
done

echo "==> 搭建 bench 与站点（幂等，已存在则跳过）"
# 宿主 git 的换行转换设置，交给容器照抄到各 app 仓库（R18 FD-081）。
# Git for Windows 默认 autocrlf=true，工作区是 CRLF；容器里的 git 没有这项设置，
# 会把每个 CRLF 文件都当成已修改。宿主没设（Linux）则为空，容器不写。
HOST_GIT_AUTOCRLF=$(git config --get core.autocrlf 2>/dev/null || true)
docker compose exec -T \
  -e HOST_GIT_AUTOCRLF="$HOST_GIT_AUTOCRLF" \
  -e SITE_NAME="${SITE_NAME:-erx.localhost}" \
  -e BENCH_NAME="${BENCH_NAME:-frappe-bench}" \
  -e DB_ROOT_PASSWORD="${DB_ROOT_PASSWORD:-123}" \
  -e ADMIN_PASSWORD="${ADMIN_PASSWORD:-admin}" \
  -e WEB_PORT="${WEB_PORT:-8000}" \
  -e GIT_PROXY="${GIT_PROXY:-}" \
  -e FRAPPE_REPO="${FRAPPE_REPO:-https://github.com/PhilixKuro/frappe.git}" \
  -e FRAPPE_BRANCH="${FRAPPE_BRANCH:-version-16}" \
  -w /workspace \
  frappe bash /workspace/docker/scripts/setup.sh
