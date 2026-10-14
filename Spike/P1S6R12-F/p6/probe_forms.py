"""P1-S6-R12 F 分片 6：A28 命名约定的边界写法探针（只读，纯函数级）。

宿主 `python -I -X utf8 Spike/P1S6R12-F/p6/probe_forms.py`。
从 test_translations.py 取出 _source_strings_from_text exec，喂「守开发守则 A28 原文、但形态不同」的构造片段，
看是否取到。守则原文：常量名以 SOURCE/SOURCES 结尾（Python 模块级常量和 JS 标识符都算），其中的字符串字面量都算本 app 源词。
"""
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
APP = ROOT / "frappe-bench/apps/frappe_china/frappe_china"
tree = ast.parse((APP / "tests/test_translations.py").read_text(encoding="utf-8"))
fns = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_source_strings_from_text"]
ns = {}
exec(compile(ast.Module(body=fns, type_ignores=[]), "tt", "exec"), ns)
f = ns["_source_strings_from_text"]

cases = [
	# (说明, 文件名, 文本, 期望取到)
	("JS 单数常量、标量字符串", "x.js", 'const LABEL_SOURCE = "Alpha";\n', {"Alpha"}),
	("JS 复数常量、对象字面量值", "x.js", 'const LABEL_SOURCES = {a: "Beta", b: "Gamma"};\n', {"Beta", "Gamma"}),
	("JS 复数常量、数组（方案原式）", "x.js", 'const LABEL_SOURCES = ["Delta"];\n', {"Delta"}),
	("JS 复数常量、多行数组", "x.js", 'const LABEL_SOURCES = [\n\t"Eps",\n\t"Zeta",\n];\n', {"Eps", "Zeta"}),
	("JS 无分号、下一行另一语句", "x.js", 'const LABEL_SOURCES = ["Eta"]\nconst other = ["NotMe"]\n', {"Eta"}),
	("JS translate 带 context 第三参", "x.js", 'translate("Theta", null, "Ctx");\n', {"Theta:Ctx"}),
	("JS __ 模板字符串", "x.js", "__(`Iota`);\n", {"Iota"}),
	("Python 复数常量、dict 值", "m.py", 'LABEL_SOURCES = {"k": "Kappa"}\n', {"Kappa"}),
	("Python 复数常量、frozenset 调用", "m.py", 'LABEL_SOURCES = frozenset({"Lambda"})\n', {"Lambda"}),
	("Python 复数常量、嵌套 tuple", "m.py", 'LABEL_SOURCES = (("Mu", 1), ("Nu", 2))\n', {"Mu", "Nu"}),
	("Python 单数常量带 Final 注解（方案原式）", "m.py", 'X_SOURCE: Final[str] = "Xi"\n', {"Xi"}),
	("Python 字面量 _() 带 context=", "m.py", '_("Omicron", context="Ctx")\n', {"Omicron:Ctx"}),
]
for desc, name, text, expected in cases:
	got = f(name, text)
	ok = expected <= got
	print(f"{'OK ' if ok else 'MISS'} | {desc} | 期望 {sorted(expected)} | 取到 {sorted(got)}")
