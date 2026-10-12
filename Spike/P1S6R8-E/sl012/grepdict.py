import json, sys, re
o = json.load(open('erx_official.json', encoding='utf-8')); m = json.load(open('erx_merged.json', encoding='utf-8'))
pat = re.compile(sys.argv[1]); which = sys.argv[2]; d = o if which == 'off' else m
with open(sys.argv[3], 'w', encoding='utf-8') as f:
    for k, v in d.items():
        if pat.search(k) or pat.search(v or ''):
            f.write(f'{k[:110]!r}\t{(v or "")[:110]}\n')
