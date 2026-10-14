"""F 分片 5：csv 全表结构与术语一致性扫描（只读）。python -I -X utf8 scan_csv.py"""
import csv, re, sys, importlib.util
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
CSV = ROOT / "frappe-bench/apps/frappe_china/frappe_china/translations/zh.csv"
rows = list(csv.reader(CSV.open(encoding="utf-8", newline="")))
print("rows", len(rows), "cols", {len(r) for r in rows})
key = lambda r: (r[0].casefold(), r[2] if len(r) == 3 else "")
print("unsorted pairs", sum(1 for a, b in zip(rows, rows[1:]) if key(a) > key(b)))
norm = [r[0].replace("\n", "\n") + (":" + r[2] if len(r) == 3 and r[2] else "") for r in rows]
from collections import Counter
print("dup (frappe-normalised)", [k for k, c in Counter(norm).items() if c > 1])
CJK = re.compile(r"[㐀-䶿一-鿿]")
nocjk = [r for r in rows if not CJK.search(r[1])]
print("targets without CJK", len(nocjk)); [print("   ", r) for r in nocjk]
same = [r for r in rows if r[0] == r[1]]
print("target == source", len(same))
TW = ["设定", "讯息", "档案", "专案", "资料库", "帐号", "帐户", "萤幕", "列印", "预设", "登入", "登出", "软体", "网路", "储存", "选单", "程式", "伺服器", "范本", "使用者", "介面", "影片", "执行绪", "数位", "支援", "物件", "汇入", "汇出", "回覆", "撷取", "透过", "连结", "资讯", "邮件地址"]
for w in TW:
    hit = [r for r in rows if w in r[1]]
    if hit:
        print(f"TW? {w}: {len(hit)}", [ (r[0][:50], r[1][:40]) for r in hit[:4]])
TERMS = [
    (r"\bItems?\b", "项目", r"Project"),
    (r"\bTimesheet|Time Sheet", "工时表", None),
    (r"\bJob Card", "作业卡|工卡|工作卡", None),
    (r"\bStock Entry", "库存凭证|库存分录|库存条目|库存录入", None),
    (r"\bJournal Entry", "日记账分录|会计分录|日记帐", None),
    (r"\bPayment Entry", "付款凭证|付款分录|付款条目", None),
    (r"\bDelivery Note", "交货单|送货单|发货单", None),
    (r"\bLeads?\b", "潜在客户|销售线索", None),
    (r"\bDeals?\b", "交易", None),
    (r"\bWork Order", "工作订单|作业单", None),
    (r"\bBOM\b", "BOM", None),
    (r"\bWarehouse", "货仓|库房", None),
    (r"\bCost Center", "成本中心", None),
]
for src_re, bad, exclude in TERMS:
    hit = [r for r in rows if re.search(src_re, r[0]) and re.search(bad, r[1]) and not (exclude and re.search(exclude, r[0]))]
    print(f"TERM {src_re} -> /{bad}/: {len(hit)}")
    for r in hit[:6]:
        print("    ", r[0][:70], "=>", r[1][:50])
# 全角/半角标点混用：中文句里半角逗号句号
half = [r for r in rows if re.search(r"[一-鿿],[一-鿿]|[一-鿿]\.(\s|$)", r[1])]
print("half-width punct inside CJK", len(half)); [print("   ", r[0][:60], "=>", r[1][:60]) for r in half[:8]]
