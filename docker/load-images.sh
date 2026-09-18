#!/usr/bin/env bash
# 从 docker/images/ 导入镜像。新电脑无网络时，在 up.sh 之前跑这个。
set -euo pipefail
export MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*'

cd "$(dirname "$0")"

TAR="images/erx001-images.tar"
[ -f "$TAR" ] || { echo "找不到 $TAR。先在原电脑跑 docker/save-images.sh。" >&2; exit 1; }

echo "==> 从 $TAR 导入镜像（需数分钟）"
docker load -i "$TAR"

echo
echo "==> 已就绪的镜像"
docker images --format '{{.Repository}}:{{.Tag}}  {{.Size}}' | grep -E 'frappe/bench|mariadb|redis' || true
echo
echo "下一步：docker/up.sh"
