const assert = require('node:assert/strict');
const {open} = require('../P1S6R4-cdp.cjs');

(async () => {
	const c = await open('http://s8ts023preview.localhost:6787');
	try {
		assert.equal(await c.evaluate('frappe.boot.sitename'), 's8ts023preview.localhost');
		assert.equal(await c.evaluate('frappe.session.user'), 'Administrator');
		const before = await c.evaluate(`(async () => ({
			status: await frappe.xcall('frappe_debug.demo.switch.switch_status'),
			snapshots: await frappe.xcall('frappe_debug.demo.snapshot.snapshot_status'),
			progress: await frappe.xcall('frappe_debug.demo.progress.get_progress'),
		}))()`);
		assert.equal(before.status.db, before.snapshots.base_db + '_a1_m');
		assert.equal(before.snapshots.work_state, 'ready');
		await c.evaluate(`frappe.xcall('frappe_debug.demo.switch.switch_to_db', {db_name: ${JSON.stringify(before.snapshots.work_db)}})`);
		await c.navigate('http://s8ts023preview.localhost:6787/desk');
		assert.equal(await c.evaluate('frappe.boot.sitename'), 's8ts023preview.localhost');
		const after = await c.evaluate(`(async () => ({
			status: await frappe.xcall('frappe_debug.demo.switch.switch_status'),
			snapshots: await frappe.xcall('frappe_debug.demo.snapshot.snapshot_status'),
		}))()`);
		assert.equal(after.status.db, before.snapshots.work_db);
		console.log(JSON.stringify({before: before.status, after: after.status, work_state: after.snapshots.work_state}));
	} finally {
		await c.close();
	}
})().catch(error => {
	console.error(error);
	process.exitCode = 1;
});
