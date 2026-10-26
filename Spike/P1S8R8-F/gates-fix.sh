#!/bin/bash
# F 审核验证门：在容器内依次跑两 app 全量 Python、Node、Ruff、构建。日志落 frappe-bench/logs/s8-r8f-fix-*
cd /workspace/frappe-bench || exit 1
L=logs
echo "start $(date -Is)" > $L/s8-r8f-fix-gates.summary
for app in frappe_debug frappe_china; do
  s=$(date +%s)
  bench --site test.localhost run-tests --app $app > $L/s8-r8f-fix-full-$app.log 2>&1
  echo "$app python exit=$? secs=$(( $(date +%s)-s ))" >> $L/s8-r8f-fix-gates.summary
done
for app in frappe_debug frappe_china; do
  (cd apps/$app && node --test $app/tests/*.cjs) > $L/s8-r8f-fix-node-$app.log 2>&1
  echo "$app node exit=$?" >> $L/s8-r8f-fix-gates.summary
  (cd apps/$app && ../../env/bin/ruff check . && ../../env/bin/ruff format --check .) > $L/s8-r8f-fix-ruff-$app.log 2>&1
  echo "$app ruff exit=$?" >> $L/s8-r8f-fix-gates.summary
done
bench build --app frappe_debug > $L/s8-r8f-fix-build.log 2>&1; echo "build debug exit=$?" >> $L/s8-r8f-fix-gates.summary
bench build --app frappe_china >> $L/s8-r8f-fix-build.log 2>&1; echo "build china exit=$?" >> $L/s8-r8f-fix-gates.summary
echo "end $(date -Is)" >> $L/s8-r8f-fix-gates.summary
