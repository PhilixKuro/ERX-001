"""偏离第 3 条：对 TS-017 时点的旧 csv（af015fa，git show 导出到本目录）跑四守卫，核「全表红 5370 行」。"""
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import verify  # noqa: E402

q = verify.install_stubs()
path = Path(__file__).with_name("zh-af015fa.csv")
with open(path, encoding="utf-8", newline="") as handle:
    rows = [row for row in csv.reader(handle) if len(row) in (2, 3)]
saved = dict(q.QUALITY_EXCEPTIONS)
result = {"rows": len(rows), "with_current_exceptions": {g.__name__: len(g(rows)) for g in q.GUARDS}}
q.QUALITY_EXCEPTIONS.clear()
per = {g.__name__: {verify.TESTS and r.split(" => ")[0] for r in g(rows)} for g in q.GUARDS}
result["no_exceptions"] = {k: len(v) for k, v in per.items()}
result["distinct_rows_any_guard"] = len(set().union(*per.values()))
q.QUALITY_EXCEPTIONS.update(saved)
Path(__file__).with_name("oldcsv-out.json").write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(result, indent=1))
