// S8 R15 step 24: read-only look at the page the running rehearsal driver's Chrome shows.
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
	const r = await send('Runtime.evaluate', { returnByValue: true, expression: `(() => ({
		url: location.href,
		panel: document.querySelector('#frappe-debug-presenter, .frappe-debug-stage, [class*=frappe-debug]')?.textContent?.replace(/\\s+/g, ' ').slice(0, 300),
		dialogs: [...document.querySelectorAll('[role=dialog], .modal.show')].map(d => d.textContent.replace(/\\s+/g, ' ').slice(0, 200)),
		pending: sessionStorage.getItem('frappe_debug_pending')?.slice(0, 300),
		mode: sessionStorage.getItem('frappe_debug_mode'),
		rehearsal: sessionStorage.getItem('frappe_debug_rehearsal')?.slice(0, 200),
		body: document.body?.innerText?.replace(/\\s+/g, ' ').slice(0, 400),
	}))()` });
	console.log(JSON.stringify(r.result?.result?.value || r.result, null, 1));
	const shot = await send('Page.captureScreenshot', { format: 'png' });
	if (shot.result?.data) fs.writeFileSync(path.join(__dirname, 'peek-rehearsal.png'), Buffer.from(shot.result.data, 'base64'));
	socket.close();
})().catch(error => { console.error(error); process.exitCode = 1; });
