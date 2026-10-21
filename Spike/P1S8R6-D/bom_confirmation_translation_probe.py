"""Offline quality checks before TS-007 CSV changes reach the application."""
import csv
import json
import sys
import types
import unittest
from pathlib import Path

stub = types.ModuleType("frappe_china.tests.utils")
stub.FrappeChinaTestCase = unittest.TestCase
sys.modules[stub.__name__] = stub
from frappe_china.tests.test_translation_quality import guard_problems
from frappe_china.tests.test_translations import _duplicate_keys, _source_strings_from_text, _unsorted_pairs

root = Path("/workspace/Spike/P1S8R6-D/bom-confirmation-draft")
with (root / "zh.csv").open(encoding="utf-8", newline="") as handle:
    rows = list(csv.reader(handle))
assert not guard_problems(rows), guard_problems(rows)
assert not _duplicate_keys(rows), _duplicate_keys(rows)
assert not _unsorted_pairs(rows), _unsorted_pairs(rows)
sources = set()
for filename in ("bom_selection.py", "production_plan.js", "work_order.js", "custom_field.json"):
    sources |= _source_strings_from_text(filename, (root / filename).read_text(encoding="utf-8"))
csv_keys = {row[0] for row in rows}
new_sources = {
    "BOM Choice Source", "Confirm BOM recommendation", "Use recommended BOM", "Keep current BOM",
    "Recommended BOM: {0}", "Inherited from production plan", "Cost recommendation confirmed",
    "Cost recommendation kept current", "BOM manually specified", "Selected automatically by cost",
}
assert new_sources <= sources, new_sources - sources
assert new_sources <= csv_keys, new_sources - csv_keys
print(json.dumps({"quality_problems": [], "duplicate_keys": [], "unsorted_pairs": [],
                  "new_sources_detected": len(new_sources)}, ensure_ascii=False))
