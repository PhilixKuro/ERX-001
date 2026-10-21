const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { open } = require('../P1S6R4-cdp.cjs');

(async () => {
	const c = await open();
	try {
		assert.equal(await c.evaluate('frappe.boot.sitename'), 'test.localhost');
		await c.evaluate("frappe.set_route('List', 'Replenishment Suggestion')");
		await c.until("cur_list?.doctype === 'Replenishment Suggestion'");
		await c.until("Array.isArray(cur_list.columns) && cur_list.columns.length > 0");
		const columns = (await c.evaluate(`cur_list.columns.map(column => String(column.df?.fieldname || column.type)).join(',')`)).split(',');
		assert.equal(columns[0], 'item_code', 'item code is the first list column');
		assert.ok(columns.indexOf('item_name') > 0, 'item name is a separate column');
		await c.screenshot(path.join(__dirname, 'SL007-suggestion-list.png'));

		const buttonExists = await c.evaluate(`Array.from(document.querySelectorAll('.page-actions button')).some(el => el.innerText.trim() === __('Calculate Now'))`);
		assert.ok(buttonExists, 'Calculate Now list action exists');
		await c.evaluate(`Array.from(document.querySelectorAll('.page-actions button')).find(el => el.innerText.trim() === __('Calculate Now')).click()`);
		await c.until("cur_dialog?.title === __('Calculate Replenishment')");
		await c.evaluate(`cur_dialog.set_value('calculation_date', frappe.datetime.get_today())`);
		await c.evaluate('void cur_dialog.get_primary_btn().click()');
		await c.until("cur_dialog?.$wrapper?.is(':visible') && cur_dialog.$body.text().trim().length > 0", 180000);
		const result = await c.evaluate(`({
			title: cur_dialog.$wrapper.find('.modal-title').text(),
			text: cur_dialog.$body.text(),
			tables: cur_dialog.$body.find('table').length,
		})`);
		assert.ok(result.text.length > 0, 'real calculation returned visible details');
		await c.screenshot(path.join(__dirname, 'SL007-calculation-actual.png'));
		const report = { site: 'test.localhost', columns, result, screenshots: ['SL007-suggestion-list.png', 'SL007-calculation-actual.png'] };
		fs.writeFileSync(path.join(__dirname, '../../frappe-bench/logs/s8-ts008-browser.json'), JSON.stringify(report, null, 2));
		console.log(JSON.stringify(report));
	} finally {
		await c.close();
	}
})().catch((error) => {
	console.error(error);
	process.exitCode = 1;
});
