from __future__ import annotations

import csv
from pathlib import Path

path = Path(__file__).with_name("P1S6R4-buttons.csv")
actions = {
    "Close": ("关闭关联销售/采购单据", "关闭"),
    "Delivery Note": ("从销售发票/销售订单/采购收货生成送货单", "送货单"),
    "Dunning": ("创建催款通知", "催款"),
    "Hold": ("将销售订单或采购订单置为暂停", "暂停"),
    "Material Request": ("从业务单据创建物料申请", "物料申请"),
    "Payment": ("创建付款条目", "付款"),
    "Project": ("从销售订单创建项目", "项目"),
    "Purchase Order": ("创建采购订单", "采购订单"),
    "Purchase Receipt": ("创建采购收货单", "采购收货单"),
    "Purchase Return": ("创建采购退货单", "采购退货"),
    "Quotation": ("从销售订单或发票创建报价单", "报价单"),
    "Re-open": ("重新打开已关闭的单据", "重新打开"),
    "Reserve": ("为销售订单预留库存", "预留"),
    "Sales Invoice": ("从销售订单或送货单创建销售发票", "销售发票"),
    "Sales Order": ("从报价单或销售发票创建销售订单", "销售订单"),
    "Unreserve": ("取消销售订单的库存预留", "取消预留"),
    "Update Items": ("更新单据中的物料明细", "更新物料"),
    "Work Order": ("从销售订单或 BOM 创建工单", "工单"),
    "Save": ("保存当前文档", "保存"),
    "Submit": ("提交当前文档", "提交"),
    "Cancel": ("取消当前文档", "取消"),
    "Amend": ("基于已取消文档新建修订单", "修订"),
    "Delete": ("删除当前文档", "删除"),
}

with path.open(encoding="utf-8-sig", newline="") as f:
    rows = list(csv.DictReader(f))
for row in rows:
    action, translation = actions[row["源词"]]
    row["实际动作"] = action
    row["判定"] = "一致"
    row["定稿译名"] = translation
with path.open("w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys(), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
print(f"finalized {len(rows)} button terms")
