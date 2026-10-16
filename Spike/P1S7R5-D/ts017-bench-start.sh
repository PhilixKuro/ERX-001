#!/bin/bash
set -e
cd /workspace/frappe-bench
exec bench start > logs/bench-start.log 2>&1
