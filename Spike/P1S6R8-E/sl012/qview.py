import json
d = json.load(open('quality.json', encoding='utf-8'))
with open('quality_view.txt', 'w', encoding='utf-8') as f:
    f.write('NO_HAN ' + json.dumps(d['no_han'], ensure_ascii=False) + '\n')
    for m in d['mixed']: f.write(f"{m['in_src']} {m['words']} | {m['key'][:70]} | {m['zh'][:70]}\n")
