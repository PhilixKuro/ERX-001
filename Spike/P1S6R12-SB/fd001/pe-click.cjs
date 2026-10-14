// R12 SB FD-001：测试站 6787 实点开账 PE 与日记账凭证的「会计凭证」按钮，读跳转后总账报表的筛选。
// 用法（项目根）：node Spike/P1S6R12-SB/fd001/pe-click.cjs <round> <PE 单号> [JE 单号]
const fs = require('node:fs');
const { open } = require('../../P1S6R4-cdp.cjs');
const [round = 'patched', pe, je] = process.argv.slice(2);
const OUT = `Spike/P1S6R12-SB/fd001/${round}`;
fs.mkdirSync(OUT, { recursive: true });
(async () => {
	const c = await open();
	const report = { round, cases: [] };
	try {
		for (const [dt, name] of [['Payment Entry', pe], ['Journal Entry', je]].filter(x => x[1])) {
			await c.evaluate(`frappe.set_route('Form', ${JSON.stringify(dt)}, ${JSON.stringify(name)});true`);
			await c.until(`cur_frm?.doc?.name===${JSON.stringify(name)} && frappe.request.ajax_count===0`, 30000);
			await c.pause(1500);
			const row = { doctype: dt, name };
			row.buttons = await c.evaluate(`(() => {
				const tb = cur_frm.page.inner_toolbar[0];
				const label = encodeURIComponent(__('Ledger'));
				return {
					toolbar: [...tb.querySelectorAll('button[data-label="' + label + '"]')].length,
					grouped: [...tb.querySelectorAll('.dropdown-item[data-label="' + label + '"]')].length,
				};
			})()`);
			await c.screenshot(`${OUT}/${dt === 'Payment Entry' ? 'pe' : 'je'}-form.png`);
			await c.evaluate(`(() => {
				const label = encodeURIComponent(__('Ledger'));
				const el = cur_frm.page.inner_toolbar[0].querySelector('[data-label="' + label + '"]');
				el.click(); return true;
			})()`);
			await c.until(`frappe.get_route()[0]==='query-report' && frappe.query_report?.report_name==='General Ledger' && frappe.request.ajax_count===0`, 30000);
			await c.pause(2500);
			row.report_filters = await c.evaluate(`(() => { const f = frappe.query_report.get_filter_values(); return {voucher_no: f.voucher_no, show_opening_entries: f.show_opening_entries || 0, company: f.company}; })()`);
			row.rows = await c.evaluate(`(frappe.query_report.data || []).filter(r => r.voucher_no === ${JSON.stringify(name)}).length`);
			await c.screenshot(`${OUT}/${dt === 'Payment Entry' ? 'pe' : 'je'}-ledger.png`);
			report.cases.push(row);
		}
	} finally {
		fs.writeFileSync(`${OUT}/result.json`, JSON.stringify(report, null, 1));
		console.log(JSON.stringify(report, null, 1));
		await c.close();
	}
})().catch(e => { console.error(e); process.exit(1); });
