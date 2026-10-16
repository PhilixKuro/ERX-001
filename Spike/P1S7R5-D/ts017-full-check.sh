#!/bin/bash
set -e
cd /workspace/frappe-bench
env/bin/ruff check apps/frappe_china --fix
env/bin/ruff format apps/frappe_china
bench --site test.localhost execute "exec(open('/workspace/Spike/P1S7R5-D/update-s7-translations.py', encoding='utf-8').read(), globals())"
bench --site test.localhost clear-cache
node --test apps/frappe_china/frappe_china/tests/*.cjs > logs/s7-r5-part3-node.log 2>&1
bench --site test.localhost run-tests --app frappe_china > logs/s7-r5-ts017-full.log 2>&1
bench --site test.localhost execute frappe_china.translation_check.run > logs/s7-r5-ts017-test-selfcheck.log 2>&1
