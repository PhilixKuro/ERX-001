#!/bin/bash
set -e
cd /workspace/frappe-bench
bench --site erx.localhost clear-cache
bench --site erx.localhost migrate > logs/s7-r5-ts017-demo-remigrate.log 2>&1
