"""P1-S6-R13 F 片 1：判别力变异（只在内存里改源码文本，不写盘）。宿主 `python -I -X utf8 mutate.py`。

对 test_translations.py 的取法与 test_translation_quality.py 的守卫各打几个变异，跑对应新增用例，看是否被杀。
"""
import ast, csv, importlib.util, json, pathlib, re, sys, types, typing, unittest
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parents[3]
APP = ROOT / "frappe-bench/apps/frappe_china/frappe_china"
NULL = open("nul" if sys.platform == "win32" else "/dev/null", "w")


def run_tests(src, cls_name, wanted, extra):
    tree = ast.parse(src)
    body = [n for n in tree.body if not isinstance(n, (ast.Import, ast.ImportFrom))]
    for n in body:
        if isinstance(n, ast.ClassDef) and n.name == cls_name:
            n.bases = [ast.Attribute(value=ast.Name("unittest", ast.Load()), attr="TestCase", ctx=ast.Load())]
            n.body = [m for m in n.body if isinstance(m, ast.FunctionDef) and m.name in wanted]
    ns = {"unittest": unittest, "re": re, "json": json, "csv": csv, "Counter": Counter, "Final": typing.Final, "__name__": "m"} | extra
    try:
        exec(compile(ast.fix_missing_locations(ast.Module(body=body, type_ignores=[])), "m", "exec"), ns)
    except Exception as exc:
        return f"load error {type(exc).__name__}"
    res = unittest.TextTestRunner(stream=NULL, verbosity=0).run(unittest.defaultTestLoader.loadTestsFromTestCase(ns[cls_name]))
    bad = sorted({str(t).split()[0] for t, _ in res.failures + res.errors})
    return f"{res.testsRun} run, red={bad}" if bad else f"{res.testsRun} run, all green"


# --- test_translations 取法 ---
tsrc = (APP / "tests/test_translations.py").read_text(encoding="utf-8")
stub_frappe = types.SimpleNamespace()
textra = {"frappe": stub_frappe, "LEGAL_LABELS": set(), "OVERRIDES": {}, "Override": None, "UNTRANSLATED": {},
          "FrappeChinaTestCase": unittest.TestCase}
twanted = {"test_source_strings_follow_a28_wording", "test_source_strings_keep_escaped_quotes", "test_source_strings_literal_key_forms",
           "test_duplicate_key_detector_normalizes_escaped_newline", "test_duplicate_key_detector"}
tmut = {
    "baseline": (None, None),
    "FD-012 py: ast.walk -> 只认 elts": ("for value in ast.walk(node.value) if", "for value in (node.value.elts if isinstance(node.value, (ast.Tuple, ast.List, ast.Set)) else [node.value]) if"),
    "FD-012 js: 去掉第三参 context": ("context = re.match(context_pattern, text[match.end():])", "context = None"),
    "FD-012 js: 去掉反引号": ("""(["'`])((?:\\\\.|(?!\\1).)*)\\1""\")\n""", """(["'])((?:\\\\.|(?!\\1).)*)\\1""\")\n"""),
    "FD-012 js: 不跳过 ${} 插值": ('if match.group(1) == "`" and "${" in match.group(2):\n\t\t\t\tcontinue', "pass"),
    "FD-013: \\\\. -> \\.": ("(?:\\\\.|(?!\\1).)*)\\1\"\"\")\n\t\t# Python", "(?:\\.|(?!\\1).)*)\\1\"\"\")\n\t\t# Python"),
    "FD-015: 去掉 \\\\n 归一": ('row[0].replace("\\\\n", "\\n")', "row[0]"),
}
for name, (old, new) in tmut.items():
    src = tsrc
    if old is not None:
        if old not in src:
            print(f"[translations] {name}: ANCHOR NOT FOUND"); continue
        src = src.replace(old, new, 1)
    print(f"[translations] {name}: {run_tests(src, 'TestTranslations', twanted, textra)}")

# --- test_translation_quality 守卫 ---
qsrc = (APP / "tests/test_translation_quality.py").read_text(encoding="utf-8")
ph = next(n for n in ast.parse(tsrc).body if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "_PLACEHOLDER")
spec = importlib.util.spec_from_file_location("wl", APP / "tests/translation_whitelist.py")
wl = importlib.util.module_from_spec(spec); spec.loader.exec_module(wl)
csv_path = str(APP / "translations/zh.csv")
qextra = {"_PLACEHOLDER": eval(compile(ast.Expression(ph.value), "p", "eval"), {"re": re}), "UNTRANSLATED": wl.UNTRANSLATED,
          "FrappeChinaTestCase": unittest.TestCase, "frappe": types.SimpleNamespace(get_app_path=lambda *a: csv_path)}
qwanted = {"test_every_exception_has_a_reason", "test_exception_waives_only_its_registered_guard", "test_no_untranslated_rows",
           "test_identity_guard_reports_constructed_row", "test_no_mixed_language_translations", "test_no_word_by_word_translations",
           "test_no_traditional_characters", "test_no_placeholder_translations"}
qmut = {
    "baseline": (None, None),
    "FD-017: _waived 退回整行全免": ("return guard in QUALITY_EXCEPTIONS.get(_key(row), (frozenset(), \"\"))[0]", "return _key(row) in QUALITY_EXCEPTIONS"),
    "FD-017: identity 不看 UNTRANSLATED": ("and row[0] not in UNTRANSLATED", ""),
    "FD-017: identity 恒假": ("return row[1].strip() == row[0].strip() and row[0] not in UNTRANSLATED", "return False"),
    "FD-017: identity 移出 GUARDS": ("find_mixed, find_identity)", "find_mixed)"),
    "FD-017: Python expression 行去掉 word_by_word 豁免": ('(frozenset({"word_by_word", "mixed"}), "译文须保留源词里的 Python', '(frozenset({"mixed"}), "译文须保留源词里的 Python'),
    "FD-017: 某 QE 理由置空": ('"Top P 为模型采样参数名，界面须按原名对照服务商文档"', '"  "'),
    "FD-017: 守卫名拼错（mixd）": ('"Top P": (frozenset({"mixed"})', '"Top P": (frozenset({"mixd"})'),
    "FD-036 连带: 白名单删 JAN": (None, "drop-JAN"),
}
for name, (old, new) in qmut.items():
    src, extra = qsrc, dict(qextra)
    if new == "drop-JAN":
        extra["UNTRANSLATED"] = {k: v for k, v in wl.UNTRANSLATED.items() if k != "JAN"}
    elif old is not None:
        if old not in src:
            print(f"[quality] {name}: ANCHOR NOT FOUND"); continue
        src = src.replace(old, new, 1)
    print(f"[quality] {name}: {run_tests(src, 'TestTranslationQuality', qwanted, extra)}")
