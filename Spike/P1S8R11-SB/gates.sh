#!/bin/bash
# R11 SB 验证门：容器内跑两 app 全量 Python、Node、Ruff、构建（测工作树）。日志落 frappe-bench/logs/s8-r11sb-*
cd /workspace/frappe-bench || exit 1
L=logs
P=s8-r11sb
echo "start $(date -Is)" > $L/$P-gates.summary
for a in frappe_china frappe_debug; do echo "$a $(git -C apps/$a rev-parse --short HEAD) dirty=$(git -C apps/$a status --short | wc -l)" >> $L/$P-gates.summary; done
for app in frappe_debug frappe_china; do
  s=$(date +%s)
  bench --site test.localhost run-tests --app $app > $L/$P-full-$app.log 2>&1
  echo "$app python exit=$? secs=$(( $(date +%s)-s ))" >> $L/$P-gates.summary
done
for app in frappe_debug frappe_china; do
  (cd apps/$app && node --test $app/tests/*.cjs) > $L/$P-node-$app.log 2>&1
  echo "$app node exit=$?" >> $L/$P-gates.summary
  (cd apps/$app && ../../env/bin/ruff check . && ../../env/bin/ruff format --check .) > $L/$P-ruff-$app.log 2>&1
  echo "$app ruff exit=$?" >> $L/$P-gates.summary
done
bench build --app frappe_debug > $L/$P-build.log 2>&1; echo "build debug exit=$?" >> $L/$P-gates.summary
bench build --app frappe_china >> $L/$P-build.log 2>&1; echo "build china exit=$?" >> $L/$P-gates.summary
echo "end $(date -Is)" >> $L/$P-gates.summary
