import json, os
os.chdir(r'D:\ERX-001')
for f in ['Spike/P1S6R6-screens/result.json','Spike/P1S6R7/ts023/hits/result.json']:
    if not os.path.exists(f): print('no',f); continue
    r=json.load(open(f,encoding='utf-8'))
    print('=====',f,len(r))
    for x in r:
        if x.get('hit_entries'):
            print('##',x['id'])
            seen=set()
            for e in x['hit_entries']:
                k=(e.get('kind'),e.get('value'))
                if k in seen: continue
                seen.add(k)
                print('   ',json.dumps(e,ensure_ascii=False)[:300])
