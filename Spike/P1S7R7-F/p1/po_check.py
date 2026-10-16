import csv,sys,re
apps=sys.argv[1]
def load_po(p):
    d={};cur=None;mode=None;buf=''
    lines=open(p,encoding='utf-8').read().split('\n')
    mid=None;ms=None;state=None
    for l in lines+['']:
        if l.startswith('msgid '):
            mid=eval(l[6:]);state='id'
        elif l.startswith('msgstr '):
            ms=eval(l[7:]);state='str'
        elif l.startswith('"') and state:
            if state=='id': mid+=eval(l)
            else: ms+=eval(l)
        else:
            if state=='str' and mid: d[mid]=ms
            state=None
    return d
off={}
for a in ['frappe','erpnext','hrms','crm','insights','raven']:
    try: off[a]=load_po(f'{apps}/{a}/{a}/locale/zh.po')
    except Exception as e: print('noload',a,e)
csvd={r[0]:r[1] for r in csv.reader(open(f'{apps}/frappe_china/frappe_china/translations/zh.csv',encoding='utf-8')) if len(r)>=2}
for s in sys.argv[2:]:
    o={a:v[s] for a,v in off.items() if v.get(s)}
    print(repr(s),'| csv:',csvd.get(s),'| official:',o)
