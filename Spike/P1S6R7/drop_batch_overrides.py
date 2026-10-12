"""A16：批量档（basis 以 DEC-038 开头）不覆盖官方。官方值即源词原样（官方有意保留英文）的键：
csv 删行回落官方、OVERRIDES 删条、键进 UNTRANSLATED 写理由。容器内 env/bin/python 跑；--write 才落盘。
另从待并入的 rows.csv 里剔除同类键（第 1 个参数，可省）。"""
import csv, sys
sys.path.insert(0, "/workspace/Spike/P1S6R7"); sys.argv_saved = list(sys.argv); sys.argv = ["x"]
import apply_rows as a
args = sys.argv_saved[1:]
write = "--write" in args
pending = [x for x in args if x != "--write"]
off = a.official_dict()
drop = {k for k, v in a.OVERRIDES.items() if v.basis.startswith("DEC-038") and off.get(k, "").strip() == k.split(":")[0].strip()}
other = {k: v for k, v in a.OVERRIDES.items() if v.basis.startswith("DEC-038") and k not in drop}
pend_drop = set()
if pending:
    for r in a.read_rows(pending[0]):
        k = a.key_of(r)
        if k in off and off[k].strip() == r[0].strip():
            pend_drop.add(k)
print({"merged_drop": sorted(drop), "pending_drop": sorted(pend_drop), "batch_overrides_other": {k: (v.official, v.ours) for k, v in other.items()}})
if not write:
    sys.exit(0)
rows = [r for r in a.read_rows(a.CSV_PATH) if a.key_of(r) not in drop]
with open(a.CSV_PATH, "w", encoding="utf-8", newline="") as h:
    csv.writer(h, lineterminator="\n").writerows(rows)
a.write_overrides({k: v for k, v in a.OVERRIDES.items() if k not in drop})
if pending:
    keep = [r for r in a.read_rows(pending[0]) if a.key_of(r) not in pend_drop]
    with open(pending[0], "w", encoding="utf-8", newline="") as h:
        csv.writer(h, lineterminator="\n").writerows(keep)
wl = "/workspace/frappe-bench/apps/frappe_china/frappe_china/tests/translation_whitelist.py"
text = open(wl, encoding="utf-8", newline="").read()
i = text.rindex("}")
reason = "官方词典有意保留原文；批量档不覆盖官方（R6 方案 A16）"
add = "".join(f"\t{k!r}: {reason!r},\r\n" for k in sorted(drop | pend_drop) if f"{k!r}:" not in text)
open(wl, "w", encoding="utf-8", newline="").write(text[:i] + add + text[i:])
print({"csv_total": len(rows), "whitelisted": len(drop | pend_drop)})
