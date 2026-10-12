"""把若干 part csv 合成一批 rows.csv + meta.json 供 apply_rows.py 用。宿主 python -I -X utf8 Spike/P1S6R7/demo_meta.py <out_prefix> <part.csv>...
依据一律 DEC-001（演示线档补缺：合并字典无中文）；与官方交集的键由 apply_rows 自动进 OVERRIDES。"""
import csv, json, sys
from pathlib import Path
args = sys.argv[1:]
basis = "DEC-001（演示线档补缺：合并字典无中文）"
if args and args[0].startswith("--basis="):
    basis = args.pop(0).split("=", 1)[1]
out, parts = Path(args[0]), args[1:]
rows, meta = [], {}
for part in parts:
    for row in csv.reader(open(part, encoding="utf-8-sig", newline="")):
        if not row:
            continue
        # 与 apply_rows.key_of 同：按 Frappe 读 csv 的方式把源词里的字面反斜杠 n 换成换行
        key = row[0].replace("\\n", "\n") + (":" + row[2] if len(row) == 3 and row[2] else "")
        rows.append(row)
        meta[key] = {"basis": basis, "named": False}
with open(str(out) + ".csv", "w", encoding="utf-8", newline="") as h:
    csv.writer(h, lineterminator="\n").writerows(rows)
Path(str(out) + ".json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
print(len(rows), "rows")
