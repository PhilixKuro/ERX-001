# 纯函数级：复制 test_translations._duplicate_keys 的实现，喂「字面 \n」与「真换行」两种写法的同一键
import csv
from collections import Counter
def _duplicate_keys(rows):
    keys = [row[0] + (":" + row[2] if len(row) == 3 and row[2] else "") for row in rows if len(row) in (2, 3)]
    return sorted(key for key, count in Counter(keys).items() if count > 1)
rows = [["a\nb", "x"], ["a\nb", "y"]]
print("detector:", _duplicate_keys(rows), "| frappe-normalized keys:", {r[0].replace("\n", "\n") for r in rows})
p = r"D:/ERX-001/frappe-bench/apps/frappe_china/frappe_china/translations/zh.csv"
lit = [r[0] for r in csv.reader(open(p, encoding="utf-8", newline="")) if "\n" in r[0]]
print("csv keys with literal backslash-n:", len(lit))
