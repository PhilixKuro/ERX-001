"""对 collision_effective.json 的仍撞组做机械同义判定（S3 DEC-075 同义判据的可机械部分）：
大小写、空白、单复数（s/es/ies）、标点与括号写法、Qty/Quantity、Id/ID、缩写全称对照表。其余列为待人工判。
宿主 python -I -X utf8 跑，出 Spike/P1S6R7/collision_classes.json。"""
import json, re
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
d = json.loads((ROOT / "Spike/P1S6R7/collision_effective.json").read_text(encoding="utf-8"))
ABBR = {"qty": "quantity", "amt": "amount", "id": "id", "uom": "unitofmeasure", "mps": "masterproductionschedule",
        "dr": "debit", "cr": "credit", "info": "details", "docname": "documentname"}
def norm(s):
    s = s.casefold().replace("&", "and")
    words = re.findall(r"[a-z0-9%]+", s)
    out = []
    for w in words:
        w = ABBR.get(w, w)
        if len(w) > 3 and w.endswith("ies"): w = w[:-3] + "y"
        elif len(w) > 3 and w.endswith("es") and w[-3] in "sxz": w = w[:-2]
        elif len(w) > 2 and w.endswith("s") and not w.endswith("ss"): w = w[:-1]
        out.append(w)
    return "".join(out)
auto, manual = [], []
for g in d["still_groups"]:
    for value, sources in g["clashes"].items():
        keys = {norm(s) for s in sources}
        (auto if len(keys) == 1 else manual).append({"target": value, "sources": sources})
(ROOT / "Spike/P1S6R7/collision_classes.json").write_text(json.dumps({"auto_synonym": auto, "manual": manual}, ensure_ascii=False, indent=1), encoding="utf-8")
print("auto synonym", len(auto), "manual", len(manual))
for m in manual:
    print(m["target"], "|", " / ".join(m["sources"]))
