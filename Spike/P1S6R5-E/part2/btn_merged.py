import importlib.util
spec = importlib.util.spec_from_file_location("bl", "D:/ERX-001/Spike/P1S6R4-baseline.py")
bl = importlib.util.module_from_spec(spec); spec.loader.exec_module(bl)
merged,_ = bl.merged_dict()
import csv
rows = list(csv.reader(open("D:/ERX-001/Spike/P1S6R4-buttons.csv", encoding="utf-8-sig")))[1:]
o = open("D:/ERX-001/Spike/P1S6R5-E/part2/btn_merged.txt","w",encoding="utf-8")
for r in rows: o.write(f"{r[0]} | merged={merged.get(r[0])!r} | 定稿={r[6]!r}\n")
