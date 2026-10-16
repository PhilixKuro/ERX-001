"""FD-011／FD-023 新增源词进 zh.csv，按 _sort_key 插入（源词 casefold、context）。"""

import csv
import io

PATH = r"D:\ERX-001\frappe-bench\apps\frappe_china\frappe_china\translations\zh.csv"
NEW = [
	["{0} processed, {1} skipped", "已处理 {0} 条，跳过 {1} 条"],
	["Daily replenishment calculation has problems", "每日补货计算有问题"],
	["frappe_china override self-check failed", "frappe_china 覆盖自检未通过"],
	["No company has replenishment enabled.", "没有启用补货的公司。"],
	["Replenishment Calculated", "补货计算完成"],
	["Replenishment Calculated with Problems", "补货计算完成，有问题"],
]

raw = open(PATH, "rb").read().decode("utf-8")
nl = "\r\n" if "\r\n" in raw else "\n"
rows = list(csv.reader(io.StringIO(raw, newline="")))
keys = {(r[0], r[2] if len(r) == 3 else "") for r in rows if r}
for new in NEW:
	assert (new[0], "") not in keys, new


def key(row):
	return (row[0].casefold(), row[2] if len(row) == 3 else "")


for new in NEW:
	index = next((i for i, row in enumerate(rows) if row and key(row) > key(new)), len(rows))
	rows.insert(index, new)

out = io.StringIO(newline="")
csv.writer(out, lineterminator=nl).writerows(rows)
open(PATH, "wb").write(out.getvalue().encode("utf-8"))
print("done", len(rows))
