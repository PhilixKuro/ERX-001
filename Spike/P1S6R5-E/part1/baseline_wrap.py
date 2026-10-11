# E-step wrapper: reuse P1S6R4-baseline.py, skip commit-lock check, optionally swap frappe_china csv.
import importlib.util, json, sys, subprocess
from pathlib import Path
spec = importlib.util.spec_from_file_location("bl", "D:/ERX-001/Spike/P1S6R4-baseline.py")
bl = importlib.util.module_from_spec(spec); spec.loader.exec_module(bl)
csv_override = Path(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1] != "-" else None
out = Path(sys.argv[2])
real_app_path = bl.app_path
def app_path(app, _csv=False):
    return real_app_path(app)
if csv_override:
    orig_parse_csv = bl.parse_csv
    real_csv = real_app_path("frappe_china") / "translations/zh.csv"
    def parse_csv(path):
        return orig_parse_csv(csv_override if Path(path) == real_csv else path)
    bl.parse_csv = parse_csv
    orig_open = Path.open
    def popen(self, *a, **k):
        return orig_open(csv_override if self == real_csv else self, *a, **k)
    Path.open = popen
heads = {a: subprocess.run(["git","-C",str(bl.ROOT/"apps"/a),"rev-parse","HEAD"],capture_output=True,text=True).stdout.strip() for a in bl.APPS}
merged, plain = bl.merged_dict()
missing, ident = bl.gaps(merged)
coll = bl.collisions(merged, plain)
surface, scope, mdt, orig_missing = bl.demo_surface(bl.doctypes(), merged)
demo = {t: s for t, s in coll.items() if sum(x in surface for x in s) >= 2}
ov = bl.official_overrides()
res = {"heads": heads, "csv": str(csv_override), "gap_counts": {a: len(v) for a, v in missing.items()},
       "gap_total": sum(len(v) for v in missing.values()), "identity": ident, "identity_total": sum(ident.values()),
       "collision_count": len(coll), "demo_collisions": len(demo), "demo_surface_count": len(surface),
       "official_overrides": [o["key"] for o in ov][:20], "official_override_count": len(ov), "lg009": mdt}
out.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(res, ensure_ascii=False))
