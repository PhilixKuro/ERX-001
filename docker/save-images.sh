#!/usr/bin/env bash
# 把镜像导出成文件，供无网络的新电脑离线导入。
#
# 不跑这个也能换电脑——up.sh 会自己 docker pull。只有新电脑没网时才需要。
# 导出物约 4.5GB，落在 docker/images/，随项目文件夹一起拷走。
set -euo pipefail
export MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*'

cd "$(dirname "$0")"
mkdir -p images

IMAGES=(frappe/bench:latest mariadb:11.8 redis:alpine)

echo "==> 检查镜像"
missing=()
for img in "${IMAGES[@]}"; do
  if docker image inspect "$img" >/dev/null 2>&1; then
    echo "    $img"
  else
    missing+=("$img")
  fi
done
if [ ${#missing[@]} -gt 0 ]; then
  echo "以下镜像本机没有，先跑 docker/up.sh 拉取：" >&2
  printf '  %s\n' "${missing[@]}" >&2
  exit 1
fi

OUT="images/erx001-images.tar"
echo "==> 导出到 $OUT（约 4.5GB，需数分钟）"
docker save "${IMAGES[@]}" -o "$OUT"

echo
echo "导出完成：$(du -h "$OUT" | cut -f1)"
echo "新电脑上先跑 docker/load-images.sh，再跑 docker/up.sh。"
