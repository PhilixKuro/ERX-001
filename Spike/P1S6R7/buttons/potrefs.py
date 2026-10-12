"""List main.pot references (#: lines) for given msgids across apps."""
import sys, re
from pathlib import Path
APPS = Path(r"D:/ERX-001/frappe-bench/apps")
targets = set(sys.argv[1:])
for app in ["frappe", "erpnext", "hrms", "india_compliance", "crm", "helpdesk", "raven", "lms", "insights"]:
    pot = APPS / app / app / "locale/main.pot"
    if not pot.exists():
        continue
    refs, ctx = [], None
    for line in pot.read_text(encoding="utf-8").splitlines():
        if line.startswith("#: "):
            refs.extend(line[3:].split())
        elif line.startswith("msgctxt "):
            ctx = line[8:].strip('"')
        elif line.startswith("msgid "):
            mid = line[6:].strip()[1:-1]
            if mid in targets:
                print(f"[{app}] {mid!r} ctx={ctx} n={len(refs)} :: {' '.join(refs[:40])}")
            refs, ctx = [], None
