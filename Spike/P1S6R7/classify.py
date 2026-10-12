"""TS-017/018 预查：csv 行按 A15 分类，列出与官方交集的行属哪类。宿主 python -I 跑。"""
import ast, csv, importlib.util, json, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "frappe-bench/apps/frappe_china/frappe_china"
spec = importlib.util.spec_from_file_location("baseline", ROOT / "Spike/P1S6R4-baseline.py")
bl = importlib.util.module_from_spec(spec); spec.loader.exec_module(bl)

def module_dict(path, name):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        target = node.target if isinstance(node, ast.AnnAssign) else (node.targets[0] if isinstance(node, ast.Assign) else None)
        if isinstance(target, ast.Name) and target.id == name:
            return node.value
    raise KeyError(name)

def literal_keys(path, name):
    return set(ast.literal_eval(module_dict(path, name)).keys())

def override_keys(path):
    return {ast.literal_eval(k) for k in module_dict(path, "OVERRIDES").keys}

def app_source_strings():
    pattern = re.compile(r"""(?<![A-Za-z_])_{1,2}\(\s*(["'])((?:\.|(?!\1).)*)\1""")
    sources = set()
    for path in [*APP.rglob("*.py"), *APP.rglob("*.js")]:
        if "tests" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        for match in pattern.finditer(text):
            context = re.match(r'''\s*,\s*context\s*=\s*(["'])(.*?)\1''', text[match.end():])
            sources.add(match.group(2) + (":" + context.group(2) if context else ""))
    for path in APP.rglob("*.json"):
        if "fixtures" in path.parts and path.name != "custom_field.json":
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            sources.update(f["label"] for f in data if isinstance(f, dict) and f.get("label"))
            continue
        if not isinstance(data, dict) or data.get("doctype") not in ("DocType", "Report"):
            continue
        sources.add(data["name"])
        for field in data.get("fields", []):
            if field.get("label"):
                sources.add(field["label"])
            if field.get("fieldtype") == "Select":
                sources.update(o.strip() for o in (field.get("options") or "").split("\n") if o.strip())
    return {s for s in sources if s and not re.search(r"[一-鿿]", s)}

if __name__ == "__main__":
    tests = APP / "tests"
    own = app_source_strings()
    required = literal_keys(tests / "test_translations.py", "REQUIRED_TRANSLATIONS")
    named = literal_keys(tests / "test_named_terms.py", "NAMED_TERMS")
    overrides = override_keys(tests / "translation_overrides.py")
    ours = bl.parse_csv(APP / "translations/zh.csv")
    official = {}
    for app in bl.APPS[:-1]:
        for e in bl.parse_po(bl.app_path(app) / "locale/zh.po"):
            if e["str"]:
                official[bl.entry_key(e)] = e["str"]
    out = {"csv_rows": len(ours), "own_in_csv": len(own & ours.keys()), "required_in_csv": len(required & ours.keys()),
           "named_in_csv": len(named & ours.keys()), "overrides": len(overrides),
           "own_missing_in_csv": sorted(own - ours.keys()),
           "overlap": len(ours.keys() & official.keys())}
    rows = []
    for k in sorted(ours.keys() & official.keys()):
        cls = "own" if k in own or k in required else "named" if k in named else "override" if k in overrides else "batch"
        rows.append([cls, k, official[k], ours[k]])
    out["overlap_by_class"] = {c: sum(r[0] == c for r in rows) for c in ("own", "named", "override", "batch")}
    print(json.dumps(out, ensure_ascii=False, indent=1))
    for r in rows:
        if r[0] in ("own", "named"):
            print(" | ".join(r))
