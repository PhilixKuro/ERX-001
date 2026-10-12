import csv, re, ast, json
R = 'D:/ERX-001/frappe-bench/apps/frappe_china/frappe_china/'
rows = list(csv.reader(open(R + 'translations/zh.csv', encoding='utf-8', newline='')))
src = open(R + 'tests/test_translation_quality.py', encoding='utf-8').read()
tree = ast.parse(src)
names = {}
for n in tree.body:
    t = n.target if isinstance(n, ast.AnnAssign) else (n.targets[0] if isinstance(n, ast.Assign) else None)
    if isinstance(t, ast.Name) and t.id in ('QUALITY_EXCEPTIONS', 'ALLOW'):
        try: names[t.id] = ast.literal_eval(n.value)
        except Exception as e: names[t.id] = f'<non-literal {type(n.value).__name__}>'
QE = names.get('QUALITY_EXCEPTIONS'); AL = names.get('ALLOW')
qe_keys = set(QE) if isinstance(QE, (dict, set, list, tuple, frozenset)) else set()
out = {'rows': len(rows), 'QE_type': type(QE).__name__, 'QE_n': len(qe_keys), 'ALLOW_n': len(AL) if hasattr(AL, '__len__') else AL}
out['zhongwen_colon'] = [r[:2] for r in rows if '中文：' in r[1]]
out['qmarks'] = [r[:2] for r in rows if '???' in r[1]]
out['empty'] = [r[:2] for r in rows if not r[1].strip()]
def nongb(s):
    bad = []
    for ch in s:
        if '\u3400' <= ch <= '\u9fff' or '\uf900' <= ch <= '\ufaff':
            try: ch.encode('gb2312')
            except UnicodeEncodeError: bad.append(ch)
    return bad
trad = []
for r in rows:
    b = nongb(r[1])
    if b:
        k = r[0] + (':' + r[2] if len(r) == 3 and r[2] else '')
        trad.append({'key': r[0], 'zh': r[1][:80], 'chars': ''.join(sorted(set(b))), 'in_QE': r[0] in qe_keys or k in qe_keys})
out['nongb_rows'] = len(trad); out['nongb_rows_not_QE'] = [t for t in trad if not t['in_QE']]
out['nongb_all'] = trad
# mixed-language scan: ascii words of >=3 letters in translation not present in source
allow = set(a.lower() for a in AL) if isinstance(AL, (dict, set, list, tuple, frozenset)) else set()
mixed = []
for r in rows:
    if not re.search(r'[\u4e00-\u9fff]', r[1]): continue
    t = re.sub(r'<[^>]+>|\{[^}]*\}|%\([^)]*\)s|%s|https?://\S+|&\w+;', ' ', r[1])
    words = re.findall(r'[A-Za-z][A-Za-z\-]{2,}', t)
    srcwords = set(w.lower() for w in re.findall(r'[A-Za-z][A-Za-z\-]{2,}', r[0]))
    odd = [w for w in words if w.lower() not in allow and not w.isupper()]
    if odd: mixed.append({'key': r[0][:80], 'zh': r[1][:80], 'words': odd, 'in_src': all(w.lower() in srcwords for w in odd)})
out['mixed_n'] = len(mixed)
out['mixed'] = mixed
# no-Chinese rows
out['no_han'] = [r[:2] for r in rows if not re.search(r'[\u4e00-\u9fff]', r[1])]
json.dump(out, open('quality.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print({k: (v if not isinstance(v, list) else len(v)) for k, v in out.items() if k not in ('nongb_all',)})
