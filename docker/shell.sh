#!/usr/bin/env bash
# 进容器交互 shell，落在 bench 目录。跑 bench 命令用这个。
set -euo pipefail

# Git Bash (MSYS) 会把 -w /workspace 改写成 Windows 路径，禁掉转换。
export MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*'
cd "$(dirname "$0")"
[ -f .env ] && { set -a; . ./.env; set +a; }

docker compose exec \
  -e TERM=xterm-256color \
  -w "/workspace/${BENCH_NAME:-bench}" \
  frappe bash
