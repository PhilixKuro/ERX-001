"""P1-S6-R13 F 片 1：csv 静态复核与 FD-013 转义键对清场的影响（只读）。宿主 `python -I -X utf8 csv_checks.py`。

① 排序（A20 _sort_key）、重复键（含 FD-015 归一）、列数，函数从 test_translations.py 抽出；
② 本轮新增 6 行的位置与译文在 csv 里的其它占用；
③ FD-015 _duplicate_keys 变异：去掉 replace 后反证用例是否变红；
④ FD-013：带转义引号的源词按新取法取出的键，能否保住 csv 里运行时形态的那一行（清场 row_key 比对）；
⑤ 法定列头宽口径撞名（复用 R12 p7/legal_collide 口径）。
"""
import ast, csv, pathlib, re
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parents[3]
APP = ROOT / "frappe-bench/apps/frappe_china/frappe_china"
src = (APP / "tests/test_translations.py").read_text(encoding="utf-8")
tree = ast.parse(src)
ns = {"Counter": Counter, "re": re}
fns = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in ("_duplicate_keys", "_sort_key", "_unsorted_pairs", "_source_strings_from_text")]
exec(compile(ast.Module(body=fns, type_ignores=[]), "tt", "exec"), ns)
rows = list(csv.reader(open(APP / "translations/zh.csv", encoding="utf-8", newline="")))
print("① rows", len(rows), "bad cols", [r for r in rows if len(r) not in (2, 3)][:3],
      "unsorted", ns["_unsorted_pairs"]([r for r in rows if len(r) in (2, 3)]), "dup", ns["_duplicate_keys"](rows))

new = {("Item Type", "Navbar Item"), ("Ledger", "Print Settings"), ("Partly Paid", "Sales Invoice"),
       ("Partly Paid and Discounted", "Sales Invoice"), ("Unpaid and Discounted", "Sales Invoice"), ("Stock Ledger Invariant Check", "")}
for i, r in enumerate(rows, 1):
    if (r[0], r[2] if len(r) == 3 else "") in new:
        others = [(j, x[0]) for j, x in enumerate(rows, 1) if x[1] == r[1] and j != i]
        print("②", i, r, "same target elsewhere:", others)
print("② Expenses rows:", [r for r in rows if r[0] == "Expenses"])

mut = src.replace('row[0].replace("\\\\n", "\\n")', "row[0]")
assert mut != src, "mutation anchor not found"
ns2 = {"Counter": Counter}
exec(compile(ast.Module(body=[n for n in ast.parse(mut).body if isinstance(n, ast.FunctionDef) and n.name == "_duplicate_keys"], type_ignores=[]), "m", "exec"), ns2)
case = [["a\\nb", "甲"], ["a\nb", "乙"]]
print("③ FD-015 original:", ns["_duplicate_keys"](case), "mutated:", ns2["_duplicate_keys"](case), "(mutant killed)" if ns2["_duplicate_keys"](case) != ["a\nb"] else "(SURVIVED)")

f = ns["_source_strings_from_text"]
prune_key = lambda r: r[0].replace("\\n", "\n") + (":" + r[2] if len(r) == 3 and r[2] else "")
for name, text, csv_row in [
    ("public/js/x.js", "__('Can\\'t save');\n", ["Can't save", "无法保存"]),
    ("pkg/m.py", '_("Say \\"hi\\"")\n', ['Say "hi"', "说“你好”"]),
]:
    keys = f(name, text)
    print("④", repr(text.strip()), "keep keys", sorted(keys), "| csv row key", repr(prune_key(csv_row)), "| kept by prune:", prune_key(csv_row) in keys)

labels = set()
for rel in ("accounting/statements/labels.py", "accounting/statements/mapping.py", "accounting/statements/cash_flow_statement.py"):
    labels |= set(re.findall(r'"([^"\n]*[一-鿿][^"\n]*)"', (APP / rel).read_text(encoding="utf-8")))
print("⑤ legal-ish labels", len(labels), "csv rows aliasing them:", [(r[0], r[1]) for r in rows if len(r) in (2, 3) and r[1] in labels and r[0] != r[1]])
