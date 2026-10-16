#!/bin/bash
set -e
cd /workspace/frappe-bench
bench --site test.localhost execute "exec(open('/workspace/Spike/P1S7R5-D/ts017-replay.py', encoding='utf-8').read(), globals())" > logs/s7-r5-ts017-replay.log 2>&1
