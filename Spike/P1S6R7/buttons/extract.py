"""Dump every add_custom_button / add_inner_button / add_menu_item call with label, group and callback text."""
import json, re, sys
from pathlib import Path

ROOT = Path(r"D:/ERX-001/frappe-bench/apps")
FILES = [
    "erpnext/erpnext/selling/doctype/sales_order/sales_order.js",
    "erpnext/erpnext/manufacturing/doctype/work_order/work_order.js",
    "erpnext/erpnext/buying/doctype/purchase_order/purchase_order.js",
    "erpnext/erpnext/stock/doctype/purchase_receipt/purchase_receipt.js",
    "erpnext/erpnext/accounts/doctype/purchase_invoice/purchase_invoice.js",
    "erpnext/erpnext/stock/doctype/stock_entry/stock_entry.js",
    "erpnext/erpnext/stock/doctype/delivery_note/delivery_note.js",
    "erpnext/erpnext/accounts/doctype/sales_invoice/sales_invoice.js",
    "erpnext/erpnext/manufacturing/doctype/production_plan/production_plan.js",
    "erpnext/erpnext/manufacturing/doctype/bom/bom.js",
    "erpnext/erpnext/manufacturing/doctype/job_card/job_card.js",
    "erpnext/erpnext/selling/doctype/quotation/quotation.js",
    "erpnext/erpnext/accounts/doctype/payment_entry/payment_entry.js",
    "erpnext/erpnext/public/js/controllers/transaction.js",
    "erpnext/erpnext/public/js/controllers/buying.js",
    "erpnext/erpnext/public/js/controllers/stock_controller.js",
    "erpnext/erpnext/public/js/controllers/accounts.js",
    "erpnext/erpnext/public/js/utils/sales_common.js",
]
PAT = re.compile(r"add_custom_button|add_inner_button|add_menu_item")
STR = re.compile(r'__\(\s*(["\'`])((?:\.|(?!\1).)*)\1(?:\s*,\s*(?:null|\[[^\]]*\]))?(?:\s*,\s*(["\'])((?:\.|(?!\3).)*)\3)?\s*\)')

def scan(rel):
    path = ROOT / rel
    lines = path.read_text(encoding="utf-8").splitlines()
    out = []
    for i, line in enumerate(lines):
        if not PAT.search(line):
            continue
        # call text: from match to balanced close paren
        start = line.index(PAT.search(line).group(0))
        text = ""
        depth = 0
        began = False
        j = i
        col = start
        while j < len(lines) and j < i + 60:
            seg = lines[j][col:] if j == i else lines[j]
            for ch in seg:
                text += ch
                if ch == "(":
                    depth += 1; began = True
                elif ch == ")":
                    depth -= 1
                    if began and depth == 0:
                        break
            else:
                text += "\n"; j += 1; continue
            break
        labels = STR.findall(text)
        out.append({"file": rel, "line": i + 1, "labels": [(m[1], m[3]) for m in labels], "text": text})
    return out

res = []
for f in FILES:
    p = ROOT / f
    if p.exists():
        res.extend(scan(f))
Path(sys.argv[1]).write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
for r in res:
    first = r["labels"][0] if r["labels"] else ("?", "")
    grp = r["labels"][-1][0] if len(r["labels"]) > 1 else ""
    body = " ".join(r["text"].split())[:200]
    print(f'{r["file"].split("/")[-1]}:{r["line"]} | {first[0]}{"::"+first[1] if first[1] else ""} | grp={grp} | {body}')
