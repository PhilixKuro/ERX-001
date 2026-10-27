"""S8 R8 SB: SPC preview site switch, so the candidate plan is screened from a full rehearsal with the acts.

User ruling A (2026-10-27): the old README flow ran only the generator on the isolated site, so the
acts' D1 documents were missing and every later plan key drifted from the real rehearsal.
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
	"frappe_debug/scenario/quality.py",
	[
		(
			'''def _require_quality_plan_site():''',
			'''PREVIEW_SITE_KEY = "frappe_debug_quality_preview"


def is_quality_preview_site() -> bool:
	"""An isolated site whose full rehearsal screens a new SPC plan (site config flag, S8 R8 SB).

	Its rehearsal generates without a plan and its acts read no frozen samples; the demo sites can
	never be one. Set with ``bench --site <site> set-config -p frappe_debug_quality_preview 1``.
	"""
	return frappe.local.site not in QUALITY_PLAN_SITES and frappe.conf.get(PREVIEW_SITE_KEY) in (1, "1", True)


def _require_quality_plan_site():''',
		)
	],
)

edit(
	"frappe_debug/demo/workspace.py",
	[
		(
			'''	if not frappe.utils.cint(quality_preview):''',
			'''	from frappe_debug.scenario.quality import is_quality_preview_site

	if not frappe.utils.cint(quality_preview) and not is_quality_preview_site():''',
		)
	],
)

edit(
	"frappe_debug/scenario/runner.py",
	[
		(
			'''		return generate.__wrapped__(from_date, to_date, job_id=job_id_arg)''',
			'''		from frappe_debug.scenario.quality import is_quality_preview_site

		return generate.__wrapped__(
			from_date, to_date, job_id=job_id_arg, preview_quality_schedule=is_quality_preview_site()
		)''',
		)
	],
)

edit(
	"frappe_debug/demo/progress.py",
	[
		(
			'''def extend_bootinfo(bootinfo):
	bootinfo.frappe_debug_demo = get_progress()''',
			'''def extend_bootinfo(bootinfo):
	from frappe_debug.scenario.quality import is_quality_preview_site

	bootinfo.frappe_debug_demo = get_progress()
	bootinfo.frappe_debug_quality_preview = is_quality_preview_site()''',
		)
	],
)

edit(
	"frappe_debug/public/js/demo/rehearsal.js",
	[
		(
			'''			if (!ALLOWED_REHEARSAL_SITES.has(frappe.boot.sitename)) throw Error("整场预跑仅允许 s8dev.localhost 或 erx.localhost");''',
			'''			// An isolated SPC preview site may also run the full rehearsal, to screen a new plan (S8 R8 SB).
			if (!ALLOWED_REHEARSAL_SITES.has(frappe.boot.sitename) && !frappe.boot.frappe_debug_quality_preview) throw Error("整场预跑仅允许 s8dev.localhost、erx.localhost 或已标记的 SPC 预览站");''',
		)
	],
)

edit(
	"README.md",
	[
		(
			'''1. 另备一座隔离清洁站（只装同版本 app、从清洁基准恢复，不要用演示站），配置 `root_password`，scheduler 保持关闭。以 Administrator 在该站控制台调 `frappe.xcall('frappe_debug.demo.workspace.prepare_work', {quality_preview: 1})` 建工作库（预览模式跳过计划检查），就绪后用 `switch_to_db` 切入工作库（参考 `Spike/P1S8R6-D/preview-switch-work.cjs`）。
2. 在该站以预览模式按本次预跑终点生成全年日链：`runner.generate(S, E-1, preview_quality_schedule=True)`（约 30 分钟；参考脚本 `Spike/P1S8R6-D/quality-preview-segment.py`）。
3. 生成到 E−1 后导出：`bench --site <隔离站> execute frappe_debug.scenario.quality.export_quality_sample_plan`（参考 `Spike/P1S8R6-D/export-quality-plan.py`；已有计划时拒绝覆盖，先把旧文件改名归档）。
4. 把导出的 `quality-plan.json` 拷到演示站同一路径，再开始整场预跑。隔离站用完撤回 `root_password`。''',
			'''计划必须从**带各幕的整场彩排**筛出来：第 1～5 幕在 D1（落在 SPC 窗口内）现场建订单、工单与工序卡，只跑生成器不演各幕时这些单据不存在，D1 之后的单据号全部错位，演示站预跑会在第 2 段首日报「缺少已筛选SPC候选」（S8 R8 SB 实测）。

1. 另备一座隔离清洁站（只装同版本 app、从演示站同一份清洁基准恢复并 migrate 到同一代码，不要用演示站），配置 `root_password`，scheduler 保持关闭，标记为 SPC 预览站：`bench --site <隔离站> set-config -p frappe_debug_quality_preview 1`。演示站名单（`erx`、`s8dev`）上的站即使设了标记也不生效。
2. 在隔离站彩排页点「开始整场预跑」。预览站的彩排建工作库不查计划、生成器以预览模式出质检读数、第 7 幕发货质检不读候选，其余与演示站整场预跑相同（约 50 分钟）。
3. 预跑结束后把站点切到工作库（`switch_to_db`，库名见 `snapshot_status` 的 `work_db`），导出：`bench --site <隔离站> execute frappe_debug.scenario.quality.export_quality_sample_plan`（已有计划时拒绝覆盖，先把旧文件改名归档）。
4. 把导出的 `quality-plan.json` 拷到演示站同一路径，再在演示站开始整场预跑。须与隔离站预跑在同一天：计划指纹含预跑终点 E。隔离站用完撤回 `root_password` 与预览标记。''',
		)
	],
)

edit(
	"frappe_debug/tests/test_quality.py",
	[
		(
			'''	def test_outgoing_inspection_uses_the_frozen_candidate_for_the_delivery_note(self):''',
			'''	def test_quality_preview_flag_only_marks_isolated_sites(self):
		"""S8 R8 SB：SPC 预览站按站点配置认，演示站名单上的站永远不是预览站。"""
		from frappe_debug.scenario.quality import PREVIEW_SITE_KEY, is_quality_preview_site

		for site, value, expected in (
			("s8r9.localhost", 1, True),
			("s8r9.localhost", "1", True),
			("s8r9.localhost", None, False),
			("s8r9.localhost", 0, False),
			("erx.localhost", 1, False),
			("s8dev.localhost", 1, False),
		):
			conf = frappe._dict({key: item for key, item in frappe.conf.items() if key != PREVIEW_SITE_KEY})
			if value is not None:
				conf[PREVIEW_SITE_KEY] = value
			with self.subTest(site=site, value=value), patch.object(frappe.local, "site", site), patch.object(
				frappe.local, "conf", conf
			):
				self.assertIs(is_quality_preview_site(), expected)

	def test_queued_generation_previews_only_on_a_preview_site(self):
		from frappe_debug.scenario import runner

		for preview in (True, False):
			with (
				self.subTest(preview=preview),
				patch("frappe_debug.scenario.quality.is_quality_preview_site", return_value=preview),
				patch.object(runner.generate, "__wrapped__") as generate,
			):
				runner._run_generate("2026-01-08", "2026-01-09", "job-x")
			self.assertIs(generate.call_args.kwargs["preview_quality_schedule"], preview)

	def test_outgoing_inspection_uses_the_frozen_candidate_for_the_delivery_note(self):''',
		)
	],
)

edit(
	"frappe_debug/tests/test_rehearsal.cjs",
	[
		(
			''' const other=setup();
 other.frappe.boot.sitename='customer.example';
 await assert.rejects(other.rehearsal.start(),/仅允许 s8dev\\.localhost 或 erx\\.localhost/);
 assert.equal(other.calls.length,0);
});''',
			''' const other=setup();
 other.frappe.boot.sitename='customer.example';
 await assert.rejects(other.rehearsal.start(),/仅允许 s8dev\\.localhost、erx\\.localhost 或已标记的 SPC 预览站/);
 assert.equal(other.calls.length,0);

 // S8 R8 SB: an isolated site marked as SPC preview may run the full rehearsal
 const preview=setup();
 preview.frappe.boot.sitename='s8r9.localhost';
 preview.frappe.boot.frappe_debug_quality_preview=true;
 await assert.rejects(preview.rehearsal.start(),/请先切回清洁基库/);
 assert.equal(preview.calls.some(([method])=>method.endsWith('get_demo_config')),true);
});''',
		)
	],
)
print("ok")
