"""P1-S6-R12 F 分片 5：独立抽检。宿主 `PYTHONUTF8=1 python -I Spike/P1S6R12-F/p5/sample_f.py`。

方法：种子 SEED=20261013（与 R7 的 20261011、R8 E 的 20261012 都不同）。
- 批量档总体：Spike/P1S6R6-batch/in-*.json 的全部 key，扣除 UNTRANSLATED 与 csv 中已不存在的键；
  按 app 分层，每 app 抽 10 条，共 60 条。
- 演示线档总体：Spike/P1S6R6-demo/in-*.json 的全部 key，同样扣除，简单随机抽 20 条。
译文取当前 zh.csv（HEAD d441e9f），附出处与 in 块里的上下文源码，供人工逐条判。
"""
from __future__ import annotations

import csv
import glob
import importlib.util
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SEED = 20261013
SPEC = importlib.util.spec_from_file_location("baseline", ROOT / "Spike/P1S6R4-baseline.py")
baseline = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(baseline)


def load(pattern):
	current = baseline.parse_csv(baseline.app_path("frappe_china") / "translations/zh.csv")
	white = {key.replace("\\n", "\n") for key in baseline.untranslated()}
	groups = {}
	for block in sorted(glob.glob(str(ROOT / pattern))):
		data = json.loads(Path(block).read_text(encoding="utf-8"))
		for item in data["items"]:
			key = item["key"].replace("\\n", "\n")
			if key in white or key not in current:
				continue
			groups.setdefault(data["group"], []).append(
				{"app": data["group"], "key": item["key"], "refs": item["refs"][:3], "target": current[key],
				 "context": item.get("context") or ""}
			)
	return groups


def main():
	rng = random.Random(SEED)
	batch = load("Spike/P1S6R6-batch/in-*.json")
	demo = load("Spike/P1S6R6-demo/in-*.json")
	picked = []
	for app in sorted(batch):
		rows = sorted(batch[app], key=lambda r: r["key"])
		picked += [dict(row, tier="batch") for row in rng.sample(rows, 10)]
	demo_rows = sorted((row for rows in demo.values() for row in rows), key=lambda r: r["key"])
	picked += [dict(row, tier="demo") for row in rng.sample(demo_rows, 20)]
	out = Path(__file__).with_name("sample_f.json")
	out.write_text(json.dumps(picked, ensure_ascii=False, indent=1), encoding="utf-8")
	print(json.dumps({"seed": SEED, "batch_population": {k: len(v) for k, v in batch.items()},
		"demo_population": len(demo_rows), "picked": len(picked)}, ensure_ascii=False))
	for i, row in enumerate(picked, 1):
		print(f"#{i} [{row['tier']}/{row['app']}] {row['key']!r}\n   => {row['target']!r}\n   @ {row['refs'][:2]}")


if __name__ == "__main__":
	main()
