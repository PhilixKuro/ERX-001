"""TS-019 第 2 步／TS-021 第 3 步：合并前机检。容器内 `env/bin/python /workspace/Spike/P1S6R7/merge_check.py <in.json> <part.csv> [--merge]`。

检查 part.csv 每行：键属于 in.json；无空译；占位符与 HTML 标签与源词一致（test_translations._tokens）；
过四道质量守卫（test_translation_quality）；不与法定列头同名（LEGAL_LABELS）；不与 csv 现有键重复；in.json 每个键都有译文。
全部通过才允许 --merge：并入 zh.csv 后全表排序（A20）。任一项不过即非 0 退出，整块退回。
"""
from __future__ import annotations

import csv
import json
import sys

sys.path.insert(0, "/workspace/frappe-bench/apps/frappe_china")

from frappe_china.accounting.statements.labels import LEGAL_LABELS
from frappe_china.tests.test_translation_quality import guard_problems
from frappe_china.tests.test_translations import _tokens
from frappe_china.tests.translation_whitelist import UNTRANSLATED

CSV_PATH = "/workspace/frappe-bench/apps/frappe_china/frappe_china/translations/zh.csv"


def key_of(row: list[str]) -> str:
	# 与 frappe/translate.py:203 同：源词里的字面 \n 读入时换成换行，故按换行后的形态判重
	return row[0].replace("\\n", "\n") + (":" + row[2] if len(row) == 3 and row[2] else "")


def read_rows(path: str) -> list[list[str]]:
	with open(path, encoding="utf-8-sig", newline="") as handle:
		return [row for row in csv.reader(handle) if row]


def check(in_path: str, part_path: str) -> tuple[list[str], list[list[str]]]:
	# 进了 UNTRANSLATED 白名单的键（品牌名、标识符等原样显示）不要求有译文
	expected = {item["key"].replace("\\n", "\n") for item in json.load(open(in_path, encoding="utf-8"))["items"]}
	expected -= {key.replace("\\n", "\n") for key in UNTRANSLATED}
	rows = read_rows(part_path)
	existing = {key_of(row) for row in read_rows(CSV_PATH)}
	problems = []
	seen = set()
	for number, row in enumerate(rows, 1):
		if len(row) not in (2, 3):
			problems.append(f"{number}: 列数 {len(row)}")
			continue
		key, target = key_of(row), row[1]
		if key not in expected:
			problems.append(f"{number}: 键不在本块 {key!r}")
		if key in seen:
			problems.append(f"{number}: 块内重复 {key!r}")
		seen.add(key)
		if key in existing:
			problems.append(f"{number}: csv 已有该键 {key!r}")
		if not target.strip():
			problems.append(f"{number}: 空译 {key!r}")
		if _tokens(row[0]) != _tokens(target):
			problems.append(f"{number}: 占位符或 HTML 不一致 {key!r} => {target!r}")
		if target.strip() in LEGAL_LABELS:
			problems.append(f"{number}: 与法定列头同名 {key!r} => {target!r}")
	problems.extend(guard_problems(rows))
	missing = sorted(expected - seen)
	if missing:
		problems.append(f"缺译 {len(missing)} 条：{missing[:20]}")
	return problems, rows


def merge(rows: list[list[str]]) -> int:
	current = read_rows(CSV_PATH)
	merged = sorted(current + rows, key=lambda row: (row[0].casefold(), row[2] if len(row) == 3 else ""))
	with open(CSV_PATH, "w", encoding="utf-8", newline="") as handle:
		csv.writer(handle, lineterminator="\n").writerows(merged)
	return len(merged)


def main() -> None:
	in_path, part_path, *flags = sys.argv[1:]
	problems, rows = check(in_path, part_path)
	print(json.dumps({"part": part_path, "rows": len(rows), "problems": len(problems)}, ensure_ascii=False))
	for problem in problems:
		print("  " + problem)
	if problems:
		sys.exit(1)
	if "--merge" in flags:
		print(json.dumps({"merged_total": merge(rows)}))


if __name__ == "__main__":
	main()
