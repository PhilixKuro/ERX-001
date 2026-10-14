"""P1-S6-R13 F 片 1：取词法复核（只读，宿主 `python -I -X utf8 extract_probe.py <旧 test_translations.py> <新 test_translations.py>`）。

① 新旧取法对本 app 全部源文件取词，比对差集（复算 SB「280 键、差集空」）；
② 跑新文件里三条取法用例（A28、转义引号、literal_key_forms）；
③ R12 片 6 probe_forms 12 例；
④ 转义引号：取出的键与运行时键（Python ast.literal_eval / JS 解释后的字符串）是否一致；上游 main.pot 收的是哪种。
⑤ FD-012 扩取法后名字以 sources 结尾、但语义不是源词清单的常量（如 resources）会被取到哪些串。
"""
import ast, json, pathlib, re, sys, unittest

ROOT = pathlib.Path(__file__).resolve().parents[3]
APP = ROOT / "frappe-bench/apps/frappe_china/frappe_china"


def load(path):
    tree = ast.parse(pathlib.Path(path).read_text(encoding="utf-8"))
    ns = {}
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_source_strings_from_text")
    exec(compile(ast.Module(body=[fn], type_ignores=[]), "f", "exec"), ns)
    return ns["_source_strings_from_text"], tree


def app_sources(f):
    out = set()
    for path in [*APP.rglob("*.py"), *APP.rglob("*.js"), *APP.rglob("*.json")]:
        if "tests" in path.parts and path.suffix != ".json":
            continue
        if path.suffix == ".json" and "fixtures" in path.parts and path.name != "custom_field.json":
            continue
        out |= f(path.relative_to(APP).as_posix(), path.read_text(encoding="utf-8"))
    return out


old, _ = load(sys.argv[1])
new, tree = load(sys.argv[2])
a, b = app_sources(old), app_sources(new)
print("① app sources old/new:", len(a), len(b), "only_old", sorted(a - b), "only_new", sorted(b - a))

ns = {"json": json, "unittest": unittest, "_source_strings_from_text": new}
cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "TestTranslations")
wanted = {"test_source_strings_follow_a28_wording", "test_source_strings_keep_escaped_quotes", "test_source_strings_literal_key_forms"}
methods = [m for m in cls.body if isinstance(m, ast.FunctionDef) and m.name in wanted]
klass = ast.ClassDef(name="T", bases=[ast.Attribute(value=ast.Name("unittest", ast.Load()), attr="TestCase", ctx=ast.Load())],
                     keywords=[], body=methods, decorator_list=[])
exec(compile(ast.fix_missing_locations(ast.Module(body=[klass], type_ignores=[])), "t", "exec"), ns)
r = unittest.TextTestRunner(verbosity=0, stream=open("nul" if sys.platform == "win32" else "/dev/null", "w")).run(
    unittest.defaultTestLoader.loadTestsFromTestCase(ns["T"]))
print("② extraction tests:", r.testsRun, "run,", len(r.failures), "fail,", len(r.errors), "error", [str(t) for t, _ in r.failures + r.errors])

cases = [
    ("x.js", 'const LABEL_SOURCE = "Alpha";\n', {"Alpha"}),
    ("x.js", 'const LABEL_SOURCES = {a: "Beta", b: "Gamma"};\n', {"Beta", "Gamma"}),
    ("x.js", 'const LABEL_SOURCES = ["Delta"];\n', {"Delta"}),
    ("x.js", 'const LABEL_SOURCES = [\n\t"Eps",\n\t"Zeta",\n];\n', {"Eps", "Zeta"}),
    ("x.js", 'const LABEL_SOURCES = ["Eta"]\nconst other = ["NotMe"]\n', {"Eta"}),
    ("x.js", 'translate("Theta", null, "Ctx");\n', {"Theta:Ctx"}),
    ("x.js", "__(`Iota`);\n", {"Iota"}),
    ("m.py", 'LABEL_SOURCES = {"k": "Kappa"}\n', {"Kappa"}),
    ("m.py", 'LABEL_SOURCES = frozenset({"Lambda"})\n', {"Lambda"}),
    ("m.py", 'LABEL_SOURCES = (("Mu", 1), ("Nu", 2))\n', {"Mu", "Nu"}),
    ("m.py", 'X_SOURCE: Final[str] = "Xi"\n', {"Xi"}),
    ("m.py", '_("Omicron", context="Ctx")\n', {"Omicron:Ctx"}),
]
ok_old = sum(e <= old(n, t) for n, t, e in cases)
ok_new = sum(e <= new(n, t) for n, t, e in cases)
print(f"③ probe_forms OK old={ok_old}/12 new={ok_new}/12")

# ④ 转义引号：运行时键 vs 取出的键
esc = [
    ("pkg/m.py", "_('Can\\'t save')\n", ast.literal_eval("'Can\\'t save'")),
    ("pkg/m.py", '_("Say \\"hi\\"")\n', ast.literal_eval('"Say \\"hi\\""')),
    ("public/js/x.js", "__('Don\\'t')\n", "Don't"),
    ("pkg/m.py", "_(\"Line\\none\")\n", "Line\none"),
]
for name, text, runtime in esc:
    got = new(name, text)
    print("④", repr(text.strip()), "extracted", sorted(got), "runtime", repr(runtime), "match" if runtime in got else "MISMATCH")

# ⑤ 名字以 sources 结尾的非源词常量
for name, text in [
    ("x.js", 'const resources = {url: "/api/method/frappe.client.get", method: "GET"};\n'),
    ("m.py", 'DATA_SOURCES = {"mysql": "MariaDB", "pg": "PostgreSQL"}\n'),
    ("x.js", 'let source = frm.doc.source || "Manual";\n'),
]:
    print("⑤", repr(text.strip()), "->", sorted(new(name, text)), "| old ->", sorted(old(name, text)))
