#!/usr/bin/env bash
# R5 IT-013 各轮：撤 doctype_list_js → 撤钩反证／states 原定做法／Property Setter 原定做法 → 恢复
set -euo pipefail
export MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*'
cd /d/ERX-001
H=frappe-bench/apps/frappe_china/frappe_china/hooks.py
PY="docker exec -u frappe -w /workspace/frappe-bench erx001-frappe-1 ./env/bin/python"
restart() {
  docker exec -u frappe erx001-frappe-1 sh -c 'pkill -f "serve --port 6787"' || true
  sleep 2
  docker exec -u frappe -w /workspace/frappe-bench erx001-frappe-1 /home/frappe/.local/bin/bench --site test.localhost clear-cache
  docker exec -d -u frappe -w /workspace/frappe-bench/sites erx001-frappe-1 sh -c "../env/bin/python -m frappe.utils.bench_helper frappe --site test.localhost serve --port 6787 > /workspace/frappe-bench/logs/serve-6787-it013-$1.log 2>&1"  # 长跑日志不写受管目录（开发守则，R13 FD-050）
  for i in $(seq 1 60); do c=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 http://127.0.0.1:6787/api/method/ping || true); [ "$c" = 200 ] && break; sleep 1; done
  echo "restart $1 -> $c"
}
git -C frappe-bench/apps/frappe_china status --porcelain > Spike/P1S6R5-SB/it013/git-before.txt
cp "$H" Spike/P1S6R5-SB/it013/hooks.py.bak
python - "$H" <<'PY2'
import pathlib,sys
p=pathlib.Path(sys.argv[1]);s=p.read_text(encoding='utf-8')
old='doctype_list_js = {\n\t"Sales Invoice": "public/js/invoice_list.js",\n\t"Purchase Invoice": "public/js/invoice_list.js",\n}\n'
if old not in s: old=old.replace('\n','\r\n')
assert s.count(old)==1, 'doctype_list_js block not found'
p.write_text(s.replace(old,''.join('# IT-013 unhook probe: '+l+'\n' for l in old.splitlines())),encoding='utf-8')
PY2
trap 'cp Spike/P1S6R5-SB/it013/hooks.py.bak "$H"; $PY /workspace/Spike/P1S6R5-SB/it013-setup.py states-off || true; $PY /workspace/Spike/P1S6R5-SB/it013-setup.py ps-off || true' ERR
restart unhooked
node Spike/P1S6R5-SB/it013-check.cjs unhooked > /dev/null && echo "round unhooked ok"
$PY /workspace/Spike/P1S6R5-SB/it013-setup.py states-on
node Spike/P1S6R5-SB/it013-check.cjs states > /dev/null && echo "round states ok"
$PY /workspace/Spike/P1S6R5-SB/it013-setup.py states-off
$PY /workspace/Spike/P1S6R5-SB/it013-setup.py ps-on
node Spike/P1S6R5-SB/it013-check.cjs property-setter > /dev/null && echo "round property-setter ok"
$PY /workspace/Spike/P1S6R5-SB/it013-setup.py ps-off
cp Spike/P1S6R5-SB/it013/hooks.py.bak "$H"
restart restored
git -C frappe-bench/apps/frappe_china status --porcelain > Spike/P1S6R5-SB/it013/git-after.txt
diff Spike/P1S6R5-SB/it013/git-before.txt Spike/P1S6R5-SB/it013/git-after.txt && echo "git status identical"
node Spike/P1S6R5-SB/it013-check.cjs restored > /dev/null && echo "round restored ok"
$PY /workspace/Spike/P1S6R5-SB/it013-setup.py check
echo DONE
