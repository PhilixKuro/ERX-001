import json,sys
sys.stdout.reconfigure(encoding='utf-8')
r=json.load(open(sys.argv[1],encoding='utf-8'))
print(type(r), list(r.keys())[:20] if isinstance(r,dict) else len(r))
rs=r if isinstance(r,list) else (r.get('results') or r.get('screens'))
print(len(rs))
print(json.dumps(rs[0],ensure_ascii=False)[:1500])
