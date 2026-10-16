#!/bin/bash
set -e
cd /workspace/frappe-bench
bench --site test.localhost execute "exec(open('/workspace/Spike/P1S7R5-D/ts016-site-data.py', encoding='utf-8').read(), globals())"
