import json, re
from pathlib import Path
pop = json.load(open('population.json', encoding='utf-8'))
off = json.load(open('erx_official.json', encoding='utf-8'))
apps = Path('D:/ERX-001/frappe-bench/apps')
doctypes = set()
for app in ['frappe', 'erpnext', 'crm', 'hrms', 'insights', 'raven']:
    for p in (apps / app / app).rglob('doctype/*/*.json'):
        if p.stem == p.parent.name:
            try: d = json.loads(p.read_text(encoding='utf-8'))
            except Exception: continue
            if d.get('doctype') == 'DocType': doctypes.add(d['name'])
rev = {}
for dt in doctypes:
    v = off.get(dt)
    if v and v != dt: rev.setdefault(v, []).append(dt)
hits = []
for app, rows in pop.items():
    for k, refs, t in rows:
        if t in rev and k not in rev[t] and k.casefold() not in {x.casefold() for x in rev[t]}:
            hits.append((app, k, t, rev[t]))
with open('coll.txt', 'w', encoding='utf-8') as f:
    f.write(f'{len(hits)}\n')
    for h in hits: f.write(repr(h) + '\n')
