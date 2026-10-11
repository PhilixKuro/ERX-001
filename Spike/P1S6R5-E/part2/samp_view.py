import ast, csv, re
src = open("D:/ERX-001/Spike/P1S6R4-repair-batch.py",encoding="utf-8").read()
tree = ast.parse(src)
for n in tree.body:
    if isinstance(n, ast.Assign) and getattr(n.targets[0],"id","")=="REPAIRS":
        R = ast.literal_eval(n.value)
rows = list(csv.reader(open("sample.out.csv",encoding="utf-8-sig")))[1:]
keys = {r[1] for r in rows}
o = open("samp_view.txt","w",encoding="utf-8")
o.write(f"REPAIRS {len(R)}; in sample {len(set(R)&keys)}; outside sample {len(set(R)-keys)}\n")
TRAD = set("們這個來為與說時從對會沒將麼過還學國開關單據帳戶項設請選擇資訊確認儲刪編輯顯訊錯誤檔載輸無條數稅計許啟聯絡統員機頁應類庫視記錄號碼實際總額貨倉價產務廠辦購賣")
for i,r in enumerate(rows,1):
    flag = "TRAD" if any(c in TRAD for c in r[3]) else ("REP" if r[1] in R else "")
    if i % 5 == 0 or flag == "TRAD":
        o.write(f"{i} [{r[0]}] {flag} EN={r[1][:110]!r}\n      ZH={r[3][:110]!r}\n")
