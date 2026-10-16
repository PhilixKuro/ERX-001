const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {open} = require('../P1S6R4-cdp.cjs');

async function main() {
	const browser = await open('http://erx.localhost:8000');
	try {
		assert.equal(await browser.evaluate('frappe.boot.sitename'), 'erx.localhost');
		await browser.evaluate(`frappe.new_doc('Work Order')`);
		await browser.until(`window.cur_frm?.doctype === 'Work Order' && cur_frm.doc.__islocal && frappe.request.ajax_count === 0`, 60000);
		const workOrder = await browser.evaluate(`({islocal: !!cur_frm.doc.__islocal, recommendationLoaded: String(cur_frm.meta.__js || '').includes('frappe_china.production.bom_selection.recommend_bom'), bomHandlers: (frappe.ui.form.handlers?.['Work Order']?.bom_no || []).length})`);
		assert.equal(workOrder.recommendationLoaded, true);
		await browser.screenshot(path.join(__dirname, 'ts017-demo-work-order.png'));
		await browser.evaluate(`frappe.set_route('spc-chart')`);
		await browser.until(`frappe.get_route()[0] === 'spc-chart' && window.echarts?.version === '5.6.0' && document.querySelector('.spc-summary')?.textContent.includes('请选择物料和检验参数')`, 60000);
		await browser.screenshot(path.join(__dirname, 'ts017-demo-spc-empty.png'));
		const spc = await browser.evaluate(`({version: echarts.version, summary: document.querySelector('.spc-summary').textContent, vendor: performance.getEntriesByType('resource').map(r => r.name).filter(name => name.includes('echarts-5.6.0'))})`);
		assert.equal(spc.vendor.length, 1);
		const result = {site: 'erx.localhost', saved: false, workOrder, spc};
		fs.writeFileSync(path.join(__dirname, 'ts017-demo-ui-result.json'), JSON.stringify(result, null, 1));
		console.log(JSON.stringify(result));
	} finally {await browser.close();}
}
main().catch(error => {console.error(error); process.exitCode = 1;});
