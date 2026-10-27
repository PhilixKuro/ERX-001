// S8 R8 SB FD-013: two full live shows on erx.localhost in a real browser (ruling A flow).
// Show 1: rehearsal page "回到演示前" -> readiness 18/18 -> "开始演示" -> → through all nine acts.
// Show 2: same start, and after act 7 opens, Alt+5 jumps back, then → through act 5 and fast-forward again.
// A node-side sampler (same session cookie) times a cheap desk API call every 3 s and records
// whether snapshot refills are running, to answer IT-003 item 6 (does refill slow the desk?).
// Usage: node fd013_two_shows.cjs
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { open } = require('../P1S6R4-cdp.cjs');

const BASE = 'http://erx.localhost:8000';
// --one-show --no-focus-release: one show pressing → as a presenter would, without moving focus first
const ONE_SHOW = process.argv.includes('--one-show');
const NO_FOCUS_RELEASE = process.argv.includes('--no-focus-release');
const logs = path.join(__dirname, '../../frappe-bench/logs');
const output = path.join(logs, NO_FOCUS_RELEASE ? 's8-r8sb-fd013-focus.json' : 's8-r8sb-fd013.json');
const log = value => console.log(JSON.stringify({ at: new Date().toISOString(), ...value }));
const pause = ms => new Promise(r => setTimeout(r, ms));
const record = { shows: [], switches: [], samples: [], errors: [], focus_releases: [] };
const save = () => fs.writeFileSync(output, JSON.stringify(record, null, 2));

