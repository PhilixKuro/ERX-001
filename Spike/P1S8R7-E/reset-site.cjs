// IT-004: return a demo site to its clean base and drop its registered snapshots.
// Usage: node reset-site.cjs <site> <port>
const assert = require('node:assert/strict');
const { open } = require('../P1S6R4-cdp.cjs');

const [site, port] = process.argv.slice(2);
assert.ok(['erx.localhost', 's8ts023preview.localhost'].includes(site), 'site not allowed');
const pause = ms => new Promise(r => setTimeout(r, ms));

(async () => {
	const c = await open(`http://${site}:${port}`);
	const api = (method, args = {}) => c.evaluate(`frappe.xcall(${JSON.stringify(method)}, ${JSON.stringify(args)})`);
	try {
		assert.equal(await c.evaluate('frappe.boot.sitename'), site);
		assert.equal(await c.evaluate('frappe.session.user'), 'Administrator');
		let registry = await api('frappe_debug.demo.snapshot.snapshot_status');
		const base = registry.base_db;
		assert.ok(base, 'no base_db registered');
		let status = await api('frappe_debug.demo.switch.switch_status');
		console.log(JSON.stringify({ event: 'before', db: status.db, base, acts: Object.keys(registry.acts || {}).length, work_state: registry.work_state }));
		if (status.db !== base) {
			await api('frappe_debug.demo.switch.switch_to_db', { db_name: base });
			await c.navigate(`http://${site}:${port}/desk`);
			await c.until('!!window.frappe?.xcall', 60000);
			status = await api('frappe_debug.demo.switch.switch_status');
			assert.equal(status.db, base);
			assert.equal(status.user, 'Administrator');
		}
		const deadline = Date.now() + 15 * 60 * 1000;
		for (;;) {
			registry = await api('frappe_debug.demo.snapshot.snapshot_status');
			const copies = Object.values(registry.acts || {}).flatMap(act => Object.values(act));
			const busy = registry.work_state === 'cloning' || copies.some(copy => copy.state === 'cloning');
			if (!busy) break;
			assert.ok(Date.now() < deadline, 'clones did not settle');
			await pause(3000);
		}
		const counts = {};
		for (const doctype of ['Company', 'Translation', 'GL Entry', 'Stock Ledger Entry', 'Sales Order', 'Work Order', 'Scenario Event']) {
			counts[doctype] = await api('frappe.client.get_count', { doctype });
		}
		assert.deepEqual(counts, { Company: 1, Translation: 0, 'GL Entry': 0, 'Stock Ledger Entry': 0, 'Sales Order': 0, 'Work Order': 0, 'Scenario Event': 0 });
		// Dropping ~28 databases outlasts CDP's 60 s call timeout; fire it and poll the registry.
		await c.evaluate("frappe.xcall('frappe_debug.demo.snapshot.drop_snapshots').then(r => window.__r7Dropped = r, e => window.__r7DropError = e?.message || String(e)); true");
		let empty;
		for (let i = 0; i < 300; i++) {
			const error = await c.evaluate('window.__r7DropError || null');
			if (error) throw Error(error);
			empty = await api('frappe_debug.demo.snapshot.snapshot_status');
			if (!empty.base_db && !Object.keys(empty.acts || {}).length && await c.evaluate('!!window.__r7Dropped')) break;
			await pause(3000);
		}
		assert.deepEqual(empty, { base_db: null, acts: {} });
		const dropped = await c.evaluate('window.__r7Dropped');
		console.log('PASS reset', JSON.stringify({ site, base, dropped, counts }));
	} finally { await c.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
