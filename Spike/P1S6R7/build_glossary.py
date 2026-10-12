"""术语表 Spike/P1S6R7/glossary.json：以 zh.csv 现有全部行为准（已定词的唯一来源），另加 NAMED_TERMS 里保留官方的条目。
宿主 python -I -X utf8 跑。每次往 csv 并入一批后重跑，后续译者即看到新定的词。"""
import ast, csv, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "frappe-bench/apps/frappe_china/frappe_china"
glossary = {}
for row in csv.reader((APP / "translations/zh.csv").open(encoding="utf-8", newline="")):
    glossary[row[0] + (":" + row[2] if len(row) == 3 and row[2] else "")] = row[1]
tree = ast.parse((APP / "tests/test_named_terms.py").read_text(encoding="utf-8"))
named = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "NAMED_TERMS")
for k, v in named.items():
    glossary.setdefault(k, v)
(ROOT / "Spike/P1S6R7/glossary.json").write_text(json.dumps(dict(sorted(glossary.items(), key=lambda i: i[0].casefold())), ensure_ascii=False, indent=1), encoding="utf-8")
print(len(glossary), "terms")
