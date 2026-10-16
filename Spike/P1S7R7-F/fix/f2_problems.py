"""FD-019、FD-023：problems 改中文（总纲 §5.1「物料 X／仓库 Y：原因」），每日告警 log_error 参数位次。"""

import sys

sys.path.insert(0, r"D:\ERX-001\Spike\P1S7R7-F\fix")
from repl import apply

R = r"D:\ERX-001\frappe-bench\apps\frappe_china\frappe_china\replenishment"
apply(
	R + r"\safety_stock.py",
	[
		(
			'f"{item_code}: demand exists in another replenishment company"',
			'f"物料 {item_code}：另一家启用补货的公司也有出库，安全库存不计算"',
		),
		('f"{item_code}: lead time missing"', 'f"物料 {item_code}：提前期缺失，安全库存记 0"'),
		(
			'f"{item_code}: service level is outside (50, 100)"',
			'f"物料 {item_code}：服务水平不在 50～100 之间（不含两端）"',
		),
		('result["problems"].append(f"{item_code}: {error}")', 'result["problems"].append(f"物料 {item_code}：{error}")'),
	],
)
apply(
	R + r"\reorder_level.py",
	[
		('f"{item_code}: lead time missing"', 'f"物料 {item_code}／仓库 {row.get(\'warehouse_group\') or row.get(\'warehouse\')}：提前期缺失，再订货点不写"'),
		('result["problems"].append(f"{item_code}: {error}")', 'result["problems"].append(f"物料 {item_code}：{error}")'),
	],
)
apply(
	R + r"\rules.py",
	[
		('problems.append(f"{item}: missing EOQ parameter")', 'problems.append(f"物料 {item}／仓库 {row.warehouse}：EOQ 参数缺失（年需求、订货成本或持有成本）")'),
		('problems.append(f"{item}: missing periodic review parameter")', 'problems.append(f"物料 {item}／仓库 {row.warehouse}：定期复核参数缺失（盘点周期或起算日）")'),
		('problems.append(f"{item}: {error}")', 'problems.append(f"物料 {item}／仓库 {row.warehouse}：{error}")'),
		('problems.append(f"{row.item_code}: {error}")', 'problems.append(f"物料 {row.item_code}（销售订单 {row.sales_order}）：{error}")'),
		('problems.append(f"sales orders: {error}")', 'problems.append(f"按订单展开原料出错：{error}")'),
		(
			"problems.append(f\"{item or 'unknown'}: no default warehouse\")",
			"problems.append(f\"物料 {item or '（未知）'}：无默认仓库，不出建议\")",
		),
	],
)
apply(
	R + r"\daily.py",
	[
		('problems.append(f"{getattr(fn, \'__name__\', str(fn))}: {error}")', 'problems.append(f"{getattr(fn, \'__name__\', str(fn))} 出错：{error}")'),
		("problems.append(f\"{proposal.get('item_code')}: {error}\")", "problems.append(f\"物料 {proposal.get('item_code')}／仓库 {proposal.get('warehouse')}：建议单写入失败：{error}\")"),
		(
			'frappe.log_error(str(result), "Daily replenishment calculation has problems")',
			'frappe.log_error(title=frappe._(DAILY_ALERT_SOURCE, lang="zh"), message=frappe.as_json(result))',
		),
		(
			"from .types import DailyResult, StepResult\n",
			"from .types import DailyResult, StepResult\n\nDAILY_ALERT_SOURCE = \"Daily replenishment calculation has problems\"\n",
		),
	],
)
print("done")
