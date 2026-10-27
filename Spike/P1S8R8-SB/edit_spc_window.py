"""S8 R8 SB: SPC anomaly-window judgement counts carry-over signals as in-window (user ruling 2026-10-27)."""

import os

ROOT = "d:/ERX-001/frappe-bench/apps/frappe_debug/frappe_debug"
CRLF, LF = chr(13) + chr(10), chr(10)


def edit(rel, pairs):
	path = os.path.join(ROOT, rel)
	with open(path, encoding="utf-8", newline="") as handle:
		text = handle.read()
	crlf = CRLF in text
	text = text.replace(CRLF, LF)
	for old, new in pairs:
		if new in text:
			continue
		assert text.count(old) == 1, (rel, old[:80])
		text = text.replace(old, new)
	if crlf:
		text = text.replace(LF, CRLF)
	with open(path, "w", encoding="utf-8", newline="") as handle:
		handle.write(text)


edit(
	"scenario/quality.py",
	[
		(
			'''def scenario_fingerprint(sc):''',
			'''# Points each Nelson rule looks back over, ending at the signalling subgroup (frappe_china spc.nelson)
RULE_WINDOWS = {1: 1, 2: 9, 3: 6, 4: 14, 5: 3, 6: 5, 7: 15, 8: 8}


def outside_window_signals(subgroups, window_start, window_end) -> list[dict]:
	"""Signalling subgroups not explained by the anomaly window (S8 R8 SB, user ruling 2026-10-27).

	A signal after the window whose rule window still contains shifted in-window subgroups is the
	anomaly's own tail (rules 5 and 6 look back 3 and 5 points), so it counts as in-window; the
	screen cannot redraw it away. Only signals whose every rule window lies outside count here.
	Provisional judgement, recorded as SH-P1S8021 for a business decision later.
	"""

	def inside(group):
		return window_start <= getdate(group["date"]) <= window_end

	result = []
	for position, group in enumerate(subgroups):
		if not group.get("rules") or inside(group):
			continue
		size = max(RULE_WINDOWS[rule] for rule in group["rules"])
		if any(inside(other) for other in subgroups[max(0, position - size + 1) : position]):
			continue
		result.append(group)
	return result


def scenario_fingerprint(sc):''',
		),
		(
			'''		outside = [
			group
			for group in result["subgroups"]
			if group["rules"] and not window_start <= getdate(group["date"]) <= window_end
		]
		inside = any(''',
			'''		outside = outside_window_signals(result["subgroups"], window_start, window_end)
		inside = any(''',
		),
		(
			'''	rule_windows = {1: 1, 2: 9, 3: 6, 4: 14, 5: 3, 6: 5, 7: 15, 8: 8}
''',
			'''	rule_windows = RULE_WINDOWS
''',
		),
		(
			'''			signals = [
				group
				for group in result["subgroups"]
				if group["rules"] and not window_start <= getdate(group["date"]) <= window_end
			]''',
			'''			signals = outside_window_signals(result["subgroups"], window_start, window_end)''',
		),
	],
)

edit(
	"scenario/verify.py",
	[
		(
			'''	out_of_window = [
		group
		for group in spc["subgroups"]
		if group["rules"] and not anomaly_start <= getdate(group["date"]) <= anomaly_end
	]''',
			'''	from frappe_debug.scenario.quality import outside_window_signals

	out_of_window = outside_window_signals(spc["subgroups"], anomaly_start, anomaly_end)''',
		)
	],
)

edit(
	"tests/test_quality_screening.py",
	[
		(
			'''	def test_no_signal_is_not_accepted_after_anomaly_window(self):''',
			'''	def test_anomaly_tail_counts_as_in_window_but_independent_outside_signals_do_not(self):
		"""S8 R8 SB（SH-P1S8021）：窗口后紧邻、规则窗口仍含窗内组的判异算窗内拖尾。"""
		from frappe_debug.scenario.quality import outside_window_signals

		start, end = date(2026, 2, 19), date(2026, 2, 26)
		groups = [
			{"inspection": "A", "date": "2026-02-17", "rules": [1]},
			{"inspection": "B", "date": "2026-02-25", "rules": [1]},
			{"inspection": "C", "date": "2026-02-26", "rules": [1, 5]},
			{"inspection": "D", "date": "2026-02-27", "rules": [5, 6]},
			{"inspection": "E", "date": "2026-02-27", "rules": [6]},
			{"inspection": "F", "date": "2026-02-27", "rules": [1]},
			{"inspection": "G", "date": "2026-03-02", "rules": []},
			{"inspection": "H", "date": "2026-03-02", "rules": []},
			{"inspection": "I", "date": "2026-03-02", "rules": []},
			{"inspection": "J", "date": "2026-03-03", "rules": [6]},
		]
		self.assertEqual(
			[group["inspection"] for group in outside_window_signals(groups, start, end)], ["A", "F", "J"]
		)

	def test_no_signal_is_not_accepted_after_anomaly_window(self):''',
		)
	],
)
print("ok")
