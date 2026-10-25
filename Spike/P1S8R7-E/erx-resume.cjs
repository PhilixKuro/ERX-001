// IT-004: resume the erx.localhost full rehearsal from a given act via the designed
// rehearsal.resume(act) path, polling tolerantly so a transient page error cannot kill it.
// Usage: node erx-resume.cjs <act>
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { open } = require('../P1S6R4-cdp.cjs');

const act = Number(process.argv[2]);
assert.ok(act >= 1 && act <= 9);
const logs = path.join(__dirname, '../../frappe-bench/logs');
const saved = path.join(logs, 's8-ts026-erx-full-rehearsal.json');
const output = path.join(logs, 's8-r7e-erx-rehearsal.json');
const log = value => console.log(JSON.stringify({ at: new Date().toISOString(), ...value }));

(async () => {
	const previous = JSON.parse(fs.readFileSync(saved, 'utf8'));
	const state = { ...previous.state, status: 'failed', error: 'R7：驱动脚本轮询异常退出，按设计从本幕续跑' };
	const c = await open('http://erx.localhost:8000');
	const safe = async expression => {
		for (let i = 0; i < 60; i++) {
			try { return await c.evaluate(expression); }
			catch (error) { if (i === 59) throw error; await c.pause(1000); }
		}
	};
	try {
		await c.until("typeof window.frappe?.xcall === 'function' && !!window.frappe_debug?.demo?.business_functions_loaded", 60000);
		assert.equal(await c.evaluate('frappe.boot.sitename'), 'erx.localhost');
		assert.equal(await c.evaluate('frappe.session.user'), 'Administrator');
		await c.evaluate(`sessionStorage.setItem('frappe_debug_rehearsal', ${JSON.stringify(JSON.stringify(state))}); sessionStorage.setItem('frappe_debug_mode', 'rehearsal'); true`);
		await c.evaluate(`(async () => { const demo = frappe_debug.demo; if (!demo.config) { demo.config = await frappe.xcall('frappe_debug.demo.config.get_demo_config'); demo.validate(demo.config); } await demo.rehearsal.resume(${act}); })().catch(e => window.__r7ResumeError = e?.message || String(e)); true`);
		log({ event: 'resume', act });
		const deadline = Date.now() + 6 * 60 * 60 * 1000;
		let last = '';
		let local;
		while (Date.now() < deadline) {
			local = await safe(`(async () => {
				if (typeof window.frappe?.xcall !== 'function') return null;
				return {
					state: JSON.parse(sessionStorage.getItem('frappe_debug_rehearsal') || 'null'),
					db: (await frappe.xcall('frappe_debug.demo.switch.switch_status')).db,
					resume_error: window.__r7ResumeError || null,
					transit_error: document.getElementById('error')?.textContent || null,
				};
			})().catch(() => null)`);
			if (!local) { await c.pause(2000); continue; }
			fs.writeFileSync(output, JSON.stringify({ ...local, observed_at: new Date().toISOString() }, null, 2));
			const s = local.state || {};
			const signature = `${s.phase}:${s.act}:${s.status}:${s.error || ''}`;
			if (signature !== last) { log({ phase: s.phase, act: s.act, status: s.status, db: local.db, error: s.error || local.resume_error || local.transit_error || null }); last = signature; }
			if (local.resume_error || local.transit_error) throw Error(local.resume_error || local.transit_error);
			if (s.status === 'failed' && s.error !== state.error) throw Error(s.error);
			if (s.status === 'done') break;
			await c.pause(5000);
		}
		assert.equal(local?.state?.status, 'done', '续跑未在限定时间内完成');
		let final;
		for (let i = 0; i < 120; i++) {
			final = await safe(`(async () => ({
				db: (await frappe.xcall('frappe_debug.demo.switch.switch_status')).db,
				snapshots: await frappe.xcall('frappe_debug.demo.snapshot.snapshot_status'),
				progress: await frappe.xcall('frappe_debug.demo.progress.get_progress'),
			}))().catch(() => null)`);
			if (final?.db?.endsWith('_a1_m') && final.progress.act === 1 && final.progress.step === 0) break;
			await c.pause(1000);
		}
		await c.screenshot(path.join(logs, 's8-r7e-erx-rehearsal.png'));
		fs.writeFileSync(output, JSON.stringify({ ...local, final, observed_at: new Date().toISOString() }, null, 2));
		const copies = Object.values(final.snapshots.acts || {}).flatMap(entry => Object.values(entry));
		assert.equal(final.db, `${final.snapshots.base_db}_a1_m`);
		assert.equal(Object.keys(final.snapshots.acts).length, 9);
		assert.equal(copies.length, 27);
		assert.deepEqual(final.progress.refs, {});
		log({ event: 'PASS', total_seconds: local.state.total_seconds, states: copies.reduce((acc, copy) => ({ ...acc, [copy.state]: (acc[copy.state] || 0) + 1 }), {}) });
	} finally { await c.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
