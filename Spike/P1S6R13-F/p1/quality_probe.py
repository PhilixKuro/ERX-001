"""P1-S6-R13 F 片 1：质量守卫复核（只读，宿主 `python -I -X utf8 quality_probe.py <test_translation_quality.py> [<zh.csv>]`）。

不 import frappe：从文件里去掉 import 语句后 exec，补上 _PLACEHOLDER（取自 test_translations.py）、UNTRANSLATED（按路径载入）。
① 当前 csv 上五道守卫计数；② QUALITY_EXCEPTIONS 每键在当前 csv 上逐道实测命中，与登记的守卫集比（多登＝过宽豁免、少登＝会红）；
③ 跑模块里不依赖站点的构造用例；④ QE 键在 csv 里是否都还在。
"""
import ast, csv, importlib.util, pathlib, re, sys, types, unittest

ROOT = pathlib.Path(__file__).resolve().parents[3]
APP = ROOT / "frappe-bench/apps/frappe_china/frappe_china"
qpath = pathlib.Path(sys.argv[1])
csv_path = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else APP / "translations/zh.csv"


def load_module(path, extra):
    tree = ast.parse(pathlib.Path(path).read_text(encoding="utf-8"))
    body = [n for n in tree.body if not isinstance(n, (ast.Import, ast.ImportFrom))]
    ns = {"re": re, "csv": csv, "Final": __import__("typing").Final, "__name__": "q"} | extra
    exec(compile(ast.Module(body=body, type_ignores=[]), str(path), "exec"), ns)
    return ns


tt = ast.parse((APP / "tests/test_translations.py").read_text(encoding="utf-8"))
ph = next(n for n in tt.body if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "_PLACEHOLDER")
_PLACEHOLDER = eval(compile(ast.Expression(ph.value), "p", "eval"), {"re": re})
spec = importlib.util.spec_from_file_location("wl", APP / "tests/translation_whitelist.py")
wl = importlib.util.module_from_spec(spec); spec.loader.exec_module(wl)

rows = [r for r in csv.reader(open(csv_path, encoding="utf-8", newline="")) if len(r) in (2, 3)]
frappe_stub = types.SimpleNamespace(get_app_path=lambda *a: str(csv_path))
q = load_module(qpath, {"_PLACEHOLDER": _PLACEHOLDER, "UNTRANSLATED": wl.UNTRANSLATED,
                        "FrappeChinaTestCase": unittest.TestCase, "frappe": frappe_stub})

print("① guard counts:", {g.__name__: len(g(rows)) for g in q["GUARDS"]})
QE = q["QUALITY_EXCEPTIONS"]
preds = {"placeholder": lambda r: q["_is_placeholder"](r[1]), "traditional": lambda r: q["_is_traditional"](r[1]),
         "word_by_word": lambda r: q["_is_word_by_word"](r[1]), "mixed": lambda r: q["_is_mixed"](r[1])}
if "_is_identity" in q:
    preds["identity"] = q["_is_identity"]
by_key = {q["_key"](r): r for r in rows}
missing = [k for k in QE if k not in by_key]
over, under, combo = [], [], {}
for key, value in QE.items():
    registered = value[0] if isinstance(value, tuple) else frozenset(preds)
    row = by_key.get(key)
    if row is None:
        continue
    hit = frozenset(name for name, p in preds.items() if p(row))
    combo[tuple(sorted(registered))] = combo.get(tuple(sorted(registered)), 0) + 1
    if registered - hit:
        over.append((key[:50], sorted(registered - hit)))
    if hit - registered:
        under.append((key[:50], sorted(hit - registered)))
print("② QE entries:", len(QE), "registered combos:", combo)
print("   registered but not hit (over-wide waiver):", over)
print("   hit but not registered:", under)
print("④ QE keys absent from csv:", missing)

names = [n for n in dir(q["TestTranslationQuality"]) if n.startswith("test_") and ("constructed" in n or "reason" in n or "waives" in n)]
suite = unittest.TestSuite(q["TestTranslationQuality"](n) for n in names)
res = unittest.TextTestRunner(verbosity=0, stream=open("nul" if sys.platform == "win32" else "/dev/null", "w")).run(suite)
print("③ constructed tests:", res.testsRun, "run,", len(res.failures), "fail,", len(res.errors), "error",
      [(str(t).split()[0], e.strip().splitlines()[-1][:120]) for t, e in res.failures + res.errors])
csvt = [n for n in dir(q["TestTranslationQuality"]) if n.startswith("test_no_")]
res2 = unittest.TextTestRunner(verbosity=0, stream=open("nul" if sys.platform == "win32" else "/dev/null", "w")).run(
    unittest.TestSuite(q["TestTranslationQuality"](n) for n in csvt))
print("   csv-wide tests:", res2.testsRun, "run,", len(res2.failures), "fail,", len(res2.errors), "error",
      [str(t).split()[0] for t, _ in res2.failures + res2.errors])
