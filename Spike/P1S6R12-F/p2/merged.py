import ast, csv, sys
from pathlib import Path
ROOT = Path("D:/ERX-001/frappe-bench/apps")
APPS = ["frappe", "erpnext", "crm", "hrms", "insights", "raven"]
def po(path):
    out = {}
    msgid = ctx = msgstr = None; field = None
    for line in [*path.read_text(encoding="utf-8-sig").splitlines(), ""]:
        if not line.strip():
            if msgid and msgstr:
                out[msgid + ((":" + ctx) if ctx else "")] = msgstr
            msgid = ctx = msgstr = None; field = None
        elif line.startswith("#"):
            continue
        elif line.startswith("msgctxt "): ctx = ast.literal_eval(line[8:]); field = "c"
        elif line.startswith("msgid "): msgid = ast.literal_eval(line[6:]); field = "i"
        elif line.startswith("msgstr "): msgstr = ast.literal_eval(line[7:]); field = "s"
        elif line.startswith('"') and field:
            v = ast.literal_eval(line)
            if field == "i": msgid += v
            elif field == "c": ctx += v
            else: msgstr += v
    return out
official = {}
per_app = {}
for a in APPS:
    p = ROOT / a / a / "locale" / "zh.po"
    d = po(p) if p.exists() else {}
    per_app[a] = d
    official.update(d)
ours = {}
with open(ROOT / "frappe_china/frappe_china/translations/zh.csv", encoding="utf-8", newline="") as f:
    for row in csv.reader(f):
        if len(row) == 3 and row[2]: ours[row[0] + ":" + row[2]] = row[1].strip()
        elif len(row) in (2, 3): ours[row[0]] = row[1].strip()
merged = dict(official); merged.update(ours)
if __name__ == "__main__":
    for k in sys.argv[1:]:
        print(repr(k), "official=", repr(official.get(k)), "csv=", repr(ours.get(k)), "merged=", repr(merged.get(k)))
