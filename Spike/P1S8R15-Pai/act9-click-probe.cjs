// S8 R15 PT-042 probe 2: follow act 9's sidebar clicks inside one Desk page.
// Read-only: only clicks sidebar navigation links and reads the DOM; never presses →,
// never clicks a button that saves, never writes demo progress.
const { spawn } = require('node:child_process');
const fs = require('node:fs'), os = require('node:os'), path = require('node:path');
const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const BASE = 'http://erx.localhost:8000';
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
(async () => {
	const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'erx-r15-act9b-'));
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
		await send('Page.navigate', { url: `${BASE}/desk/replenishment-suggestion?sidebar=Business%20Flow` }); await sleep(10000);
		const state = `(() => {
			const anchors = [...document.querySelectorAll('.item-anchor')];
			const find = name => anchors.find(a => [name, __(name)].includes(a.querySelector?.('.sidebar-item-label')?.textContent.trim()));
			const look = ['Item Price','Supplier Scorecard','Replenishment Suggestion'].map(name => [name, !!find(name) && $(find(name)).is(':visible')]);
			return { route: frappe.get_route_str(), sidebar: frappe.app.sidebar?.sidebar_title, list: window.cur_list?.doctype, rows: window.cur_list?.$result?.find('.list-row-container').length, look };
		})()`;
		const click = name => evaluate(`(() => {
			const anchor = [...document.querySelectorAll('.item-anchor')].find(a => [${JSON.stringify(name)}, __(${JSON.stringify(name)})].includes(a.querySelector?.('.sidebar-item-label')?.textContent.trim()));
			if (!anchor) return 'missing';
			window.__t0 = Date.now(); anchor.click(); return 'clicked';
		})()`);
		console.log('start', JSON.stringify(await evaluate(state)));
		for (const name of ['Item Price', 'Supplier Scorecard', 'Replenishment Suggestion']) {
			console.log('click', name, await click(name));
			for (const wait of [500, 1500, 4000]) { await sleep(wait); console.log(`  +${wait}`, JSON.stringify(await evaluate(state))); }
		}
		// A form opened from the list, then the material request link, as act 9 does.
		const eoq = await evaluate(`frappe.db.get_list('Replenishment Suggestion',{filters:{rule:'EOQ'},fields:['name'],order_by:'creation desc',limit:1}).then(r=>r[0]?.name)`);
		console.log('eoq', eoq);
		if (eoq) {
			await evaluate(`frappe.set_route('Form','Replenishment Suggestion',${JSON.stringify(eoq)})`); await sleep(4000);
			console.log('form', JSON.stringify(await evaluate(state)));
			console.log('Item Price', await click('Item Price')); await sleep(4000);
			console.log('  after', JSON.stringify(await evaluate(state)));
		}
		socket.close();
	} finally {
		chrome.kill();
	}
})().catch(error => { console.error(error); process.exitCode = 1; });
