#!/usr/bin/env bash
# 备份站点（数据库 + 上传的文件）到 docker/backups/。
#
# named volume 拷不走，故迁移到新电脑前必须跑这个。
# 备份落在项目文件夹内，会随文件夹一起被拷走。
set -euo pipefail

# Git Bash (MSYS) 会把 -w /workspace 改写成 Windows 路径，禁掉转换。
export MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*'
cd "$(dirname "$0")"
[ -f .env ] && { set -a; . ./.env; set +a; }

SITE="${SITE_NAME:-erx.localhost}"
BENCH="${BENCH_NAME:-bench}"

echo "==> 备份站点 $SITE（含上传文件）"
docker compose exec -T -w "/workspace/$BENCH" frappe \
  bench --site "$SITE" backup --with-files

# bench 把备份写在 sites/<site>/private/backups/，那里已在 bind mount 内。
# 复制到 docker/backups/ 便于查找与拷贝。
SRC="../$BENCH/sites/$SITE/private/backups"
mkdir -p backups
if [ -d "$SRC" ]; then
  # 取每类最新一份。公开文件的模式须排除 private——两者都能被 *-files.tar 匹配到。
  copy_latest() {
    local latest
    latest=$(eval "ls -t $1 2>/dev/null" | { [ -n "${2:-}" ] && grep -v -- "$2" || cat; } | head -1)
    [ -n "$latest" ] && cp -f "$latest" backups/ && echo "    $(basename "$latest")"
  }
  copy_latest "\"$SRC\"/*-database.sql.gz"
  copy_latest "\"$SRC\"/*-files.tar" "private-files.tar"
  copy_latest "\"$SRC\"/*-private-files.tar"
  copy_latest "\"$SRC\"/*_config*.json"
fi

echo
echo "备份已存入 docker/backups/"
echo "迁移到新电脑：拷走整个项目文件夹 → 在新机器上跑 docker/up.sh → 再跑 docker/restore.sh"
