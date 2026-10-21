import csv
from pathlib import Path

path = Path('frappe-bench/apps/frappe_china/frappe_china/translations/zh.csv')
with path.open(encoding='utf-8', newline='') as source:
    rows = list(csv.reader(source))
additions = [
    ['Replenishment Strategy Comparison', '补货策略对比'],
    ['SPC Chart', '过程控制图'],
    ['Comparison Period', '时间段'], ['Comparison Days', '天数'],
    ['Average Inventory Value', '平均库存金额'], ['Purchase Order Count', '采购次数'],
    ['Inventory Related Total Cost', '库存相关总成本'], ['Shortage Count', '缺料次数'],
    ['From', '起', 'Replenishment Strategy Comparison'], ['To', '止', 'Replenishment Strategy Comparison'],
    ['Period {0}', '第 {0} 段'],
    ['Select two or three complete, non-overlapping comparison periods', '请选择两个或三个完整且互不重叠的对比时间段'],
    ['Invalid comparison period dates', '对比时间段日期无效'],
    ['Company {0}: set Order Cost and Holding Rate above zero; total costs are unavailable', '公司 {0}：请将单次订货成本和年持有成本率设为大于零，暂无法计算总成本'],
]
for number in (1, 2, 3):
    additions.extend([[f'Period {number} From', f'第 {number} 段起始日期'], [f'Period {number} To', f'第 {number} 段截止日期']])
keys = {(row[0], row[2] if len(row) > 2 else '') for row in rows}
rows = [row for row in rows if row[0] != 'Company {0} does not exist']
for row in additions:
    key = (row[0], row[2] if len(row) > 2 else '')
    if key not in keys:
        rows.append(row)
rows.sort(key=lambda row: (row[0].casefold(), row[2] if len(row) > 2 else ''))
with path.open('w', encoding='utf-8', newline='') as target:
    csv.writer(target, lineterminator='\n').writerows(rows)
print(f'Checked {len(additions)} strategy report translations')
