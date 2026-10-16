#!/bin/bash
set -e
cd /workspace/frappe-bench
bench --site erx.localhost execute "exec(open('/workspace/Spike/P1S7R5-D/ts017-diagnose.py', encoding='utf-8').read(), globals())"
