import json
d = json.load(open("baseline.out.json", encoding="utf-8"))
print("gap_counts", d["gap_counts"]); print("identity", d["identity_gap_counts"])
surf = set(d["demo_surface"])
for app, items in d["gaps"].items():
    for key, refs in items:
        base = key.split(":")[0] if False else key
        tag = "DEMO" if key in surf or key.rsplit(":",1)[0] in surf else "    "
        print(app, tag, repr(key)[:140], refs[:2])
dc = d["demo_collisions"]
print("demo_collisions", len(dc))
json.dump(dc, open("demo_collisions.json","w",encoding="utf-8"), ensure_ascii=False, indent=1)
