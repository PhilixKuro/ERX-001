"""R11 E independent grep for HT-027: grouped add_custom_button / add_inner_button calls and
change/remove calls with a group, across desk JS of all apps. Read-only.
python -I -X utf8 grep_buttons.py <apps_dir>"""
import json
import re
import sys
from pathlib import Path

APPS = Path(sys.argv[1])
FN_ADD = ("add_custom_button", "add_inner_button")
FN_CHG = ("change_custom_button_type", "remove_custom_button", "change_inner_button_type", "remove_inner_button")
CALL = re.compile(r"\b(" + "|".join(FN_ADD + FN_CHG) + r")\s*\(")


def split_args(text, i):
	"""i points just after '('. Return list of raw top-level argument strings."""
	depth, cur, out, quote = 0, [], [], None
	while i < len(text):
		c = text[i]
		if quote:
			cur.append(c)
			if c == "\\" and i + 1 < len(text):
				cur.append(text[i + 1]); i += 1
			elif c == quote:
				quote = None
		elif c in "\"'`":
			quote = c; cur.append(c)
		elif c in "([{":
			depth += 1; cur.append(c)
		elif c in ")]}":
			if depth == 0:
				out.append("".join(cur).strip()); return out
			depth -= 1; cur.append(c)
		elif c == "," and depth == 0:
			out.append("".join(cur).strip()); cur = []
		else:
			cur.append(c)
		i += 1
	return out


LIT = re.compile(r"""^(["'])(.*)\1$|^`([^`$]*)`$""", re.S)
rows = []
for app_dir in sorted(p for p in APPS.iterdir() if p.is_dir()):
	if app_dir.name == "frappe_china":
		continue
	import os
	paths = []
	for d, dirs, files in os.walk(app_dir):
		dirs[:] = [x for x in dirs if x not in ("node_modules", "dist", ".git", "frontend")]
		paths += [Path(d) / f for f in files if f.endswith(".js")]
	for path in paths:
		try:
			text = path.read_text(encoding="utf-8", errors="replace")
		except OSError:
			continue
		for m in CALL.finditer(text):
			args = split_args(text, m.end())
			fn = m.group(1)
			grp_idx = 2 if fn in FN_ADD else 1
			group = args[grp_idx] if len(args) > grp_idx else ""
			label = args[0] if args else ""
			lit = LIT.match(label)
			rows.append({
				"file": path.relative_to(APPS).as_posix(),
				"line": text.count("\n", 0, m.start()) + 1,
				"fn": fn,
				"label": label[:120],
				"label_literal": (lit.group(2) if lit and lit.group(2) is not None else (lit.group(3) if lit else None)),
				"group": group[:80],
			})
json.dump(rows, sys.stdout, ensure_ascii=False, indent=0)
