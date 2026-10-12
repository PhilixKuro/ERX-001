"""R9 TS-028 第 1 步（HT-027）：frappe、erpnext、hrms 里 add_custom_button(／add_inner_button( 首参为字面量且带分组的调用，
以及以同一英文字面量调 change_／remove_ 两类按钮函数并带分组的调用。
宿主 python -I -X utf8 Spike/P1S6R9/ht027.py"""
import json
import re
from pathlib import Path

APPS = Path(__file__).resolve().parents[2] / "frappe-bench/apps"
STR = r"""(["'`])((?:\.|(?!\1).)*)\1"""
ADD = re.compile(r"(?:add_custom_button|add_inner_button)\(\s*" + STR + r"\s*,")
CALL = re.compile(r"(change_custom_button_type|remove_custom_button|change_inner_button_type|remove_inner_button)\(\s*" + STR + r"\s*(,\s*([^,)]+))?")


def args_after(text, start):
	"""从 start（首参之后的逗号后）起，按括号深度切出剩余实参，返回 [实参文本, ...]。"""
	depth, items, cur, i, quote = 0, [], "", start, None
	while i < len(text):
		c = text[i]
		if quote:
			cur += c
			if c == "\\":
				cur += text[i + 1]; i += 1
			elif c == quote:
				quote = None
		elif c in "\"'`":
			quote = c; cur += c
		elif c in "([{":
			depth += 1; cur += c
		elif c in ")]}":
			if depth == 0:
				items.append(cur.strip()); return items
			depth -= 1; cur += c
		elif c == "," and depth == 0:
			items.append(cur.strip()); cur = ""
		else:
			cur += c
		i += 1
	return items


adds, calls = [], []
for app in ("frappe", "erpnext", "hrms"):
	for path in (APPS / app / app).rglob("*.js"):
		if "node_modules" in path.parts or "/dist/" in path.as_posix():
			continue
		text = path.read_text(encoding="utf-8", errors="replace")
		rel = path.relative_to(APPS).as_posix()
		for m in ADD.finditer(text):
			rest = args_after(text, m.end())
			if len(rest) >= 2 and rest[1] not in ("", "null", "undefined"):
				adds.append({"file": rel, "line": text.count("\n", 0, m.start()) + 1, "label": m.group(2), "group": rest[1]})
		for m in CALL.finditer(text):
			calls.append({"file": rel, "line": text.count("\n", 0, m.start()) + 1, "fn": m.group(1), "label": m.group(3), "group": (m.group(5) or "").strip()})
labels = {a["label"] for a in adds}
conflicts = [c for c in calls if c["label"] in labels and c["group"]]
print(json.dumps({"raw_grouped_adds": adds, "same_label_calls": [c for c in calls if c["label"] in labels], "conflicts": conflicts}, ensure_ascii=False, indent=1))
