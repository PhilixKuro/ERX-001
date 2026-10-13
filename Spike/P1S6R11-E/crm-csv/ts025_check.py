"""E R11 只读核 TS-025：从 test_translations.py 用 ast 取两个函数 exec，构造片段验判别力，并做变异检验。

宿主 `python -I -X utf8 Spike/P1S6R11-E/crm-csv/ts025_check.py`；只读，不写盘。
"""
import ast
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
APP = ROOT / "frappe-bench/apps/frappe_china/frappe_china"
PATH = APP / "tests/test_translations.py"
SRC = PATH.read_text(encoding="utf-8")
TREE = ast.parse(SRC)
NAMES = ("_source_strings_from_text", "_app_source_strings")


def load(src_text=SRC):
	tree = ast.parse(src_text)
	funcs = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in NAMES]
	assert len(funcs) == 2, [n.name for n in funcs]
	ns = {"__file__": str(PATH)}
	exec(compile(ast.Module(body=funcs, type_ignores=[]), str(PATH), "exec"), ns)
	return ns


# 1) 纯函数性：函数体内 import、无 frappe、无 open/read_text/Path
func = next(n for n in TREE.body if isinstance(n, ast.FunctionDef) and n.name == "_source_strings_from_text")
body_src = ast.get_source_segment(SRC, func)
imports = [ast.get_source_segment(SRC, n) for n in ast.walk(func) if isinstance(n, (ast.Import, ast.ImportFrom))]
print("pure.imports_in_body:", imports)
print("pure.mentions:", {w: (w in body_src) for w in ("frappe", "open(", "read_text", "Path", "__file__", "glob")})

ns = load()
f = ns["_source_strings_from_text"]

# 2) 方案 SL-021 ② 构造片段（照方案原文，不照用例）
py = 'FOO_SOURCES = ("A", "B")\nBAR_SOURCE: Final[str] = "C"\nOTHER = ("D",)\n'
js = "translate('E');\nconst sources = {x: new Set(['F'])};\ntranslateLabel('G');\n"
side = json.dumps({"doctype": "Workspace Sidebar", "name": "S", "title": "Side Title", "items": [{"label": "Item Label"}, {"label": "Item 2"}]})
print("frag.py:", sorted(f("x/m.py", py)))
print("frag.js:", sorted(f("public/js/x.js", js)))
print("frag.sidebar:", sorted(f("workspace_sidebar/s.json", side)))
# 额外边界
extra = {
	"py_lower_sources": f("m.py", 'my_sources = ["L1"]\n'),
	"py_nested_in_func": f("m.py", 'def g():\n    X_SOURCES = ("N1",)\n'),
	"py_dict_sources": f("m.py", 'D_SOURCES = {"k": "v"}\n'),
	"py_frozenset": f("m.py", 'F_SOURCES = frozenset({"Z1"})\n'),
	"py_resources_name": f("m.py", 'RESOURCES = ("R1",)\n'),
	"js_obj_translate": f("a.js", "obj.translate('T1'); $translate('T2'); __('T3');"),
	"js_let_sources_multiline": f("a.js", "let sources = {\n  a: new Set(['M1', 'M2']),\n  b: new Set(['M3']),\n};\n"),
	"js_resources_ident": f("a.js", "const resources = ['RX'];"),
	"js_sources_not_bracket": f("a.js", "const SOURCES = 'S1';"),
	"desktop_icon": f("desktop_icon/i.json", json.dumps({"doctype": "Desktop Icon", "label": "IconL", "title": "IconT"})),
	"py_context": f("m.py", '_("Avail", context="Raven User")'),
}
for k, v in extra.items():
	print("edge.", k, sorted(v))

# 3) _app_source_strings 实跑
app = ns["_app_source_strings"]()
literal = {item["key"] for item in json.loads((ROOT / "Spike/P1S6R8-E/sl012/literal_keys.json").read_text(encoding="utf-8"))}
need = literal | {"CN Tax", "{0} Filter Applied", "{0} Filters Applied", "(Empty)", "Add {0}...", "Select {0}..."}
print("app.count:", len(app), "literal:", len(literal), "missing:", sorted(need - app))
m = re.search(r"LITERAL_KEYS = \{(.*?)\n\}", SRC, re.S)
const = set(ast.literal_eval("{" + m.group(1) + "}"))
print("LITERAL_KEYS const == json|CN Tax:", const == literal | {"CN Tax"}, sorted(const ^ (literal | {"CN Tax"})))

# 4) 变异检验：按用例断言模拟
def case_asserts(fn):
	res = {}
	res["py"] = fn("pkg/mod.py", py) == {"A", "B", "C"}
	res["js"] = fn("public/js/x.js", js) == {"E", "F"}
	res["sidebar"] = fn("workspace_sidebar/s.json", json.dumps({"doctype": "Workspace Sidebar", "name": "S", "title": "Side Title", "items": [{"label": "Item Label"}]})) == {"Side Title", "Item Label"}
	res["icon"] = fn("desktop_icon/i.json", json.dumps({"doctype": "Desktop Icon", "name": "I", "label": "Icon Label"})) == {"Icon Label"}
	return res

print("mut.baseline:", case_asserts(f))
mutants = {
	"py_SOURCES_rule_removed": ('re.search(r"SOURCES?$", target.id, re.I)', "False"),
	"py_SOURCES_suffix_only_S": ('r"SOURCES?$"', 'r"SOURCES$"'),
	"js_translate_alias_removed": ("(?:_{1,2}|translate)", "_{1,2}"),
	"js_sources_ident_removed": (r'r"(?:const|let|var)\s+\w*sources\s*="', r'r"(?!x)x"'),
	"json_sidebar_removed": ('("Workspace Sidebar", "Desktop Icon")', '("__none__",)'),
	"json_items_removed": ('data.get("items") or []', '[]'),
	"lookbehind_removed": ("(?<![A-Za-z_.$])", ""),
	"py_annassign_removed": ("node.target if isinstance(node, ast.AnnAssign) else ", ""),
}
for name, (old, new) in mutants.items():
	assert SRC.count(old) >= 1, (name, old)
	mns = load(SRC.replace(old, new, 1))
	r = case_asserts(mns["_source_strings_from_text"])
	lit_ok = (const - mns["_app_source_strings"]()) == set()
	print(f"mut.{name}: case={r} red={not all(r.values())} literal_test_red={not lit_ok}")
