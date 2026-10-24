const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { open } = require('../P1S6R4-cdp.cjs');

const logs = path.join(__dirname, '../../frappe-bench/logs');
const output = path.join(logs, 's8-ts026-erx-full-rehearsal.json');

(async () => {
	const c = await open('http://erx.localhost:8000');
	try {
		await c.until("typeof window.frappe?.xcall === 'function'", 60000);
		assert.equal(await c.evaluate('frappe.boot.sitename'), 'erx.localhost');
		assert.equal(await c.evaluate('frappe.session.user'), 'Administrator');
		await c.until('!!window.frappe_debug?.demo?.business_functions_loaded', 60000);
		const initial = await c.evaluate(`(async () => ({
			status: await frappe.xcall('frappe_debug.demo.switch.switch_status'),
			snapshots: await frappe.xcall('frappe_debug.demo.snapshot.snapshot_status'),
			progress: await frappe.xcall('frappe_debug.demo.progress.get_progress'),
		}))()`);
		await c.evaluate("frappe.set_route('demo-rehearsal')");
		await c.until("!!window.frappe_debug?.demo?.rehearsal && document.body.innerText.includes('开始整场预跑')");
		const previous = fs.existsSync(output) ? JSON.parse(fs.readFileSync(output, 'utf8')) : null;
		const completed = previous?.state?.status === 'done' && Object.keys(initial.snapshots.acts || {}).length === 9;
		const resume = previous?.state?.status === 'running'
			&& previous.state.phase === 'acts' && previous.state.act === 1;
		if (completed) {
			assert.equal(initial.status.db, previous.db);
			assert.equal(initial.snapshots.base_db, previous.snapshots.base_db);
			assert.equal(initial.progress.act, 1);
			assert.equal(initial.progress.step, 0);
			assert.deepEqual(initial.progress.refs, {});
			console.log('VERIFY completed erx rehearsal', JSON.stringify({db:initial.status.db,acts:Object.keys(initial.snapshots.acts || {}).length}));
		} else if (resume) {
			assert.equal(initial.status.db, previous.db);
			assert.equal(initial.snapshots.base_db, previous.snapshots.base_db);
			assert.equal(initial.progress.act, 1);
			assert.equal(initial.progress.step, 0);
			assert.deepEqual(initial.progress.refs, {});
			await c.until(`(async () => {
				const s = await frappe.xcall('frappe_debug.demo.snapshot.snapshot_status');
				const copies = s.acts?.['1'];
				return !!copies && Object.values(copies).every(copy => copy.state === 'ready');
			})()`, 120000);
			const savedState = JSON.stringify(JSON.stringify(previous.state));
			await c.evaluate(`sessionStorage.setItem('frappe_debug_rehearsal', ${savedState}); sessionStorage.setItem('frappe_debug_mode', 'rehearsal'); void frappe_debug.demo.rehearsal.continue(); true`);
			console.log('RESUME erx rehearsal', JSON.stringify({phase:previous.state.phase, act:previous.state.act, step:initial.progress.step}));
		} else {
			assert.ok(!initial.snapshots.base_db || initial.status.db === initial.snapshots.base_db);
			assert.deepEqual(initial.snapshots.acts || {}, {});
			assert.equal(initial.snapshots.work_db || null, null);
			const counts = await c.evaluate(`(async () => ({
				companies: await frappe.db.count('Company'),
				translations: await frappe.db.count('Translation'),
				gl: await frappe.db.count('GL Entry'),
				sle: await frappe.db.count('Stock Ledger Entry'),
			}))()`);
			assert.deepEqual(counts, { companies: 1, translations: 0, gl: 0, sle: 0 });
			await c.evaluate(`document.querySelectorAll('button').forEach(button => {
				if (button.textContent.trim() === '开始整场预跑') button.click();
			})`);
		}
		const deadline = Date.now() + 8 * 60 * 60 * 1000;
		let last = '';
		while (!completed && Date.now() < deadline) {
			await c.until("typeof window.frappe?.xcall === 'function'", 120000);
			let state;
			try { state = await c.evaluate(`(async () => ({
				state: JSON.parse(sessionStorage.getItem('frappe_debug_rehearsal') || 'null'),
				db: (await frappe.xcall('frappe_debug.demo.switch.switch_status')).db,
				snapshots: await frappe.xcall('frappe_debug.demo.snapshot.snapshot_status'),
				progress: await frappe.xcall('frappe_debug.demo.progress.get_progress'),
			}))()`); }
			catch (error) {
				if (/frappe\.xcall is not a function|Cannot read properties of undefined/.test(error.message)) continue;
				throw error;
			}
			fs.writeFileSync(output, JSON.stringify({ initial, ...state, observed_at: new Date().toISOString() }, null, 2));
			const signature = `${state.state?.phase}:${state.state?.act}:${state.state?.status}:${state.state?.error || ''}`;
			if (signature !== last) {
				console.log(JSON.stringify({ phase: state.state?.phase, act: state.state?.act, status: state.state?.status, db: state.db, work_state: state.snapshots.work_state, acts: Object.keys(state.snapshots.acts || {}).length, error: state.state?.error || null }));
				last = signature;
			}
			if (state.state?.status === 'failed' || state.state?.status === 'done') break;
			await c.pause(5000);
		}
		const final = completed ? previous : JSON.parse(fs.readFileSync(output, 'utf8'));
		await c.screenshot(path.join(logs, 's8-ts026-erx-full-rehearsal.png'));
		assert.equal(final.state?.status, 'done', final.state?.error || '预跑未在限定时间内完成');
		assert.equal(final.db, `${final.snapshots.base_db}_a1_m`);
		assert.equal(final.progress.active, true);
		assert.equal(final.progress.act, 1);
		assert.equal(final.progress.step, 0);
		assert.deepEqual(final.progress.refs, {});
		assert.equal(Object.keys(final.snapshots.acts || {}).length, 9);
		const copies = Object.values(final.snapshots.acts || {}).flatMap(act => Object.values(act));
		const used = copies.filter(copy => copy.state === 'used');
		assert.equal(copies.length, 27);
		assert.equal(used.length, 1);
		assert.equal(used[0].db, final.db);
		assert(copies.every(copy => ['ready', 'used'].includes(copy.state)));
		console.log('PASS erx full rehearsal', JSON.stringify({ total_seconds: final.state.total_seconds, timings: final.state.timings.length, registry: final.snapshots }));
	} finally {
		await c.close();
	}
})().catch(error => {
	console.error(error);
	process.exitCode = 1;
});
