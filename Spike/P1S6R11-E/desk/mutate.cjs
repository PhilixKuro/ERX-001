// R11 E: mutation check for desk_patches.js / independent_app_labels.js.
// Copies source + test into ./mut/<id>/, applies one textual mutation, runs node --test, reports failures.
// node mutate.cjs <frappe_china_app_dir>
const fs = require('node:fs');
const path = require('node:path');
const { spawnSync } = require('node:child_process');

const app = process.argv[2];
const lf = (s) => s.replace(/\r\n/g, '\n');
const deskSrc = lf(fs.readFileSync(path.join(app, 'frappe_china/public/js/desk_patches.js'), 'utf8'));
const deskTest = fs.readFileSync(path.join(app, 'frappe_china/tests/test_desk_patches.cjs'), 'utf8');
const ialSrc = lf(fs.readFileSync(path.join(app, 'frappe_china/public/js/independent_app_labels.js'), 'utf8'));
const ialTest = fs.readFileSync(path.join(app, 'frappe_china/tests/test_independent_app_labels.cjs'), 'utf8');

const M = [
	['M01 filter: no translation (raw English template)', 'desk',
		'this.filter_button.attr("title", translate(count > 1 ? "{0} Filters Applied" : "{0} Filter Applied", [count]));',
		'this.filter_button.attr("title", `${count} Filter${count > 1 ? "s" : ""} Applied`);'],
	['M02 filter: always singular key', 'desk',
		'translate(count > 1 ? "{0} Filters Applied" : "{0} Filter Applied", [count])',
		'translate("{0} Filter Applied", [count])'],
	['M03 filter: skip n=0 (only write title when filters exist)', 'desk',
		'if (isZh() && this.filter_button?.attr && this.filters) {',
		'if (isZh() && this.filter_button?.attr && this.filters?.length) {'],
	['M04 filter: ignore language', 'desk',
		'if (isZh() && this.filter_button?.attr && this.filters) {',
		'if (this.filter_button?.attr && this.filters) {'],
	['M05 header: return native html', 'desk',
		'return wrong === right ? html : html.replace(wrong, right);',
		'return html;'],
	['M06 header: replaceAll instead of first only', 'desk',
		'html.replace(wrong, right)', 'html.split(wrong).join(right)'],
	['M07 header: drop doctype fallback', 'desk',
		'df.parent || this.doctype', 'df.parent'],
	['M08 header: ignore language', 'desk',
		'if (!isZh() || typeof html !== "string" || !df?.label) return html;',
		'if (typeof html !== "string" || !df?.label) return html;'],
	['M09 button: no translation', 'desk',
		'if (isZh() && group && typeof label === "string") args[0] = translate(label);', ''],
	['M10 button: translate ungrouped too', 'desk',
		'if (isZh() && group && typeof label === "string")', 'if (isZh() && typeof label === "string")'],
	['M11 button: delegate only 3 args', 'desk',
		'return native.apply(this, args);\n\t\t}\n\t);\n\n\t// R9 A24',
		'return native.call(this, args[0], args[1], args[2]);\n\t\t}\n\t);\n\n\t// R9 A24'],
	['M12 button: ignore language', 'desk',
		'if (isZh() && group && typeof label === "string")', 'if (group && typeof label === "string")'],
	['M13 report: no translation', 'desk',
		'const shown = typeof value === "string" && value ? translate(value) : value;', 'const shown = value;'],
	['M14 report: mutate row data instead of display value', 'desk',
		'return format.call(this, shown, row, col, data, filter);',
		'if (data && typeof data[column.fieldname] === "string") data[column.fieldname] = shown; return format.call(this, shown, row, col, data, filter);'],
	['M15 report: all fields of whitelisted report', 'desk',
		'if (!fields.includes(column?.fieldname) || typeof column.format !== "function") continue;',
		'if (typeof column.format !== "function") continue;'],
	['M16 report: drop receiver (format(...) not format.call(this,...))', 'desk',
		'return format.call(this, shown, row, col, data, filter);', 'return format(shown, row, col, data, filter);'],
	['M17 report: drop typeof/empty guard', 'desk',
		'typeof value === "string" && value ? translate(value) : value', 'value != null ? translate(value) : value'],
	['M18 timeline: any <b> in document', 'desk',
		'root.querySelectorAll?.(".new-timeline .timeline-content b")', 'root.querySelectorAll?.("b")'],
	['M19 timeline: only null, not undefined', 'desk',
		'if (node.textContent === "null" || node.textContent === "undefined")', 'if (node.textContent === "null")'],
	['M20 timeline: substring match', 'desk',
		'if (node.textContent === "null" || node.textContent === "undefined")', 'if (/null|undefined/.test(node.textContent))'],
	['M21 timeline: ignore language', 'desk',
		'const fix_timeline_nulls = (root) => {\n\t\tif (!isZh()) return;', 'const fix_timeline_nulls = (root) => {'],
	['M22 timeline: no idempotent mark', 'desk',
		'if (typeof document !== "undefined" && document.body && !document.__frappe_china_timeline_nulls) {',
		'if (typeof document !== "undefined" && document.body) {'],
	['M23 dialog: no title check', 'desk',
		'if (this.title !== translate(title)) continue;', ''],
	['M24 dialog: no fieldtype check', 'desk',
		'if (labels[field?.fieldname] && field.fieldtype === "Date")', 'if (labels[field?.fieldname])'],
	['M25 dialog: relabel after make (too late)', 'desk',
		'function () {\n\t\t\tif (isZh()) {\n\t\t\t\tfor (const [title, labels]',
		'function () {\n\t\t\tconst __r = native.apply(this, arguments);\n\t\t\tif (isZh()) {\n\t\t\t\tfor (const [title, labels]'],
	['M25b dialog: drop make return value', 'desk',
		'\t\t\treturn native.apply(this, arguments);\n\t\t}\n\t);\n\n\t// The legacy',
		'\t\t\tnative.apply(this, arguments);\n\t\t}\n\t);\n\n\t// The legacy'],
	['M25c dialog: drop make receiver', 'desk',
		'\t\t\treturn native.apply(this, arguments);\n\t\t}\n\t);\n\n\t// The legacy',
		'\t\t\treturn native.apply(undefined, arguments);\n\t\t}\n\t);\n\n\t// The legacy'],
	['M25d header: drop receiver', 'desk',
		'const html = native.apply(this, arguments);', 'const html = native.apply({columns: this.columns, native_html: this.native_html}, arguments);'],
	['M25e raven: no applyContextKeys call in raven branch (runtime wiring)', 'ial',
		"applyContextKeys(root.frappe, RAVEN_CONTEXT_KEYS, key => console.warn(`[frappe_china] missing Raven context entry: ${key}`));", ''],
	['M26 dialog: ignore language', 'desk',
		'function () {\n\t\t\tif (isZh()) {\n\t\t\t\tfor (const [title, labels]', 'function () {\n\t\t\tif (true) {\n\t\t\t\tfor (const [title, labels]'],
	['M27 patch_method: no idempotent mark check', 'desk',
		'if (proto[method][mark]) return;', ''],
	['M28 patch_method: throw when missing', 'desk',
		'console.warn(`[frappe_china] ${owner_name}.${method} is unavailable; patch skipped`);\n\t\t\treturn;',
		'throw new Error("missing");'],
	['M29 patch_method: drop return value', 'desk',
		'const result = native.apply(this, arguments);\n\t\t\tif (isZh() && this.filter_button',
		'native.apply(this, arguments); const result = undefined;\n\t\t\tif (isZh() && this.filter_button'],
	['M30 raven: overwrite even when context entry missing', 'ial',
		"if (!value) {warn(key); continue;}", "if (!value) {warn(key);}"],
	['M31 raven: no warn when missing', 'ial',
		"if (!value) {warn(key); continue;}", "if (!value) {continue;}"],
	['M32 raven: wrong separator', 'ial',
		"frappe?._messages?.[`${key}:${context}`]", "frappe?._messages?.[`${key}|${context}`]"],
	['M33 raven: bridge overwrites runtime entries', 'ial',
		"Object.assign({}, frappe.boot.__messages, frappe._messages || {})", "Object.assign({}, frappe._messages || {}, frappe.boot.__messages)"],
];

