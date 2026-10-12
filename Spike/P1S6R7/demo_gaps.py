"""TS-019 第 1 步：演示面中合并字典无中文的键，按出处分块导出（每块 ≤150）。宿主 python -I -X utf8 跑。"""
import importlib.util, json, re, sys
from collections import defaultdict
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("baseline", ROOT / "Spike/P1S6R4-baseline.py")
bl = importlib.util.module_from_spec(spec); spec.loader.exec_module(bl)
spec = importlib.util.spec_from_file_location("wl", ROOT / "frappe-bench/apps/frappe_china/frappe_china/tests/translation_whitelist.py")
wl = importlib.util.module_from_spec(spec); spec.loader.exec_module(wl)
CJK = re.compile(r"[一-鿿]")
data = json.loads((ROOT / sys.argv[1]).read_text(encoding="utf-8"))
merged, _ = bl.merged_dict()
surface = data["demo_surface"]

def context_lines(ref):
    # ref 形如 path:line 或 path:fieldname 或 path
    m = re.match(r"(.+?\.(?:json|js|py|vue|tsx?|jsx|md)):?(.*)$", ref)
    if not m:
        return None
    path = ROOT / m.group(1)
    if not path.exists():
        return None
    lines = path.read_text(encoding="utf-8-sig", errors="replace").splitlines()
    tail = m.group(2)
    if tail.isdigit():
        i = int(tail) - 1
    elif tail:
        i = next((n for n, l in enumerate(lines) if f'"fieldname": "{tail}"' in l or f'"fieldname":"{tail}"' in l), None)
        if i is None:
            return None
    else:
        return None
    return "\n".join(lines[max(0, i - 3): i + 4])

todo = []
for key, refs in surface.items():
    if key in wl.UNTRANSLATED:
        continue
    value = merged.get(key)
    if CJK.search(key) or (value and CJK.search(value)):
        continue  # 源词本身是中文（自有侧栏的报表名），或已有中文
    identity = not value or value == key
    if not identity and not re.search(r"[a-z]{2}", key):
        continue  # 官方给了非中文但非原样的值（如 A+ → A +），属代码类，不处理
    kind = "code" if not re.search(r"[a-z]{2}", key) or re.search(r"\.YYYY\.|\.#|^[A-Z]+-[A-Z-]*$", key) else ""
    todo.append((key, refs, kind))
print("todo", len(todo), "code-like", sum(1 for t in todo if t[2]))
for key, refs, kind in todo:
    if kind:
        print("  CODE", repr(key), merged.get(key), refs[0][-60:])
groups = defaultdict(list)
for key, refs, kind in todo:
    first = refs[0] if refs else ""
    group = first.split("/")[2] if first.startswith("frappe-bench/apps/") else "named"
    if kind:
        continue
    groups[group].append({"key": key, "refs": refs[:6], "current": merged.get(key), "context": context_lines(first) if first else None})
out = ROOT / "Spike/P1S6R6-demo"; out.mkdir(exist_ok=True)
n = 0
for group in sorted(groups):
    items = sorted(groups[group], key=lambda x: x["key"].casefold())
    for i in range(0, len(items), 150):
        n += 1
        (out / f"in-{n:02d}.json").write_text(json.dumps({"group": group, "items": items[i:i + 150]}, ensure_ascii=False, indent=1), encoding="utf-8")
        print(n, group, len(items[i:i + 150]))
