const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {open} = require('../P1S6R4-cdp.cjs');

async function main() {
	const data = JSON.parse(fs.readFileSync(path.join(__dirname, 'ts016-fixture.json'), 'utf8'));
	const browser = await open('http://test.localhost:6787');
	try {
		assert.equal(await browser.evaluate('frappe.boot.sitename'), 'test.localhost');
		await browser.evaluate(`frappe.set_route('query-report', 'SPC Control Chart', ${JSON.stringify({item_code: data.item, specification: data.parameter})})`);
		await browser.until(`frappe.query_report?.report_name === 'SPC Control Chart' && frappe.query_report.data?.length === 28`, 60000);
		await browser.screenshot(path.join(__dirname, 'ts015-spc-report.png'));
		await browser.evaluate(`Array.from(document.querySelectorAll('.page-head button')).find(b => b.textContent.includes('打开控制图')).click()`);
		await browser.until(`frappe.get_route()[0] === 'spc-chart' && window.echarts && Array.from(document.querySelectorAll('div')).some(e => e.getAttribute('_echarts_instance_'))`, 60000);
		const chartState = await browser.evaluate(`(() => {
			const element = document.querySelector('[_echarts_instance_]');
			const instance = echarts.getInstanceByDom(element);
			const option = instance.getOption();
			const points = option.series[0].data;
			return {version: echarts.version, points: points.length, colors: [...new Set(points.map(p => p.itemStyle.color))],
				signals: points.filter(p => p.rules.length).map((p, index) => ({name: p.subgroup.inspection, rules: p.rules})),
				filters: Object.fromEntries(Object.entries(frappe.pages['spc-chart'].spc_fields || {}).map(([key, field]) => [key, field.get_value()]))};
		})()`);
		assert.equal(chartState.version, '5.6.0');
		assert.equal(chartState.points, 28);
		assert.equal(chartState.colors.length, 2);
		assert.ok(chartState.signals.some(p => p.rules.includes(1)));
		assert.ok(chartState.signals.some(p => p.rules.includes(2)));
		await browser.screenshot(path.join(__dirname, 'ts016-spc-overall.png'));
		await browser.evaluate(`(() => {
			const instance = echarts.getInstanceByDom(document.querySelector('[_echarts_instance_]'));
			const points = instance.getOption().series[0].data;
			const index = points.findIndex(p => p.rules.includes(1));
			instance.dispatchAction({type: 'showTip', seriesIndex: 0, dataIndex: index});
		})()`);
		await browser.pause(400);
		await browser.screenshot(path.join(__dirname, 'ts016-spc-signal-tooltip.png'));
		fs.writeFileSync(path.join(__dirname, 'ts016-ui-result.json'), JSON.stringify(chartState, null, 1));
		console.log(JSON.stringify(chartState));
	} finally {await browser.close();}
}
main().catch(error => {console.error(error); process.exitCode = 1;});
