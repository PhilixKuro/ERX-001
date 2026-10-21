const { open } = require('../P1S6R4-cdp.cjs');

(async () => {
	const c = await open();
	try {
		const site = await c.evaluate('frappe.boot.sitename');
		if (site !== 'test.localhost') throw Error(`Refusing cleanup on ${site}`);
		const result = await c.evaluate(`(async () => {
			const csrf = frappe.csrf_token;
			const req = async (url, options = {}) => {
				const response = await fetch(url, {headers:{'Content-Type':'application/json','X-Frappe-CSRF-Token':csrf}, ...options});
				const body = await response.json();
				if (!response.ok || body.exc) throw Error(JSON.stringify(body));
				return body.data || body.message;
			};
			const itemQuery = new URLSearchParams({filters:JSON.stringify([['item_code','like','_TS009_%']]),fields:JSON.stringify(['name']),limit:'100'});
			const items = await req('/api/resource/Item?'+itemQuery);
			const itemNames = new Set(items.map(row => row.name));
			const receiptQuery = new URLSearchParams({filters:JSON.stringify([['supplier','like','_S6R6 验收供应商']]),fields:JSON.stringify(['name','docstatus']),limit:'100'});
			const receipts = await req('/api/resource/Purchase Receipt?'+receiptQuery);
			const removed = [];
			for (const row of receipts) {
				const doc = await req('/api/resource/Purchase Receipt/'+encodeURIComponent(row.name));
				if (!doc.items.some(detail => itemNames.has(detail.item_code))) continue;
				if (doc.docstatus === 1) await req('/api/method/frappe.client.cancel',{method:'POST',body:JSON.stringify({doctype:'Purchase Receipt',name:doc.name})});
				await req('/api/method/frappe.client.delete',{method:'POST',body:JSON.stringify({doctype:'Purchase Receipt',name:doc.name})});
				removed.push(doc.name);
			}
			for (const item of items) await req('/api/method/frappe.client.delete',{method:'POST',body:JSON.stringify({doctype:'Item',name:item.name})});
			return JSON.stringify({items:items.map(row=>row.name),receipts:removed});
		})()`);
		console.log(result);
	} finally {
		await c.close();
	}
})().catch(error => { console.error(error); process.exitCode = 1; });
