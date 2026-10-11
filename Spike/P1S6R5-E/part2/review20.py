import importlib.util, csv, json, random, re
from pathlib import Path
OUT = Path("D:/ERX-001/Spike/P1S6R5-E/part2")
spec = importlib.util.spec_from_file_location("smp", "D:/ERX-001/Spike/P1S6R4-sample.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
batch = m.population()
STOP = {"is","the","to","a","of","and","for","in","on","with","you","your","this","be","are","can","not","will","from","by","an","or","if","it","that","has","have","do"}
TRAD = set("們這個來為與說時從對會沒將麼過還學國開關單據帳戶項設請選擇資訊確認儲刪編輯顯訊錯誤檔載輸無條數稅計許啟聯絡統員機頁應類庫視記錄號碼實際總額貨倉價產務廠辦購賣")
def bad(t):
    clean = re.sub(r"<[^>]+>|\{[^}]*\}|%\([^)]*\)s","",t)
    words=[w.lower() for w in re.findall(r"[A-Za-z]+", clean)]
    g = bool(re.search(r"[\u4e00-\u9fff]",t)) and any(w in STOP for w in words)
    return g, any(c in TRAD for c in t), "中文：" in t or "???" in t
sample_keys = {row[1] for row in csv.reader(open(OUT/"sample.out.csv",encoding="utf-8-sig"))}
o = open(OUT/"review20.txt","w",encoding="utf-8")
tot = {"n":0,"garb":0,"trad":0,"ph":0}; samp={"n":0,"garb":0,"trad":0,"ph":0}
allrows=[]
for app, rows in batch.items():
    for key, refs, t in rows:
        g,tr,ph = bad(t)
        d = samp if key in sample_keys else tot
        d["n"]+=1; d["garb"]+=g; d["trad"]+=tr; d["ph"]+=ph
        if key not in sample_keys: allrows.append((app,key,refs,t))
o.write(f"non-sample population {tot}\nsample {samp}\n")
rng = random.Random(42)
pick = rng.sample(allrows, 20)
for i,(app,key,refs,t) in enumerate(pick,1):
    o.write(f"\n#{i} [{app}] {refs[:1]}\n  EN: {key[:200]!r}\n  ZH: {t[:200]!r}\n")
