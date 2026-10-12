"""Build buttons.md / buttons.json for TS-020 (按钮抽检重做).

现译在运行时从合并字典取（Spike/P1S6R4-baseline.py 的 merged_dict），
占用查询调用 Spike/P1S6R4-occupancy.py 的命令行，输出原样贴入。
路径约定：erpnext/... = frappe-bench/apps/erpnext/erpnext/...，frappe/... = frappe-bench/apps/frappe/frappe/...
"""
from __future__ import annotations

import datetime
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPIKE = HERE.parents[1]
SPEC = importlib.util.spec_from_file_location("baseline", SPIKE / "P1S6R4-baseline.py")
baseline = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(baseline)
LOAD_NOTE = "严格载入（无重复键）"
_strict_parse = baseline.parse_csv


def _tolerant_parse(path):
    """Same as baseline.parse_csv but later duplicate keys overwrite earlier ones (Frappe 读 csv 也是后者覆盖)."""
    import csv as _csv
    if not path.exists():
        return {}
    values = {}
    with path.open(encoding="utf-8-sig", newline="") as handle:
        for row in _csv.reader(handle):
            if len(row) not in (2, 3):
                continue
            source, target = (value.replace("\\n", "\n") for value in row[:2])
            values[source + (":" + row[2] if len(row) == 3 and row[2] else "")] = target.strip()
    return values


try:
    MERGED, _PLAIN = baseline.merged_dict()
except ValueError as exc:  # csv 正被并行任务改写、出现重复键时
    LOAD_NOTE = f"严格载入失败（{str(exc)[:120]}…），改用容重复解析（后者覆盖）"
    baseline.parse_csv = _tolerant_parse
    MERGED, _PLAIN = baseline.merged_dict()

OCC_SPEC = importlib.util.spec_from_file_location("occupancy", SPIKE / "P1S6R4-occupancy.py")

# ---- 文件简写 ----
SO = "erpnext/selling/doctype/sales_order/sales_order.js"
SOP = "erpnext/selling/doctype/sales_order/sales_order.py"
QT = "erpnext/selling/doctype/quotation/quotation.js"
QTP = "erpnext/selling/doctype/quotation/quotation.py"
WO = "erpnext/manufacturing/doctype/work_order/work_order.js"
WOP = "erpnext/manufacturing/doctype/work_order/work_order.py"
PO = "erpnext/buying/doctype/purchase_order/purchase_order.js"
POP = "erpnext/buying/doctype/purchase_order/purchase_order.py"
PR = "erpnext/stock/doctype/purchase_receipt/purchase_receipt.js"
PRP = "erpnext/stock/doctype/purchase_receipt/purchase_receipt.py"
PI = "erpnext/accounts/doctype/purchase_invoice/purchase_invoice.js"
PIP = "erpnext/accounts/doctype/purchase_invoice/purchase_invoice.py"
SE = "erpnext/stock/doctype/stock_entry/stock_entry.js"
SEP = "erpnext/stock/doctype/stock_entry/stock_entry.py"
DN = "erpnext/stock/doctype/delivery_note/delivery_note.js"
DNP = "erpnext/stock/doctype/delivery_note/delivery_note.py"
SI = "erpnext/accounts/doctype/sales_invoice/sales_invoice.js"
SIP = "erpnext/accounts/doctype/sales_invoice/sales_invoice.py"
PP = "erpnext/manufacturing/doctype/production_plan/production_plan.js"
PPP = "erpnext/manufacturing/doctype/production_plan/production_plan.py"
BOM = "erpnext/manufacturing/doctype/bom/bom.js"
BOMP = "erpnext/manufacturing/doctype/bom/bom.py"
JC = "erpnext/manufacturing/doctype/job_card/job_card.js"
JCP = "erpnext/manufacturing/doctype/job_card/job_card.py"
PE = "erpnext/accounts/doctype/payment_entry/payment_entry.js"
TX = "erpnext/public/js/controllers/transaction.js"
BUY = "erpnext/public/js/controllers/buying.js"
STC = "erpnext/public/js/controllers/stock_controller.js"
UT = "erpnext/public/js/utils.js"
SR = "erpnext/public/js/stock_reservation.js"
SRE = "erpnext/stock/doctype/stock_reservation_entry/stock_reservation_entry.py"
RET = "erpnext/controllers/sales_and_purchase_return.py"
SUB = "erpnext/controllers/subcontracting_controller.py"
TB = "frappe/public/js/frappe/form/toolbar.js"
FM = "frappe/public/js/frappe/form/form.js"
FSAVE = "frappe/public/js/frappe/form/save.js"
FSAVEP = "frappe/desk/form/save.py"
OPEN_MAPPED = "frappe/public/js/frappe/model/create_new.js:325 open_mapped_doc → frappe/model/mapper.py:13 make_mapped_doc"
MAP_CURRENT = f"{UT}:1044 map_current_doc → frappe/model/mapper.py:37 map_docs"
WO_SE = f"{WOP}:2709 make_stock_entry（建 Stock Entry 并 as_dict 返回，2767，不保存）"
DRAFT = "返回未保存的新单并跳到其表单，点保存才落库"

# 分类
W = "点击即写库"
D = "生成下游草稿"
F = "改当前单据（未写库）"

