// S8 R15 PT-042 probe: why act 9 steps need several → presses.
// Read-only: opens list/form pages and reads the sidebar and list DOM; never clicks a button
// that saves, never presses →, never writes demo progress.
const { spawn } = require('node:child_process');
const fs = require('node:fs'), os = require('node:os'), path = require('node:path');
const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const BASE = 'http://erx.localhost:8000';
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
(async () => {
	const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'erx-r15-act9-'));
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
		const sidebar = `(() => {
			const wanted = ['Item Price','Supplier Scorecard','Replenishment Suggestion','Material Request'];
			const anchors = [...document.querySelectorAll('.item-anchor')];
			const rows = wanted.map(name => {
				const names = [name, __(name)];
				const anchor = anchors.find(a => names.includes(a.querySelector?.('.sidebar-item-label')?.textContent.trim()));
				return { name, found: !!anchor, visible: !!anchor && $(anchor).is(':visible'), hidden_parent: !!anchor?.closest('.hidden'), href: anchor?.getAttribute('href') };
			});
			return { route: frappe.get_route_str(), sidebar_title: frappe.app.sidebar?.sidebar_title, rows,
				demo_active: !!window.frappe_debug?.demo?.progress?.active, act: window.frappe_debug?.demo?.progress?.act, step: window.frappe_debug?.demo?.progress?.step,
				section_state: localStorage.getItem('section-breaks-state') };
		})()`;
		for (const url of ['/desk/replenishment-suggestion?sidebar=Business%20Flow', '/desk/item-price', '/desk/supplier-scorecard', '/desk/material-request']) {
			await send('Page.navigate', { url: `${BASE}${url}` }); await sleep(9000);
			console.log(url, JSON.stringify(await evaluate(sidebar), null, 1));
		}
		// The same route without ?sidebar: which sidebar does Desk pick?
		await send('Page.navigate', { url: `${BASE}/desk/replenishment-suggestion` }); await sleep(9000);
		console.log('no sidebar param', JSON.stringify(await evaluate(sidebar), null, 1));
		socket.close();
	} finally {
		chrome.kill();
	}
})().catch(error => { console.error(error); process.exitCode = 1; });
