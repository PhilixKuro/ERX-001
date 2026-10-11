import csv, re, json, sys
P = "D:/ERX-001/frappe-bench/apps/frappe_china/frappe_china/translations/zh.csv"
rows = list(csv.reader(open(P, encoding="utf-8", newline="")))
print("rows", len(rows))
# traditional-only chars sample
TRAD = set("們這個來為與說時從對會沒將麼們過還學們國開關單據帳戶項設請選擇資訊確認儲存刪除編輯顯示訊錯誤檔載輸無條數據稅計許使用者啟聯絡統員機選單頁應類別庫視窗")
SIMP_STOP = {"is","the","to","a","of","and","for","in","on","with","you","your","this","be","are","can","not","will","from","by","an","or","if","it"}
trad = []; mixed = []; garb = []
for i, r in enumerate(rows, 1):
    if len(r) < 2: continue
    s, t = r[0], r[1]
    if any(c in TRAD for c in t): trad.append(i)
    if re.search(r"[\u4e00-\u9fff]", t):
        words = [w.lower() for w in re.findall(r"[A-Za-z]{2,}", re.sub(r"<[^>]+>|\{[^}]*\}|%\([^)]*\)s", "", t))]
        stop = [w for w in words if w in SIMP_STOP]
        if stop: garb.append(i)
        elif len(words) >= 3: mixed.append(i)
print("trad-like", len(trad)); print("cjk+english stopwords", len(garb)); print("cjk + >=3 eng words", len(mixed))
# section ordering check: find runs sorted
keys = [r[0].lower() for r in rows if len(r)>=2]
breaks = [i for i in range(1,len(keys)) if keys[i] < keys[i-1]]
print("order breaks", len(breaks), breaks[:20])
json.dump({"trad":trad,"garb":garb,"mixed":mixed}, open("scan_csv.json","w"), indent=0)
for i in garb[:25]: print(i, rows[i-1][:2])
print("---trad sample")
for i in trad[:10]: print(i, rows[i-1][:2])
