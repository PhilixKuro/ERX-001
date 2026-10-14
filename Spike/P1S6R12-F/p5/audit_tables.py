"""F 分片 5：三张例外表与 csv 的一致性、csv 行来源归类、覆盖键在上游源码里的全部出处（只读）。
python -I -X utf8 Spike/P1S6R12-F/p5/audit_tables.py
"""
from __future__ import annotations

import ast
import csv
import glob
import importlib.util
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
APP = ROOT / "frappe-bench/apps/frappe_china/frappe_china"
APPS = ROOT / "frappe-bench/apps"


def load(path, name):
	spec = importlib.util.spec_from_file_location(name, path)
	mod = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(mod)
	return mod


baseline = load(ROOT / "Spike/P1S6R4-baseline.py", "baseline")
prune = load(ROOT / "Spike/P1S6R6-csv-prune.py", "prune")


def dict_literal(path, name):
	tree = ast.parse(Path(path).read_text(encoding="utf-8"))
	for node in tree.body:
		target = node.target if isinstance(node, ast.AnnAssign) else (node.targets[0] if isinstance(node, ast.Assign) else None)
		if isinstance(target, ast.Name) and target.id == name:
			return {ast.literal_eval(k): v for k, v in zip(node.value.keys, node.value.values)}
	raise KeyError(name)


rows = list(csv.reader((APP / "translations/zh.csv").open(encoding="utf-8", newline="")))
csv_keys = {prune.row_key(r) for r in rows}
csv_map = {prune.row_key(r): r[1] for r in rows}
qe = dict_literal(APP / "tests/test_translation_quality.py", "QUALITY_EXCEPTIONS")
allow = dict_literal(APP / "tests/test_translation_quality.py", "ALLOW")
untr = baseline.untranslated()
out = {}
out["QUALITY_EXCEPTIONS_not_in_csv"] = sorted(k for k in qe if k.replace("\\n", "\n") not in csv_keys and k not in csv_keys)
words = re.compile(r"[A-Za-z][A-Za-z0-9]+")
used = set()
for r in rows:
	used.update(words.findall(r[1]))
out["ALLOW_unused"] = sorted(w for w in allow if w not in used)
pot_keys = set()
for app in ("frappe", "erpnext", "crm", "hrms", "insights", "raven"):
	for e in baseline.parse_po(baseline.app_path(app) / "locale/main.pot"):
		pot_keys.add(baseline.entry_key(e))
own = prune._app_source_strings()
out["UNTRANSLATED_not_in_pot_nor_own"] = sorted(k for k in untr if k not in pot_keys and k.replace("\\n", "\n") not in pot_keys and k not in own)
out["UNTRANSLATED_also_in_csv"] = sorted(k for k in untr if k in csv_keys or k.replace("\\n", "\n") in csv_keys)
out["UNTRANSLATED_count"] = len(untr)

# csv 行来源归类：A15 四类之外还剩什么
keep = prune.keep_keys()
blocks = set()
for f in glob.glob(str(ROOT / "Spike/P1S6R6-*/in-*.json")):
	for item in json.loads(Path(f).read_text(encoding="utf-8"))["items"]:
		blocks.add(item["key"].replace("\\n", "\n"))
classified = keep["own"] | keep["named"] | keep["override"] | blocks
rest = sorted(csv_keys - classified)
out["csv_rows"] = len(rows)
out["csv_not_in_A15_123_nor_blocks"] = len(rest)
out["csv_not_in_A15_123_nor_blocks_sample"] = [[k, csv_map[k]] for k in rest]
# 再跑一次清场（dry）会删多少
kept, dropped, counts = prune.prune(rows)
out["prune_rerun_counts"] = counts

# 无 context 的覆盖键：上游源码里的全部出处（不只 main.pot）
overrides = dict_literal(APP / "tests/translation_overrides.py", "OVERRIDES")
pat_cache = {}
files = []
import os

SKIP = {"node_modules", "locale", "dist", ".git", "__pycache__", "assets", "www_build"}
for app in ("frappe", "erpnext", "crm", "hrms", "insights", "raven"):
	for dirpath, dirnames, filenames in os.walk(APPS / app):
		dirnames[:] = [d for d in dirnames if d not in SKIP and not d.startswith(".")]
		for name in filenames:
			if name.rsplit(".", 1)[-1] in ("py", "js", "vue", "ts", "tsx", "html", "json") and "test" not in name:
				files.append(Path(dirpath) / name)
texts = {}
for p in files:
	try:
		texts[p] = p.read_text(encoding="utf-8")
	except Exception:
		pass
refs = {}
for key in overrides:
	if ":" in key and key.split(":")[-1][:1].isupper() and " " not in key.split(":")[-1][:0]:
		pass
	esc = re.escape(key)
	call = re.compile(r"""(?<![A-Za-z_])_{1,2}\(\s*(["'])""" + esc + r"""\1\s*[,)]""")
	label = re.compile(r'"label":\s*"' + esc + r'"')
	opt = re.compile(r'"options":\s*"(?:[^"]*\\n)?' + esc + r'(?:\\n[^"]*)?"')
	hits = []
	for p, t in texts.items():
		for rx, kind in ((call, "call"), (label, "label"), (opt, "option")):
			for m in rx.finditer(t):
				hits.append(f"{p.relative_to(APPS).as_posix()}:{t.count(chr(10), 0, m.start()) + 1}:{kind}")
	refs[key] = hits
out["override_refs"] = refs
Path(__file__).with_name("audit_tables.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
for k, v in out.items():
	if k != "override_refs":
		print(k, json.dumps(v, ensure_ascii=False)[:1500])
print("override keys with refs:", {k: len(v) for k, v in refs.items()})
