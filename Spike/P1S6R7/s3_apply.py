"""TS-019 第 4、5 步：S3 收付款方向全表与改词组 → 占用重查表 + 待写 csv 行。宿主 python -I -X utf8 跑。
用法：s3_apply.py check   → 出 Spike/P1S6R7/s3_recheck.json（不写 csv）
     s3_apply.py write   → 按 s3_final.json（check 后经主 Session 判定的定稿）写 csv"""
import csv, importlib.util, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("occ", ROOT / "Spike/P1S6R4-occupancy.py")
occ = importlib.util.module_from_spec(spec); spec.loader.exec_module(occ)
data = json.loads((ROOT / "Spike/P1S6R7/s3_terms.json").read_text(encoding="utf-8"))
# 后续裁决覆盖 S3 原定（逐条有出处）
LATER = {
    "Payment": ("收付款", "DEC-035（取代 S3 §2.3.1「收付款单」）"),
    "Create Chart Of Accounts Based On": ("科目表建立方式", "DEC-021（取代 S3 §2.3.1「科目表来源」）"),
    "Unpaid": (None, "DEC-036：无 context 的 Unpaid 不写，显示官方「未付」"),
}
rows = {}
for r in data["direction"]:
    key = r["source"] + (":" + r["context"] if r.get("context") else "")
    rows.setdefault(key, {"source": r["source"], "context": r.get("context"), "target": r["target"], "from": [], "group": set()})
    rows[key]["from"].append("S3 术语标准 " + r["section"].split(" ")[0])
for g in data["groups"]:
    for c in g.get("changes", []):
        key = c["source"] + (":" + c["context"] if c.get("context") else "")
        e = rows.setdefault(key, {"source": c["source"], "context": c.get("context"), "target": c["target"], "from": [], "group": set()})
        if e["target"] != c["target"]:
            e.setdefault("conflict", []).append((g["section"], c["target"]))
        e["from"].append("S3 术语标准 " + g["section"])
        e["group"].add(g["target_word"])
merged, plain = occ._merged()
out = []
same_target = {}
for key, e in rows.items():
    same_target.setdefault(e["target"], set()).add(e["source"])
for key, e in sorted(rows.items(), key=lambda i: i[0].casefold()):
    target, note = e["target"], ""
    if e["context"] is None and e["source"] in LATER:
        target, note = LATER[e["source"]]
    item = {"key": key, "source": e["source"], "context": e["context"], "s3_target": e["target"], "target": target,
            "basis": e["from"][0], "note": note, "conflict_in_s3": e.get("conflict"),
            "current": merged.get(key), "official_key_exists": key in merged}
    if target and e["context"] is None:
        others = [o for o in occ.occupants(target) if o != e["source"] and o not in same_target.get(target, set())]
        item["occupants"] = others
    out.append(item)
(ROOT / "Spike/P1S6R7/s3_recheck.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print(len(out), "rows;", sum(1 for i in out if i.get("occupants")), "occupied;", sum(1 for i in out if i["conflict_in_s3"]), "s3-internal conflicts")
for i in out:
    if i.get("occupants") or i["conflict_in_s3"] or i["note"]:
        print(i["key"], "→", i["target"], "| occ:", i.get("occupants"), "| s3conf:", i["conflict_in_s3"], "|", i["note"])
