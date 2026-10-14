import sys
sys.path.insert(0, ".")
from merged import per_app, ours, ROOT
cnt = {}
bad = []
for app, d in per_app.items():
    for k, v in d.items():
        if "工时表" in v:
            cnt[app] = cnt.get(app, 0) + 1
            exp = v.replace("工时表", "工时单")
            if ours.get(k) != exp:
                bad.append((app, k, v, ours.get(k)))
print("count", cnt, "bad", bad)
for app in per_app:
    p = ROOT / app / app / "locale" / "zh.po"
    if p.exists():
        t = p.read_text(encoding="utf-8")
        print(app, "plural entries", t.count("msgid_plural"))
print("csv rows with 工时表:", sum(1 for v in ours.values() if "工时表" in v))
