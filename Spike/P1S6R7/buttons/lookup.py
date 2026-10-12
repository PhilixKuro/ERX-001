"""Print merged-dict translation for each source word given on argv (or all labels in raw_calls.json)."""
import importlib.util, json, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("baseline", HERE.parents[1] / "P1S6R4-baseline.py")
baseline = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(baseline)
merged, plain = baseline.merged_dict()
words = sys.argv[1:]
if not words:
    seen = []
    for r in json.loads((HERE / "raw_calls.json").read_text(encoding="utf-8")):
        for src, ctx in r["labels"]:
            k = f"{src}:{ctx}" if ctx else src
            if k not in seen: seen.append(k)
    words = seen + ["Save", "Submit", "Update", "Cancel", "Amend", "Delete", "Inter Company Invoice", "Inter Company Order", "Inter Company Purchase Receipt", "Inter Company Sales Order", "Inter Company Purchase Order", "Inter Company Purchase Invoice", "Inter Company Sales Invoice", "Payment Entry"]
for w in words:
    ctxkeys = sorted(k for k in merged if k.startswith(w + ":") and ":" not in k[len(w)+1:][:0] )
    ctxkeys = [k for k in merged if k.split(":")[0] == w and k != w and len(k) > len(w) and k[len(w)] == ":"]
    print(f"{w}\t{merged.get(w, '<无>')}\t{'plain' if w in plain else '-'}\t{ {k: merged[k] for k in ctxkeys} if ctxkeys else ''}")
