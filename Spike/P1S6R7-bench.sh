#!/usr/bin/env bash
# 宿主侧一键在容器 bench 目录里跑命令：Spike/P1S6R7-bench.sh '<bench 命令行>'
export MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*'
cd "$(dirname "$0")/../docker"
exec docker compose exec -T -w /workspace/frappe-bench frappe bash -lc "$1"
