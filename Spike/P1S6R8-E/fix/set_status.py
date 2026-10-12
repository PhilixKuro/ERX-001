"""把 R8 报告「问题详情」各行的档位/状态改为裁决后的值。用法：python -I set_status.py <json>"""
import json, re, sys
P = r"D:/ERX-001/docs/01-需求摸底/S06-译名与导航/R08-确认/P1-S6-R8-E确认报告.md"
m = json.load(open(sys.argv[1], encoding="utf-8"))
s = open(P, encoding="utf-8", newline="").read()
nl = "\r\n" if "\r\n" in s else "\n"
out = []
for line in s.split(nl):
    mm = re.match(r"\| \*\*(IT-\d{3})\*\* \|", line)
    if mm and mm.group(1) in m:
        cells = line.split(" | ")
        v = m[mm.group(1)]
        if "tier" in v: cells[-3] = v["tier"]
        cells[-1] = v["status"] + " |"
        line = " | ".join(cells)
    out.append(line)
open(P, "w", encoding="utf-8", newline="").write(nl.join(out))
print("ok", len(m))
