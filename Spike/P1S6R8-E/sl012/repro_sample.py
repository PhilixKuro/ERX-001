import importlib.util, csv, json, sys
R='D:/ERX-001/'
s=importlib.util.spec_from_file_location('samp',R+'Spike/P1S6R4-sample.py'); m=importlib.util.module_from_spec(s); s.loader.exec_module(m)
batch=m.population()
sel,quotas=m.stratified_sample(batch)
print('pop',{a:len(r) for a,r in batch.items()},'total',sum(len(r) for r in batch.values()));print('quotas',quotas)
orig=list(csv.reader(open(R+'Spike/P1S6R6-sample.out.csv',encoding='utf-8-sig',newline='')))[1:]
ok=[(a,k) for a,(k,refs,t) in sel]; ok2=[(r[0],r[1]) for r in orig]
print('same keys & order as D sample:', ok==ok2, 'set equal:', set(ok)==set(ok2))
# translation now vs sample
cur={(a,k):t for a,(k,refs,t) in sel}
diff=[(r[1],r[3],cur.get((r[0],r[1]))) for r in orig if cur.get((r[0],r[1]))!=r[3]]
print('translation differs now vs sample file:',len(diff)); [print('  ',d) for d in diff]
json.dump({a:[list(x) for x in rows] for a,rows in batch.items()},open('population.json','w',encoding='utf-8'),ensure_ascii=False)
