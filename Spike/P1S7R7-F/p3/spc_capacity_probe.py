"""F 片3 探针：test.localhost 只读。纯计算手算一例、负荷报表三种桶与工作中心筛选 SQL 可执行、残留查询。
不写任何记录；末尾 rollback。"""
import json
import math

import frappe

assert frappe.local.site == "test.localhost"
frappe.local.lang = "zh"
from frappe_china.production.spc import compute, load_subgroups, nelson

out = {}
# 手算例（报告里逐式列出）：n=2、3、4 各一组 + n=1 一组，只有上限 12
groups = [
	{"inspection": "a", "date": "2026-10-01", "values": [1, 3]},
	{"inspection": "b", "date": "2026-10-01", "values": [2, 4, 6]},
	{"inspection": "c", "date": "2026-10-01", "values": [3, 5, 7, 9]},
	{"inspection": "d", "date": "2026-10-01", "values": [5]},
]
r = compute(groups, 12, None)
out["hand"] = {k: r[k] for k in ("grand_mean", "r_bar", "sigma_within", "sigma_overall", "cpk", "ppk", "readings", "insufficient", "signals")}
out["hand_z"] = [g["z"] for g in r["subgroups"]]
out["hand_notes"] = r["notes"]
# 两侧限都无
out["no_limits"] = {k: compute(groups, None, None)[k] for k in ("cpk", "ppk", "notes")}
# Nelson 8：全在同侧 8 点 |z|>1（经典定义要求两侧都有，本实现按方案「两侧均可」）
out["rule8_same_side"] = nelson([1.5] * 8)[-1]
# 规则 4 含零差值
out["rule4_with_flat"] = nelson([0.5, -0.5] * 6 + [-0.5, 0.5])[-1]
# 工作中心筛选 SQL 可执行（库里无该工作中心，应得空）
out["ws_filter"] = load_subgroups({"item_code": "_FCT_F_NONE", "specification": "_FCT_F_NONE", "workstation": "_FCT_F_NONE"})
# 负荷报表：日、月桶真跑 execute（只读，直接调 execute 不经 desk 定时器）
from frappe_china.production_plus.report.capacity_load.capacity_load import execute

company = frappe.db.get_value("Company", {}, "name")
for bucket in ("Day", "Week", "Month"):
	cols, rows, _m, chart = execute({"company": company, "from_date": "2026-10-30", "to_date": "2026-11-02", "bucket": bucket, "workstations": "[]"})
	out[f"exec_{bucket}"] = {"rows": len(rows), "labels": chart["data"]["labels"]}
out["company_used"] = company
out["labels_zh"] = [c["label"] for c in cols]
# 残留：D 的 TS-016 浏览器 fixture 前缀
out["residue_spc"] = frappe.db.sql("select count(*) from `tabQuality Inspection` where name like '\\_FCT SPC%%'")[0][0]
out["residue_items"] = frappe.db.sql("select count(*) from tabItem where name like '\\_FCT SPC%%'")[0][0]
out["prepared_flags"] = frappe.db.sql("select name, prepared_report from tabReport where name in ('Capacity Load','SPC Control Chart')")
out["alert_title_zh"] = frappe._("frappe_china override self-check failed")
frappe.db.rollback()
print(json.dumps(out, ensure_ascii=False, default=str, indent=1))
