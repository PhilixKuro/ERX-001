"""S3 改词各源词在六 app main.pot 的出处数与演示面出处（判无 context 行的波及面）。宿主 python -I -X utf8 跑。"""
import importlib.util, json, sys
from collections import defaultdict
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("bl", ROOT / "Spike/P1S6R4-baseline.py")
bl = importlib.util.module_from_spec(spec); spec.loader.exec_module(bl)
refs = defaultdict(list)
for app in bl.APPS[:-1]:
    for e in bl.parse_po(bl.app_path(app) / "locale/main.pot"):
        if not e["context"]:
            refs[e["id"]].extend(f"{app}/{r}" for r in e["refs"])
demo = json.loads((ROOT / "Spike/P1S6R7-baseline-ts018.json").read_text(encoding="utf-8"))["demo_surface"]
rows = json.loads((ROOT / "Spike/P1S6R7/s3_recheck.json").read_text(encoding="utf-8"))
out = []
for r in rows:
    if r["context"] or not r["target"]:
        continue
    s = r["source"]
    out.append({"key": s, "target": r["target"], "pot_refs": len(refs[s]), "demo_refs": demo.get(s, []), "all_refs": refs[s][:40]})
out.sort(key=lambda x: -x["pot_refs"])
(ROOT / "Spike/P1S6R7/s3_spread.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
for x in out:
    print(f'{x["pot_refs"]:4d} {len(x["demo_refs"]):3d}  {x["key"]!r} → {x["target"]}')
