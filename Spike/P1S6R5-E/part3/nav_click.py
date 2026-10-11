import json
d = json.load(open(r"D:/ERX-001/Spike/P1S6R4-nav-click.out.json", encoding="utf-8"))
r = d["results"]
print("results", len(r), "pass", sum(1 for x in r if x.get("pass")), "passed field", d["passed"])
print("sections", d["sections"])
print("home first", d["home"][0]["text"] if d["home"] else None, "home count", len(d["home"]))
print("undefined_requests", d["undefined_requests"])
labels = [x["label"] for x in r]
print("dup labels", [l for l in set(labels) if labels.count(l) > 1])
for x in r:
    p = x.get("page", {})
    print(x["pass"], "|", x["label"], "|", x["href"], "|", x["target"], "|", p.get("url"), "|", p.get("route"), "|", p.get("title"), "|", p.get("sidebar"), "|", "trees", p.get("trees"), "rec", p.get("records"), {k: v for k, v in p.items() if k not in ("url", "route", "title", "sidebar", "trees", "records", "text")})
print("keys of one result", sorted(r[0]))
print("boot keys", sorted(d["boot"]))
