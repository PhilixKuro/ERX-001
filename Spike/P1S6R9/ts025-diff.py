"""R9 TS-025：新旧 _app_source_strings() 差集（旧取法取自 HEAD）。宿主 python -I -X utf8 Spike/P1S6R9/ts025-diff.py"""
import ast
from pathlib import Path

APP = Path(__file__).resolve().parents[2] / "frappe-bench/apps/frappe_china/frappe_china"


def load(path, names):
	tree = ast.parse(Path(path).read_text(encoding="utf-8"))
	ns = {"__file__": str(APP / "tests/test_translations.py")}
	exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names], type_ignores=[]), "x", "exec"), ns)
	return ns["_app_source_strings"]()


old = load(Path(__file__).with_name("_old_tt.py"), {"_app_source_strings"})
new = load(APP / "tests/test_translations.py", {"_app_source_strings", "_source_strings_from_text"})
print("old", len(old), "new", len(new))
print("added", sorted(new - old))
print("removed", sorted(old - new))
