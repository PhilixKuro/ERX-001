import json,re,sys,random
M=json.load(open('merged_zh.json',encoding='utf-8'))
L=open(r'D:/ERX-001/docs/01-需求摸底/S06-译名与导航/R07-代码/P1-S6-R7-D附表-演示线定词.md',encoding='utf-8').read().splitlines()
han=re.compile(r'[\u4e00-\u9fff]')
rows=[]
for l in L[4:469]:
    if not l.startswith('| `'): continue
    m=re.match(r'\| `(.*?)` \| (.*?) \| (.*) \|$',l)
    if not m: print('BAD',l);continue
    rows.append(m.groups())
print('rows',len(rows))
bad=[];miss=[];diff=[]
for k,src,tr in rows:
    k2=k.replace('\|','|')
    v=M.get(k2)
    if v is None: miss.append(k2); continue
    if not han.search(v): bad.append((k2,v))
    if v!=tr.replace('\|','|'): diff.append((k2,tr,v))
print('miss',len(miss),miss[:20]);print('nonzh',len(bad),bad[:20]);print('diff',len(diff));
for d in diff[:30]: print(d)
json.dump(rows,open('t1rows.json','w',encoding='utf-8'),ensure_ascii=False,indent=0)
