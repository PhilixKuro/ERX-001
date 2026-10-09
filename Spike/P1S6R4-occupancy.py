"""Check whether a candidate translation is already occupied."""
from __future__ import annotations
import csv, sys
from pathlib import Path

CSV_PATH = Path(__file__).resolve().parents[1] / "frappe-bench/apps/frappe_china/frappe_china/translations/zh.csv"

def occupants(target: str):
    result = []
    with CSV_PATH.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.reader(handle):
            if len(row) >= 2 and row[1].strip() == target.strip() and (len(row) == 2 or not row[2]):
                result.append(row[0])
    return sorted(set(result))

def check(source: str, candidate: str, synonyms=frozenset()):
    found = [item for item in occupants(candidate) if item not in {source, *synonyms}]
    return not found, found

if __name__ == "__main__":
    source, candidate, *synonyms = sys.argv[1:]
    ok, found = check(source, candidate, set(synonyms))
    print({"source": source, "candidate": candidate, "usable": ok, "occupants": found})
