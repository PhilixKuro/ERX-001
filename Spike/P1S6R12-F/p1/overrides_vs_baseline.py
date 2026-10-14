# 只读：比对基线 official_overrides 与 OVERRIDES 键集合；查 csv 是否有含 CJK 的键
import ast, csv, json, re, sys

BASE = r"D:/ERX-001/Spike/P1S6R12-F/p1/baseline.out.json"
OV = r"D:/ERX-001/frappe-bench/apps/frappe_china/frappe_china/tests/translation_overrides.py"
CSV = r"D:/ERX-001/frappe-bench/apps/frappe_china/frappe_china/translations/zh.csv"

d = json.load(open(BASE, encoding="utf-8"))
base = {o["key"] for o in d["official_overrides"]}
tree = ast.parse(open(OV, encoding="utf-8").read())
keys = set()
for node in tree.body:
    if isinstance(node, ast.AnnAssign) and getattr(node.target, "id", "") == "OVERRIDES":
        keys = {k.value for k in node.value.keys}
print("baseline official_overrides:", len(base), "OVERRIDES:", len(keys))
print("baseline - OVERRIDES:", sorted(base - keys))
print("OVERRIDES - baseline:", sorted(keys - base))
rows = list(csv.reader(open(CSV, encoding="utf-8", newline="")))
print("csv rows:", len(rows), "CJK keys:", [r[0] for r in rows if re.search("[\u4e00-\u9fff]", r[0])][:10])
