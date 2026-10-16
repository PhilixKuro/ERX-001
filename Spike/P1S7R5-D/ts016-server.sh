#!/bin/bash
cd /workspace/frappe-bench
exec bench --site test.localhost serve --port 6787 --noreload > logs/s7-r5-ts016-web.log 2>&1
