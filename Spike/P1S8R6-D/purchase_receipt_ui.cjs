const assert = require('node:assert/strict');
const path = require('node:path');
const { open } = require('../P1S6R4-cdp.cjs');

(async () => {
	const c = await open();
	let fixture;
	try {
		assert.equal(await c.evaluate('frappe.boot.sitename'), 'test.localhost');
		fixture = JSON.parse(await c.evaluate(`(async () => {
			const headers = {'Content-Type': 'application/json', 'X-Frappe-CSRF-Token': frappe.csrf_token};
			const request = async (url, options = {}) => {
				const response = await fetch(url, {...options, headers: {...headers, ...options.headers}});
				const body = await response.json();
				if (!response.ok || body.exc) throw Error(JSON.stringify(body));
				return body.data || body.message;
			};
			const companies = await request('/api/resource/Company?fields=' + encodeURIComponent(JSON.stringify(['name'])));
			const company = companies.find(row => row.name.includes('_S6R6 测试公司'))?.name;
			if (!company) throw Error('The isolated test company was not found');
			const suppliers = await request('/api/resource/Supplier?fields=' + encodeURIComponent(JSON.stringify(['name'])));
			const supplier = suppliers.find(row => row.name.includes('_S6R6 验收供应商'))?.name;
			if (!supplier) throw Error('The isolated test supplier was not found');
			const uoms = await request('/api/resource/UOM?fields=' + encodeURIComponent(JSON.stringify(['name'])));
			const uom = uoms.find(row => row.name === 'Nos' || row.name === 'Each')?.name || uoms[0]?.name;
			const groups = await request('/api/resource/Item Group?fields=' + encodeURIComponent(JSON.stringify(['name'])));
			const item_group = groups.find(row => row.name === 'Raw Material')?.name || groups.find(row => !['All Item Groups', 'All Item Group'].includes(row.name))?.name;
			if (!uom || !item_group) throw Error('Required Item Group or UOM missing: ' + JSON.stringify({uoms:uoms.slice(0,5),groups:groups.slice(0,5)}));
			const prefix = '_TS009_' + Date.now();
			const item_code = prefix + '_Service';
			return JSON.stringify({company, supplier, item_code, item_group, uom});
		})()`));
		console.log(JSON.stringify({stage: 'prepared', ...fixture}));
		await c.evaluate(`(async () => {
			const response = await fetch('/api/resource/Item', {method:'POST',headers:{'Content-Type':'application/json','X-Frappe-CSRF-Token':frappe.csrf_token},body:JSON.stringify({
				item_code:${JSON.stringify(fixture.item_code)}, item_name:${JSON.stringify(fixture.item_code)}, item_group:${JSON.stringify(fixture.item_group)}, stock_uom:${JSON.stringify(fixture.uom)},
				is_stock_item:0,is_purchase_item:1,is_sales_item:0
			})});
			const result = await response.json(); if (!response.ok || result.exc) throw Error(JSON.stringify(result)); return true;
		})()`);
		console.log(JSON.stringify({stage: 'item-created', item_code: fixture.item_code}));
		fixture.receipt = await c.evaluate(`(async () => {
			const response = await fetch('/api/resource/Purchase Receipt',{method:'POST',headers:{'Content-Type':'application/json','X-Frappe-CSRF-Token':frappe.csrf_token},body:JSON.stringify({
				company:${JSON.stringify(fixture.company)}, supplier:${JSON.stringify(fixture.supplier)}, posting_date:frappe.datetime.get_today(),
				items:[{item_code:${JSON.stringify(fixture.item_code)},item_name:${JSON.stringify(fixture.item_code)},qty:1,received_qty:1,uom:${JSON.stringify(fixture.uom)},stock_uom:${JSON.stringify(fixture.uom)},conversion_factor:1,rate:0.01,amount:0.01}]
			})});
			const result = await response.json(); if (!response.ok || result.exc) throw Error(JSON.stringify(result)); return result.data.name;
		})()`);
		console.log(JSON.stringify({stage: 'receipt-created', receipt: fixture.receipt}));
		await c.evaluate(`frappe.set_route('Form', 'Purchase Receipt', ${JSON.stringify(fixture.receipt)})`);
		await c.until("window.cur_frm?.doctype === 'Purchase Receipt' && cur_frm.doc.docstatus === 0");
		const actions = await c.evaluate("JSON.stringify([...document.querySelectorAll('.page-actions button')].map(button => button.innerText.trim()))");
		assert(JSON.parse(actions).includes('提交'), `Submit action missing: ${actions}`);
		await c.evaluate("[...document.querySelectorAll('.page-actions button')].find(button => button.innerText.trim() === '提交')?.click(); true");
		await c.pause(300);
		if (await c.evaluate("!!document.querySelector('.modal.show')")) {
			await c.evaluate("[...document.querySelectorAll('.modal.show .btn-primary')].at(-1)?.click(); true");
		}
		console.log(await c.evaluate(`JSON.stringify({docstatus:cur_frm.doc.docstatus,buttons:[...document.querySelectorAll('.page-actions button')].map(button=>button.innerText.trim()),modals:[...document.querySelectorAll('.modal.show')].map(modal=>modal.innerText)})`));
		await c.screenshot(path.join(__dirname, 'SL008-submit-attempt.png'));
		await c.until("cur_frm.doc.docstatus === 1", 60000);
		await c.until("document.body.innerText.includes('已成功提交采购入库')", 15000);
		await c.screenshot(path.join(__dirname, 'SL008-submit-success-real.png'));
		console.log(JSON.stringify({site: 'test.localhost', ...fixture, docstatus: 1,
			message: '已成功提交采购入库', screenshot: 'SL008-submit-success-real.png'}));
	} finally {
		if (fixture) {
			await c.evaluate(`(async () => {
				const fixture = ${JSON.stringify(fixture)};
				const csrf = frappe.csrf_token;
				const request = async (url, options = {}) => {
					const response = await fetch(url, {headers: {'Content-Type':'application/json','X-Frappe-CSRF-Token':csrf}, ...options});
					const result = await response.json();
					if (!response.ok || result.exc) throw Error(JSON.stringify(result));
					return result;
				};
				const exists = await fetch('/api/resource/Purchase Receipt/' + encodeURIComponent(fixture.receipt));
				if (exists.ok) {
					const doc = (await exists.json()).data;
					if (doc.docstatus === 1) await request('/api/method/frappe.client.cancel', {method:'POST', body:JSON.stringify({doctype:'Purchase Receipt', name:fixture.receipt})});
					await request('/api/method/frappe.client.delete', {method:'POST', body:JSON.stringify({doctype:'Purchase Receipt', name:fixture.receipt})});
				}
				const item = await fetch('/api/resource/Item/' + encodeURIComponent(fixture.item_code));
				if (item.ok) await request('/api/method/frappe.client.delete', {method:'POST', body:JSON.stringify({doctype:'Item', name:fixture.item_code})});
			})()`);
		}
		await c.close();
	}
})().catch(error => {
	console.error(error);
	process.exitCode = 1;
});
