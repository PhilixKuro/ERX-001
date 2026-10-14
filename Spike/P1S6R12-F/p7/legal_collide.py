"""P7：csv 译文与法定列头（宽口径：三个文件里全部带汉字的字符串字面量）同名的行。只读。"""
import csv, re, sys, pathlib
app = pathlib.Path(sys.argv[1]) / "frappe_china"
labels = set()
for rel in ("accounting/statements/labels.py", "accounting/statements/mapping.py", "accounting/statements/cash_flow_statement.py"):
	labels |= {m for m in re.findall(r'"([^"\n]*[一-鿿][^"\n]*)"', (app / rel).read_text(encoding="utf-8"))}
rows = [r for r in csv.reader(open(app / "translations/zh.csv", encoding="utf-8", newline="")) if len(r) in (2, 3)]
hits = [(r[0], r[1]) for r in rows if r[1] in labels and r[0] != r[1]]
print("legal-ish labels:", len(labels), "csv rows:", len(rows), "collisions:", hits)
