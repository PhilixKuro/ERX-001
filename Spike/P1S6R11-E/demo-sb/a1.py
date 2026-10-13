import json,sys
new=json.load(open(sys.argv[1],encoding='utf-8'))
old=json.load(open(sys.argv[2],encoding='utf-8'))
def screens(d):
    return d if isinstance(d,list) else d.get('screens',d)
print(type(new), (list(new.keys()) if isinstance(new,dict) else ''))
ns=screens(new); os_=screens(old)
print(len(ns),len(os_))
nid=[s['id'] for s in ns]; oid=[s['id'] for s in os_]
print('dup new',len(nid)-len(set(nid)))
print('added',[i for i in nid if i not in oid])
print('removed',[i for i in oid if i not in nid])
for s in ns:
    if 'kind_expected' in s: print(s['id'],s['kind_expected'],{k:v for k,v in s.items() if k not in('id',)})
# changed besides kind_expected
od={s['id']:s for s in os_}
for s in ns:
    if s['id'] in od:
        a=dict(s);a.pop('kind_expected',None)
        if a!=od[s['id']]: print('CHANGED',s['id'])
