#!/bin/bash
set -e
cd /workspace/frappe-bench
bench build --app frappe_china > logs/s7-r5-ts017-build.log 2>&1
