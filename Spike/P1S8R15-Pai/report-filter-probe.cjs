// S8 R15 PT-046 probe: how far apart are a report's filter boxes? A frame adds 5px padding and a
// 5px ring on each side, so filters closer than ~20px get frames that run into each other.
// Read-only: opens report and page routes and reads the DOM; clicks nothing.
const { spawn } = require('node:child_process');
const fs = require('node:fs'), os = require('node:os'), path = require('node:path');
const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const BASE = 'http://erx.localhost:8000';
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
(async () => {
	const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'erx-r15-filters-'));
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
		const box = `e => { const r = e?.getBoundingClientRect?.(); return r && { left: Math.round(r.left), right: Math.round(r.right), top: Math.round(r.top), bottom: Math.round(r.bottom) }; }`;
		for (const [report, fields] of [['Capacity Load', ['company', 'from_date', 'to_date', 'bucket']], ['Stock Ledger', ['company', 'from_date', 'to_date']]]) {
			await send('Page.navigate', { url: `${BASE}/desk/query-report/${encodeURIComponent(report)}?sidebar=Business%20Flow` }); await sleep(9000);
			console.log(report, JSON.stringify(await evaluate(`(() => { const box = ${box};
				return ${JSON.stringify(fields)}.map(f => [f, box(frappe.query_report.get_filter(f)?.$wrapper?.[0])]); })()`)));
		}
		await send('Page.navigate', { url: `${BASE}/desk/spc-chart?sidebar=Business%20Flow` }); await sleep(9000);
		console.log('spc', JSON.stringify(await evaluate(`(() => { const box = ${box}; const page = frappe.pages['spc-chart']?.wrapper;
			const fields = page?.spc_fields || {}; return Object.keys(fields).map(f => [f, box(fields[f].$wrapper?.[0])]); })()`)));
		socket.close();
	} finally {
		chrome.kill();
	}
})().catch(error => { console.error(error); process.exitCode = 1; });
