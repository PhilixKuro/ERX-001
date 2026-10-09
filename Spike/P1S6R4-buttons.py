"""Extract and classify data-changing demo-line custom buttons for review."""
from __future__ import annotations

import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ERP = ROOT / "frappe-bench/apps/erpnext/erpnext"
OUT = ROOT / "Spike/P1S6R4-buttons.csv"

DOCS = {
    "sales_order", "work_order", "purchase_order", "purchase_receipt", "purchase_invoice",
    "stock_entry", "delivery_note", "sales_invoice", "production_plan", "bom",
    "job_card", "quotation", "payment_entry", "journal_entry",
}
BUTTON = re.compile(r'add_custom_button\(\s*__\(\s*["\']([^"\']+)["\']\s*\)', re.MULTILINE)
ACTION = re.compile(r"(?:frappe\.model\.open_mapped_doc|frappe\.call|frm\.save|frm\.submit|frm\.cancel|frm\.set_value|make_\w+|return_doc|submit_doc|cancel_doc|delete_doc)")


def main():
    result = {}
    for path in sorted(ERP.rglob("*.js")):
        if path.parent.name not in DOCS or path.stem != path.parent.name:
            continue
        source = path.read_text(encoding="utf-8", errors="ignore")
        for match in BUTTON.finditer(source):
            label = match.group(1)
            line = source.count("\n", 0, match.start()) + 1
            context = source[match.end(): source.find("\n", match.end()) + 1]
            result.setdefault(label, []).append((path.relative_to(ROOT).as_posix(), line, context.strip()))
    with OUT.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["源词", "源码位置", "调用行后续", "是否改数据", "实际动作", "判定", "定稿译名"])
        for label in sorted(result):
            refs = result[label]
            evidence = "； ".join(f"{path}:{line}" for path, line, _ in refs)
            contexts = "； ".join(context for _, _, context in refs if context)
            changing = bool(ACTION.search(contexts)) or label in {
                "Update Items", "Submit", "Cancel", "Delete", "Return", "Hold", "Close", "Re-open",
                "Reserve", "Unreserve", "Payment", "Purchase Receipt", "Delivery Note", "Sales Invoice",
                "Purchase Order", "Work Order", "Stock Entry", "Journal Entry", "Quotation", "Material Request",
            }
            if changing:
                writer.writerow([label, evidence, contexts, "是", "见源码调用", "待审", ""])
        common = [
            ("Save", "frappe-bench/apps/frappe/frappe/public/js/frappe/form/toolbar.js", "保存当前文档"),
            ("Submit", "frappe-bench/apps/frappe/frappe/public/js/frappe/form/toolbar.js", "提交当前文档"),
            ("Cancel", "frappe-bench/apps/frappe/frappe/public/js/frappe/form/toolbar.js", "取消当前文档"),
            ("Amend", "frappe-bench/apps/frappe/frappe/public/js/frappe/form/toolbar.js", "基于已取消文档新建修订单"),
            ("Delete", "frappe-bench/apps/frappe/frappe/public/js/frappe/form/toolbar.js", "删除当前文档"),
        ]
        for label, path, action in common:
            writer.writerow([label, path, action, "是", action, "一致", ""])
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
