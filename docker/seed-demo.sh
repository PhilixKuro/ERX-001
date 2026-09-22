#!/usr/bin/env bash
# 建公司并导入 ERPNext 演示数据，让界面有内容可看。
#
#   docker/seed-demo.sh            建公司 + 导演示数据（幂等）
#   docker/seed-demo.sh --clear    只清除演示数据，保留公司
#   docker/seed-demo.sh --bare     只补 v16 缺的初始化，不建公司、不导演示数据
#                                  （骨架由人手工建的场合用，如教学实操）
#
# 公司信息可在 .env 里改（COMPANY_NAME / COMPANY_COUNTRY / COMPANY_CURRENCY 等）。
set -euo pipefail
export MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*'

cd "$(dirname "$0")"
[ -f .env ] && { set -a; . ./.env; set +a; }

docker compose exec -T \
  -e SITE_NAME="${SITE_NAME:-erx.localhost}" \
  -e COMPANY_NAME="${COMPANY_NAME:-ERX Demo}" \
  -e COMPANY_ABBR="${COMPANY_ABBR:-ERX}" \
  -e COMPANY_COUNTRY="${COMPANY_COUNTRY:-China}" \
  -e COMPANY_CURRENCY="${COMPANY_CURRENCY:-CNY}" \
  -e COMPANY_TIMEZONE="${COMPANY_TIMEZONE:-Asia/Shanghai}" \
  -w /workspace \
  frappe bash /workspace/docker/scripts/seed-demo.sh "${1:-}"
