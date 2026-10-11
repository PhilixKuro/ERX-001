import json
d = json.load(open(r"D:/ERX-001/Spike/P1S6R4-migration-acceptance.json", encoding="utf-8"))
b, a = d["before"], d["after"]
print("keys before", sorted(b), "after", sorted(a))
for key in ("Desktop Icon", "Workspace Sidebar", "Workspace Sidebar Item"):
    proj = lambda rows: {r["name"]: (str(r.get("modified")), r.get("hidden"), r.get("idx")) for r in rows}
    pb, pa = proj(b[key]), proj(a[key])
    diff = [(n, pb.get(n), pa.get(n)) for n in sorted(set(pb) | set(pa)) if pb.get(n) != pa.get(n)]
    full = sum(1 for x, y in zip(b[key], a[key]) if x != y) + abs(len(b[key]) - len(a[key]))
    print(key, "rows", len(b[key]), len(a[key]), "proj diff", len(diff), "full-row diff", full, diff[:5])
print("CN Tax equal", b["CN Tax"] == a["CN Tax"], b["CN Tax"]["modified"], a["CN Tax"]["modified"])
print("own modified", b["own"]["modified"], a["own"]["modified"], "label1", b["own"]["items"][1]["label"], a["own"]["items"][1]["label"])
print("own module", a["own"]["module"], "own standard", a["own"]["standard"], "icon", {k: a["icon"][k] for k in ("app", "idx", "hidden", "standard", "label", "modified")})

n = json.load(open(r"D:/ERX-001/Spike/P1S6R4-nav-current-before.json", encoding="utf-8"))
for key in ("Desktop Icon", "Workspace Sidebar", "Workspace Sidebar Item"):
    pn = {r["name"]: (str(r.get("modified")), r.get("hidden"), r.get("idx")) for r in n[key]}
    pa = {r["name"]: (str(r.get("modified")), r.get("hidden"), r.get("idx")) for r in a[key]}
    diff = [(x, pn.get(x), pa.get(x)) for x in sorted(set(pn) | set(pa)) if pn.get(x) != pa.get(x)]
    print("nav-current-before vs acceptance-after", key, len(pn), len(pa), "diff", len(diff), diff[:3])
print("nav-before CN Tax", n["CN Tax"], "BF icon", n["Business Flow icon"], "now", n["now"])
