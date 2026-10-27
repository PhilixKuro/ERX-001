"""S8 R8 SB FD-011 edit script: start-demo entry on the rehearsal page, refuse to start on base/work db."""

import os

ROOT = "d:/ERX-001/frappe-bench/apps/frappe_debug"


def edit(rel, pairs):
	path = os.path.join(ROOT, rel)
	with open(path, encoding="utf-8") as handle:
		text = handle.read()
	for old, new in pairs:
		assert text.count(old) == 1, (rel, old[:80])
		text = text.replace(old, new)
	with open(path, "w", encoding="utf-8") as handle:
		handle.write(text)


edit(
	"frappe_debug/demo/progress.py",
	[
		(
			'''@frappe.whitelist(methods=["POST"])
def save_progress(''',
			'''def _refuse_clean_database(mode: str = "live") -> None:
	"""The clean base never carries a show; the work database only a rehearsal (FD-011)."""
	from frappe_debug.demo.registry import get_registry

	registered = get_registry()
	db_name = frappe.conf.db_name
	if registered.get("base_db") and db_name == registered["base_db"]:
		frappe.throw("当前是演示前的清洁基库，请在彩排页点「开始演示」进入第 1 幕", frappe.ValidationError)
	if mode != "rehearsal" and registered.get("work_db") and db_name == registered["work_db"]:
		frappe.throw("当前是整场预跑的工作库，不能现场开播", frappe.ValidationError)


@frappe.whitelist()
def assert_can_start(mode: str = "live") -> dict:
	if frappe.session.user != "Administrator":
		frappe.throw("仅 Administrator 可开始演示", frappe.PermissionError)
	_refuse_clean_database(mode)
	return {"db": frappe.conf.db_name}


@frappe.whitelist(methods=["POST"])
def save_progress(''',
		),
		(
			'''	progress = frappe.get_doc("Demo Progress", "Demo Progress")
	progress.update({"act": act, "step": step, "active": 1})''',
			'''	_refuse_clean_database("rehearsal")
	progress = frappe.get_doc("Demo Progress", "Demo Progress")
	progress.update({"act": act, "step": step, "active": 1})''',
		),
	],
)

edit(
	"frappe_debug/public/js/demo/runner.js",
	[
		(
			'''		const loaded = config || await frappe.xcall("frappe_debug.demo.config.get_demo_config");
		demo.validate(loaded);''',
			'''		// FD-011: never start a show on the clean base (it would write act 1 into it) or the work db.
		await frappe.xcall("frappe_debug.demo.progress.assert_can_start", { mode: mode() });
		const loaded = config || await frappe.xcall("frappe_debug.demo.config.get_demo_config");
		demo.validate(loaded);''',
		),
		(
			'''	demo.return_to_base = async () => {''',
			'''	// FD-011: the rehearsal page's entry for each show; the transit page moves to act 1's copy.
	demo.start_show = async () => {
		if (frappe.session.user !== "Administrator") throw Error("仅 Administrator 可开始演示");
		const snapshots = await frappe.xcall("frappe_debug.demo.snapshot.snapshot_status");
		if (!Object.keys(snapshots.acts || {}).length) throw Error("还没有快照，请先整场预跑");
		if (snapshots.work_db) throw Error("整场预跑的工作库还在，请先等预跑结束");
		const loaded = await frappe.xcall("frappe_debug.demo.config.get_demo_config");
		demo.validate(loaded);
		demo.config = loaded;
		sessionStorage.setItem("frappe_debug_mode", "live");
		return demo.switch_act(1, "jump");
	};
	demo.return_to_base = async () => {''',
		),
	],
)

edit(
	"frappe_debug/frappe_debug/page/demo_rehearsal/demo_rehearsal.js",
	[
		(
			'''	page.main.append("<p class='text-muted'>演示结束后，先回到演示前，再清理快照库。</p>");''',
			'''	page.main.append("<p class='text-muted'>每场开讲前回到演示前、就绪检查全绿后点「开始演示」；全部演示结束后再清理快照库。</p>");''',
		),
		(
			'''	page.add_inner_button("开始整场预跑", async () => {''',
			'''	// FD-011: each show starts here; the transit page switches into act 1's ready copy.
	page.add_inner_button("开始演示", async () => {
		try { await frappe_debug.demo.start_show(); }
		catch (error) { frappe.msgprint({title: "演示未开始", message: frappe.utils.escape_html(error.message || String(error)), indicator: "red"}); }
	});
	page.add_inner_button("开始整场预跑", async () => {''',
		),
	],
)

edit(
	"README.md",
	[
		(
			'''1. 开讲前打开 `/desk/demo-rehearsal` 看「开讲前就绪检查」：停在第 1 幕主用库时显示 17/18 即为就绪（当前所在库计为已用）；少于 17 时点「补齐快照」并等待。
2. 打开 `data/demo.yaml` 中的起始业务流程页，以演示管理员登录；运行器由页面加载。''',
			'''每场演示都从演示前的清洁基库开始（FD-011 裁决 A）：

1. 以演示管理员登录，打开 `/desk/demo-rehearsal`。若上一场没点「回到演示前」，先点它；回到基库后看「开讲前就绪检查」，18/18 全部就绪再开讲，少于 18 时点「补齐快照」并等待。整场预跑刚结束时站点停在第 1 幕主用库，可以不回基库直接开讲。
2. 点「开始演示」：中转页把站点切到第 1 幕的就绪副本并打开起始页，运行器随之启动。运行器在清洁基库和预跑工作库上拒绝开播，不会把第 1 幕写进基库。''',
		),
		(
			'''6. 演示结束后点「回到演示前」：后台会把本场用掉的快照逐份补回，下一场无须重跑预跑。要彻底清理时，等就绪检查全绿后再点「清理快照库」，不要在当前连接指向快照库时清理。''',
			'''6. 演示结束后在彩排页点「回到演示前」：后台会把本场用掉的快照逐份补回，下一场无须重跑预跑，从第 1 条重新开始。要彻底清理时，等就绪检查全绿后再点「清理快照库」，不要在当前连接指向快照库时清理。''',
		),
	],
)
print("ok")
