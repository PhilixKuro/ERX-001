"""TS-019 第 3 步：demo_collisions 导成表（目标词／源词／各源词出处）。宿主 python -I -X utf8 跑。"""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
d = json.loads((ROOT / sys.argv[1]).read_text(encoding="utf-8"))
out = []
for target, g in sorted(d["demo_collisions"].items()):
    out.append({"target": target, "sources": g["sources"],
                "visible": {s: refs[:4] for s, refs in g["visible"].items()}})
(ROOT / "Spike/P1S6R7/demo_collisions.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print(len(out), sum(len(g["sources"]) for g in out))
