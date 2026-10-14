# R12 SB FD-013：恢复 \. 前后对本 app 全部源文件取词，比对差集（应为空：现有代码无转义引号源词）。
# 用法（frappe_china 仓库根）：python <本文件> <旧 test_translations.py> <新 test_translations.py>
import ast, pathlib, sys
def load(p):
    tree = ast.parse(pathlib.Path(p).read_text(encoding='utf-8')); ns = {}
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == '_source_strings_from_text')
    exec(compile(ast.Module(body=[fn], type_ignores=[]), 'f', 'exec'), ns); return ns['_source_strings_from_text']
old, new = load(sys.argv[1]), load(sys.argv[2])
root = pathlib.Path('frappe_china'); a = set(); b = set()
for path in [*root.rglob('*.py'), *root.rglob('*.js'), *root.rglob('*.json')]:
    if 'tests' in path.parts and path.suffix != '.json': continue
    if path.suffix == '.json' and 'fixtures' in path.parts and path.name != 'custom_field.json': continue
    n = path.relative_to(root).as_posix(); t = path.read_text(encoding='utf-8')
    a |= old(n, t); b |= new(n, t)
print(len(a), len(b), 'only_old', sorted(a - b), 'only_new', sorted(b - a))
