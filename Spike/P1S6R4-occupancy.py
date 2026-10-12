"""Check whether a candidate translation is already occupied in the merged dictionary (six official apps + frappe_china)."""
from __future__ import annotations
import importlib.util
import sys
from functools import lru_cache
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("baseline", Path(__file__).with_name("P1S6R4-baseline.py"))
baseline = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(baseline)


@lru_cache(maxsize=1)
def _merged():
    return baseline.merged_dict()


def occupants(target: str):
    """Context-free source strings whose merged translation (stripped) equals target."""
    merged, plain_keys = _merged()
    return sorted(key for key in plain_keys if key in merged and merged[key].strip() == target.strip())


def check(source: str, candidate: str, synonyms=frozenset()):
    found = [item for item in occupants(candidate) if item not in {source, *synonyms}]
    return not found, found


if __name__ == "__main__":
    source, candidate, *synonyms = sys.argv[1:]
    ok, found = check(source, candidate, set(synonyms))
    print({"source": source, "candidate": candidate, "usable": ok, "occupants": found})
