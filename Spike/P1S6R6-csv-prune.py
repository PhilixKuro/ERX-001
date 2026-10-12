"""S6 R6 方案 TS-018：按 A15 清场 zh.csv 并全表排序（A20）。宿主 `python -I -X utf8 Spike/P1S6R6-csv-prune.py [--dry-run]`。

保留四类：① 本 app 自有源词（复用 test_translations._app_source_strings 的取法）∪ REQUIRED_TRANSLATIONS；
② NAMED_TERMS；③ OVERRIDES（TS-017 重建后）；④ 本轮 TS-019～021 新写的行（本脚本只在 TS-018 跑一次，此时 ④ 为空）。
删除行另存 Spike/P1S6R6-pruned.csv 留档。
"""
from __future__ import annotations

import argparse
import ast
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "frappe-bench/apps/frappe_china/frappe_china"
CSV_PATH = APP / "translations/zh.csv"
PRUNED_PATH = ROOT / "Spike/P1S6R6-pruned.csv"


def _module_ast(path: Path) -> ast.Module:
	return ast.parse(path.read_text(encoding="utf-8"))


def _assigned(tree: ast.Module, name: str) -> ast.expr:
	for node in tree.body:
		target = node.target if isinstance(node, ast.AnnAssign) else (node.targets[0] if isinstance(node, ast.Assign) else None)
		if isinstance(target, ast.Name) and target.id == name:
			return node.value
	raise KeyError(f"{name} not found")


def _dict_keys(path: Path, name: str) -> set[str]:
	value = _assigned(_module_ast(path), name)
	if not isinstance(value, ast.Dict):
		raise TypeError(f"{path.name}:{name} is not a dict literal")
	return {ast.literal_eval(key) for key in value.keys}


def _app_source_strings() -> set[str]:
	"""执行 test_translations.py 里同名函数的源码（不 import frappe），保证与测试同一取法。"""
	path = APP / "tests/test_translations.py"
	tree = _module_ast(path)
	# R9 TS-025：取法拆成两层，两个函数都要取出（import 都在函数体内）
	names = ("_source_strings_from_text", "_app_source_strings")
	functions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names]
	if len(functions) != len(names):
		raise KeyError(f"test_translations.py 缺函数：{set(names) - {node.name for node in functions}}")
	namespace = {"__file__": str(path)}
	exec(compile(ast.Module(body=functions, type_ignores=[]), str(path), "exec"), namespace)
	return namespace["_app_source_strings"]()


def keep_keys() -> dict[str, set[str]]:
	tests = APP / "tests"
	return {
		"own": _app_source_strings() | _dict_keys(tests / "test_translations.py", "REQUIRED_TRANSLATIONS"),
		"named": _dict_keys(tests / "test_named_terms.py", "NAMED_TERMS"),
		"override": _dict_keys(tests / "translation_overrides.py", "OVERRIDES"),
	}


def row_key(row: list[str]) -> str:
	return row[0].replace("\\n", "\n") + (":" + row[2] if len(row) == 3 and row[2] else "")


def prune(rows: list[list[str]]) -> tuple[list[list[str]], list[list[str]], dict[str, int]]:
	"""返回（保留行，删除行，{类别: 行数}）；一行同属多类时记在第一个命中的类别。"""
	classes = keep_keys()
	kept, dropped = [], []
	counts = {name: 0 for name in classes} | {"dropped": 0}
	for row in rows:
		category = next((name for name, keys in classes.items() if row_key(row) in keys), None)
		if category:
			kept.append(row)
			counts[category] += 1
		else:
			dropped.append(row)
			counts["dropped"] += 1
	return kept, dropped, counts


def sort_rows(rows: list[list[str]]) -> list[list[str]]:
	return sorted(rows, key=lambda row: (row[0].casefold(), row[2] if len(row) == 3 else ""))


def _read(path: Path) -> list[list[str]]:
	with path.open(encoding="utf-8", newline="") as handle:
		rows = list(csv.reader(handle))
	bad = [row for row in rows if len(row) not in (2, 3)]
	if bad:
		raise ValueError(f"rows with wrong column count: {bad[:5]}")
	return rows


def _write(path: Path, rows: list[list[str]]) -> None:
	with path.open("w", encoding="utf-8", newline="") as handle:
		csv.writer(handle, lineterminator="\n").writerows(rows)


def main() -> None:
	parser = argparse.ArgumentParser()
	parser.add_argument("--dry-run", action="store_true")
	args = parser.parse_args()
	rows = _read(CSV_PATH)
	kept, dropped, counts = prune(rows)
	assert len(kept) + len(dropped) == len(rows)
	report = {"original": len(rows), "kept": len(kept), **counts}
	print(json.dumps(report, ensure_ascii=False))
	if args.dry_run:
		return
	_write(PRUNED_PATH, dropped)
	_write(CSV_PATH, sort_rows(kept))


if __name__ == "__main__":
	main()
