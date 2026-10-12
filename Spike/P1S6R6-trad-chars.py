"""生成逐屏核 v2 的繁体字表（TS-022 第 1 步，A18／HT-016）。

取六个 app 官方 po 的 msgstr 用字：zh_TW 用字 − zh 用字，再只留 GB2312 编不出的汉字
（与 frappe_china/tests/test_translation_quality.py::_is_traditional 同一判据）。
浏览器端没有 gb2312 编码器，故把字表注入页面比对。

用法：python -I -X utf8 Spike/P1S6R6-trad-chars.py [bench_apps_dir] [out_json]
"""

import json
import re
import sys
from pathlib import Path

APPS = ["frappe", "erpnext", "crm", "hrms", "insights", "raven"]
# 与 test_translation_quality._CJK 同一区间
CJK = re.compile(r"[㐀-䶿一-鿿]")
# msgstr "…" / msgstr[0] "…"，以及其后的续行 "…"
MSGSTR = re.compile(r'^msgstr(?:\[\d+\])?\s+"(.*)"\s*$')
CONT = re.compile(r'^"(.*)"\s*$')


def msgstr_chars(path: Path) -> set[str]:
	chars: set[str] = set()
	in_msgstr = False
	for line in path.read_text(encoding="utf-8").splitlines():
		line = line.strip()
		m = MSGSTR.match(line)
		if m:
			in_msgstr = True
			chars.update(CJK.findall(m.group(1)))
			continue
		if in_msgstr:
			c = CONT.match(line)
			if c:
				chars.update(CJK.findall(c.group(1)))
				continue
			in_msgstr = False
	return chars


def outside_gb2312(ch: str) -> bool:
	try:
		ch.encode("gb2312")
		return False
	except UnicodeEncodeError:
		return True


def main() -> int:
	root = Path(__file__).resolve().parent.parent
	apps_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else root / "frappe-bench" / "apps"
	out = Path(sys.argv[2]) if len(sys.argv) > 2 else root / "Spike" / "P1S6R6-trad-chars.json"
	tw: set[str] = set()
	zh: set[str] = set()
	used, skipped = [], []
	for app in APPS:
		locale = apps_dir / app / app / "locale"
		tw_po, zh_po = locale / "zh_TW.po", locale / "zh.po"
		if zh_po.exists():
			zh |= msgstr_chars(zh_po)
		if not tw_po.exists():
			skipped.append(app)
			continue
		tw |= msgstr_chars(tw_po)
		used.append(app)
	# 自检：zh 用字应全部在 GB2312 内（HT-016），否则判据不成立
	zh_outside = sorted(ch for ch in zh if outside_gb2312(ch))
	chars = "".join(sorted(ch for ch in tw - zh if outside_gb2312(ch)))
	source = (
		f"zh_TW.po msgstr 用字 − zh.po msgstr 用字，只留 GB2312 外汉字；"
		f"zh_TW 取自 {', '.join(used)}；无 zh_TW.po 跳过：{', '.join(skipped) or '无'}；"
		f"zh.po 取自六 app 中存在者；zh 用字 {len(zh)} 个，其中 GB2312 外 {len(zh_outside)} 个"
		+ (f"（{''.join(zh_outside)}）" if zh_outside else "")
	)
	out.write_text(
		json.dumps({"chars": chars, "count": len(chars), "source": source}, ensure_ascii=False, indent=1) + "\n",
		encoding="utf-8",
	)
	print(json.dumps({"count": len(chars), "zh_chars": len(zh), "tw_chars": len(tw), "zh_outside_gb2312": len(zh_outside), "skipped": skipped}, ensure_ascii=False))
	return 0


if __name__ == "__main__":
	sys.exit(main())
