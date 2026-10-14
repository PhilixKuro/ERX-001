# R12 SB FD-012：宿主上抽出 _source_strings_from_text，跑 test_translations.py 里 FD-012／FD-013 与 A28 三条取法用例。
# 用法：python -I -X utf8 Spike/P1S6R12-SB/fd012/run.py <test_translations.py 路径>
import ast, json, sys, pathlib, unittest
src = pathlib.Path(sys.argv[1]).read_text(encoding='utf-8')
tree = ast.parse(src)
ns = {'json': json, 'unittest': unittest}
fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == '_source_strings_from_text')
exec(compile(ast.Module(body=[fn], type_ignores=[]), 'f', 'exec'), ns)
cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'TestTranslations')
wanted = {'test_source_strings_follow_a28_wording', 'test_source_strings_keep_escaped_quotes', 'test_source_strings_literal_key_forms'}
methods = [m for m in cls.body if isinstance(m, ast.FunctionDef) and m.name in wanted]
klass = ast.ClassDef(name='T', bases=[ast.Attribute(value=ast.Name('unittest', ast.Load()), attr='TestCase', ctx=ast.Load())],
                     keywords=[], body=methods, decorator_list=[], type_params=[]) if sys.version_info >= (3, 12) else \
        ast.ClassDef(name='T', bases=[ast.Attribute(value=ast.Name('unittest', ast.Load()), attr='TestCase', ctx=ast.Load())],
                     keywords=[], body=methods, decorator_list=[])
exec(compile(ast.fix_missing_locations(ast.Module(body=[klass], type_ignores=[])), 't', 'exec'), ns)
result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ns['T']))
sys.exit(not result.wasSuccessful())
