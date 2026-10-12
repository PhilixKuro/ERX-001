import json
e=json.load(open('baseline.json.eff.json',encoding='utf-8'))
t=json.load(open('../../P1S6R7/collision_table.json',encoding='utf-8'))
M=json.load(open('merged_zh.json',encoding='utf-8'))
syn={}
for x in t:
    if 'group' in x: syn[frozenset(x['sources'])]=x
het=[x for x in t if 'source' in x]
print('syn rows',len(syn),'het rows',len(het))
nomatch=[]
for g in e['still']:
    for v,src in g['clashes'].items():
        k=frozenset(src)
        if k in syn: continue
        # subset match
        sup=[s for s in syn if k<=s]
        if sup: continue
        nomatch.append((v,list(src)))
print('still clash entries not covered by synonym table:',len(nomatch))
for n in nomatch: print(' ',n)
# het definitions now distinct?
print('--- het')
for x in het:
    print(x['source'],'|',x['target'],'|',x['rows'],'| now:',M.get(x['source']), [M.get(x['source']+':'+r) for r in x['rows'] if r!='（无 context）'])
