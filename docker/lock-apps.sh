#!/usr/bin/env bash
# 把各 app 当前的 commit 写进 docker/apps.json，锁定精确版本。
#
# 什么时候跑：合并上游后、或确认当前版本可用后。
# 作用：换机器时 up.sh 会 checkout 到这些 commit，而不是分支的最新提交——
# 否则两台机器可能拿到不同版本。
#
#   docker/lock-apps.sh          写入当前 commit
#   docker/lock-apps.sh --show   只显示，不写
set -euo pipefail
export MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*'

cd "$(dirname "$0")"
[ -f .env ] && { set -a; . ./.env; set +a; }
BENCH="../${BENCH_NAME:-frappe-bench}"

[ -d "$BENCH/apps" ] || { echo "找不到 $BENCH/apps，先跑 docker/up.sh。" >&2; exit 1; }

echo "==> 各 app 当前版本"
for d in "$BENCH"/apps/*/; do
  name=$(basename "$d")
  [ -d "$d/.git" ] || continue
  sha=$(git -C "$d" rev-parse HEAD)
  branch=$(git -C "$d" rev-parse --abbrev-ref HEAD)
  dirty=$(git -C "$d" status --porcelain | wc -l)
  printf '    %-12s %s  %s' "$name" "${sha:0:12}" "$branch"
  [ "$dirty" -gt 0 ] && printf '  \033[33m(有 %s 项未提交改动)\033[0m' "$dirty"
  echo
done

[ "${1:-}" = "--show" ] && exit 0

echo "==> 写入 apps.json"
python - <<PY
import json, subprocess, pathlib

bench = pathlib.Path("$BENCH")
apps_json = pathlib.Path("apps.json")
existing = {a["url"]: a for a in json.loads(apps_json.read_text(encoding="utf-8"))}

out = []
for d in sorted((bench / "apps").iterdir()):
    if not (d / ".git").exists():
        continue
    url = subprocess.run(["git", "-C", str(d), "remote", "get-url", "origin"],
                         capture_output=True, text=True).stdout.strip()
    sha = subprocess.run(["git", "-C", str(d), "rev-parse", "HEAD"],
                         capture_output=True, text=True).stdout.strip()
    branch = subprocess.run(["git", "-C", str(d), "rev-parse", "--abbrev-ref", "HEAD"],
                            capture_output=True, text=True).stdout.strip()
    entry = existing.get(url, {})
    entry.update({"url": url, "branch": branch, "commit": sha})
    out.append(entry)

apps_json.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
for a in out:
    print(f"    {a['url'].rsplit('/', 1)[-1]:20} {a['commit'][:12]}")
PY

cat <<EOF

已锁定。apps.json 会随 git 走，换机器时 up.sh 按它 checkout。

解除锁定：删掉 apps.json 里对应的 commit 字段（保留 branch 即取最新）。
EOF
