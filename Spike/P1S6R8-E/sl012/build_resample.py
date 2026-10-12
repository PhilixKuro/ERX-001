import json, csv, random, re
from pathlib import Path
R = Path('D:/ERX-001')
APPS = R / 'frappe-bench/apps'
pop = json.load(open('population.json', encoding='utf-8'))
orig = list(csv.reader(open(R / 'Spike/P1S6R6-sample.out.csv', encoding='utf-8-sig', newline='')))[1:]
sampled = {(r[0], r[1]) for r in orig}
cur = {}
for a, rows in pop.items():
    for k, refs, t in rows: cur[(a, k)] = (refs, t)
def ctx(refs, n=2):
    out = []
    for ref in refs[:2]:
        m = re.match(r'(.+):(\d+)$', ref)
        if not m: continue
        p = APPS / m.group(1).split('/')[0] / m.group(1)
        if not p.exists(): p = APPS / m.group(1)
        if not p.exists(): out.append(f'{ref}: <missing>'); continue
        lines = p.read_text(encoding='utf-8', errors='replace').splitlines()
        i = int(m.group(2)) - 1
        out.append(ref + '\n' + '\n'.join(f'  {j+1}: {lines[j][:220]}' for j in range(max(0, i-n), min(len(lines), i+n+1))))
    return out
rng = random.Random(20261012)
a_rows = rng.sample(orig, 20)
quota = {'crm': 5, 'erpnext': 12, 'frappe': 3, 'hrms': 2, 'insights': 4, 'raven': 14}
b = []
for app in sorted(quota):
    pool = [row for row in pop[app] if (app, row[0]) not in sampled]
    for k, refs, t in random.Random(20261012).sample(pool, quota[app]):
        b.append({'set': 'B', 'app': app, 'key': k, 'refs': refs, 'translation': t})
a = [{'set': 'A', 'app': r[0], 'key': r[1], 'refs': cur[(r[0], r[1])][0], 'translation': cur[(r[0], r[1])][1], 'd_verdict': r[4], 'd_reason': r[5]} for r in a_rows]
items = a + b
for i, it in enumerate(items, 1): it['id'] = i
json.dump(items, open('resample_input.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
with open('resample_view.txt', 'w', encoding='utf-8') as f:
    for it in items:
        f.write(f"=== #{it['id']} [{it['set']}] {it['app']}\nKEY: {it['key']}\nZH : {it['translation']}\n")
        if it['set'] == 'A': f.write(f"D  : {it['d_verdict']} / {it['d_reason']}\n")
        for c in ctx(it['refs']): f.write(c + '\n')
        if len(it['refs']) > 2: f.write(f"  (+{len(it['refs'])-2} more refs)\n")
print(len(items))
