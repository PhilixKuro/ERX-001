"""偏离第 3 条判别力：把真实 test_translation_quality.py 复制到本目录，逐个把守卫谓词改成恒假，跑判别力用例看是否失败。"""
from __future__ import annotations

import io
import json
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import verify  # noqa: E402

SRC = verify.TESTS / "test_translation_quality.py"
HERE = Path(__file__).parent
PREDICATES = {
    "_is_placeholder": "test_placeholder_guard_reports_constructed_row",
    "_is_traditional": "test_traditional_guard_reports_constructed_row",
    "_is_word_by_word": "test_word_by_word_guard_reports_constructed_row",
    "_is_mixed": "test_mixed_guard_reports_constructed_row",
}

results = {}
text = SRC.read_text(encoding="utf-8")
for predicate, test_name in PREDICATES.items():
    mutated = re.sub(rf"(def {predicate}\(target: str\) -> bool:\n)", r"\1\treturn False\n", text, count=1)
    assert mutated != text, predicate
    path = HERE / f"mut{predicate}.py"
    path.write_text(mutated, encoding="utf-8")
    module = verify.install_stubs(path)
    outcome = {}
    for name in PREDICATES.values():
        suite = unittest.TestSuite([module.TestTranslationQuality(name)])
        r = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(suite)
        outcome[name] = "PASS" if r.wasSuccessful() else "FAIL"
    results[predicate] = outcome
    path.unlink()

# 另一种变异：去掉 QUALITY_EXCEPTIONS 扣除，看全表守卫是否变红（证明例外表确实在挡命中行）
module = verify.install_stubs()
saved = dict(module.QUALITY_EXCEPTIONS)
module.QUALITY_EXCEPTIONS.clear()
rows = module.csv_rows()
results["no_exceptions_full_table"] = {g.__name__: len(g(rows)) for g in module.GUARDS}
module.QUALITY_EXCEPTIONS.update(saved)
print(json.dumps(results, ensure_ascii=False, indent=1))
