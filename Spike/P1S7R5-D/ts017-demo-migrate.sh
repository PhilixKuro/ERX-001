#!/bin/bash
set -e
cd /workspace/frappe-bench
bench --site erx.localhost execute "exec(open('/workspace/Spike/P1S7R5-D/ts017-clean-demo.py', encoding='utf-8').read(), globals())" > logs/s7-r5-ts017-demo-clean.log 2>&1
bench --site erx.localhost migrate > logs/s7-r5-ts017-demo-migrate.log 2>&1