ROWS = [
    # ---------------- 框架工具栏 ----------------
    dict(source="Save", cat=W,
         calls=[f"{TB}:775（status=Save）", f"{TB}:828（click 映射）", f"{TB}:845（set_primary_action(__(status))）"],
         does=f"{FM}:803 save → {FSAVE}:22 → {FSAVEP}:16 savedocs，docstatus=0 → doc.save()（{FSAVEP}:43）：保存草稿写库"),
    dict(source="Submit", cat=W,
         calls=[f"{TB}:770", f"{TB}:831", f"{TB}:845"],
         does=f"{FM}:898 savesubmit（确认框）→ save('Submit') → {FSAVEP}:16 savedocs，docstatus=1 → doc.submit()（{FSAVEP}:41）：提交"),
    dict(source="Update", cat=W,
         calls=[f"{TB}:779", f"{TB}:834", f"{TB}:845"],
         does=f"已提交单据改了「提交后可改」字段时出现；{FM}:803 save('Update') → {FSAVEP}:16 savedocs，docstatus 仍为 1 → doc.submit() 路径写回（{FSAVEP}:41）"),
    dict(source="Cancel", cat=W,
         calls=[f"{TB}:781", f"{TB}:808（set_secondary_action(__(status))）"],
         does=f"{FM}:943 savecancel（先查已提交的关联单，可连带取消）→ {FM}:1043 _cancel → {FSAVE}:57 → {FSAVEP}:55 cancel → doc.cancel()：docstatus=2"),
    dict(source="Amend", cat=D,
         calls=[f"{TB}:783", f"{TB}:837", f"{TB}:845", f"{TB}:747（已修订过时置灰）"],
         does=f"{FM}:1130 amend_doc → {FM}:1440 copy_doc：复制已取消单为新草稿，写 amended_from；{DRAFT}"),
    dict(source="Delete", cat=W,
         calls=[f"{TB}:508（page.add_menu_item）"],
         does=f"{FM}:1123 savetrash → frappe/public/js/frappe/model/model.js:695 delete_doc（确认框）→ frappe/client.py:297 delete → frappe/model/delete_doc.py:24 delete_doc：物理删除"),
    # ---------------- 状态类 ----------------
    dict(source="Close", cat=W,
         calls=[f"{SO}:969", f"{SO}:1000", f"{WO}:764", f"{PO}:349", f"{PR}:250", f"{DN}:321", f"{PP}:131"],
         does=(f"销售订单 {SO}:1834 → {SO}:1837 → {SOP}:1895 → {SOP}:624 set_status(Closed)；"
               f"工单 {WO}:1245 → {WOP}:2875 close_work_order；采购订单 {PO}:733 → {POP}:997 → {POP}:469；"
               f"采购入库 {PR}:337 → {PRP}:1690；发货单 {DN}:424 → {DN}:432 → {DNP}:1173；"
               f"生产计划 {PP}:317 → {PPP}:700 set_status(close=True) db_set Closed（706）。均把单据状态写成「已关闭」")),
    dict(source="Re-open", cat=W,
         calls=[f"{SO}:973", f"{WO}:782", f"{PO}:368", f"{PP}:123"],
         does=(f"销售订单 update_status('Re-open','Draft') → {SOP}:624 重算状态；采购订单 {PO}:729 → {POP}:469（Submitted）；"
               f"工单（仅已停止时出现）{WO}:1245 → {WOP}:2803 stop_unstop(Resumed)；生产计划 {PPP}:700(close=False)。撤销关闭／停止状态")),
    dict(source="Reopen", cat=W,
         calls=[f"{PR}:279", f"{DN}:357"],
         does=f"采购入库 {PR}:341 → {PRP}:1690(Submitted)；发货单 {DN}:428 → {DNP}:1173(Submitted)：撤销关闭"),
    dict(source="Hold", cat=W,
         calls=[f"{SO}:994", f"{PO}:337"],
         does=(f"{SO}:1801 / {PO}:693：弹框填原因 → frappe/desk/form/utils.py:27 add_comment 写评论 → "
               f"update_status('Hold','On Hold') → {SOP}:624 / {POP}:469：状态置「暂挂」")),
    dict(source="Resume", cat=W,
         calls=[f"{SO}:959", f"{PO}:343"],
         does=f"销售订单 update_status('Resume','Draft') → {SOP}:624；采购订单 {PO}:689 → {POP}:469：从暂挂恢复，状态重算"),
    dict(source="Stop", cat=W,
         calls=[f"{WO}:774"],
         does=f"{WO}:1245 change_work_order_status → {WOP}:2803 stop_unstop(Stopped)：工单状态置「已停止」"),
    # ---------------- 库存预留 ----------------
    dict(source="Reserve", cat=W,
         calls=[f"{SO}:106", f"{WO}:944"],
         does=(f"销售订单 {SO}:256 弹框 → {SO}:412 → {SOP}:856 → {SRE}:1580：按订单行建库存预留单；"
               f"工单 {SR}:4 make_entries → {SR}:188 reserve_stock → {WOP}:2425 make_stock_reservation_entries："
               f"为工单所需原材料（required_items）建库存预留单并 db_set 状态（2456）")),
    dict(source="Unreserve", cat=W,
         calls=[f"{SO}:121", f"{WO}:953"],
         does=(f"销售订单 {SO}:457 → {SO}:517 → {SOP}:876 → {SRE}:1787 cancel_stock_reservation_entries；"
               f"工单 {SR}:216 → {SR}:264 → {WOP}:2460：取消所选库存预留单")),
    dict(source="Reserve for Sub-assembly", cat=W,
         calls=[f"{PP}:268"],
         does=f"{SR}:4 → {SR}:188 → {PPP}:2356 make_stock_reservation_entries(sub_assembly_items)：为子装配件建库存预留单"),
    dict(source="Unreserve for Sub-assembly", cat=W,
         calls=[f"{PP}:276"],
         does=f"{SR}:216 → {SR}:264 → {PPP}:2393 cancel_stock_reservation_entries"),
    dict(source="Reserve for Raw Materials", cat=W,
         calls=[f"{PP}:294"],
         does=f"{SR}:4 → {SR}:188 → {PPP}:2356(mr_items)：为原材料建库存预留单"),
    dict(source="Unreserve for Raw Materials", cat=W,
         calls=[f"{PP}:302"],
         does=f"{SR}:216 → {SR}:264 → {PPP}:2393 cancel_stock_reservation_entries"),
    # ---------------- 改已提交单据 ----------------
    dict(source="Update Items", cat=W,
         calls=[f"{SO}:90", f"{SO}:946", f"{PO}:324", f"{QT}:136"],
         does=(f"{UT}:713 update_child_items 弹框 → {UT}:1020 → erpnext/controllers/accounts_controller.py:4004 update_child_qty_rate："
               f"改已提交单据的明细行（数量、单价、交期，可增行）并 parent.save()（4345）。报价单上同样出现（{QT}:136）"),
         verdict="不一致", final="变更明细",
         reason="现译「订单变更」在报价单（不是订单）上也出现；动作是改明细行",
         occ=[("Update Items", "变更明细")]),
    dict(source="Update Rate as per Last Purchase", cat=F,
         calls=[f"{PO}:575（Tools 组）"],
         does=(f"frappe.call doc 方法 → {POP}:419 get_last_purchase_rate：把本采购订单各行单价改为最近采购价，"
               f"frm.dirty 后待用户保存；不改物料或价目表"),
         verdict="不一致", final="按最近采购价更新单价",
         reason="现译说更新「价格主数据」，源码只改本单行单价",
         occ=[("Update Rate as per Last Purchase", "按最近采购价更新单价")]),
    # ---------------- 收付款 ----------------
    dict(source="Payment", cat=D,
         calls=[f"{SI}:98", f"{PI}:124", f"{SO}:1175", f"{PO}:429"],
         does=(f"{TX}:2788 make_payment_entry → {TX}:2798 → {TX}:3031 get_method_for_payment → "
               f"erpnext/accounts/doctype/payment_entry/payment_entry.py:2898 get_payment_entry：建收付款凭证草稿（3070 返回、不保存），"
               f"方向由 payment_entry.py:3299 set_payment_type 定：销售订单／销售发票=收款，采购订单／采购发票=付款"),
         final="收付款", reason="DEC-035",
         occ=[("Payment", "收付款", "Payments"), ("Payment", "收付款")]),
    dict(source="Payment Request", cat=W,
         calls=[f"{SO}:1167", f"{PO}:437", f"{PI}:145", f"{SI}:139"],
         does=(f"{TX}:502 make_payment_request_with_schedule → 弹框 {TX}:584 → "
               f"erpnext/accounts/doctype/payment_request/payment_request.py:579 make_payment_request：insert（776/779），"
               f"默认即 submit（780；会计设置勾「草稿」时不提交）")),
    # ---------------- 生产 ----------------
    dict(source="Start", cat=D,
         calls=[f"{WO}:824"],
         does=f"{WO}:1159 make_se(purpose='Material Transfer for Manufacture') → {WO_SE}：建「工单发料」库存凭证草稿，不启动工单",
         verdict="不一致（不可分，保留）", final=None,
         reason=("动作是领料；但 `Start` 无 context，另有 frappe 打印页／Recorder、hrms 考核周期、erpnext 计时器与期间结账等出处，"
                 "改成「领料」会误导那些处，按 R3 Part2 TS-009 第 4 条记「不可分、保留」"),
         occ=[("Start", "领料")]),
    dict(source="Finish", cat=D,
         calls=[f"{WO}:904", f"{WO}:919", f"{WO}:928"],
         does=f"{WO}:1159 make_se(purpose='Manufacture') → {WO_SE}：建「完工入库」库存凭证草稿"),
    dict(source="Additional Material Transfer", cat=D,
         calls=[f"{WO}:837（Make 组）"],
         does=f"{WO}:1093 弹框填数量 → {WO}:844 xcall → {WO_SE}，is_additional_transfer_entry=1：建超出计划量的工单发料草稿"),
    dict(source="Material Consumption", cat=D,
         calls=[f"{WO}:883（Make 组）"],
         does=f"{WO}:1219 make_consumption_se → {WO_SE}，purpose='Material Consumption for Manufacture'：建工单耗用草稿"),
    dict(source="Return Components", cat=D,
         calls=[f"{WO}:299"],
         does=f"{WO}:306 → {WOP}:3161 make_stock_return_entry：建 is_return 的工单发料退回草稿（未耗用原材料退回）"),
    dict(source="Disassemble Order", cat=D,
         calls=[f"{WO}:228（Create 组）"],
         does=f"{WO}:456 弹框 → {WO_SE}，purpose='Disassemble'：建拆解库存凭证草稿"),
    dict(source="Disassemble", cat=D,
         calls=[f"{SE}:405（Create 组）"],
         does=f"{SE}:405 内 xcall → {WO_SE}，purpose='Disassemble'：由完工入库单建拆解草稿"),
    dict(source="Create Job Card", cat=W,
         calls=[f"{WO}:203"],
         does=f"{WO}:321 弹框选工序 → {WO}:400 → {WOP}:2841 make_job_card → {WOP}:2968 create_job_card(auto_create) insert（3014）：直接建生产任务单"),
    dict(source="Create Pick List", cat=D,
         calls=[f"{WO}:816"],
         does=f"{WO}:1198 → {WOP}:3031 create_pick_list：建拣货单草稿"),
    dict(source="BOM", cat=D,
         calls=[f"{WO}:212（Create 组）"],
         does=f"{WO}:443 → {WOP}:1987 make_bom：按已完工入库耗用建新 BOM（new_doc，不保存）"),
    dict(source="Work Order", cat=W,
         calls=[f"{SO}:1055", f"{BOM}:257"],
         does=(f"销售订单 {SO}:1249 → {SOP}:2067 取可生产行 → 弹框 → {SO}:1334 → {SOP}:1830 make_work_orders：直接 insert 工单（1854）；"
               f"BOM {BOM}:332 → {WOP}:2593 make_work_order：返回未保存工单（2632）")),
    dict(source="Work Order / Subcontract PO", cat=W,
         calls=[f"{PP}:143"],
         does=f"{PP}:329 → {PPP}:773 make_work_order → {PPP}:925 create_work_order insert（947）＋ {PPP}:864 委外采购订单：按计划批量建工单与委外采购订单"),
    dict(source="Production Plan", cat=D,
         calls=[f"{SO}:1063"],
         does=f"{SO}:1370 → {OPEN_MAPPED} → {SOP}:1864 make_production_plan：{DRAFT}"),
    dict(source="Material Request", cat=W,
         calls=[f"{SO}:1092", f"{WO}:820", f"{PP}:158", f"{JC}:220", f"{SE}:322",
                f"{PO}:527（取物料来源，筛掉）", f"{SE}:478（取物料来源，筛掉）"],
         does=(f"销售订单 {SO}:1385 → {SOP}:1043、工单 {WO}:1191 → {WOP}:3127、生产任务单 {JC}:830 → {JCP}:1866：经 open_mapped_doc 建物料需求草稿；"
               f"生产计划 {PP}:340 确认框 → {PP}:352 → {PPP}:962 make_material_request：save（1028），选「是」再 submit（1030）；"
               f"库存凭证 {SE}:322 前端 new_doc 物料需求草稿")),
    dict(source="Request for Raw Materials", cat=W,
         calls=[f"{SO}:1098"],
         does=f"{SO}:1403 → 弹框 {SO}:1482 → {SOP}:1901 make_raw_material_request：insert（1953）并 submit（1956）物料需求"),
    dict(source="Make Stock Entry", cat=W,
         calls=[f"{PR}:255", f"{JC}:111"],
         does=(f"采购入库 {PR}:457 → {OPEN_MAPPED} → {PRP}:1696：物料移动草稿；"
               f"生产任务单 {JC}:111 确认框 → {JC}:120 → {JCP}:1736 make_stock_entry_for_semi_fg_item：建半成品入库，选「是」submit（1770）否则 save（1772）")),
    dict(source="Material Transfer", cat=D,
         calls=[f"{JC}:228（Create 组）"],
         does=f"{JC}:838 → {OPEN_MAPPED} → {JCP}:1897 make_stock_entry：purpose='Material Transfer for Manufacture'（1919），即工单发料草稿",
         verdict="不一致（不可分，保留）", final=None,
         reason=("生产任务单上建的是工单发料，现译「直接调拨」是库存凭证用途 `Material Transfer` 的译名；该键无 context，"
                 "另 8 处出处（库存凭证类型、物料需求类型、拣货单用途等）都指「直接调拨」，改了误导，记「不可分、保留」"),
         occ=[("Material Transfer", "工单发料")]),
    dict(source="Make Subcontracting PO", cat=D,
         calls=[f"{JC}:419"],
         does=f"{OPEN_MAPPED} → {JCP}:1782 make_subcontracting_po：{DRAFT}"),
    dict(source="Corrective Job Card", cat=D,
         calls=[f"{JC}:456（Make 组）"],
         does=f"{JC}:494 → {JCP}:2024 make_corrective_job_card：建返工生产任务单草稿"),
    dict(source="Update Cost", cat=W,
         calls=[f"{BOM}:225（Actions 组）"],
         does=f"{BOM}:567 update_cost(save=true) → {BOMP}:677：重算 BOM 成本并保存（已提交也写回）"),
    dict(source="New Version", cat=D,
         calls=[f"{BOM}:246（Actions 组）"],
         does="frappe.model.copy_doc（frappe/public/js/frappe/model/create_new.js:281）复制本 BOM 为新草稿"),
    dict(source="Variant BOM", cat=D,
         calls=[f"{BOM}:266（Create 组）"],
         does=f"{BOM}:360 → {BOMP}:2036 make_variant_bom：建变体 BOM 草稿"),
    dict(source="Quality Inspection(s)", cat=W,
         calls=[f"{TX}:436", f"{SE}:218"],
         does=f"{TX}:2846 make_quality_inspection 弹框 → {TX}:2925 → erpnext/controllers/stock_controller.py:2412 make_quality_inspections：逐行 save 质检单（2447）"),
    dict(source="Quality Inspection", cat=D,
         calls=[f"{BOM}:276（Create 组）"],
         does=f"{BOM}:560 → erpnext/stock/doctype/quality_inspection/quality_inspection.py:537：质检单草稿"),
    # ---------------- 销售下游 ----------------
    dict(source="Sales Order", cat=D,
         calls=[f"{QT}:134（Create）", f"{DN}:156（取物料来源，筛掉）", f"{SI}:378（取物料来源，筛掉）"],
         does=(f"报价单 {QT}:190 → {OPEN_MAPPED} → {QTP}:377 make_sales_order：{DRAFT}。"
               f"另两处在「取物料来源」组：{MAP_CURRENT} → {SOP}:1172 / {SOP}:1356，把销售订单行带入当前草稿，不建新单")),
    dict(source="Delivery Note", cat=D,
         calls=[f"{SO}:1047（Create）", f"{SI}:128（Create）", f"{PR}:58（Create，公司间）", f"{SI}:434（取物料来源，筛掉）"],
         does=(f"销售订单 {SO}:1515 → {SO}:1578 → {SOP}:1172；销售发票 {SI}:733 → {SIP}:2507；"
               f"采购入库（内部供应商）→ {PRP}:1756 make_inter_company_delivery_note：均经 open_mapped_doc，{DRAFT}。"
               f"{SI}:434 是取物料来源 → {DNP}:834 带入当前发票")),
    dict(source="Sales Invoice", cat=D,
         calls=[f"{SO}:1077", f"{DN}:346"],
         does=f"销售订单 {SO}:1591 → {SOP}:1356；发货单 {DN}:384 → {DNP}:834：经 open_mapped_doc，{DRAFT}"),
    dict(source="Pick List", cat=D,
         calls=[f"{SO}:1027（Create）", f"{DN}:198（取物料来源，筛掉）"],
         does=f"{SO}:1242 → {SOP}:1968 create_pick_list：{DRAFT}；{DN}:198 → erpnext/stock/doctype/pick_list/pick_list.py:1405 带入当前发货单"),
    dict(source="Credit Note", cat=D,
         calls=[f"{DN}:88"],
         does=f"退货发货单上 → {OPEN_MAPPED} → {DNP}:834 make_sales_invoice：建退货（is_return）销售发票草稿，即红字发票"),
    dict(source="Return / Credit Note", cat=D,
         calls=[f"{SI}:110"],
         does=f"{SI}:600 → {SIP}:2556 make_sales_return → {RET}:446 make_return_doc：建退货销售发票（红字发票）草稿",
         verdict="不一致", final="退货/红字发票",
         reason="Credit Note 是红字发票、不是退款（S3 术语草案已定；`Credit Note` 现译「红字发票」）",
         occ=[("Return / Credit Note", "退货/红字发票")]),
    dict(source="Sales Return", cat=D,
         calls=[f"{DN}:269"],
         does=f"{DN}:398 → {DNP}:1166 → {RET}:446：建退货发货单草稿"),
    dict(source="Project", cat=D, calls=[f"{SO}:1138"],
         does=f"{SO}:1605 → {SOP}:1145 make_project：{DRAFT}"),
    dict(source="Maintenance Visit", cat=D, calls=[f"{SO}:1121"],
         does=f"{SO}:1619 → {SOP}:1591：{DRAFT}"),
    dict(source="Maintenance Schedule", cat=D, calls=[f"{SO}:1128", f"{SI}:163"],
         does=f"{SO}:1598 → {SOP}:1565；{SI}:231 → {SIP}:2490：{DRAFT}"),
    dict(source="Subcontracting Inward Order", cat=D, calls=[f"{SO}:1010"],
         does=f"{SO}:1853 → {SOP}:2136：{DRAFT}"),
    dict(source="Purchase Order", cat=W,
         calls=[f"{SO}:1111（Create）", f"{SO}:188（取物料来源，筛掉）", f"{PI}:155（取物料来源，筛掉）", f"{PR}:216（取物料来源，筛掉）"],
         does=(f"销售订单 {SO}:1626 弹框选供应商 → {SO}:1735 → {SOP}:1655 make_purchase_order：直接 insert 采购订单（1805）。"
               f"其余三处是取物料来源：{MAP_CURRENT} → {POP}:1004 / {POP}:869 / {POP}:800，带入当前草稿")),
    dict(source="Internal Purchase Order", cat=D, calls=[f"{SO}:1151（button_label，{SO}:1154 加按钮）"],
         does=f"{SO}:1612 → {SOP}:1961 make_inter_company_purchase_order：{DRAFT}"),
    dict(source="Inter Company Purchase Order", cat=D, calls=[f"{SO}:1152（同上）"],
         does=f"{SO}:1612 → {SOP}:1961：{DRAFT}"),
    dict(source="Dunning", cat=D, calls=[f"{SI}:158"],
         does=f"{SI}:224 → {SIP}:3161 create_dunning：{DRAFT}"),
    dict(source="Invoice Discounting", cat=D, calls=[f"{SI}:147"],
         does=f"{SI}:217 → {SIP}:3054：{DRAFT}"),
    dict(source="Internal Purchase Invoice", cat=D, calls=[f"{SI}:178（button_label，{SI}:181 __(button_label)）"],
         does=f"{SI}:521 → {SIP}:2650 make_inter_company_purchase_invoice：{DRAFT}",
         verdict="不一致（缺译）", final="内部采购发票", reason="合并字典无此键，界面显示英文",
         occ=[("Internal Purchase Invoice", "内部采购发票")]),
    dict(source="Inter Company Purchase Invoice", cat=D, calls=[f"{SI}:179（同上）"],
         does=f"{SI}:521 → {SIP}:2650：{DRAFT}",
         verdict="不一致（缺译）", final="公司间采购发票", reason="合并字典无此键，界面显示英文",
         occ=[("Inter Company Purchase Invoice", "公司间采购发票")]),
    dict(source="Shipment", cat=D, calls=[f"{DN}:245"], does=f"{DN}:368 → {DNP}:1085：{DRAFT}"),
    dict(source="Installation Note", cat=D, calls=[f"{DN}:259"], does=f"{DN}:391 → {DNP}:1002：{DRAFT}"),
    dict(source="Delivery Trip", cat=D, calls=[f"{DN}:279"], does=f"{DN}:405 → {DNP}:972：{DRAFT}"),
    dict(source="Packing Slip", cat=D, calls=[f"{DN}:295"], does=f"{OPEN_MAPPED} → {DNP}:1030：{DRAFT}"),
    dict(source="Internal Purchase Receipt", cat=D, calls=[f"{DN}:110（button_label，{DN}:113 __(button_label)）"],
         does=f"{OPEN_MAPPED} → {DNP}:1180 make_inter_company_purchase_receipt：{DRAFT}",
         verdict="不一致（缺译）", final="内部采购入库", reason="合并字典无此键，界面显示英文",
         occ=[("Internal Purchase Receipt", "内部采购入库")]),
    dict(source="Inter Company Purchase Receipt", cat=D, calls=[f"{DN}:111（同上）"],
         does=f"{OPEN_MAPPED} → {DNP}:1180：{DRAFT}",
         verdict="不一致（缺译）", final="公司间采购入库", reason="合并字典无此键，界面显示英文",
         occ=[("Inter Company Purchase Receipt", "公司间采购入库")]),
    # ---------------- 采购下游 ----------------
    dict(source="Purchase Receipt", cat=D,
         calls=[f"{PO}:383（Create）", f"{PI}:642（Create）", f"{PI}:180（取物料来源，筛掉）", f"{PI}:652（View，筛掉）"],
         does=(f"采购订单 {PO}:502 → {POP}:800；采购发票 {PI}:721 → {PIP}:2130：经 open_mapped_doc，{DRAFT}。"
               f"{PI}:180 带入当前发票；{PI}:652 跳采购入库列表")),
    dict(source="Purchase Invoice", cat=D,
         calls=[f"{PO}:416（Create）", f"{PR}:262（Create）", f"{PR}:117（取物料来源，筛掉）", f"{SE}:459（取物料来源，筛掉）"],
         does=(f"采购订单 {PO}:510 → {POP}:869；采购入库 {PR}:285 → {PRP}:1521：{DRAFT}。"
               f"另两处取物料来源 → {PIP}:2130 / {PIP}:2105，带入当前草稿")),
    dict(source="Debit Note", cat=D, calls=[f"{PR}:44"],
         does=f"退货采购入库上 → {OPEN_MAPPED} → {PRP}:1521 make_purchase_invoice：建退货采购发票草稿，即采购红字发票"),
    dict(source="Return / Debit Note", cat=D, calls=[f"{PI}:130"],
         does=f"{PI}:473 → {PIP}:2098 make_debit_note → {RET}:446 make_return_doc：建退货采购发票（采购红字发票）草稿",
         verdict="不一致", final="退货/采购红字发票",
         reason="Debit Note 是采购红字发票、不是退款（`Debit Note` 现译「采购红字发票」）",
         occ=[("Return / Debit Note", "退货/采购红字发票")]),
    dict(source="Purchase Return", cat=D, calls=[f"{PR}:253"],
         does=f"{PR}:292（有拒收行时询问）→ {PRP}:1676 或 {PR}:450 → {PRP}:1683 → {RET}:446：建退货采购入库草稿"),
    dict(source="Landed Cost Voucher", cat=D, calls=[f"{PR}:87", f"{PI}:666"],
         does=f"{PR}:99 / {PI}:676 → {PRP}:1766 make_lcv：new_doc 到岸成本凭证，不保存"),
    dict(source="Sample Retention Stock Entry", cat=W, calls=[f"{PR}:268", f"{SE}:570"],
         does=f"{PR}:345 / {SE}:683 → {SEP}:4321 move_sample_to_retention_warehouse：先 save 批次序列包（4381），再返回未保存的留样物料移动"),
    dict(source="Subcontracting Order", cat=D, calls=[f"{PO}:403"],
         does=f"{PO}:517 → {POP}:1011 make_subcontracting_order（前端不传 save/submit）：{DRAFT}"),
    dict(source="Material to Supplier", cat=D, calls=[f"{PO}:393（Transfer 组）"],
         does=f"{PO}:481 → {SUB}:1384 make_rm_stock_entry：建「委外发料」物料移动草稿"),
    dict(source="Return of Components", cat=D, calls=[f"{PO}:105（Create 组）"],
         does=f"{PO}:93 → {SUB}:1572 get_materials_from_supplier → {SUB}:1524：建委外原材料退回（is_return）草稿"),
    dict(source="Deliver (Dropship)", cat=W, calls=[f"{PO}:358（Status 组）"],
         does=f"{PO}:737 弹框填数量 → {PO}:819 → {POP}:609 update_dropship_received_qty：db_set 各行 received_qty（657）并 set_status（665）"),
    dict(source="Block Invoice", cat=W, calls=[f"{PI}:108"],
         does=f"{PI}:248 → {PI}:266 弹框 → {PI}:296 → {PIP}:1967：db_set on_hold=1、原因、解冻日（1973）"),
    dict(source="Unblock Invoice", cat=W, calls=[f"{PI}:100"],
         does=f"{PI}:241 → {PIP}:1976：db_set on_hold=0（1978）"),
    dict(source="Change Release Date", cat=W, calls=[f"{PI}:93（Hold Invoice 组）"],
         does=f"{PI}:252 → {PI}:344 → {PIP}:1981：db_set release_date（1990）"),
    dict(source="Internal Sales Order", cat=D, calls=[f"{PO}:452（button_label，{PO}:455 加按钮）"],
         does=f"{PO}:495 → {POP}:1004 make_inter_company_sales_order：{DRAFT}"),
    dict(source="Inter Company Sales Order", cat=D, calls=[f"{PO}:453（同上）"],
         does=f"{PO}:495 → {POP}:1004：{DRAFT}"),
    dict(source="Inter Company Invoice", cat=D, calls=[f"{PI}:228（字面串，未包 __()）"],
         does=f"{PI}:413 → {PIP}:2123 make_inter_company_sales_invoice：建对方公司的销售发票草稿",
         verdict="不一致（未包 __()，csv 无效）", final="公司间销售发票",
         reason="按钮名是裸字符串，加 csv 也不会译；要改须动 erpnext 代码或另挂补丁（本任务不改代码）",
         occ=[("Inter Company Invoice", "公司间销售发票")]),
    # ---------------- 其它 ----------------
    dict(source="Set as Lost", cat=W, calls=[f"{QT}:146"],
         does=f"erpnext/public/js/utils/sales_common.js:588 set_as_lost_dialog → quotation.py:265 declare_enquiry_lost：db_set status=Lost（273）并记原因"),
    dict(source="End Transit", cat=D, calls=[f"{SE}:381"],
         does=f"{OPEN_MAPPED} → {SEP}:4402 make_stock_in_entry：建在途入库物料移动草稿"),
]

