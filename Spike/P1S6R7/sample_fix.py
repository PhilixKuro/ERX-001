"""TS-021 第 6 步：抽检不可用 3 条当场改，并按错误类型回扫同类（宿主 python -I -X utf8 跑，产出 rows/meta 供 apply_rows）。
类型 1 [意思错／用词]：物料成本价追溯调整（Repost Item Valuation、Stock Reposting Settings）一族官方用「追溯调整」，批量档写成「重过账」；
       会计凭证重过账（Repost Accounting Ledger）一族官方即「重过账」，不动。按出处文件分：repost_item_valuation.* 与 stock_reposting_settings.* 改。
类型 2 [术语]：Payment Reference 子表官方「付款凭据」，回扫「付款参考」。
类型 3 [意思错]：Vote Selection 与 Poll Option 同译「投票选项」，回扫源词不含 Option 却译「投票选项」的行。"""
import csv, importlib.util, json, re
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
s = importlib.util.spec_from_file_location("bl", ROOT / "Spike/P1S6R4-baseline.py"); bl = importlib.util.module_from_spec(s); s.loader.exec_module(bl)
refs = {}
for app in bl.APPS[:-1]:
    for e in bl.parse_po(bl.app_path(app) / "locale/main.pot"):
        refs[bl.entry_key(e)] = e["refs"]
rows = [r for r in csv.reader((ROOT / "frappe-bench/apps/frappe_china/frappe_china/translations/zh.csv").open(encoding="utf-8", newline="")) if r]
STOCK = re.compile(r"repost_item_valuation|stock_reposting_settings")
SPECIFIC = {"Reposting Item and Warehouse": "追溯调整的物料与仓库",
            "Grand Total must match sum of Payment References": "总计必须等于各付款凭据行金额之和",
            "Vote Selection": "所选选项"}
changed, scan = [], []
for r in rows:
    key = r[0] + (":" + r[2] if len(r) == 3 and r[2] else "")
    new = r[1]
    if key in SPECIFIC:
        new = SPECIFIC[key]
    elif any(STOCK.search(x) for x in refs.get(r[0], [])) and ("重过账" in new or "重新过账" in new):
        new = new.replace("重新过账", "追溯调整").replace("重过账", "追溯调整")
        scan.append({"type": "追溯调整", "key": key, "old": r[1], "new": new})
    elif "付款参考" in new:
        new = new.replace("付款参考", "付款凭据"); scan.append({"type": "付款凭据", "key": key, "old": r[1], "new": new})
    elif "投票选项" in new and "Option" not in r[0]:
        scan.append({"type": "投票选项（待人工）", "key": key, "old": r[1], "new": new})
    if new != r[1]:
        changed.append([*r[:1], new, *r[2:]])
with (ROOT / "Spike/P1S6R7/sample_fix_rows.csv").open("w", encoding="utf-8", newline="") as h:
    csv.writer(h, lineterminator="\n").writerows(changed)
meta = {r[0] + (":" + r[2] if len(r) == 3 and r[2] else ""): {"basis": "DEC-038（批量档重译；抽检回扫）", "named": False} for r in changed}
(ROOT / "Spike/P1S6R7/sample_fix_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
(ROOT / "Spike/P1S6R7/sample_backscan.json").write_text(json.dumps({"specific": SPECIFIC, "backscan": scan}, ensure_ascii=False, indent=1), encoding="utf-8")
print(len(changed), "rows changed;", len(scan), "back-scan hits")
for x in scan: print(" ", x["type"], repr(x["key"][:60]), "|", x["new"][:50])
