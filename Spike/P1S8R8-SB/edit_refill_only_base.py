"""S8 R8 SB FD-013: live switches no longer refill in the background (IT-003 item 6 fallback, ruled 2026-10-26).

Measured on erx 2026-10-27: a refill clone during the show pushed desk API latency from ~8 ms to 26 s
and a 7->8 fast-forward to 27.7 s. Refills now run only on return to base and from the rehearsal
page button; an act with no clean copy still repairs itself, but only that act.
"""

import os

ROOT = "d:/ERX-001/frappe-bench/apps/frappe_debug"
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
	"frappe_debug/demo/registry.py",
	[
		(
			'''def _claim_refill_unlocked(registry: dict, keep: set, first_act: int | None = None) -> list[tuple[int, str]]:
	"""Mark every consumed or failed copy for rebuilding from its act's original."""
	claimed = []
	for act in sorted(registry.get("acts", {}), key=lambda key: (int(key) != first_act, int(key))):''',
			'''def _claim_refill_unlocked(
	registry: dict, keep: set, first_act: int | None = None, only_act: int | None = None
) -> list[tuple[int, str]]:
	"""Mark every consumed or failed copy (of ``only_act`` alone when given) for rebuilding."""
	claimed = []
	for act in sorted(registry.get("acts", {}), key=lambda key: (int(key) != first_act, int(key))):
		if only_act is not None and int(act) != only_act:
			continue''',
		),
		(
			'''def claim_refill(keep: set, first_act: int | None = None) -> list[tuple[int, str]]:
	with filelock("frappe_debug_snapshots"):
		registry = _read_unlocked()
		if registry is None:
			return []
		claimed = _claim_refill_unlocked(registry, keep, first_act)''',
			'''def claim_refill(keep: set, first_act: int | None = None, only_act: int | None = None) -> list[tuple[int, str]]:
	with filelock("frappe_debug_snapshots"):
		registry = _read_unlocked()
		if registry is None:
			return []
		claimed = _claim_refill_unlocked(registry, keep, first_act, only_act)''',
		),
		(
			'''def reserve_snapshot(act: int, purpose: str) -> tuple[dict | None, list]:
	"""Atomically consume one clean copy and claim every other consumed copy for refill.

	The returned copy becomes the connected database and is never claimed. The copy being
	left is claimed too: refills run only after the response has moved the session.
	"""''',
			'''def reserve_snapshot(act: int, purpose: str, claim: bool = True) -> tuple[dict | None, list]:
	"""Atomically consume one clean copy and, with ``claim``, claim every other consumed copy.

	The returned copy becomes the connected database and is never claimed. The copy being
	left is claimed too: refills run only after the response has moved the session. Live
	switches pass ``claim=False`` (FD-013): refills slow the desk, so they wait for the base.
	"""''',
		),
		(
			'''		selected["state"] = "used"
		refill = _claim_refill_unlocked(registry, {selected["db"]}, first_act=act)''',
			'''		selected["state"] = "used"
		refill = _claim_refill_unlocked(registry, {selected["db"]}, first_act=act) if claim else []''',
		),
	],
)

edit(
	"frappe_debug/demo/switch.py",
	[
		(
			'''	selected, refill = registry.reserve_snapshot(act, purpose)
	if not selected:
		# Nothing clean is ready. Rebuild consumed or failed copies, this act first, instead
		# of waiting for a refill that was never started (IT-003). The connected database
		# stays put because no switch happens.
		_schedule_replenish(registry.claim_refill(keep={frappe.conf.db_name}, first_act=act))''',
			'''	# FD-013: refilling during the show slowed the desk to seconds (IT-003 item 6), so a live
	# switch only consumes a copy; consumed copies are rebuilt when the show returns to base.
	selected, refill = registry.reserve_snapshot(act, purpose, claim=False)
	if not selected:
		# Nothing clean is ready for this act. Rebuild only its copies from the original instead
		# of waiting for a refill that was never started (IT-003). The connected database
		# stays put because no switch happens.
		_schedule_replenish(registry.claim_refill(keep={frappe.conf.db_name}, only_act=act))''',
		),
	],
)

edit(
	"frappe_debug/tests/test_switch.py",
	[
		(
			'''			patch(
				"frappe_debug.demo.switch.registry.reserve_snapshot",
				return_value=(selected, [(1, "s8_base_a1_m")]),
			),
			patch("frappe_debug.demo.switch._switch") as change,
			patch.object(frappe.local, "request", MagicMock(), create=True) as request,
		):
			self.assertEqual(switch_to_act(1, "restart"), {"status": "switched", "db": selected["db"]})
		change.assert_called_once_with(selected["db"])
		request.after_response.add.assert_called_once()''',
			'''			patch(
				"frappe_debug.demo.switch.registry.reserve_snapshot", return_value=(selected, [])
			) as reserve,
			patch("frappe_debug.demo.switch._switch") as change,
			patch.object(frappe.local, "request", MagicMock(), create=True) as request,
		):
			self.assertEqual(switch_to_act(1, "restart"), {"status": "switched", "db": selected["db"]})
		change.assert_called_once_with(selected["db"])
		# FD-013: a live switch consumes a copy without starting any refill
		reserve.assert_called_once_with(1, "restart", claim=False)
		request.after_response.add.assert_not_called()''',
		),
		(
			'''		claim.assert_called_once_with(keep={"s8_base_a5_m"}, first_act=6)''',
			'''		claim.assert_called_once_with(keep={"s8_base_a5_m"}, only_act=6)''',
		),
	],
)

edit(
	"frappe_debug/tests/test_registry.py",
	[
		(
			'''			snapshots.release_reservation(6, selected["db"], refill)
			stored = snapshots.get_registry()["acts"]
			self.assertEqual(stored["6"]["b"]["state"], "ready")
			self.assertEqual(stored["8"]["m"]["state"], "used")''',
			'''			snapshots.release_reservation(6, selected["db"], refill)
			stored = snapshots.get_registry()["acts"]
			self.assertEqual(stored["6"]["b"]["state"], "ready")
			self.assertEqual(stored["8"]["m"]["state"], "used")

			# FD-013: a live switch consumes the copy without claiming anything for refill
			selected, refill = snapshots.reserve_snapshot(6, "forward", claim=False)
			self.assertEqual((selected["db"], refill), ("s8_base_a6_b", []))
			stored = snapshots.get_registry()["acts"]
			self.assertEqual(stored["8"]["m"]["state"], "used")
			self.assertEqual(snapshots.claim_refill(keep={"s8_base_a6_b"}, only_act=8), [(8, "s8_base_a8_m")])
			self.assertEqual(snapshots.get_registry()["acts"]["1"]["b"]["state"], "used")''',
		)
	],
)

edit(
	"README.md",
	[
		(
			'''- 预跑与快进期间 scheduler 必须关闭；后台补库 worker 保持运行。生成器运行期间不切换站点数据库。''',
			'''- 预跑与快进期间 scheduler 必须关闭；后台补库 worker 保持运行。生成器运行期间不切换站点数据库。
- 演示中途换库（快进、`Alt+R`、`Alt+数字`）只取用一份就绪副本，不在后台补库：补库期间整库导入使 desk 接口响应由约 8 毫秒拖到二十多秒（S8 R8 SB FD-013 实测，IT-003 第 6 条的退路）。用掉的副本在「回到演示前」或点「补齐快照」时补回。某幕两份副本都用完时，仍会从该幕原始快照自行补回再切入（约 30～70 秒），只补这一幕。''',
		)
	],
)
print("ok")
