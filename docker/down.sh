#!/usr/bin/env bash
# 停容器。数据保留在 named volume 里，下次 up.sh 继续用。
#
# 要连数据一起删，加 --purge（不可恢复，先跑 backup.sh）。
set -euo pipefail
cd "$(dirname "$0")"

if [ "${1:-}" = "--purge" ]; then
  echo "这会删除数据库与 Redis 的全部数据，不可恢复。"
  printf '确定？[y/N] '
  read -r ans
  [ "$ans" = y ] || [ "$ans" = Y ] || { echo "已取消"; exit 0; }
  docker compose down -v
  echo "容器与数据卷已删除。bench 目录仍在（它是 bind mount）。"
else
  docker compose down
  echo "容器已停，数据保留。"
fi
