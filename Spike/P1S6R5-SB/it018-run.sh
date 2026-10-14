#!/usr/bin/env bash
# R5 IT-018：不刷新六例中例 1、3、4、5 的可照做命令序列（宿主 Git Bash 里在项目根执行）。
# 前置：容器 erx001-frappe-1 在跑、`bench start` 的 socketio（9100）在跑；测试站 6787 未被占用。
# 例 2 只记结论（LG-073）；例 6 在演示站只读，本次不复跑（R5 报告未点名它）。
set -euo pipefail
export MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*'
cd "$(dirname "$0")/../.."
PY="docker exec -u frappe -w /workspace/frappe-bench erx001-frappe-1 ./env/bin/python"
BENCH="docker exec -u frappe -w /workspace/frappe-bench erx001-frappe-1 /home/frappe/.local/bin/bench"
OUT=Spike/P1S6R5-SB/it018
step() { echo "== $(date '+%F %T') $*"; }

step "0a 容器 /etc/hosts 临时加 test.localhost：实时服务鉴权时按页面 Origin 回调站点（realtime/utils.js:4-15），容器里解析不了 test.localhost 就报 Unauthorized: fetch failed；退出时还原"
docker exec -u root erx001-frappe-1 sh -c 'getent hosts test.localhost >/dev/null || { cp /etc/hosts /tmp/hosts.it018.bak; echo "127.0.0.1 test.localhost  # P1-S6-R5 SB IT-018 temporary" >> /etc/hosts; }'
# 退出时停掉第 0 步起的 6787，并还原 hosts（R11 IT-057：序列须写全 6787 启停）
trap 'docker exec -u frappe erx001-frappe-1 sh -c "pkill -f \"serve --port 6787\"" || true; docker exec -u root erx001-frappe-1 sh -c "[ -f /tmp/hosts.it018.bak ] && cp /tmp/hosts.it018.bak /etc/hosts && rm /tmp/hosts.it018.bak; getent hosts test.localhost || echo hosts restored"' EXIT
step "0 重起测试站 6787，带 DEV_SERVER=1：不带时页面按自身 6787 连 socket.io、得 404，实时通道不通（socketio_client.js:120-127）"
docker exec -u frappe erx001-frappe-1 sh -c 'pkill -f "serve --port 6787"' || true
sleep 2
if true; then
  docker exec -d -u frappe -w /workspace/frappe-bench/sites erx001-frappe-1 sh -c "DEV_SERVER=1 ../env/bin/python -m frappe.utils.bench_helper frappe --site test.localhost serve --port 6787 > /workspace/frappe-bench/logs/serve-6787-it018.log 2>&1"  # 长跑日志不写受管目录（开发守则，R13 FD-050）
  for i in $(seq 1 60); do [ "$(curl -s -o /dev/null -w '%{http_code}' --max-time 5 http://127.0.0.1:6787/api/method/ping || true)" = 200 ] && break; sleep 1; done
fi
step "1 造数据：公司 _FCT S6 Part3、仓库、员工、两个物料、工序、两张日记账、期初库存、一张物料移动"
$PY /workspace/Spike/P1S6R5-SB/it018-part3-data.py prepare > $OUT/01-prepare.json
step "2 造工作站（BOM 的工序行要用）"
$PY /workspace/Spike/P1S6R5-SB/it018-part3-data.py manufacturing-setup > $OUT/02-workstation.json
step "3 例 3：浏览器新建 BOM（1 行原料、1 道工序）→ 点保存 → 不刷新读提交按钮；脚本内先验实时通道"
node Spike/P1S6R5-SB/it018-refresh-check.js bom > $OUT/03-bom.out
step "4 用例 3 那张 BOM 提交并建工单（关产能计划）、取出唯一的任务单、设跳过发料"
$PY /workspace/Spike/P1S6R5-SB/it018-part3-data.py work-order > $OUT/04-work-order.json
step "5 例 4：浏览器在任务单上 开始（选员工）→ 暂停 → 继续 → 完成，每步读库里时间行；脚本内先验实时通道"
node Spike/P1S6R5-SB/it018-refresh-check.js job > $OUT/05-job.out
step "6 例 1、5：先验实时通道，再从业务流程侧栏点 Account／Warehouse／Cost Center／Company／Employee，干净状态与进过列表视图各一轮"
node Spike/P1S6R5-SB/it018-tree-rounds.js > $OUT/06-tree.out
step "7 清理：按状态文件倒序取消并删除本次造的单据、删公司，核无残留"
$PY /workspace/Spike/P1S6R5-SB/it018-part3-data.py cleanup > $OUT/07-cleanup.json
step DONE
