#!/usr/bin/env bash
# 启动开发服务器（bench start）。Ctrl-C 停止。
set -euo pipefail

# Git Bash (MSYS) 会把 -w /workspace 改写成 Windows 路径，禁掉转换。
export MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*'
cd "$(dirname "$0")"
[ -f .env ] && { set -a; . ./.env; set +a; }

docker compose exec \
  -w "/workspace/${BENCH_NAME:-bench}" \
  frappe bench start
