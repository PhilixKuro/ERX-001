"""容器内 env/bin/python 跑：对 zh.csv 与覆盖清单 ours 跑四道守卫，出计数与覆盖清单判定预查。"""
import collections, json, sys
sys.path.insert(0, "/workspace/frappe-bench/apps/frappe_china")
import csv
from frappe_china.tests import test_translation_quality as q
from frappe_china.tests.translation_overrides import OVERRIDES
path = "/workspace/frappe-bench/apps/frappe_china/frappe_china/translations/zh.csv"
rows = [r for r in csv.reader(open(path, encoding="utf-8", newline="")) if len(r) in (2, 3)]
print({g.__name__: len(g(rows)) for g in q.GUARDS})
bad = set()
for g in q.GUARDS:
    for item in g(rows):
        bad.add(item.split(" => ")[0])
print("rows hit by any guard:", len(bad), "of", len(rows))
ov_rows = [[k.split(":")[0] if False else k, v.ours] for k, v in OVERRIDES.items()]
hits = {k for k, v in OVERRIDES.items() if q.guard_problems([[k, v.ours]])}
print("overrides hit:", len(hits), "clean:", len(OVERRIDES) - len(hits))
for k, v in OVERRIDES.items():
    if k not in hits:
        print("CLEAN", repr(k), v.official, "->", v.ours, "|", v.basis)
