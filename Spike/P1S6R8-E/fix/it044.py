"""R8 IT-044：补译 Naming series 源词（占位符正则修好后可过检查），移出白名单。宿主 python -I 跑，带 --write 才写。"""
import csv
import io
import sys

APP = r"D:/ERX-001/frappe-bench/apps/frappe_china/frappe_china"
CSV_PATH = f"{APP}/translations/zh.csv"
WL_PATH = f"{APP}/tests/translation_whitelist.py"
KEY = "Naming series '{0}' for DocType '{1}' does not contain standard '.' or '{{' separator. Using fallback extraction."
# 「{{」原样保留：源词经 str.format 后显示为「{」，译文同样经 format
ZH = "编号模板「{0}」（单据类型「{1}」）不含标准分隔符「.」或「{{」，改用备用方式提取前缀。"
write = "--write" in sys.argv


def sort_key(row):
	return (row[0].casefold(), row[2] if len(row) == 3 else "")


with open(CSV_PATH, encoding="utf-8", newline="") as handle:
	rows = list(csv.reader(handle))
assert not any(row[0] == KEY for row in rows)
rows.append([KEY, ZH])
rows.sort(key=sort_key)
buffer = io.StringIO()
csv.writer(buffer, lineterminator="\n").writerows(rows)

wl = open(WL_PATH, encoding="utf-8", newline="").read()
nl = "\r\n" if "\r\n" in wl else "\n"
lines = wl.split(nl)
hits = [i for i, line in enumerate(lines) if line.startswith("\t\"Naming series '{0}' for DocType")]
assert len(hits) == 1, hits
del lines[hits[0]]

print({"csv_rows": len(rows), "whitelist_line_removed": hits[0] + 1, "check": "{0}".format(ZH.replace("{0}", "X").replace("{1}", "Y"))[:60]})
if write:
	open(CSV_PATH, "w", encoding="utf-8", newline="").write(buffer.getvalue())
	open(WL_PATH, "w", encoding="utf-8", newline="").write(nl.join(lines))
	print("written")
