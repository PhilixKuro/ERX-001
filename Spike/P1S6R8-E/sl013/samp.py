import json,random,re,os
rows=json.load(open('t1rows.json',encoding='utf-8'))
random.seed(13019)
S=random.sample(rows,15)
B='D:/ERX-001/frappe-bench/apps/'
for k,src,tr in S:
    print('=== ',k,'->',tr,' @',src)
    p,_,loc=src.rpartition(':')
    if not p.endswith(('.json','.js','.py','.vue','.tsx','.ts','.html')): p,loc=src,''
    f=B+p
    if not os.path.exists(f): print('  nofile');continue
    L=open(f,encoding='utf-8',errors='replace').read().splitlines()
    if loc.isdigit():
        n=int(loc); print('\n'.join('  '+x[:160] for x in L[max(0,n-3):n+2]))
    else:
        # json fieldname
        for i,x in enumerate(L):
            if '"fieldname": "%s"'%loc in x:
                print('\n'.join('  '+y[:160] for y in L[max(0,i-6):i+8])); break
