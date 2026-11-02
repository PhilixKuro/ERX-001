// S8 R15 step 24: read-only look at the CRM page of the running rehearsal (scripts, error, statuses).
// Usage: node peek-rehearsal.cjs <user-data-dir>   (attaches over DevTools; clicks nothing)
const fs = require('node:fs'), path = require('node:path');
(async () => {
	const port = fs.readFileSync(path.join(process.argv[2], 'DevToolsActivePort'), 'utf8').split('\n')[0];
	const pages = (await (await fetch(`http://127.0.0.1:${port}/json/list`)).json()).filter(t => t.type === 'page');
	console.log('pages', JSON.stringify(pages.map(p => p.url)));
	const socket = new WebSocket(pages[0].webSocketDebuggerUrl);
	await new Promise((resolve, reject) => { socket.addEventListener('open', resolve); socket.addEventListener('error', reject); });
	let id = 0; const waiting = new Map();
	socket.addEventListener('message', event => { const data = JSON.parse(event.data); waiting.get(data.id)?.(data); waiting.delete(data.id); });
	const send = (method, params = {}) => new Promise(resolve => { const n = ++id; waiting.set(n, resolve); socket.send(JSON.stringify({ id: n, method, params })); });
	const r = await send('Runtime.evaluate', { returnByValue: true, awaitPromise: true, expression: `(async () => ({
		scripts: [...document.scripts].map(s => s.src).filter(s => /frappe_debug/.test(s)),
		error: [...document.querySelectorAll('aside')].map(a => a.textContent).slice(-2),
		statuses: await fetch('/api/method/frappe.client.get_list', { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Frappe-CSRF-Token': window.csrf_token }, body: JSON.stringify({ doctype: 'CRM Lead Status', fields: ['name'] }) }).then(r => r.status + ' ' + r.statusText).catch(e => String(e)),
		csrf: typeof window.csrf_token, idb: (await indexedDB.databases?.())?.map(d => d.name),
	}))()` });
	console.log(JSON.stringify(r.result?.result?.value || r.result, null, 1));
	const shot = await send('Page.captureScreenshot', { format: 'png' });
	if (shot.result?.data) fs.writeFileSync(path.join(__dirname, 'peek-rehearsal.png'), Buffer.from(shot.result.data, 'base64'));
	socket.close();
})().catch(error => { console.error(error); process.exitCode = 1; });
