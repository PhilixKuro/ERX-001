import sys,json
def apply(p, reps):
    raw=open(p,'rb').read().decode('utf-8')
    crlf='\r\n' in raw
    s=raw.replace('\r\n','\n')
    for a,b in reps:
        if a not in s: sys.exit(f'MISSING in {p}: {a[:80]!r}')
        s=s.replace(a,b)
    if crlf: s=s.replace('\n','\r\n')
    open(p,'wb').write(s.encode('utf-8'))
