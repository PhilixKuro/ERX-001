# R13 F p2: compare EXPECTED_LINKS (test) vs plan table (R3 Part3 TS-010 step 2) vs sidebar json
import ast, json, re, sys
root = sys.argv[1]
t = open(root + "/frappe-bench/apps/frappe_china/frappe_china/tests/test_business_flow_navigation.py", encoding="utf-8").read()
m = re.search(r"EXPECTED_LINKS = (\[.*?\n\])", t, re.S)
exp = ast.literal_eval(m.group(1))
plan = []; sec = None; plan_secs = []
row = re.compile(r"\s*\|\s*(`[^`]*`)?\s*\|\s*`([^`]+)`\s*\|\s*(DocType|Report|URL)\s*\|\s*`([^`]+)`\s*\|")
for line in open(root + "/docs/01-需求摸底/S06-译名与导航/R03-开发方案/P1-S6-R3-C开发方案-Part3.md", encoding="utf-8"):
    mm = row.match(line)
    if mm:
        if mm.group(1):
            sec = mm.group(1).strip("`"); plan_secs.append(sec)
        plan.append((mm.group(2), mm.group(3), mm.group(4), sec))
d = json.load(open(root + "/frappe-bench/apps/frappe_china/frappe_china/workspace_sidebar/business_flow.json", encoding="utf-8"))
js = []; sec = None; js_secs = []
for it in d["items"]:
    if it["type"] == "Section Break":
        sec = it["label"]; js_secs.append(sec)
    elif it["type"] == "Link":
        js.append((it["label"], it["link_type"], it.get("link_to") or it.get("url"), sec))
print("exp", len(exp), "plan", len(plan), "json", len(js))
print("exp==plan(3col)", exp == [p[:3] for p in plan])
print("exp==json(3col)", exp == [j[:3] for j in js])
print("plan==json(with section)", plan == js)
print("plan sections", plan_secs)
print("json sections", js_secs)
