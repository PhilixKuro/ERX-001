"""S6 分层抽检 100 条（R6 方案 TS-021 第 5 步改：种子 20261011，总体取 R6 批量档 Spike/P1S6R6-batch/part-*.csv 的行，译文取当前 zh.csv）。"""
from __future__ import annotations
import argparse
import csv
import importlib.util
import io
import json
import random
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEED = 20261011
SPEC = importlib.util.spec_from_file_location("baseline", ROOT / "Spike/P1S6R4-baseline.py")
baseline = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(baseline)

def population():
    """总体：批量档各块并入 zh.csv 的行，按 in 块的 app 分层；出处取 in 块的 refs。"""
    current = baseline.parse_csv(baseline.app_path("frappe_china") / "translations/zh.csv")
    whitelist = {key.replace("\\n", "\n") for key in baseline.untranslated()}
    result = {}
    for block in sorted((ROOT / "Spike/P1S6R6-batch").glob("in-*.json")):
        data = json.loads(block.read_text(encoding="utf-8"))
        part = block.with_name(block.name.replace("in-", "part-")).with_suffix(".csv")
        if not part.exists():
            raise ValueError(f"batch block not translated yet: {part.name}")
        for item in data["items"]:
            key = item["key"].replace("\\n", "\n")  # 与 Frappe 读 csv 同
            if key in whitelist:
                continue  # 进了白名单（品牌名、标识符、官方保留原文）的不在总体内
            target = current.get(key)
            if target is None:
                raise ValueError(f"batch key not in zh.csv: {item['key']!r}")
            result.setdefault(data["group"], []).append((item["key"], item["refs"], target))
    return {app: sorted(rows) for app, rows in result.items()}

def stratified_sample(batch, n=100, floor=5):
    apps = sorted(batch)
    if any(len(batch[app]) < floor for app in apps):
        raise ValueError("Each app needs at least five batch rows")
    total = sum(len(batch[app]) for app in apps)
    ideals = {app: max(floor, n * len(batch[app]) / total) for app in apps}
    quotas = {app: int(ideals[app]) for app in apps}
    while sum(quotas.values()) != n:
        if sum(quotas.values()) < n:
            app = max(apps, key=lambda name: (ideals[name] - quotas[name], name))
            quotas[app] += 1
        else:
            app = max((name for name in apps if quotas[name] > floor), key=lambda name: (quotas[name] - ideals[name], name))
            quotas[app] -= 1
    rng = random.Random(SEED)
    selected = [(app, row) for app in apps for row in rng.sample(batch[app], quotas[app])]
    assert len(selected) == n
    return selected, quotas

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=ROOT / "Spike/P1S6R6-sample.out.csv")
    args = parser.parse_args()
    batch = population()
    selected, quotas = stratified_sample(batch)
    with args.out.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["app", "键", "出处", "译文", "判定", "不可用原因"])
        for app, (key, refs, target) in selected:
            writer.writerow([app, key, "; ".join(refs), target, "待审", ""])
    report = {"seed": SEED, "rows": len(selected), "population": {app: len(rows) for app, rows in batch.items()}, "quotas": quotas}
    (ROOT / "Spike/P1S6R6-sample-meta.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))

if __name__ == "__main__":
    main()
