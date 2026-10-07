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
python - "$BENCH" <<'PY'
import pathlib
import subprocess
import sys

bench = pathlib.Path(sys.argv[1])
entries = __import__("json").loads(pathlib.Path("apps.json").read_text(encoding="utf-8"))
declared = set()
for entry in entries:
    name = entry.get("app_name") or entry["url"].rstrip("/").rsplit("/", 1)[-1].removesuffix(".git")
    declared.add(name)
    repo = bench / "apps" / name
    if not (repo / ".git").exists():
        print(f"    {name:<12} 未克隆（apps.json 条目保留）")
        continue
    sha = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
    ref = f"tag={entry['tag']}" if entry.get("tag") else f"branch={entry.get('branch') or '未记录'}"
    # 记录值之外另显示仓库实际所在的 ref，两者不同时一眼可见（P1-S5-R9 F 审核 FD-011）
    actual = (
        subprocess.run(["git", "-C", str(repo), "symbolic-ref", "-q", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
        or subprocess.run(["git", "-C", str(repo), "describe", "--tags", "--exact-match", "HEAD"], capture_output=True, text=True).stdout.strip()
        or "游离"
    )
    ref = f"{ref}（实际 {actual}）"
    official = " official" if entry.get("official") else ""
    dirty = len(subprocess.check_output(["git", "-C", str(repo), "status", "--porcelain"], text=True).splitlines())
    suffix = f"  (有 {dirty} 项未提交改动)" if dirty else ""
    print(f"    {name:<12} {sha[:12]}  {ref}{official}{suffix}")
for repo in sorted((bench / "apps").iterdir()):
    if (repo / ".git").exists() and repo.name not in declared:
        print(f"    警告：apps/{repo.name} 未在 apps.json 声明")
PY

[ "${1:-}" = "--show" ] && exit 0

echo "==> 写入 apps.json"
python - "$BENCH" <<'PY'
import json
import pathlib
import subprocess
import sys

bench = pathlib.Path(sys.argv[1])
apps_json = pathlib.Path("apps.json")
entries = json.loads(apps_json.read_text(encoding="utf-8"))
out = []
declared = set()

def git(repo, *args):
    return subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, check=False
    ).stdout.strip()

for entry in entries:
    name = entry.get("app_name") or entry["url"].rstrip("/").rsplit("/", 1)[-1].removesuffix(".git")
    declared.add(name)
    repo = bench / "apps" / name
    if not (repo / ".git").exists():
        print(f"警告：{name} 未克隆，原样保留 apps.json 条目")
        out.append(entry)
        continue

    if entry.get("official"):
        url = entry["url"]
    else:
        url = git(repo, "remote", "get-url", "origin") or git(repo, "remote", "get-url", "upstream") or entry["url"]

    entry.update({"url": url, "commit": git(repo, "rev-parse", "HEAD"), "app_name": name})
    if entry.get("tag"):
        tag_commit = git(repo, "rev-parse", "-q", "--verify", f"refs/tags/{entry['tag']}^{{commit}}")
        if tag_commit != entry["commit"]:
            print(f"警告：{name} HEAD 不在 tag {entry['tag']} 上（tag 指向 {tag_commit[:12] or '不存在'}），"
                  "写出的条目 tag 与 commit 对不上，请改 tag 或改用 branch（P1-S5-R9 F 审核 FD-011）")
        entry.pop("branch", None)
    else:
        branch = git(repo, "symbolic-ref", "-q", "--short", "HEAD")
        if branch:
            entry["branch"] = branch
        else:
            print(f"警告：{name} HEAD 游离，branch 沿用 apps.json")
        entry.pop("tag", None)
    out.append(entry)

for repo in sorted((bench / "apps").iterdir()):
    if not (repo / ".git").exists() or repo.name in declared:
        continue
    print(f"警告：发现新 app {repo.name}，已追加到末尾，请确认装载顺序")
    origin = git(repo, "remote", "get-url", "origin")
    entry = {"url": origin or git(repo, "remote", "get-url", "upstream")}
    # 只有 upstream、没有 origin 的是官方仓库：标 official，否则下次 setup.sh 会给它配一个
    # 指向官方仓库、可推送的 origin（P1-S5-R9 F 审核 FD-010）
    if not origin:
        entry["official"] = True
        print(f"警告：{repo.name} 没有 origin，按官方仓库标 official=true，请确认")
    branch = git(repo, "symbolic-ref", "-q", "--short", "HEAD")
    tag = "" if branch else git(repo, "describe", "--tags", "--exact-match", "HEAD")
    if branch:
        entry["branch"] = branch
    elif tag:
        entry["tag"] = tag
    else:
        print(f"警告：{repo.name} HEAD 游离且不在任何 tag 上，未写 branch／tag，请手工补（否则重建时退到缺省分支）")
    entry.update({"commit": git(repo, "rev-parse", "HEAD"), "app_name": repo.name})
    out.append(entry)

apps_json.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
for entry in out:
    ref = f"tag={entry['tag']}" if entry.get("tag") else f"branch={entry.get('branch', '未记录')}"
    official = " official" if entry.get("official") else ""
    print(f"    {entry['app_name']:<20} {entry['commit'][:12]}  {ref}{official}")
PY

cat <<EOF

已锁定。apps.json 会随 git 走，换机器时 up.sh 按它 checkout；文件顺序就是装载顺序。
official=true 表示官方仓库，只保留只读 upstream；tag 与 branch 二选一，tag 优先。

解除锁定：删掉 apps.json 里对应的 commit 字段（保留 branch 即取最新）。
EOF
