"""P1-S6-R12 F 分片 6：取法一致性扫描（只读）。

宿主 `python -I -X utf8 Spike/P1S6R12-F/p6/scan_keys.py`。
1. 从 test_translations.py 用 ast 取出 _source_strings_from_text / _app_source_strings 两个函数 exec（不 import frappe）；
2. 另用宽口径扫 frappe_china 全部非 tests 的 .py/.js/.html/.json 中所有字符串字面量；
3. 对 zh.csv 的键：宽口径命中（源码里出现过该字面量）但 keep_keys 三类都不认 → 疑似漏认的自有键；
4. 列出所有 __(/_(/translate( 调用里实参不是单个字面量的调用点（取法认不出）。
输出 JSON 到 stdout。
"""
from __future__ import annotations

import ast
import csv
import importlib.util
import io
import json
import re
import sys
import tokenize
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
APP = ROOT / "frappe-bench/apps/frappe_china/frappe_china"

spec = importlib.util.spec_from_file_location("prune", ROOT / "Spike/P1S6R6-csv-prune.py")
prune = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prune)

tree = ast.parse((APP / "tests/test_translations.py").read_text(encoding="utf-8"))
fns = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in ("_source_strings_from_text", "_app_source_strings")]
ns = {"__file__": str(APP / "tests/test_translations.py")}
exec(compile(ast.Module(body=fns, type_ignores=[]), "tt", "exec"), ns)
from_text = ns["_source_strings_from_text"]

keep = prune.keep_keys()
keep_all = keep["own"] | keep["named"] | keep["override"]

with (APP / "translations/zh.csv").open(encoding="utf-8", newline="") as h:
	rows = [r for r in csv.reader(h) if len(r) in (2, 3)]
csv_keys = {prune.row_key(r): r for r in rows}
plain_csv = {r[0].replace("\\n", "\n") for r in rows}


def py_literals(text):
	out = []
	try:
		for tok in tokenize.generate_tokens(io.StringIO(text).readline):
			if tok.type == tokenize.STRING:
				try:
					v = ast.literal_eval(tok.string)
				except Exception:
					continue
				if isinstance(v, str):
					out.append((v, tok.start[0]))
	except tokenize.TokenError:
		pass
	return out


JS_STR = re.compile(r"""(["'`])((?:\\.|(?!\1).)*?)\1""", re.S)


def js_literals(text):
	out = []
	for m in JS_STR.finditer(text):
		out.append((m.group(2), text.count("\n", 0, m.start()) + 1))
	return out


def json_strings(obj, acc):
	if isinstance(obj, str):
		acc.append(obj)
	elif isinstance(obj, list):
		for x in obj:
			json_strings(x, acc)
	elif isinstance(obj, dict):
		for x in obj.values():
			json_strings(x, acc)


files = [p for p in [*APP.rglob("*.py"), *APP.rglob("*.js"), *APP.rglob("*.json"), *APP.rglob("*.html")]
         if not ("tests" in p.parts and p.suffix != ".json") and "node_modules" not in p.parts]

wide: dict[str, list[str]] = {}
extracted_by_file: dict[str, set[str]] = {}
nonliteral_calls = []
CALL = re.compile(r"(?<![A-Za-z_.$])(_{1,2}|translate)\(")
for p in files:
	rel = p.relative_to(APP).as_posix()
	text = p.read_text(encoding="utf-8")
	if p.suffix in (".py", ".js", ".json"):
		try:
			extracted_by_file[rel] = from_text(rel, text)
		except Exception as e:  # noqa
			extracted_by_file[rel] = {f"<error {e}>"}
	if p.suffix == ".py":
		lits = py_literals(text)
	elif p.suffix == ".json":
		acc = []
		json_strings(json.loads(text), acc)
		lits = [(s, 0) for s in acc]
	else:
		lits = js_literals(text)
	for v, line in lits:
		if v in plain_csv:
			wide.setdefault(v, []).append(f"{rel}:{line}")
	if p.suffix in (".py", ".js", ".html"):
		for m in CALL.finditer(text):
			after = text[m.end():m.end() + 120]
			if not re.match(r"""\s*(["'])""", after):
				line = text.count("\n", 0, m.start()) + 1
				nonliteral_calls.append(f"{rel}:{line}: {text[m.start():m.end() + 70].splitlines()[0]}")

own_text = set().union(*extracted_by_file.values())
suspects = {}
for key, locs in sorted(wide.items()):
	if key in keep_all:
		continue
	# 对应的 csv 键可能带 context
	if any(k.startswith(key + ":") and k in keep_all for k in csv_keys):
		continue
	suspects[key] = {"csv": csv_keys.get(key), "locs": locs[:6]}

result = {
	"files_scanned": len(files),
	"own_from_text_union": len(own_text),
	"app_source_strings": len(ns["_app_source_strings"]()),
	"keep_counts": {k: len(v) for k, v in keep.items()},
	"csv_rows": len(rows),
	"suspects_wide_literal_in_csv_not_kept": suspects,
	"nonliteral_translate_calls": nonliteral_calls,
	"own_not_in_csv_or_merged_check": sorted(k for k in keep["own"] if k not in csv_keys)[:400],
}
json.dump(result, sys.stdout, ensure_ascii=False, indent=1)
