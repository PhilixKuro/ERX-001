#!/usr/bin/env bash
# 从 docker/backups/ 恢复站点数据。在新电脑上 up.sh 跑完后执行。
#
# 会覆盖当前站点的全部数据。
set -euo pipefail

# Git Bash (MSYS) 会把 -w /workspace 改写成 Windows 路径，禁掉转换。
export MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*'
cd "$(dirname "$0")"
[ -f .env ] && { set -a; . ./.env; set +a; }

SITE="${SITE_NAME:-erx.localhost}"
BENCH="${BENCH_NAME:-bench}"
DB_PW="${DB_ROOT_PASSWORD:-123}"

DB=$(ls -t backups/*-database.sql.gz 2>/dev/null | head -1 || true)
[ -z "$DB" ] && { echo "docker/backups/ 里没有数据库备份。先在原机器跑 docker/backup.sh。"; exit 1; }

echo "将用以下备份覆盖站点 $SITE 的全部数据："
echo "  $(basename "$DB")"
PUB=$(ls -t backups/*-files.tar 2>/dev/null | grep -v private | head -1 || true)
PRIV=$(ls -t backups/*-private-files.tar 2>/dev/null | head -1 || true)
[ -n "$PUB" ]  && echo "  $(basename "$PUB")"
[ -n "$PRIV" ] && echo "  $(basename "$PRIV")"
printf '\n继续？[y/N] '
read -r ans
[ "$ans" = y ] || [ "$ans" = Y ] || { echo "已取消"; exit 0; }

# 备份文件在 docker/backups/，容器内路径为 /workspace/docker/backups/
ARGS="--force --db-root-password $DB_PW /workspace/docker/backups/$(basename "$DB")"
[ -n "$PUB" ]  && ARGS="$ARGS --with-public-files /workspace/docker/backups/$(basename "$PUB")"
[ -n "$PRIV" ] && ARGS="$ARGS --with-private-files /workspace/docker/backups/$(basename "$PRIV")"

echo "==> 恢复中"
docker compose exec -T -w "/workspace/$BENCH" frappe \
  bash -c "bench --site $SITE restore $ARGS"

echo "==> 跑迁移"
docker compose exec -T -w "/workspace/$BENCH" frappe \
  bench --site "$SITE" migrate

echo
echo "恢复完成。启动: docker/start.sh"
