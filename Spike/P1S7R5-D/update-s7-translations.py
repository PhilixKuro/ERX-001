"""Add only keys absent from official dictionaries; keep existing decisions intact."""
import csv
from pathlib import Path

import frappe
from frappe_china.install import _app_translations

ADDITIONS = {
    "Piece Rate Summary": "计件汇总单", "Piece Rate Summary Item": "计件汇总明细",
    "Piece Rate Entries": "计件明细", "Piece Rate Source": "计件单价来源", "No Piece Rate": "无计件单价",
    "BOM Operation": "物料清单工序", "Piece Rate": "计件单价", "Log Date": "报工日期",
    "HRMS is required for piece rate payroll": "计件工资需要安装人事薪酬应用",
    "Cannot map piece rate operation for Job Card {0}": "无法匹配生产任务单 {0} 的计件工序",
    "Piece rate period must be a complete calendar month": "计件期间须为同一自然月的月初至月末",
    "Employee must belong to the selected company": "员工须属于所选公司",
    "A submitted piece rate summary already exists for this employee and period": "该员工本期间已有已提交的计件汇总单",
    "No piece rate earnings for this period": "本期间无计件金额",
    "Employee {0}: existing summary {1}": "员工 {0}：已有汇总单 {1}", "Employee {0}: {1}": "员工 {0}：{1}",
    "Generate Monthly Piece Rate": "按月生成计件汇总", "Created": "已创建",
    "Calculation date cannot be later than today": "计算日期不能晚于今天",
    "Capacity Load": "产能负荷", "Time Bucket": "时间桶", "Demand Hours": "需求工时",
    "Capacity Hours": "产能工时", "Capacity Load Percent": "产能负荷率", "No Capacity": "无产能",
    "Unscheduled Job Cards": "未排期", "Company, From Date and To Date are required": "须填写公司、开始日期和结束日期",
    "From Date cannot be after To Date": "开始日期不能晚于结束日期",
    "Capacity bucket must be Day, Week or Month": "产能时间桶须为日、周或月",
    "SPC Control Chart": "过程统计控制图", "Inspection Parameter": "检验参数",
    "Subgroup Size": "子组大小", "Subgroup Mean": "子组均值", "Subgroup Range": "子组极差",
    "Triggered Rules": "触发规则", "Subgroups": "子组数", "SPC Readings": "统计读数数",
    "Rejected Readings": "剔除读数数", "Signal Points": "判异点数", "Subgroup Number": "子组序号",
    "Insufficient samples; for reference only": "样本不足、仅供参考", "Open SPC Chart": "打开控制图",
    "Select an item and inspection parameter": "请选择物料和检验参数", "Unable to load SPC chart": "控制图加载失败",
    "Item and inspection parameter are required": "须填写物料和检验参数",
    "Specification limits differ; using the last subgroup limits": "规格限不一致，采用最后一个子组的规格限",
    "Subgroups larger than 10 are excluded from X-bar/R calculations": "子组大小超过 10，不参与均值极差计算",
    "No specification limits; capability indices are unavailable": "未设规格限，无法计算过程能力指数",
    "Insufficient variation or readings; some capability indices are unavailable": "波动或读数不足，部分过程能力指数无法计算",
}

official = {}
errors = []
for app in ("frappe", "erpnext", "crm", "hrms", "insights", "raven"):
    official.update(_app_translations("zh", app, errors))
if errors:
    raise RuntimeError(errors)
path = Path(frappe.get_app_path("frappe_china", "translations", "zh.csv"))
with path.open(encoding="utf-8", newline="") as stream:
    rows = list(csv.reader(stream))
existing = {tuple(row[::2]) if len(row) > 2 else (row[0],) for row in rows}
for key, value in ADDITIONS.items():
    if key in official:
        print("official", key, official[key])
    elif (key,) not in existing:
        rows.append([key, value])
rows.sort(key=lambda row: (row[0].casefold(), row[2] if len(row) > 2 else ""))
with path.open("w", encoding="utf-8", newline="") as stream:
    csv.writer(stream, lineterminator="\n").writerows(rows)
frappe.clear_cache()
