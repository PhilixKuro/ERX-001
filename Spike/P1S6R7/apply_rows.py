"""把一批定稿行并入 zh.csv，并同步覆盖清单与点名用词表。容器内跑：
`env/bin/python /workspace/Spike/P1S6R7/apply_rows.py <rows.csv> <meta.json> [--write]`

meta.json：{键: {"basis": 依据, "named": 是否进 NAMED_TERMS}}；行里每个键都须在 meta 里。
检查：占位符与 HTML、四道守卫、法定列头、块内重复。键已在 csv 的行替换原行（回执记「改 csv」）。
写入：csv 全表排序（A20）；与官方交集的键追加／更新进 OVERRIDES（basis 取 meta，须合 _BASIS_FORM）；named 的键进 NAMED_TERMS。
不带 --write 只做检查与差异报告。
"""
from __future__ import annotations

import csv
import json
import re
import sys

APP = "/workspace/frappe-bench/apps/frappe_china"
sys.path.insert(0, APP)

from frappe_china.accounting.statements.labels import LEGAL_LABELS
from frappe_china.tests.test_translation_quality import guard_problems
from frappe_china.tests.test_translations import _BASIS_FORM, _tokens
from frappe_china.tests.translation_overrides import OVERRIDES, Override
from frappe_china.tests.test_named_terms import NAMED_TERMS

CSV_PATH = f"{APP}/frappe_china/translations/zh.csv"
OVERRIDES_PATH = f"{APP}/frappe_china/tests/translation_overrides.py"
NAMED_PATH = f"{APP}/frappe_china/tests/test_named_terms.py"
APPS = ("frappe", "erpnext", "crm", "hrms", "insights", "raven")


def key_of(row):
	# 与 frappe/translate.py:203 同：源词里的字面 \n 读入时换成换行，故按换行后的形态判重
	return row[0].replace("\\n", "\n") + (":" + row[2] if len(row) == 3 and row[2] else "")


def read_rows(path):
	with open(path, encoding="utf-8-sig", newline="") as handle:
		return [row for row in csv.reader(handle) if row]


def official_dict():
	"""六个官方 app 的 .po（与站点 get_translations_from_apps 同源，不必连站点）。"""
	from babel.messages.pofile import read_po

	result = {}
	for app in APPS:
		path = f"/workspace/frappe-bench/apps/{app}/{app}/locale/zh.po"
		try:
			with open(path, "rb") as handle:
				catalog = read_po(handle)
		except FileNotFoundError:
			continue
		for message in catalog:
			if message.id and message.string:
				result[message.id + (":" + message.context if message.context else "")] = message.string
	return result


def py(value):
	return '"' + value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'


def write_overrides(entries):
	lines = ["from typing import NamedTuple", "", "", "class Override(NamedTuple):", "\tofficial: str", "\tours: str", "\tbasis: str", "",
		"", "# 覆盖官方译名的 csv 行，逐条写真实依据（S6 R6 方案 TS-017；依据形态见 test_translations.test_override_basis_forms）",
		"OVERRIDES: dict[str, Override] = {"]
	for key in sorted(entries, key=lambda k: (k.casefold(), k)):
		value = entries[key]
		lines.append(f"\t{py(key)}: Override({py(value.official)}, {py(value.ours)}, {py(value.basis)}),")
	lines.append("}")
	with open(OVERRIDES_PATH, "w", encoding="utf-8", newline="\r\n") as handle:
		handle.write("\n".join(lines) + "\n")


def write_named(additions):
	text = open(NAMED_PATH, encoding="utf-8").read()
	start = text.index("NAMED_TERMS = {")
	end = text.index("\n}\n", start)
	body = text[start:end]
	for key, value in additions.items():
		line = f"\t{py(key)}: {py(value)},"
		pattern = re.compile(r"^\t" + re.escape(py(key)) + r": .*,$", re.MULTILINE)
		body = pattern.sub(line, body) if pattern.search(body) else body + "\n" + line
	with open(NAMED_PATH, "w", encoding="utf-8", newline="\n") as handle:
		handle.write(text[:start] + body + text[end:])


def main():
	rows_path, meta_path, *flags = sys.argv[1:]
	rows = read_rows(rows_path)
	meta = json.load(open(meta_path, encoding="utf-8"))
	problems = []
	seen = set()
	for number, row in enumerate(rows, 1):
		if len(row) not in (2, 3):
			problems.append(f"{number}: 列数 {len(row)}")
			continue
		key = key_of(row)
		if key in seen:
			problems.append(f"{number}: 块内重复 {key!r}")
		seen.add(key)
		if key not in meta:
			problems.append(f"{number}: meta 缺 {key!r}")
		if not row[1].strip():
			problems.append(f"{number}: 空译 {key!r}")
		if _tokens(row[0]) != _tokens(row[1]):
			problems.append(f"{number}: 占位符或 HTML 不一致 {key!r} => {row[1]!r}")
		if row[1].strip() in LEGAL_LABELS:
			problems.append(f"{number}: 与法定列头同名 {key!r}")
	problems.extend(guard_problems(rows))
	official = official_dict()
	current = {key_of(row): row for row in read_rows(CSV_PATH)}
	replaced = [(key, current[key][1], row[1]) for row in rows if (key := key_of(row)) in current and current[key][1] != row[1]]
	overrides = dict(OVERRIDES)
	named = {}
	for row in rows:
		key = key_of(row)
		info = meta.get(key, {})
		if key in official:
			basis = info.get("basis", "")
			if not _BASIS_FORM.match(basis):
				problems.append(f"覆盖官方但依据形态不合：{key!r} basis={basis!r}")
			overrides[key] = Override(official[key], row[1].strip(), basis)
		elif key in overrides:
			del overrides[key]
		if info.get("named"):
			named[key] = row[1].strip()
	report = {"rows": len(rows), "problems": len(problems), "replaced": replaced,
		"overrides_before": len(OVERRIDES), "overrides_after": len(overrides), "named_added": len(named)}
	print(json.dumps(report, ensure_ascii=False, indent=1))
	for problem in problems:
		print("  " + problem)
	if problems:
		sys.exit(1)
	if "--write" not in flags:
		return
	for row in rows:
		current[key_of(row)] = row
	merged = sorted(current.values(), key=lambda row: (row[0].casefold(), row[2] if len(row) == 3 else ""))
	with open(CSV_PATH, "w", encoding="utf-8", newline="") as handle:
		csv.writer(handle, lineterminator="\n").writerows(merged)
	write_overrides(overrides)
	if named:
		write_named(named)
	print(json.dumps({"csv_total": len(merged)}))


if __name__ == "__main__":
	main()
