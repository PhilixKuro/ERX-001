"""F 分片 5：守卫判别力反例（复制 test_translation_quality / test_translations 的判定逻辑，不 import frappe、不改原文件）。
python -I -X utf8 Spike/P1S6R12-F/p5/guard_probe.py
"""
from __future__ import annotations

import ast
import csv
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
APP = ROOT / "frappe-bench/apps/frappe_china/frappe_china"
QUALITY = APP / "tests/test_translation_quality.py"
TRANS = APP / "tests/test_translations.py"


def _literal(path, name):
	for node in ast.parse(path.read_text(encoding="utf-8")).body:
		target = node.target if isinstance(node, ast.AnnAssign) else (node.targets[0] if isinstance(node, ast.Assign) else None)
		if isinstance(target, ast.Name) and target.id == name:
			return node.value
	raise KeyError(name)


# 照抄原实现用到的常量（从源文件取，保证一致）
STOPWORDS = frozenset(ast.literal_eval(_literal(QUALITY, "STOPWORDS").args[0].func.value).split())
ALLOW = {ast.literal_eval(k) for k in _literal(QUALITY, "ALLOW").keys}
QE = {ast.literal_eval(k) for k in _literal(QUALITY, "QUALITY_EXCEPTIONS").keys}
_PLACEHOLDER = re.compile(ast.literal_eval(_literal(TRANS, "_PLACEHOLDER").args[0]))
_CJK = re.compile(r"[㐀-䶿一-鿿]")
_HTML_TAG = re.compile(r"<[^>]+>")
_EMPHASIS = re.compile(r"\*\*|__")
_SPACED_CJK = re.compile(r"[㐀-䶿一-鿿] +[㐀-䶿一-鿿]")
_WORD = re.compile(r"[A-Za-z][A-Za-z0-9]+")


def _strip(t):
	return _EMPHASIS.sub("", _HTML_TAG.sub("", _PLACEHOLDER.sub("0", t)))


def placeholder(t):
	return t.strip().startswith("中文：") or "???" in t


def traditional(t):
	for ch in _CJK.findall(t):
		try:
			ch.encode("gb2312")
		except UnicodeEncodeError:
			return True
	return False


def wbw(t):
	if not _CJK.search(t):
		return False
	s = _strip(t)
	return bool(_SPACED_CJK.search(s)) or any(w.lower() in STOPWORDS for w in re.findall(r"[A-Za-z]+", s))


def mixed(t):
	if not _CJK.search(t):
		return False
	return any(not w.isupper() and w not in ALLOW for w in _WORD.findall(_strip(t)))


def any_guard(t):
	return [g.__name__ for g in (placeholder, traditional, wbw, mixed) if g(t)]


def duplicate_keys(rows):  # 照抄 test_translations._duplicate_keys
	keys = [r[0] + (":" + r[2] if len(r) == 3 and r[2] else "") for r in rows if len(r) in (2, 3)]
	return sorted(k for k, c in Counter(keys).items() if c > 1)


CASES = [
	("自检：方案原文四例应命中", "帳戶"), ("", "登录 带 密码"), ("", "中文：A0"), ("", "上传 Photo"),
	("未译：译文即源词原样（无汉字）", "Upload Photo"),
	("未译：英文改写（无汉字）", "Upload picture"),
	("占位：其它机翻占位形态", "【待译】Upload Photo"), ("", "[TODO]"), ("", "（未翻译）"),
	("繁体：GB2312 内的繁体／异体字", "於此處"), ("", "乾淨"), ("", "著作權"),
	("台湾用词（简体字形）", "伺服器设定"), ("", "请检查网路连线"), ("", "资料库档案"),
	("逐词直译：无空格、无停用词", "登录带密码"), ("", "上传照片它"),
	("混排：全大写英文词", "上传 PHOTO"), ("", "保存 FILE"),
	("混排：单字母英文", "选择 x 项"),
	("CJK 兼容区汉字（U+F900 起）", "豈更"),
]
print("== 守卫反例")
for label, text in CASES:
	print(f"{label:<28} {text!r:<26} -> {any_guard(text) or '全部放过'}")

print("== QUALITY_EXCEPTIONS 豁免整行全部四道守卫（不分哪道）")
rows = list(csv.reader((APP / "translations/zh.csv").open(encoding="utf-8", newline="")))
key = lambda r: r[0] + (":" + r[2] if len(r) == 3 and r[2] else "")
for r in rows:
	if key(r) in QE:
		hits = any_guard(r[1])
		if any(h != "mixed" for h in hits):
			print("  QE 行另命中非混排守卫：", key(r)[:60], hits)
print("  构造：把『帳戶』塞进任一 QE 行译文，_report 仍放过（QE 判在 predicate 之前）")

print("== 重复键检测不按 Frappe 读法归一字面 \\n")
probe = [["a\\nb", "甲"], ["a\nb", "乙"]]
print("  test._duplicate_keys ->", duplicate_keys(probe), "；Frappe 读后两行同键 'a<换行>b'，后者覆盖前者")
print("== 当前 csv：无汉字的译文行", [r[:2] for r in rows if not _CJK.search(r[1])][:6])
