"""R9：往 zh.csv 加／改行并按 A20 全表重排（源词不区分大小写，再按 context）。
宿主 `python -I -X utf8 Spike/P1S6R9/csv_rows.py <rows.json>`；rows.json 为 [[源词, 译文] 或 [源词, 译文, context], ...]。
同键（源词＋context）已存在则改译文，否则新增。打印新增、改动各几行。"""
import csv
import json
import sys
from pathlib import Path

CSV_PATH = Path(__file__).resolve().parents[2] / "frappe-bench/apps/frappe_china/frappe_china/translations/zh.csv"


def key(row):
	return (row[0], row[2] if len(row) == 3 else "")


rows = list(csv.reader(CSV_PATH.open(encoding="utf-8", newline="")))
index = {key(row): i for i, row in enumerate(rows)}
added = changed = 0
for new in json.loads(Path(sys.argv[1]).read_text(encoding="utf-8")):
	if key(new) in index:
		old = rows[index[key(new)]]
		if old[1] != new[1]:
			print("changed", old, "->", new)
			rows[index[key(new)]] = new
			changed += 1
	else:
		rows.append(new)
		index[key(new)] = len(rows) - 1
		added += 1
rows.sort(key=lambda row: (row[0].casefold(), row[2] if len(row) == 3 else ""))
with CSV_PATH.open("w", encoding="utf-8", newline="") as handle:
	csv.writer(handle, lineterminator="\n").writerows(rows)
print({"added": added, "changed": changed, "rows": len(rows)})
