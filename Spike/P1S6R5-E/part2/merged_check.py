import importlib.util
spec = importlib.util.spec_from_file_location("bl", "D:/ERX-001/Spike/P1S6R4-baseline.py")
bl = importlib.util.module_from_spec(spec); spec.loader.exec_module(bl)
merged, plain = bl.merged_dict()
keys = ["Is Paid","Paid Amount","Paid Amount:Purchase Invoice","Paid Amount:Sales Invoice","Paid Amount:Payment Entry","Paid Amount:Payment Schedule","Received Amount","Received Amount:Payment Entry","Payment Amount","Payment Type","Type of Payment","Mode of Payment","Mode Of Payment","Payment Mode","Payment Method","Mode of Payments","Modes of Payment","Outstanding Amount","Outstanding","Outward","Inward","Unpaid","Paid","Unpaid:Sales Invoice","Unpaid:Purchase Invoice","Stock Ledger","Stock Ledger Entry","Stock Balance","Stock Ledger Invariant Check","Timesheet","Timesheets","Dr","Item","Settings","Qualification"]
o=open("merged_check.txt","w",encoding="utf-8")
for k in keys: o.write(f"{k!r} -> {merged.get(k)!r}\n")
# occupants of target words
for t in ["收付款方式","是否已付","到账金额","未结金额","库存台账","物料凭证","借方","核销明细","工时表"]:
    o.write(f"OCC {t}: {sorted(k for k in plain if merged.get(k,'').strip()==t)[:15]}\n")
n=sum(1 for k,v in merged.items() if "工时表" in v); o.write(f"merged entries containing 工时表: {n}\n")
for k,v in merged.items():
    if "工时表" in v: o.write(f"  {k!r}: {v!r}\n")
