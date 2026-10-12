"""TS-018 回归查漏：被清场删掉、但本 app 非 _() 代码（字面量元组、JS Set 等）仍按键取用的行。宿主 python -I -X utf8 跑。
判法：pruned.csv 的键以引号字面量出现在 frappe_china 的 .py/.js/.html（不含 tests、translations）里，且合并字典现无中文。
产出 Spike/P1S6R7/prune_restore.csv／.json（供 apply_rows）。"""
import csv, importlib.util, json, re
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "frappe-bench/apps/frappe_china/frappe_china"
s = importlib.util.spec_from_file_location("bl", ROOT / "Spike/P1S6R4-baseline.py"); bl = importlib.util.module_from_spec(s); s.loader.exec_module(bl)
merged, _ = bl.merged_dict()
CJK = re.compile(r"[一-鿿]")
code = {}
for p in [*APP.rglob("*.py"), *APP.rglob("*.js"), *APP.rglob("*.html")]:
    if "tests" in p.parts or "translations" in p.parts or "node_modules" in p.parts:
        continue
    code[p.relative_to(APP).as_posix()] = p.read_text(encoding="utf-8", errors="replace")
restore, meta, report = [], {}, []
for r in csv.reader((ROOT / "Spike/P1S6R6-pruned.csv").open(encoding="utf-8", newline="")):
    if not r:
        continue
    key = r[0] + (":" + r[2] if len(r) == 3 and r[2] else "")
    if merged.get(key) and CJK.search(merged[key]):
        continue
    hits = [f for f, text in code.items() if f"'{r[0]}'" in text or f'"{r[0]}"' in text]
    if hits:
        restore.append(r)
        meta[key] = {"basis": "DEC-026（R4 TS-014 独立前端入口适配；本 app 字面量取用，TS-018 误删后恢复）", "named": False}
        report.append({"key": key, "value": r[1], "used_in": hits})
with (ROOT / "Spike/P1S6R7/prune_restore.csv").open("w", encoding="utf-8", newline="") as h:
    csv.writer(h, lineterminator="\n").writerows(restore)
(ROOT / "Spike/P1S6R7/prune_restore.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
(ROOT / "Spike/P1S6R7/prune_restore_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
print(len(restore), "rows to restore")
for x in report:
    print(" ", repr(x["key"]), "->", x["value"], "|", x["used_in"])
