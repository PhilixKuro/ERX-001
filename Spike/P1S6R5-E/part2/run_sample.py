import importlib.util, csv, json, sys
from pathlib import Path
OUT = Path("D:/ERX-001/Spike/P1S6R5-E/part2")
spec = importlib.util.spec_from_file_location("smp", "D:/ERX-001/Spike/P1S6R4-sample.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
batch = m.population()
selected, quotas = m.stratified_sample(batch)
with (OUT/"sample.out.csv").open("w", encoding="utf-8-sig", newline="") as h:
    w = csv.writer(h, lineterminator="\n"); w.writerow(["app","键","出处","译文","判定","不可用原因"])
    for app,(key,refs,target) in selected: w.writerow([app,key,"; ".join(refs),target,"待审",""])
rep = {"seed": m.SEED, "rows": len(selected), "population": {a: len(r) for a,r in batch.items()}, "quotas": quotas}
(OUT/"sample-meta.json").write_text(json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(rep, ensure_ascii=False))
# review
spec2 = importlib.util.spec_from_file_location("rev", "D:/ERX-001/Spike/P1S6R4-sample-review.py")
r = importlib.util.module_from_spec(spec2); spec2.loader.exec_module(r)
r.SHEET = OUT/"sample.out.csv"; r.REPORT = OUT/"sample-review.json"
r.main()
