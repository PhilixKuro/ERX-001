import ast, importlib.util, json
from pathlib import Path
spec = importlib.util.spec_from_file_location("bl", "D:/ERX-001/Spike/P1S6R4-baseline.py")
bl = importlib.util.module_from_spec(spec); spec.loader.exec_module(bl)
src = Path("D:/ERX-001/frappe-bench/apps/frappe_china/frappe_china/tests/translation_overrides.py").read_text(encoding="utf-8-sig")
tree = ast.parse(src)
ov = {}
for node in ast.walk(tree):
    if isinstance(node, ast.AnnAssign) and isinstance(node.value, ast.Dict):
        for k, v in zip(node.value.keys, node.value.values):
            ov[ast.literal_eval(k)] = [ast.literal_eval(a) for a in v.args]
off = bl.official_overrides()
keys = {o["key"] for o in off}
ours = bl.parse_csv(bl.app_path("frappe_china") / "translations/zh.csv")
print("OVERRIDES", len(ov), "po-overlap", len(keys))
print("overlap not in OVERRIDES:", sorted(keys - set(ov))[:20])
print("ours mismatch:", [k for k, v in ov.items() if ours.get(k) != v[1]][:20])
offmap = {o["key"]: o["official"] for o in off}
print("official mismatch vs zh.po:", [(k, v[0], offmap.get(k)) for k, v in ov.items() if offmap.get(k) != v[0]][:20])
print("basis with ????:", sum("????" in v[2] for v in ov.values()))
