import json, re, sys
plan = open(r"D:/ERX-001/docs/01-需求摸底/S06-译名与导航/R03-开发方案/P1-S6-R3-C开发方案-Part3.md", encoding="utf-8").read().splitlines()
rows = []
sec = None
for line in plan[87:139]:
    cells = [c.strip() for c in line.strip().strip("|").split("|")]
    if len(cells) != 4:
        continue
    s, lab, lt, to = [c.strip("`") for c in cells]
    if s:
        sec = s
        rows.append(("SB", s, None, None))
    rows.append(("L", lab, lt, to))
sb = json.load(open(r"D:/ERX-001/frappe-bench/apps/frappe_china/frappe_china/workspace_sidebar/business_flow.json", encoding="utf-8"))
items = sb["items"]
print("plan rows", len(rows), "json items", len(items))
print("links plan", sum(1 for r in rows if r[0] == "L"), "json", sum(1 for i in items if i["type"] == "Link"))
bad = 0
SBK = {"type": "Section Break", "link_type": "DocType", "child": 0, "indent": 1, "collapsible": 1, "keep_closed": 0}
LK = {"type": "Link", "child": 1, "indent": 0, "collapsible": 1, "keep_closed": 0}
for r, it in zip(rows, items):
    if r[0] == "SB":
        ok = it.get("label") == r[1] and all(it.get(k) == v for k, v in SBK.items())
        extra = set(it) - set(SBK) - {"label"}
    else:
        ok = it.get("label") == r[1] and it.get("link_type") == r[2] and all(it.get(k) == v for k, v in LK.items())
        if r[2] == "URL":
            ok = ok and it.get("url") == r[3] and "link_to" not in it
        else:
            ok = ok and it.get("link_to") == r[3] and "url" not in it
        extra = set(it) - set(LK) - {"label", "link_type", "link_to", "url", "icon"}
    if not ok or extra:
        bad += 1
        print("MISMATCH", r, it, extra)
print("mismatch", bad)
print("top keys", sorted(sb))
labels = [i["label"] for i in items if i["type"] == "Link"]
print("dup source labels", [l for l in set(labels) if labels.count(l) > 1])
