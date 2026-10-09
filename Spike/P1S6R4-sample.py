"""Reproduce the 100-row review of newly filled, non-demo S6 gaps."""
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
SEED = 20261009
SPEC = importlib.util.spec_from_file_location("baseline", ROOT / "Spike/P1S6R4-baseline.py")
baseline = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(baseline)

def population():
    frozen = json.loads((ROOT / "Spike/P1S6R4-baseline.out.json").read_text(encoding="utf-8"))
    app_repo = ROOT / "frappe-bench/apps/frappe_china"
    original = subprocess.run(
        ["git", "-C", str(app_repo), "show", frozen["commits"]["frappe_china"] + ":frappe_china/translations/zh.csv"],
        check=True, capture_output=True, encoding="utf-8",
    ).stdout
    before = {}
    for app in baseline.APPS[:-1]:
        before.update(baseline.parse_csv(baseline.app_path(app) / "translations/zh.csv"))
        for entry in baseline.parse_po(baseline.app_path(app) / "locale/zh.po"):
            if entry["str"]:
                before[baseline.entry_key(entry)] = entry["str"]
    for row in csv.reader(io.StringIO(original)):
        key = row[0] + (":" + row[2] if len(row) == 3 and row[2] else "")
        before[key] = row[1]
    current = {}
    with (baseline.app_path("frappe_china") / "translations/zh.csv").open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.reader(handle):
            if len(row) in (2, 3):
                key = row[0] + (":" + row[2] if len(row) == 3 and row[2] else "")
                current[key] = row[1].strip()
    result = {}
    for app in baseline.APPS[:-1]:
        rows = {}
        for entry in baseline.parse_po(baseline.app_path(app) / "locale/main.pot"):
            key = baseline.entry_key(entry)
            old = before.get(key) or before.get(entry["id"])
            target = current.get(key) or current.get(entry["id"])
            if entry["id"] in frozen["demo_surface"] or not target:
                continue
            if old and old != entry["id"]:
                continue
            refs = [f"frappe-bench/apps/{app}/{ref}" for ref in entry["refs"]]
            rows[key] = (key, refs, target)
        result[app] = [rows[key] for key in sorted(rows)]
    return result

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
    parser.add_argument("--out", type=Path, default=ROOT / "Spike/P1S6R4-sample.out.csv")
    args = parser.parse_args()
    batch = population()
    selected, quotas = stratified_sample(batch)
    with args.out.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["app", "键", "出处", "译文", "判定", "不可用原因"])
        for app, (key, refs, target) in selected:
            writer.writerow([app, key, "; ".join(refs), target, "待审", ""])
    report = {"seed": SEED, "rows": len(selected), "population": {app: len(rows) for app, rows in batch.items()}, "quotas": quotas}
    (ROOT / "Spike/P1S6R4-sample-meta.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))

if __name__ == "__main__":
    main()
