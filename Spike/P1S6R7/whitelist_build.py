"""TS-019 第 6 步／TS-021 第 7 步：基线残余缺口里的代码值进 UNTRANSLATED 并逐条写理由。
宿主 `python -I -X utf8 Spike/P1S6R7/whitelist_build.py <baseline.json> [--write]`。
只收按规则能判为代码值的键；其余残余缺口打印出来，须译，不进白名单。
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WHITELIST = ROOT / "frappe-bench/apps/frappe_china/frappe_china/tests/translation_whitelist.py"

RULES: list[tuple[re.Pattern, str]] = [
	(re.compile(r"\.YYYY\.|\.#|^[A-Z]{2,}(-[A-Z]+)*-$"), "单据编号规则（naming series），系统按原样解析，译了会改变编号"),
	(re.compile(r"^(A|B|AB|O)[+-]$"), "血型写法，国际通用"),
	(re.compile(r"^(EAN(-8|-13)?|UPC-A|ISBN-1[03]|GTIN-14|JAN)$"), "条码制式名，原样显示"),
	(re.compile(r"^(A\d|B\d{1,2}|C5E|Comm10E)$"), "纸张规格名，原样显示"),
	(re.compile(r"^(CSV|PDF|HTML|JSON|SQL|XLSX|CSS|JS|API|CMD)$"), "文件或技术格式名，原样显示"),
	(re.compile(r"^(UID|UIDNEXT|UIDVALIDITY)$"), "IMAP 协议字段名，原样显示"),
	(re.compile(r"^\d{2}:\d{2}$"), "时刻，原样显示"),
	(re.compile(r"^[\d.]+$|^\d+[-+]\d*$|^\d+-\d+$|^<\d+$"), "数字或数字区间，原样显示"),
	(re.compile(r"^[A-Z] - [A-Z]$"), "公式示例里的字母代号，原样显示"),
	(re.compile(r"^[NM1]:[NM1]$"), "关系基数记号，原样显示"),
	(re.compile(r"^(!=|<|>|>=|<=|=|/|X)$"), "运算符或符号，原样显示"),
	(re.compile(r"^[\s#{}\d%&=?]*$"), "只含占位符与符号，原样显示"),
	(re.compile(r"^(POS|IBAN|AI|IRS 1099|PCV|DFS|Mx)$"), "通用缩写或专名，原样显示"),
	(re.compile(r"^(<[^>]+>\s*)+$|^(<[^>]+>|\{\d*\}|\s)+$"), "纯 HTML 标签与占位符，无可译文字"),
	(re.compile(r"^[\w.+-]+@[\w-]+\.[\w.]+$"), "示例邮箱地址，原样显示"),
]


def reason_for(key: str) -> str | None:
	if not key.strip():
		return "空白字符串，无可译内容"
	for pattern, reason in RULES:
		if pattern.search(key):
			return reason
	return None


def main() -> None:
	baseline = json.loads((ROOT / sys.argv[1]).read_text(encoding="utf-8"))
	residual = sorted({key for items in baseline["gaps"].values() for key, _refs in items})
	add, rest = {}, []
	for key in residual:
		reason = reason_for(key)
		(add.__setitem__(key, reason) if reason else rest.append(key))
	print(json.dumps({"residual": len(residual), "whitelist_add": len(add), "must_translate": len(rest)}, ensure_ascii=False))
	# 明细写文件，不打到控制台（Windows 控制台遇制表符等控制字符会 OSError）
	(ROOT / "Spike/P1S6R7/whitelist_report.json").write_text(
		json.dumps({"whitelist": add, "must_translate": rest}, ensure_ascii=False, indent=1), encoding="utf-8")
	if "--write" not in sys.argv:
		return
	text = WHITELIST.read_text(encoding="utf-8")
	start = text.index("UNTRANSLATED: dict[str, str] = {")
	end = text.index("\n}", start)
	body = text[start:end]
	existing = set(re.findall(r'^\t("(?:[^"\\]|\\.)*"):', body, re.MULTILINE))
	lines = [f"\t{json.dumps(key, ensure_ascii=False)}: {json.dumps(reason, ensure_ascii=False)}," for key, reason in add.items()
		if json.dumps(key, ensure_ascii=False) not in existing]
	text = text[:end] + ("\n" + "\n".join(lines) if lines else "") + text[end:]
	WHITELIST.write_bytes(text.replace("\r\n", "\n").replace("\n", "\r\n").encode("utf-8"))
	print(json.dumps({"written": len(lines)}))


if __name__ == "__main__":
	main()