FILTERED = [
    ("Quotation", f"{SO}:1191、{SI}:402", "仅在「取物料来源」组：把报价单行带入当前草稿，不建新单"),
    ("Opportunity", f"{QT}:153", "取物料来源"),
    ("Supplier Quotation", f"{PO}:552", "取物料来源"),
    ("Transit Entry", f"{SE}:600", "取物料来源"),
    ("Bill of Materials", f"{SE}:785", "取物料来源（{SE}:795 get_items_from_bom 填当前单）".replace("{SE}", SE)),
    ("Expired Batches", f"{SE}:531", "取物料来源"),
    ("Product Bundle", f"{BUY}:324", "取物料来源"),
    ("Timesheet", f"{SI}:301", "Get Timesheets 组：把工时单带入当前发票"),
    ("Alternate Item", f"{WO}:162、{SE}:358、{BOM}:291", f"{UT}:565 弹框换当前单的物料行，不写库"),
    ("Link to Material Request", f"{PO}:590", "只在前端给本单行补 material_request 引用，不写库"),
    ("Reserved Stock", f"{SO}:134、{WO}:960", "弹框查看已预留"),
    ("Reserved Stock for Sub-assembly", f"{PP}:282", "查看"),
    ("Reserved Stock for Raw Materials", f"{PP}:308", "查看"),
    ("Stock Ledger", f"{STC}:96、erpnext/public/js/utils/ledger_preview.js:36", "跳报表／预览"),
    ("Accounting Ledger", f"{STC}:117、erpnext/public/js/utils/ledger_preview.js:7", "跳报表／预览"),
    ("Ledger", f"{PE}:425", "跳总账"),
    ("View Exchange Gain/Loss Journals", f"{PE}:255", "跳列表"),
    ("Production Plan Summary", f"{PP}:109", "跳报表"),
    ("Browse BOM", f"{BOM}:233", "跳树视图"),
    ("Asset", f"{PR}:191", "跳列表"),
    ("Asset Movement", f"{PR}:202", "跳列表"),
    ("Received Stock Entries", f"{SE}:390", "跳列表"),
    ("Send SMS", f"{TX}:733（page.add_menu_item）", "发短信，不改业务单据"),
    ("Excise Invoice", f"{SE}:1550", "仅 country=India 时出现，中国站不显示"),
    ("UnReconcile", "erpnext/public/js/utils/unreconcile.js:24", "会写库（unreconcile_payment.py:215 save+submit），但定义在 public/js/utils/，不在本次范围（13 张 .js＋controllers/）；现译「取消核销」与动作一致"),
]


