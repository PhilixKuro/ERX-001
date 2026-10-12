"""R8 IT-046：四个 Button 字段 label 的依据改为 DEC-027；10 条 ours == official 的无效覆盖从 csv 与 OVERRIDES 删掉。
宿主 python -I 跑，带 --write 才写。"""
import csv
import io
import re
import sys

APP = r"D:/ERX-001/frappe-bench/apps/frappe_china/frappe_china"
CSV_PATH = f"{APP}/translations/zh.csv"
OV_PATH = f"{APP}/tests/translation_overrides.py"
TO_DEC027 = ["Get Items for Purchase / Transfer", "Get Items for Purchase Only", "Get Sub Assembly Items", "Update Rate and Availability"]
NOOP = ["Accounts Receivable", "Add Row", "Cash Flow", "days", "Deals", "Debtors", "Global Defaults", "Leads", "Send", "Value"]
write = "--write" in sys.argv

ov = open(OV_PATH, encoding="utf-8", newline="").read()
nl = "\r\n" if "\r\n" in ov else "\n"  # 工作区文件可能是 CRLF（core.autocrlf），保留原换行
lines = ov.split(nl)
out, removed, rebased = [], [], []
for line in lines:
	m = re.match(r'\t"((?:[^"\\]|\\.)*)": Override\(', line)
	key = m.group(1) if m else None
	if key in NOOP:
		removed.append(key)
		continue
	if key in TO_DEC027:
		new = re.sub(r'"DEC-026[^"]*"\),$', '"DEC-027（R4 Desk 按钮悬停提示）"),', line)
		assert new != line, key
		rebased.append(key)
		line = new
	out.append(line)
assert sorted(removed) == sorted(NOOP), removed
assert sorted(rebased) == sorted(TO_DEC027), rebased

with open(CSV_PATH, encoding="utf-8", newline="") as handle:
	rows = list(csv.reader(handle))
kept = [row for row in rows if not (len(row) == 2 and row[0] in NOOP)]
dropped = [row for row in rows if len(row) == 2 and row[0] in NOOP]
assert sorted(r[0] for r in dropped) == sorted(NOOP), dropped
buffer = io.StringIO()
csv.writer(buffer, lineterminator="\n").writerows(kept)

print({"overrides_removed": len(removed), "rebased": len(rebased), "csv_before": len(rows), "csv_after": len(kept), "dropped": dropped})
if write:
	open(OV_PATH, "w", encoding="utf-8", newline="").write(nl.join(out))
	open(CSV_PATH, "w", encoding="utf-8", newline="").write(buffer.getvalue())
	print("written")
