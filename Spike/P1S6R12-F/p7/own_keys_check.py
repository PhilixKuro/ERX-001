"""P7：不 import frappe，从 test_translations.py 抽出 _source_strings_from_text 与 R9_OWN_KEYS/LITERAL_KEYS，按 _app_source_strings 的口径扫 app，核 IT-052/053。只读。"""
import ast, pathlib, sys
app = pathlib.Path(sys.argv[1]) / "frappe_china"
src = (app / "tests/test_translations.py").read_text(encoding="utf-8")
tree = ast.parse(src)
ns = {}
for node in tree.body:
	if isinstance(node, ast.FunctionDef) and node.name == "_source_strings_from_text":
		exec(compile(ast.Module(body=[node], type_ignores=[]), "f", "exec"), ns)
	if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") in ("R9_OWN_KEYS", "LITERAL_KEYS"):
		ns[node.targets[0].id] = ast.literal_eval(node.value)
f = ns["_source_strings_from_text"]
sources = set()
for p in [*app.rglob("*.py"), *app.rglob("*.js"), *app.rglob("*.json")]:
	if "tests" in p.parts and p.suffix != ".json": continue
	if p.suffix == ".json" and "fixtures" in p.parts and p.name != "custom_field.json": continue
	sources |= f(p.relative_to(app).as_posix(), p.read_text(encoding="utf-8"))
print("sources:", len(sources))
print("R9_OWN_KEYS missing:", sorted(ns["R9_OWN_KEYS"] - sources))
print("LITERAL_KEYS missing:", sorted(ns["LITERAL_KEYS"] - sources))
print("JS singular:", f("public/js/y.js", 'const FOO_SOURCE = ["H"];\n'))
print("escaped quote:", f("x.py", '_("Say \\"hi\\" now")\n'))
