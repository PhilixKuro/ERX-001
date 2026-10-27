#!/bin/bash
# Hammer snapshot_status while erx jumps to act 1 and returns to base; keep any 500 body.
H="Host: erx.localhost"; U=http://127.0.0.1:8000/api/method
sid=$(curl -s -i -H "$H" -H "Content-Type: application/json" -d '{"usr":"Administrator","pwd":"admin"}' $U/login | grep -o "sid=[^;]*" | head -1)
out=frappe-bench/logs/s8-r8sb-status500.txt; : > $out
( for i in $(seq 1 400); do b=$(curl -s -w ' HTTP%{http_code}' -X POST -H "$H" -H "Cookie: $sid" -H "Content-Type: application/json" -d '{}' $U/frappe_debug.demo.snapshot.snapshot_status); case "$b" in *HTTP500*) echo "$b" >> $out;; esac; sleep 0.1; done ) &
loop=$!
base=$(curl -s -X POST -H "$H" -H "Cookie: $sid" -H "Content-Type: application/json" -d '{}' $U/frappe_debug.demo.snapshot.snapshot_status | python -c "import sys,json;print(json.load(sys.stdin)['message']['base_db'])")
echo base=$base
curl -s -o /dev/null -w "jump %{http_code}\n" -X POST -H "$H" -H "Cookie: $sid" -H "Content-Type: application/json" -d '{"act":1,"purpose":"jump"}' $U/frappe_debug.demo.switch.switch_to_act
sleep 3
curl -s -o /dev/null -w "return %{http_code}\n" -X POST -H "$H" -H "Cookie: $sid" -H "Content-Type: application/json" -d "{\"db_name\":\"$base\"}" $U/frappe_debug.demo.switch.switch_to_db
wait $loop
echo "500s: $(grep -c HTTP500 $out)"