def current(key):
    return MERGED.get(key)


_OCC = None


def occupancy(args):
    """Run P1S6R4-occupancy.py CLI; if it crashes on a csv duplicate key, run its check() in-process with tolerant parse."""
    global _OCC
    cmd = [sys.executable, "-I", "-X", "utf8", str(SPIKE / "P1S6R4-occupancy.py"), *args]
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", cwd=SPIKE.parent)
    shown = " ".join(f'"{a}"' for a in args)
    out = proc.stdout.strip()
    if proc.returncode == 0 and out:
        return f"`{shown}` → `{out}`"
    if _OCC is None:
        _OCC = importlib.util.module_from_spec(OCC_SPEC)
        OCC_SPEC.loader.exec_module(_OCC)
        _OCC.baseline.parse_csv = _tolerant_parse
    source, candidate, *syn = args
    ok, found = _OCC.check(source, candidate, set(syn))
    res = {"source": source, "candidate": candidate, "usable": ok, "occupants": found}
    return f"`{shown}` → `{res}`（CLI 因 csv 重复键报错，同函数进程内重跑）"


def esc(text):
    return str(text).replace("|", "\\|").replace("\n", " ")


def main():
    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    records = []
    for row in ROWS:
        cur = current(row["source"])
        verdict = row.get("verdict", "一致")
        final = row.get("final") or cur
        if final is None:
            final = cur
        occ = [occupancy(a) for a in row.get("occ", [])]
        records.append(dict(row, current=cur, verdict=verdict, final=final, occ_out=occ))

    write_count = sum(1 for r in records if r["cat"] == W)
    draft_count = sum(1 for r in records if r["cat"] == D)
    form_count = sum(1 for r in records if r["cat"] == F)
    bad = [r for r in records if r["verdict"] != "一致"]

    lines = [
        "# 改数据按钮抽检表（TS-020，重做 IT-010）",
        "",
        f"生成：`Spike/P1S6R7/buttons/build.py`，{stamp}。现译取自 `P1S6R4-baseline.py` 的 `merged_dict()`（读盘即时值，非站点 clear-cache 后实测）；本次 {LOAD_NOTE}。",
        "路径约定：`erpnext/...` = `frappe-bench/apps/erpnext/erpnext/...`，`frappe/...` = `frappe-bench/apps/frappe/frappe/...`。",
        "",
        f"入表 **{len(records)}** 个源词：点击即写库 {write_count}、生成下游草稿 {draft_count}、改当前单据未写库 {form_count}。判不一致 {len(bad)} 个。",
        "",
        "**不在 20–40 区间的原因**：需求 §4.4 口径把「创建 → 下游单据」整类算作改数据。13 张单据的「创建」菜单下游类型多（销售订单一张就有 15 种），"
        "加上公司间单据的 6 个按钮名，去重后远超 40。若只计「点击即写库」一类，"
        f"是 {write_count} 个，落在区间内。另需注意：经 `open_mapped_doc`／`get_mapped_doc` 的「创建」按钮点击时并不写库，只返回未保存的新单，用户点保存才生成记录（`frappe/model/mapper.py:13`、`create_new.js:325`）。",
        "",
        "| 源词 | 现译 | 调用行（文件:行，全部） | 源码实际做什么（写到被调方法定义 文件:行） | 判定 | 建议定稿 | 占用查询输出 |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in records:
        does = f"〔{r['cat']}〕" + r["does"]
        if r.get("reason"):
            does += f"。判定依据：{r['reason']}"
        final_cell = r["final"]
        lines.append("| " + " | ".join(esc(x) for x in [
            f"`{r['source']}`", r["current"] or "（无）", "<br>".join(r["calls"]), does,
            r["verdict"], final_cell or "—", "<br>".join(r["occ_out"]) or "—",
        ]) + " |")

    lines += [
        "",
        "## 筛掉的按钮",
        "",
        "| 源词 | 调用行 | 为何不算改数据 |",
        "|---|---|---|",
    ]
    for src, where, why in FILTERED:
        lines.append(f"| `{esc(src)}` | {esc(where)} | {esc(why)} |")

    lines += [
        "",
        "「取物料来源」组的按钮走 `erpnext/public/js/utils.js:1044 map_current_doc` → `frappe/model/mapper.py:37 map_docs`，把源单行映射进**当前未保存草稿**，回调里只 `frm.dirty()`／`refresh()`，不建新单、不写库。"
        "它们与「创建」组同名的（`Sales Order`、`Purchase Order`、`Purchase Receipt`、`Purchase Invoice`、`Delivery Note`、`Material Request`、`Pick List`）在主表里一并列出调用行并注明「筛掉」。",
        "",
        "## E 报告点名四行的核对",
        "",
        f"1. **`{SI}:378`**：源词 `Sales Order`（现译「{current('Sales Order')}」），在 `sales_order_btn()`（{SI}:365）里加到「Get Items From」（现译「{current('Get Items From')}」）组；"
        f"只在草稿且非退货时出现（{SI}:284-292）。点击 → {MAP_CURRENT} → `{SOP}:1356 make_sales_invoice`，target_doc 为当前销售发票：把所选销售订单行带入本发票。不建新单、不写库。**不算改数据**。",
        f"2. **`{SI}:402`**：源词 `Quotation`（现译「{current('Quotation')}」），`quotation_btn()`（{SI}:400），同在「Get Items From」组、同样条件。点击 → {MAP_CURRENT} → `{QTP}:532 make_sales_invoice`：把报价单行带入本发票。**不算改数据**。上一轮「从销售订单或发票创建报价单」的描述是错的。",
        f"3. **`{PI}:155`**：源词 `Purchase Order`（现译「{current('Purchase Order')}」），草稿态（{PI}:154 `docstatus === 0`）加到「Get Items From」组。点击 → {MAP_CURRENT} → `{POP}:869 make_purchase_invoice`：把所选采购订单行带入本采购发票。确为「从采购订单取物料」，**不算改数据**。",
        f"4. **`{WO}:944`**：源词 `Reserve`（现译「{current('Reserve')}」），在 `setup_stock_reservation`（{WO}:938），仅已提交、勾了 reserve_stock、且有未预留量时加到「Stock Reservation」组。点击 → `{SR}:4 make_entries` → 弹框 → `{SR}:188 reserve_stock` → `{WOP}:2425 make_stock_reservation_entries`："
        "为**工单所需原材料**（required_items）建库存预留单（2451）并 db_set 工单状态（2456）。**改数据**。上一轮写成「为销售订单预留库存」，对象错了；中文「预留」本身与动作一致。",
        "",
        "## 判不一致汇总",
        "",
        "| 源词 | 现译 | 建议定稿 | 说明 |",
        "|---|---|---|---|",
    ]
    for r in bad:
        lines.append(f"| `{esc(r['source'])}` | {esc(r['current'] or '（无）')} | {esc(r['final'])} | {esc(r['verdict'])}：{esc(r.get('reason', ''))} |")

    (HERE / "buttons.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    payload = [dict(source=r["source"], current=r["current"], calls=r["calls"], does=r["does"],
                    verdict=r["verdict"], final=r["final"]) for r in records]
    (HERE / "buttons.json").write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(len(records), write_count, draft_count, form_count)
    for r in bad:
        print(r["source"], "|", r["current"], "->", r["final"], "|", r["verdict"])
    missing = [r["source"] for r in records if r["current"] is None]
    print("no current:", missing)


if __name__ == "__main__":
    main()
