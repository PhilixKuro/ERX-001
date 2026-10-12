"""IT-044／045 判别力：旧正则下新用例的两条断言应失败；_misused_own_basis 去掉判断应失败。"""
import re
OLD = re.compile(r"\{\{?\s*[^{}]+\s*\}?|\{\d+\}|%\([^)]*\)s|%s")
NEW = re.compile(r"\{\{?\s*[^{}]+?\s*\}\}?|\{\d+\}|%\([^)]*\)s|%s")
src = "Series '{0}' has no '{{' separator. Using fallback."
zh = "编号模板「{0}」不含「{{」分隔符，改用备用方式"
for name, rx in (("old", OLD), ("new", NEW)):
    a = sorted(rx.findall(src)) == sorted(rx.findall(zh))
    b = rx.findall("{{ doc.name }} and {label}") == ["{{ doc.name }}", "{label}"]
    print(name, "closing-brace assert1", a, "assert2", b)
ov = {"Formula": "本 app 自有源词", "Other": "本 app 自有源词"}
guard = sorted(k for k, v in ov.items() if v.startswith("本 app 自有源词") and k not in {"Formula"})
noguard = sorted(k for k, v in ov.items() if False)
print("own-basis guard", guard, "without guard", noguard)
