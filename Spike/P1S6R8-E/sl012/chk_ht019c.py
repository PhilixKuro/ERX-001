import csv, json, random, re
B = 'D:/ERX-001/'
def rd(p): return list(csv.reader(open(p, encoding='utf-8', newline='')))
def key(r): return r[0].replace('\\n', '\n') + (':' + r[2] if len(r) == 3 and r[2] else '')
pr = rd(B + 'Spike/P1S6R6-pruned.csv'); cur = rd(B + 'frappe-bench/apps/frappe_china/frappe_china/translations/zh.csv')
curd = {key(r): r[1] for r in cur}
merged = json.load(open('erx_merged.json', encoding='utf-8')); off = json.load(open('erx_official.json', encoding='utf-8'))
src = {key(r): r[0].replace('\\n', '\n') for r in pr}
allov = sorted({key(r) for r in pr if key(r) in off})
neq = [k for k in allov if off[k] != src[k] and k not in curd]
han = re.compile(r'[\u4e00-\u9fff]')
random.seed(20261012); s = sorted(random.sample(neq, min(10, len(neq))))
out = {'n_override_pruned': len(allov), 'n_official_ne_source_not_back': len(neq),
       'n_official_has_han': len([k for k in allov if han.search(off[k] or '')]),
       'all_161_not_back_mismatch': [k for k in allov if k not in curd and merged.get(k) != off[k]],
       'back_in_csv': {k: {'csv': curd[k], 'official': off[k], 'merged': merged.get(k)} for k in allov if k in curd},
       'neq_keys': neq,
       'sample': [{'key': k, 'pruned_csv': [r[1] for r in pr if key(r) == k][0], 'official': off[k], 'merged_erx': merged.get(k), 'eq': merged.get(k) == off[k]} for k in s]}
json.dump(out, open('ht019_sample.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
