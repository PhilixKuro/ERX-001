"""TS-019 第 3 步（DJ-001 补充证据）：按渲染点重算演示撞名。宿主 `python -I -X utf8 Spike/P1S6R7/collision_effective.py <baseline.json>`。

基线 demo_collisions 只按无 context 键归并；而 DocType 字段 label／Select 选项渲染时带 df.parent 作 context。
本脚本对每组的每个源词、每个演示面出处，取该出处实际会显示的译文（字段出处先查 `源词:DocType`，再回落无 context），
再按「实际译文」重新归并：同一实际译文下仍有 ≥2 个源词的，才是仍待判的撞名组。输出 Spike/P1S6R7/collision_effective.json。
"""
from __future__ import annotations

import importlib.util
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("baseline", ROOT / "Spike/P1S6R4-baseline.py")
baseline = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(baseline)


def main() -> None:
	data = json.loads((ROOT / sys.argv[1]).read_text(encoding="utf-8"))
	merged, _plain = baseline.merged_dict()
	by_path = {path.relative_to(baseline.PROJECT).as_posix(): name for name, (path, _d) in baseline.doctypes().items()}
	field_ref = re.compile(r"(.+\.json):(\w+)$")
	still, resolved = [], []
	for target, group in sorted(data["demo_collisions"].items()):
		shown = defaultdict(lambda: defaultdict(list))  # 实际译文 → 源词 → 出处
		for source, refs in group["visible"].items():
			for ref in refs:
				match = field_ref.match(ref)
				doctype = by_path.get(match.group(1)) if match else None
				value = (merged.get(f"{source}:{doctype}") if doctype else None) or merged.get(source) or source
				shown[value.strip()][source].append(ref)
		clashes = {value: dict(sources) for value, sources in shown.items() if len(sources) >= 2}
		entry = {"target": target, "sources": group["sources"], "clashes": clashes}
		(still if clashes else resolved).append(entry)
	out = {"groups": len(data["demo_collisions"]), "still": len(still), "resolved_by_context": len(resolved),
		"still_groups": still, "resolved_groups": [g["target"] for g in resolved]}
	(ROOT / "Spike/P1S6R7/collision_effective.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
	print(json.dumps({k: out[k] for k in ("groups", "still", "resolved_by_context")}, ensure_ascii=False))


if __name__ == "__main__":
	main()
