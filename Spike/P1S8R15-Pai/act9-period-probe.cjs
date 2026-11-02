// S8 R15 PT-043 probe 6: can the scorecard form lead to a monthly period, and what does the period form show?
// Read-only: opens forms and lists and reads the DOM; clicks nothing.
const { spawn } = require('node:child_process');
const fs = require('node:fs'), os = require('node:os'), path = require('node:path');
const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const BASE = 'http://erx.localhost:8000';
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
(async () => {
	const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'erx-r15-period-'));
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
		await send('Page.navigate', { url: `${BASE}/desk/supplier-scorecard/${encodeURIComponent('钢丝供应商04')}?sidebar=Business%20Flow` }); await sleep(9000);
		console.log('connections', JSON.stringify(await evaluate(`(() => [...document.querySelectorAll('.form-documents [data-doctype], .form-links [data-doctype]')]
			.map(e => ({ tag: e.tagName, cls: e.className, doctype: e.dataset.doctype, text: e.textContent.trim().slice(0, 40), visible: $(e).is(':visible') })))()`)));
		await evaluate(`frappe.set_route('List', 'Supplier Scorecard Period', { supplier: '钢丝供应商04' })`); await sleep(6000);
		console.log('period list', JSON.stringify(await evaluate(`(() => ({ rows: cur_list.data.length, sort: cur_list.sort_by + ' ' + cur_list.sort_order,
			cols: [...document.querySelectorAll('.list-row-head .list-row-col')].map(e => e.textContent.trim()),
			first: cur_list.data[0] }))()`)));
		await evaluate(`frappe.set_route('Form', 'Supplier Scorecard Period', 'PU-SSP-2026-00048')`); await sleep(5000);
		console.log('period form', JSON.stringify(await evaluate(`(() => Object.fromEntries(['supplier', 'start_date', 'end_date', 'total_score', 'criteria', 'variables'].map(n => {
			const f = cur_frm.fields_dict[n]; const w = f?.$wrapper?.[0];
			return [n, { visible: !!w && $(w).is(':visible'), collapsed: f?.section?.is_collapsed?.() ?? null,
				cols: [...(w?.querySelectorAll('.grid-heading-row .static-area') || [])].map(e => e.textContent.trim()) }];
		})))()`)));
		socket.close();
	} finally {
		chrome.kill();
	}
})().catch(error => { console.error(error); process.exitCode = 1; });
