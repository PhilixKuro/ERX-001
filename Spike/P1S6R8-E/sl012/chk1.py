import csv,collections
B='D:/ERX-001/'
def rd(p): return list(csv.reader(open(p,encoding='utf-8',newline='')))
old=rd(B+'Spike/P1S6R8-E/sl012/old_zh.csv')
pr=rd(B+'Spike/P1S6R6-pruned.csv')
cur=rd(B+'frappe-bench/apps/frappe_china/frappe_china/translations/zh.csv')
T=lambda r: tuple(r)
co=collections.Counter(map(T,old)); cp=collections.Counter(map(T,pr))
print('old',len(old),'pruned',len(pr))
print('pruned subset of old:', all(co[k]>=v for k,v in cp.items()))
kept=co-cp
print('kept rows',sum(kept.values()))
cc=collections.Counter(map(T,cur))
print('kept rows still in cur (exact):',sum(min(v,cc[k]) for k,v in kept.items()))
missing=[k for k in kept if cc[k]==0]
print('kept not in cur exact',len(missing), missing[:10])
# pruned rows now back in cur exact
back=[k for k in cp if cc[k]>0]
print('pruned rows exactly present in cur', len(back))
