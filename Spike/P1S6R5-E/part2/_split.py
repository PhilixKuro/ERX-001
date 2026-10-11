"""R6 C 步事实补查：把 zh.csv 各行分为自有源词／点名用词／有依据的覆盖／批量档，并按 app 计批量档。"""
import ast
import collections
import csv
import importlib.util
from pathlib import Path

ROOT = Path("D:/ERX-001/frappe-bench/apps/frappe_china/frappe_china")
SPIKE = Path("D:/ERX-001/Spike")


def load(name, path):
	spec = importlib.util.spec_from_file_location(name, path)
	module = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(module)
	return module


baseline = load("baseline", SPIKE / "P1S6R4-baseline.py")
overrides = load("overrides", ROOT / "tests/translation_overrides.py").OVERRIDES

source = (ROOT / "tests/test_translations.py").read_text(encoding="utf-8")
code = source[source.index("def _app_source_strings"):source.index("# 编码名")]
namespace = {}
exec(code.replace("Path(__file__).resolve().parents[1]", f"Path(r'{ROOT}')"), namespace)
own = namespace["_app_source_strings"]()

tree = ast.parse((ROOT / "tests/test_named_terms.py").read_text(encoding="utf-8"))
named = next(set(ast.literal_eval(node.value).keys()) for node in tree.body
	if isinstance(node, ast.Assign) and node.targets[0].id == "NAMED_TERMS")

real = {key for key, item in overrides.items()
	if not any(mark in item.basis + item.ours for mark in ("????", "中文：", "???"))}

owner = {}
for app in baseline.APPS[:-1]:
	for entry in baseline.parse_po(baseline.app_path(app) / "locale/main.pot"):
		owner.setdefault(baseline.entry_key(entry), app)
		owner.setdefault(entry["id"], app)

rows = list(csv.reader((ROOT / "translations/zh.csv").open(encoding="utf-8", newline="")))
counts, by_app = collections.Counter(), collections.Counter()
for row in rows:
	key = row[0] + (":" + row[2] if len(row) > 2 and row[2] else "")
	if key in own or row[0] in own:
		counts["own"] += 1
	elif key in named:
		counts["named"] += 1
	elif key in real:
		counts["override-real"] += 1
	else:
		counts["batch"] += 1
		by_app[owner.get(key) or owner.get(row[0]) or "none"] += 1

print("rows", len(rows), dict(counts))
print("batch by app", dict(by_app))
print("own sources", len(own), "overrides", len(overrides), "real", len(real))
print("real override keys:", sorted(real))

# ---- 批量档细分：官方已有译文（覆盖）／不在任何 main.pot（孤儿）／真缺口 ----
official = {}
for app in baseline.APPS[:-1]:
	for entry in baseline.parse_po(baseline.app_path(app) / "locale/zh.po"):
		if entry["str"]:
			official[baseline.entry_key(entry)] = entry["str"]
kinds = collections.Counter(); orphans = []
for row in rows:
	key = row[0] + (":" + row[2] if len(row) > 2 and row[2] else "")
	if key in own or row[0] in own or key in named or key in real:
		continue
	if key in official:
		kinds["covers-official"] += 1
	elif key not in owner:
		kinds["orphan"] += 1; orphans.append(key)
	else:
		kinds["gap"] += 1
print("batch kinds", dict(kinds))
print("orphan sample", [o[:50] for o in orphans[:25]])
