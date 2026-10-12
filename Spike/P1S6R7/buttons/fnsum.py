"""Print def line and key side-effect lines (insert/submit/save/db_set/set_status/delete/cancel/return) of given file:line python functions."""
import re, sys
from pathlib import Path
APPS = Path(r"D:/ERX-001/frappe-bench/apps")
KEY = re.compile(r"\.insert\(|\.submit\(|\.save\(|db_set|set_status|update_status|\.cancel\(|delete_doc|frappe\.db\.set_value|get_mapped_doc|^\s*return\b|make_|create_|\.flags\.|status\s*=")
for spec in sys.argv[1:]:
    f, ln = spec.rsplit(":", 1)
    lines = (APPS / f).read_text(encoding="utf-8").splitlines()
    i = int(ln) - 1
    indent = len(lines[i]) - len(lines[i].lstrip())
    print(f"=== {f}:{ln}  {lines[i].strip()}")
    j = i + 1
    while j < len(lines):
        s = lines[j]
        if s.strip() and (len(s) - len(s.lstrip())) <= indent and not s.strip().startswith((")", "]", "}", "#")):
            break
        if KEY.search(s):
            print(f"  {j+1}: {s.strip()[:150]}")
        j += 1
