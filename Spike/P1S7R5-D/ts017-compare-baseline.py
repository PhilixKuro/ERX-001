"""Compare collected test identities to both earlier completed full runs."""
import json
import re
from pathlib import Path

logs = Path("/workspace/frappe-bench/logs")

def cases(path):
    current, result = None, set()
    clean = re.sub(r"\x1b\[[0-9;]*m", "", path.read_text(encoding="utf-8"))
    for line in clean.splitlines():
        if line.startswith("frappe_china.tests."):
            current = line.strip()
        match = re.search(r"✔\s+(test_\w+)", line)
        if match and current:
            result.add(current + "." + match[1])
    return result

actual = cases(logs / "s7-r5-ts017-full.log")
result = {}
for name in ("s7-r5-python-before.log", "s7-r5-part2-python-full.log"):
    baseline = cases(logs / name)
    result[name] = {"baseline": len(baseline), "actual": len(actual), "missing": sorted(baseline - actual), "added": len(actual - baseline)}
    assert baseline and not baseline - actual, result[name]
Path("/workspace/Spike/P1S7R5-D/ts017-baseline-comparison.json").write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(result, ensure_ascii=False))
