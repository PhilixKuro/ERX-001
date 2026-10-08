import os,csv,sys,collections
def parse(p):
    ents=[];cur=None;field=None
    for line in open(p,encoding='utf-8'):
        line=line.rstrip('\n')
        if line.startswith('msgctxt '):
            cur={'ctx':eval(line[8:]),'id':'','str':''};ents.append(cur);field=None;continue
        if line.startswith('msgid '):
            if cur is None or field is not None:
                cur={'ctx':'','id':'','str':''};ents.append(cur)
            field='id';cur['id']+=eval(line[6:])
        elif line.startswith('msgstr '):
            field='str';cur['str']+=eval(line[7:])
        elif line.startswith('"') and cur is not None and field:
            cur[field]+=eval(line)
        elif not line.strip():
            cur=None;field=None
    return [e for e in ents if e['id'] and e['str']]
order=['frappe','erpnext','crm','hrms','insights','raven','frappe_china']
d={};src={}
for a in order:
    p=f'apps/{a}/{a}/locale/zh.po'
    if os.path.exists(p):
        for e in parse(p):
            if e['ctx']: continue
            d[e['id']]=e['str'];src[e['id']]=a
    c=f'apps/{a}/{a}/translations/zh.csv'
    if os.path.exists(c):
        for r in csv.reader(open(c,encoding='utf-8')):
            if len(r)==2: d[r[0]]=r[1];src[r[0]]=a
g=collections.defaultdict(set)
for k,v in d.items(): g[v.strip()].add(k)
coll={v:ks for v,ks in g.items() if len(ks)>=2}
print('entries',len(d),'collision groups',len(coll))
# groups involving a source from a non-frappe/erpnext app
inv=collections.Counter()
for v,ks in coll.items():
    apps={src[k] for k in ks}
    for a in apps-{'frappe','erpnext'}: inv[a]+=1
print('groups touching each new app',dict(inv))
# new collisions: groups that contain at least one source from a non-frappe/erpnext app
new=[(v,ks) for v,ks in coll.items() if any(src[k] not in ('frappe','erpnext') for k in ks)]
print('groups with app-sourced member',len(new))
for v,ks in sorted(new,key=lambda x:-len(x[1]))[:12]:
    print(v,'<-',sorted((k,src[k]) for k in ks)[:5])