(async () => {
	const c = await open(BASE);
	let sampling = true;
	let cookie = null;
	let csrf = null;
	const safe = async (expression, fallback = null) => {
		try { return await c.evaluate(expression); } catch { return fallback; }
	};
	// POST for every call: some demo endpoints accept POST only (switch_status); the page CSRF token goes along
	const http = async (method, args = {}) => {
		const started = Date.now();
		const response = await fetch(`http://127.0.0.1:8000/api/method/${method}`, {
			method: 'POST',
			headers: { Host: 'erx.localhost', Cookie: cookie, 'Content-Type': 'application/json', 'X-Frappe-CSRF-Token': csrf || '' },
			body: JSON.stringify(args),
		});
		const body = await response.json().catch(() => ({}));
		if (!response.ok || body.exc) throw Error(`${method}: HTTP ${response.status} ${body.exc_type || ''}`);
		return { ms: Date.now() - started, status: response.status, message: body.message };
	};
	const refreshCookie = async () => {
		const { cookies } = await c.send('Network.getCookies', { urls: [BASE] });
		const sid = cookies.find(item => item.name === 'sid');
		if (sid) cookie = `sid=${sid.value}`;
		const token = await safe('window.frappe?.csrf_token || null');
		if (token) csrf = token;
	};
	const sampler = (async () => {
		while (sampling) {
			try {
				if (cookie) {
					const probe = await http('frappe.client.get_count', { doctype: 'ToDo' });
					const status = await http('frappe_debug.demo.snapshot.snapshot_status');
					const copies = Object.values(status.message?.acts || {}).flatMap(entry => Object.values(entry));
					record.samples.push({ at: Date.now(), ms: probe.ms, status: probe.status, cloning: copies.filter(x => x.state === 'cloning').length });
				}
			} catch (error) { record.samples.push({ at: Date.now(), error: String(error.message || error) }); }
			await pause(3000);
		}
	})();
	const progress = async () => (await http('frappe_debug.demo.progress.get_progress')).message;
	const signature = () => safe(`(() => {
		const say = document.querySelector('#frappe-debug-presenter .frappe-debug-say')?.textContent || '';
		return location.pathname + location.search + '|' + say;
	})()`, 'navigating');
	const pageError = () => safe(`(() => {
		const panel = document.getElementById('frappe-debug-presenter');
		if (panel?.classList.contains('frappe-debug-error')) return panel.textContent;
		const transit = document.getElementById('error')?.textContent;
		if (transit) return '中转页：' + transit;
		const red = [...document.querySelectorAll('aside')].find(a => a.style?.background === 'rgb(170, 34, 34)' || a.style?.background === '#a22');
		return red ? red.textContent : null;
	})()`);
	const settled = () => safe(`(() => {
		if (document.readyState !== 'complete' || location.pathname.includes('/assets/frappe_debug/demo/transit.html')) return false;
		if (location.pathname.startsWith('/crm')) return !!document.getElementById('frappe-debug-presenter');
		const d = window.frappe_debug?.demo;
		return !!(window.frappe?.request && d?.config && !d.busy && !d.navigation_pending && frappe.request.ajax_count === 0);
	})()`, false);
	const waitSettled = async (ms = 360000) => {
		const end = Date.now() + ms;
		for (;;) {
			const error = await pageError();
			if (error) throw Error(error);
			if (await settled()) return;
			if (Date.now() > end) throw Error('页面未在限定时间内就绪');
			await pause(250);
		}
	};
	// Frappe focuses the first input of a new form (form.js focus_on_first_input) and the runner ignores
	// keys while an input has focus. A presenter clicks a blank spot first; do the same and count it.
	const releaseFocus = async () => {
		if (NO_FOCUS_RELEASE) {
			const field = await safe(`document.activeElement?.matches?.("input,select,textarea") ? (document.activeElement.closest('.frappe-control')?.dataset?.fieldname || document.activeElement.tagName) : null`);
			if (field) record.focus_releases.push({ at: Date.now(), field, url: await safe('location.pathname'), released: false });
			return;
		}
		const focused = await safe(`(() => {
			const el = document.activeElement;
			if (!el?.matches?.("input,select,textarea,[contenteditable=true],[contenteditable='']")) return null;
			const label = el.closest('.frappe-control')?.dataset?.fieldname || el.name || el.tagName;
			el.blur();
			return label;
		})()`);
		if (focused) record.focus_releases.push({ at: Date.now(), field: focused, url: await safe('location.pathname') });
	};
	const key = async (keyName, code, vk, modifiers = 0) => {
		await releaseFocus();
		try {
			await c.send('Input.dispatchKeyEvent', { type: 'keyDown', key: keyName, code, windowsVirtualKeyCode: vk, modifiers });
			await c.send('Input.dispatchKeyEvent', { type: 'keyUp', key: keyName, code, windowsVirtualKeyCode: vk, modifiers });
		} catch (error) { if (!/context|navigat|Target closed/i.test(error.message)) throw error; }
	};
	const position = async () => {
		try { const p = await progress(); return `${p.act}:${p.step}`; } catch { return 'unknown'; }
	};
	const press = async (keyName, code, vk, modifiers = 0, ms = 360000) => {
		const before = await signature();
		const beforePosition = await position();
		const started = Date.now();
		await key(keyName, code, vk, modifiers);
		const end = started + ms;
		for (;;) {
			const error = await pageError();
			if (error) throw Error(error);
			const now = await signature();
			// a step may keep the same route and narration; the saved position still moves
			const moved = (now !== before && now !== 'navigating') || (await position()) !== beforePosition;
			if (moved && await settled()) break;
			if (Date.now() > end) throw Error(`按键 ${keyName} 后页面没有变化`);
			await pause(250);
		}
		await pause(400);
		await refreshCookie();
		return (Date.now() - started) / 1000;
	};
	const right = () => press('ArrowRight', 'ArrowRight', 39);
	const rehearsalPage = async () => {
		await c.navigate(`${BASE}/desk/demo-rehearsal`);
		await c.until("Array.from(document.querySelectorAll('button')).some(b => b.textContent.trim() === '开始演示')", 90000);
	};
	const clickButton = label => c.evaluate(`Array.from(document.querySelectorAll('button')).find(b => b.textContent.trim() === ${JSON.stringify(label)}).click(); true`);
	const readiness = async () => {
		// a transient 500 right after returning to base is recorded and retried (S8 R8 SB observation)
		let status;
		for (let attempt = 0; ; attempt++) {
			try { status = (await http('frappe_debug.demo.snapshot.snapshot_status')).message; break; }
			catch (error) { record.errors.push({ transient: true, message: error.message, at: Date.now() }); if (attempt >= 5) throw error; await pause(2000); }
		}
		const copies = Object.values(status.acts || {}).flatMap(entry => [entry.m, entry.b]);
		return { ready: copies.filter(x => x.state === 'ready').length, total: copies.length, failed: copies.filter(x => x.state === 'failed').length };
	};
	const returnToBase = async () => {
		await rehearsalPage();
		const started = Date.now();
		try { await clickButton('回到演示前'); } catch (error) { if (!/context|navigat/i.test(error.message)) throw error; }
		// The click only starts the transit page; poll until the switch has really landed on the base.
		const registry = (await http('frappe_debug.demo.snapshot.snapshot_status')).message;
		let db = null;
		for (;;) {
			const error = await pageError();
			if (error) throw Error(error);
			await refreshCookie();
			try { db = (await http('frappe_debug.demo.switch.switch_status')).message; } catch { db = null; }
			const settledPage = await safe("!location.pathname.includes('/assets/') && !!window.frappe?.xcall", false);
			if (db?.db === registry.base_db && settledPage) break;
			assert.ok(Date.now() - started < 180000, `回到演示前 180 秒未完成（当前 ${db?.db}）`);
			await pause(1000);
		}
		const switchSeconds = (Date.now() - started) / 1000;
		let state;
		for (;;) {
			state = await readiness();
			assert.equal(state.failed, 0, '补库失败');
			if (state.ready === state.total) break;
			assert.ok(Date.now() - started < 30 * 60 * 1000, '补库 30 分钟未就绪');
			await pause(5000);
		}
		const seconds = (Date.now() - started) / 1000;
		log({ event: 'base_ready', switch_seconds: switchSeconds, seconds, ...state });
		return { switch_seconds: switchSeconds, seconds, ...state };
	};
	const config = async () => (await http('frappe_debug.demo.config.get_demo_config')).message;
	const playShow = async (index, { jumpBackAt = null } = {}) => {
		const show = { index, started: new Date().toISOString(), steps: 0, switches: [] };
		const ready = await returnToBase();
		show.base_ready = ready;
		await rehearsalPage();
		const startClicked = Date.now();
		try { await clickButton('开始演示'); } catch (error) { if (!/context|navigat/i.test(error.message)) throw error; }
		await c.until("!location.pathname.includes('/assets/') && !!window.frappe_debug?.demo?.config && !!document.getElementById('frappe-debug-presenter')", 180000);
		await waitSettled();
		await refreshCookie();
		show.start_seconds = (Date.now() - startClicked) / 1000;
		let p = await progress();
		assert.equal(p.act, 1); assert.equal(p.step, 0);
		const cfg = await config();
		const lastAct = cfg.acts.length;
		let jumped = false;
		for (;;) {
			p = await progress();
			if (p.act === lastAct && p.step >= cfg.acts[lastAct - 1].steps.length) break;
			if (jumpBackAt && !jumped && p.act === jumpBackAt.when_act && p.step === 0) {
				const seconds = await press(String(jumpBackAt.to), `Digit${jumpBackAt.to}`, 48 + jumpBackAt.to, 1);
				const after = await progress();
				assert.equal(after.act, jumpBackAt.to); assert.equal(after.step, 0);
				const entry = { show: index, purpose: 'jump', from: jumpBackAt.when_act, to: jumpBackAt.to, seconds, db: (await http('frappe_debug.demo.switch.switch_status')).message.db };
				record.switches.push(entry); show.switches.push(entry); log({ event: 'switch', ...entry }); save();
				jumped = true;
				continue;
			}
			const actBefore = p.act, stepBefore = p.step;
			const crossing = stepBefore >= cfg.acts[actBefore - 1].steps.length && cfg.acts[actBefore]?.scene_date !== cfg.acts[actBefore - 1].scene_date;
			const seconds = await right();
			show.steps += 1;
			if (crossing) {
				const after = await progress();
				const entry = { show: index, purpose: 'forward', from: actBefore, to: after.act, seconds, after_jump: jumped && actBefore === jumpBackAt?.to, db: (await http('frappe_debug.demo.switch.switch_status')).message.db };
				assert.equal(after.act, actBefore + 1); assert.equal(after.step, 0);
				record.switches.push(entry); show.switches.push(entry); log({ event: 'switch', ...entry }); save();
			}
		}
		show.finished = new Date().toISOString();
		show.seconds = (Date.parse(show.finished) - Date.parse(show.started)) / 1000;
		record.shows.push(show); save();
		log({ event: 'show_done', index, steps: show.steps, seconds: show.seconds });
		await c.screenshot(path.join(logs, `s8-r8sb-fd013-show${index}.png`));
	};
	try {
		assert.equal(await c.evaluate('frappe.boot.sitename'), 'erx.localhost');
		assert.equal(await c.evaluate('frappe.session.user'), 'Administrator');
		await refreshCookie();
		await playShow(1);
		if (!ONE_SHOW) await playShow(2, { jumpBackAt: { when_act: 7, to: 5 } });
		await returnToBase();
		const latencies = record.samples.filter(s => s.ms !== undefined);
		const summarise = rows => {
			const values = rows.map(s => s.ms).sort((a, b) => a - b);
			if (!values.length) return null;
			return { n: values.length, median: values[Math.floor(values.length / 2)], p95: values[Math.floor(values.length * 0.95)], max: values.at(-1) };
		};
		record.summary = {
			switches: record.switches,
			desk_latency_while_refilling: summarise(latencies.filter(s => s.cloning > 0)),
			desk_latency_idle: summarise(latencies.filter(s => s.cloning === 0)),
			focus_releases: record.focus_releases.length,
		};
		save();
		log({ event: 'PASS', ...record.summary });
	} catch (error) {
		record.errors.push({ message: error.message, url: await safe('location.href'), text: await safe('document.body.innerText.slice(0, 2000)') });
		save();
		await c.screenshot(path.join(logs, 's8-r8sb-fd013-failure.png')).catch(() => {});
		throw error;
	} finally {
		sampling = false;
		await sampler.catch(() => {});
		await c.close();
	}
})().catch(error => { console.error(error); process.exitCode = 1; });
