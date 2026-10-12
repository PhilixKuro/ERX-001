"""TS-019 第 4、5 步落 csv（DJ-001 落法）。宿主 python -I -X utf8 跑；只产出 Spike/P1S6R7/s3_rows.csv 与 s3_rows.json（待 merge_check）。"""
import csv, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
recheck = {r["key"]: r for r in json.loads((ROOT / "Spike/P1S6R7/s3_recheck.json").read_text(encoding="utf-8"))}
place = {p["source"]: p for p in json.loads((ROOT / "Spike/P1S6R7/s3_place.json").read_text(encoding="utf-8"))}
CSV = ROOT / "frappe-bench/apps/frappe_china/frappe_china/translations/zh.csv"
existing = {}
for row in csv.reader(CSV.open(encoding="utf-8", newline="")):
    existing[row[0] + (":" + row[2] if len(row) == 3 and row[2] else "")] = row[1]
CONTEXT_ONLY = {"Selling", "Buying", "Contact", "Taxes"}          # DJ-001 例外：侧栏同名指模块／DocType，只落 S3 分析过的 DocType
SKIP_DATA = {"Stores": "服务端 _() 生成的仓库记录名", "Accountant": "fixture 职位名"}
OFFICIAL_SAME = {"Paid": "无 context 的 Paid 官方即「已付款」，不写，进 NAMED_TERMS 断言官方值"}
rows, report = [], []
def add(source, target, context, basis, why):
    key = source + (":" + context if context else "")
    if key in existing:
        report.append({"key": key, "action": "已在 csv" if existing[key] == target else "改 csv", "csv": existing[key], "target": target, "basis": basis})
        if existing[key] != target:
            rows.append([source, target, context] if context else [source, target])
        return
    rows.append([source, target, context] if context else [source, target])
    report.append({"key": key, "action": "写", "target": target, "basis": basis, "why": why})
for key, r in recheck.items():
    source, target, basis = r["source"], r["target"], r["basis"]
    if r["context"]:
        add(source, target, r["context"], basis, "S3 带 context 行")
        continue
    if target is None:
        report.append({"key": key, "action": "不写", "why": r["note"]}); continue
    if source in SKIP_DATA:
        report.append({"key": key, "action": "不写", "why": SKIP_DATA[source]}); continue
    if source in OFFICIAL_SAME:
        report.append({"key": key, "action": "不写", "why": OFFICIAL_SAME[source]}); continue
    p = place.get(source, {"contexts": [], "plain_refs": []})
    # Receivable／Payable：S3 §2.3.3 指科目类别，渲染点（account_type、Party Type、科目余额报表筛选）都是这一义，无 context 落、两者对称
    direction = basis.startswith("S3 术语标准 §1.") or source in ("Receivable", "Payable")
    if direction or (p["plain_refs"] and source not in CONTEXT_ONLY):
        add(source, target, None, basis, "无 context 行：" + ("§1 收付款方向全表落" if direction else "演示面有不带 context 的渲染点 " + ", ".join(x.split("/")[-1] for x in p["plain_refs"][:4])))
    elif p["contexts"]:
        for ctx in p["contexts"]:
            add(source, target, ctx, basis, "context 行：演示面渲染点为该 DocType 字段")
    else:
        report.append({"key": key, "action": "不写", "why": "演示面无出处（DEC-002 演示线外撞名不处理）"})
with (ROOT / "Spike/P1S6R7/s3_rows.csv").open("w", encoding="utf-8", newline="") as h:
    csv.writer(h, lineterminator="\n").writerows(rows)
meta = {}
for r in report:
    if r["action"] in ("写", "改 csv"):
        basis = r["basis"].split("（")[0]
        meta[r["key"]] = {"basis": basis, "named": basis.startswith("S3 术语标准 §1.") or r["key"].split(":")[0] in ("Receivable", "Payable")}
(ROOT / "Spike/P1S6R7/s3_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
(ROOT / "Spike/P1S6R7/s3_rows.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
from collections import Counter
print(len(rows), "rows;", Counter(r["action"] for r in report))
for r in report:
    if r["action"] != "写" or (r["action"] == "已在 csv" and not r["match"]):
        print(r)
