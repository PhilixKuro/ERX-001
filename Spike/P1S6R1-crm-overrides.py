import os,csv,collections,sys
exec(open(__file__.replace('P1S6R1-crm-overrides.py','P1S6R1-merged-collisions.py'),encoding='utf-8').read().split('order=')[0])
order=['frappe','erpnext','crm','hrms','insights','raven','frappe_china']
base={}
for a in ['frappe','erpnext']:
    for e in parse(f'apps/{a}/{a}/locale/zh.po'):
        if not e['ctx']: base[e['id']]=e['str']
cnt=collections.Counter();ex=collections.defaultdict(list)
for a in ['crm','hrms','insights']:
    for e in parse(f'apps/{a}/{a}/locale/zh.po'):
        if e['ctx']: continue
        k=e['id']
        if k in base and base[k].strip()!=e['str'].strip():
            cnt[a]+=1; ex[a].append((k,base[k],e['str']))
print(dict(cnt))
for a in ex:
    for t in ex[a][:8]: print(a,t)
