import csv
from pathlib import Path

path = Path('/workspace/frappe-bench/apps/frappe_china/frappe_china/translations/zh.csv')
with path.open(encoding='utf-8', newline='') as source:
    rows = list(csv.reader(source))
rows.sort(key=lambda row: ((row[0] if row else '').casefold(), row[2] if len(row) > 2 else ''))
with path.open('w', encoding='utf-8', newline='') as target:
    csv.writer(target, lineterminator='\n').writerows(rows)
