import json,re
M=json.load(open('merged_zh.json',encoding='utf-8'))
L=open(r'D:/ERX-001/docs/01-需求摸底/S06-译名与导航/R07-代码/P1-S6-R7-D附表-按钮抽检.md',encoding='utf-8').read().splitlines()
rows=[]
for l in L:
    if not l.startswith('| `'): continue
    c=[x.strip() for x in re.split('(?<!' + chr(92)*2 + ')[|]',l)[1:-1]]
    if len(c)==7: rows.append(c)
print('rows',len(rows),'cols',set(len(c) for c in rows))
import collections
kinds=collections.Counter(re.search(r'〔(.*?)〕',c[3]).group(1) if re.search(r'〔(.*?)〕',c[3]) else '?' for c in rows)
print(kinds)
print(collections.Counter(c[4] for c in rows))
mis=[]
for c in rows:
    k=c[0].strip('`'); fin=c[5]
    v=M.get(k)
    if v!=fin: mis.append((k,c[1],fin,v))
print('mismatch',len(mis))
for m in mis: print(m)
print('--- 不一致 rows')
for c in rows:
    if c[4]!='一致': print(c[0],'|',c[1],'|',c[4],'|',c[5],'| now',M.get(c[0].strip('`')))
json.dump(rows,open('btnrows.json','w',encoding='utf-8'),ensure_ascii=False)
