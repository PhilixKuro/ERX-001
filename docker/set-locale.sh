#!/usr/bin/env bash
# 设界面语言与默认公司。
#
#   docker/set-locale.sh                     用 .env 里的 UI_LANGUAGE（默认 zh）
#   UI_LANGUAGE=en docker/set-locale.sh      改回英文
#   DEFAULT_COMPANY="ERX Demo" docker/set-locale.sh
#
# 默认公司若与单据所属公司不一致，打开该单据会报「没有权限」——本脚本默认对齐到
# 演示数据所在的那家公司。
set -euo pipefail
export MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*'

cd "$(dirname "$0")"
[ -f .env ] && { set -a; . ./.env; set +a; }

docker compose exec -T \
  -e SITE_NAME="${SITE_NAME:-erx.localhost}" \
  -e UI_LANGUAGE="${UI_LANGUAGE:-zh}" \
  -e DEFAULT_COMPANY="${DEFAULT_COMPANY:-}" \
  -w /workspace \
  frappe bash /workspace/docker/scripts/set-locale.sh
