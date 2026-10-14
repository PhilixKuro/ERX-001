// R12 SB FD-016 ③④：对 invoice_list.js／desk_patches.js 的临时副本逐个打变异，
// 跑 test_invoice_status.cjs，每个变异应至少红一条。原文件不动：把测试与变异后的 js 放进临时目录跑。
// 用法（项目根）：node Spike/P1S6R12-SB/fd016/mutate.cjs
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const APP = path.resolve('frappe-bench/apps/frappe_china/frappe_china');
const MUTANTS = [
	['invoice_list.js', 'badge 不取 context（报告列的 :13 条件）', 'result[0] = __(doc.status, null, doctype);', ''],
	['invoice_list.js', '筛选不补 df.context（报告列的 :29）', 'field.df.context = doctype;', ''],
	['desk_patches.js', 'Select 不传 context（报告列的 :241）', 'return context ? __(text, null, context) : __(text);', 'return __(text);'],
	['desk_patches.js', '库存类开账判定恒假', 'const opening = this.frm?.doc?.purpose', 'const opening = false && this.frm?.doc?.purpose'],
	['desk_patches.js', '库存类开账不带 show_opening_entries', 'show_opening_entries: 1,\n\t\t\t\t\t\t\t\tignore_prepared_report', 'ignore_prepared_report'],
];
const results = [];
for (const [file, label, from, to] of MUTANTS) {
	const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'fd016-'));
	fs.mkdirSync(path.join(dir, 'public/js'), { recursive: true });
	fs.mkdirSync(path.join(dir, 'tests'));
	for (const f of ['invoice_list.js', 'desk_patches.js']) {
		let text = fs.readFileSync(path.join(APP, 'public/js', f), 'utf8');
		if (f === file) {
			const norm = text.replace(/\r\n/g, '\n');
			if (!norm.includes(from)) throw Error(`mutant anchor not found: ${label}`);
			text = norm.replace(from, to);
		}
		fs.writeFileSync(path.join(dir, 'public/js', f), text);
	}
	fs.copyFileSync(path.join(APP, 'tests/test_invoice_status.cjs'), path.join(dir, 'tests/test_invoice_status.cjs'));
	const run = spawnSync(process.execPath, ['--test', path.join(dir, 'tests/test_invoice_status.cjs')], { encoding: 'utf8' });
	const fail = Number((run.stdout.match(/ℹ fail (\d+)/) || [])[1]);
	results.push({ label, fail, killed: fail > 0 });
	fs.rmSync(dir, { recursive: true, force: true });
}
console.log(JSON.stringify(results, null, 1));
process.exitCode = results.every((r) => r.killed) ? 0 : 1;
