#!/usr/bin/env bash
# 配置四个 App：CRM 集成、Raven 连接、演示 bot 与 15 条只读工具。宿主侧入口。
#
#   docker/configure-apps.sh                          站点取 .env 的 SITE_NAME
#   docker/configure-apps.sh --site test.localhost
#   docker/configure-apps.sh --site erx.localhost --company 华东弹簧有限公司
#
# --company 缺省取站上唯一一家「小企业会计准则(2024)」公司；零家或多家时报错要求显式传。
# 可重复跑：第二次起输出「无改动」。RAVEN_LLM_URL／KEY／MODEL 从 .env 读，密钥不打印。
# 实际逻辑在 docker/scripts/configure_apps.py（容器内跑）。
set -euo pipefail
export MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*'

cd "$(dirname "$0")"
[ -f .env ] && { set -a; . ./.env; set +a; }

site="${SITE_NAME:-erx.localhost}"
company=""
while [ $# -gt 0 ]; do
  case "$1" in
    --site) site="${2:?--site 需要一个值}"; shift 2 ;;
    --company) company="${2:?--company 需要一个值}"; shift 2 ;;
    *) echo "configure-apps：未知参数 $1" >&2; exit 2 ;;
  esac
done

args=(--site "$site")
[ -n "$company" ] && args+=(--company "$company")

# 只写变量名、不写值：密钥不出现在宿主的进程参数里（.env 已由 set -a 导出）
docker compose exec -T \
  -e RAVEN_LLM_URL -e RAVEN_LLM_KEY -e RAVEN_LLM_MODEL \
  -w "/workspace/${BENCH_NAME:-frappe-bench}/sites" \
  frappe "/workspace/${BENCH_NAME:-frappe-bench}/env/bin/python" /workspace/docker/scripts/configure_apps.py "${args[@]}"
