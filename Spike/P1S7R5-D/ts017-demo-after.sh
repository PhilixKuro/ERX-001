#!/bin/bash
set -e
cd /workspace/frappe-bench
S7_STATE_SUFFIX=after bench --site erx.localhost execute "exec(open('/workspace/Spike/P1S7R5-D/s7-site-state.py', encoding='utf-8').read(), globals())" > logs/s7-r5-ts017-demo-after.log 2>&1
bench --site erx.localhost execute frappe_china.translation_check.run > logs/s7-r5-ts017-demo-selfcheck.log 2>&1
