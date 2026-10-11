import csv, re, json
P = "D:/ERX-001/frappe-bench/apps/frappe_china/frappe_china/translations/zh.csv"
rows = list(csv.reader(open(P, encoding="utf-8", newline="")))
TRAD = set("們這個來為與說時從對會沒將麼過還學國開關單據帳戶項設請選擇資訊確認儲刪編輯顯訊錯誤檔載輸無條數稅計許啟聯絡統員機頁應類庫視記錄號碼實際總額貨倉價產務廠辦購賣")
STOP = {"is","the","to","a","of","and","for","in","on","with","you","your","this","be","are","can","not","will","from","by","an","or","if","it","that","has","have","do"}
out = open("scan_csv2.txt","w",encoding="utf-8")
trad=[];garb=[]
for i,r in enumerate(rows,1):
    if len(r)<2: continue
    s,t=r[0],r[1]
    if any(c in TRAD for c in t): trad.append(i)
    if re.search(r"[\u4e00-\u9fff]", t):
        clean = re.sub(r"<[^>]+>|\{[^}]*\}|%\([^)]*\)s|\*\*[^*]*\*\*","",t)
        words=[w.lower() for w in re.findall(r"[A-Za-z]+", clean)]
        if any(w in STOP for w in words): garb.append(i)
out.write(f"rows {len(rows)} trad {len(trad)} cjk+english-stopword {len(garb)}\n")
out.write("== garb (first 60)\n")
for i in garb[:60]: out.write(f"{i}\t{rows[i-1][0][:90]!r}\t{rows[i-1][1][:90]!r}\n")
out.write("== trad (first 40)\n")
for i in trad[:40]: out.write(f"{i}\t{rows[i-1][0][:80]!r}\t{rows[i-1][1][:80]!r}\n")
json.dump({"trad":trad,"garb":garb},open("scan_csv2.json","w"))
# where do these lines sit: range distribution
import collections
b=collections.Counter(i//500*500 for i in garb); out.write("garb by 500-line bucket "+str(sorted(b.items()))+"\n")
b=collections.Counter(i//500*500 for i in trad); out.write("trad by bucket "+str(sorted(b.items()))+"\n")
