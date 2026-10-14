# 只读：在容器内跑（需 frappe 环境但不连库）。列出 csv 中译文等于法定列头的键，以及其中被 NAMED_TERMS 豁免的
import csv, os, sys
os.chdir("/workspace/frappe-bench/sites")
sys.path.insert(0, "/workspace/frappe-bench/apps/frappe_china")
import frappe
frappe.init("erx.localhost")
try:
    from frappe_china.accounting.statements.labels import LEGAL_LABELS
    from frappe_china.tests.test_named_terms import NAMED_TERMS
    path = "/workspace/frappe-bench/apps/frappe_china/frappe_china/translations/zh.csv"
    rows = [r for r in csv.reader(open(path, encoding="utf-8", newline="")) if len(r) in (2, 3)]
    hits = [(r[0] + (":" + r[2] if len(r) == 3 and r[2] else ""), r[1]) for r in rows if r[1].strip() in LEGAL_LABELS and r[0] != r[1]]
    for key, target in hits:
        print("HIT", repr(key), "->", target, "| exempt by NAMED_TERMS" if key in NAMED_TERMS else "")
    print("total", len(hits), "LEGAL_LABELS", len(LEGAL_LABELS))
finally:
    frappe.destroy()
