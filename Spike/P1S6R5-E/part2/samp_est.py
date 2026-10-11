import csv, re
rows = list(csv.reader(open("sample.out.csv",encoding="utf-8-sig")))[1:]
TRAD = set("們這個來為與說時從對會沒將麼過還學國開關單據帳戶項設請選擇資訊確認儲刪編輯顯訊錯誤檔載輸無條數稅計許啟聯絡統員機頁應類庫視記錄號碼實際總額貨倉價產務廠辦購賣參偵測轉載")
WBW = re.compile(r"[\u4e00-\u9fff] (是|至|带|的|不|与|中|从|用于|有|您|此)( |$|[.,])|[\u4e00-\u9fff]{1,3} [\u4e00-\u9fff]{1,3} [\u4e00-\u9fff]{1,3}")
o=open("samp_est.txt","w",encoding="utf-8")
t=w=0
for i,r in enumerate(rows,1):
    tr = any(c in TRAD for c in r[3]); wb = bool(WBW.search(r[3]))
    t+=tr; w+=wb and not tr
    if wb and not tr: o.write(f"WBW {i} [{r[0]}] {r[1][:80]!r} -> {r[3][:80]!r}\n")
o.write(f"trad {t}; word-by-word {w}\n")
