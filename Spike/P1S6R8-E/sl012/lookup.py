import json, sys
o = json.load(open('erx_official.json', encoding='utf-8')); m = json.load(open('erx_merged.json', encoding='utf-8'))
keys = [l.rstrip('\n') for l in open(sys.argv[1], encoding='utf-8') if l.strip()]
with open(sys.argv[2], 'w', encoding='utf-8') as f:
    for k in keys: f.write(f'{k!r}\toff={o.get(k)}\tmerged={m.get(k)}\n')
