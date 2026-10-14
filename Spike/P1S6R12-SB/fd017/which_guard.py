# R12 SB FD-017：逐条算出每个 QUALITY_EXCEPTIONS 键在当前 csv 上实际命中哪几道守卫（宿主，不 import frappe）。
# 守卫函数从 test_translation_quality.py 原文 AST 摘取后执行，_PLACEHOLDER 从 test_translations.py 摘取。
# 用法（frappe_china 仓库根）：python -I -X utf8 <本文件>
import ast, csv, json, re, pathlib
from typing import Final
T = pathlib.Path('frappe_china/tests')

def pick(path, names):
    tree = ast.parse((T / path).read_text(encoding='utf-8'))
    keep = []
    for n in tree.body:
        if isinstance(n, (ast.FunctionDef,)) and n.name in names: keep.append(n)
        elif isinstance(n, (ast.Assign, ast.AnnAssign)):
            tgt = n.target if isinstance(n, ast.AnnAssign) else n.targets[0]
            if isinstance(tgt, ast.Name) and tgt.id in names: keep.append(n)
    return ast.Module(body=keep, type_ignores=[])

ns = {'re': re, 'Final': Final, 'frozenset': frozenset}
exec(compile(pick('test_translations.py', {'_PLACEHOLDER'}), 'a', 'exec'), ns)
exec(compile(pick('test_translation_quality.py', {
    'STOPWORDS', 'ALLOW', 'QUALITY_EXCEPTIONS', '_CJK', '_HTML_TAG', '_EMPHASIS', '_SPACED_CJK', '_WORD',
    '_strip_markup', '_is_placeholder', '_is_traditional', '_is_word_by_word', '_is_mixed'}), 'b', 'exec'), ns)
rows = [r for r in csv.reader(open('frappe_china/translations/zh.csv', encoding='utf-8', newline='')) if len(r) in (2, 3)]
by_key = {r[0] + (':' + r[2] if len(r) == 3 and r[2] else ''): r[1] for r in rows}
qe = ns['QUALITY_EXCEPTIONS']
guards = {'placeholder': ns['_is_placeholder'], 'traditional': ns['_is_traditional'],
          'word_by_word': ns['_is_word_by_word'], 'mixed': ns['_is_mixed']}
out = {}
for key in qe:
    target = by_key.get(key)
    out[key] = None if target is None else [g for g, f in guards.items() if f(target)]
print(json.dumps(out, ensure_ascii=False, indent=1))
print('counts', {g: sum(g in (v or []) for v in out.values()) for g in guards}, 'missing', [k for k, v in out.items() if v is None], 'none', [k for k, v in out.items() if v == []])
