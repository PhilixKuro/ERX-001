"""P1-S6-R12 F p6: compare AST-based _()/__() constant-arg extraction with the regex in _source_strings_from_text (read-only)."""
import ast, csv, importlib.util
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
APP = ROOT / "frappe-bench/apps/frappe_china/frappe_china"
tree = ast.parse((APP / "tests/test_translations.py").read_text(encoding="utf-8"))
fns = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_source_strings_from_text"]
ns = {}; exec(compile(ast.Module(body=fns, type_ignores=[]), "tt", "exec"), ns)
f = ns["_source_strings_from_text"]
rows = [r for r in csv.reader((APP / "translations/zh.csv").open(encoding="utf-8", newline="")) if len(r) in (2, 3)]
csvk = {r[0].replace("\n", "\n") + (":" + r[2] if len(r) == 3 and r[2] else ""): r[1] for r in rows}
missed = []
for p in APP.rglob("*.py"):
    if "tests" in p.parts: continue
    text = p.read_text(encoding="utf-8")
    got = f(p.relative_to(APP).as_posix(), text)
    for node in ast.walk(ast.parse(text)):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in ("_", "__") and node.args:
            a = node.args[0]
            if isinstance(a, ast.Constant) and isinstance(a.value, str):
                ctx = next((k.value.value for k in node.keywords if k.arg == "context" and isinstance(k.value, ast.Constant)), None)
                key = a.value + (":" + ctx if ctx else "")
                if key not in got:
                    missed.append((p.relative_to(APP).as_posix(), node.lineno, key, csvk.get(key)))
print("PY _() constant keys missed by regex:", len(missed))
for m in missed: print(m)
for k in ("From Date", "To Date", "Fetch Timesheet", "Raven User", "Select", "of", "Load More", "Empty", "Click to sort by {0}", "Search", "Filter based on {0}"):
    print(repr(k), "csv:", csvk.get(k))
