#!/bin/bash
set -e
cd /workspace/frappe-bench
bench --site erx.localhost execute "exec(open('/workspace/Spike/P1S7R5-D/ts017-clean-errors.py', encoding='utf-8').read(), globals())" > logs/s7-r5-ts017-clean-errors.log 2>&1
