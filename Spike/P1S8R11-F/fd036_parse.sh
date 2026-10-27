#!/bin/bash
# FD-036 复验：用真实 apps.json 跑 setup.sh 的解析，再按第 4 段新旧两种 read 写法读，打印 app_official
cd /workspace || exit 1
entries=$(sed -n '/^app_entries=\$(/,/^) ||/p' docker/scripts/setup.sh | sed '1s/.*/frappe-bench\/env\/bin\/python - docker\/apps.json <<'"'"'PY'"'"'/; $d' | bash)
echo "== new (line 272 now)"
while IFS=$'\t' read -r app_url app_ref app_commit app_name app_official _app_demo_only; do
  printf '%-14s official=%q demo_only=%q\n' "$app_name" "$app_official" "$_app_demo_only"
done <<<"$entries"
echo "== old (5 vars)"
while IFS=$'\t' read -r app_url app_ref app_commit app_name app_official; do
  printf '%-14s official=%q\n' "$app_name" "$app_official"
done <<<"$entries"
