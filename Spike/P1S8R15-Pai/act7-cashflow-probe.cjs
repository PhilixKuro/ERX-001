// S8 R15 step 24 probe: reproduce act 7 steps 39-41 (sidebar Cash Flow Worksheet, list primary,
// wait for the new form) on the s8r9 work db and read what the page shows.
// Writes nothing: pressing the list's primary button only opens an unsaved new form.
const { spawn } = require('node:child_process');
const fs = require('node:fs'), os = require('node:os'), path = require('node:path');
const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const BASE = 'http://s8r9.localhost:6787';
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
(async () => {
	const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'erx-r15-cashflow-'));
	const chrome = spawn(CHROME, ['--headless=new', '--remote-debugging-port=0', `--user-data-dir=${profile}`, '--window-size=1440,900', 'about:blank'], { stdio: 'ignore' });
	try {
		let port;
		for (let i = 0; i < 100 && !port; i++) { try { port = fs.readFileSync(path.join(profile, 'DevToolsActivePort'), 'utf8').split('\n')[0]; } catch { await sleep(100); } }
		const target = (await (await fetch(`http://127.0.0.1:${port}/json/list`)).json()).find(t => t.type === 'page');
		const socket = new WebSocket(target.webSocketDebuggerUrl);
		await new Promise((resolve, reject) => { socket.addEventListener('open', resolve); socket.addEventListener('error', reject); });
		let id = 0; const waiting = new Map();
		socket.addEventListener('message', event => { const data = JSON.parse(event.data); waiting.get(data.id)?.(data); waiting.delete(data.id); });
		const send = (method, params = {}) => new Promise(resolve => { const n = ++id; waiting.set(n, resolve); socket.send(JSON.stringify({ id: n, method, params })); });
		const evaluate = async expression => {
			const r = await send('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true });
			if (r.result?.exceptionDetails) console.log('EXCEPTION', JSON.stringify(r.result.exceptionDetails).slice(0, 800));
			return r.result?.result?.value;
		};
		await send('Network.enable'); await send('Network.setCacheDisabled', { cacheDisabled: true });
		await send('Page.navigate', { url: `${BASE}/login` }); await sleep(3000);
		await evaluate(`fetch('/api/method/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({usr:'Administrator',pwd:'admin'})}).then(r=>r.status)`);
		await send('Page.navigate', { url: `${BASE}/desk/month-end-closing-voucher?sidebar=Business%20Flow` }); await sleep(9000);
		const state = `(() => ({ route: frappe.get_route_str(), list: window.cur_list?.doctype, frm: window.cur_frm && { doctype: cur_frm.doctype, is_new: cur_frm.is_new?.(), name: cur_frm.docname },
			dialog: window.cur_dialog?.display ? window.cur_dialog.title : null, msg: frappe.msg_dialog?.display ? frappe.msg_dialog.body?.textContent?.slice(0, 200) : null,
			primary: window.cur_list?.page?.btn_primary?.[0]?.textContent?.trim(), primary_visible: !!window.cur_list?.page?.btn_primary?.is?.(':visible') }))()`;
		console.log('db', await evaluate(`frappe.xcall('frappe_debug.demo.switch.switch_status').then(r => r.db)`));
		console.log('before', JSON.stringify(await evaluate(state)));
		console.log('press', JSON.stringify(await evaluate(`(async () => {
			const demo = frappe_debug.demo;
			if (!demo.config) demo.config = await frappe.xcall('frappe_debug.demo.config.get_demo_config');
			frappe.msg_dialog?.hide?.();
			await new Promise(r => setTimeout(r, 800));
			const ctx = demo.context();
			sessionStorage.setItem('frappe_debug_mode', 'rehearsal');
			const act7 = demo.config.acts[6].steps;
			const out = [];
			for (const index of [38, 39]) {
				const step = demo.expand(act7[index], ctx);
				const t0 = Date.now(); let error = null;
				try { await demo.actions[step.action](step, ctx); } catch (e) { error = e.message; }
				out.push({ index: index + 1, action: step.action, target: step.target, ms: Date.now() - t0, error, route: frappe.get_route_str(), list: window.cur_list?.doctype });
			}
			sessionStorage.removeItem('frappe_debug_mode');
			return out;
		})()`)));
		for (const wait of [1000, 4000, 10000]) { await sleep(wait); console.log(`+${wait}`, JSON.stringify(await evaluate(state))); }
		socket.close();
	} finally {
		chrome.kill();
	}
})().catch(error => { console.error(error); process.exitCode = 1; });
