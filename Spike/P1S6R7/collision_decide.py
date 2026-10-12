"""TS-019 第 3 步：演示撞名人工判定的落地。宿主 python -I -X utf8 跑。
DECISIONS 里每个异义源词给定词与落法（plain＝无 context 行；ctx＝按演示面字段出处的每个 DocType 写 context 行；
ctx:<DocType> 只写指定 DocType）。其余仍撞组判同义保留（理由见 SYNONYM_NOTES，未列的为机械同义）。
产出 Spike/P1S6R7/collision_rows.csv、collision_meta.json（供 apply_rows.py）与 collision_table.json（回执附表）。
"""
import csv, importlib.util, json, re
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("bl", ROOT / "Spike/P1S6R4-baseline.py")
bl = importlib.util.module_from_spec(spec); spec.loader.exec_module(bl)
spec = importlib.util.spec_from_file_location("occ", ROOT / "Spike/P1S6R4-occupancy.py")
occ = importlib.util.module_from_spec(spec); spec.loader.exec_module(occ)

# 源词 → (定词, 落法, 理由)
DECISIONS = {
    "POS Profile": ("POS配置", "plain", "配置记录，与全局 POS Settings 异义；占用者 Point-of-Sale Profile 为同一对象"),
    "Leaves": ("休假", "plain", "HRMS 休假模块与 Holiday List（节假日表）异义；11 处出处均指休假"),
    "Document Naming": ("单据编号设置", "ctx", "设置页签，与 Against Docname（源单编号）异义"),
    "Pinned Views": ("已固定视图", "plain", "已固定的视图列表，与「固定视图」动作异义"),
    "Due Date": ("到期日期", "plain", "到期日与 To Date（期间截止）异义"),
    "Debit Note": ("采购红字发票", "plain", "采购退货发票，与 Payment Entry Deduction（收付款扣减）异义；与 S3 Credit Note → 红字发票 成对"),
    "Disassembled Qty": ("已拆解数量", "ctx", "完成量，与 Qty to Disassemble（待拆解）异义"),
    "Stock Ledger": ("库存台账", "plain", "E 点名：报表与 Stock Ledger Entry（分录）异义（R3 Part2 TS-006 第 5 步候选）"),
    "Loyalty Point Entry": ("积分记录", "plain", "积分流水记录，与 Loyalty Points（积分数）异义"),
    "Editor": ("编辑器", "plain", "Raven 指令编辑器页签，与「编辑」动作异义"),
    "Process Payment Reconciliation": ("收付款核销任务", "plain", "批处理单据，与 Auto reconcile Payments 勾选框异义"),
    "Expenses": ("报销管理", "plain", "HRMS 报销模块，与科目根类型 Expense（费用）异义"),
    "Returned Qty ": ("已退回数量", "ctx", "已退回的数量，与 Return Qty（退货按钮）异义"),
    "Problem": ("故障", "ctx", "工位状态选项，与 Issue（客服问题单）异义；占用者 Breakdown／Failure 同义"),
    "Cash Flow Name": ("现金流量项目名称", "plain", "本 app 现金流量小计的项目名，与 Project Name（工程项目）异义"),
    "Item Type": ("物料类别", "plain", "物料列表列名（是否固定资产），与 Project Type 异义"),
    "Reserved Inventory": ("已预留库存", "ctx", "Bin 分节，指已预留量，与 Reserve Stock（预留动作）异义；占用者 Reserved Stock／Stock Reserved 同义"),
    "From": ("原单位", "ctx:UOM Conversion Factor", "单位换算的源单位，与 Sender（发件人）异义；无 context 的 From 另有邮件发件人义，不改"),
}
SYNONYM_NOTES = {
    "商机": "CRM Deal 与 ERPNext Opportunity 是两个 App 里同一业务概念；演示链路只用 CRM 商机",
    "应用": "App／Hidden 的出处是 desktop_icon DocType 定义文件，被基线脚本的图标 glob 误收，首页不显示",
    "隐藏": "同上",
    "关闭": "Raven 命令菜单「esc 关闭」与按钮「关闭」同义",
    "搜索": "同上",
    "生成": "Generate／Make 同义动词",
    "发生错误": "大小写与措辞变体",
    "会计账簿": "S3 §2.3.3 判同义并同改",
    "低税率扣除证明": "侧栏条目即该 DocType",
    "原材料耗用": "BOM 分节与制造设置分节同指原材料耗用",
    "外包收货订单": "侧栏分组标题即该单据",
    "委外订单": "同上",
    "对方科目": "GL Entry.against 即对方科目",
    "应付账款": "报表与侧栏分组同指",
    "应收账款": "S3 §2.3.3 保留",
    "采购": "模块与物料需求类型同指采购",
    "销售": "模块与订单类型同指销售",
    "销售税费": "侧栏条目即该子表",
    "联系人": "侧栏与 CRM 指联系人 DocType，与 Contact Person 同指；S3 改的 contact_display 已按 context 解开",
    "物料移动明细": "ste_detail 字段引用的就是该明细行",
    "替代物料": "按钮与 DocType 同指",
}


def contexts_for(source, demo, by_path):
    out = set()
    for ref in demo.get(source, []):
        m = re.match(r"(.+\.json):(\w+)$", ref)
        if m and m.group(1) in by_path:
            out.add(by_path[m.group(1)])
    return sorted(out)


def main():
    base = json.loads((ROOT / "Spike/P1S6R7-baseline-ts019b.json").read_text(encoding="utf-8"))
    demo = base["demo_surface"]
    by_path = {p.relative_to(bl.PROJECT).as_posix(): n for n, (p, _d) in bl.doctypes().items()}
    classes = json.loads((ROOT / "Spike/P1S6R7/collision_classes.json").read_text(encoding="utf-8"))
    rows, meta, table = [], {}, []
    for source, (target, mode, why) in DECISIONS.items():
        occupants = occ.occupants(target)
        if mode == "plain":
            keys = [(source, None)]
        elif mode == "ctx":
            keys = [(source, c) for c in contexts_for(source, demo, by_path)]
        else:
            keys = [(source, mode.split(":", 1)[1])]
        if not keys:
            raise SystemExit(f"no context found for {source!r}")
        for s, c in keys:
            rows.append([s, target, c] if c else [s, target])
            meta[s + (":" + c if c else "")] = {"basis": "演示线撞名", "named": False}
        table.append({"source": source, "target": target, "rows": [c or "（无 context）" for _s, c in keys], "occupants": occupants, "why": why})
    for group in classes["manual"]:
        if not any(s in DECISIONS for s in group["sources"]):
            table.append({"group": group["target"], "sources": group["sources"], "verdict": "同义保留",
                          "why": SYNONYM_NOTES.get(group["target"], "S3 §2.3 判同义或写法变体（S3 DEC-075）")})
    for group in classes["auto_synonym"]:
        table.append({"group": group["target"], "sources": group["sources"], "verdict": "同义保留", "why": "机械同义：大小写／单复数／缩写全称"})
    with (ROOT / "Spike/P1S6R7/collision_rows.csv").open("w", encoding="utf-8", newline="") as h:
        csv.writer(h, lineterminator="\n").writerows(rows)
    (ROOT / "Spike/P1S6R7/collision_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    (ROOT / "Spike/P1S6R7/collision_table.json").write_text(json.dumps(table, ensure_ascii=False, indent=1), encoding="utf-8")
    print(len(rows), "rows;", sum(1 for t in table if t.get("verdict")), "synonym groups")
    for t in table:
        if "rows" in t:
            print(t["source"], "→", t["target"], t["rows"], "occ:", t["occupants"])


if __name__ == "__main__":
    main()
