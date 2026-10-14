# R13 FD-043：宿主上抽出 _source_strings_from_text 与转义用例直接跑（函数不 import frappe）。
# 用法：python -I -X utf8 Spike/P1S6R13-F/fix/fd043_run.py <test_translations.py 路径>
import ast, pathlib, sys
src = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8")
tree = ast.parse(src)
ns = {}
fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_source_strings_from_text")
exec(compile(ast.Module(body=[fn], type_ignores=[]), "f", "exec"), ns)
f = ns["_source_strings_from_text"]
cases = [
    ("public/js/x.js", "__('Can\\'t save');\n", {"Can't save"}),
    ("pkg/mod.py", '_("Say \\"hi\\"")\n', {'Say "hi"'}),
    ("public/js/y.js", "const FOO_SOURCES = ['Don\\'t', \"B\"];\n", {"Don't", "B"}),
    ("public/js/z.js", "__(`Line\\nTwo \\u00e9`);\n", {"Line\nTwo é"}),
    ("pkg/mod.py", "_('Tab\\tEnd', context='Ctx')\n", {"Tab\tEnd:Ctx"}),
]
bad = 0
for name, text, want in cases:
    got = f(name, text)
    ok = got == want
    bad += not ok
    print("OK " if ok else "BAD", name, sorted(map(repr, got)), "want", sorted(map(repr, want)))
sys.exit(bad)
