import json
from pathlib import Path

import frappe
from frappe_china.tests.spc_data import make_spc_inspections

assert frappe.local.site == "test.localhost"
# Constant within-group spread and deliberately different means create both
# a >3 sigma point and a run of nine means above the grand mean.
means = [11] * 9 + [9] * 9 + [10] * 8 + [20, 0]
assert len(means) == 28 and sum(means) / len(means) == 10
fixture = make_spc_inspections([[mean-0.1, mean, mean+0.1] for mean in means])
Path("/workspace/Spike/P1S7R5-D/ts016-fixture.json").write_text(json.dumps(fixture, ensure_ascii=False, indent=1), encoding="utf-8")
frappe.db.commit()
print(json.dumps(fixture, ensure_ascii=False))
