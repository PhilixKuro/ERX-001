import ast, sys
sys.path.insert(0, ".")
from merged import merged, official, ours
src = open("D:/ERX-001/frappe-bench/apps/frappe_china/frappe_china/tests/test_named_terms.py", encoding="utf-8").read()
tree = ast.parse(src)
named = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "NAMED_TERMS")
bad = [(k, v, merged.get(k)) for k, v in named.items() if merged.get(k) != v]
same_as_official = [k for k, v in named.items() if official.get(k) == v]
print("named", len(named), "mismatch", bad)
print("asserted value equals official (removing csv row would not turn red):", same_as_official)
print("in named but absent from csv:", [k for k in named if k not in ours])
