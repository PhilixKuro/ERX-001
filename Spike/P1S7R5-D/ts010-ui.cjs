const fs = require('node:fs');
const path = require('node:path');
const { open } = require('../P1S6R4-cdp.cjs');

const OUT = path.resolve(__dirname);
const BASE = 'http://test.localhost:6787';
const company = '_S6R6 测试公司';
const supplier = '_S6R6 验收供应商';
const warehouse = '_S6R6 验收原料 - S6R';
const stamp = Date.now();
const itemCode = `_FCT_TS010_UI_${stamp}`;
const batchA = `_FCT-TS010-A-${stamp}`;
const batchB = `_FCT-TS010-B-${stamp}`;

async function main() {
	const browser = await open(BASE);
	const report = { itemCode, batchA, batchB, created: {}, before: null, after: null };
	try {
		// 写之前先确认连的是测试站：8000 只服务演示站（R7 F FD-013）
		const site = await browser.evaluate('frappe.boot.sitename');
		if (site !== 'test.localhost') throw new Error(`refusing to write: connected to ${site}`);
		const created = await browser.evaluate(`(async () => {
			const insert = async (doc) => {
				return await new Promise(resolve => frappe.call({ method: 'frappe.client.insert', args: { doc },
					callback: response => resolve({ ok: true, value: response.message }),
					error: (response, responseText) => resolve({ ok: false, error: JSON.stringify({ response, responseText }) }),
				}));
			};
			const call = async (method, args) => await new Promise(resolve => frappe.call({
				method, args,
				callback: response => resolve({ ok: true, value: response.message, response }),
				error: (response, responseText) => resolve({ ok: false, error: JSON.stringify({ response, responseText }) }),
			}));
			const itemResult = await insert({
				doctype: 'Item', item_code: ${JSON.stringify(itemCode)}, item_name: ${JSON.stringify(itemCode)},
				item_group: 'All Item Groups', stock_uom: 'Kg', is_stock_item: 1, has_batch_no: 1,
				weight_uom: 'Kg', cn_unit_length_m: 0.5,
				uoms: [{ uom: 'Nos', conversion_factor: 0.004 }],
			});
			if (!itemResult.ok) return { step: 'item', error: itemResult.error };
			const item = itemResult.value;
			const aResult = await insert({ doctype: 'Batch', batch_id: ${JSON.stringify(batchA)}, item: item.name, cn_linear_density: 0.01 });
			if (!aResult.ok) return { step: 'batch_a', error: aResult.error, partial: { item: item.name } };
			const a = aResult.value;
			const bResult = await insert({ doctype: 'Batch', batch_id: ${JSON.stringify(batchB)}, item: item.name, cn_linear_density: 0.012 });
			if (!bResult.ok) return { step: 'batch_b', error: bResult.error, partial: { item: item.name, batch_a: a.name } };
			const b = bResult.value;
			const itemProbe = await call('frappe.client.get_value', { doctype: 'Item', name: item.name,
				fieldname: ['stock_uom', 'weight_uom', 'cn_unit_length_m'] });
			const batchProbe = await call('frappe.client.get_value', { doctype: 'Batch', name: a.name,
				fieldname: ['item', 'cn_linear_density'] });
			const factorProbe = await call('frappe_china.production.batch_uom.get_batch_conversion_factor', {
				item_code: item.name, batch_no: a.name, uom: 'Nos',
			});
			return { item: item.name, batch_a: a.name, batch_b: b.name, itemProbe, batchProbe, factorProbe };
		})()`);
		report.created = created.partial || created;
		if (created.error) throw new Error(`${created.step}: ${created.error}`);

		await browser.navigate(`${BASE}/desk/purchase-receipt/new-purchase-receipt-1`);
		await browser.until(`cur_frm?.doctype === 'Purchase Receipt' && cur_frm.doc?.doctype === 'Purchase Receipt' && frappe.request.ajax_count === 0`, 60000);
		await browser.evaluate(`(async () => {
			const frm = cur_frm;
			await frappe.model.set_value(frm.doctype, frm.doc.name, 'company', ${JSON.stringify(company)});
			await frappe.model.set_value(frm.doctype, frm.doc.name, 'supplier', ${JSON.stringify(supplier)});
			frm.clear_table('items');
			for (const batch of [${JSON.stringify(batchA)}, ${JSON.stringify(batchB)}]) {
				frm.add_child('items', {
					item_code: ${JSON.stringify(created.item)}, item_name: ${JSON.stringify(created.item)},
					qty: 10, uom: 'Nos', stock_uom: 'Kg', conversion_factor: 0.004,
					warehouse: ${JSON.stringify(warehouse)}, rate: 1,
				});
			}
			const grid = frm.fields_dict.items.grid;
			grid.setup_user_defined_columns = () => {
				grid.user_defined_columns = ['batch_no', 'qty', 'uom', 'conversion_factor'].map((fieldname) => {
					const field = grid.docfields.find((docfield) => docfield.fieldname === fieldname);
					field.in_list_view = 1;
					field.columns = 2;
					return field;
				});
			};
			grid.visible_columns = [];
			grid.refresh();
			return true;
		})()`);
		await browser.pause(500);
		report.handlers = await browser.evaluate(`({
			batch: frappe.ui.form.handlers?.['Purchase Receipt Item']?.batch_no?.length || 0,
			uom: frappe.ui.form.handlers?.['Purchase Receipt Item']?.uom?.length || 0,
			batch_source: (frappe.ui.form.handlers?.['Purchase Receipt Item']?.batch_no || []).map(fn => fn.toString().slice(0, 350)),
			loaded: performance.getEntriesByType('resource').map(r => r.name).filter(name => name.includes('batch_uom')),
			item_count: cur_frm.doc.items.length,
		})`);
		report.batchAPI = await browser.evaluate(`Promise.all([${JSON.stringify(batchA)}, ${JSON.stringify(batchB)}].map(batch_no => frappe.xcall('frappe_china.production.batch_uom.get_batch_conversion_factor', { item_code: ${JSON.stringify(created.item)}, batch_no, uom: 'Nos' }).catch(error => ({ error: String(error) }))))`);
			report.factorFetch = await browser.evaluate(`fetch('/api/method/frappe_china.production.batch_uom.get_batch_conversion_factor', {
			method: 'POST', credentials: 'include', headers: {
				'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
				'X-Frappe-CSRF-Token': frappe.csrf_token,
			},
			body: new URLSearchParams({item_code: ${JSON.stringify(created.item)}, batch_no: ${JSON.stringify(batchA)}, uom: 'Nos'})
		}).then(async response => ({status: response.status, text: await response.text()}))`);
		report.before = await browser.evaluate(`cur_frm.doc.items.map(row => ({ batch_no: row.batch_no, conversion_factor: row.conversion_factor, stock_qty: row.stock_qty }))`);

		await browser.evaluate(`(async () => {
			const rows = cur_frm.doc.items;
			await Promise.all([
				frappe.model.set_value(rows[0].doctype, rows[0].name, 'batch_no', ${JSON.stringify(batchA)}),
				frappe.model.set_value(rows[1].doctype, rows[1].name, 'batch_no', ${JSON.stringify(batchB)}),
			]);
			return true;
		})()`);
		try {
			await browser.until(`Math.abs(Number(cur_frm.doc.items[0].conversion_factor) - 0.005) < 1e-9 && Math.abs(Number(cur_frm.doc.items[1].conversion_factor) - 0.006) < 1e-9`, 8000);
		} catch (error) {
			report.batch_rows_after_select = await browser.evaluate(`cur_frm.doc.items.map(row => ({ batch_no: row.batch_no, conversion_factor: row.conversion_factor, stock_qty: row.stock_qty }))`);
			throw error;
		}
		report.after = await browser.evaluate(`cur_frm.doc.items.map(row => ({ batch_no: row.batch_no, conversion_factor: row.conversion_factor, stock_qty: row.stock_qty }))`);
		await browser.evaluate(`(async () => {
			const rows = cur_frm.doc.items;
			await Promise.all([
				frappe.model.set_value(rows[0].doctype, rows[0].name, 'batch_no', ${JSON.stringify(batchB)}),
				frappe.model.set_value(rows[1].doctype, rows[1].name, 'batch_no', ${JSON.stringify(batchA)}),
			]);
		})()`);
		await browser.until(`Math.abs(Number(cur_frm.doc.items[0].conversion_factor) - 0.006) < 1e-9 && Math.abs(Number(cur_frm.doc.items[1].conversion_factor) - 0.005) < 1e-9`, 30000);
		report.switched = await browser.evaluate(`cur_frm.doc.items.map(row => ({ batch_no: row.batch_no, conversion_factor: row.conversion_factor, stock_qty: row.stock_qty }))`);
		await browser.evaluate(`(async () => {
			const rows = cur_frm.doc.items;
			await Promise.all([
				frappe.model.set_value(rows[0].doctype, rows[0].name, 'batch_no', ${JSON.stringify(batchA)}),
				frappe.model.set_value(rows[1].doctype, rows[1].name, 'batch_no', ${JSON.stringify(batchB)}),
			]);
		})()`);
		await browser.until(`Math.abs(Number(cur_frm.doc.items[0].conversion_factor) - 0.005) < 1e-9 && Math.abs(Number(cur_frm.doc.items[1].conversion_factor) - 0.006) < 1e-9`, 30000);
		report.final = await browser.evaluate(`cur_frm.doc.items.map(row => ({ batch_no: row.batch_no, conversion_factor: row.conversion_factor, stock_qty: row.stock_qty }))`);
		await browser.pause(1000);
		await browser.screenshot(path.join(OUT, 'ts010-purchase-receipt-batch-factors.png'));
	} finally {
		if (report.created.batch_a) {
			for (const name of [report.created.batch_a, report.created.batch_b]) {
				try { await browser.evaluate(`frappe.xcall('frappe.client.delete', { doctype: 'Batch', name: ${JSON.stringify(name)} }).then(() => true)`); } catch (error) { report[`delete_${name}`] = String(error); }
			}
		}
		if (report.created.item) {
			try { report.deleted_item = await browser.evaluate(`frappe.xcall('frappe.client.delete', { doctype: 'Item', name: ${JSON.stringify(report.created.item)} }).then(() => true)`); } catch (error) { report.delete_item_error = String(error); }
		}
		fs.writeFileSync(path.join(OUT, 'ts010-ui-result.json'), JSON.stringify(report, null, 1), 'utf8');
		console.log(JSON.stringify(report, null, 1));
		await browser.close();
	}
}

main().catch(error => { console.error(error); process.exitCode = 1; });
