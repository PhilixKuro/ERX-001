import re, importlib.util
_PLACEHOLDER = re.compile(r"\{\{?\s*[^{}]+\s*\}?|\{\d+\}|%\([^)]*\)s|%s")  # test_translations.py:236 原样
src = "Naming series '{0}' for DocType '{1}' does not contain standard '.' or '{{' separator. Using fallback extraction."
zh_good = "DocType「{1}」的编号模板「{0}」不含标准的「.」或「{{」分隔符，改用备用方式提取。"
zh_copy = "编号模板 '{0}'（DocType '{1}'）不含标准的 '.' 或 '{{' separator. Using fallback extraction."
for label, s in [('source', src), ('zh_good', zh_good), ('zh_copy_tail', zh_copy)]:
    print(label, sorted(_PLACEHOLDER.findall(s)))
print('equal(source, zh_good):', sorted(_PLACEHOLDER.findall(src)) == sorted(_PLACEHOLDER.findall(zh_good)))
fixed = re.compile(r"\{\{\s*[^{}]+?\s*\}\}|\{\d+\}|%\([^)]*\)s|%s")
print('closed-brace regex:', sorted(fixed.findall(src)), sorted(fixed.findall(zh_good)), sorted(fixed.findall(src)) == sorted(fixed.findall(zh_good)))
s = importlib.util.spec_from_file_location('w', 'D:/ERX-001/frappe-bench/apps/frappe_china/frappe_china/tests/translation_whitelist.py'); m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
print('in UNTRANSLATED:', src in m.UNTRANSLATED); print('reason:', m.UNTRANSLATED.get(src))
