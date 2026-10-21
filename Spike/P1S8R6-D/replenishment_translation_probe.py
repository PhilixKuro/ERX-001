"""Read-only TS-008 basis collision inventory; no site/database access."""
import csv
import json
import re
from pathlib import Path

root = Path("/workspace/frappe-bench/apps")
doc = json.loads((root / "frappe_china/frappe_china/stock_plus/doctype/replenishment_basis_item/replenishment_basis_item.json").read_text())
options = next(field["options"] for field in doc["fields"] if field["fieldname"] == "basis").splitlines()
official = {}
for app in ("frappe", "erpnext", "crm", "hrms", "insights", "raven"):
    path = root / app / app / "locale/zh.po"
    if not path.exists():
        continue
    for block in path.read_text(encoding="utf-8").split("\n\n"):
        source = re.search(r'^msgid (".*")$', block, re.M)
        target = re.search(r'^msgstr (".*")$', block, re.M)
        if source and target and "msgctxt " not in block:
            key, value = json.loads(source[1]), json.loads(target[1])
            if value:
                official[key] = value
    path = root / app / app / "translations/zh.csv"
    if path.exists():
        with path.open(encoding="utf-8", newline="") as handle:
            official.update({row[0]: row[1] for row in csv.reader(handle) if len(row) == 2})
with (root / "frappe_china/frappe_china/translations/zh.csv").open(encoding="utf-8", newline="") as handle:
    ours = {row[0]: row[1] for row in csv.reader(handle) if len(row) == 2}
print(json.dumps([{"source": key, "official": official.get(key), "app": ours.get(key)} for key in options], ensure_ascii=False, indent=2))
