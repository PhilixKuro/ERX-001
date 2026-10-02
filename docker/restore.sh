#!/usr/bin/env bash
# 从 docker/backups/ 恢复站点数据。在新电脑上 up.sh 跑完后执行。
#
#   docker/restore.sh                    恢复 backups/ 根目录下最新的一套
#   docker/restore.sh 20261001_110222    恢复指定时间戳的那套（根目录与 保留-* 等子目录都找）
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
STAMP="${1:-}"

if [ -n "$STAMP" ]; then
  # 基准备份另存在子目录里（见 README「重装站点」节），故按时间戳找时连子目录一起找。
  # 同一时间戳在根目录与子目录各有一份时内容相同，取先找到的那份。
  DB=$(ls backups/"$STAMP"-*-database.sql.gz backups/*/"$STAMP"-*-database.sql.gz 2>/dev/null | head -1 || true)
  if [ -z "$DB" ]; then
    echo "找不到时间戳为 $STAMP 的数据库备份。可用的有："
    ls backups/*-database.sql.gz backups/*/*-database.sql.gz 2>/dev/null \
      | sed -E 's#^backups/##; s#-[^/]*-database\.sql\.gz$##' | sort -u | sed 's/^/  /'
    exit 1
  fi
  DIR=$(dirname "$DB")
  PUB=$(ls "$DIR/$STAMP"-*-files.tar 2>/dev/null | grep -v private | head -1 || true)
  PRIV=$(ls "$DIR/$STAMP"-*-private-files.tar 2>/dev/null | head -1 || true)
else
  DB=$(ls -t backups/*-database.sql.gz 2>/dev/null | head -1 || true)
  [ -z "$DB" ] && { echo "docker/backups/ 里没有数据库备份。先在原机器跑 docker/backup.sh。"; exit 1; }
  PUB=$(ls -t backups/*-files.tar 2>/dev/null | grep -v private | head -1 || true)
  PRIV=$(ls -t backups/*-private-files.tar 2>/dev/null | head -1 || true)
fi

echo "将用以下备份覆盖站点 $SITE 的全部数据："
echo "  $DB"
[ -n "$PUB" ]  && echo "  $PUB"
[ -n "$PRIV" ] && echo "  $PRIV"
printf '\n继续？[y/N] '
read -r ans
[ "$ans" = y ] || [ "$ans" = Y ] || { echo "已取消"; exit 0; }

# 备份文件在 docker/ 下，容器内路径为 /workspace/docker/<相对路径>。子目录名含中文，用单引号包住（路径里不会有单引号）
ARGS="--force --db-root-password $DB_PW '/workspace/docker/$DB'"
[ -n "$PUB" ]  && ARGS="$ARGS --with-public-files '/workspace/docker/$PUB'"
[ -n "$PRIV" ] && ARGS="$ARGS --with-private-files '/workspace/docker/$PRIV'"

echo "==> 恢复中"
docker compose exec -T -w "/workspace/$BENCH" frappe \
  bash -c "bench --site $SITE restore $ARGS"

echo "==> 跑迁移"
docker compose exec -T -w "/workspace/$BENCH" frappe \
  bench --site "$SITE" migrate

echo
echo "恢复完成。启动: docker/start.sh"
