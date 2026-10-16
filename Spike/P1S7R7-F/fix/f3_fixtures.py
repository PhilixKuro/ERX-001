"""FD-009 去掉 Item 服务水平默认 95；FD-010 Company 补货节挪到「库存与生产」页签末尾；FD-016 补 fixtures 清单。"""

import json
import sys

sys.path.insert(0, r"D:\ERX-001\Spike\P1S7R7-F\fix")
from repl import apply

A = r"D:\ERX-001\frappe-bench\apps\frappe_china\frappe_china"
path = A + r"\fixtures\custom_field.json"
raw = open(path, "rb").read().decode("utf-8")
crlf = "\r\n" in raw
rows = json.loads(raw)
NEW = "2026-10-17 10:00:00.000000"
for row in rows:
	if row["name"] == "Item-cn_service_level":
		assert row.get("default") == "95"
		row["default"] = None
		row["modified"] = NEW
	if row["name"] == "Company-cn_replenishment_section":
		assert row["insert_after"] == "default_currency"
		row["insert_after"] = "default_scrap_warehouse"
		row["modified"] = NEW
text = json.dumps(rows, ensure_ascii=False, indent=1) + "\n"
if crlf:
	text = text.replace("\n", "\r\n")
open(path, "wb").write(text.encode("utf-8"))

apply(
	A + r"\hooks.py",
	[('\t\t\t\t\t"Item-cn_unit_length_m",\n', '\t\t\t\t\t"Item-cn_unit_length_m",\n\t\t\t\t\t"Material Request-cn_replenishment_suggestion",\n')],
)
print("done")
