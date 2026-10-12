import json, os, sys
os.chdir(r'D:\ERX-001')
r=json.load(open('Spike/P1S6R6-screens/result.json',encoding='utf-8'))
print('total',len(r),'pass',sum(1 for x in r if x.get('pass')))
keys=set()
for x in r: keys|=set(x.keys())
print(sorted(keys))
for x in r:
    if not x.get('pass'):
        print('FAIL',x['id'],'| en',x.get('english'),'| tr',x.get('traditional'),'| title',x.get('title_issues'),'| dd',x.get('default_data'),'| sb',x.get('sidebar_title'),x.get('sidebar_ok'),'| err',x.get('error'))
print('--- default_data nonempty')
for x in r:
    if x.get('default_data'): print(x['id'],x['default_data'],x['pass'])
print('--- missing screenshot')
for x in r:
    p=x.get('screenshot')
    if not p or not os.path.exists(p.replace('//','/')): print('MISSING',x['id'],p)
print('--- confirm')
for x in r:
    if x['id'].startswith('confirm-'):
        print(x['id'],x['pass'],{k:v for k,v in x.items() if k not in ('id','stage','state','english','traditional','title_issues','default_data','screenshot','traditional_samples','url','sidebar_ok','sidebar_title','pass')})
print('--- prefilled')
for x in r:
    if x['state']=='prefilled': print(x['id'],x['sidebar_title'],x['sidebar_ok'],x['url'])
print('--- sidebar not BF')
for x in r:
    if x.get('sidebar_title')!='Business Flow': print(x['id'],repr(x.get('sidebar_title')),x.get('sidebar_ok'))
