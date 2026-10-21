"""Prepare TS-007 metadata offline; do not import Frappe or connect to a site."""
import csv
import json
from datetime import datetime
from pathlib import Path

root = Path(__file__).parent / "bom-confirmation-draft"
fields_path = root / "custom_field.json"
fields = json.loads(fields_path.read_text(encoding="utf-8"))
modified = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
for doctype, anchor in (("Production Plan Item", "cn_recommended_bom"), ("Work Order", "bom_no")):
    name = f"{doctype}-cn_bom_source"
    assert not any(field["name"] == name for field in fields)
    fields.append({
        "doctype": "Custom Field", "dt": doctype, "fieldname": "cn_bom_source",
        "fieldtype": "Select", "options": "\nconfirmed\nkept\nmanual",
        "insert_after": anchor, "label": "BOM Choice Source", "read_only": 1,
        "hidden": 1, "modified": modified, "name": name,
    })
fields_path.write_text(json.dumps(fields, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

translations_path = root / "zh.csv"
with translations_path.open(encoding="utf-8", newline="") as handle:
    rows = list(csv.reader(handle))
new = {
    "BOM Choice Source": "物料清单选择来源",
    "Confirm BOM recommendation": "确认物料清单推荐",
    "Use recommended BOM": "换用推荐",
    "Keep current BOM": "保留当前",
    "Recommended BOM: {0}": "推荐物料清单：{0}",
    "Inherited from production plan": "由生产计划带入",
    "Cost recommendation confirmed": "按成本推荐、人已确认",
    "Cost recommendation kept current": "按成本推荐、人选择保留",
    "BOM manually specified": "人工指定",
    "Selected automatically by cost": "按成本自动选用",
}
assert not new.keys() & {row[0] for row in rows if len(row) == 2}
rows.extend(new.items())
rows.sort(key=lambda row: (row[0].casefold(), row[2] if len(row) > 2 else ""))
with translations_path.open("w", encoding="utf-8", newline="") as handle:
    csv.writer(handle).writerows(rows)
print(json.dumps({"source_fields": 2, "new_translations": len(new)}, ensure_ascii=False))
