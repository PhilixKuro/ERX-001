"""P1-S6-R13 F 片 1：FD-009 出处索引的盲区探针（只读）。宿主 `python -I -X utf8 index_blindspot.py <baseline.json>`。

source_index 只认 `_()`/`__()` 字面量与 json 的 label、options。这里对 112 个无 context 覆盖键另扫六个上游 app 的 json 里
其它会被翻译显示的键（description、title、name（DocType/Report/Workspace 等）、link_to、placeholder、heading 等），
以及 JS 里不经 `__()` 的裸数组（如 meta.js get_print_sizes），看有没有 main.pot 没记、索引也没收的出处。
"""
import json, os, pathlib, re, sys
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parents[3] / "frappe-bench/apps"
APPS = ("frappe", "erpnext", "crm", "hrms", "insights", "raven")
SKIP = {"node_modules", "locale", "dist", ".git", "__pycache__", "assets", "www_build", "tests", "test"}
data = json.load(open(sys.argv[1], encoding="utf-8"))
rows = {r["key"]: r for r in data["official_overrides"] if ":" not in r["key"]}
keys = set(rows)
FIELDS = ("description", "title", "name", "link_to", "placeholder", "heading", "subtitle", "button_label", "insert_after_label")
pat = re.compile(r'"(%s)":\s*("(?:\\.|[^"\\])*")' % "|".join(FIELDS))
found = defaultdict(set)
for app in APPS:
    base = ROOT / app
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames[:] = [d for d in dirnames if d not in SKIP and not d.startswith(".")]
        for fn in filenames:
            if not fn.endswith(".json"):
                continue
            p = pathlib.Path(dirpath) / fn
            try:
                text = p.read_text(encoding="utf-8-sig")
            except Exception:
                continue
            for m in pat.finditer(text):
                try:
                    v = json.loads(m.group(2))
                except Exception:
                    continue
                if v in keys:
                    found[v].add(f"{p.relative_to(base).as_posix()}:{m.group(1)}")
indexed = {k: {ref.split(":")[0] for ref in r["source_refs"]} for k, r in rows.items()}
print("keys with json refs outside label/options:", len(found))
for k in sorted(found):
    extra = sorted(ref for ref in found[k] if ref.split(":")[0] not in indexed[k])
    if extra:
        print(" ", k, "|", len(extra), extra[:4])

# 裸字符串数组里出现、不经 __() 的覆盖键（JS 选项来源），只报 Ledger 等已知案例所在的形态
js_hits = defaultdict(set)
for app in APPS:
    for dirpath, dirnames, filenames in os.walk(ROOT / app):
        dirnames[:] = [d for d in dirnames if d not in SKIP and not d.startswith(".")]
        for fn in filenames:
            if fn.endswith(".js") and not fn.startswith("test_"):
                p = pathlib.Path(dirpath) / fn
                text = p.read_text(encoding="utf-8", errors="ignore")
                for m in re.finditer(r'^\s*"([^"\n]+)",\s*$', text, re.M):
                    if m.group(1) in keys:
                        js_hits[m.group(1)].add(p.relative_to(ROOT).as_posix())
print("bare JS array items equal to override keys:", {k: sorted(v)[:3] for k, v in sorted(js_hits.items())})
