# R13 F p2：扫六个 app 的全部 po，看 `Master` 与 `Master Data` 在各语言下的译文，
# 判 dashboards.py 无语言守卫对非中文会话的影响。只读。
import re, sys
from pathlib import Path

apps = Path(sys.argv[1]) / "frappe-bench/apps"
rows = []
for app in ("frappe", "erpnext", "crm", "hrms", "insights", "raven"):
	for po in sorted((apps / app / app / "locale").glob("*.po")):
		t = po.read_text(encoding="utf-8-sig")
		got = {}
		for key in ("Master", "Master Data"):
			# 只取无 msgctxt 的那条
			for m in re.finditer(r"\n(?:#[^\n]*\n)*msgid \"" + re.escape(key) + r"\"\nmsgstr \"([^\"]*)\"", t):
				if m.group(1):
					got[key] = m.group(1)
		if got:
			rows.append((app, po.stem, got))
print(f"命中条目 {len(rows)} 条")
for app, lang, got in rows:
	print(f"{app:8} {lang:6} {got}")
langs = {lang for _, lang, got in rows if got.get("Master")}
print("\n有 Master 译文的语言：", sorted(langs))
print("有 Master Data 译文的语言：", sorted({lang for _, lang, got in rows if got.get('Master Data')}))
