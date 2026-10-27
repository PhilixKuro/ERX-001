"""Pull the server traceback out of a saved Frappe 500 page."""
import html
import re
import sys

t = open(sys.argv[1], encoding="utf-8", errors="replace").read()
hits = [m.start() for m in re.finditer(r"Traceback \(most recent call last\)", t)]
print("hits", len(hits), "size", len(t))
for start in hits[-1:]:
	seg = html.unescape(re.sub(r"<[^>]+>", "", t[start : start + 15000]))
	print(seg[:6000])
