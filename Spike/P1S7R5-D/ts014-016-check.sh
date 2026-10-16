#!/bin/bash
set -e
cd /workspace/frappe-bench
env/bin/ruff check apps/frappe_china --fix
env/bin/ruff format apps/frappe_china
bench --site test.localhost execute "exec(open('/workspace/Spike/P1S7R5-D/update-s7-translations.py', encoding='utf-8').read(), globals())"
bench --site test.localhost reload-doc production_plus report capacity_load
bench --site test.localhost reload-doc production_plus report spc_control_chart
bench --site test.localhost reload-doc production_plus page spc_chart
bench --site test.localhost clear-cache
bench --site test.localhost run-tests --module frappe_china.tests.test_capacity_load > logs/s7-r5-ts014-green.log 2>&1
bench --site test.localhost run-tests --module frappe_china.tests.test_spc > logs/s7-r5-ts015-green.log 2>&1
bench --site test.localhost run-tests --module frappe_china.tests.test_translation_quality > logs/s7-r5-ts013-016-quality.log 2>&1
bench --site test.localhost run-tests --module frappe_china.tests.test_translations > logs/s7-r5-ts013-016-translations.log 2>&1
bench --site test.localhost execute frappe_china.translation_check.run
node --test apps/frappe_china/frappe_china/tests/*.cjs > logs/s7-r5-part3-node.log 2>&1
