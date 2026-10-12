"""译者用查词工具：宿主 `python -I -X utf8 Spike/P1S6R7/lookup.py <英文词或短语> [...]`。

对每个参数打印：合并字典（六个官方 app + frappe_china csv）里该键的现译；以及源词里含该词（整词、不区分大小写）的前 15 条现译，
供译者对齐官方既有用词。只读，不写任何文件。
"""
from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("baseline", ROOT / "Spike/P1S6R4-baseline.py")
baseline = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(baseline)
CJK = re.compile(r"[一-鿿]")


def main(words: list[str]) -> None:
	merged, _ = baseline.merged_dict()
	for word in words:
		print(f"== {word!r} => {merged.get(word)!r}")
		pattern = re.compile(rf"(?<![A-Za-z]){re.escape(word)}(?![A-Za-z])", re.IGNORECASE)
		hits = [(key, value) for key, value in merged.items() if key != word and pattern.search(key) and CJK.search(value or "")]
		for key, value in sorted(hits, key=lambda item: len(item[0]))[:15]:
			print(f"   {key!r} => {value!r}")


if __name__ == "__main__":
	main(sys.argv[1:])
