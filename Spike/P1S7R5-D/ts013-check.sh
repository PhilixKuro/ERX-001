#!/bin/bash
set -e
cd /workspace/frappe-bench
bench --site test.localhost execute "exec(open('/workspace/Spike/P1S7R5-D/update-s7-translations.py', encoding='utf-8').read(), globals())"
bench --site test.localhost run-tests --module frappe_china.tests.test_piece_rate > logs/s7-r5-ts013-green-recheck.log 2>&1
tail -60 logs/s7-r5-ts013-green-recheck.log
