"""csv 带 context 的行：其无 context 源词有官方译文的条数，及译文与官方不同的条数（口径外覆盖）。"""
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import verify  # noqa: E402

b = verify.load("baseline", verify.PROJECT / "Spike/P1S6R4-baseline.py")
off = {}
for a in verify.OFFICIAL_APPS:
    off.update(verify.po_dict(b, a))
total = shadow = differ = 0
samples = []
with open(verify.TESTS.parent / "translations/zh.csv", encoding="utf-8", newline="") as handle:
    for row in csv.reader(handle):
        if len(row) == 3 and row[2]:
            total += 1
            if row[0] in off:
                shadow += 1
                if off[row[0]].strip() != row[1].strip():
                    differ += 1
                    if len(samples) < 8:
                        samples.append(f"{row[0]}:{row[2]} 官方={off[row[0]]} ours={row[1]}")
out = Path(__file__).with_name("ctx-out.txt")
out.write_text(f"context rows={total}; plain source has official={shadow}; differ={differ}\n" + "\n".join(samples) + "\n", encoding="utf-8")
