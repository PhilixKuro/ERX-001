// IT-004: full rehearsal on erx.localhost, started from the rehearsal page or resumed from an act.
// Polls tolerantly: a navigation mid-evaluate returns null instead of killing the run (R7 lesson).
// Usage: node erx-rehearsal.cjs start | node erx-rehearsal.cjs resume <act>
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { open } = require('../P1S6R4-cdp.cjs');

const mode = process.argv[2];
const resumeAct = Number(process.argv[3] || 0);
assert.ok(mode === 'start' || (mode === 'resume' && resumeAct >= 1 && resumeAct <= 9));
const logs = path.join(__dirname, '../../frappe-bench/logs');
const output = path.join(logs, 's8-r7e-erx-rehearsal.json');
const log = value => console.log(JSON.stringify({ at: new Date().toISOString(), ...value }));

(async () => {
	const c = await open('http://erx.localhost:8000');
	const safe = async expression => {
		for (let i = 0; i < 60; i++) {
			try { return await c.evaluate(expression); }
			catch (error) { if (i === 59) throw error; await c.pause(1000); }
		}
	};
	const read = () => safe(`(async () => {
		if (typeof window.frappe?.xcall !== 'function') return null;
		return {
			state: JSON.parse(sessionStorage.getItem('frappe_debug_rehearsal') || 'null'),
			db: (await frappe.xcall('frappe_debug.demo.switch.switch_status')).db,
			start_error: window.__r7StartError || null,
			transit_error: document.getElementById('error')?.textContent || null,
		};
	})().catch(() => null)`);
	try {
		await c.until("typeof window.frappe?.xcall === 'function' && !!window.frappe_debug?.demo?.business_functions_loaded", 60000);
		assert.equal(await c.evaluate('frappe.boot.sitename'), 'erx.localhost');
		assert.equal(await c.evaluate('frappe.session.user'), 'Administrator');
		let resumedFrom = null;
		if (mode === 'start') {
			const initial = await c.evaluate(`(async () => ({
				status: await frappe.xcall('frappe_debug.demo.switch.switch_status'),
				snapshots: await frappe.xcall('frappe_debug.demo.snapshot.snapshot_status'),
				counts: {
					gl: await frappe.db.count('GL Entry'), sle: await frappe.db.count('Stock Ledger Entry'),
					translations: await frappe.db.count('Translation'), companies: await frappe.db.count('Company'),
				},
			}))()`);
			assert.deepEqual(initial.snapshots, { base_db: null, acts: {} });
			assert.deepEqual(initial.counts, { gl: 0, sle: 0, translations: 0, companies: 1 });
			log({ event: 'baseline', db: initial.status.db });
			await c.evaluate("frappe.set_route('demo-rehearsal')");
			await c.until("Array.from(document.querySelectorAll('button')).some(b => b.textContent.trim() === '开始整场预跑')", 60000);
			await c.evaluate("Array.from(document.querySelectorAll('button')).find(b => b.textContent.trim() === '开始整场预跑').click(); true");
		} else {
			const saved = JSON.parse(fs.readFileSync(output, 'utf8'));
			resumedFrom = 'R7：驱动脚本中断，按设计从本幕续跑';
			const state = { ...saved.state, status: 'failed', error: resumedFrom };
			await c.evaluate(`sessionStorage.setItem('frappe_debug_rehearsal', ${JSON.stringify(JSON.stringify(state))}); sessionStorage.setItem('frappe_debug_mode', 'rehearsal'); true`);
			await c.evaluate(`(async () => { const demo = frappe_debug.demo; if (!demo.config) { demo.config = await frappe.xcall('frappe_debug.demo.config.get_demo_config'); demo.validate(demo.config); } await demo.rehearsal.resume(${resumeAct}); })().catch(e => window.__r7StartError = e?.message || String(e)); true`);
		}
		log({ event: mode, act: resumeAct || 1 });
		const deadline = Date.now() + 6 * 60 * 60 * 1000;
		let last = '';
		let local;
		while (Date.now() < deadline) {
			const sample = await read();
			if (!sample) { await c.pause(2000); continue; }
			local = sample;
			if (local.state) fs.writeFileSync(output, JSON.stringify({ ...local, observed_at: new Date().toISOString() }, null, 2));
			const s = local.state || {};
			const signature = `${s.phase}:${s.act}:${s.status}:${s.error || ''}`;
			if (signature !== last) { log({ phase: s.phase, act: s.act, status: s.status, db: local.db, error: s.error || local.start_error || local.transit_error || null }); last = signature; }
			if (local.start_error || local.transit_error) throw Error(local.start_error || local.transit_error);
			if (s.status === 'failed' && s.error !== resumedFrom) throw Error(s.error);
			if (s.status === 'done') break;
			await c.pause(5000);
		}
		assert.equal(local?.state?.status, 'done', '预跑未在限定时间内完成');
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
		const states = copies.reduce((acc, copy) => ({ ...acc, [copy.state]: (acc[copy.state] || 0) + 1 }), {});
		log({ event: 'PASS', total_seconds: local.state.total_seconds, timings: local.state.timings, states });
	} finally { await c.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
