import json,sys,os
sys.stdout.reconfigure(encoding='utf-8')
fin=json.load(open('P1S6R9-screens/result.json',encoding='utf-8'))
r1=json.load(open('P1S6R9/ts036/result-run1.json',encoding='utf-8'))
print('final',len(fin),'pass',sum(1 for x in fin if x.get('pass') is True))
for k in ('english','traditional','title_issues'):
    print(k,'nonempty',[x['id'] for x in fin if x.get(k)])
print('sidebar_ok false',[x['id'] for x in fin if x.get('sidebar_ok') is not True])
print('keys union',sorted(set().union(*[x.keys() for x in fin])))
print('default_data',[(x['id'],x['default_data']) for x in fin if x.get('default_data')])
ids=[x['id'] for x in fin]; print('dup',len(ids)-len(set(ids)))
sc=json.load(open('P1S6R9-screens.json',encoding='utf-8'))['screens']
print('order same as screens.json',ids==[s['id'] for s in sc])
missing=[x['screenshot'] for x in fin if x.get('screenshot') and not os.path.exists('../'+x['screenshot'])]
print('missing png',missing)
R7=['17-work-order-list','19-job-card-list','22-sales-invoice-list','report-Stock Ledger','report-General Ledger','13-opening-to-ledger','17-work-order-saved','19-job-card-saved','20-stock-entry-manufacture','21-sales-order-status-menu','crm-leads','crm-deals','crm-dashboard','crm-lead-detail','crm-deal-detail']
fd={x['id']:x for x in fin}
for i in R7:
    x=fd.get(i); print(i, None if x is None else (x['pass'],x['english'],x['traditional'],x['title_issues']))
# dialogs
for x in fin:
    if 'dialog_kind' in x or 'docstatus_before' in x or 'kind_ok' in x:
        print('DLG',x['id'],{k:x.get(k) for k in x if k.startswith(('dialog','docstatus','kind','error'))})
print('run1 len',len(r1),'pass',sum(1 for x in r1 if x.get('pass') is True))
r1d={x['id']:x for x in r1}
print('run1 order==final',[x['id'] for x in r1]==ids)
diff=[i for i in ids if json.dumps(r1d.get(i),sort_keys=True)!=json.dumps(fd[i],sort_keys=True)]
print('differing ids',diff)
for i in diff:
    print('RUN1',json.dumps(r1d.get(i),ensure_ascii=False)[:800]); print('FIN',json.dumps(fd[i],ensure_ascii=False)[:800])
