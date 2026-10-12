"""S3 改词的落法：演示面出处是 DocType 字段 → 按该 DocType 写 context 行；是 JS 字面量／侧栏／首页 → 只能写无 context 行。宿主 python -I -X utf8 跑。"""
import importlib.util, json, re
from collections import defaultdict
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("bl", ROOT / "Spike/P1S6R4-baseline.py")
bl = importlib.util.module_from_spec(spec); spec.loader.exec_module(bl)
index = bl.doctypes()
by_path = {path.relative_to(ROOT.parent if False else bl.PROJECT).as_posix(): name for name, (path, _) in index.items()}
demo = json.loads((ROOT / "Spike/P1S6R7-baseline-ts018.json").read_text(encoding="utf-8"))["demo_surface"]
rows = json.loads((ROOT / "Spike/P1S6R7/s3_recheck.json").read_text(encoding="utf-8"))
out = []
for r in rows:
    if r["context"] or not r["target"]:
        continue
    contexts, plain = set(), []
    for ref in demo.get(r["source"], []):
        m = re.match(r"(.+\.json):(\w+)$", ref)
        if m and m.group(1) in by_path:
            contexts.add(by_path[m.group(1)])
        else:
            plain.append(ref)
    out.append({"source": r["source"], "target": r["target"], "basis": r["basis"], "contexts": sorted(contexts), "plain_refs": plain})
(ROOT / "Spike/P1S6R7/s3_place.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
for x in out:
    print(f"{x['source']!r} → {x['target']} | ctx {x['contexts']} | plain {[p.split('/')[-1] for p in x['plain_refs']]}")