const out = path.join(__dirname, 'mut');
fs.rmSync(out, { recursive: true, force: true });
const results = [];
for (const [name, target, from, to] of M) {
	const id = name.split(' ')[0];
	const dir = path.join(out, id);
	fs.mkdirSync(path.join(dir, 'public/js'), { recursive: true });
	fs.mkdirSync(path.join(dir, 'tests'), { recursive: true });
	const src = target === 'desk' ? deskSrc : ialSrc;
	if (!src.includes(from)) { results.push({ id, name, status: 'PATTERN-NOT-FOUND' }); continue; }
	const mutated = src.replace(from, to);
	if (mutated === src) { results.push({ id, name, status: 'NO-OP' }); continue; }
	fs.writeFileSync(path.join(dir, 'public/js/desk_patches.js'), target === 'desk' ? mutated : deskSrc);
	fs.writeFileSync(path.join(dir, 'public/js/independent_app_labels.js'), target === 'ial' ? mutated : ialSrc);
	const testName = target === 'desk' ? 'test_desk_patches.cjs' : 'test_independent_app_labels.cjs';
	fs.writeFileSync(path.join(dir, 'tests', testName), target === 'desk' ? deskTest : ialTest);
	const r = spawnSync(process.execPath, ['--test', '--test-reporter=tap', path.join(dir, 'tests', testName)], { encoding: 'utf8' });
	const failed = [...r.stdout.matchAll(/^not ok \d+ - (.+)$/gm)].map((m) => m[1]);
	results.push({ id, name, status: failed.length ? 'KILLED' : 'SURVIVED', failed });
}
for (const r of results) console.log(`${r.status.padEnd(17)} ${r.name}${r.failed?.length ? '\n    -> ' + r.failed.join('\n    -> ') : ''}`);
