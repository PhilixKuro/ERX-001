import importlib.util, collections, json, csv
spec = importlib.util.spec_from_file_location("ov", "D:/ERX-001/frappe-bench/apps/frappe_china/frappe_china/tests/translation_overrides.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
O = m.OVERRIDES
o = open("ov.txt","w",encoding="utf-8")
o.write(f"OVERRIDES {len(O)}\n")
c = collections.Counter(v.basis for v in O.values())
for b,n in c.most_common(): o.write(f"  {n}\t{b}\n")
bad = [(k,v.ours) for k,v in O.items() if "中文：" in v.ours or "???" in v.ours]
o.write(f"ours with 中文：/??? {len(bad)}\n")
for k,v in bad[:15]: o.write(f"   {k!r} -> {v!r}\n")
d = json.load(open("baseline.out.json",encoding="utf-8"))
ov_keys = {x["key"] for x in d["official_overrides"]}
o.write(f"csv∩official {len(ov_keys)}; missing from OVERRIDES {sorted(ov_keys-set(O))[:20]}\n")
for k in ["Timesheet","Timesheets","Dr","Setup","Item","Payment References","Hold","Delivery Note"]:
    o.write(f"{k}: {O.get(k)}\n")
# csv rows with 中文： or ???
rows = list(csv.reader(open("D:/ERX-001/frappe-bench/apps/frappe_china/frappe_china/translations/zh.csv",encoding="utf-8")))
ph = [r for r in rows if len(r)>=2 and ("中文：" in r[1] or "???" in r[1])]
o.write(f"csv rows with 中文：/??? : {len(ph)}\n")
for r in ph[:10]: o.write(f"   {r}\n")
