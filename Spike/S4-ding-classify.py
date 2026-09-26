import json, os, glob, unicodedata
BENCH = r'D:\ERX-001\frappe-bench\apps'
PS = r'D:\ERX-001\Reference\zelin-tech-erpnext_china\erpnext_china\fixtures\property_setter.json'
index = {}
for app in ('frappe','erpnext'):
    for path in glob.glob(os.path.join(BENCH, app, '**','doctype','*','*.json'), recursive=True):
        base = os.path.basename(path)[:-5]; parent = os.path.basename(os.path.dirname(path))
        if base != parent: continue
        try: d = json.load(open(path, encoding='utf-8'))
        except Exception: continue
        if d.get('doctype') == 'DocType': index.setdefault(d.get('name'), d)

def has_cjk(s):
    return any('\u4e00' <= ch <= '\u9fff' for ch in (s or ''))

recs = [d for d in json.load(open(PS, encoding='utf-8')) if d.get('property') == 'label']
buckets = {'noop':[], 'en2en':[], 'en2zh':[], 'zh2zh':[], 'unknown_orig':[]}
rows = []
for i, r in enumerate(recs, 1):
    dt, fn, new = r.get('doc_type'), r.get('field_name'), r.get('value')
    d = index.get(dt)
    orig = None; found = False
    if d:
        for fld in d.get('fields', []):
            if fld.get('fieldname') == fn:
                orig = fld.get('label'); found = True; break
    if not found:
        cls = 'unknown_orig'
    elif (orig or '') == (new or ''):
        cls = 'noop'
    elif has_cjk(orig) and has_cjk(new): cls = 'zh2zh'
    elif not has_cjk(orig) and has_cjk(new): cls = 'en2zh'
    else: cls = 'en2en'
    buckets[cls].append(i)
    rows.append((i, dt, fn, orig if found else '<NOT IN fields[]>', new, cls))

print('%-3s %-30s %-32s %-34s %-38s %s' % ('#','DocType','field','orig label','new label','class'))
for r in rows:
    print('%-3d %-30s %-32s %-34s %-38s %s' % r)
print()
print('--- classification counts ---')
for k in ('noop','en2en','en2zh','zh2zh','unknown_orig'):
    print('  %-14s %2d  %s' % (k, len(buckets[k]), buckets[k]))
