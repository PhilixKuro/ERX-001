const assert = require('node:assert/strict');
const path = require('node:path');
const { open } = require('../P1S6R4-cdp.cjs');

(async () => {
	const c = await open();
	try {
		assert.equal(await c.evaluate('frappe.boot.sitename'), 'test.localhost');
		const report = { site: 'test.localhost' };
		for (const [doctype, route, expected] of [
			['CRM Lead Status', 'leads', [['New', '新线索'], ['Contacted', '已联系'], ['Nurture', '培育中'], ['Qualified', '合格'], ['Converted', '已转化'], ['Unqualified', '不合格'], ['Junk', '无效']]],
			['CRM Deal Status', 'deals', [['Qualification', '需求确认'], ['Demo/Making', '方案演示'], ['Proposal/Quotation', '报价'], ['Negotiation', '谈判中'], ['Ready to Close', '待成交'], ['Won', '赢单'], ['Lost', '未成交']]],
		]) {
			await c.navigate(`http://test.localhost:6787/crm/${route}`);
			await c.until("document.querySelector('#app')?.innerText.length > 30");
			await c.evaluate("(() => { const input = [...document.querySelectorAll('#app input')].find(item => item.placeholder === '状态'); input?.click(); input?.focus(); return !!input; })()");
			await c.pause(500);
			const values = await c.evaluate(`(async () => {
				const query = new URLSearchParams({ fields: JSON.stringify(['name']), limit: '100' });
				const response = await fetch('/api/resource/${encodeURIComponent(doctype)}?' + query);
				const list = (await response.json()).data;
				const text = document.querySelector('#app').innerText;
				return JSON.stringify({ list: list.map(row => row.name), text });
			})()`);
			const data = JSON.parse(values);
			for (const [source] of expected) {
				assert(data.list.includes(source), `${doctype}: source value changed: ${source}`);
			}
			report[route] = { statuses: expected.map(([, translated]) => translated), stored_values: data.list };
			await c.screenshot(path.join(__dirname, `SL008-crm-${route}-status.png`));
		}
		await c.navigate('http://test.localhost:6787/desk');
		await c.until('!!window.frappe?.boot');
		const drafts = await c.evaluate(`(async () => {
			const query = new URLSearchParams({ filters: JSON.stringify({ docstatus: 0 }), fields: JSON.stringify(['name', 'supplier', 'company']), limit: '10' });
			return JSON.stringify((await (await fetch('/api/resource/Purchase Receipt?' + query)).json()).data);
		})()`);
		report.purchase_receipt_drafts = JSON.parse(drafts);
		await c.evaluate("frappe.set_route('query-report', 'Stock and Account Value Comparison')");
		await c.until("frappe.query_report?.report_name === 'Stock and Account Value Comparison'");
		await c.until("frappe.query_report?.filters?.length > 0");
		await c.evaluate("frappe.query_report.set_filter_value('company', '_S6R6 测试公司'); frappe.query_report.refresh(); true");
		await c.until("document.body.innerText.includes('库存与账面金额无差异')", 30000);
		const reconciliation = await c.evaluate(`JSON.stringify({
			filters: frappe.query_report.get_filter_values(),
			rows: frappe.query_report.data?.length,
			message: document.querySelector('.no-result')?.innerText || document.body.innerText.slice(-400)
		})`);
		report.reconciliation = JSON.parse(reconciliation);
		await c.screenshot(path.join(__dirname, 'SL008-reconciliation.png'));
		const operations = await c.evaluate(`(async () => {
			const query = new URLSearchParams({ fields: JSON.stringify(['name']), limit: '10' });
			return JSON.stringify((await (await fetch('/api/resource/Operation?' + query)).json()).data);
		})()`);
		const operation = JSON.parse(operations)[0];
		assert(operation, 'test.localhost has no Operation record for the form check');
		await c.evaluate(`frappe.set_route('Form', 'Operation', ${JSON.stringify(operation.name)})`);
		await c.until("window.cur_frm?.doctype === 'Operation'");
		await c.evaluate("cur_frm.set_value('cn_piece_rate', 0.004)");
		await c.pause(300);
		const pieceRate = await c.evaluate(`JSON.stringify({
			name: cur_frm.doc.name,
			value: document.querySelector('[data-fieldname="cn_piece_rate"] input')?.value,
			precision: cur_frm.get_field('cn_piece_rate')?.df.precision
		})`);
		assert.equal(Number(JSON.parse(pieceRate).value), 0.004, 'Operation form must preserve the 0.004 rate');
		report.piece_rate_form = JSON.parse(pieceRate);
		await c.screenshot(path.join(__dirname, 'SL008-piece-rate-form.png'));
		console.log(JSON.stringify(report));
	} finally {
		await c.close();
	}
})().catch(error => {
	console.error(error);
	process.exitCode = 1;
});
