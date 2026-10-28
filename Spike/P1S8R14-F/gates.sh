#!/bin/bash
# R14 F re-review validation gates, run in the container: full Python, Node, Ruff and build for the apps given (default both). Logs go to frappe-bench/logs/s8-r14f-*
cd /workspace/frappe-bench || exit 1
L=logs
P=s8-r14f
apps=${*:-frappe_debug frappe_china}
echo "start $(date -Is) apps=$apps" >> $L/$P-gates.summary
for a in frappe_china frappe_debug; do echo "$a $(git -C apps/$a rev-parse --short HEAD) dirty=$(git -C apps/$a status --short | wc -l)" >> $L/$P-gates.summary; done
for app in $apps; do
  s=$(date +%s)
  bench --site test.localhost run-tests --app $app > $L/$P-full-$app.log 2>&1
  echo "$app python exit=$? secs=$(( $(date +%s)-s )) $(grep -E '^Ran ' $L/$P-full-$app.log | tail -1)" >> $L/$P-gates.summary
  (cd apps/$app && node --test $app/tests/*.cjs) > $L/$P-node-$app.log 2>&1
  echo "$app node exit=$? $(grep -E '^# (pass|fail)' $L/$P-node-$app.log | tr '\n' ' ')" >> $L/$P-gates.summary
  (cd apps/$app && ../../env/bin/ruff check . && ../../env/bin/ruff format --check .) > $L/$P-ruff-$app.log 2>&1
  echo "$app ruff exit=$?" >> $L/$P-gates.summary
  bench build --app $app >> $L/$P-build.log 2>&1; echo "build $app exit=$?" >> $L/$P-gates.summary
done
echo "end $(date -Is)" >> $L/$P-gates.summary
