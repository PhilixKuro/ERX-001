// R13 F p2：在仓库外副本上逐个打变异，跑 node --test，看是否有用例变红。
// 用法：node mutate.cjs <副本根目录（含 public/js 与 tests）>
const fs = require('node:fs');
const path = require('node:path');
const { spawnSync } = require('node:child_process');

const root = process.argv[2];
const js = (f) => path.join(root, 'public/js', f);
const MUTANTS = [
	['FD-001 PE 分组回到 "fa fa-table"', 'opening_ledger.js', 'is_journal ? __("View") : undefined', 'is_journal ? __("View") : "fa fa-table"'],
	['FD-001 JE 也不带分组', 'opening_ledger.js', 'is_journal ? __("View") : undefined', 'undefined'],
	['FD-001 去掉 remove_custom_button', 'opening_ledger.js', 'frm.remove_custom_button(__("Ledger"), group);', ''],
	['FD-001 去掉 show_opening_entries', 'opening_ledger.js', 'show_opening_entries: 1,', ''],
	['FD-019 去掉 :not(.frappe-card)', 'desk_patches.js', '.timeline-content:not(.frappe-card) b', '.timeline-content b'],
	['FD-019 :not 挂错层（挂在 .new-timeline）', 'desk_patches.js', '.new-timeline .timeline-content:not(.frappe-card) b', '.new-timeline:not(.frappe-card) .timeline-content b'],
	['FD-018 replacer 回到字符串', 'desk_patches.js', 'html.replace(wrong, () => right)', 'html.replace(wrong, right)'],
	['FD-020 回到无保护写法', 'desk_patches.js', 'const formatters = frappe.form?.formatters;', 'const formatters = frappe.form.formatters;'],
	['FD-020 缺接点不告警', 'desk_patches.js', 'console.warn("[frappe_china] frappe.form.formatters.Data is unavailable; Select formatter patch skipped");', ''],
	['FD-016③ Select 去 df.parent', 'desk_patches.js', 'const context = df?.parent || doc?.doctype;', 'const context = doc?.doctype;'],
	['FD-016③ Select 去 doc.doctype 回退', 'desk_patches.js', 'const context = df?.parent || doc?.doctype;', 'const context = df?.parent;'],
	['FD-016③ 徽标去 context', 'invoice_list.js', 'result[0] = __(doc.status, null, doctype);', 'result[0] = __(doc.status);'],
	['FD-016③ 徽标判定放宽（On Hold 也改）', 'invoice_list.js', 'if (result && result[2] === "status,=," + doc.status) {', 'if (result) {'],
	['FD-016③ 筛选不补 context', 'invoice_list.js', 'field.df.context = doctype;', ''],
	['FD-016③ 筛选不清 last_options', 'invoice_list.js', 'field.last_options = null;', ''],
	['FD-016③ 筛选不 set_options', 'invoice_list.js', 'field.set_options();', ''],
	['FD-016③ 徽标去幂等标记', 'invoice_list.js', 'settings.__frappe_china_wrapped = true;', ''],
	['FD-016③ onload 不委托原方法', 'invoice_list.js', 'const result = original.apply(this, arguments);', 'const result = undefined;'],
];

function run() {
	const r = spawnSync(process.execPath, ['--test', ...fs.readdirSync(path.join(root, 'tests')).filter((f) => f.endsWith('.cjs')).map((f) => path.join(root, 'tests', f))], { encoding: 'utf8' });
	const out = r.stdout + r.stderr;
	const pass = +(out.match(/ℹ pass (\d+)/) || [])[1];
	const fail = +(out.match(/ℹ fail (\d+)/) || [])[1];
	const failed = [...out.matchAll(/^✖ (.+?) \(/gm)].map((m) => m[1]).filter((n) => !/^tests\//.test(n));
	return { pass, fail, failed };
}

const base = run();
console.log(`基线 pass=${base.pass} fail=${base.fail}`);
for (const [name, file, from, to] of MUTANTS) {
	const p = js(file);
	const orig = fs.readFileSync(p, 'utf8');
	const n = orig.split(from).length - 1;
	if (n !== 1) { console.log(`[跳过] ${name}：匹配 ${n} 处`); continue; }
	fs.writeFileSync(p, orig.replace(from, () => to));
	const r = run();
	fs.writeFileSync(p, orig);
	console.log(`${r.fail > 0 ? '[杀死]' : '[存活]'} ${name}：fail=${r.fail}${r.failed.length ? ' ← ' + [...new Set(r.failed)].slice(0, 4).join(' | ') : ''}`);
}
const after = run();
console.log(`还原后 pass=${after.pass} fail=${after.fail}`);
