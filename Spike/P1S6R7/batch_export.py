"""TS-021 第 1 步：重跑基线后取剩余缺口（演示面外），按 app 分块（每块 ≤300）导出 Spike/P1S6R6-batch/in-{app}-{nn}.json。
宿主 python -I -X utf8 Spike/P1S6R7/batch_export.py <baseline.json>。键、出处、出处前后各 3 行源码。"""
import importlib.util, json, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("dg", ROOT / "Spike/P1S6R7/demo_gaps.py")
data = json.loads((ROOT / sys.argv[1]).read_text(encoding="utf-8"))
surface = data["demo_surface"]
CJK = re.compile(r"[一-鿿]")

def context_lines(app, ref):
    m = re.match(r"(.+?):(\d+)$", ref)
    path = ROOT / "frappe-bench/apps" / app / (m.group(1) if m else ref)
    if not path.exists() or path.is_dir():
        return None
    lines = path.read_text(encoding="utf-8-sig", errors="replace").splitlines()
    if m:
        i = int(m.group(2)) - 1
        return "\n".join(lines[max(0, i - 3): i + 4])
    return None

def json_context(app, ref, key):
    path = ROOT / "frappe-bench/apps" / app / ref
    if not path.suffix == ".json" or not path.exists():
        return None
    lines = path.read_text(encoding="utf-8-sig", errors="replace").splitlines()
    needle = json.dumps(key, ensure_ascii=False)[1:-1][:60]
    i = next((n for n, l in enumerate(lines) if needle and needle in l), None)
    return None if i is None else "\n".join(lines[max(0, i - 3): i + 4])

out = ROOT / "Spike/P1S6R6-batch"
for old in out.glob("in-*.json"):
    old.unlink()
total = {}
seen = {}
code_like = []
CODE = re.compile(r"^\S*(\.YYYY\.|\.#)\S*$|^[A-Z0-9]+(-[A-Z0-9]+)*-?$")
# 无小写词但须译的：Raven 私信、财年、季度、示例前缀、SQL 关键字提示
MUST_TRANSLATE = {"DM", "DMs", "FY", "Q1", "Q2", "Q3", "Q4", "FROM", "API URL", "REST API"}
for app, items in data["gaps"].items():
    rows = []
    for key, refs in items:
        if key in seen:  # 同一源词在多个 app 的 main.pot 里：只交第一个 app 的块译，出处并入
            seen[key]["refs"].extend(f"{app}/{r}" for r in refs[:3])
            continue
        if key not in MUST_TRANSLATE and "e.g." not in key and (not re.search(r"[a-z]{2}", key) or CODE.search(key)):
            code_like.append({"key": key, "app": app, "refs": [f"{app}/{r}" for r in refs[:4]]})
            seen[key] = {"refs": []}
            continue
        source = key.split(":")[0] if ":" in key and key not in surface else key
        if key in surface or source in surface:
            continue
        ctx = None
        for ref in refs[:3]:
            ctx = context_lines(app, ref) or json_context(app, ref, source)
            if ctx:
                break
        row = {"key": key, "refs": [f"{app}/{r}" for r in refs[:6]], "current": None, "context": ctx}
        seen[key] = row
        rows.append(row)
    rows.sort(key=lambda r: r["key"].casefold())
    total[app] = len(rows)
    for n, i in enumerate(range(0, len(rows), 300), 1):
        (out / f"in-{app}-{n:02d}.json").write_text(json.dumps({"group": app, "items": rows[i:i + 300]}, ensure_ascii=False, indent=1), encoding="utf-8")
(ROOT / "Spike/P1S6R7/code_like.json").write_text(json.dumps(code_like, ensure_ascii=False, indent=1), encoding="utf-8")
print(total, sum(total.values()), "blocks:", len(list(out.glob("in-*.json"))), "code-like:", len(code_like))
