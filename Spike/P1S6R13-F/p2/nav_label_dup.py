# R13 F p2：按「六个 app 的 zh.po ＋ 本 app zh.csv（后者覆盖）」近似合并字典，
# 核业务流程侧栏 7 个分节与 51 个条目的中文显示是否跨类型重名
# （用例 test_chinese_labels_are_unique 只在同类型内判）。只读。
import ast, csv, json, re, sys
from pathlib import Path

root = Path(sys.argv[1])
apps = root / "frappe-bench/apps"
merged = {}


def load_po(path):
	msgid = ctx = msgstr = None
	field = None
	out = {}
	lines = path.read_text(encoding="utf-8-sig").splitlines() + [""]
	for line in lines:
		if not line.strip():
			if msgid is not None and msgstr:
				out[msgid + ((":" + ctx) if ctx else "")] = msgstr
			msgid = ctx = msgstr = None
			field = None
		elif line.startswith("msgctxt "):
			ctx = ast.literal_eval(line[8:]); field = "ctx"
		elif line.startswith("msgid "):
			msgid = ast.literal_eval(line[6:]); field = "msgid"
		elif line.startswith("msgstr "):
			msgstr = ast.literal_eval(line[7:]); field = "msgstr"
		elif line.startswith('"') and field:
			v = ast.literal_eval(line)
			if field == "msgid":
				msgid = (msgid or "") + v
			elif field == "ctx":
				ctx = (ctx or "") + v
			else:
				msgstr = (msgstr or "") + v
	return out


for app in ("frappe", "erpnext", "crm", "hrms", "insights", "raven"):
	p = apps / app / app / "locale" / "zh.po"
	if p.exists():
		merged.update(load_po(p))
with open(apps / "frappe_china/frappe_china/translations/zh.csv", encoding="utf-8", newline="") as f:
	for row in csv.reader(f):
		if len(row) >= 3 and row[2]:
			merged[f"{row[0]}:{row[2]}"] = row[1]
		elif len(row) >= 2:
			merged[row[0]] = row[1]

d = json.loads((apps / "frappe_china/frappe_china/workspace_sidebar/business_flow.json").read_text(encoding="utf-8"))
shown = {}
for it in d["items"]:
	label = it["label"]
	shown.setdefault(merged.get(label, label), []).append((it["type"], label))
print("分节+条目合计", sum(len(v) for v in shown.values()))
dups = {k: v for k, v in shown.items() if len(v) > 1}
print("跨类型/同类型重名:", json.dumps(dups, ensure_ascii=False))
for it in d["items"]:
	if it["type"] == "Section Break":
		print("分节", it["label"], "->", merged.get(it["label"], it["label"]))
