import json,re,sys,os
from collections import defaultdict
M=json.load(open('merged_zh.json',encoding='utf-8'))
base=sys.argv[1]
d=json.load(open(base,encoding='utf-8'))['demo_collisions']
P='D:/ERX-001/'
cache={}
def dtname(p):
    if p in cache: return cache[p]
    n=None
    try:
        j=json.load(open(P+p,encoding='utf-8'))
        if isinstance(j,dict) and j.get('doctype')=='DocType': n=j.get('name')
    except Exception: pass
    cache[p]=n; return n
fr=re.compile(r'(.+\.json):(\w+)$')
still=[];res=[]
for tgt,g in sorted(d.items()):
    shown=defaultdict(lambda: defaultdict(list))
    for s,refs in g['visible'].items():
        for r in refs:
            m=fr.match(r); dt=dtname(m.group(1)) if m else None
            v=(M.get(f'{s}:{dt}') if dt else None) or M.get(s) or s
            shown[v.strip()][s].append(r)
    cl={v:dict(x) for v,x in shown.items() if len(x)>=2}
    (still if cl else res).append({'target':tgt,'clashes':cl})
print(base,'groups',len(d),'still',len(still),'resolved',len(res))
json.dump({'still':still,'resolved':[r['target'] for r in res]},open(os.path.basename(base)+'.eff.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
