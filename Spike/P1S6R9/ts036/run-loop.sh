#!/usr/bin/env bash
# R9 TS-036 第 4 步：演示站按次序造数，任一步失败即停（同 R7 ts023/run-loop.sh，加 cancel-opens）
cd /workspace/frappe-bench
for a in masters receipt purchase-invoice purchase-payment sales-order production-plan work-order transfer manufacture delivery sales-invoice sales-payment finish closing drafts opens cancel-opens crm; do
  echo "=== $a"
  env/bin/python /workspace/Spike/P1S6R9/closed-loop.py erx.localhost "$a" > /workspace/Spike/P1S6R9/ts036/loop-$a.out 2>&1 || { echo "FAILED $a"; tail -20 /workspace/Spike/P1S6R9/ts036/loop-$a.out; exit 1; }
done
echo ALL-OK
