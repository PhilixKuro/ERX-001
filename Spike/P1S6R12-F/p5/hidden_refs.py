"""覆盖键在源码里的出处 vs main.pot `#:` 出处：列出 main.pot 没记的源码出处（多因跨 app 去重）。python -I -X utf8"""
import json, importlib.util
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location("b", ROOT / "Spike/P1S6R4-baseline.py"); b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b)
refs = json.loads(Path(__file__).with_name("audit_tables.json").read_text(encoding="utf-8"))["override_refs"]
pot = {}
for app in ("frappe", "erpnext", "crm", "hrms", "insights", "raven"):
    for e in b.parse_po(b.app_path(app) / "locale/main.pot"):
        if not e["context"]:
            pot.setdefault(e["id"], set()).update(r.split(":")[0] for r in e["refs"])
for key, hits in refs.items():
    potfiles = pot.get(key, set())
    hidden = []
    for h in hits:
        path = h.rsplit(":", 2)[0]
        rel = path.split("/", 1)[1] if "/" in path else path
        if not any(rel.endswith(p) or p.endswith(rel) for p in potfiles):
            hidden.append(h)
    if hidden:
        print(key, "| pot:", sorted(potfiles)[:3], "| hidden:", hidden[:6])
