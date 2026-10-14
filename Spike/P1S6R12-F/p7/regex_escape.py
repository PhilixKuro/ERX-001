"""P7：比对 474cd1c 与 d441e9f 两版源词取法正则对「引号内反斜杠转义」的处理。只读，不 import frappe。"""
import pathlib
import re
import sys

BS = "\\"
# 474cd1c test_translations.py:85 —— 正则里是 \\. （反斜杠＋任意字符）
OLD = re.compile(r"(?<![A-Za-z_])_{1,2}\(\s*([\"'])((?:" + BS + BS + r".|(?!\1).)*)\1")
# d441e9f test_translations.py:101 —— 正则里是 \. （字面点号）
NEW_PY = re.compile(r"(?<![A-Za-z_])_{1,2}\(\s*([\"'])((?:" + BS + r".|(?!\1).)*)\1")
NEW_JS = re.compile(r"(?<![A-Za-z_.$])(?:_{1,2}|translate)\(\s*([\"'])((?:" + BS + r".|(?!\1).)*)\1")

print("OLD pattern:", OLD.pattern)
print("NEW pattern:", NEW_PY.pattern)
sample = '_("Say ' + BS + '"hi' + BS + '" now")'
print("sample:", sample)
print("  old ->", [m.group(2) for m in OLD.finditer(sample)])
print("  new ->", [m.group(2) for m in NEW_PY.finditer(sample)])

root = pathlib.Path(sys.argv[1]) / "frappe_china"
lost_total = 0
for p in [*root.rglob("*.py"), *root.rglob("*.js")]:
	if "tests" in p.parts:
		continue
	t = p.read_text(encoding="utf-8")
	a = {m.group(2) for m in OLD.finditer(t)}
	b = {m.group(2) for m in (NEW_PY if p.suffix == ".py" else NEW_JS).finditer(t)}
	if a - b:
		lost_total += len(a - b)
		print("LOST", p.relative_to(root).as_posix(), sorted(a - b))
	esc = [m.group(2) for m in OLD.finditer(t) if BS in m.group(2)]
	if esc:
		print("ESCAPED-IN-SOURCE", p.relative_to(root).as_posix(), esc)
print("lost_total:", lost_total)
