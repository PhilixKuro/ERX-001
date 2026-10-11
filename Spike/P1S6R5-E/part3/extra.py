import json, glob, os
n = json.load(open(r"D:/ERX-001/Spike/P1S6R4-nav-current-before.json", encoding="utf-8"))
a = json.load(open(r"D:/ERX-001/Spike/P1S6R4-migration-acceptance.json", encoding="utf-8"))["after"]
pn = {r["name"]: str(r["modified"]) for r in n["Workspace Sidebar"]}
pa = {r["name"]: str(r["modified"]) for r in a["Workspace Sidebar"]}
print("WS modified diff nav-before vs acc-after", [k for k in set(pn) | set(pa) if pn.get(k) != pa.get(k)])
print("fields in nav-before WS row", sorted(n["Workspace Sidebar"][0]), "WSI row", sorted(n["Workspace Sidebar Item"][0]))
# is_tree across sidebar DocTypes
sb = json.load(open(r"D:/ERX-001/frappe-bench/apps/frappe_china/frappe_china/workspace_sidebar/business_flow.json", encoding="utf-8"))
dts = [i["link_to"] for i in sb["items"] if i.get("link_type") == "DocType" and i["type"] == "Link"]
idx = {}
for p in glob.glob(r"D:/ERX-001/frappe-bench/apps/*/*/*/doctype/*/*.json"):
    if os.path.basename(os.path.dirname(p)) + ".json" != os.path.basename(p):
        continue
    try:
        d = json.load(open(p, encoding="utf-8"))
    except Exception:
        continue
    if isinstance(d, dict) and d.get("doctype") == "DocType":
        idx[d.get("name")] = d.get("is_tree", 0)
print("doctype count", len(dts), "missing", [d for d in dts if d not in idx])
print("is_tree", [d for d in dts if idx.get(d)])
