# R12 SB FD-017：把 QUALITY_EXCEPTIONS 由「键 → 理由」改写为「键 → (frozenset({守卫名}), 理由)」。
# 守卫名取 which_guard.out 的实测命中（每键至少一道）；只改该字典的值，键、理由与顺序不动。
# 用法（frappe_china 仓库根）：python -I -X utf8 <本文件> <which_guard.out>
import ast, json, pathlib, sys
path = pathlib.Path('frappe_china/tests/test_translation_quality.py')
text = path.read_text(encoding='utf-8')
raw = pathlib.Path(sys.argv[1]).read_text(encoding='utf-8')
hits = json.loads(raw[:raw.rindex('\ncounts ')])
tree = ast.parse(text)
node = next(n for n in tree.body if isinstance(n, ast.AnnAssign) and n.target.id == 'QUALITY_EXCEPTIONS')
lines = text.splitlines(keepends=True)
out = []
for i, line in enumerate(lines, 1):
    if node.lineno < i < node.end_lineno:
        entry = ast.parse('{' + line.strip().rstrip(',') + '}', mode='eval').body
        key, reason = entry.keys[0].value, entry.values[0].value
        guards = hits[key]
        assert guards, key
        names = ', '.join(json.dumps(g) for g in guards)
        out.append('\t' + json.dumps(key, ensure_ascii=False) + ': (frozenset({' + names + '}), '
                   + json.dumps(reason, ensure_ascii=False) + '),\n')
    elif i == node.lineno:
        out.append(line.replace('Final[dict[str, str]]', 'Final[dict[str, tuple[frozenset[str], str]]]'))
    else:
        out.append(line)
new = ''.join(out)
old_qe = ast.literal_eval(ast.get_source_segment(text, node.value))
new_tree = ast.parse(new)
new_node = next(n for n in new_tree.body if isinstance(n, ast.AnnAssign) and n.target.id == 'QUALITY_EXCEPTIONS')
seg = ast.get_source_segment(new, new_node.value)
new_qe = eval(seg, {'frozenset': frozenset})
assert list(old_qe) == list(new_qe) and all(old_qe[k] == new_qe[k][1] for k in old_qe)
path.write_text(new, encoding='utf-8', newline='')
print(len(new_qe), 'entries converted')
