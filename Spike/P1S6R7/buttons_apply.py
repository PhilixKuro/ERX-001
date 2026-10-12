"""TS-020 第 4 步：按钮抽检定稿写 csv、进 NAMED_TERMS，覆盖官方的进 OVERRIDES（依据「按钮抽检 IT-010」）。宿主 python -I -X utf8 跑，产出 rows/meta 供 apply_rows。"""
import csv, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
FINAL = {  # 源词 → 定稿；改无 context 行前已查其余出处（buttons.md「调用行」列），均同义
    "Update Items": "变更明细",
    "Update Rate as per Last Purchase": "按最近采购价更新单价",
    "Return / Credit Note": "退货/红字发票",
    "Return / Debit Note": "退货/采购红字发票",
    "Internal Purchase Invoice": "内部采购发票",
    "Inter Company Purchase Invoice": "公司间采购发票",
    "Internal Purchase Receipt": "内部采购入库",
    "Inter Company Purchase Receipt": "公司间采购入库",
}
rows = [[k, v] for k, v in FINAL.items()]
meta = {k: {"basis": "按钮抽检 IT-010", "named": True} for k in FINAL}
with (ROOT / "Spike/P1S6R7/buttons_rows.csv").open("w", encoding="utf-8", newline="") as h:
    csv.writer(h, lineterminator="\n").writerows(rows)
(ROOT / "Spike/P1S6R7/buttons_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
print(len(rows), "rows")
