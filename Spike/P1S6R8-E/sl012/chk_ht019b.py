import csv,json,random,re
B='D:/ERX-001/'
def rd(p): return list(csv.reader(open(p,encoding='utf-8',newline='')))
def key(r): return r[0].replace('\n','\n')+(':'+r[2] if len(r)==3 and r[2] else '')
pr=rd(B+'Spike/P1S6R6-pruned.csv'); cur=rd(B+'frappe-bench/apps/frappe_china/frappe_china/translations/zh.csv')
curd={key(r):r[1] for r in cur}
merged=json.load(open('erx_merged.json',encoding='utf-8')); off=json.load(open('erx_official.json',encoding='utf-8'))
han=re.compile(r'[\u4e00-\u9fff]')
allov=sorted({key(r) for r in pr if key(r) in off})
ch=[k for k in allov if han.search(off[k] or '')]
neq=[k for k in allov if off[k]!=k.split(':')[0]]
print('official != source among 161:',len(neq))
rest=[k for k in allov if k not in ch and k not in curd]
random.seed(20261012); s=ch+random.sample(rest,7)
out=[]
for k in s:
    pv=[r[1] for r in pr if key(r)==k][0]
    out.append({'key':k,'pruned_csv':pv,'official':off[k],'merged_erx':merged.get(k),'eq':merged.get(k)==off[k]})
for k in ['Lft','old_parent']:
    out.append({'key':k,'back_in_csv':curd.get(k),'official':off.get(k),'merged_erx':merged.get(k),'pruned_csv':[r[1] for r in pr if key(r)==k]})
json.dump(out,open('ht019_sample.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
for o in out: print(o)
