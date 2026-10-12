"""IT-044：新旧 _PLACEHOLDER 在 zh.csv 全表与六 app 源词上的差异。"""
import csv, re
OLD = re.compile(r"\{\{?\s*[^{}]+\s*\}?|\{\d+\}|%\([^)]*\)s|%s")
NEW = re.compile(r"\{\{?\s*[^{}]+?\s*\}\}?|\{\d+\}|%\([^)]*\)s|%s")
rows = list(csv.reader(open(r"D:/ERX-001/frappe-bench/apps/frappe_china/frappe_china/translations/zh.csv", encoding="utf-8", newline="")))
n = 0
for r in rows:
    for t in r[:2]:
        if sorted(OLD.findall(t)) != sorted(NEW.findall(t)):
            n += 1; print(repr(t[:120]), OLD.findall(t), NEW.findall(t))
bad = [r[0] for r in rows if len(r) >= 2 and sorted(NEW.findall(r[0])) != sorted(NEW.findall(r[1]))]
print("diff cells", n, "mismatch rows under NEW", len(bad), bad[:5])
