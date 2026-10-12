import csv,collections,sys,importlib.util,json
B='D:/ERX-001/'
spec=importlib.util.spec_from_file_location('prune',B+'Spike/P1S6R6-csv-prune.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
cls=m.keep_keys()
print({k:len(v) for k,v in cls.items()})
def rd(p): return list(csv.reader(open(p,encoding='utf-8',newline='')))
old=rd(B+'Spike/P1S6R8-E/sl012/old_zh.csv'); pr=rd(B+'Spike/P1S6R6-pruned.csv')
allk=set().union(*cls.values())
cp=collections.Counter(map(tuple,pr)); co=collections.Counter(map(tuple,old)); kept=co-cp
nk=[r for r in kept if m.row_key(list(r)) not in allk]
print('kept rows not in current classes',len(nk),nk[:10])
own=cls['own']
po=[r for r in pr if m.row_key(r) in own]
print('pruned rows whose key in current own',len(po),[r[0] for r in po][:20])
pn=[r for r in pr if m.row_key(r) in cls['named']]
print('pruned rows in current named',len(pn),[r[0] for r in pn][:40])
pov=[r for r in pr if m.row_key(r) in cls['override']]
print('pruned rows in current overrides',len(pov))
# rerun prune dry on old
k2,d2,c2=m.prune(old); print('re-prune old with current classes',c2,len(k2))
