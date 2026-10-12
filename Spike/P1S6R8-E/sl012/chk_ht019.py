import csv,json,random,re
B='D:/ERX-001/'
def rd(p): return list(csv.reader(open(p,encoding='utf-8',newline='')))
def key(r): return r[0].replace('\n','\n')+(':'+r[2] if len(r)==3 and r[2] else '')
pr=rd(B+'Spike/P1S6R6-pruned.csv'); cur=rd(B+'frappe-bench/apps/frappe_china/frappe_china/translations/zh.csv')
curk={key(r) for r in cur}
merged=json.load(open('erx_merged.json',encoding='utf-8')); off=json.load(open('erx_official.json',encoding='utf-8'))
han=re.compile(r'[\u4e00-\u9fff]')
cand=sorted({key(r) for r in pr if key(r) in off and han.search(off[key(r)] or '') and key(r) not in curk})
allov=sorted({key(r) for r in pr if key(r) in off})
print('pruned keys overriding official:',len(allov),' with chinese official & not back in csv:',len(cand))
# full check
bad=[k for k in allov if k not in curk and merged.get(k)!=off[k]]
print('full check (not back in csv) mismatches:',len(bad),bad[:5])
back=[k for k in allov if k in curk]; print('override keys pruned but now back in csv:',len(back),back[:20])
random.seed(20261012); s=random.sample(cand,10)
out=[]
for k in s:
    pv=[r[1] for r in pr if key(r)==k][0]
    out.append({'key':k,'pruned_csv':pv,'official':off[k],'merged':merged.get(k),'eq':merged.get(k)==off[k]})
json.dump(out,open('ht019_sample.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
for o in out: print(o)
