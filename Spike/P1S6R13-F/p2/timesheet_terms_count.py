# R13 F p2：复算 test_named_terms._official_timesheet_terms 在锁定版本下的条数，
# 并核六个 app 的 locale/zh.po 是否都存在（断言下限 29 是否贴着实际值）。只读。
import ast, sys
from pathlib import Path

apps = Path(sys.argv[1]) / "frappe-bench/apps"
result = {}
for app in ("frappe", "erpnext", "crm", "hrms", "insights", "raven"):
	path = apps / app / app / "locale" / "zh.po"
	print(f"{app:8} zh.po exists={path.exists()}")
	if not path.exists():
		continue
	msgid = context = msgstr = None
	field = None
	hits = 0
	for line in [*path.read_text(encoding="utf-8-sig").splitlines(), ""]:
		if not line.strip():
			if msgid is not None and msgstr and "工时表" in msgstr:
				result[msgid + ((":" + context) if context else "")] = msgstr
				hits += 1
			msgid = context = msgstr = None
			field = None
		elif line.startswith("msgctxt "):
			context = ast.literal_eval(line[8:]); field = "context"
		elif line.startswith("msgid "):
			msgid = ast.literal_eval(line[6:]); field = "msgid"
		elif line.startswith("msgstr "):
			msgstr = ast.literal_eval(line[7:]); field = "msgstr"
		elif line.startswith('"') and field:
			v = ast.literal_eval(line)
			if field == "msgid":
				msgid = (msgid or "") + v
			elif field == "context":
				context = (context or "") + v
			else:
				msgstr = (msgstr or "") + v
	print(f"         含「工时表」的条目 {hits}")
print("去重后合计", len(result), "（用例断言 >= 29）")
