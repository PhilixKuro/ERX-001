"""P1-S6-R13 F 片 1：上游 Python `_()` 首参源码里带反斜杠转义引号的调用，以及 main.pot 收的键形（只读）。
宿主 `python -I -X utf8 upstream_escape.py`。"""
import ast, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parents[3] / "frappe-bench/apps"
BS = chr(92)
hits = []
for app in ["frappe", "erpnext", "hrms"]:
    for p in (ROOT / app / app).rglob("*.py"):
        if "tests" in p.parts or "node_modules" in p.parts:
            continue
        try:
            src = p.read_text(encoding="utf-8")
            tree = ast.parse(src)
        except Exception:
            continue
        for n in ast.walk(tree):
            if (isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "_" and n.args
                    and isinstance(n.args[0], ast.Constant) and isinstance(n.args[0].value, str)):
                seg = ast.get_source_segment(src, n.args[0]) or ""
                if BS + "'" in seg or BS + '"' in seg:
                    hits.append((p.relative_to(ROOT).as_posix(), n.lineno, seg[:70], n.args[0].value[:60]))
print("python _() calls with escaped quotes:", len(hits))
for h in hits[:5]:
    print(" ", h)
pot = (ROOT / "frappe/frappe/locale/main.pot").read_text(encoding="utf-8")
for _, _, _, value in hits[:3]:
    probe = value.replace('"', BS + '"')
    print("  in main.pot as runtime string:", probe[:50] in pot)
